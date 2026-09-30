# T08 — Cart and Pricing backend. Owner: Than Andrian.
# LLD 1/2: calc_order_weight(), calc_delivery_fee() — BR-1 ($10 fee at >=20lb),
# BR-3 (block checkout over 200lb).
from flask import Blueprint, jsonify

bp = Blueprint("cart", __name__, url_prefix="/api/cart")


@bp.get("")
def get_cart():
    return jsonify(error="not_implemented"), 501


@bp.put("/items/<product_id>")
def update_cart_item(product_id):
    return jsonify(error="not_implemented"), 501
