from ..extensions import db


class TripStop(db.Model):
    """One Order's delivery attempt on one Trip.

    Unique per (trip, order), not per order: a failed delivery goes back to the queue
    (delivery_failed -> placed) and rides a later Trip, so an Order can have one stop per attempt.
    The failed attempt's row stays as history (T19 delivery metrics).
    """

    __tablename__ = "trip_stops"
    __table_args__ = (
        db.UniqueConstraint("trip_id", "stop_number", name="uq_trip_stops_sequence"),
        db.UniqueConstraint("trip_id", "order_id", name="uq_trip_stops_order"),
        db.CheckConstraint("stop_number BETWEEN 1 AND 10", name="ck_trip_stops_number"),
        db.CheckConstraint("latitude BETWEEN -90 AND 90", name="ck_trip_stops_latitude"),
        db.CheckConstraint("longitude BETWEEN -180 AND 180", name="ck_trip_stops_longitude"),
        db.CheckConstraint("status IN ('pending','arrived','delivered','delivery_failed')", name="ck_trip_stops_status"),
    )

    id = db.Column(db.Integer, primary_key=True)
    trip_id = db.Column(db.Integer, db.ForeignKey("trips.id", ondelete="CASCADE"), nullable=False)
    order_id = db.Column(db.Integer, db.ForeignKey("orders.id", ondelete="RESTRICT"), nullable=False, index=True)
    stop_number = db.Column(db.SmallInteger, nullable=False)
    latitude = db.Column(db.Numeric(9, 6), nullable=False)
    longitude = db.Column(db.Numeric(9, 6), nullable=False)
    estimated_arrival = db.Column(db.DateTime(timezone=True))
    arrived_at = db.Column(db.DateTime(timezone=True))
    completed_at = db.Column(db.DateTime(timezone=True))
    status = db.Column(db.String(20), nullable=False, server_default="pending")
    failure_reason = db.Column(db.Text)

    order = db.relationship("Order")
