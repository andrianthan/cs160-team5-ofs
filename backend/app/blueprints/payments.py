# T10 — Payments with Stripe test mode. Owner: Than Andrian.
# LLD 2 §2.3: create_payment_intent() with an idempotency key (no double-charge).
from flask import Blueprint, jsonify

bp = Blueprint("payments", __name__, url_prefix="/api/payments")


@bp.post("")
def create_payment():
    return jsonify(error="not_implemented"), 501
