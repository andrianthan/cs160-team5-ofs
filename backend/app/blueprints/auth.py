# T04 — Auth and Roles backend. Owner: Karnani Shresthkumar.
# LLD 1 (docs/part2): hash_password(), create_session(), require_role(...).
import threading
import time
from functools import wraps

from email_validator import EmailNotValidError, validate_email
from flask import Blueprint, current_app, jsonify, request
from flask_login import current_user, login_user, logout_user
from sqlalchemy.exc import IntegrityError
from werkzeug.security import generate_password_hash

from ..extensions import db
from ..models.user import CUSTOMER, EMPLOYEE, MANAGER, User

bp = Blueprint("auth", __name__, url_prefix="/api/auth")

MIN_PASSWORD_LENGTH = 8
MAX_PASSWORD_LENGTH = 128  # scrypt hashes whatever it is given: a 100,000-character password is a cheap way to burn CPU
MAX_NAME_LENGTH = User.name.type.length

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
manager_required = require_role(MANAGER)

def _error(code, message, status):
    return jsonify(error=code, message=message), status


def _body():
    data = request.get_json(silent=True)
    return data if isinstance(data, dict) else {}


def _text(data, key):
    value = data.get(key)
    return value.strip() if isinstance(value, str) else ""

# Failed sign-ins per account, in memory (one gunicorn process serves the API). Keyed by email rather than
# IP because behind the Apache proxy every request arrives from the proxy's address.
_failures = {}
_failures_lock = threading.Lock()


def _login_wait(email):
    """Seconds the caller must wait, or 0 when sign-in is allowed."""
    limit, window = current_app.config["LOGIN_MAX_FAILURES"], current_app.config["LOGIN_FAILURE_WINDOW_S"]
    now = time.monotonic()
    with _failures_lock:
        recent = [t for t in _failures.get(email, []) if now - t < window]
        _failures[email] = recent
        if len(recent) >= limit:
            return max(1, int(window - (now - recent[0])))
    return 0


def _login_failed(email):
    with _failures_lock:
        _failures.setdefault(email, []).append(time.monotonic())


def _login_ok(email):
    with _failures_lock:
        _failures.pop(email, None)


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
    # users.name is VARCHAR(120): a longer name was a 500 on PostgreSQL and saved whole on SQLite.
    if len(name) > MAX_NAME_LENGTH:
        return _error("invalid_name", f"Name must be at most {MAX_NAME_LENGTH} characters", 400)

    if not isinstance(password, str) or not (MIN_PASSWORD_LENGTH <= len(password) <= MAX_PASSWORD_LENGTH):
        return _error("invalid_password", f"Password must be {MIN_PASSWORD_LENGTH} to {MAX_PASSWORD_LENGTH} characters", 400)

    if User.query.filter_by(email=email).first():
        return _error("email_taken", "An account with this email address has been made already", 409)

    user = User(email=email, name=name, role=CUSTOMER)
    user.password_hash = hash_password(password)

    db.session.add(user)
    try:
        db.session.commit()
    except IntegrityError:
        # Two sign-ups with this email at the same moment both passed the check above; the unique
        # index lets one through. The other was a 500 (tests/test_stress_concurrency.py).
        db.session.rollback()
        return _error("email_taken", "An account with this email address has been made already", 409)

    create_session(user)

    return jsonify(user.to_dict()), 201


@bp.post("/login")
def login():
    data = _body()
    email = _text(data, "email").lower()
    password = data.get("password")

    wait = _login_wait(email)
    if wait:
        resp = _error("too_many_attempts", "Too many failed sign-in attempts. Try again in a few minutes.", 429)
        resp[0].headers["Retry-After"] = str(wait)
        return resp

    user = User.query.filter_by(email=email).first()

    if (
        not user
        or not isinstance(password, str)
        or len(password) > MAX_PASSWORD_LENGTH
        or not user.check_password(password)
    ):
        _login_failed(email)
        return _error("invalid_credentials", "Email or password is incorrect.", 401)
    _login_ok(email)

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

