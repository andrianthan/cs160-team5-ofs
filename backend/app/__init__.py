from flask import Flask, jsonify, request
from werkzeug.exceptions import HTTPException
from sqlalchemy.engine import make_url

from .config import Config
from .extensions import db, migrate, cors, login_manager


def _has_nul(value):
    """True if any string in a parsed JSON body (keys included) contains a NUL character."""
    if isinstance(value, str):
        return "\x00" in value
    if isinstance(value, dict):
        return any(_has_nul(k) or _has_nul(v) for k, v in value.items())
    if isinstance(value, list):
        return any(_has_nul(v) for v in value)
    return False


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    # The URI may be a string or a SQLAlchemy URL object (the migration tests pass one).
    if make_url(app.config["SQLALCHEMY_DATABASE_URI"]).get_backend_name() == "postgresql":
        app.config.setdefault("SQLALCHEMY_ENGINE_OPTIONS", app.config["POSTGRES_ENGINE_OPTIONS"])

    db.init_app(app)
    migrate.init_app(app, db)
    cors.init_app(app, resources={r"/api/*": {"origins": app.config["CORS_ORIGINS"]}})

    login_manager.init_app(app)

    from .models import User

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    @login_manager.unauthorized_handler
    def unauthorized():
        # API returns JSON, never a redirect to a login page.
        return jsonify(error="unauthorized"), 401

    from .blueprints import auth, products, cart, addresses, payments, orders, trips, tracking, reports, settings, robots

    for bp in (
        auth.bp, products.bp, cart.bp, addresses.bp, payments.bp,
        orders.bp, trips.bp, tracking.bp, reports.bp, settings.bp, robots.bp,
    ):
        app.register_blueprint(bp)

    @app.before_request
    def reject_nul_characters():
        # PostgreSQL can't store a NUL (\x00) in text: psycopg2 raises, and the request became a 500
        # on every endpoint that saves a string (found by tests/test_stress_api.py). Refuse it up front.
        if request.is_json and _has_nul(request.get_json(silent=True)):
            return jsonify(error="invalid_text", message="Text can't contain NUL characters."), 400
        return None

    @app.errorhandler(HTTPException)
    def api_http_error(e):
        # Unknown URLs, wrong methods, oversized bodies: answer the API with JSON, not Flask's HTML page.
        if request.path.startswith("/api/"):
            return jsonify(error=e.name.lower().replace(" ", "_"), message=e.description), e.code
        return e

    @app.errorhandler(Exception)
    def api_unexpected_error(e):
        # Never send a stack trace or internal detail to the client.
        app.logger.exception("Unhandled error on %s %s", request.method, request.path)
        return jsonify(error="server_error", message="Something went wrong on our side. Please try again."), 500

    @app.get("/api/health")
    def health():
        return jsonify(status="ok")

    return app
