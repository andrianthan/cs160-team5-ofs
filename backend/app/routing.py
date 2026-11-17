# T14 — Route Optimizer. Orders a Trip's stops and draws the Robot's route.
# Mapbox Optimization API (roundtrip from the store) when a token is set; otherwise, or if Mapbox
# errors or times out, a nearest-neighbour ordering with straight-line legs so Dispatch never blocks
# on a third party. Creates the Trip's TripStops and sets route_geometry / estimated_duration_minutes.
# Nothing here commits; the calling route does.
from datetime import datetime, timedelta, timezone

import requests
from flask import current_app

from .extensions import db
from .models import TripStop
from .planning import distance_km

MAPBOX_TIMEOUT_S = 5


def _depot():
    cfg = current_app.config
    return cfg["STORE_LAT"], cfg["STORE_LNG"]


def _nearest_neighbour(depot, orders, speed_kmh):
    """Greedy order from the depot. Returns (ordered orders, leg seconds, [lng, lat] path)."""
    remaining, ordered, legs = list(orders), [], []
    here = depot
    while remaining:
        nxt = min(remaining, key=lambda o: distance_km(*here, o.delivery_lat, o.delivery_lng))
        legs.append(distance_km(*here, nxt.delivery_lat, nxt.delivery_lng) / speed_kmh * 3600)
        remaining.remove(nxt)
        ordered.append(nxt)
        here = (nxt.delivery_lat, nxt.delivery_lng)
    legs.append(distance_km(*here, *depot) / speed_kmh * 3600)  # back to the store
    path = [[depot[1], depot[0]]] + [[o.delivery_lng, o.delivery_lat] for o in ordered] + [[depot[1], depot[0]]]
    return ordered, legs, path


def _mapbox(token, depot, orders):
    """Returns (ordered orders, leg seconds, path) or None on any failure."""
    coords = [(depot[1], depot[0])] + [(o.delivery_lng, o.delivery_lat) for o in orders]
    path = ";".join(f"{lng},{lat}" for lng, lat in coords)
    url = f"https://api.mapbox.com/optimized-trips/v1/mapbox/driving/{path}"
    params = {"access_token": token, "geometries": "geojson", "overview": "full",
              "roundtrip": "true", "source": "first"}
    try:
        resp = requests.get(url, params=params, timeout=MAPBOX_TIMEOUT_S)
        data = resp.json()
        if resp.status_code != 200 or data.get("code") != "Ok":
            raise ValueError(data.get("message") or data.get("code") or resp.status_code)
        waypoints = data["waypoints"]  # same order as the input coordinates
        trip = data["trips"][0]
        by_position = sorted(range(1, len(coords)), key=lambda i: waypoints[i]["waypoint_index"])
        ordered = [orders[i - 1] for i in by_position]
        legs = [leg["duration"] for leg in trip["legs"]]
        if len(legs) != len(orders) + 1:
            raise ValueError("unexpected leg count")
        return ordered, legs, trip["geometry"]["coordinates"]
    except Exception as exc:  # network, bad JSON, unexpected shape: all mean "use the fallback"
        current_app.logger.warning("Mapbox optimization failed (%s); using nearest-neighbour route", exc)
        return None


def optimize_route(trip, now=None):
    """Create the Trip's stops in visiting order. No-op if it already has them."""
    if trip.stops:
        return trip
    now = now or datetime.now(timezone.utc)
    depot = _depot()
    orders = list(trip.orders)
    result = None
    token = current_app.config.get("MAPBOX_ACCESS_TOKEN")
    if token:
        result = _mapbox(token, depot, orders)
    if result is None:
        result = _nearest_neighbour(depot, orders, current_app.config["ROBOT_SPEED_KMH"])
    ordered, legs, path = result

    elapsed = 0.0
    for number, (order, leg) in enumerate(zip(ordered, legs), start=1):
        elapsed += leg
        trip.stops.append(TripStop(
            order_id=order.id, stop_number=number,
            latitude=order.delivery_lat, longitude=order.delivery_lng,
            estimated_arrival=now + timedelta(seconds=elapsed),
        ))
    total = elapsed + legs[-1]
    trip.route_geometry = {"type": "LineString", "coordinates": path}
    trip.estimated_duration_minutes = max(1, round(total / 60))
    db.session.flush()
    return trip
