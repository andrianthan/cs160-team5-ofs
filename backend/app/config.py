import os


class Config:
    """Base config, read from environment. See .env.example for the full list."""

    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-me")
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", "postgresql://ofs:ofs@localhost:5432/ofs_dev"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    STRIPE_SECRET_KEY = os.environ.get("STRIPE_SECRET_KEY")
    STRIPE_WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET")
    MAPBOX_ACCESS_TOKEN = os.environ.get("MAPBOX_ACCESS_TOKEN")

    SMTP_HOST = os.environ.get("SMTP_HOST")
    SMTP_PORT = int(os.environ.get("SMTP_PORT", 587))
    SMTP_USERNAME = os.environ.get("SMTP_USERNAME")
    SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD")
    SMTP_FROM = os.environ.get("SMTP_FROM")

    # BR-1..BR-9 constants (docs/part2 shared draft, business rules table)
    DELIVERY_FEE_THRESHOLD_LB = 20
    DELIVERY_FEE_AMOUNT = 10
    TRIP_MAX_ORDERS = 10
    TRIP_MAX_WEIGHT_LB = 200
    TRIP_DISPATCH_TIMEOUT_MIN = 30


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
