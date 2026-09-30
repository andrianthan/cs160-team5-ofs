# T12 — Orders creation and status lifecycle. Owner: Karnani Shresthkumar.
# LLD 2 §2.4: Order Status state machine (Placed -> Planned -> Out for Delivery
# -> Delivered, plus Delivery Failed / Manual Review / Cancelled). BR-4.
from flask import Blueprint, jsonify

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
def override_order(order_id):
    # T20 — Order Override. Owner: Nateras Jorge.
    return jsonify(error="not_implemented"), 501
