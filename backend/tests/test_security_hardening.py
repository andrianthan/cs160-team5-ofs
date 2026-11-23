"""Black-box hardening found while preparing for another team's testing (Part IV).

Each test is a thing a tester can try from outside: forge a session, hammer the login, send an oversized
password, ask for a URL that doesn't exist, call the API from another website.
"""
from flask.sessions import SecureCookieSessionInterface

from app.blueprints import auth
from app.config import _PUBLIC_DEFAULT_SECRET

from tests.test_auth import PASSWORD, login, make_user, register


def test_the_public_default_secret_is_not_the_signing_key(app):
    assert app.config["SECRET_KEY"] != _PUBLIC_DEFAULT_SECRET
    assert len(app.config["SECRET_KEY"]) >= 32


def test_a_session_cookie_signed_with_the_published_default_is_rejected(app, client):
    manager = make_user("boss@example.com", "manager")
    from flask import Flask
    other = Flask("forger")
    other.secret_key = _PUBLIC_DEFAULT_SECRET
    cookie = SecureCookieSessionInterface().get_signing_serializer(other).dumps({"_user_id": str(manager.id), "_fresh": True})
    client.set_cookie("session", cookie)
    assert client.get("/api/auth/me").status_code == 401
    assert client.get("/api/reports/sales").status_code == 401


def test_session_cookie_is_httponly_and_samesite(client):
    make_user("a@example.com", "customer")
    cookie = login(client, "a@example.com").headers["Set-Cookie"]
    assert "HttpOnly" in cookie
    assert "SameSite=Lax" in cookie


def test_login_locks_after_repeated_failures_then_recovers(app, client):
    make_user("a@example.com", "customer")
    app.config["LOGIN_MAX_FAILURES"] = 3
    for _ in range(3):
        assert login(client, "a@example.com", "wrong-password").status_code == 401
    locked = login(client, "a@example.com", PASSWORD)  # even the right password waits out the lockout
    assert locked.status_code == 429
    assert locked.get_json()["error"] == "too_many_attempts"
    assert int(locked.headers["Retry-After"]) > 0
    auth._failures.clear()  # the window passing
    assert login(client, "a@example.com", PASSWORD).status_code == 200


def test_lockout_is_per_account(app, client):
    make_user("a@example.com", "customer")
    make_user("b@example.com", "customer")
    app.config["LOGIN_MAX_FAILURES"] = 2
    for _ in range(2):
        login(client, "a@example.com", "wrong-password")
    assert login(client, "a@example.com", PASSWORD).status_code == 429
    assert login(client, "b@example.com", PASSWORD).status_code == 200


def test_a_good_login_resets_the_failure_count(app, client):
    make_user("a@example.com", "customer")
    app.config["LOGIN_MAX_FAILURES"] = 3
    for _ in range(2):
        login(client, "a@example.com", "wrong-password")
    assert login(client, "a@example.com", PASSWORD).status_code == 200
    for _ in range(2):
        assert login(client, "a@example.com", "wrong-password").status_code == 401


def test_oversized_password_is_rejected_at_register_and_login(client):
    assert register(client, password="a" * 129).status_code == 400
    assert register(client, password="a" * 100_000).status_code == 400
    make_user("a@example.com", "customer")
    assert login(client, "a@example.com", "a" * 100_000).status_code == 401


def test_unknown_api_paths_answer_json_not_html(client):
    for method, path, status in (("get", "/api/nope", 404), ("post", "/api/health", 405), ("get", "/api/orders/abc", 404)):
        resp = getattr(client, method)(path)
        assert resp.status_code == status
        assert resp.is_json, path
        assert "<html" not in resp.get_data(as_text=True).lower()


def test_cors_only_allows_the_configured_origins(client):
    ok = client.get("/api/health", headers={"Origin": "http://localhost:5173"})
    assert ok.headers.get("Access-Control-Allow-Origin") == "http://localhost:5173"
    evil = client.get("/api/health", headers={"Origin": "https://evil.example"})
    assert "Access-Control-Allow-Origin" not in evil.headers


def test_unexpected_errors_do_not_leak_internals(app, client):
    @app.get("/api/boom")
    def boom():
        raise RuntimeError("secret database detail")

    app.config["PROPAGATE_EXCEPTIONS"] = False
    resp = client.get("/api/boom")
    assert resp.status_code == 500
    assert "secret database detail" not in resp.get_data(as_text=True)
    assert "Traceback" not in resp.get_data(as_text=True)
