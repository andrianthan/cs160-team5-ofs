# T12 — Orders creation and status lifecycle. Owner: Karnani Shresthkumar.
# LLD 2 §2.4: Order Status state machine (Placed -> Planned -> Out for Delivery
# -> Delivered, plus Delivery Failed / Manual Review / Cancelled). BR-4.
# Orders are never created by the client: the Stripe webhook calls place_order()
# once the payment succeeds (CONTEXT.md: "An Order exists only after payment succeeds").
from decimal import Decimal

from flask import Blueprint, jsonify, request
from flask_login import current_user

from .auth import require_role, staff_required
from .cart import validate_cart_for_checkout
from .. import notifications
from ..config import Config
from ..extensions import db
from ..models import Cart, Order, OrderLine, Product
from ..models.order import (
    DELIVERED, DELIVERY_FAILED, MANUAL_REVIEW, OUT_FOR_DELIVERY, PLACED, PLANNED, STATUSES,
)
from ..models.trip import NOT_DISPATCHED
from ..planning import assign_to_trip, leave_trip
from ..models.user import MANAGER

bp = Blueprint("orders", __name__, url_prefix="/api/orders")

# Staff status changes. Cancelling (and refunding) is a Manager Order Override, not a status edit.
# Placed -> Planned only happens through POST /<id>/prepare (it puts the Order on a Trip), and
# Planned -> Out for Delivery through Dispatch, so no Order is ever Planned without a Trip.
TRANSITIONS = {
    PLACED: {MANUAL_REVIEW},
    PLANNED: {PLACED, MANUAL_REVIEW},  # taken back off its Trip, while that hasn't been dispatched
    OUT_FOR_DELIVERY: {DELIVERED, DELIVERY_FAILED},
    DELIVERY_FAILED: {PLACED, MANUAL_REVIEW},
    MANUAL_REVIEW: {PLACED},
}


def _error(code, message, status):
    return jsonify(error=code, message=message), status


def place_order(payment):
    """Turn the payer's cart into an Order. Returns (order, None) or (None, reason).

    Locks the products, re-runs checkout validation, and checks the cart still totals what was
    paid. On success: snapshots the lines, decrements stock, removes the bought lines from the
    cart and links the payment. The caller commits (or rolls back) the whole thing at once.
    """
    if not payment.delivery_address:
        return None, "missing_address"
    cart = Cart.query.filter_by(user_id=payment.user_id).first()
    ids = [line.product_id for line in cart.lines] if cart else []
    if ids:
        # Row locks so two concurrent webhooks can't both sell the last unit (no-op on SQLite).
        Product.query.filter(Product.product_id.in_(ids)).populate_existing().with_for_update().all()

    summary, err = validate_cart_for_checkout(payment.user)
    if err:
        return None, err
    if round(summary["total"] * 100) != payment.amount_cents:
        return None, "cart_changed"

    order = Order(
        user_id=payment.user_id,
        subtotal=Decimal(str(summary["subtotal"])),
        delivery_fee=Decimal(str(summary["deliveryFee"])),
        total=Decimal(str(summary["total"])),
        weight_lb=Decimal(str(summary["orderWeightLb"])),
        delivery_address=payment.delivery_address,
        delivery_lat=payment.delivery_lat,
        delivery_lng=payment.delivery_lng,
    )
    for line in [line for line in cart.lines if line.product.active]:
        p = line.product
        order.lines.append(OrderLine(
            product_id=p.product_id, name=p.name, unit_price=p.price, weight_lb=p.weight_lb,
            quantity=line.quantity,
        ))
        p.stock_qty -= line.quantity
        cart.lines.remove(line)
    db.session.add(order)
    db.session.flush()
    payment.order_id = order.id
    return order, None


def _visible(order_id):
    """The order if the signed-in user may see it: its customer, or any staff member."""
    order = db.session.get(Order, order_id)
    if order and (current_user.is_staff or order.user_id == current_user.id):
        return order
    return None


@bp.get("")
def list_orders():
    if not current_user.is_authenticated:
        return _error("unauthorized", "Sign in required.", 401)
    query = Order.query.order_by(Order.created_at.desc(), Order.id.desc())
    if not current_user.is_staff:
        query = query.filter_by(user_id=current_user.id)
    status = request.args.get("status")
    if status:
        if status not in STATUSES:
            return _error("invalid_status", "Unknown order status.", 400)
        query = query.filter_by(status=status)
    return jsonify(orders=[o.to_dict() for o in query.all()])


@bp.get("/<int:order_id>")
def get_order(order_id):
    if not current_user.is_authenticated:
        return _error("unauthorized", "Sign in required.", 401)
    order = _visible(order_id)
    if order is None:
        return _error("not_found", "Order not found.", 404)
    return jsonify(order.to_dict())


@bp.patch("/<int:order_id>/status")
@staff_required
def update_order_status(order_id):
    order = db.session.get(Order, order_id)
    if order is None:
        return _error("not_found", "Order not found.", 404)
    body = request.get_json(silent=True)
    new = body.get("status") if isinstance(body, dict) else None
    if new not in STATUSES:
        return _error("invalid_status", "Unknown order status.", 400)
    if new not in TRANSITIONS.get(order.status, set()):
        return _error("invalid_transition", f"Can't move an order from {order.status} to {new}.", 409)
    if order.status == PLANNED and order.trip is not None and order.trip.status not in NOT_DISPATCHED:
        return _error("trip_dispatched", "That order's trip has already been dispatched.", 409)
    if new in (PLACED, MANUAL_REVIEW):
        leave_trip(order)  # back to the queue (or held): it's no longer on a Trip
    order.status = new
    db.session.commit()
    notifications.notify_status_change(order)
    return jsonify(order.to_dict())


@bp.post("/<int:order_id>/prepare")
@staff_required
def prepare_order(order_id):
    """Preparation Queue "Mark Prepared": the Employee has gathered the items; the Order joins a Trip."""
    order = db.session.get(Order, order_id)
    if order is None:
        return _error("not_found", "Order not found.", 404)
    if order.status != PLACED:
        return _error("invalid_transition", f"Only placed orders can be prepared (this one is {order.status}).", 409)

    trip = assign_to_trip(order)
    db.session.commit()
    if trip is None:
        notifications.notify_status_change(order)  # Manual Review: tell Staff
        return _error(
            "too_heavy_for_robot",
            f"Order is over {Config.TRIP_MAX_WEIGHT_LB} lb, so it can't fit a Robot. Moved to Manual Review.",
            409,
        )
    return jsonify(order=order.to_dict(), trip=trip.to_dict())


@bp.post("/<order_id>/override")
@require_role(MANAGER)
def override_order(order_id):
    # T20 — Order Override. Owner: Nateras Jorge.

    # Step 1: Read JSON request.
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify(error="INVALID_OVERRIDE"), 400

    # Step 2: Validate action and reason.
    action = data.get("action")
    reason = data.get("reason")

    if not isinstance(action, str) or not action.strip():
        return jsonify(error="INVALID_OVERRIDE"), 400

    if not isinstance(reason, str) or not reason.strip():
        return jsonify(error="INVALID_OVERRIDE"), 400

    # Step 3: Validate confirmation.
    if data.get("confirmed") is not True:
        return jsonify(error="INVALID_OVERRIDE"), 400

    # Step 4: Find the order.
    # TODO: Connect to the Order model.

    # Step 5: Apply the approved override.
    # TODO: Validate action and current order status.

    # Step 6: Record the manager and reason.
    # TODO: Save the audit record.

    return jsonify(error="not_implemented"), 501
