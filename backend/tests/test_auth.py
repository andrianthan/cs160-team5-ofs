import pytest

from app.blueprints.auth import require_role
from app.extensions import db
from app.models import User

PASSWORD = "johnathanpassword123"

def make_user(email, role, name="John Tester"):
    user = User(email=email, name=name, role=role)
    user.set_password(PASSWORD)
    db.session.add(user)
    db.session.commit()
    return user

def register(client, **overrides):
    body = {"email": "test@email.com", "name": "New Customer", "password": PASSWORD, **overrides}

    return client.post("/api/auth/register", json=body)

def login(client, email, password=PASSWORD, **extra):
    body = {"email": email, "password": password, **extra}
    return client.post("/api/auth/login", json=body)




def test_register_and_sign_in(client):
    resp = register(client)

    assert resp.status_code == 201
    assert resp.get_json()["role"] == "customer"
    assert "password" not in str(resp.get_json())
    assert client.get("/api/auth/me").get_json()["email"] == "test@email.com"

def test_password_is_stored_as_a_hash(app, client):
    register(client)

    with app.app_context():
        user = User.query.filter_by(email="test@email.com").first()

        assert user is not None
        assert user.password_hash != PASSWORD
        assert user.check_password(PASSWORD)

def test_duplicate_email_is_rejected(client):
    first = register(client)
    second = register(client, name="Another Person")

    assert first.status_code == 201
    assert second.status_code == 409
    assert second.get_json()["error"] == "email_taken"

def test_duplicate_email_is_case_insensitive(client):
    first = register(client, email="TEST@EMAIL.COM")
    second = register(client, email="test@email.com")

    assert first.status_code == 201
    assert second.status_code == 409

def test_current_user_requires_login(client):
    response = client.get("/api/auth/me")

    assert response.status_code == 401
    assert response.get_json()["error"] == "unauthorized"