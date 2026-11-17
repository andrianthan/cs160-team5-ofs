
from datetime import datetime, timezone

from ..extensions import db


def _now():
    return datetime.now(timezone.utc)


class DeliverySettings(db.Model):
    __tablename__ = "delivery_settings"

    id = db.Column(db.Integer, primary_key=True)
    paused = db.Column(db.Boolean, nullable=False, default=False)
    updated_by = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=True
    )
    updated_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=_now,
        onupdate=_now
    )


def deliveries_paused():
    settings = db.session.get(DeliverySettings, 1)
    return settings.paused if settings is not None else False
