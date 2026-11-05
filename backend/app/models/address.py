from ..extensions import db


class Address(db.Model):
    """Saved customer address; checkout still revalidates it with Mapbox."""

    __tablename__ = "addresses"
    __table_args__ = (
        db.CheckConstraint("latitude BETWEEN -90 AND 90", name="ck_addresses_latitude"),
        db.CheckConstraint("longitude BETWEEN -180 AND 180", name="ck_addresses_longitude"),
        db.Index("ix_addresses_user_default", "user_id", "is_default"),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    line1 = db.Column(db.String(150), nullable=False)
    line2 = db.Column(db.String(150))
    city = db.Column(db.String(80), nullable=False)
    state = db.Column(db.String(2), nullable=False, server_default="CA")
    postal_code = db.Column(db.String(12), nullable=False)
    formatted_address = db.Column(db.Text, nullable=False)
    latitude = db.Column(db.Numeric(9, 6), nullable=False)
    longitude = db.Column(db.Numeric(9, 6), nullable=False)
    in_delivery_zone = db.Column(db.Boolean, nullable=False, server_default=db.false())
    is_default = db.Column(db.Boolean, nullable=False, server_default=db.false())
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, server_default=db.func.now())
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, server_default=db.func.now(), onupdate=db.func.now())

    user = db.relationship("User")
