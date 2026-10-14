# T08 — Cart and Pricing backend. Owner: Than Andrian.
# LLD 1/2: calc_order_weight(), calc_delivery_fee() — BR-1 ($10 fee at >=20lb),
# BR-3 (block checkout over 200lb).
from decimal import ROUND_HALF_UP, Decimal

from flask import Blueprint, jsonify, request
from flask_login import current_user

from ..config import Config
from ..extensions import db
from ..models import Cart, CartLine, Product

bp = Blueprint("cart", __name__, url_prefix="/api/cart")

MAX_QUANTITY = 999
CENT = Decimal("0.01")


def _money(value):
    return Decimal(value).quantize(CENT, rounding=ROUND_HALF_UP)


def calc_order_weight(lines):
    """Total pounds across (product, quantity) pairs."""
    return sum((Decimal(p.weight_lb) * q for p, q in lines), Decimal("0"))


def calc_delivery_fee(order_weight_lb, threshold=Config.DELIVERY_FEE_THRESHOLD_LB, fee=Config.DELIVERY_FEE_AMOUNT):
    """BR-1: $0 under the threshold, flat fee at exactly the threshold or above."""
    return Decimal(fee) if Decimal(order_weight_lb) >= Decimal(threshold) else Decimal("0")


def check_overweight(order_weight_lb, limit=Config.TRIP_MAX_WEIGHT_LB):
    """BR-3: strictly over the Robot limit. Exactly the limit still fits."""
    return Decimal(order_weight_lb) > Decimal(limit)


def _error(code, message, status):
    return jsonify(error=code, message=message), status


def _require_login():
    if not current_user.is_authenticated:
        return _error("unauthorized", "Sign in required.", 401)
    return None


def _get_cart(user, create=True):
    cart = Cart.query.filter_by(user_id=user.id).first()
    if cart is None and create:
        cart = Cart(user_id=user.id)
        db.session.add(cart)
        db.session.commit()
    return cart


def _summarize(cart):
    lines, priced = [], []
    for line in cart.lines if cart else []:
        p = line.product
        available = p.active
        item = {
            "productId": p.product_id,
            "name": p.name,
            "price": float(p.price),
            "weightLb": float(p.weight_lb),
            "quantity": line.quantity,
            "unavailable": not available,
        }
        if available:
            item["lineTotal"] = float(_money(Decimal(p.price) * line.quantity))
            item["lineWeightLb"] = float(Decimal(p.weight_lb) * line.quantity)
            priced.append((p, line.quantity))
        lines.append(item)

    weight = calc_order_weight(priced)
    subtotal = _money(sum((Decimal(p.price) * q for p, q in priced), Decimal("0")))
    fee = _money(calc_delivery_fee(weight))
    return {
        "lines": lines,
        "orderWeightLb": float(weight),
        "subtotal": float(subtotal),
        "deliveryFee": float(fee),
        "total": float(subtotal + fee),
        "overweight": check_overweight(weight),
    }


def validate_cart_for_checkout(user):
    """Returns (summary, error). error is None, "empty_cart", "overweight" or "insufficient_stock".
    Re-checks stock and drops unavailable lines from consideration. T10 and T12 reuse this."""
    cart = _get_cart(user, create=False)
    summary = _summarize(cart)
    active = [l for l in (cart.lines if cart else []) if l.product.active]
    if not active:
        return summary, "empty_cart"
    if any(l.quantity > l.product.stock_qty for l in active):
        return summary, "insufficient_stock"
    if summary["overweight"]:
        return summary, "overweight"
    return summary, None


@bp.get("")
def get_cart():
    denied = _require_login()
    if denied:
        return denied
    return jsonify(_summarize(_get_cart(current_user)))


@bp.delete("")
def clear_cart():
    denied = _require_login()
    if denied:
        return denied
    cart = _get_cart(current_user)
    cart.lines.clear()
    db.session.commit()
    return jsonify(_summarize(cart))


@bp.put("/items/<product_id>")
def update_cart_item(product_id):
    denied = _require_login()
    if denied:
        return denied

    body = request.get_json(silent=True)
    quantity = body.get("quantity") if isinstance(body, dict) else None
    if not isinstance(quantity, int) or isinstance(quantity, bool) or not 0 <= quantity <= MAX_QUANTITY:
        return _error("invalid_quantity", f"Quantity must be a whole number from 0 to {MAX_QUANTITY}.", 400)

    product = db.session.get(Product, int(product_id)) if product_id.isdigit() else None
    if product is None or not product.active:
        return _error("product_not_found", "That product is not available.", 404)

    cart = _get_cart(current_user)
    line = CartLine.query.filter_by(cart_id=cart.id, product_id=product.product_id).first()

    if quantity == 0:
        if line:
            db.session.delete(line)
    else:
        if quantity > product.stock_qty:  # BR-4
            return _error("insufficient_stock", f"Only {product.stock_qty} in stock.", 409)
        if line:
            line.quantity = quantity
        else:
            db.session.add(CartLine(cart_id=cart.id, product_id=product.product_id, quantity=quantity))
    db.session.commit()
    db.session.refresh(cart)
    return jsonify(_summarize(cart))
