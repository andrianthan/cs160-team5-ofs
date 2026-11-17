
from datetime import datetime, timezone

from ..extensions import db


def _now():
    return datetime.now(timezone.utc)


class OrderOverrideAudit(db.Model):
    __tablename__ = "order_override_audits"

    id = db.Column(db.Integer, primary_key=True)

    order_id = db.Column(
        db.Integer,
        db.ForeignKey("orders.id"),
        nullable=False,
        index=True
    )

    manager_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    action = db.Column(db.String(50), nullable=False)
    previous_status = db.Column(db.String(20), nullable=False)
    new_status = db.Column(db.String(20), nullable=False)
    reason = db.Column(db.Text, nullable=False)

    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=_now
    )
