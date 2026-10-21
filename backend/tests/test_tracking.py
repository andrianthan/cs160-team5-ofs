def test_tracking_requires_login(client):
    response = client.get("/api/tracking/1")

    assert response.status_code == 401
    assert response.get_json() == {
        "error": "unauthorized"
    }


def test_tracking_requires_login_for_any_order(client):
    response = client.get("/api/tracking/999")

    assert response.status_code == 401
    assert response.get_json()["error"] == "unauthorized"


def test_tracking_logged_in_customer(client):
    # Step 1: Register a customer.
    register_response = client.post(
        "/api/auth/register",
        json={
            "email": "tracking@example.com",
            "name": "Tracking Tester",
            "password": "johnathanpassword123"
        }
    )

    assert register_response.status_code == 201

    # Step 2: Registration automatically logs in the customer.
    # Step 3: Request tracking information for order 1.
    response = client.get("/api/tracking/1")

    # Step 4: Tracking is not implemented yet.
    assert response.status_code == 501
    assert response.get_json()["error"] == "tracking_not_available"


from app.extensions import db
from app.models import User


def test_tracking_logged_in_employee(app, client):
    with app.app_context():
        employee = User(
            email="employee@example.com",
            name="Test Employee",
            role="employee"
        )
        employee.set_password("johnathanpassword123")
        db.session.add(employee)
        db.session.commit()

    # Log in as employee.
    login_response = client.post(
        "/api/auth/login",
        json={
            "email": "employee@example.com",
            "password": "johnathanpassword123"
        }
    )

    assert login_response.status_code == 200

    # Request tracking information.
    response = client.get("/api/tracking/1")

    assert response.status_code == 501
    assert response.get_json()["error"] == "tracking_not_available"


def test_tracking_logged_in_manager(app, client):
    with app.app_context():
        manager = User(
            email="manager@example.com",
            name="Test Manager",
            role="manager"
        )
        manager.set_password("johnathanpassword123")
        db.session.add(manager)
        db.session.commit()

    # Log in as manager.
    login_response = client.post(
        "/api/auth/login",
        json={
            "email": "manager@example.com",
            "password": "johnathanpassword123"
        }
    )

    assert login_response.status_code == 200

    # Request tracking information.
    response = client.get("/api/tracking/1")

    assert response.status_code == 501
    assert response.get_json()["error"] == "tracking_not_available"
