from decimal import Decimal

import pytest
import stripe

from app.blueprints import payments as pay
from app.extensions import db
from app.models import Cart, Order, Payment, Product, User

KEY = "key-12345678"
ADDRESS = "150 S 1st St, San Jose"
DOWNTOWN = {"lat": 37.333, "lng": -121.889, "place_name": "150 S 1st St, San Jose, CA 95113"}


@pytest.fixture(autouse=True)
def stripe_config(app, monkeypatch):
    app.config["STRIPE_SECRET_KEY"] = "sk_test_x"
    app.config["STRIPE_WEBHOOK_SECRET"] = "whsec_x"
    monkeypatch.setattr(pay, "geocode", lambda address: DOWNTOWN)


@pytest.fixture
def calls(monkeypatch):
    log = []

    def fake_create(amount_cents, key, metadata):
        log.append((amount_cents, key, metadata))
        return {"id": f"pi_{len(log)}", "client_secret": f"secret_{len(log)}"}

    monkeypatch.setattr(pay, "create_payment_intent", fake_create)
    monkeypatch.setattr(pay, "cancel_payment_intent", lambda intent_id: log.append(("cancel", intent_id)))
    monkeypatch.setattr(pay, "refund_payment_intent", lambda intent_id, key: log.append(("refund", intent_id, key)))
    stripe_says(monkeypatch, "requires_payment_method")  # polling: not paid yet unless a test says so
    return log


def stripe_says(monkeypatch, status):
    """What Stripe reports for any PaymentIntent when GET /api/payments/<id> asks it."""
    monkeypatch.setattr(pay, "retrieve_payment_intent", lambda intent_id: {"id": intent_id, "status": status})


def sign_in(client, email="a@example.com"):
    if not User.query.filter_by(email=email).first():
        user = User(email=email, name="A", role="customer")
        user.set_password("password123")
        db.session.add(user)
        db.session.commit()
    assert client.post("/api/auth/login", json={"email": email, "password": "password123"}).status_code == 200


def fill_cart(client, price="10.00", weight="10.00", qty=1, stock=100):
    p = Product(name="Thing", category="X", price=Decimal(price), weight_lb=Decimal(weight), stock_qty=stock)
    db.session.add(p)
    db.session.commit()
    assert client.put(f"/api/cart/items/{p.product_id}", json={"quantity": qty}).status_code == 200
    return p


def start(client, key=KEY, address=ADDRESS):
    return client.post("/api/payments", json={"idempotencyKey": key, "address": address})


def event(monkeypatch, kind, intent_id="pi_1", message=None):
    obj = {"id": intent_id}
    if message:
        obj["last_payment_error"] = {"message": message}
    monkeypatch.setattr(
        stripe.Webhook, "construct_event", lambda payload, sig, secret: {"type": kind, "data": {"object": obj}}
    )


def hook(client):
    return client.post("/api/payments/webhook", data=b"{}", headers={"Stripe-Signature": "t"})


# ============ POST /api/payments ============

def test_requires_login(client):
    assert start(client).status_code == 401


@pytest.mark.parametrize("key", [None, "", "short", "x" * 65, 12345678])
def test_invalid_key(client, calls, key):
    sign_in(client)
    resp = client.post("/api/payments", json={"idempotencyKey": key, "address": ADDRESS})
    assert resp.status_code == 400 and not calls


def test_empty_cart_rejected_before_stripe(client, calls):
    sign_in(client)
    resp = start(client)
    assert resp.status_code == 400 and resp.get_json()["error"] == "empty_cart" and not calls


def test_overweight_rejected_before_stripe(client, calls):
    sign_in(client)
    fill_cart(client, weight="100.00", qty=3)
    resp = start(client)
    assert resp.status_code == 409 and resp.get_json()["error"] == "overweight" and not calls


def test_amount_is_server_total_with_fee_at_20_lb(client, calls):
    sign_in(client)
    fill_cart(client, price="10.00", weight="10.00", qty=2)  # 20 lb: $20 + $10 fee
    resp = start(client)
    body = resp.get_json()
    assert resp.status_code == 201 and body["amountCents"] == 3000 and body["clientSecret"] == "secret_1"
    assert calls[0][0] == 3000 and calls[0][1] == KEY


def test_no_fee_under_20_lb(client, calls):
    sign_in(client)
    fill_cart(client, price="6.49", weight="1.60", qty=3)
    assert start(client).get_json()["amountCents"] == 1947


def test_double_submit_charges_once(client, calls):
    sign_in(client)
    fill_cart(client)
    first, second = start(client), start(client)
    assert first.status_code == 201 and second.status_code == 200
    assert first.get_json()["paymentId"] == second.get_json()["paymentId"]
    assert len(calls) == 1 and Payment.query.count() == 1


def test_new_key_new_payment(client, calls):
    sign_in(client)
    fill_cart(client)
    start(client, "key-aaaaaaaa")
    start(client, "key-bbbbbbbb")
    assert len(calls) == 2 and Payment.query.count() == 2


def test_key_reuse_by_other_user_conflicts(client, calls):
    sign_in(client, "a@example.com")
    fill_cart(client)
    start(client)
    client.post("/api/auth/logout")
    sign_in(client, "b@example.com")
    assert start(client).status_code == 409


def test_unavailable_when_stripe_key_unset(client, calls, app):
    app.config["STRIPE_SECRET_KEY"] = None
    sign_in(client)
    fill_cart(client)
    resp = start(client)
    assert resp.status_code == 503 and not calls and Payment.query.count() == 0


def test_stripe_error_marks_failed_and_hides_details(client, monkeypatch):
    def boom(*a, **k):
        raise stripe.error.APIConnectionError("secret internals")

    monkeypatch.setattr(pay, "create_payment_intent", boom)
    sign_in(client)
    fill_cart(client)
    resp = start(client)
    assert resp.status_code == 502 and "secret internals" not in resp.get_data(as_text=True)
    assert Payment.query.one().status == "failed"


# ============ webhook ============

def paid_setup(client, calls):
    sign_in(client)
    fill_cart(client)
    start(client)


def test_webhook_success(client, calls, monkeypatch):
    paid_setup(client, calls)
    event(monkeypatch, "payment_intent.succeeded")
    assert hook(client).status_code == 200
    assert Payment.query.one().status == "succeeded"


def test_webhook_failed_records_reason(client, calls, monkeypatch):
    paid_setup(client, calls)
    event(monkeypatch, "payment_intent.payment_failed", message="Your card was declined.")
    hook(client)
    p = Payment.query.one()
    assert p.status == "failed" and p.failure_reason == "Your card was declined."


def test_webhook_canceled(client, calls, monkeypatch):
    paid_setup(client, calls)
    event(monkeypatch, "payment_intent.canceled")
    hook(client)
    assert Payment.query.one().status == "canceled"


def test_webhook_replay_and_no_downgrade(client, calls, monkeypatch):
    paid_setup(client, calls)
    event(monkeypatch, "payment_intent.succeeded")
    hook(client)
    hook(client)
    event(monkeypatch, "payment_intent.payment_failed", message="late")
    hook(client)
    p = Payment.query.one()
    assert p.status == "succeeded" and p.failure_reason is None


def test_webhook_unknown_intent_ignored(client, calls, monkeypatch):
    paid_setup(client, calls)
    event(monkeypatch, "payment_intent.succeeded", intent_id="pi_nope")
    assert hook(client).status_code == 200
    assert Payment.query.one().status == "pending"


def test_webhook_bad_signature(client):
    resp = client.post("/api/payments/webhook", data=b"{}", headers={"Stripe-Signature": "bad"})
    assert resp.status_code == 400


def test_webhook_secret_unset(client, app):
    app.config["STRIPE_WEBHOOK_SECRET"] = None
    assert client.post("/api/payments/webhook", data=b"{}").status_code == 503


# ============ GET / cancel ============

def test_get_payment_owner_only(client, calls):
    paid_setup(client, calls)
    pid = Payment.query.one().id
    assert client.get(f"/api/payments/{pid}").get_json()["status"] == "pending"
    client.post("/api/auth/logout")
    assert client.get(f"/api/payments/{pid}").status_code == 401
    sign_in(client, "b@example.com")
    assert client.get(f"/api/payments/{pid}").status_code == 404
    assert client.post(f"/api/payments/{pid}/cancel").status_code == 404


def test_cancel_pending(client, calls):
    paid_setup(client, calls)
    pid = Payment.query.one().id
    resp = client.post(f"/api/payments/{pid}/cancel")
    assert resp.status_code == 200 and resp.get_json()["status"] == "canceled"
    assert ("cancel", "pi_1") in calls
    assert client.post(f"/api/payments/{pid}/cancel").status_code == 409


def test_cannot_cancel_succeeded(client, calls, monkeypatch):
    paid_setup(client, calls)
    event(monkeypatch, "payment_intent.succeeded")
    hook(client)
    pid = Payment.query.one().id
    assert client.post(f"/api/payments/{pid}/cancel").get_json()["error"] == "not_cancelable"


# ============ address at checkout ============

@pytest.mark.parametrize("address", [None, "", "   ", "x" * 301])
def test_address_required(client, calls, address):
    sign_in(client)
    fill_cart(client)
    resp = start(client, address=address)
    assert resp.status_code == 400 and resp.get_json()["error"] == "invalid_address" and not calls


def test_address_not_found(client, calls, monkeypatch):
    monkeypatch.setattr(pay, "geocode", lambda address: None)
    sign_in(client)
    fill_cart(client)
    assert start(client).status_code == 404 and not calls


def test_address_outside_zone(client, calls, monkeypatch):
    monkeypatch.setattr(pay, "geocode", lambda address: {"lat": 37.77, "lng": -122.42, "place_name": "SF"})
    sign_in(client)
    fill_cart(client)
    resp = start(client)
    assert resp.status_code == 422 and resp.get_json()["error"] == "OUTSIDE_DELIVERY_ZONE" and not calls


# ============ webhook -> Order ============

def test_success_places_order(client, calls, monkeypatch):
    sign_in(client)
    p = fill_cart(client, price="10.00", weight="10.00", qty=2, stock=5)
    start(client)
    event(monkeypatch, "payment_intent.succeeded")
    hook(client)

    order = Order.query.one()
    assert order.status == "placed" and float(order.total) == 30.0 and float(order.delivery_fee) == 10.0
    assert order.delivery_address == DOWNTOWN["place_name"] and order.delivery_lat == DOWNTOWN["lat"]
    assert [(l.product_id, l.name, float(l.unit_price), l.quantity) for l in order.lines] == [
        (p.product_id, "Thing", 10.0, 2)
    ]
    assert db.session.get(Product, p.product_id).stock_qty == 3
    assert Cart.query.one().lines == []
    assert client.get(f"/api/payments/{Payment.query.one().id}").get_json()["orderId"] == order.id


def test_replayed_success_places_one_order(client, calls, monkeypatch):
    sign_in(client)
    p = fill_cart(client, stock=5)
    start(client)
    event(monkeypatch, "payment_intent.succeeded")
    hook(client)
    hook(client)
    assert Order.query.count() == 1 and db.session.get(Product, p.product_id).stock_qty == 4


def test_order_keeps_price_snapshot(client, calls, monkeypatch):
    sign_in(client)
    p = fill_cart(client, price="10.00")
    start(client)
    event(monkeypatch, "payment_intent.succeeded")
    hook(client)
    p.price = Decimal("99.00")
    db.session.commit()
    assert float(Order.query.one().lines[0].unit_price) == 10.0


def test_sold_out_mid_payment_refunds(client, calls, monkeypatch):
    sign_in(client)
    p = fill_cart(client, qty=2, stock=2)
    start(client)
    p.stock_qty = 1  # someone else bought one while this customer was paying
    db.session.commit()
    event(monkeypatch, "payment_intent.succeeded")
    assert hook(client).status_code == 200

    payment = Payment.query.one()
    assert payment.status == "refunded" and "sold out" in payment.failure_reason
    assert ("refund", "pi_1", f"refund-{payment.id}") in calls
    assert Order.query.count() == 0 and db.session.get(Product, p.product_id).stock_qty == 1
    assert len(Cart.query.one().lines) == 1  # nothing bought, cart left alone


def test_cart_changed_mid_payment_refunds(client, calls, monkeypatch):
    sign_in(client)
    p = fill_cart(client, qty=1)
    start(client)
    client.put(f"/api/cart/items/{p.product_id}", json={"quantity": 3})
    event(monkeypatch, "payment_intent.succeeded")
    hook(client)
    assert Payment.query.one().status == "refunded" and Order.query.count() == 0


def test_refund_error_lets_stripe_retry(client, calls, monkeypatch):
    def boom(*a, **k):
        raise stripe.error.APIConnectionError("down")

    sign_in(client)
    p = fill_cart(client, qty=2, stock=2)
    start(client)
    p.stock_qty = 0
    db.session.commit()
    monkeypatch.setattr(pay, "refund_payment_intent", boom)
    event(monkeypatch, "payment_intent.succeeded")
    assert hook(client).status_code == 500
    assert Payment.query.one().status == "pending"


def test_refunded_not_downgraded(client, calls, monkeypatch):
    sign_in(client)
    p = fill_cart(client, qty=1, stock=1)
    start(client)
    p.stock_qty = 0
    db.session.commit()
    event(monkeypatch, "payment_intent.succeeded")
    hook(client)
    event(monkeypatch, "payment_intent.payment_failed", message="late")
    hook(client)
    assert Payment.query.one().status == "refunded"


# ============ polling catches up without the webhook ============

def poll(client):
    return client.get(f"/api/payments/{Payment.query.one().id}").get_json()


def test_poll_places_order_without_webhook(client, calls, monkeypatch):
    sign_in(client)
    p = fill_cart(client, qty=2, stock=5)
    start(client)
    assert poll(client)["orderId"] is None  # Stripe hasn't charged it yet

    stripe_says(monkeypatch, "succeeded")
    body = poll(client)
    assert body["status"] == "succeeded" and body["orderId"] == Order.query.one().id
    assert db.session.get(Product, p.product_id).stock_qty == 3


def test_poll_then_webhook_places_one_order(client, calls, monkeypatch):
    sign_in(client)
    p = fill_cart(client, stock=5)
    start(client)
    stripe_says(monkeypatch, "succeeded")
    poll(client)
    event(monkeypatch, "payment_intent.succeeded")
    assert hook(client).status_code == 200
    assert Order.query.count() == 1 and db.session.get(Product, p.product_id).stock_qty == 4
    assert not [c for c in calls if c[0] == "refund"]


def test_webhook_then_poll_places_one_order(client, calls, monkeypatch):
    sign_in(client)
    fill_cart(client)
    start(client)
    event(monkeypatch, "payment_intent.succeeded")
    hook(client)
    stripe_says(monkeypatch, "succeeded")
    assert poll(client)["orderId"] == Order.query.one().id and Order.query.count() == 1


def test_losing_the_race_never_refunds_a_placed_order(client, calls, monkeypatch):
    # The other path placed the order and emptied the cart between our status check and our claim.
    sign_in(client)
    fill_cart(client)
    start(client)
    event(monkeypatch, "payment_intent.succeeded")
    hook(client)
    payment = Payment.query.one()
    assert pay.settle_succeeded(payment) is True  # sees an empty cart, but must not claim or refund
    assert payment.status == "succeeded" and Order.query.count() == 1
    assert not [c for c in calls if c[0] == "refund"]


def test_poll_sold_out_refunds(client, calls, monkeypatch):
    sign_in(client)
    p = fill_cart(client, qty=1, stock=1)
    start(client)
    p.stock_qty = 0
    db.session.commit()
    stripe_says(monkeypatch, "succeeded")
    body = poll(client)
    assert body["status"] == "refunded" and body["orderId"] is None
    assert [c for c in calls if c[0] == "refund"] == [("refund", "pi_1", f"refund-{body['paymentId']}")]


def test_poll_survives_stripe_errors(client, calls, monkeypatch):
    def boom(intent_id):
        raise stripe.error.APIConnectionError("down")

    sign_in(client)
    fill_cart(client)
    start(client)
    monkeypatch.setattr(pay, "retrieve_payment_intent", boom)
    resp = client.get(f"/api/payments/{Payment.query.one().id}")
    assert resp.status_code == 200 and resp.get_json()["status"] == "pending"


def test_poll_skips_stripe_once_final(client, calls, monkeypatch):
    sign_in(client)
    fill_cart(client)
    start(client)
    event(monkeypatch, "payment_intent.succeeded")
    hook(client)

    def must_not_call(intent_id):
        raise AssertionError("final payments shouldn't hit Stripe")

    monkeypatch.setattr(pay, "retrieve_payment_intent", must_not_call)
    assert poll(client)["status"] == "succeeded"

