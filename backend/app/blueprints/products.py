# T05 — Catalog and Inventory backend. Owner: Karnani Shresthkumar.
from sqlalchemy.exc import IntegrityError
from flask import Blueprint, jsonify, request
from flask_login import current_user
from .. import inventory
from ..extensions import db
from ..models.product import Product, REQUIRED, OPTIONAL
from ..models.cart import CartLine
from ..models.inventory_log import InventoryLog
from ..models.order import OrderLine
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

@bp.get("/all")
@staff_required
def get_all():
    products = Product.query.order_by(Product.name).all()

    return jsonify([p.to_dict() for p in products])

def _stock_reason(data):
    """Optional `stock_reason` and `stock_note` for a hand edit of Stock. Returns (reason, note, error)."""
    reason, note = data.get("stock_reason"), data.get("stock_note")
    if reason is not None and reason not in inventory.MANUAL_REASONS:
        return None, None, f"Invalid: stock_reason (use {', '.join(inventory.MANUAL_REASONS)})"
    if note is not None and not (isinstance(note, str) and len(note) <= inventory.NOTE_MAX):
        return None, None, f"Invalid: stock_note (text, at most {inventory.NOTE_MAX} characters)"
    return reason, (note.strip() or None) if note else None, None


@bp.patch("/<int:product_id>")
@manager_required
def update_product(product_id):
    # Row lock, so a sale settling at the same moment can't slip between reading Stock and logging it.
    product = db.session.get(Product, product_id, with_for_update=True, populate_existing=True)

    if product is None:
        return jsonify(error="Product not found"), 404

    data = _body()
    values, error = _clean(data, creating=False)
    if error:
        return jsonify(error=error), 400
    reason, note, error = _stock_reason(data)
    if error:
        return jsonify(error=error), 400

    # Stock never changes without an inventory_log row (T05: log every restock, return or correction).
    new_stock = values.pop("stock_qty", None)
    change = 0 if new_stock is None else new_stock - product.stock_qty
    if change < 0 and reason in (inventory.RESTOCK, inventory.RETURN):  # a CORRECTION may go either way
        return jsonify(error=f"Invalid: a {reason} can only add stock"), 400

    for column, value in values.items():
        setattr(product, column, value)
    if change:
        default = inventory.RESTOCK if change > 0 else inventory.CORRECTION
        inventory.change_stock(product, change, reason or default, user_id=current_user.id, note=note)
    db.session.commit()
    return jsonify(product.to_dict())


@bp.get("/<int:product_id>/inventory-log")
@manager_required
def inventory_history(product_id):
    """The product's Stock history, newest first: every sale, restock, return, correction and cancel."""
    product = db.session.get(Product, product_id)
    if product is None:
        return jsonify(error="Product not found"), 404
    entries = (
        InventoryLog.query.filter_by(product_id=product_id)
        .order_by(InventoryLog.created_at.desc(), InventoryLog.id.desc())
        .all()
    )
    return jsonify(productId=product.product_id, name=product.name, stock=product.stock_qty,
                   entries=[e.to_dict() for e in entries])


@bp.delete("/<int:product_id>")
@manager_required
def delete_product(product_id):
    product = db.session.get(Product, product_id)

    if product is None:
        return jsonify(error="Product not found"), 404

    if CartLine.query.filter_by(product_id=product_id).first():
        return jsonify(error="Product is in a cart. Deactivate it instead."), 409
    # Past orders and Stock history keep pointing at the product (the database restricts these
    # deletes on PostgreSQL; checking here gives the same clear answer on SQLite too).
    if OrderLine.query.filter_by(product_id=product_id).first():
        return jsonify(error="Product has been ordered. Deactivate it instead."), 409
    if InventoryLog.query.filter_by(product_id=product_id).first():
        return jsonify(error="Product has stock history. Deactivate it instead."), 409

    data = product.to_dict()

    try:
        db.session.delete(product)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify(error="Product is still referenced elsewhere. Deactivate it instead."), 409

    return jsonify(data)


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
