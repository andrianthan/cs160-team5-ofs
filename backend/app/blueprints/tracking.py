# T16 — Order Tracking and live map. Owner: Nateras Jorge.
# LLD 4: authorize customer owns the order before returning position/status.
from flask import Blueprint, jsonify
from flask_login import current_user

from .auth import require_role
from ..models.user import CUSTOMER, EMPLOYEE

bp = Blueprint("tracking", __name__, url_prefix="/api/tracking")


@bp.get("/<order_id>")
@require_role(CUSTOMER, EMPLOYEE)
def track_order(order_id):
    # The user must be logged in to reach this function.
    # Step 1: Require authentication.
    if not current_user.is_authenticated:
        return jsonify(error="unauthorized"), 401

    # Step 2: Retrieve the order and check ownership.
    # TODO: Connect to the Order database model once implemented.
    # Example:
    #
    # order = db.session.get(Order, order_id)
    #
    # if order is None:
    #     return jsonify(error="order_not_found"), 404
    #
    # if order.customer_id != current_user.id:
    #     return jsonify(error="forbidden"), 403

    # Step 3: Retrieve the assigned trip.
    # TODO: Connect to the Trip model.

    # Step 4: Retrieve the robot's latest GPS coordinates.
    # TODO: Connect to the Robot model or simulator.

    # Step 5: Return tracking data.
    # Until ownership checks and data retrieval are implemented,
    # do not expose any order information.
    return jsonify(
        error="tracking_not_available",
        message="Order tracking is not implemented yet."
    ), 501