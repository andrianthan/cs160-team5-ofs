# T13 — Delivery Planning and trip grouping. Owner: Notario Ethan Rodriguez.
# LLD 3: trip grouping loop (oldest Order first, nearest neighbors, BR-2/BR-6),
# 30-min dispatch timer (BR-7). T14 Route Optimizer (Mapbox Optimization) and
# T15 Robot Fleet simulator feed into these same endpoints.
from flask import Blueprint, jsonify

bp = Blueprint("trips", __name__, url_prefix="/api/trips")


@bp.get("")
def list_trips():
    return jsonify(error="not_implemented"), 501


@bp.post("/<trip_id>/dispatch")
def dispatch_trip(trip_id):
    return jsonify(error="not_implemented"), 501
