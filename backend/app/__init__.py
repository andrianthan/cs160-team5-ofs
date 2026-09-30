from flask import Flask, jsonify

from .config import Config
from .extensions import db, migrate, cors


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)
    cors.init_app(app, resources={r"/api/*": {"origins": "*"}})  # tighten before prod

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
