# T05 — Catalog and Inventory backend. Owner: Karnani Shresthkumar.
from flask import Blueprint, jsonify, request
from ..extensions import db
from ..models.product import Product, REQUIRED, OPTIONAL
from .auth import staff_required, manager_required

bp = Blueprint("products", __name__, url_prefix="/api/products")

def _body():
    data = request.get_json(silent=True)
    return data if isinstance(data, dict) else {}


def _text(data, key):
    value = data.get(key)
    return value.strip() if isinstance(value, str) else ""


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

    data = request.get_json(silent=True)

    if not isinstance(data, dict) or not data:
        return jsonify(error="Invalid input"), 400



    return jsonify(error="not_implemented"), 2501


@bp.post("")
@manager_required
def create_product():
    return jsonify(error="not_implemented"), 501
