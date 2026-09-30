# T19 — Manager Reports. Owner: Than Andrian.
# LLD 4: metric definitions (on-time rate, delivery duration, trip utilization,
# product demand) must match the Test Plan's metric definitions exactly.
from flask import Blueprint, jsonify

bp = Blueprint("reports", __name__, url_prefix="/api/reports")


@bp.get("/sales")
def sales_report():
    return jsonify(error="not_implemented"), 501


@bp.get("/inventory")
def inventory_report():
    return jsonify(error="not_implemented"), 501


@bp.get("/delivery")
def delivery_report():
    return jsonify(error="not_implemented"), 501
