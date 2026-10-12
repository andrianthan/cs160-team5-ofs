from decimal import Decimal

import pytest

from app.extensions import db
from app.models import Product, User

# Request keys are column names; responses use the names from Product.to_dict().
NEW = {"name": "Honey", "category": "Pantry", "price": 8.5, "weight_lb": 1.0, "stock_qty": 10}


def add(name="Free-Range Eggs", **extra):
    """Put a product straight into the database."""
    product = Product(name=name, category="Dairy", price=Decimal("6.49"), weight_lb=Decimal("1.60"), **extra)
    db.session.add(product)
    db.session.commit()
    return product


def sign_in(client, role):
    user = User(email=f"{role}@example.com", name=role.title(), role=role)
    user.set_password("password123")
    db.session.add(user)
    db.session.commit()
    assert client.post("/api/auth/login", json={"email": user.email, "password": "password123"}).status_code == 200


# ============ GET /api/products ============

def test_empty_catalog_returns_an_empty_list(client):
    resp = client.get("/api/products")
    assert resp.status_code == 200 and resp.get_json() == []


def test_product_shape(client):
    p = add(stock_qty=18)
    [item] = client.get("/api/products").get_json()
    assert item["id"] == p.product_id
    assert item["name"] == "Free-Range Eggs" and item["category"] == "Dairy"
    assert item["price"] == 6.49 and item["weightLb"] == 1.6 and item["stock"] == 18

'''
def test_internal_fields_are_not_exposed(client):
    add()
    [item] = client.get("/api/products").get_json()
    for hidden in ("stock_qty", "weight_lb", "image_url", "low_stock_threshold", "active", "updated_at"):
        assert hidden not in item'''


def test_sorted_by_name(client):
    for name in ["Sourdough Loaf", "Apples", "Milk"]:
        add(name=name)
    assert [p["name"] for p in client.get("/api/products").get_json()] == ["Apples", "Milk", "Sourdough Loaf"]


def test_inactive_products_are_hidden(client):
    add(name="Visible")
    add(name="Removed", active=False)
    assert [p["name"] for p in client.get("/api/products").get_json()] == ["Visible"]


def test_out_of_stock_products_are_still_listed(client):
    add(stock_qty=0)
    assert client.get("/api/products").get_json()[0]["stock"] == 0


def test_listing_is_public(client):
    add()
    assert client.get("/api/auth/me").status_code == 401  # confirm we are signed out
    assert client.get("/api/products").status_code == 200


# ============ the model ============

def test_defaults(app):
    p = add()
    db.session.refresh(p)
    assert (p.stock_qty, p.low_stock_threshold, p.active) == (0, 5, True)


def test_updated_at_is_set_on_create_and_refreshed_on_update(app):
    from datetime import datetime, timezone

    p = add()
    assert p.updated_at is not None
    p.updated_at = datetime(2000, 1, 1, tzinfo=timezone.utc)  # pretend it was last touched long ago
    db.session.commit()
    assert Product.query.one().updated_at.year == 2000  # an explicit value is respected
    p.stock_qty = 5
    db.session.commit()
    db.session.refresh(p)
    assert p.updated_at.year > 2000  # refreshed automatically


# ============ who may write ============

@pytest.mark.parametrize("role, status", [(None, 401), ("customer", 403), ("employee", 403)])
def test_only_managers_can_create_or_update(client, role, status):
    p = add()
    if role:
        sign_in(client, role)
    assert client.post("/api/products", json=NEW).status_code == status
    assert client.patch(f"/api/products/{p.product_id}", json={"stock_qty": 1}).status_code == status
    assert Product.query.count() == 1 and Product.query.one().stock_qty == 0  # nothing changed


# ============ POST /api/products ============

def test_manager_can_create_a_product(client):
    sign_in(client, "manager")
    resp = client.post("/api/products", json=NEW)
    assert resp.status_code == 201
    body = resp.get_json()
    assert body["name"] == "Honey" and body["weightLb"] == 1.0 and body["stock"] == 10 and body["price"] == 8.5
    assert [p["name"] for p in client.get("/api/products").get_json()] == ["Honey"]


def test_optional_fields_can_be_left_out(client):
    sign_in(client, "manager")
    minimal = {k: NEW[k] for k in ("name", "category", "price", "weight_lb")}
    resp = client.post("/api/products", json=minimal)
    assert resp.status_code == 201 and resp.get_json()["stock"] == 0  # database default


@pytest.mark.parametrize("missing", ["name", "category", "price", "weight_lb"])
def test_each_required_field_is_required(client, missing):
    sign_in(client, "manager")
    body = {k: v for k, v in NEW.items() if k != missing}
    resp = client.post("/api/products", json=body)
    assert resp.status_code == 400 and missing in resp.get_json()["error"]


@pytest.mark.parametrize(
    "change",
    [
        {"name": None}, {"name": "  "}, {"name": 5}, {"name": "x" * 161}, {"category": "x" * 81},
        {"price": -1}, {"price": 1.234}, {"price": "6.49"}, {"price": True}, {"price": 10**8},
        {"weight_lb": 0}, {"weight_lb": -2}, {"stock_qty": -1}, {"stock_qty": 1.5}, {"stock_qty": True},
        {"low_stock_threshold": -1}, {"active": "yes"}, {"description": 5}, {"image_url": ["x"]},
    ],
    ids=lambda c: str(c)[:40],
)
def test_bad_values_are_rejected(client, change):
    sign_in(client, "manager")
    resp = client.post("/api/products", json={**NEW, **change})
    assert resp.status_code == 400 and next(iter(change)) in resp.get_json()["error"]
    assert Product.query.count() == 0


@pytest.mark.parametrize(
    "change",
    [{"name": "x" * 160}, {"price": 0}, {"price": 99999999.99}, {"weight_lb": 0.01}, {"stock_qty": 0},
     {"description": None}, {"image_url": "/img/a.jpg"}, {"active": False}],
    ids=lambda c: str(c)[:40],
)
def test_boundary_values_are_accepted(client, change):
    sign_in(client, "manager")
    assert client.post("/api/products", json={**NEW, **change}).status_code == 201


def test_nan_is_rejected(client):
    sign_in(client, "manager")
    raw = '{"name":"X","category":"Y","price":NaN,"weight_lb":1}'
    assert client.post("/api/products", data=raw, content_type="application/json").status_code == 400
    assert Product.query.count() == 0


def test_unknown_fields_are_ignored_and_id_cannot_be_set(client):
    sign_in(client, "manager")
    resp = client.post("/api/products", json={**NEW, "typo": 1, "product_id": 999})
    assert resp.status_code == 201 and resp.get_json()["id"] != 999


def test_names_are_trimmed(client):
    sign_in(client, "manager")
    assert client.post("/api/products", json={**NEW, "name": "  Honey  "}).get_json()["name"] == "Honey"


@pytest.mark.parametrize("raw", ["not json", "[1, 2]", "null"])
def test_a_body_that_is_not_a_json_object_is_a_clean_400(client, raw):
    sign_in(client, "manager")
    resp = client.post("/api/products", data=raw, content_type="application/json")
    assert resp.status_code == 400


# ============ PATCH /api/products/<id> ============

def test_patch_changes_only_the_given_fields(client):
    sign_in(client, "manager")
    p = add(stock_qty=18)
    resp = client.patch(f"/api/products/{p.product_id}", json={"stock_qty": 5})
    assert resp.status_code == 200
    assert resp.get_json()["stock"] == 5 and resp.get_json()["price"] == 6.49 and resp.get_json()["name"] == "Free-Range Eggs"


def test_patch_can_change_several_fields_at_once(client):
    sign_in(client, "manager")
    p = add()
    body = {"name": "  Duck Eggs ", "price": 9, "weight_lb": 2.25, "stock_qty": 3}
    resp = client.patch(f"/api/products/{p.product_id}", json=body).get_json()
    assert (resp["name"], resp["price"], resp["weightLb"], resp["stock"]) == ("Duck Eggs", 9.0, 2.25, 3)


def test_patch_active_false_removes_it_and_true_brings_it_back(client):
    sign_in(client, "manager")
    p = add()
    assert client.patch(f"/api/products/{p.product_id}", json={"active": False}).status_code == 200
    assert client.get("/api/products").get_json() == []
    assert client.patch(f"/api/products/{p.product_id}", json={"active": True}).status_code == 200
    assert len(client.get("/api/products").get_json()) == 1


def test_patch_can_clear_the_description(client):
    sign_in(client, "manager")
    p = add(description="Pasture-raised")
    assert client.patch(f"/api/products/{p.product_id}", json={"description": None}).status_code == 200
    assert Product.query.one().description is None


def test_patch_with_any_bad_value_changes_nothing(client):
    sign_in(client, "manager")
    p = add()
    assert client.patch(f"/api/products/{p.product_id}", json={"stock_qty": 5, "price": -1}).status_code == 400
    assert Product.query.one().stock_qty == 0  # the valid field was not applied either


@pytest.mark.parametrize("body", [{}, {"product_id": 5}, {"nonsense": 1}])
def test_patch_with_nothing_to_update_is_400(client, body):
    sign_in(client, "manager")
    p = add()
    resp = client.patch(f"/api/products/{p.product_id}", json=body)
    assert resp.status_code == 400 and resp.get_json()["error"] == "Nothing to update"


def test_patch_unknown_product_is_404(client):
    sign_in(client, "manager")
    resp = client.patch("/api/products/9999", json={"stock_qty": 1})
    assert resp.status_code == 404 and resp.get_json()["error"] == "Product not found"
