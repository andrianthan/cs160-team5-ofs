# T15 — Robot fleet status for the staff dashboard.
from flask import Blueprint, jsonify

from .auth import staff_required
from ..models import Robot
from ..timeutil import iso_utc

bp = Blueprint("robots", __name__, url_prefix="/api/robots")


@bp.get("")
@staff_required
def list_robots():
    robots = Robot.query.order_by(Robot.id).all()
    return jsonify(robots=[
        {
            "id": r.id,
            "code": r.robot_code,
            "status": r.status,
            "lat": float(r.current_latitude) if r.current_latitude is not None else None,
            "lng": float(r.current_longitude) if r.current_longitude is not None else None,
            "updatedAt": iso_utc(r.updated_at),
        }
        for r in robots
    ])
