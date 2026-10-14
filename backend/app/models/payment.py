from datetime import datetime, timezone

from ..extensions import db

PENDING, SUCCEEDED, FAILED, CANCELED = "pending", "succeeded", "failed", "canceled"


def _now():
    return datetime.now(timezone.utc)


class Payment(db.Model):
    __tablename__ = "payments"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    idempotency_key = db.Column(db.String(64), unique=True, nullable=False)
    stripe_payment_intent_id = db.Column(db.String(120), unique=True)
    amount_cents = db.Column(db.Integer, nullable=False)
    currency = db.Column(db.String(3), nullable=False, default="usd")
    status = db.Column(db.String(20), nullable=False, default=PENDING)
    failure_reason = db.Column(db.Text)
    # Filled by T12 once the Order exists. Plain integer on purpose: orders table is T02/T12's.
    order_id = db.Column(db.Integer)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=_now)
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, default=_now, onupdate=_now)
