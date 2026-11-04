from datetime import datetime, timezone

from ..extensions import db
from ..timeutil import iso_utc

# open: still taking Orders (Preparation Queue adds to it).
# ready: locked because it's full or its oldest Order hit the dispatch deadline (BR-7); waits for an
#        Employee to confirm the Robot is loaded and Dispatch it.
# dispatched: out on a Robot. completed: back at the store.
OPEN, READY, DISPATCHED, COMPLETED = "open", "ready", "dispatched", "completed"
TRIP_STATUSES = (OPEN, READY, DISPATCHED, COMPLETED)
NOT_DISPATCHED = (OPEN, READY)  # Orders can still be taken off these


def _now():
    return datetime.now(timezone.utc)


class Trip(db.Model):
    # One Robot run through 1-10 Order addresses and back (CONTEXT.md "Trip"). Robot assignment and
    # route order come with Dispatch (T14/T15).
    __tablename__ = "trips"

    id = db.Column(db.Integer, primary_key=True)
    status = db.Column(db.String(20), nullable=False, default=OPEN, index=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=_now)
    ready_at = db.Column(db.DateTime(timezone=True))
    ready_reason = db.Column(db.String(20))  # "full" or "deadline"
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
            "createdAt": iso_utc(self.created_at),
            "readyReason": self.ready_reason,
            "dispatchedAt": iso_utc(self.dispatched_at),
        }
