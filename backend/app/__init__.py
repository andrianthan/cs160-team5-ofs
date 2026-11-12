from flask import Flask, jsonify
from sqlalchemy.engine import make_url

from .config import Config
from .extensions import db, migrate, cors, login_manager


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    # The URI may be a string or a SQLAlchemy URL object (the migration tests pass one).
    if make_url(app.config["SQLALCHEMY_DATABASE_URI"]).get_backend_name() == "postgresql":
        app.config.setdefault("SQLALCHEMY_ENGINE_OPTIONS", app.config["POSTGRES_ENGINE_OPTIONS"])

    db.init_app(app)
    migrate.init_app(app, db)
    cors.init_app(app, resources={r"/api/*": {"origins": "*"}})  # tighten before prod

    login_manager.init_app(app)

    from .models import User

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    @login_manager.unauthorized_handler
    def unauthorized():
        # API returns JSON, never a redirect to a login page.
        return jsonify(error="unauthorized"), 401

    from .blueprints import auth, products, cart, addresses, payments, orders, trips, tracking, reports, settings

    for bp in (
        auth.bp, products.bp, cart.bp, addresses.bp, payments.bp,
        orders.bp, trips.bp, tracking.bp, reports.bp, settings.bp,
    ):
        app.register_blueprint(bp)

    @app.get("/api/health")
    def health():
        return jsonify(status="ok")

    return app
