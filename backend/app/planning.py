# T13 — Delivery Planning: grouping prepared Orders into Trips (CONTEXT.md "Delivery Planning", BR-2/6/7).
#   - Nearby: an Order joins an open Trip only if it's within TRIP_GROUP_RADIUS_KM of every Order
#     already on it, so a Robot never crosses downtown for one stop. The closest such Trip wins.
#   - Capacity: at most TRIP_MAX_ORDERS Orders and TRIP_MAX_WEIGHT_LB per Trip.
#   - Deadline: TRIP_DISPATCH_TIMEOUT_MIN after a Trip's oldest Order was placed, or once full, the
#     Trip is locked as "ready" for an Employee to Dispatch. There's no background scheduler, so
#     lock_due_trips() runs whenever Trips are listed or an Order is prepared.
# Nothing here commits; the calling route does, so each step is all-or-nothing.
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from math import asin, cos, radians, sin, sqrt

from .config import Config
from .extensions import db
from .models import Order, Trip
from .models.order import MANUAL_REVIEW, PLANNED
from .models.trip import NOT_DISPATCHED, OPEN, READY
from .timeutil import as_utc

EARTH_RADIUS_KM = 6371.0


def distance_km(lat1, lng1, lat2, lng2):
    """Straight-line (haversine) distance. Plenty for a ~2.5 km zone; road routing is Dispatch's job."""
    dlat, dlng = radians(lat2 - lat1), radians(lng2 - lng1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlng / 2) ** 2
    return 2 * EARTH_RADIUS_KM * asin(sqrt(a))


def trip_deadline(trip):
    """BR-7: when the Trip must be dispatched, counted from its oldest Order's placement. None if empty."""
    if not trip.orders:
        return None
    oldest = min(as_utc(o.created_at) for o in trip.orders)
    return oldest + timedelta(minutes=Config.TRIP_DISPATCH_TIMEOUT_MIN)


def _is_full(trip):
    return (len(trip.orders) >= Config.TRIP_MAX_ORDERS
            or sum((o.weight_lb for o in trip.orders), Decimal("0")) >= Config.TRIP_MAX_WEIGHT_LB)


def _lock(trip, reason, now):
    trip.status, trip.ready_reason, trip.ready_at = READY, reason, now


def lock_due_trips(now=None):
    """Lock every open Trip whose deadline has passed. Returns the Trips it locked."""
    now = now or datetime.now(timezone.utc)
    locked = []
    for trip in Trip.query.filter_by(status=OPEN).all():
        deadline = trip_deadline(trip)
        if deadline is not None and deadline <= now:
            _lock(trip, "deadline", now)
            locked.append(trip)
    return locked


def _fits(trip, order):
    """Room left, and the Order is within the radius of every Order already on the Trip.
    Returns the farthest distance (for picking the tightest Trip), or None if it doesn't fit."""
    if len(trip.orders) >= Config.TRIP_MAX_ORDERS:
        return None
    weight = sum((o.weight_lb for o in trip.orders), Decimal("0"))
    if weight + order.weight_lb > Config.TRIP_MAX_WEIGHT_LB:
        return None
    farthest = max(
        (distance_km(order.delivery_lat, order.delivery_lng, o.delivery_lat, o.delivery_lng) for o in trip.orders),
        default=0.0,
    )
    return farthest if farthest <= Config.TRIP_GROUP_RADIUS_KM else None


def assign_to_trip(order, now=None):
    """Put a prepared Order on the closest open Trip it fits, or open a new Trip.

    Returns the Trip, or None when the Order alone is over the Robot limit (it goes to Manual Review).
    Sets the Order to Planned. Locks the Trip as ready if this filled it.
    """
    if order.weight_lb > Config.TRIP_MAX_WEIGHT_LB:
        order.status = MANUAL_REVIEW
        return None

    now = now or datetime.now(timezone.utc)
    lock_due_trips(now)  # an overdue Trip must not take more Orders

    # Lock the open Trips (and reload them) so two Employees preparing at once can't both take a
    # Trip's last slot. Row locks are a no-op on SQLite, which only allows one writer anyway.
    open_trips = (Trip.query.filter_by(status=OPEN).order_by(Trip.created_at, Trip.id)
                  .populate_existing().with_for_update().all())
    scored = [(d, i, t) for i, t in enumerate(open_trips) if (d := _fits(t, order)) is not None]
    if scored:
        trip = min(scored, key=lambda s: (s[0], s[1]))[2]  # closest; oldest Trip on a tie
    else:
        trip = Trip()
        db.session.add(trip)

    order.trip = trip
    order.status = PLANNED
    db.session.flush()
    db.session.refresh(trip)  # trip.orders now includes this Order
    if _is_full(trip):
        _lock(trip, "full", now)
    return trip


def leave_trip(order):
    """Take an Order off its (not yet dispatched) Trip, dropping the Trip if it's left empty."""
    trip = order.trip
    order.trip = None
    if trip is not None and trip.status in NOT_DISPATCHED:
        db.session.flush()
        db.session.refresh(trip)
        if not trip.orders:
            db.session.delete(trip)
