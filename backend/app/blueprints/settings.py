# T20 — Delivery Pause. Owner: Nateras Jorge. BR-9: disables checkout, notice shown.
from flask import Blueprint, jsonify

bp = Blueprint("settings", __name__, url_prefix="/api/settings")


@bp.put("/delivery-pause")
def set_delivery_pause():
    return jsonify(error="not_implemented"), 501
