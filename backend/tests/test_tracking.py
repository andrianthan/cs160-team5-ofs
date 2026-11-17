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
    assert response.status_code == 404
    assert response.get_json()["error"] == "order_not_found"


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

    assert response.status_code == 404
    assert response.get_json()["error"] == "order_not_found"


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

    assert response.status_code == 404
    assert response.get_json()["error"] == "order_not_found"


def test_tracking_nonexistent_order(client):
    register_response = client.post(
        "/api/auth/register",
        json={
            "email": "missingorder@example.com",
            "name": "Missing Order Tester",
            "password": "johnathanpassword123",
        },
    )

    assert register_response.status_code == 201

    response = client.get("/api/tracking/999999")

    assert response.status_code == 404
    assert response.get_json()["error"] == "order_not_found"


from decimal import Decimal

from app.models import Order, OrderLine, Product, Trip
from app.models.robot import Robot


def create_tracking_order(user_id, trip_id=None):
    product = Product(
        name="Tracking Apple",
        category="Fruit",
        price=Decimal("1.50"),
        weight_lb=Decimal("0.50"),
        stock_qty=10,
    )
    db.session.add(product)
    db.session.flush()

    order = Order(
        user_id=user_id,
        status="placed" if trip_id is None else "planned",
        subtotal=Decimal("3.00"),
        delivery_fee=Decimal("0.00"),
        total=Decimal("3.00"),
        weight_lb=Decimal("1.00"),
        delivery_address="1 Main St",
        delivery_lat=37.33,
        delivery_lng=-121.89,
        trip_id=trip_id,
    )

    order.lines.append(OrderLine(
        product_id=product.product_id,
        name="Tracking Apple",
        unit_price=Decimal("1.50"),
        weight_lb=Decimal("0.50"),
        quantity=2,
    ))

    db.session.add(order)
    db.session.commit()
    return order.id


def create_tracking_user(email, role="customer"):
    user = User(
        email=email,
        name=email.split("@")[0],
        role=role,
    )
    user.set_password("password123")
    db.session.add(user)
    db.session.commit()
    return user.id


def login_tracking_user(client, email):
    client.post("/api/auth/logout")
    response = client.post(
        "/api/auth/login",
        json={"email": email, "password": "password123"},
    )
    assert response.status_code == 200


def test_customer_tracks_own_order(app, client):
    with app.app_context():
        user_id = create_tracking_user("owner@example.com")
        order_id = create_tracking_order(user_id)

    login_tracking_user(client, "owner@example.com")

    response = client.get(f"/api/tracking/{order_id}")

    assert response.status_code == 200
    data = response.get_json()
    assert data["orderId"] == order_id
    assert data["status"] == "placed"
    assert data["trip"] is None
    assert data["robot"] is None


def test_customer_cannot_track_another_order(app, client):
    with app.app_context():
        create_tracking_user("alice-track@example.com")
        bob_id = create_tracking_user("bob-track@example.com")
        order_id = create_tracking_order(bob_id)

    login_tracking_user(client, "alice-track@example.com")

    response = client.get(f"/api/tracking/{order_id}")

    assert response.status_code == 403
    assert response.get_json()["error"] == "forbidden"


def test_employee_tracks_customer_order(app, client):
    with app.app_context():
        customer_id = create_tracking_user("buyer@example.com")
        create_tracking_user("staff-track@example.com", "employee")
        order_id = create_tracking_order(customer_id)

    login_tracking_user(client, "staff-track@example.com")

    response = client.get(f"/api/tracking/{order_id}")

    assert response.status_code == 200
    assert response.get_json()["orderId"] == order_id


def test_tracking_with_trip_and_robot(app, client):
    with app.app_context():
        user_id = create_tracking_user("robotbuyer@example.com")

        robot = Robot(
            robot_code="T16-ROBOT-1",
            status="out_for_delivery",
            current_latitude=Decimal("37.335000"),
            current_longitude=Decimal("-121.890000"),
        )
        db.session.add(robot)
        db.session.flush()

        trip = Trip(
            status="dispatched",
            robot_id=robot.id,
            estimated_duration_minutes=15,
        )
        db.session.add(trip)
        db.session.flush()

        order_id = create_tracking_order(user_id, trip.id)

    login_tracking_user(client, "robotbuyer@example.com")

    response = client.get(f"/api/tracking/{order_id}")

    assert response.status_code == 200

    data = response.get_json()
    assert data["trip"]["status"] == "dispatched"
    assert data["robot"]["robotCode"] == "T16-ROBOT-1"
    assert data["robot"]["latitude"] == 37.335
    assert data["robot"]["longitude"] == -121.89


def test_tracking_robot_without_gps(app, client):
    with app.app_context():
        user_id = create_tracking_user("nogps@example.com")

        robot = Robot(robot_code="T16-NO-GPS")
        db.session.add(robot)
        db.session.flush()

        trip = Trip(status="ready", robot_id=robot.id)
        db.session.add(trip)
        db.session.flush()

        order_id = create_tracking_order(user_id, trip.id)

    login_tracking_user(client, "nogps@example.com")

    response = client.get(f"/api/tracking/{order_id}")

    assert response.status_code == 200
    assert response.get_json()["robot"]["latitude"] is None
    assert response.get_json()["robot"]["longitude"] is None
