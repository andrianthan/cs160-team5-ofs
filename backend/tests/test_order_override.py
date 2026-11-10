
from app.extensions import db
from app.models import User

PASSWORD = "johnathanpassword123"


def login_as(client, app, role):
    with app.app_context():
        user = User(
            email=f"{role}@example.com",
            name="Test User",
            role=role
        )
        user.set_password(PASSWORD)
        db.session.add(user)
        db.session.commit()

    response = client.post(
        "/api/auth/login",
        json={
            "email": f"{role}@example.com",
            "password": PASSWORD
        }
    )

    assert response.status_code == 200


def test_override_requires_login(client):
    response = client.post("/api/orders/1/override")

    assert response.status_code == 401
    assert response.get_json()["error"] == "unauthorized"


def test_customer_cannot_override(app, client):
    login_as(client, app, "customer")

    response = client.post("/api/orders/1/override")

    assert response.status_code == 403
    assert response.get_json()["error"] == "forbidden"


def test_employee_cannot_override(app, client):
    login_as(client, app, "employee")

    response = client.post("/api/orders/1/override")

    assert response.status_code == 403
    assert response.get_json()["error"] == "forbidden"



def test_manager_can_access_override(app, client):
    login_as(client, app, "manager")

    response = client.post(
        "/api/orders/1/override",
        json={
            "action": "cancel",
            "reason": "Customer requested cancellation",
            "confirmed": True
        }
    )

    assert response.status_code == 501
    assert response.get_json()["error"] == "not_implemented"


def test_override_missing_action(app, client):
    login_as(client, app, "manager")

    response = client.post(
        "/api/orders/1/override",
        json={
            "reason": "Customer requested cancellation",
            "confirmed": True
        }
    )

    assert response.status_code == 400
    assert response.get_json()["error"] == "INVALID_OVERRIDE"


def test_override_missing_reason(app, client):
    login_as(client, app, "manager")

    response = client.post(
        "/api/orders/1/override",
        json={
            "action": "cancel",
            "confirmed": True
        }
    )

    assert response.status_code == 400
    assert response.get_json()["error"] == "INVALID_OVERRIDE"


def test_override_missing_confirmation(app, client):
    login_as(client, app, "manager")

    response = client.post(
        "/api/orders/1/override",
        json={
            "action": "cancel",
            "reason": "Customer requested cancellation"
        }
    )

    assert response.status_code == 400
    assert response.get_json()["error"] == "INVALID_OVERRIDE"


def test_override_empty_json(app, client):
    login_as(client, app, "manager")

    response = client.post(
        "/api/orders/1/override",
        json={}
    )

    assert response.status_code == 400
    assert response.get_json()["error"] == "INVALID_OVERRIDE"


def test_override_blank_reason(app, client):
    login_as(client, app, "manager")

    response = client.post(
        "/api/orders/1/override",
        json={
            "action": "cancel",
            "reason": "   ",
            "confirmed": True
        }
    )

    assert response.status_code == 400
    assert response.get_json()["error"] == "INVALID_OVERRIDE"


def test_override_invalid_action_type(app, client):
    login_as(client, app, "manager")

    response = client.post(
        "/api/orders/1/override",
        json={
            "action": 123,
            "reason": "Customer requested cancellation",
            "confirmed": True
        }
    )

    assert response.status_code == 400
    assert response.get_json()["error"] == "INVALID_OVERRIDE"


def test_override_confirmation_must_be_true(app, client):
    login_as(client, app, "manager")

    response = client.post(
        "/api/orders/1/override",
        json={
            "action": "cancel",
            "reason": "Customer requested cancellation",
            "confirmed": False
        }
    )

    assert response.status_code == 400
    assert response.get_json()["error"] == "INVALID_OVERRIDE"
