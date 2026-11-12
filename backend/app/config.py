import os


class Config:
    """Base config, read from environment. See .env.example for the full list."""

    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-me")
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", "postgresql://ofs:ofs@localhost:5432/ofs_dev"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Connection pool for a remote PostgreSQL (Supabase). create_app() applies these only to
    # postgresql:// URLs; SQLite (local demo.db, the in-memory test DB) doesn't use a pool like this.
    POSTGRES_ENGINE_OPTIONS = {
        # Test each pooled connection before reusing it. Supabase closes idle connections, and
        # without this the first request after a quiet spell fails with "server closed the
        # connection unexpectedly".
        "pool_pre_ping": True,
        # Replace connections older than 5 minutes before the server drops them.
        "pool_recycle": 300,
        # At most 5 connections per backend process (default is 15). Supabase's free tier allows
        # only a few dozen in total, shared by every teammate's backend and the email threads.
        "pool_size": 3,
        "max_overflow": 2,
    }

    STRIPE_SECRET_KEY = os.environ.get("STRIPE_SECRET_KEY")
    STRIPE_WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET")
    MAPBOX_ACCESS_TOKEN = os.environ.get("MAPBOX_ACCESS_TOKEN")

    SMTP_HOST = os.environ.get("SMTP_HOST")
    SMTP_PORT = int(os.environ.get("SMTP_PORT", 587))
    SMTP_USERNAME = os.environ.get("SMTP_USERNAME")
    SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD")
    SMTP_FROM = os.environ.get("SMTP_FROM")
    SMTP_STARTTLS = os.environ.get("SMTP_STARTTLS", "1") != "0"
    SMTP_TIMEOUT_S = 10

    # T17: emails go out from a background thread so a slow mail server never delays checkout.
    NOTIFICATIONS_ASYNC = True
    NOTIFY_MAX_ATTEMPTS = 3
    NOTIFY_RETRY_DELAY_S = 2

    # BR-1..BR-9 constants (docs/part2 shared draft, business rules table)
    DELIVERY_FEE_THRESHOLD_LB = 20
    DELIVERY_FEE_AMOUNT = 10
    TRIP_MAX_ORDERS = 10
    TRIP_MAX_WEIGHT_LB = 200
    TRIP_DISPATCH_TIMEOUT_MIN = 30
    TRIP_GROUP_RADIUS_KM = 0.5  # every Order on a Trip is within this of the others


class TestConfig(Config):
    TESTING = True
    NOTIFICATIONS_ASYNC = False
    NOTIFY_RETRY_DELAY_S = 0
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
