# T10 — Payments with Stripe test mode. Owner: Than Andrian.
# LLD 2 §2.3: create_payment_intent() with an idempotency key (no double-charge).
import stripe
from flask import Blueprint, current_app, jsonify, request
from flask_login import current_user
from sqlalchemy.exc import IntegrityError

from .. import notifications
from ..extensions import db
from ..models import Payment
from ..models.payment import CANCELED, FAILED, PENDING, REFUNDED, SUCCEEDED
from ..models.delivery_settings import deliveries_paused
from .addresses import geocode, inside_delivery_zone
from .cart import validate_cart_for_checkout
from .orders import place_order

bp = Blueprint("payments", __name__, url_prefix="/api/payments")

KEY_MIN, KEY_MAX = 8, 64
REASON_MAX = 300
CART_ERRORS = {"empty_cart": 400, "overweight": 409, "insufficient_stock": 409}
ADDRESS_MAX = 300
CART_CHANGED = "Your cart changed while you were paying, so no order was placed. You have been refunded."
# place_order() reasons -> what the customer sees on the refunded payment.
REFUND_REASONS = {
    "insufficient_stock": "An item sold out while you were paying, so no order was placed. You have been refunded.",
    "cart_changed": CART_CHANGED,
    "empty_cart": CART_CHANGED,
    "overweight": CART_CHANGED,
    "missing_address": "No delivery address was saved for this payment. You have been refunded.",
}


def create_payment_intent(amount_cents, key, metadata):
    """Thin Stripe wrapper so tests can monkeypatch it. Returns the PaymentIntent."""
    return stripe.PaymentIntent.create(
        amount=amount_cents,
        currency="usd",
        metadata=metadata,
        automatic_payment_methods={"enabled": True},
        idempotency_key=key,
        api_key=current_app.config["STRIPE_SECRET_KEY"],
    )


def cancel_payment_intent(intent_id):
    return stripe.PaymentIntent.cancel(intent_id, api_key=current_app.config["STRIPE_SECRET_KEY"])


def retrieve_payment_intent(intent_id):
    return stripe.PaymentIntent.retrieve(intent_id, api_key=current_app.config["STRIPE_SECRET_KEY"])


def refund_payment_intent(intent_id, key):
    """Full refund. The idempotency key makes webhook retries return the same refund, not a second one."""
    return stripe.Refund.create(
        payment_intent=intent_id, idempotency_key=key, api_key=current_app.config["STRIPE_SECRET_KEY"]
    )


def _error(code, message, status):
    return jsonify(error=code, message=message), status


# Not final yet: a declined card leaves the same PaymentIntent open for another try.
OPEN = (PENDING, FAILED)


def _claim(payment, **values):
    """Atomically move an open payment to a final state. False if the webhook or a poll already did.

    The conditional UPDATE is what makes the two paths safe to race: only one request can match
    status IN OPEN, so an Order is placed (or a refund issued) exactly once.
    """
    won = Payment.query.filter(Payment.id == payment.id, Payment.status.in_(OPEN)).update(
        values, synchronize_session="fetch"
    )
    return won == 1


def settle_succeeded(payment):
    """The payment's intent succeeded: place the Order, or refund when it can't be filled.

    Shared by the webhook and GET /api/payments/<id> polling, so checkout works even when webhooks
    can't reach the server (local dev without `stripe listen`). Commits or rolls back.
    Returns False only if the refund call failed, so the caller can ask Stripe to retry.
    """
    order, reason = place_order(payment)
    if order is not None:
        if _claim(payment, status=SUCCEEDED, failure_reason=None, order_id=order.id):
            order_id = order.id
            db.session.commit()
            notifications.notify_order_event(order_id, notifications.ORDER_PLACED)
        else:
            db.session.rollback()  # the other path placed it first
        return True

    if not _claim(payment, status=REFUNDED, failure_reason=REFUND_REASONS[reason]):
        db.session.rollback()
        return True
    try:
        refund_payment_intent(payment.stripe_payment_intent_id, f"refund-{payment.id}")
    except stripe.error.StripeError:
        db.session.rollback()  # back to open, so a retry can refund
        current_app.logger.exception("Stripe Refund.create failed")
        return False
    db.session.commit()
    return True


def _sync_with_stripe(payment):
    """Catch up a payment whose webhook hasn't arrived by asking Stripe for the intent's status."""
    if payment.status not in OPEN or not payment.stripe_payment_intent_id:
        return
    if not current_app.config.get("STRIPE_SECRET_KEY"):
        return
    try:
        intent = retrieve_payment_intent(payment.stripe_payment_intent_id)
    except stripe.error.StripeError:
        current_app.logger.exception("Stripe PaymentIntent.retrieve failed")
        return  # report what we have; the next poll tries again
    if intent["status"] == "succeeded":
        settle_succeeded(payment)
        db.session.refresh(payment)


def _unauth():
    return _error("unauthorized", "Sign in required.", 401)


def _view(payment, client_secret=None):
    out = {
        "paymentId": payment.id,
        "status": payment.status,
        "amountCents": payment.amount_cents,
        "failureReason": payment.failure_reason,
        "orderId": payment.order_id,
    }
    if client_secret:
        out["clientSecret"] = client_secret
    return out


def _owned(payment_id):
    payment = db.session.get(Payment, payment_id)
    return payment if payment and payment.user_id == current_user.id else None


@bp.post("")
def create_payment():
    if not current_user.is_authenticated:
        return _unauth()

    body = request.get_json(silent=True)
    key = body.get("idempotencyKey") if isinstance(body, dict) else None
    if not isinstance(key, str) or not KEY_MIN <= len(key) <= KEY_MAX:
        return _error("invalid_idempotency_key", f"idempotencyKey must be {KEY_MIN}-{KEY_MAX} characters.", 400)

    existing = Payment.query.filter_by(idempotency_key=key).first()
    if existing:
        if existing.user_id != current_user.id:
            return _error("idempotency_conflict", "That key is already in use.", 409)
        return jsonify(_view(existing)), 200

    # Existing idempotent requests remain retrievable.
    if deliveries_paused():
        return _error(
            "delivery_paused",
            "Deliveries are temporarily paused. Please try again later.",
            503
        )

    address = body.get("address")
    address = address.strip() if isinstance(address, str) else ""
    if not address or len(address) > ADDRESS_MAX:
        return _error("invalid_address", "Enter a delivery address.", 400)

    # Amount always comes from the server-side cart, never from the client.
    summary, err = validate_cart_for_checkout(current_user)
    if err:
        return _error(err, f"Cart cannot be checked out: {err.replace('_', ' ')}.", CART_ERRORS[err])

    geo = geocode(address)  # BR-5: same check as POST /api/addresses/validate
    if geo is None:
        return _error("ADDRESS_NOT_FOUND", "We couldn't find that address.", 404)
    if not inside_delivery_zone(geo):
        return _error("OUTSIDE_DELIVERY_ZONE", "This address is outside the Downtown San Jose Delivery Zone.", 422)

    if not current_app.config.get("STRIPE_SECRET_KEY"):
        return _error("payments_unavailable", "Payments are temporarily unavailable.", 503)

    amount_cents = round(summary["total"] * 100)
    payment = Payment(
        user_id=current_user.id, idempotency_key=key, amount_cents=amount_cents,
        delivery_address=geo["place_name"], delivery_lat=geo["lat"], delivery_lng=geo["lng"],
    )
    db.session.add(payment)
    try:
        db.session.commit()
    except IntegrityError:  # concurrent double submit with the same key
        db.session.rollback()
        existing = Payment.query.filter_by(idempotency_key=key, user_id=current_user.id).first()
        if existing:
            return jsonify(_view(existing)), 200
        return _error("idempotency_conflict", "That key is already in use.", 409)

    try:
        intent = create_payment_intent(
            amount_cents, key, {"user_id": current_user.id, "payment_id": payment.id}
        )
    except stripe.error.StripeError:
        current_app.logger.exception("Stripe PaymentIntent.create failed")
        payment.status = FAILED
        payment.failure_reason = "Payment provider error."
        db.session.commit()
        return _error("payment_provider_error", "We couldn't start your payment. Please try again.", 502)

    payment.stripe_payment_intent_id = intent["id"]
    db.session.commit()
    return jsonify(_view(payment, intent["client_secret"])), 201


@bp.post("/webhook")
def webhook():
    secret = current_app.config.get("STRIPE_WEBHOOK_SECRET")
    if not secret:
        return _error("payments_unavailable", "Webhook secret not configured.", 503)
    try:
        event = stripe.Webhook.construct_event(
            request.get_data(), request.headers.get("Stripe-Signature", ""), secret
        )
    except (ValueError, stripe.error.SignatureVerificationError):
        return _error("invalid_signature", "Bad webhook signature.", 400)

    intent = event["data"]["object"]
    payment = Payment.query.filter_by(stripe_payment_intent_id=intent["id"]).first()
    if payment is None or payment.status in (SUCCEEDED, REFUNDED):
        return jsonify(received=True), 200  # unknown intent, or already final: ignore

    kind = event["type"]
    if kind == "payment_intent.succeeded":
        if not settle_succeeded(payment):
            return _error("payment_provider_error", "Refund failed; Stripe will retry.", 500)
        return jsonify(received=True), 200
    if kind == "payment_intent.payment_failed":
        err = intent.get("last_payment_error") or {}
        payment.status = FAILED
        payment.failure_reason = (err.get("message") or "Payment failed.")[:REASON_MAX]
    elif kind == "payment_intent.canceled":
        payment.status = CANCELED
    db.session.commit()
    return jsonify(received=True), 200


@bp.get("/<int:payment_id>")
def get_payment(payment_id):
    if not current_user.is_authenticated:
        return _unauth()
    payment = _owned(payment_id)
    if payment is None:
        return _error("not_found", "Payment not found.", 404)
    _sync_with_stripe(payment)
    return jsonify(_view(payment))


@bp.post("/<int:payment_id>/cancel")
def cancel_payment(payment_id):
    if not current_user.is_authenticated:
        return _unauth()
    payment = _owned(payment_id)
    if payment is None:
        return _error("not_found", "Payment not found.", 404)
    if payment.status != PENDING:
        return _error("not_cancelable", "Only pending payments can be canceled.", 409)
    if payment.stripe_payment_intent_id:
        try:
            cancel_payment_intent(payment.stripe_payment_intent_id)
        except stripe.error.StripeError:
            current_app.logger.exception("Stripe PaymentIntent.cancel failed")
            return _error("payment_provider_error", "Couldn't cancel right now. Please try again.", 502)
    payment.status = CANCELED
    db.session.commit()
    return jsonify(_view(payment))
