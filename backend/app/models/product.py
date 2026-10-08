from datetime import datetime, timezone
from ..extensions import db

REQUIRED = {"name", "category", "price", "weightLb"}
OPTIONAL = {"description", "weightLb", "stock", "lowStockThreshold", "imageUrl", "active"}

class Product(db.Model):
    __tablename__ = "products"

    product_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(160), nullable=False)
    category = db.Column(db.String(80), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    weight_lb = db.Column(db.Numeric(8, 2), nullable=False)
    stock_qty = db.Column(db.Integer, nullable=False, default=0)
    low_stock_threshold = db.Column(db.Integer, nullable=False, default=5)
    image_url = db.Column(db.Text)
    active = db.Column(db.Boolean, nullable=False, default=True)
    updated_at = db.Column(
        db.DateTime(timezone=True), nullable=False, server_default=db.func.now(), onupdate=db.func.now()
    )

    def to_dict(self):
        return {
            "id": self.product_id,
            "name": self.name,
            "category": self.category,
            "description": self.description,
            "price": float(self.price),
            "weightLb": float(self.weight_lb),
            "stock": self.stock_qty,
            "imageUrl": self.image_url,
            "active": self.active,
            "updated_at": self.updated_at,
        }