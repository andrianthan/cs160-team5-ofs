# T10 — Payments with Stripe test mode. Owner: Than Andrian.
# LLD 2 §2.3: create_payment_intent() with an idempotency key (no double-charge).
import stripe
from flask import Blueprint, current_app, jsonify, request
from flask_login import current_user
from sqlalchemy.exc import IntegrityError

from ..extensions import db
from ..models import Payment
from ..models.payment import CANCELED, FAILED, PENDING, SUCCEEDED
from .cart import validate_cart_for_checkout

bp = Blueprint("payments", __name__, url_prefix="/api/payments")

KEY_MIN, KEY_MAX = 8, 64
REASON_MAX = 300
CART_ERRORS = {"empty_cart": 400, "overweight": 409, "insufficient_stock": 409}


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


def _error(code, message, status):
    return jsonify(error=code, message=message), status


def _unauth():
    return _error("unauthorized", "Sign in required.", 401)


def _view(payment, client_secret=None):
    out = {
        "paymentId": payment.id,
        "status": payment.status,
        "amountCents": payment.amount_cents,
        "failureReason": payment.failure_reason,
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

    # Amount always comes from the server-side cart, never from the client.
    summary, err = validate_cart_for_checkout(current_user)
    if err:
        return _error(err, f"Cart cannot be checked out: {err.replace('_', ' ')}.", CART_ERRORS[err])

    if not current_app.config.get("STRIPE_SECRET_KEY"):
        return _error("payments_unavailable", "Payments are temporarily unavailable.", 503)

    amount_cents = round(summary["total"] * 100)
    payment = Payment(user_id=current_user.id, idempotency_key=key, amount_cents=amount_cents)
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
    if payment is None or payment.status == SUCCEEDED:
        return jsonify(received=True), 200  # unknown intent, or already final: ignore

    kind = event["type"]
    if kind == "payment_intent.succeeded":
        payment.status, payment.failure_reason = SUCCEEDED, None
    elif kind == "payment_intent.payment_failed":
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
