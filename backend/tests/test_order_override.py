from decimal import Decimal

from app.extensions import db
from app.models import Order, OrderOverrideAudit, User
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

    # Create a customer and an order.
    with app.app_context():
        customer = User(
            email="ordercustomer@example.com",
            name="Order Customer",
            role="customer"
        )
        customer.set_password(PASSWORD)
        db.session.add(customer)
        db.session.flush()

        order = Order(
            user_id=customer.id,
            status="placed",
            subtotal=Decimal("10.00"),
            delivery_fee=Decimal("2.00"),
            total=Decimal("12.00"),
            weight_lb=Decimal("2.00"),
            delivery_address="1 Main St",
            delivery_lat=37.33,
            delivery_lng=-121.89
        )

        db.session.add(order)
        db.session.commit()
        order_id = order.id

    # Manager requests cancellation.
    response = client.post(
        f"/api/orders/{order_id}/override",
        json={
            "action": "cancel",
            "reason": "Customer requested cancellation",
            "confirmed": True
        }
    )

    # Verify the API response.
    assert response.status_code == 200
    body = response.get_json()
    assert body["status"] == "cancelled"
    assert body["action"] == "cancel"
    assert body["reason"] == "Customer requested cancellation"


    # Verify the order was cancelled and audit record saved.
    with app.app_context():
        updated_order = db.session.get(Order, order_id)
        assert updated_order.status == "cancelled"

        audits = OrderOverrideAudit.query.filter_by(
            order_id=order_id
        ).all()

        assert len(audits) == 1

        audit = audits[0]
        assert audit.action == "cancel"
        assert audit.previous_status == "placed"
        assert audit.new_status == "cancelled"
        assert audit.reason == "Customer requested cancellation"
        assert audit.manager_id is not None
        assert audit.created_at is not None



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
