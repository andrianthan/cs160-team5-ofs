from decimal import Decimal

import pytest

from app.extensions import db
from app.models import Order, OrderLine, Product, Trip, User

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


def make_order(user, status="placed", weight="1.00"):
    p = Product(name="Apple", category="Fruit", price=Decimal("1.50"), weight_lb=Decimal("0.50"), stock_qty=10)
    db.session.add(p)
    db.session.flush()
    order = Order(
        user_id=user.id, status=status, subtotal=Decimal("3.00"), delivery_fee=Decimal("0"),
        total=Decimal("3.00"), weight_lb=Decimal(weight), delivery_address="1 Main St",
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
    ("placed", "manual_review"),
    ("planned", "placed"),
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
    ("placed", "planned"),  # only POST /prepare plans an order, so it always gets a Trip
    ("planned", "out_for_delivery"),  # that's Dispatch
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


# ============ Preparation Queue: POST /api/orders/<id>/prepare ============

def prepare(client, order):
    return client.post(f"/api/orders/{order.id}/prepare")


def test_prepare_requires_staff(client, people):
    order = make_order(people["alice"])
    assert prepare(client, order).status_code == 401
    sign_in(client, people["alice"])
    assert prepare(client, order).status_code == 403


def test_prepare_opens_a_trip_and_plans_the_order(client, people):
    order = make_order(people["alice"])
    sign_in(client, people["employee"])
    resp = prepare(client, order)
    body = resp.get_json()
    assert resp.status_code == 200
    assert body["order"]["status"] == "planned" and body["order"]["tripId"] == body["trip"]["id"]
    assert body["trip"]["status"] == "open" and body["trip"]["orderIds"] == [order.id]


def test_prepared_orders_share_the_open_trip(client, people):
    a, b = make_order(people["alice"]), make_order(people["bob"])
    sign_in(client, people["employee"])
    first, second = prepare(client, a).get_json(), prepare(client, b).get_json()
    assert first["trip"]["id"] == second["trip"]["id"] and second["trip"]["orderCount"] == 2


def test_eleventh_order_starts_a_new_trip(client, people):
    orders = [make_order(people["alice"]) for _ in range(11)]
    sign_in(client, people["employee"])
    trips = [prepare(client, o).get_json()["trip"]["id"] for o in orders]
    assert len(set(trips[:10])) == 1 and trips[10] != trips[0]
    assert Trip.query.count() == 2


def test_order_that_would_overload_the_trip_starts_a_new_one(client, people):
    heavy, heavier = make_order(people["alice"], weight="150.00"), make_order(people["bob"], weight="60.00")
    sign_in(client, people["employee"])
    t1 = prepare(client, heavy).get_json()["trip"]["id"]
    t2 = prepare(client, heavier).get_json()["trip"]["id"]  # 150 + 60 > 200 lb
    assert t1 != t2


def test_exactly_200_lb_still_fits(client, people):
    a, b = make_order(people["alice"], weight="150.00"), make_order(people["bob"], weight="50.00")
    sign_in(client, people["employee"])
    assert prepare(client, a).get_json()["trip"]["id"] == prepare(client, b).get_json()["trip"]["id"]


def test_order_over_robot_limit_goes_to_manual_review(client, people):
    order = make_order(people["alice"], weight="201.00")
    sign_in(client, people["employee"])
    resp = prepare(client, order)
    assert resp.status_code == 409 and resp.get_json()["error"] == "too_heavy_for_robot"
    assert db.session.get(Order, order.id).status == "manual_review" and Trip.query.count() == 0


@pytest.mark.parametrize("status", ["planned", "manual_review", "delivered"])
def test_only_placed_orders_can_be_prepared(client, people, status):
    order = make_order(people["alice"], status=status)
    sign_in(client, people["employee"])
    assert prepare(client, order).status_code == 409


def test_unpreparing_takes_the_order_off_its_trip(client, people):
    a, b = make_order(people["alice"]), make_order(people["bob"])
    sign_in(client, people["employee"])
    trip_id = prepare(client, a).get_json()["trip"]["id"]
    prepare(client, b)
    resp = client.patch(f"/api/orders/{a.id}/status", json={"status": "placed"})
    assert resp.status_code == 200 and resp.get_json()["tripId"] is None
    assert db.session.get(Trip, trip_id).orders == [db.session.get(Order, b.id)]


def test_trip_left_empty_is_removed(client, people):
    order = make_order(people["alice"])
    sign_in(client, people["employee"])
    prepare(client, order)
    client.patch(f"/api/orders/{order.id}/status", json={"status": "manual_review"})
    assert Trip.query.count() == 0


def test_orders_on_a_dispatched_trip_cannot_be_unprepared(client, people):
    order = make_order(people["alice"])
    sign_in(client, people["employee"])
    trip_id = prepare(client, order).get_json()["trip"]["id"]
    db.session.get(Trip, trip_id).status = "dispatched"
    db.session.commit()
    resp = client.patch(f"/api/orders/{order.id}/status", json={"status": "placed"})
    assert resp.status_code == 409 and resp.get_json()["error"] == "trip_dispatched"


def test_order_shows_customer_name(client, people):
    make_order(people["alice"])
    sign_in(client, people["employee"])
    assert client.get("/api/orders").get_json()["orders"][0]["customerName"] == "alice"

