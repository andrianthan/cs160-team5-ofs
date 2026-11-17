# T15 — Robot fleet status for the staff dashboard.
from flask import Blueprint, jsonify

from .auth import staff_required
from ..extensions import db
from ..models import Robot
from ..robot import Robot as Fleet, rebalance_reserve
from ..timeutil import iso_utc

bp = Blueprint("robots", __name__, url_prefix="/api/robots")


@bp.get("")
@staff_required
def list_robots():
    robots = Robot.query.order_by(Robot.id).all()
    return jsonify(robots=[_view(r) for r in robots])


def _view(r):
    return {
        "id": r.id,
        "code": r.robot_code,
        "status": r.status,
        "lat": float(r.current_latitude) if r.current_latitude is not None else None,
        "lng": float(r.current_longitude) if r.current_longitude is not None else None,
        "updatedAt": iso_utc(r.updated_at),
    }


def _change(robot_id, event):
    robot = Fleet.get(robot_id)
    if robot is None:
        return jsonify(error="not_found", message="Robot not found."), 404
    if not robot.trigger(event):
        return jsonify(error="invalid_transition",
                       message=f"Can't do that while the Robot is {robot.state.replace('_', ' ')}."), 409
    return None


@bp.post("/<int:robot_id>/offline")
@staff_required
def take_offline(robot_id):
    """Take a Robot in the depot out of service (maintenance). Robots on a Trip can't be pulled."""
    error = _change(robot_id, "manual_override")
    if error:
        return error
    rebalance_reserve()
    return jsonify(_view(db.session.get(Robot, robot_id)))


@bp.post("/<int:robot_id>/online")
@staff_required
def bring_online(robot_id):
    """Maintenance finished: the Robot rejoins the depot."""
    error = _change(robot_id, "maintenance_resolved")
    if error:
        return error
    rebalance_reserve()
    return jsonify(_view(db.session.get(Robot, robot_id)))
