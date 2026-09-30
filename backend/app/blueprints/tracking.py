# T16 — Order Tracking and live map. Owner: Nateras Jorge.
# LLD 4: authorize customer owns the order before returning position/status.
from flask import Blueprint, jsonify

bp = Blueprint("tracking", __name__, url_prefix="/api/tracking")


@bp.get("/<order_id>")
def track_order(order_id):
    return jsonify(error="not_implemented"), 501
