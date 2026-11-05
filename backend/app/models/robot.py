from ..extensions import db


class Robot(db.Model):
    """Persisted fleet state for the T15 simulator.

    No capacity columns: every Robot carries the same load, and that limit is
    Config.TRIP_MAX_ORDERS / TRIP_MAX_WEIGHT_LB (BR-6), enforced when Orders join a Trip.
    """

    __tablename__ = "robots"
    __table_args__ = (
        db.CheckConstraint("status IN ('available','reserved','loading','out_for_delivery','returning','offline')", name="ck_robots_status"),
        db.CheckConstraint("current_latitude BETWEEN -90 AND 90", name="ck_robots_latitude"),
        db.CheckConstraint("current_longitude BETWEEN -180 AND 180", name="ck_robots_longitude"),
    )

    id = db.Column(db.Integer, primary_key=True)
    robot_code = db.Column(db.String(24), nullable=False, unique=True)
    status = db.Column(db.String(24), nullable=False, server_default="available", index=True)
    current_latitude = db.Column(db.Numeric(9, 6))
    current_longitude = db.Column(db.Numeric(9, 6))
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, server_default=db.func.now(), onupdate=db.func.now())
