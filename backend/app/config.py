import os

from dotenv import load_dotenv

load_dotenv()

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
        # Make a dead connection fail in seconds instead of hanging. After the laptop sleeps (or
        # changes Wi-Fi), the pooled sockets to Supabase are dead, but nothing tells this side: a
        # query, or even pool_pre_ping's test, sits waiting for TCP to give up (~15 min). With
        # only 4 gunicorn threads, a few polling pages tie them all up and the whole API freezes.
        "connect_args": {
            "connect_timeout": 10,         # seconds to open a new connection
            "keepalives": 1,               # detect a dead idle connection...
            "keepalives_idle": 30,         # ...after 30s idle,
            "keepalives_interval": 10,     # probing every 10s,
            "keepalives_count": 3,         # and giving up after 3 misses
            "tcp_user_timeout": 30000,     # ms: give up on a sent query nobody acknowledges
        },
    }

    STRIPE_SECRET_KEY = os.environ.get("STRIPE_SECRET_KEY")
    STRIPE_WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET")
    MAPBOX_ACCESS_TOKEN = os.environ.get("MAPBOX_ACCESS_TOKEN")

    SMTP_HOST = os.environ.get("SMTP_HOST")
    SMTP_PORT = int(os.environ.get("SMTP_PORT", 587))
    SMTP_USERNAME = os.environ.get("SMTP_USERNAME")
    SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD")
    # Falls back to the sending address, so setting the username is enough.
    SMTP_FROM = os.environ.get("SMTP_FROM") or (
        f"Basil <{SMTP_USERNAME}>" if SMTP_USERNAME else None
    )
    SMTP_STARTTLS = os.environ.get("SMTP_STARTTLS", "1") != "0"
    # Gmail's first TLS handshake can take longer than 10s, which failed the send before the
    # password was even checked.
    SMTP_TIMEOUT_S = int(os.environ.get("SMTP_TIMEOUT_S", 30))

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

    # T14/T15: the store every Robot leaves from and returns to (downtown San Jose by default).
    STORE_LAT = float(os.environ.get("STORE_LAT", 37.3352))
    STORE_LNG = float(os.environ.get("STORE_LNG", -121.8811))
    ROBOT_SPEED_KMH = 8.0  # used for ETAs when Mapbox isn't available
    ROBOT_SIM_ENABLED = True  # off: Robots are assigned but never drive (unit tests of Dispatch)
    ROBOT_SIM_ASYNC = True  # run Trips on a background thread; tests run them inline
    # The speed knobs are env-configurable so a demo can slow the Robot down enough to
    # actually watch it move on the customer map (which refreshes every 10 seconds).
    ROBOT_SIM_TICK_S = float(os.environ.get("ROBOT_SIM_TICK_S", 1.0))  # seconds between position updates (0 = no waiting)
    ROBOT_SIM_STEPS = int(os.environ.get("ROBOT_SIM_STEPS", 10))  # position updates per leg of the route
    ROBOT_SIM_DWELL_S = float(os.environ.get("ROBOT_SIM_DWELL_S", 3.0))  # time spent at each stop handing over the order


class TestConfig(Config):
    TESTING = True
    NOTIFICATIONS_ASYNC = False
    NOTIFY_RETRY_DELAY_S = 0
    ROBOT_SIM_ASYNC = False
    MAPBOX_ACCESS_TOKEN = None  # tests never call the real Mapbox
    ROBOT_SIM_TICK_S = 0
    ROBOT_SIM_DWELL_S = 0
    ROBOT_SIM_STEPS = 2
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
