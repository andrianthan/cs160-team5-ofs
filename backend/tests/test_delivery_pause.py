from app.extensions import db
from app.models import User
from app.models.delivery_settings import DeliverySettings

PASSWORD = "testpassword123"


def login_as(client, app, role):
    with app.app_context():
        user = User(
            email=f"pause-{role}@example.com",
            name="Test User",
            role=role
        )
        user.set_password(PASSWORD)
        db.session.add(user)
        db.session.commit()

    response = client.post(
        "/api/auth/login",
        json={
            "email": f"pause-{role}@example.com",
            "password": PASSWORD
        }
    )
    assert response.status_code == 200


def test_delivery_pause_defaults_to_false(client):
    response = client.get("/api/settings/delivery-pause")

    assert response.status_code == 200
    assert response.get_json()["paused"] is False


def test_delivery_pause_requires_login(client):
    response = client.put(
        "/api/settings/delivery-pause",
        json={"paused": True}
    )

    assert response.status_code == 401


def test_customer_cannot_pause(app, client):
    login_as(client, app, "customer")

    response = client.put(
        "/api/settings/delivery-pause",
        json={"paused": True}
    )

    assert response.status_code == 403


def test_employee_cannot_pause(app, client):
    login_as(client, app, "employee")

    response = client.put(
        "/api/settings/delivery-pause",
        json={"paused": True}
    )

    assert response.status_code == 403


def test_manager_can_pause_and_resume(app, client):
    login_as(client, app, "manager")

    response = client.put(
        "/api/settings/delivery-pause",
        json={"paused": True}
    )

    assert response.status_code == 200
    assert response.get_json()["paused"] is True

    # Verify that pause state is saved in the database.
    with app.app_context():
        settings = db.session.get(DeliverySettings, 1)
        assert settings is not None
        assert settings.paused is True
        assert settings.updated_by is not None

    response = client.get("/api/settings/delivery-pause")
    assert response.status_code == 200
    assert response.get_json()["paused"] is True

    # Resume deliveries.
    response = client.put(
        "/api/settings/delivery-pause",
        json={"paused": False}
    )

    assert response.status_code == 200
    assert response.get_json()["paused"] is False

    with app.app_context():
        settings = db.session.get(DeliverySettings, 1)
        assert settings.paused is False


def test_delivery_pause_rejects_invalid_data(app, client):
    login_as(client, app, "manager")

    invalid_bodies = [
        {},
        {"paused": "true"},
        {"paused": 1},
        {"paused": None},
        {"paused": []}
    ]

    for body in invalid_bodies:
        response = client.put(
            "/api/settings/delivery-pause",
            json=body
        )

        assert response.status_code == 400
        assert response.get_json()["error"] == "INVALID_DELIVERY_PAUSE"


def test_checkout_blocked_when_deliveries_paused(app, client):
    login_as(client, app, "manager")

    # Manager pauses deliveries.
    response = client.put(
        "/api/settings/delivery-pause",
        json={"paused": True}
    )
    assert response.status_code == 200

    # Log out the manager.
    client.post("/api/auth/logout")

    # Log in as a customer.
    login_as(client, app, "customer")

    # Attempt to start a payment.
    response = client.post(
        "/api/payments",
        json={
            "idempotencyKey": "pause-checkout-test-123",
            "address": "1 Washington Sq, San Jose, CA"
        }
    )

    assert response.status_code == 503
    assert response.get_json()["error"] == "delivery_paused"
