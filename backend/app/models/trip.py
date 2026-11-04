from datetime import datetime, timezone

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

    id = db.Column(db.Integer, primary_key=True)
    status = db.Column(db.String(20), nullable=False, default=OPEN, index=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=_now)
    dispatched_at = db.Column(db.DateTime(timezone=True))
    completed_at = db.Column(db.DateTime(timezone=True))

    orders = db.relationship("Order", backref="trip", order_by="Order.created_at")

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
