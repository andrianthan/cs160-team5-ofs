"""Shared setup for the stress tests (test_stress_api.py, test_stress_concurrency.py). Owner: Karnani Shresthkumar.

stress_app("sqlite") is an in-memory database like conftest's. stress_app("postgresql") runs on
TEST_POSTGRES_URL (set in CI) in a fresh random schema with a pool big enough for many threads,
and drops only that schema afterwards.

Unlike conftest's `app` fixture, stress_app yields with NO app context pushed. Requests then get a
fresh context each, as in production. (If a test holds one open, Flask reuses it for every request
and Flask-Login's cached user leaks from one test client to the next.) The helpers below open a
context only around their own database work; tests do the same with `with app.app_context():`.
"""
import itertools
import json
import os
import threading
from contextlib import contextmanager
from decimal import Decimal
from uuid import uuid4

import sqlalchemy as sa
import stripe
from werkzeug.security import generate_password_hash

from app import create_app
from app.blueprints import addresses, payments
from app.config import TestConfig
from app.extensions import db
from app.models import Payment, Product, User

PASSWORD = "password123"
# A cheap hash keeps logins fast when a test signs in dozens of users; check_password reads any method.
CHEAP_HASH = generate_password_hash(PASSWORD, method="pbkdf2:sha256:1000")
DOWNTOWN = {"lat": 37.333, "lng": -121.889, "place_name": "150 S 1st St, San Jose, CA 95113"}
DATABASES = ["sqlite"] + (["postgresql"] if os.getenv("TEST_POSTGRES_URL") else [])


@contextmanager
def stress_app(kind):
    admin = schema = None

    class StressConfig(TestConfig):
        STRIPE_SECRET_KEY = "sk_test_x"
        STRIPE_WEBHOOK_SECRET = "whsec_x"

    if kind == "postgresql":
        url = sa.engine.make_url(os.environ["TEST_POSTGRES_URL"])
        schema = "ofs_stress_" + uuid4().hex
        admin = sa.create_engine(url)
        with admin.begin() as connection:
            connection.execute(sa.text(f'CREATE SCHEMA "{schema}"'))
        StressConfig.SQLALCHEMY_DATABASE_URI = url.update_query_dict({"options": f"-csearch_path={schema}"})
        StressConfig.SQLALCHEMY_ENGINE_OPTIONS = {"pool_size": 30, "max_overflow": 10}

    app = create_app(StressConfig)
    try:
        with app.app_context():
            db.create_all()
        yield app
    finally:
        with app.app_context():
            db.session.remove()
            db.engine.dispose()
        if admin is not None:
            with admin.begin() as connection:
                connection.execute(sa.text(f'DROP SCHEMA "{schema}" CASCADE'))
            admin.dispose()


class FakeStripe:
    """Stands in for Stripe and Mapbox. Safe to call from many threads at once."""

    def __init__(self, monkeypatch):
        self.lock = threading.Lock()
        self.refunds = []
        self._ids = itertools.count(1)
        monkeypatch.setattr(addresses, "geocode", lambda address: DOWNTOWN)
        monkeypatch.setattr(payments, "geocode", lambda address: DOWNTOWN)
        monkeypatch.setattr(payments, "create_payment_intent", self._create)
        monkeypatch.setattr(payments, "refund_payment_intent", self._refund)
        monkeypatch.setattr(payments, "cancel_payment_intent", lambda intent_id: None)
        monkeypatch.setattr(payments, "retrieve_payment_intent",
                            lambda intent_id: {"id": intent_id, "status": "requires_payment_method"})
        monkeypatch.setattr(stripe.Webhook, "construct_event", self._event)

    @staticmethod
    def _event(payload, sig, secret):
        """Like Stripe: a bad signature or body is rejected before the app sees it. A good one
        names its PaymentIntent in the body, so each request can settle a different payment."""
        if sig != "t":
            raise stripe.error.SignatureVerificationError("bad signature", sig)
        try:
            intent_id = json.loads(payload)["id"]
        except (ValueError, TypeError, KeyError) as exc:
            raise ValueError("bad payload") from exc
        return {"type": "payment_intent.succeeded", "data": {"object": {"id": intent_id}}}

    def _create(self, amount_cents, key, metadata):
        with self.lock:
            n = next(self._ids)
        return {"id": f"pi_{n}", "client_secret": f"secret_{n}"}

    def _refund(self, intent_id, key):
        with self.lock:
            self.refunds.append(intent_id)


def make_user(app, email, role="customer"):
    with app.app_context():
        user = User(email=email, name=email.split("@")[0], role=role, password_hash=CHEAP_HASH)
        db.session.add(user)
        db.session.commit()
        return user.id


def make_product(app, name="Apple", stock=10, price="1.50", weight="0.50"):
    with app.app_context():
        product = Product(name=name, category="Fruit", price=Decimal(price), weight_lb=Decimal(weight),
                          stock_qty=stock)
        db.session.add(product)
        db.session.commit()
        return product.product_id


def signed_in(app, email):
    """A test client with its own session cookie, so each thread can act as a different person."""
    client = app.test_client()
    resp = client.post("/api/auth/login", json={"email": email, "password": PASSWORD})
    assert resp.status_code == 200, resp.get_json()
    return client


def call(client, method, path, body=None, raw=None, query=None):
    """(status, detail). TESTING re-raises what production turns into a 500, so catch it here."""
    kwargs = {"query_string": query} if query else {}
    if raw is not None:
        kwargs.update(data=raw, content_type="application/json")
    elif body is not None:
        kwargs["json"] = body
    try:
        return client.open(path, method=method, **kwargs).status_code, None
    except Exception as exc:  # noqa: BLE001 - any uncaught error is a 500 for the user
        return 500, f"{type(exc).__name__}: {exc}"[:160]


def start_payment(app, client, product_quantities):
    """Fill the signed-in customer's cart and start checkout. Returns the PaymentIntent id."""
    for product_id, quantity in product_quantities:
        resp = client.put(f"/api/cart/items/{product_id}", json={"quantity": quantity})
        assert resp.status_code == 200, resp.get_json()
    resp = client.post("/api/payments", json={"idempotencyKey": "key-" + uuid4().hex, "address": "150 S 1st St"})
    assert resp.status_code in (200, 201), resp.get_json()
    with app.app_context():
        return db.session.get(Payment, resp.get_json()["paymentId"]).stripe_payment_intent_id


def webhook(client, intent_id):
    return client.post("/api/payments/webhook", data=json.dumps({"id": intent_id}),
                       headers={"Stripe-Signature": "t", "Content-Type": "application/json"})
