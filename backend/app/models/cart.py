from datetime import datetime, timezone

from ..extensions import db


def _now():
    return datetime.now(timezone.utc)


class Cart(db.Model):
    __tablename__ = "carts"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, unique=True)
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, default=_now, onupdate=_now)

    lines = db.relationship("CartLine", backref="cart", cascade="all, delete-orphan", order_by="CartLine.id")


class CartLine(db.Model):
    # Separate from the future order_lines table: a cart line is mutable, an order line is a snapshot.
    __tablename__ = "cart_lines"
    __table_args__ = (db.UniqueConstraint("cart_id", "product_id"),)

    id = db.Column(db.Integer, primary_key=True)
    cart_id = db.Column(db.Integer, db.ForeignKey("carts.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("products.product_id"), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)

    product = db.relationship("Product")
