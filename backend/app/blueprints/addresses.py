# T11 — Address Validation and Delivery Zone check. Owner: Than Andrian.
# LLD 2 §2.2: geocode() via Mapbox, inside_delivery_zone() point-in-polygon. BR-5.
from flask import Blueprint, jsonify

bp = Blueprint("addresses", __name__, url_prefix="/api/addresses")


@bp.post("/validate")
def validate_address():
    return jsonify(error="not_implemented"), 501
