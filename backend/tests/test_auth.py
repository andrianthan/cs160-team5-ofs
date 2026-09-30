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
