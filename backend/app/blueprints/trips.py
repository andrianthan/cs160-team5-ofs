# T13 — Delivery Planning and trip grouping. Owner: Notario Ethan Rodriguez.
# LLD 3: trip grouping loop (oldest Order first, nearest neighbors, BR-2/BR-6),
# 30-min dispatch timer (BR-7). T14 Route Optimizer (Mapbox Optimization) and
# T15 Robot Fleet simulator feed into these same endpoints.
# Grouping itself lives in app/planning.py (shared with POST /api/orders/<id>/prepare).
# The earlier Mapbox nearest-neighbor draft (commit 49017d6) is the starting point for T14 stop ordering.
from datetime import datetime, timezone

from flask import Blueprint, jsonify

from .auth import staff_required
from ..extensions import db
from ..models import Trip
from ..models.order import OUT_FOR_DELIVERY
from ..models.trip import DISPATCHED, NOT_DISPATCHED, OPEN, READY
from ..planning import lock_due_trips, trip_deadline
from ..timeutil import iso_utc

bp = Blueprint("trips", __name__, url_prefix="/api/trips")


def _error(code, message, status):
    return jsonify(error=code, message=message), status


def _view(trip, now):
    deadline = trip_deadline(trip)
    out = trip.to_dict()
    out["deadline"] = deadline.isoformat() if deadline else None
    out["overdue"] = bool(deadline and deadline <= now and trip.status in NOT_DISPATCHED)
    out["orders"] = [
        {
            "id": o.id,
            "customerName": o.user.name,
            "status": o.status,
            "weightLb": float(o.weight_lb),
            "deliveryAddress": o.delivery_address,
            "deliveryLat": o.delivery_lat,
            "deliveryLng": o.delivery_lng,
            "createdAt": iso_utc(o.created_at),
        }
        for o in trip.orders
    ]
    return out


@bp.get("")
@staff_required
def list_trips():
    """Dispatch page: every Trip not yet completed. Ready (full or past deadline) first, then open, then out."""
    now = datetime.now(timezone.utc)
    if lock_due_trips(now):
        db.session.commit()

    rank = {READY: 0, OPEN: 1, DISPATCHED: 2}
    trips = Trip.query.filter(Trip.status.in_(rank)).all()
    trips.sort(key=lambda t: (rank[t.status], t.created_at, t.id))
    return jsonify(trips=[_view(t, now) for t in trips])


@bp.post("/<int:trip_id>/dispatch")
@staff_required
def dispatch_trip(trip_id):
    """An Employee confirms the Robot is loaded and sends the Trip out (CONTEXT.md "Dispatch")."""
    trip = db.session.get(Trip, trip_id)
    if trip is None:
        return _error("not_found", "Trip not found.", 404)
    if trip.status not in NOT_DISPATCHED:
        return _error("invalid_transition", f"This trip is already {trip.status}.", 409)
    if not trip.orders:
        return _error("empty_trip", "This trip has no orders.", 409)

    now = datetime.now(timezone.utc)
    trip.status, trip.dispatched_at = DISPATCHED, now
    for order in trip.orders:
        order.status = OUT_FOR_DELIVERY
    db.session.commit()
    return jsonify(_view(trip, now))
