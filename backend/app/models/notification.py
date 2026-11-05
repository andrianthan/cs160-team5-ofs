from datetime import datetime, timezone

from ..extensions import db

PENDING, SENT, FAILED, SKIPPED = "pending", "sent", "failed", "skipped"


class Notification(db.Model):
    """One email to one recipient about one Order event. The unique key is the deduplication (BR-8)."""

    __tablename__ = "notifications"
    __table_args__ = (db.UniqueConstraint("order_id", "event", "recipient_email", name="uq_notification_once"),)

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("orders.id"), nullable=False, index=True)
    event = db.Column(db.String(40), nullable=False)
    recipient_email = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(10), nullable=False, default=PENDING)
    attempts = db.Column(db.Integer, nullable=False, default=0)
    last_error = db.Column(db.String(500))
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    sent_at = db.Column(db.DateTime(timezone=True))
