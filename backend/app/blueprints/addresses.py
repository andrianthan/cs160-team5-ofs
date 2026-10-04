# T11 — Address Validation and Delivery Zone check. Owner: Than Andrian.
# LLD 2 §2.2: geocode() via Mapbox, inside_delivery_zone() point-in-polygon. BR-5.
from urllib.parse import quote

import requests
from flask import Blueprint, current_app, jsonify, request

bp = Blueprint("addresses", __name__, url_prefix="/api/addresses")

# Rough Downtown San Jose boundary for BR-5 — a bounding rectangle around the
# core downtown grid (St James Park / N First St to Diridon / SAP Center,
# Guadalupe Pkwy to roughly 4th St). Not survey-accurate; good enough for the
# demo and matches the Delivery Zone described in docs/part1 and CONTEXT.md.
# Points are (lng, lat), closed implicitly (ray casting doesn't need the first
# point repeated).
DELIVERY_ZONE_POLYGON = [
    (-121.9015, 37.3455),  # NW — near St James Park
    (-121.8820, 37.3455),  # NE — near N 4th St
    (-121.8820, 37.3220),  # SE — near I-280
    (-121.9015, 37.3220),  # SW — near Diridon / SAP Center
]


def geocode(address):
    """Mapbox Geocoding. Returns {"lat", "lng", "place_name"} or None on no match."""
    token = current_app.config.get("MAPBOX_ACCESS_TOKEN")
    if not token:
        current_app.logger.warning("MAPBOX_ACCESS_TOKEN not set — geocoding disabled")
        return None

    url = f"https://api.mapbox.com/geocoding/v5/mapbox.places/{quote(address)}.json"
    try:
        resp = requests.get(url, params={"access_token": token, "limit": 1}, timeout=5)
        resp.raise_for_status()
    except requests.RequestException:
        current_app.logger.exception("Mapbox geocoding request failed")
        return None

    features = resp.json().get("features") or []
    if not features:
        return None

    lng, lat = features[0]["center"]
    return {"lat": lat, "lng": lng, "place_name": features[0].get("place_name", address)}


def inside_delivery_zone(geo):
    """Point-in-polygon via ray casting against DELIVERY_ZONE_POLYGON. BR-5."""
    x, y = geo["lng"], geo["lat"]
    poly = DELIVERY_ZONE_POLYGON
    inside = False
    j = len(poly) - 1
    for i, (xi, yi) in enumerate(poly):
        xj, yj = poly[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi) + xi:
            inside = not inside
        j = i
    return inside


@bp.post("/validate")
def validate_address():
    data = request.get_json(silent=True) or {}
    address = data.get("address")
    address = address.strip() if isinstance(address, str) else ""

    if not address:
        return jsonify(error="invalid_address", message="Enter a delivery address."), 400

    geo = geocode(address)
    if geo is None:
        return jsonify(error="ADDRESS_NOT_FOUND", message="We couldn't find that address."), 404

    if not inside_delivery_zone(geo):
        return jsonify(
            error="OUTSIDE_DELIVERY_ZONE",
            message="This address is outside the Downtown San Jose Delivery Zone.",
        ), 422

    return jsonify(valid=True, address=geo["place_name"], lat=geo["lat"], lng=geo["lng"])
