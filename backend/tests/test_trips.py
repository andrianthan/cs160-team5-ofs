from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from app.extensions import db
from app.models import Order, OrderLine, Product, Trip, User
from app.planning import distance_km

PASSWORD = "password123"
CITY_HALL = (37.3377, -121.8858)
NEAR_CITY_HALL = (37.3404, -121.8858)  # ~0.3 km north
SAP_CENTER = (37.3328, -121.9010)  # ~1.4 km west of City Hall


def make_user(email, role="customer"):
    user = User(email=email, name=email.split("@")[0], role=role)
    user.set_password(PASSWORD)
    db.session.add(user)
    db.session.commit()
    return user


def make_order(user, at=CITY_HALL, weight="1.00", placed_minutes_ago=0):
    p = Product(name="Apple", category="Fruit", price=Decimal("1.50"), weight_lb=Decimal("0.50"), stock_qty=10)
    db.session.add(p)
    db.session.flush()
    order = Order(
        user_id=user.id, subtotal=Decimal("3.00"), delivery_fee=Decimal("0"), total=Decimal("3.00"),
        weight_lb=Decimal(weight), delivery_address="somewhere downtown", delivery_lat=at[0], delivery_lng=at[1],
        created_at=datetime.now(timezone.utc) - timedelta(minutes=placed_minutes_ago),
    )
    order.lines.append(OrderLine(product_id=p.product_id, name="Apple", unit_price=p.price,
                                 weight_lb=p.weight_lb, quantity=2))
    db.session.add(order)
    db.session.commit()
    return order


@pytest.fixture
def staff(app, client):
    customer = make_user("casey@example.com")
    employee = make_user("emp@example.com", "employee")
    assert client.post("/api/auth/login", json={"email": employee.email, "password": PASSWORD}).status_code == 200
    return customer


def prepare(client, order):
    return client.post(f"/api/orders/{order.id}/prepare").get_json()["trip"]


def trips(client):
    return client.get("/api/trips").get_json()["trips"]


def test_distances_are_sane():
    assert distance_km(*CITY_HALL, *NEAR_CITY_HALL) == pytest.approx(0.3, abs=0.05)
    assert distance_km(*CITY_HALL, *SAP_CENTER) == pytest.approx(1.4, abs=0.1)


# ============ grouping nearby Orders ============

def test_nearby_orders_share_a_trip(client, staff):
    a, b = make_order(staff, CITY_HALL), make_order(staff, NEAR_CITY_HALL)
    assert prepare(client, a)["id"] == prepare(client, b)["id"]


def test_far_order_starts_its_own_trip(client, staff):
    a, b = make_order(staff, CITY_HALL), make_order(staff, SAP_CENTER)
    assert prepare(client, a)["id"] != prepare(client, b)["id"]


def test_order_must_be_near_every_order_on_the_trip(client, staff):
    # 0.4 km apart each step: B is near A, C is near B but ~0.8 km from A, so C can't join.
    a = make_order(staff, (37.3377, -121.8858))
    b = make_order(staff, (37.3413, -121.8858))
    c = make_order(staff, (37.3449, -121.8858))
    t = prepare(client, a)["id"]
    assert prepare(client, b)["id"] == t
    assert prepare(client, c)["id"] != t


def test_order_joins_the_closest_trip_that_fits(client, staff):
    west, east = make_order(staff, SAP_CENTER), make_order(staff, CITY_HALL)
    west_trip, east_trip = prepare(client, west)["id"], prepare(client, east)["id"]
    near_east = make_order(staff, NEAR_CITY_HALL)
    assert prepare(client, near_east)["id"] == east_trip != west_trip


# ============ locking: full or past the deadline ============

def test_tenth_order_locks_the_trip_as_ready(client, staff):
    orders = [make_order(staff) for _ in range(10)]
    trip = [prepare(client, o) for o in orders][-1]
    assert trip["status"] == "ready" and trip["readyReason"] == "full"
    assert prepare(client, make_order(staff))["id"] != trip["id"]  # the 11th can't join


def test_200_lb_locks_the_trip(client, staff):
    trip = [prepare(client, make_order(staff, weight=w)) for w in ("150.00", "50.00")][-1]
    assert trip["status"] == "ready" and trip["readyReason"] == "full"


def test_trip_past_its_deadline_is_locked_when_listed(client, staff):
    old = make_order(staff, placed_minutes_ago=31)
    trip_id = prepare(client, old)["id"]
    listed = trips(client)
    assert listed[0]["id"] == trip_id and listed[0]["status"] == "ready"
    assert listed[0]["readyReason"] == "deadline" and listed[0]["overdue"] is True


def test_deadline_counts_from_the_oldest_order(client, staff):
    trip_id = prepare(client, make_order(staff, placed_minutes_ago=29))["id"]
    prepare(client, make_order(staff, placed_minutes_ago=0))
    trip = next(t for t in trips(client) if t["id"] == trip_id)
    assert trip["status"] == "open" and trip["overdue"] is False
    deadline = datetime.fromisoformat(trip["deadline"])
    assert timedelta(0) < deadline - datetime.now(timezone.utc) <= timedelta(minutes=1)


def test_overdue_trip_takes_no_more_orders(client, staff):
    old_trip = prepare(client, make_order(staff, placed_minutes_ago=45))["id"]
    new_trip = prepare(client, make_order(staff))["id"]  # same spot, but the old Trip is past its deadline
    assert new_trip != old_trip
    assert db.session.get(Trip, old_trip).status == "ready"


# ============ GET /api/trips ============

def test_trips_are_staff_only(client, app):
    assert client.get("/api/trips").status_code == 401
    customer = make_user("c@example.com")
    client.post("/api/auth/login", json={"email": customer.email, "password": PASSWORD})
    assert client.get("/api/trips").status_code == 403


def test_list_shows_ready_then_open_then_dispatched(client, staff):
    dispatched = prepare(client, make_order(staff, SAP_CENTER))["id"]
    client.post(f"/api/trips/{dispatched}/dispatch")
    open_trip = prepare(client, make_order(staff, CITY_HALL))["id"]
    ready = [prepare(client, make_order(staff, (37.3260, -121.8900))) for _ in range(10)][-1]["id"]
    assert [t["id"] for t in trips(client)] == [ready, open_trip, dispatched]


def test_list_includes_order_details_with_utc_times(client, staff):
    order = make_order(staff)
    prepare(client, order)
    listed = trips(client)[0]["orders"][0]
    assert listed["id"] == order.id and listed["customerName"] == "casey"
    assert datetime.fromisoformat(listed["createdAt"]).tzinfo is not None


# ============ POST /api/trips/<id>/dispatch ============

def test_dispatch_sends_the_orders_out(client, staff):
    a, b = make_order(staff), make_order(staff)
    trip_id = prepare(client, a)["id"]
    prepare(client, b)
    resp = client.post(f"/api/trips/{trip_id}/dispatch")
    assert resp.status_code == 200 and resp.get_json()["status"] == "dispatched"
    assert {db.session.get(Order, o.id).status for o in (a, b)} == {"out_for_delivery"}


def test_dispatched_trip_cannot_be_dispatched_again_or_take_orders(client, staff):
    trip_id = prepare(client, make_order(staff))["id"]
    client.post(f"/api/trips/{trip_id}/dispatch")
    assert client.post(f"/api/trips/{trip_id}/dispatch").status_code == 409
    assert prepare(client, make_order(staff))["id"] != trip_id


def test_dispatch_unknown_trip(client, staff):
    assert client.post("/api/trips/999/dispatch").status_code == 404


def test_order_can_leave_a_ready_trip_but_not_a_dispatched_one(client, staff):
    orders = [make_order(staff) for _ in range(10)]
    trip_id = [prepare(client, o) for o in orders][-1]["id"]  # full -> ready
    assert client.patch(f"/api/orders/{orders[0].id}/status", json={"status": "placed"}).status_code == 200
    client.post(f"/api/trips/{trip_id}/dispatch")
    # dispatched orders are out_for_delivery, so "back to placed" isn't a valid move any more
    resp = client.patch(f"/api/orders/{orders[1].id}/status", json={"status": "placed"})
    assert resp.status_code == 409 and db.session.get(Order, orders[1].id).trip_id == trip_id
