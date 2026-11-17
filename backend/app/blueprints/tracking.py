# T16 — Order Tracking and live map. Owner: Nateras Jorge. Data side wired up with T15 (Robot fleet).
# LLD 4: authorize customer owns the order before returning position/status.
from flask import Blueprint, jsonify
from flask_login import current_user

from .auth import require_role
from ..extensions import db
from ..models import Order
from ..models.user import CUSTOMER, EMPLOYEE
from ..timeutil import iso_utc

bp = Blueprint("tracking", __name__, url_prefix="/api/tracking")


@bp.get("/<int:order_id>")
@require_role(CUSTOMER, EMPLOYEE)
def track_order(order_id):
    order = db.session.get(Order, order_id)
    if order is None:
        return jsonify(error="order_not_found"), 404
    if not current_user.is_staff and order.user_id != current_user.id:
        return jsonify(error="forbidden"), 403

    trip, robot = order.trip, None
    if trip is not None:
        robot = trip.robot
    own_stop = next((s for s in (trip.stops if trip else []) if s.order_id == order.id), None)

    return jsonify(
        orderId=order.id,
        status=order.status,
        deliveryAddress=order.delivery_address,
        destination={"lat": order.delivery_lat, "lng": order.delivery_lng},
        tripId=trip.id if trip else None,
        tripStatus=trip.status if trip else None,
        robot={
            "code": robot.robot_code,
            "status": robot.status,
            "lat": float(robot.current_latitude),
            "lng": float(robot.current_longitude),
            "updatedAt": iso_utc(robot.updated_at),
        } if robot else None,
        stop={
            "number": own_stop.stop_number,
            "status": own_stop.status,
            "estimatedArrival": iso_utc(own_stop.estimated_arrival),
            "arrivedAt": iso_utc(own_stop.arrived_at),
        } if own_stop else None,
        stops=[
            {"number": s.stop_number, "status": s.status, "lat": float(s.latitude), "lng": float(s.longitude)}
            for s in (trip.stops if trip else [])
        ] if current_user.is_staff else None,
        routeGeometry=trip.route_geometry if trip else None,
    )
