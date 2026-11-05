from datetime import datetime, timezone

from ..extensions import db

PENDING, SUCCEEDED, FAILED, CANCELED = "pending", "succeeded", "failed", "canceled"
# Paid, but the Order could not be placed (stock ran out or the cart changed mid-payment).
REFUNDED = "refunded"


def _now():
    return datetime.now(timezone.utc)


class Payment(db.Model):
    __tablename__ = "payments"
    __table_args__ = (
        db.UniqueConstraint("order_id", name="uq_payments_order_id"),
        db.CheckConstraint("amount_cents >= 0", name="ck_payments_amount"),
        db.CheckConstraint("status IN ('pending','succeeded','failed','canceled','refunded')", name="ck_payments_status"),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    idempotency_key = db.Column(db.String(64), unique=True, nullable=False)
    stripe_payment_intent_id = db.Column(db.String(120), unique=True)
    amount_cents = db.Column(db.Integer, nullable=False)
    currency = db.Column(db.String(3), nullable=False, default="usd")
    status = db.Column(db.String(20), nullable=False, default=PENDING)
    failure_reason = db.Column(db.Text)
    # Validated delivery address, carried from checkout to the Order the webhook creates.
    delivery_address = db.Column(db.Text)
    delivery_lat = db.Column(db.Float)
    delivery_lng = db.Column(db.Float)
    # Pending/failed payments have no Order; successful checkout links exactly one.
    order_id = db.Column(db.Integer, db.ForeignKey("orders.id", name="fk_payments_order_id", ondelete="RESTRICT"))
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=_now)
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, default=_now, onupdate=_now)

    user = db.relationship("User")
