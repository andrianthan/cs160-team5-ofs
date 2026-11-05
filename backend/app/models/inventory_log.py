from ..extensions import db


class InventoryLog(db.Model):
    """Audit storage for T05/T12; callers write this in the stock transaction."""

    __tablename__ = "inventory_log"
    __table_args__ = (
        db.CheckConstraint("before_qty >= 0 AND after_qty >= 0", name="ck_inventory_quantities"),
        db.CheckConstraint("after_qty = before_qty + change_qty", name="ck_inventory_balance"),
        db.CheckConstraint("change_qty != 0", name="ck_inventory_change"),
        db.CheckConstraint("reason IN ('SALE','RESTOCK','RETURN','CORRECTION','CANCEL')", name="ck_inventory_reason"),
        db.Index("ix_inventory_product_created", "product_id", "created_at"),
    )

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey("products.product_id", ondelete="RESTRICT"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"))
    order_id = db.Column(db.Integer, db.ForeignKey("orders.id", ondelete="SET NULL"))
    before_qty = db.Column(db.Integer, nullable=False)
    change_qty = db.Column(db.Integer, nullable=False)
    after_qty = db.Column(db.Integer, nullable=False)
    reason = db.Column(db.String(32), nullable=False)
    note = db.Column(db.Text)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, server_default=db.func.now())

    product = db.relationship("Product")
    user = db.relationship("User")
    order = db.relationship("Order")
