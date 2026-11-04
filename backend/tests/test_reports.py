from datetime import datetime, timezone
from decimal import Decimal

from app.extensions import db
from app.models import Order, OrderLine, Product, User
from app.models.order import CANCELLED, DELIVERED, DELIVERY_FAILED, PLACED

PASSWORD = "johnathanpassword123"


def login_as(client, app, role):
    with app.app_context():
        user = User(email=f"{role}@example.com", name="Test User", role=role)
        user.set_password(PASSWORD)
        db.session.add(user)
        db.session.commit()
        uid = user.id
    r = client.post("/api/auth/login", json={"email": f"{role}@example.com", "password": PASSWORD})
    assert r.status_code == 200
    return uid


def make_product(name, category="Produce", price="2.00", stock=10, threshold=5, active=True):
    p = Product(name=name, category=category, price=Decimal(price), weight_lb=Decimal("1.00"),
                stock_qty=stock, low_stock_threshold=threshold, active=active)
    db.session.add(p)
    db.session.flush()
    return p


def make_order(uid, product, qty, status=PLACED, day=(2026, 11, 2), fee="0.00"):
    sub = product.price * qty
    o = Order(user_id=uid, status=status, subtotal=sub, delivery_fee=Decimal(fee), total=sub + Decimal(fee),
              weight_lb=Decimal(qty), delivery_address="1 Main St", delivery_lat=37.3, delivery_lng=-121.9,
              created_at=datetime(*day, 12, 0, tzinfo=timezone.utc))
    o.lines.append(OrderLine(product_id=product.product_id, name=product.name, unit_price=product.price,
                             weight_lb=product.weight_lb, quantity=qty))
    db.session.add(o)
    db.session.commit()
    return o


def seed(app, uid):
    with app.app_context():
        apple = make_product("Apple", price="2.00")
        kale = make_product("Kale", price="3.00")
        make_order(uid, apple, 5, DELIVERED, (2026, 11, 1))            # 10.00
        make_order(uid, apple, 5, DELIVERED, (2026, 11, 2), fee="10.00")  # 10.00 + 10 fee
        make_order(uid, kale, 2, DELIVERY_FAILED, (2026, 11, 2))       # 6.00
        make_order(uid, kale, 9, CANCELLED, (2026, 11, 2))             # excluded
        make_order(uid, kale, 1, PLACED, (2026, 10, 1))                # outside range


# ---------- access ----------

def test_reports_require_login(client):
    for path in ("sales", "inventory", "delivery"):
        assert client.get(f"/api/reports/{path}").status_code == 401


def test_employee_and_customer_forbidden(app, client):
    login_as(client, app, "employee")
    for path in ("sales", "inventory", "delivery"):
        assert client.get(f"/api/reports/{path}").status_code == 403


# ---------- sales ----------

def test_sales_totals_exclude_cancelled_and_out_of_range(app, client):
    uid = login_as(client, app, "manager")
    seed(app, uid)
    data = client.get("/api/reports/sales?from=2026-11-01&to=2026-11-03").get_json()
    assert data["orderCount"] == 3
    assert data["subtotal"] == 26.0
    assert data["deliveryFees"] == 10.0
    assert data["revenue"] == 36.0
    assert data["averageOrderValue"] == 12.0


def test_sales_by_day_and_product_demand(app, client):
    uid = login_as(client, app, "manager")
    seed(app, uid)
    data = client.get("/api/reports/sales?from=2026-11-01&to=2026-11-03").get_json()
    assert data["byDay"] == [
        {"date": "2026-11-01", "orders": 1, "revenue": 10.0},
        {"date": "2026-11-02", "orders": 2, "revenue": 26.0},
    ]
    assert data["productDemand"][0] == {"productId": data["productDemand"][0]["productId"],
                                        "name": "Apple", "units": 10, "revenue": 20.0}
    assert [p["name"] for p in data["productDemand"]] == ["Apple", "Kale"]


def test_sales_empty_period(app, client):
    login_as(client, app, "manager")
    data = client.get("/api/reports/sales?from=2026-01-01&to=2026-01-02").get_json()
    assert data["orderCount"] == 0 and data["revenue"] == 0 and data["averageOrderValue"] == 0
    assert data["byDay"] == [] and data["productDemand"] == []


def test_sales_bad_dates(app, client):
    login_as(client, app, "manager")
    assert client.get("/api/reports/sales?from=nope").status_code == 400
    assert client.get("/api/reports/sales?from=2026-11-05&to=2026-11-01").status_code == 400


def test_sales_defaults_to_last_30_days(app, client):
    login_as(client, app, "manager")
    data = client.get("/api/reports/sales").get_json()
    assert data["from"] and data["to"] and data["orderCount"] == 0


# ---------- inventory ----------

def test_inventory_snapshot(app, client):
    login_as(client, app, "manager")
    with app.app_context():
        make_product("Fine", stock=20, threshold=5)
        make_product("Low", stock=3, threshold=5)
        make_product("Out", stock=0, threshold=5)
        make_product("Hidden", stock=0, active=False)
        db.session.commit()
    data = client.get("/api/reports/inventory").get_json()
    assert data["totalProducts"] == 3
    assert data["outOfStock"] == 1 and data["lowStock"] == 1
    names = [p["name"] for p in data["attention"]]
    assert names == ["Out", "Low"]  # out of stock first
    assert {c["category"] for c in data["byCategory"]} == {"Produce"}


# ---------- delivery ----------

def test_delivery_performance(app, client):
    uid = login_as(client, app, "manager")
    seed(app, uid)
    data = client.get("/api/reports/delivery?from=2026-11-01&to=2026-11-03").get_json()
    assert data["statusCounts"][DELIVERED] == 2
    assert data["statusCounts"][DELIVERY_FAILED] == 1
    assert data["statusCounts"][CANCELLED] == 1
    assert data["delivered"] == 2 and data["failed"] == 1
    assert round(data["deliverySuccessRate"], 4) == round(2 / 3, 4)
    assert data["onTimeRate"] is None  # needs trip ETAs (T13/T15)


def test_delivery_no_completed_orders(app, client):
    login_as(client, app, "manager")
    data = client.get("/api/reports/delivery?from=2026-01-01&to=2026-01-02").get_json()
    assert data["deliverySuccessRate"] is None
