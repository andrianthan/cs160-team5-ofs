# T15 — Robot fleet status for the staff dashboard.
from flask import Blueprint, jsonify
from sqlalchemy.exc import IntegrityError

from .auth import manager_required, staff_required
from ..extensions import db
from ..models import Robot, Trip
from ..robot import IN_DEPOT, OFFLINE, Robot as Fleet, next_robot_code, rebalance_reserve
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


# ---- adding and removing Robots (Managers): a new Robot starts parked at the store ----

@bp.post("")
@manager_required
def add_robot():
    for _ in range(3):  # two Managers adding at once can pick the same code: the unique index refuses one
        try:
            robot = Fleet.create(next_robot_code())
            db.session.commit()
            break
        except IntegrityError:
            db.session.rollback()
    else:
        return jsonify(error="conflict", message="Couldn't add a Robot right now. Try again."), 409
    rebalance_reserve()  # a second Robot in the depot releases the reserve
    return jsonify(_view(db.session.get(Robot, robot.model.id))), 201


@bp.delete("/<int:robot_id>")
@manager_required
def remove_robot(robot_id):
    """Take a Robot out of the fleet for good. Only from the depot (or offline), never while on a Trip.
    Its past Trips keep their history but no longer point at it."""
    robot = db.session.get(Robot, robot_id)
    if robot is None:
        return jsonify(error="not_found", message="Robot not found."), 404
    if robot.status not in (*IN_DEPOT, OFFLINE):
        return jsonify(error="invalid_transition",
                       message=f"{robot.robot_code} is {robot.status.replace('_', ' ')}. Wait until it's back at the store."), 409
    Trip.query.filter_by(robot_id=robot_id).update({"robot_id": None})
    code = robot.robot_code
    db.session.delete(robot)
    db.session.commit()
    rebalance_reserve()  # the depot may now have a single Robot left
    return jsonify(removed=code)
