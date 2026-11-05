from datetime import datetime, timezone
from sqlalchemy.dialects.postgresql import JSONB

from ..extensions import db

# open: still taking Orders (Preparation Queue adds to it). dispatched: out on a Robot. completed: back at the store.
OPEN, DISPATCHED, COMPLETED = "open", "dispatched", "completed"
TRIP_STATUSES = (OPEN, DISPATCHED, COMPLETED)


def _now():
    return datetime.now(timezone.utc)


class Trip(db.Model):
    # One Robot run through 1-10 Order addresses and back (CONTEXT.md "Trip"). Robot assignment and
    # route order come with Dispatch (T14/T15).
    __tablename__ = "trips"
    __table_args__ = (
        db.CheckConstraint("status IN ('open','dispatched','completed')", name="ck_trips_status"),
        db.CheckConstraint("estimated_duration_minutes >= 0", name="ck_trips_duration"),
        db.Index("ix_trips_status_created", "status", "created_at"),
    )

    id = db.Column(db.Integer, primary_key=True)
    status = db.Column(db.String(20), nullable=False, default=OPEN, index=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=_now)
    dispatched_at = db.Column(db.DateTime(timezone=True))
    completed_at = db.Column(db.DateTime(timezone=True))
    robot_id = db.Column(db.Integer, db.ForeignKey("robots.id", name="fk_trips_robot_id", ondelete="SET NULL"), index=True)
    route_geometry = db.Column(db.JSON().with_variant(JSONB(), "postgresql"))
    estimated_duration_minutes = db.Column(db.Integer)

    orders = db.relationship("Order", backref="trip", order_by="Order.created_at")
    robot = db.relationship("Robot")
    stops = db.relationship("TripStop", backref="trip", cascade="all, delete-orphan", passive_deletes=True, order_by="TripStop.stop_number")

    @property
    def weight_lb(self):
        return sum((o.weight_lb for o in self.orders), 0)

    def to_dict(self):
        return {
            "id": self.id,
            "status": self.status,
            "orderIds": [o.id for o in self.orders],
            "orderCount": len(self.orders),
            "weightLb": float(self.weight_lb),
            "createdAt": self.created_at.isoformat(),
            "dispatchedAt": self.dispatched_at.isoformat() if self.dispatched_at else None,
        }
