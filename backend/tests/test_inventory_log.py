# T05 / T12: every Stock change writes an inventory_log row. Owner: Karnani Shresthkumar.
from decimal import Decimal

import pytest
import stripe

from app.blueprints import payments as pay
from app.extensions import db
from app.models import InventoryLog, Order, OrderLine, Product, Trip, User

PASSWORD = "password123"
DOWNTOWN = {"lat": 37.333, "lng": -121.889, "place_name": "150 S 1st St, San Jose, CA 95113"}


def make_user(email, role="customer"):
    user = User(email=email, name=email.split("@")[0], role=role)
    user.set_password(PASSWORD)
    db.session.add(user)
    db.session.commit()
    return user


def sign_in(client, user):
    client.post("/api/auth/logout")
    assert client.post("/api/auth/login", json={"email": user.email, "password": PASSWORD}).status_code == 200


def make_product(stock=10, name="Apple"):
    p = Product(name=name, category="Fruit", price=Decimal("1.50"), weight_lb=Decimal("0.50"), stock_qty=stock)
    db.session.add(p)
    db.session.commit()
    return p


def make_order(user, product, quantity=2, status="placed", trip=None):
    order = Order(
        user_id=user.id, status=status, subtotal=Decimal("3.00"), delivery_fee=Decimal("0"),
        total=Decimal("3.00"), weight_lb=Decimal("1.00"), delivery_address="1 Main St",
        delivery_lat=37.33, delivery_lng=-121.89, trip_id=trip.id if trip else None,
    )
    order.lines.append(OrderLine(product_id=product.product_id, name=product.name, unit_price=product.price,
                                 weight_lb=product.weight_lb, quantity=quantity))
    db.session.add(order)
    db.session.commit()
    return order


def logs(product=None):
    query = InventoryLog.query.order_by(InventoryLog.id)
    if product is not None:
        query = query.filter_by(product_id=product.product_id)
    return query.all()


def stock(product):
    return db.session.get(Product, product.product_id, populate_existing=True).stock_qty


@pytest.fixture
def people(app):
    return {
        "alice": make_user("alice@example.com"),
        "employee": make_user("emp@example.com", "employee"),
        "manager": make_user("mgr@example.com", "manager"),
    }


# ============ SALE: the Stripe webhook places the Order ============

@pytest.fixture
def stripe_ok(app, monkeypatch):
    app.config["STRIPE_SECRET_KEY"] = "sk_test_x"
    app.config["STRIPE_WEBHOOK_SECRET"] = "whsec_x"
    monkeypatch.setattr(pay, "geocode", lambda address: DOWNTOWN)
    monkeypatch.setattr(pay, "create_payment_intent",
                        lambda amount_cents, key, metadata: {"id": "pi_1", "client_secret": "secret_1"})
    monkeypatch.setattr(pay, "refund_payment_intent", lambda intent_id, key: None)
    monkeypatch.setattr(pay, "retrieve_payment_intent",
                        lambda intent_id: {"id": intent_id, "status": "requires_payment_method"})
    monkeypatch.setattr(stripe.Webhook, "construct_event",
                        lambda payload, sig, secret: {"type": "payment_intent.succeeded",
                                                      "data": {"object": {"id": "pi_1"}}})


def checkout(client, product, quantity):
    assert client.put(f"/api/cart/items/{product.product_id}", json={"quantity": quantity}).status_code == 200
    assert client.post("/api/payments", json={"idempotencyKey": "key-12345678",
                                              "address": "150 S 1st St"}).status_code in (200, 201)


def webhook(client):
    return client.post("/api/payments/webhook", data=b"{}", headers={"Stripe-Signature": "t"})


def test_a_sale_is_logged_with_its_order(client, people, stripe_ok):
    p = make_product(stock=5)
    sign_in(client, people["alice"])
    checkout(client, p, 2)
    webhook(client)

    order = Order.query.one()
    [entry] = logs(p)
    assert (entry.reason, entry.before_qty, entry.change_qty, entry.after_qty) == ("SALE", 5, -2, 3)
    assert entry.order_id == order.id and entry.user_id == people["alice"].id
    assert stock(p) == 3


def test_a_replayed_webhook_logs_one_sale(client, people, stripe_ok):
    p = make_product(stock=5)
    sign_in(client, people["alice"])
    checkout(client, p, 1)
    webhook(client)
    webhook(client)
    assert [e.reason for e in logs(p)] == ["SALE"] and stock(p) == 4


def test_a_refunded_payment_logs_nothing(client, people, stripe_ok):
    p = make_product(stock=5)
    sign_in(client, people["alice"])
    checkout(client, p, 2)
    p.stock_qty = 1  # sold out while the customer was paying, so the payment is refunded
    db.session.commit()
    webhook(client)
    assert Order.query.count() == 0 and logs() == [] and stock(p) == 1


# ============ Manager stock edits: RESTOCK / RETURN / CORRECTION ============

def patch(client, product, body):
    return client.patch(f"/api/products/{product.product_id}", json=body)


def test_raising_stock_logs_a_restock_by_the_manager(client, people):
    p = make_product(stock=10)
    sign_in(client, people["manager"])
    assert patch(client, p, {"stock_qty": 25}).status_code == 200
    [entry] = logs(p)
    assert (entry.reason, entry.before_qty, entry.change_qty, entry.after_qty) == ("RESTOCK", 10, 15, 25)
    assert entry.user_id == people["manager"].id and entry.order_id is None


def test_lowering_stock_logs_a_correction(client, people):
    p = make_product(stock=10)
    sign_in(client, people["manager"])
    assert patch(client, p, {"stock_qty": 7}).status_code == 200
    [entry] = logs(p)
    assert (entry.reason, entry.change_qty, entry.after_qty) == ("CORRECTION", -3, 7)


def test_manager_can_give_a_reason_and_note(client, people):
    p = make_product(stock=10)
    sign_in(client, people["manager"])
    body = {"stock_qty": 12, "stock_reason": "RETURN", "stock_note": "  customer brought back 2  "}
    assert patch(client, p, body).status_code == 200
    [entry] = logs(p)
    assert (entry.reason, entry.change_qty, entry.note) == ("RETURN", 2, "customer brought back 2")


def test_a_correction_can_add_stock(client, people):
    p = make_product(stock=10)
    sign_in(client, people["manager"])
    assert patch(client, p, {"stock_qty": 11, "stock_reason": "CORRECTION"}).status_code == 200
    assert logs(p)[0].reason == "CORRECTION"


@pytest.mark.parametrize("body", [
    {"stock_qty": 5, "stock_reason": "RESTOCK"},   # a restock can't remove stock
    {"stock_qty": 5, "stock_reason": "RETURN"},
    {"stock_qty": 15, "stock_reason": "SALE"},     # only checkout writes sales
    {"stock_qty": 15, "stock_reason": "CANCEL"},   # only an Order Override writes cancels
    {"stock_qty": 15, "stock_reason": "restock"},
    {"stock_qty": 15, "stock_note": 7},
    {"stock_qty": 15, "stock_note": "x" * 501},
])
def test_bad_reason_or_note_changes_nothing(client, people, body):
    p = make_product(stock=10)
    sign_in(client, people["manager"])
    assert patch(client, p, {**body, "price": 2}).status_code == 400
    assert stock(p) == 10 and logs() == [] and db.session.get(Product, p.product_id).price == Decimal("1.50")


@pytest.mark.parametrize("body", [{"stock_qty": 10}, {"price": 2.25}, {"name": "Green Apple"}])
def test_edits_that_leave_stock_alone_log_nothing(client, people, body):
    p = make_product(stock=10)
    sign_in(client, people["manager"])
    assert patch(client, p, body).status_code == 200
    assert logs() == [] and stock(p) == 10


def test_stock_and_other_fields_change_together(client, people):
    p = make_product(stock=10)
    sign_in(client, people["manager"])
    resp = patch(client, p, {"stock_qty": 4, "price": 2.25})
    assert resp.status_code == 200 and resp.get_json()["stock"] == 4 and resp.get_json()["price"] == 2.25
    assert [(e.reason, e.change_qty) for e in logs(p)] == [("CORRECTION", -6)]


def test_creating_a_product_logs_nothing(client, people):
    sign_in(client, people["manager"])
    body = {"name": "Honey", "category": "Pantry", "price": 8.5, "weight_lb": 1.0, "stock_qty": 10}
    assert client.post("/api/products", json=body).status_code == 201
    assert logs() == []  # history starts here: the first change's before_qty is the starting Stock


# ============ CANCEL: a Manager Order Override puts the items back ============

def cancel(client, order, reason="Customer called to cancel"):
    return client.post(f"/api/orders/{order.id}/override",
                       json={"action": "cancel", "reason": reason, "confirmed": True})


@pytest.mark.parametrize("status", ["placed", "planned", "manual_review", "delivery_failed"])
def test_cancel_returns_the_items_to_stock(client, people, status):
    p = make_product(stock=8)
    order = make_order(people["alice"], p, quantity=2, status=status)
    sign_in(client, people["manager"])
    assert cancel(client, order).status_code == 200

    assert stock(p) == 10
    [entry] = logs(p)
    assert (entry.reason, entry.before_qty, entry.change_qty, entry.after_qty) == ("CANCEL", 8, 2, 10)
    assert entry.order_id == order.id and entry.user_id == people["manager"].id
    assert entry.note == "Customer called to cancel"


def test_cancel_returns_every_line(client, people):
    apple, pear = make_product(stock=8), make_product(stock=1, name="Pear")
    order = make_order(people["alice"], apple, quantity=2)
    order.lines.append(OrderLine(product_id=pear.product_id, name="Pear", unit_price=pear.price,
                                 weight_lb=pear.weight_lb, quantity=3))
    db.session.commit()
    sign_in(client, people["manager"])
    assert cancel(client, order).status_code == 200
    assert (stock(apple), stock(pear)) == (10, 4)
    assert sorted((e.product_id, e.change_qty) for e in logs()) == sorted(
        [(apple.product_id, 2), (pear.product_id, 3)])


def test_cancelling_twice_restocks_once(client, people):
    p = make_product(stock=8)
    order = make_order(people["alice"], p, quantity=2)
    sign_in(client, people["manager"])
    assert cancel(client, order).status_code == 200
    assert cancel(client, order).status_code == 409
    assert stock(p) == 10 and len(logs(p)) == 1


@pytest.mark.parametrize("status", ["delivered"])
def test_refused_cancel_moves_no_stock(client, people, status):
    p = make_product(stock=8)
    order = make_order(people["alice"], p, quantity=2, status=status)
    sign_in(client, people["manager"])
    assert cancel(client, order).status_code == 409
    assert stock(p) == 8 and logs() == []


def test_cancel_refused_once_the_trip_left_moves_no_stock(client, people):
    p = make_product(stock=8)
    trip = Trip(status="ready", ready_reason="full")
    db.session.add(trip)
    db.session.commit()
    order = make_order(people["alice"], p, quantity=2, status="planned", trip=trip)
    sign_in(client, people["manager"])
    assert cancel(client, order).status_code == 409
    assert stock(p) == 8 and logs() == []


def test_employee_cancel_is_forbidden_and_moves_no_stock(client, people):
    p = make_product(stock=8)
    order = make_order(people["alice"], p, quantity=2)
    sign_in(client, people["employee"])
    assert cancel(client, order).status_code == 403
    assert stock(p) == 8 and logs() == []


# ============ GET /api/products/<id>/inventory-log ============

def test_manager_sees_history_newest_first(client, people):
    p = make_product(stock=10)
    sign_in(client, people["manager"])
    patch(client, p, {"stock_qty": 20})
    patch(client, p, {"stock_qty": 18, "stock_note": "2 bruised"})

    resp = client.get(f"/api/products/{p.product_id}/inventory-log")
    assert resp.status_code == 200
    body = resp.get_json()
    assert (body["productId"], body["name"], body["stock"]) == (p.product_id, "Apple", 18)
    assert [(e["reason"], e["beforeQty"], e["changeQty"], e["afterQty"]) for e in body["entries"]] == [
        ("CORRECTION", 20, -2, 18), ("RESTOCK", 10, 10, 20)]
    newest = body["entries"][0]
    assert newest["note"] == "2 bruised" and newest["userName"] == "mgr" and newest["orderId"] is None
    assert newest["createdAt"].endswith("+00:00")


def test_history_only_shows_that_product(client, people):
    apple, pear = make_product(stock=10), make_product(stock=10, name="Pear")
    sign_in(client, people["manager"])
    patch(client, apple, {"stock_qty": 11})
    patch(client, pear, {"stock_qty": 12})
    entries = client.get(f"/api/products/{apple.product_id}/inventory-log").get_json()["entries"]
    assert [e["productId"] for e in entries] == [apple.product_id]


def test_history_of_a_product_with_no_changes_is_empty(client, people):
    p = make_product(stock=10)
    sign_in(client, people["manager"])
    assert client.get(f"/api/products/{p.product_id}/inventory-log").get_json()["entries"] == []


def test_history_of_unknown_product_is_404(client, people):
    sign_in(client, people["manager"])
    assert client.get("/api/products/9999/inventory-log").status_code == 404


def test_history_requires_a_manager(client, people):
    p = make_product()
    url = f"/api/products/{p.product_id}/inventory-log"
    assert client.get(url).status_code == 401
    sign_in(client, people["alice"])
    assert client.get(url).status_code == 403
    sign_in(client, people["employee"])
    assert client.get(url).status_code == 403


# ============ Deleting a product keeps its history ============

def test_product_with_stock_history_cannot_be_deleted(client, people):
    p = make_product(stock=10)
    sign_in(client, people["manager"])
    patch(client, p, {"stock_qty": 12})
    resp = client.delete(f"/api/products/{p.product_id}")
    assert resp.status_code == 409 and "Deactivate" in resp.get_json()["error"]
    assert db.session.get(Product, p.product_id) is not None and len(logs(p)) == 1


def test_ordered_product_cannot_be_deleted(client, people):
    p = make_product(stock=10)
    make_order(people["alice"], p)
    sign_in(client, people["manager"])
    resp = client.delete(f"/api/products/{p.product_id}")
    assert resp.status_code == 409 and "Deactivate" in resp.get_json()["error"]


def test_product_without_history_can_still_be_deleted(client, people):
    p = make_product(stock=10)
    sign_in(client, people["manager"])
    assert client.delete(f"/api/products/{p.product_id}").status_code == 200
    assert db.session.get(Product, p.product_id) is None
