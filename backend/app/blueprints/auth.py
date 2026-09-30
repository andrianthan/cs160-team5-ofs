# T04 — Auth and Roles backend. Owner: Karnani Shresthkumar.
# LLD 1 (docs/part2): hash_password(), create_session(), require_role(...).
from flask import Blueprint, jsonify

bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@bp.post("/register")
def register():
    return jsonify(error="not_implemented"), 501


@bp.post("/login")
def login():
    return jsonify(error="not_implemented"), 501


@bp.post("/logout")
def logout():
    return jsonify(error="not_implemented"), 501
