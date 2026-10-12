# T05 — Catalog and Inventory backend. Owner: Karnani Shresthkumar.
from flask import Blueprint, jsonify, request
from ..extensions import db
from ..models.product import Product, REQUIRED, OPTIONAL
from .auth import staff_required, manager_required

bp = Blueprint("products", __name__, url_prefix="/api/products")

def _body():
    data = request.get_json(silent=True)
    return data if isinstance(data, dict) else {}

def _number(v):  # a JSON number, not true/false
    return isinstance(v, (int, float)) and not isinstance(v, bool)

def _whole(v):
    return isinstance(v, int) and not isinstance(v, bool) and 0 <= v <= 2_147_483_647

RULES = {
    "name": lambda v: isinstance(v, str) and 0 < len(v.strip()) <= 160,
    "category": lambda v: isinstance(v, str) and 0 < len(v.strip()) <= 80,
    "description": lambda v: v is None or isinstance(v, str),
    "image_url": lambda v: v is None or isinstance(v, str),
    "price": lambda v: _number(v) and 0 <= v < 10**8 and v == round(v, 2),
    "weight_lb": lambda v: _number(v) and 0 < v < 10**6 and v == round(v, 2),
    "stock_qty": _whole,
    "low_stock_threshold": _whole,
    "active": lambda v: isinstance(v, bool),
}


def _clean(data, creating):
    """Returns (values, None) or (None, error message)."""
    if creating and (missing := REQUIRED - data.keys()):
        return None, f"Required: {', '.join(sorted(missing))}"
    values = {k: data[k] for k in RULES if k in data}  # unknown keys are ignored
    if not values:
        return None, "Nothing to update"
    if bad := [k for k, v in values.items() if not RULES[k](v)]:
        return None, f"Invalid: {', '.join(bad)}"
    for k in ("name", "category"):
        if k in values:
            values[k] = values[k].strip()
    return values, None


@bp.get("")
def list_products():
    products = Product.query.filter_by(active=True).order_by(Product.name).all()

    return jsonify([p.to_dict() for p in products])


@bp.patch("/<int:product_id>")
@manager_required
def update_product(product_id):
    product = db.session.get(Product, product_id)

    if product is None:
        return jsonify(error="Product not found"), 404

    values, error = _clean(_body(), creating=False)
    if error:
        return jsonify(error=error), 400

    for column, value in values.items():
        setattr(product, column, value)
    db.session.commit()
    return jsonify(product.to_dict())


@bp.post("")
@manager_required
def create_product():
    values, error = _clean(_body(), creating=True)
    if error:
        return jsonify(error=error), 400

    product = Product(**values)
    db.session.add(product)
    db.session.commit()
    return jsonify(product.to_dict()), 201
