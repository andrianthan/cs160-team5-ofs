# T05 — Catalog and Inventory backend. Owner: Karnani Shresthkumar.
from flask import Blueprint, jsonify

bp = Blueprint("products", __name__, url_prefix="/api/products")


@bp.get("")
def list_products():
    return jsonify(error="not_implemented"), 501


@bp.patch("/<product_id>")
def update_product(product_id):
    return jsonify(error="not_implemented"), 501


@bp.post("")
def create_product():
    return jsonify(error="not_implemented"), 501
