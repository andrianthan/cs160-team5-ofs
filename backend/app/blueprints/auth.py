# T04 — Auth and Roles backend. Owner: Karnani Shresthkumar.
# LLD 1 (docs/part2): hash_password(), create_session(), require_role(...).
from functools import wraps

from email_validator import EmailNotValidError, validate_email
from flask import Blueprint, jsonify, request
from flask_login import current_user, login_user, logout_user
from werkzeug.security import generate_password_hash

from ..extensions import db
from ..models.user import CUSTOMER, EMPLOYEE, MANAGER, User

bp = Blueprint("auth", __name__, url_prefix="/api/auth")

MIN_PASSWORD_LENGTH = 8

_IMPLIED_ROLES = {
    CUSTOMER: {CUSTOMER},
    EMPLOYEE: {EMPLOYEE},
    MANAGER: {MANAGER, EMPLOYEE},
}

def hash_password(password):
    return generate_password_hash(password)

def create_session(user):
    login_user(user)

def require_role(*roles):
    """401 if not logged in, 403 if the role isn't allowed. A manager passes "employee" checks."""

    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if not current_user.is_authenticated:
                return jsonify(error="unauthorized"), 401
            if not _IMPLIED_ROLES.get(current_user.role, set()) & set(roles):
                return jsonify(error="forbidden"), 403
            return view(*args, **kwargs)

        return wrapped

    return decorator

staff_required = require_role(EMPLOYEE) 

def _error(code, message, status):
    return jsonify(error=code, message=message), status


def _body():
    data = request.get_json(silent=True)
    return data if isinstance(data, dict) else {}


def _text(data, key):
    value = data.get(key)
    return value.strip() if isinstance(value, str) else ""

@bp.post("/register")
def register():
    data = _body()
    name = _text(data, "name")
    password = data.get("password")

    try:
        email = validate_email(_text(data, "email"), check_deliverability=False).normalized.lower()
    except EmailNotValidError:
        return _error("invalid_email", "Enter a valid email address", 400)

    if not name:
        return _error("invalid_name", "Enter a valid name", 400)

    if not isinstance(password, str) or len(password) < MIN_PASSWORD_LENGTH:
        return _error("invalid_password", "Enter a valid password", 400)

    if User.query.filter_by(email=email).first():
        return _error("email_taken", "An account with this email address has been made already", 409)

    user = User(email=email, name=name, role=CUSTOMER)
    user.password_hash = hash_password(password)

    db.session.add(user)
    db.session.commit()

    create_session(user)

    return jsonify(user.to_dict()), 201


@bp.post("/login")
def login():
    data = _body()
    email = _text(data, "email").lower()
    password = data.get("password")

    user = User.query.filter_by(email=email).first()

    if not user or not isinstance(password, str) or not user.check_password(password):
        return _error("invalid_credentials", "Email or password is incorrect.", 401)

    portal = data.get("portal")

    if portal == "staff" and not user.is_staff:
        return _error("wrong_portal", "This is a customer account. Sign in on the storefront.", 403)
    if portal == "customer" and user.is_staff:
        return _error("wrong_portal", "This is a staff account. Sign in on the staff dashboard.", 403)

    create_session(user)

    return jsonify(user.to_dict())


@bp.post("/logout")
def logout():
    logout_user()
    return jsonify(ok=True)

@bp.get("/me")
def me():
    if not current_user.is_authenticated:
        return _error("unauthorized", "Not signed in.", 401)
    
    return jsonify(current_user.to_dict())

