from datetime import datetime, timezone

from ..extensions import db
from ..timeutil import iso_utc

# LLD 2 §2.4 Order Status. Cancelled is only reachable through a Manager Order Override (T20).
PLACED, PLANNED, OUT_FOR_DELIVERY, DELIVERED = "placed", "planned", "out_for_delivery", "delivered"
DELIVERY_FAILED, MANUAL_REVIEW, CANCELLED = "delivery_failed", "manual_review", "cancelled"
STATUSES = (PLACED, PLANNED, OUT_FOR_DELIVERY, DELIVERED, DELIVERY_FAILED, MANUAL_REVIEW, CANCELLED)


def _now():
    return datetime.now(timezone.utc)


class Order(db.Model):
    __tablename__ = "orders"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    status = db.Column(db.String(20), nullable=False, default=PLACED, index=True)
    subtotal = db.Column(db.Numeric(10, 2), nullable=False)
    delivery_fee = db.Column(db.Numeric(10, 2), nullable=False)
    total = db.Column(db.Numeric(10, 2), nullable=False)
    weight_lb = db.Column(db.Numeric(8, 2), nullable=False)
    delivery_address = db.Column(db.Text, nullable=False)
    delivery_lat = db.Column(db.Float, nullable=False)
    delivery_lng = db.Column(db.Float, nullable=False)
    # set when an Employee marks the Order prepared (Preparation Queue); cleared if it's taken back off
    trip_id = db.Column(db.Integer, db.ForeignKey("trips.id"), index=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=_now)
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, default=_now, onupdate=_now)

    lines = db.relationship("OrderLine", backref="order", cascade="all, delete-orphan", order_by="OrderLine.id")
    user = db.relationship("User")

    def to_dict(self):
        return {
            "id": self.id,
            "userId": self.user_id,
            "customerName": self.user.name,
            "tripId": self.trip_id,
            "status": self.status,
            "lines": [line.to_dict() for line in self.lines],
            "subtotal": float(self.subtotal),
            "deliveryFee": float(self.delivery_fee),
            "total": float(self.total),
            "orderWeightLb": float(self.weight_lb),
            "deliveryAddress": self.delivery_address,
            "deliveryLat": self.delivery_lat,
            "deliveryLng": self.delivery_lng,
            "createdAt": iso_utc(self.created_at),
        }


class OrderLine(db.Model):
    # Snapshot of the cart line at payment time: later price or name edits don't rewrite past orders.
    __tablename__ = "order_lines"

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("orders.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("products.product_id"), nullable=False)
    name = db.Column(db.String(160), nullable=False)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)
    weight_lb = db.Column(db.Numeric(8, 2), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)

    def to_dict(self):
        return {
            "productId": self.product_id,
            "name": self.name,
            "price": float(self.unit_price),
            "weightLb": float(self.weight_lb),
            "quantity": self.quantity,
        }
