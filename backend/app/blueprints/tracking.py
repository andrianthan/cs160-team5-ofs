# T16 — Order Tracking and live map. Owner: Nateras Jorge.
# LLD 4: authorize customer owns the order before returning position/status.

from flask import Blueprint, jsonify
from flask_login import current_user

from .auth import require_role
from ..extensions import db
from ..models.user import CUSTOMER, EMPLOYEE
from ..models.order import Order
from ..timeutil import iso_utc

bp = Blueprint("tracking", __name__, url_prefix="/api/tracking")


@bp.get("/<int:order_id>")
@require_role(CUSTOMER, EMPLOYEE)
def track_order(order_id):
    # Step 1: Retrieve the order.
    order = db.session.get(Order, order_id)

    if order is None:
        return jsonify(error="order_not_found"), 404

    # Step 2: Verify ownership.
    if current_user.role == CUSTOMER:
        if order.user_id != current_user.id:
            return jsonify(error="forbidden"), 403

    # Step 3: Retrieve assigned trip.
    trip = order.trip

    trip_data = None
    robot_data = None

    if trip is not None:
        trip_data = {
            "id": trip.id,
            "status": trip.status,
            "dispatchedAt": iso_utc(trip.dispatched_at),
            "estimatedDurationMinutes":
                trip.estimated_duration_minutes,
        }

        # Step 4: Retrieve robot's latest GPS coordinates.
        robot = trip.robot

        if robot is not None:
            robot_data = {
                "id": robot.id,
                "robotCode": robot.robot_code,
                "status": robot.status,
                "latitude": (
                    float(robot.current_latitude)
                    if robot.current_latitude is not None
                    else None
                ),
                "longitude": (
                    float(robot.current_longitude)
                    if robot.current_longitude is not None
                    else None
                ),
                "updatedAt": iso_utc(robot.updated_at),
            }

    # Step 5: Return tracking information.
    return jsonify({
        "orderId": order.id,
        "status": order.status,
        "tripId": order.trip_id,
        "trip": trip_data,
        "robot": robot_data,
        "deliveryAddress": order.delivery_address,
        "deliveryLocation": {
            "latitude": order.delivery_lat,
            "longitude": order.delivery_lng,
        },
        "createdAt": iso_utc(order.created_at),
        "updatedAt": iso_utc(order.updated_at),
    }), 200
