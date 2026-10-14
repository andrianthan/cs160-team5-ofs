from decimal import Decimal

import pytest

from app.blueprints.cart import calc_delivery_fee, calc_order_weight, check_overweight, validate_cart_for_checkout
from app.extensions import db
from app.models import Product, User


def add(name="Eggs", price="6.49", weight="1.60", stock=100, **extra):
    p = Product(name=name, category="Dairy", price=Decimal(price), weight_lb=Decimal(weight), stock_qty=stock, **extra)
    db.session.add(p)
    db.session.commit()
    return p


def make_user(email="a@example.com"):
    user = User(email=email, name="A", role="customer")
    user.set_password("password123")
    db.session.add(user)
    db.session.commit()
    return user


def sign_in(client, email="a@example.com"):
    if not User.query.filter_by(email=email).first():
        make_user(email)
    assert client.post("/api/auth/login", json={"email": email, "password": "password123"}).status_code == 200


def put(client, product, quantity):
    return client.put(f"/api/cart/items/{product.product_id}", json={"quantity": quantity})


# ============ auth ============

def test_cart_requires_login(client):
    assert client.get("/api/cart").status_code == 401
    assert client.put("/api/cart/items/1", json={"quantity": 1}).status_code == 401
    assert client.delete("/api/cart").status_code == 401


# ============ GET / PUT / DELETE ============

def test_empty_cart(client):
    sign_in(client)
    body = client.get("/api/cart").get_json()
    assert body == {"lines": [], "orderWeightLb": 0, "subtotal": 0, "deliveryFee": 0, "total": 0, "overweight": False}


def test_add_update_remove(client):
    sign_in(client)
    p = add()
    body = put(client, p, 3).get_json()
    [line] = body["lines"]
    assert line["quantity"] == 3 and line["lineTotal"] == 19.47 and line["lineWeightLb"] == 4.8
    assert body["subtotal"] == 19.47 and body["orderWeightLb"] == 4.8 and body["total"] == 19.47
    assert put(client, p, 5).get_json()["lines"][0]["quantity"] == 5
    assert put(client, p, 0).get_json()["lines"] == []


def test_remove_missing_line_is_ok(client):
    sign_in(client)
    assert put(client, add(), 0).status_code == 200


def test_clear_cart(client):
    sign_in(client)
    put(client, add(), 2)
    assert client.delete("/api/cart").get_json()["lines"] == []


def test_cart_persists_across_sessions(client):
    sign_in(client)
    put(client, add(), 2)
    client.post("/api/auth/logout")
    sign_in(client)
    assert client.get("/api/cart").get_json()["lines"][0]["quantity"] == 2


def test_carts_are_per_user(client):
    p = add()
    sign_in(client, "a@example.com")
    put(client, p, 2)
    client.post("/api/auth/logout")
    sign_in(client, "b@example.com")
    assert client.get("/api/cart").get_json()["lines"] == []


# ============ validation ============

@pytest.mark.parametrize("bad", [-1, 1.5, "3", True, None, 1000])
def test_invalid_quantity(client, bad):
    sign_in(client)
    resp = put(client, add(), bad)
    assert resp.status_code == 400 and resp.get_json()["error"] == "invalid_quantity"


def test_missing_body(client):
    sign_in(client)
    p = add()
    assert client.put(f"/api/cart/items/{p.product_id}").status_code == 400


def test_unknown_and_inactive_product(client):
    sign_in(client)
    assert client.put("/api/cart/items/999", json={"quantity": 1}).status_code == 404
    assert client.put("/api/cart/items/abc", json={"quantity": 1}).status_code == 404
    assert put(client, add(name="Gone", active=False), 1).status_code == 404


def test_stock_limit_br4(client):
    sign_in(client)
    p = add(stock=4)
    assert put(client, p, 4).status_code == 200
    resp = put(client, p, 5)
    assert resp.status_code == 409 and resp.get_json()["error"] == "insufficient_stock"


def test_line_for_deactivated_product_is_flagged_and_excluded(client):
    sign_in(client)
    p = add()
    put(client, p, 2)
    p.active = False
    db.session.commit()
    body = client.get("/api/cart").get_json()
    assert body["lines"][0]["unavailable"] is True
    assert body["subtotal"] == 0 and body["orderWeightLb"] == 0


# ============ pricing (BR-1, BR-3) ============

@pytest.mark.parametrize("weight,fee", [("0", 0), ("19.99", 0), ("20", 10), ("20.00", 10), ("20.01", 10)])
def test_delivery_fee_boundary(weight, fee):
    assert calc_delivery_fee(Decimal(weight)) == fee


@pytest.mark.parametrize("weight,over", [("199.99", False), ("200", False), ("200.01", True)])
def test_overweight_boundary(weight, over):
    assert check_overweight(Decimal(weight)) is over


def test_calc_order_weight():
    a, b = Product(weight_lb=Decimal("1.25")), Product(weight_lb=Decimal("0.5"))
    assert calc_order_weight([(a, 4), (b, 3)]) == Decimal("6.5")


def test_fee_applies_at_exactly_20_lb_via_api(client):
    sign_in(client)
    p = add(price="10.00", weight="10.00")
    assert put(client, p, 1).get_json()["deliveryFee"] == 0
    body = put(client, p, 2).get_json()
    assert body["orderWeightLb"] == 20 and body["deliveryFee"] == 10 and body["total"] == 30


def test_overweight_flag_via_api(client):
    sign_in(client)
    p = add(price="1.00", weight="100.00")
    assert put(client, p, 2).get_json()["overweight"] is False
    assert put(client, p, 3).get_json()["overweight"] is True


# ============ validate_cart_for_checkout ============

def test_checkout_validation(client, app):
    user = make_user()
    sign_in(client)
    assert validate_cart_for_checkout(user)[1] == "empty_cart"

    p = add(price="1.00", weight="100.00", stock=10)
    put(client, p, 2)
    assert validate_cart_for_checkout(user)[1] is None

    put(client, p, 3)
    assert validate_cart_for_checkout(user)[1] == "overweight"

    put(client, p, 2)
    p.stock_qty = 1
    db.session.commit()
    assert validate_cart_for_checkout(user)[1] == "insufficient_stock"
