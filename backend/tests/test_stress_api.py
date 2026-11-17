"""Stress tests across the whole API: who can call what, junk input, and sign-in abuse.

Owner: Karnani Shresthkumar (T04 auth and roles, T05 catalog, T12 orders). Runs on SQLite, and on
PostgreSQL too when TEST_POSTGRES_URL is set (CI sets it), because PostgreSQL enforces column
lengths and types that SQLite silently accepts.
"""
from decimal import Decimal

import pytest

from app.extensions import db
from app.models import Order, OrderLine, Trip, User
from stress_support import DATABASES, PASSWORD, FakeStripe, call, make_product, make_user, signed_in, stress_app

PUBLIC, SIGNED_IN, STAFF, MANAGER = "public", "signed in", "staff", "manager"

# Every route and the least access it needs. test_every_route_is_listed fails when a route is
# added or removed without updating this table, so a new endpoint can't skip the sweep.
ROUTES = {
    ("POST", "/api/addresses/validate"): PUBLIC,
    ("POST", "/api/auth/login"): PUBLIC,
    ("POST", "/api/auth/logout"): PUBLIC,
    ("GET", "/api/auth/me"): SIGNED_IN,
    ("POST", "/api/auth/register"): PUBLIC,
    ("GET", "/api/cart"): SIGNED_IN,
    ("DELETE", "/api/cart"): SIGNED_IN,
    ("PUT", "/api/cart/items/<product_id>"): SIGNED_IN,
    ("GET", "/api/health"): PUBLIC,
    ("GET", "/api/orders"): SIGNED_IN,
    ("GET", "/api/orders/<int:order_id>"): SIGNED_IN,
    ("POST", "/api/orders/<int:order_id>/prepare"): STAFF,
    ("PATCH", "/api/orders/<int:order_id>/status"): STAFF,
    ("POST", "/api/orders/<int:order_id>/override"): MANAGER,
    ("POST", "/api/payments"): SIGNED_IN,
    ("GET", "/api/payments/<int:payment_id>"): SIGNED_IN,
    ("POST", "/api/payments/<int:payment_id>/cancel"): SIGNED_IN,
    ("POST", "/api/payments/webhook"): PUBLIC,  # protected by the Stripe signature instead
    ("GET", "/api/products"): PUBLIC,
    ("POST", "/api/products"): MANAGER,
    ("GET", "/api/products/all"): STAFF,
    ("PATCH", "/api/products/<int:product_id>"): MANAGER,
    ("DELETE", "/api/products/<int:product_id>"): MANAGER,
    ("GET", "/api/products/<int:product_id>/inventory-log"): MANAGER,
    ("GET", "/api/reports/delivery"): MANAGER,
    ("GET", "/api/reports/inventory"): MANAGER,
    ("GET", "/api/reports/sales"): MANAGER,
    ("GET", "/api/settings/delivery-pause"): PUBLIC,
    ("PUT", "/api/settings/delivery-pause"): MANAGER,
    ("GET", "/api/tracking/<int:order_id>"): SIGNED_IN,  # customers (own orders) and staff
    ("GET", "/api/robots"): STAFF,
    ("GET", "/api/trips"): STAFF,
    ("POST", "/api/trips/<int:trip_id>/dispatch"): STAFF,
}
# Logout would sign the sweeps' own clients out, so it gets its own test instead.
SWEPT = {route: access for route, access in ROUTES.items() if route != ("POST", "/api/auth/logout")}
ALLOWED = {
    PUBLIC: {None, "customer", "employee", "manager"},
    SIGNED_IN: {"customer", "employee", "manager"},
    STAFF: {"employee", "manager"},
    MANAGER: {"manager"},
}
ROLES = (None, "customer", "employee", "manager")  # None = not signed in


def _path(rule, value="1"):
    out = rule
    while "<" in out:
        start = out.index("<")
        out = out[:start] + value + out[out.index(">", start) + 1:]
    return out


@pytest.fixture(params=DATABASES)
def world(request, monkeypatch):
    """An app with one of everything (ids are all 1), and a signed-in client per role."""
    with stress_app(request.param) as app:
        FakeStripe(monkeypatch)
        ids = {role: make_user(app, f"{role}@example.com", role) for role in ("customer", "employee", "manager")}
        product_id = make_product(app, stock=50)
        with app.app_context():
            order = Order(user_id=ids["customer"], subtotal=Decimal("3.00"), delivery_fee=Decimal("0"),
                          total=Decimal("3.00"), weight_lb=Decimal("1.00"), delivery_address="1 Main St",
                          delivery_lat=37.33, delivery_lng=-121.89)
            order.lines.append(OrderLine(product_id=product_id, name="Apple", unit_price=Decimal("1.50"),
                                         weight_lb=Decimal("0.50"), quantity=2))
            db.session.add_all([order, Trip()])
            db.session.commit()
        clients = {None: app.test_client()}
        clients.update({role: signed_in(app, f"{role}@example.com") for role in ids})
        yield app, clients, request.param


# ============ Access control sweep ============

def test_every_route_is_listed(world):
    app, _, _ = world
    registered = {
        (method, rule.rule)
        for rule in app.url_map.iter_rules() if rule.endpoint != "static"
        for method in rule.methods - {"HEAD", "OPTIONS"}
    }
    assert registered - set(ROUTES) == set(), "new route: add it to ROUTES with the access it needs"
    assert set(ROUTES) - registered == set(), "route removed: drop it from ROUTES"


def test_access_control_on_every_route(world):
    _, clients, _ = world
    wrong = []
    for (method, rule), access in SWEPT.items():
        for role in ROLES:
            status, detail = call(clients[role], method, _path(rule))
            who = role or "anonymous"
            if role not in ALLOWED[access]:
                expected = 401 if role is None else 403
                if status != expected:
                    wrong.append(f"{who} {method} {rule}: {status}, expected {expected} {detail or ''}")
            elif status >= 500 or (access in (STAFF, MANAGER) and status in (401, 403)):
                wrong.append(f"{who} {method} {rule}: {status}, but this role is allowed {detail or ''}")
    assert wrong == [], "\n".join(wrong)


def test_role_cannot_be_chosen_at_registration(world):
    app, _, _ = world
    client = app.test_client()
    resp = client.post("/api/auth/register", json={"email": "sneaky@example.com", "name": "Sneaky",
                                                   "password": PASSWORD, "role": "manager"})
    assert resp.status_code == 201 and resp.get_json()["role"] == "customer"
    assert client.get("/api/reports/sales").status_code == 403


# ============ Junk input on every route: nothing may crash (5xx) ============

WEIRD_VALUES = [None, True, 0, -1, 2**63, 1e308, "", " ", "x" * 5000, "\u0000", "🍎" * 300, [], [1, "a"], {},
                {"a": {"b": [None]}}]
BODY_KEYS = ["email", "password", "name", "portal", "quantity", "address", "idempotencyKey", "status", "action",
             "reason", "confirmed", "paused", "stock_qty", "stock_reason", "stock_note", "price", "weight_lb",
             "category", "description", "image_url", "low_stock_threshold", "active"]
RAW_BODIES = [b"", b"not json", b"[]", b"null", b'"text"', b"123", b'{"price": NaN, "stock_qty": Infinity}',
              b'{"quantity": 1e400}', b"\xff\xfe"]
ODD_IDS = ["abc", "-1", "0", "1.5", "%20", "1%00", "99999999999999999999"]
# A body most write routes accept as far as their id lookup, so the odd id actually reaches the database.
VALID_LOOKING = {"action": "cancel", "reason": "stress test", "confirmed": True, "quantity": 1, "status": "placed"}
ODD_QUERIES = [{"status": "x"}, {"from": "nope", "to": "2026-99-99"}, {"from": "2026-12-31", "to": "2026-01-01"},
               {"from": "0001-01-01", "to": "9999-12-31"}, {"status": "x" * 3000}]


def test_junk_bodies_never_crash_any_route(world):
    _, clients, db_kind = world
    crashes = set()
    bodies = [{"raw": raw} for raw in RAW_BODIES] + [
        {"body": {key: value for key in BODY_KEYS}} for value in WEIRD_VALUES]
    for (method, rule), _ in SWEPT.items():
        if method == "GET":
            continue
        for role in (None, "customer", "manager"):
            for b in bodies:
                status, detail = call(clients[role], method, _path(rule), b.get("body"), b.get("raw"))
                if status >= 500:
                    crashes.add(f"[{db_kind}] {method} {rule} body={str(b)[:40]}: {detail}")
    assert sorted(crashes) == [], "\n".join(sorted(crashes)[:30])


def test_odd_ids_and_queries_never_crash_any_route(world):
    _, clients, db_kind = world
    crashes = set()
    for (method, rule), _ in SWEPT.items():
        for role in ("customer", "manager"):
            if "<" in rule:
                for odd in ODD_IDS:
                    if db_kind == "sqlite" and len(odd) > 18:
                        continue  # SQLite can't even compare a 20-digit integer; PostgreSQL covers it
                    status, detail = call(clients[role], method, _path(rule, odd), body=VALID_LOOKING)
                    if status >= 500:
                        crashes.add(f"[{db_kind}] {method} {_path(rule, odd)}: {detail}")
            if method == "GET":
                for query in ODD_QUERIES:
                    status, detail = call(clients[role], method, _path(rule), query=query)
                    if status >= 500:
                        crashes.add(f"[{db_kind}] GET {rule}?{str(query)[:40]}: {detail}")
    assert sorted(crashes) == [], "\n".join(sorted(crashes)[:30])


# ============ Sign-in abuse (T04) ============

@pytest.mark.parametrize("name", ["x" * 120, "名" * 120, "x" * 121, "x" * 5000])
def test_long_names_are_rejected_cleanly_or_saved_whole(world, name):
    app, _, _ = world
    status, detail = call(app.test_client(), "POST", "/api/auth/register",
                          {"email": "long@example.com", "name": name, "password": PASSWORD})
    with app.app_context():
        saved = User.query.filter_by(email="long@example.com").first()
        if len(name) <= 120:
            assert status == 201 and saved.name == name, detail
        else:
            assert status == 400 and saved is None, detail


def test_email_variants_are_one_account(world):
    app, _, _ = world
    client = app.test_client()
    assert client.post("/api/auth/register", json={"email": "  Mixed.Case@Example.COM ", "name": "M",
                                                   "password": PASSWORD}).status_code == 201
    for variant in ("mixed.case@example.com", "MIXED.CASE@EXAMPLE.COM", " Mixed.Case@example.com"):
        dup = app.test_client().post("/api/auth/register", json={"email": variant, "name": "M2",
                                                                 "password": PASSWORD})
        assert dup.status_code == 409, variant
        login = app.test_client().post("/api/auth/login", json={"email": variant, "password": PASSWORD})
        assert login.status_code == 200, variant
    with app.app_context():
        assert User.query.filter(User.email.ilike("mixed.case@example.com")).count() == 1


def test_many_failed_logins_then_the_right_password_still_works(world):
    app, _, _ = world
    client = app.test_client()
    for i in range(40):
        resp = client.post("/api/auth/login", json={"email": "customer@example.com", "password": f"wrong{i}"})
        assert resp.status_code == 401 and resp.get_json()["error"] == "invalid_credentials"
        assert client.get("/api/auth/me").status_code == 401
    ok = client.post("/api/auth/login", json={"email": "customer@example.com", "password": PASSWORD})
    assert ok.status_code == 200
    assert client.get("/api/auth/me").get_json()["email"] == "customer@example.com"


def test_unknown_email_and_wrong_password_look_the_same(world):
    app, _, _ = world
    unknown = app.test_client().post("/api/auth/login", json={"email": "nobody@example.com", "password": PASSWORD})
    wrong = app.test_client().post("/api/auth/login", json={"email": "customer@example.com", "password": "nope-nope"})
    assert (unknown.status_code, unknown.get_json()) == (wrong.status_code, wrong.get_json())


def test_logout_ends_the_session(world):
    app, _, _ = world
    client = signed_in(app, "manager@example.com")
    assert client.get("/api/reports/sales").status_code == 200
    assert client.post("/api/auth/logout").status_code == 200
    for path in ("/api/auth/me", "/api/reports/sales", "/api/products/all", "/api/cart"):
        assert client.get(path).status_code == 401, path


def test_passwords_are_never_stored_or_returned(world):
    app, _, _ = world
    resp = app.test_client().post("/api/auth/register", json={"email": "plain@example.com", "name": "P",
                                                              "password": "hunter2hunter2"})
    assert resp.status_code == 201
    assert "hunter2hunter2" not in resp.get_data(as_text=True) and "password" not in resp.get_json()
    with app.app_context():
        stored = User.query.filter_by(email="plain@example.com").one().password_hash
    assert "hunter2hunter2" not in stored and stored.count("$") >= 2


# ============ NUL characters: PostgreSQL refuses them in text, so they must be a 400, not a 500 ============

NUL_REQUESTS = [  # (role, method, path, body); everything else in the body is valid
    (None, "POST", "/api/auth/register", {"email": "nul@example.com", "name": "Bad\x00Name", "password": PASSWORD}),
    (None, "POST", "/api/auth/login", {"email": "customer@example.com\x00", "password": PASSWORD}),
    ("manager", "POST", "/api/products", {"name": "Ho\x00ney", "category": "Pantry", "price": 8.5, "weight_lb": 1}),
    ("manager", "POST", "/api/products", {"name": "Honey", "category": "Pan\x00try", "price": 8.5, "weight_lb": 1}),
    ("manager", "POST", "/api/products", {"name": "Honey", "category": "Pantry", "price": 8.5, "weight_lb": 1,
                                          "description": "sweet\x00"}),
    ("manager", "POST", "/api/products", {"name": "Honey", "category": "Pantry", "price": 8.5, "weight_lb": 1,
                                          "image_url": "https://x/\x00.png"}),
    ("manager", "PATCH", "/api/products/1", {"name": "Ap\x00ple"}),
    ("manager", "PATCH", "/api/products/1", {"stock_qty": 60, "stock_note": "box\x00 of 10"}),
    ("manager", "POST", "/api/orders/1/override", {"action": "cancel", "reason": "asked\x00", "confirmed": True}),
    ("customer", "POST", "/api/payments", {"idempotencyKey": "key-\x00-12345678", "address": "150 S 1st St"}),
]


@pytest.mark.parametrize("role, method, path, body", NUL_REQUESTS,
                         ids=[f"{m} {p} {sorted(b)[0]}" for _, m, p, b in NUL_REQUESTS])
def test_nul_characters_are_rejected_not_crashed(world, role, method, path, body):
    _, clients, db_kind = world
    if path == "/api/payments":
        clients[role].put("/api/cart/items/1", json={"quantity": 1})
    status, detail = call(clients[role], method, path, body)
    assert status in (400, 401), f"[{db_kind}] {status} {detail}"
