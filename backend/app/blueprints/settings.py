# T20 — Delivery Pause. Owner: Nateras Jorge. BR-9: disables checkout, notice shown.
# BR-9: Managers can pause or resume new deliveries.

from flask import Blueprint, jsonify, request
from flask_login import current_user

from .auth import require_role
from ..extensions import db
from ..models.delivery_settings import DeliverySettings, deliveries_paused
from ..models.user import MANAGER

bp = Blueprint("settings", __name__, url_prefix="/api/settings")


@bp.get("/delivery-pause")
def get_delivery_pause():
    return jsonify(paused=deliveries_paused()), 200


@bp.put("/delivery-pause")
@require_role(MANAGER)
def set_delivery_pause():
    data = request.get_json(silent=True)

    if not isinstance(data, dict) or type(data.get("paused")) is not bool:
        return jsonify(error="INVALID_DELIVERY_PAUSE"), 400

    settings = db.session.get(DeliverySettings, 1)

    if settings is None:
        settings = DeliverySettings(id=1)
        db.session.add(settings)

    settings.paused = data["paused"]
    settings.updated_by = current_user.id

    db.session.commit()

    return jsonify(
        paused=settings.paused,
        updatedBy=settings.updated_by
    ), 200
