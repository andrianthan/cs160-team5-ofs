# T12 — Orders creation and status lifecycle. Owner: Karnani Shresthkumar.
# LLD 2 §2.4: Order Status state machine (Placed -> Planned -> Out for Delivery
# -> Delivered, plus Delivery Failed / Manual Review / Cancelled). BR-4.
from flask import Blueprint, jsonify, request
from .auth import require_role
from ..models.user import MANAGER

bp = Blueprint("orders", __name__, url_prefix="/api/orders")


@bp.post("")
def create_order():
    return jsonify(error="not_implemented"), 501


@bp.get("")
def list_orders():
    return jsonify(error="not_implemented"), 501


@bp.patch("/<order_id>/status")
def update_order_status(order_id):
    return jsonify(error="not_implemented"), 501


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
