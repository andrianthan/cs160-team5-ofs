from decimal import Decimal

import pytest

from app.extensions import db
from app.models import Order, OrderLine, Product, User

PASSWORD = "password123"


def make_user(email, role="customer"):
    user = User(email=email, name=email.split("@")[0], role=role)
    user.set_password(PASSWORD)
    db.session.add(user)
    db.session.commit()
    return user


def sign_in(client, user):
    client.post("/api/auth/logout")
    assert client.post("/api/auth/login", json={"email": user.email, "password": PASSWORD}).status_code == 200


def make_order(user, status="placed"):
    p = Product(name="Apple", category="Fruit", price=Decimal("1.50"), weight_lb=Decimal("0.50"), stock_qty=10)
    db.session.add(p)
    db.session.flush()
    order = Order(
        user_id=user.id, status=status, subtotal=Decimal("3.00"), delivery_fee=Decimal("0"),
        total=Decimal("3.00"), weight_lb=Decimal("1.00"), delivery_address="1 Main St",
        delivery_lat=37.33, delivery_lng=-121.89,
    )
    order.lines.append(OrderLine(product_id=p.product_id, name="Apple", unit_price=p.price,
                                 weight_lb=p.weight_lb, quantity=2))
    db.session.add(order)
    db.session.commit()
    return order


@pytest.fixture
def people(app):
    return {
        "alice": make_user("alice@example.com"),
        "bob": make_user("bob@example.com"),
        "employee": make_user("emp@example.com", "employee"),
        "manager": make_user("mgr@example.com", "manager"),
    }


def test_orders_require_login(client):
    assert client.get("/api/orders").status_code == 401
    assert client.get("/api/orders/1").status_code == 401
    assert client.patch("/api/orders/1/status", json={"status": "planned"}).status_code == 401


def test_clients_cannot_create_orders(client, people):
    sign_in(client, people["alice"])
    assert client.post("/api/orders", json={}).status_code == 405


def test_customer_sees_only_own_orders(client, people):
    mine = make_order(people["alice"])
    theirs = make_order(people["bob"])
    sign_in(client, people["alice"])
    body = client.get("/api/orders").get_json()
    assert [o["id"] for o in body["orders"]] == [mine.id]
    assert body["orders"][0]["lines"][0] == {
        "productId": mine.lines[0].product_id, "name": "Apple", "price": 1.5, "weightLb": 0.5, "quantity": 2,
    }
    assert client.get(f"/api/orders/{mine.id}").status_code == 200
    assert client.get(f"/api/orders/{theirs.id}").status_code == 404


@pytest.mark.parametrize("role", ["employee", "manager"])
def test_staff_see_all_orders_and_filter(client, people, role):
    make_order(people["alice"])
    planned = make_order(people["bob"], status="planned")
    sign_in(client, people[role])
    assert len(client.get("/api/orders").get_json()["orders"]) == 2
    assert [o["id"] for o in client.get("/api/orders?status=planned").get_json()["orders"]] == [planned.id]
    assert client.get("/api/orders?status=bogus").status_code == 400
    assert client.get(f"/api/orders/{planned.id}").status_code == 200


def test_customer_cannot_change_status(client, people):
    order = make_order(people["alice"])
    sign_in(client, people["alice"])
    assert client.patch(f"/api/orders/{order.id}/status", json={"status": "planned"}).status_code == 403


@pytest.mark.parametrize("start, new", [
    ("placed", "planned"),
    ("planned", "out_for_delivery"),
    ("out_for_delivery", "delivered"),
    ("out_for_delivery", "delivery_failed"),
    ("delivery_failed", "placed"),
    ("manual_review", "placed"),
])
def test_allowed_transitions(client, people, start, new):
    order = make_order(people["alice"], status=start)
    sign_in(client, people["employee"])
    resp = client.patch(f"/api/orders/{order.id}/status", json={"status": new})
    assert resp.status_code == 200 and resp.get_json()["status"] == new


@pytest.mark.parametrize("start, new", [
    ("placed", "delivered"),
    ("placed", "cancelled"),  # cancelling is a Manager Order Override
    ("delivered", "placed"),
    ("cancelled", "placed"),
])
def test_blocked_transitions(client, people, start, new):
    order = make_order(people["alice"], status=start)
    sign_in(client, people["manager"])
    resp = client.patch(f"/api/orders/{order.id}/status", json={"status": new})
    assert resp.status_code == 409 and resp.get_json()["error"] == "invalid_transition"
    assert db.session.get(Order, order.id).status == start


@pytest.mark.parametrize("body", [None, {}, {"status": "shipped"}, {"status": 3}])
def test_bad_status_body(client, people, body):
    order = make_order(people["alice"])
    sign_in(client, people["employee"])
    assert client.patch(f"/api/orders/{order.id}/status", json=body).status_code == 400


def test_status_unknown_order(client, people):
    sign_in(client, people["employee"])
    assert client.patch("/api/orders/999/status", json={"status": "planned"}).status_code == 404
