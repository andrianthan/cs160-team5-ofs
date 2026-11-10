"""Exercise T02 migrations, data preservation, constraints and order snapshots.

Optional TEST_POSTGRES_URL adds PostgreSQL runs in a fresh random schema.
It never drops or modifies existing schemas. SQLite runs are always included.
"""
import os
from pathlib import Path
from uuid import uuid4

import pytest
import sqlalchemy as sa
from flask_migrate import check, downgrade, upgrade
from sqlalchemy.exc import IntegrityError

from app import create_app
from app.config import TestConfig
from app.extensions import db
from app.models import Address, InventoryLog, Order, OrderLine, Payment, Product, Robot, Trip, TripStop, User

MIGRATIONS = str(Path(__file__).resolve().parents[1] / "migrations")
DATABASES = ["sqlite"] + (["postgresql"] if os.getenv("TEST_POSTGRES_URL") else [])
TABLES = {"users", "addresses", "products", "inventory_log", "carts", "cart_lines", "orders",
          "order_lines", "payments", "robots", "trips", "trip_stops", "app_settings", "notifications", "alembic_version"}


@pytest.fixture(params=DATABASES)
def database_app(request, tmp_path):
    admin = None
    schema = None
    if request.param == "postgresql":
        url = sa.engine.make_url(os.environ["TEST_POSTGRES_URL"])
        assert url.get_backend_name() == "postgresql"
        schema = "ofs_test_" + uuid4().hex
        admin = sa.create_engine(url)
        with admin.begin() as connection:
            connection.execute(sa.text(f'CREATE SCHEMA "{schema}"'))
        uri = url.update_query_dict({"options": f"-csearch_path={schema}"})
    else:
        uri = "sqlite:///" + str(tmp_path / "migration.db")

    class DatabaseConfig(TestConfig):
        SQLALCHEMY_DATABASE_URI = uri

    app = create_app(DatabaseConfig)
    try:
        with app.app_context():
            yield app
            db.session.remove()
            db.engine.dispose()
    finally:
        if admin is not None:
            with admin.begin() as connection:
                connection.execute(sa.text(f'DROP SCHEMA "{schema}" CASCADE'))
            admin.dispose()


def add_test_rows():
    # Small fixture for database integrity tests; the team's demo seed is unchanged.
    user = User(email="customer@example.com", name="Test Customer", password_hash="test-hash", role="customer")
    product = Product(name="Test Apples", category="Produce", price="5.99", weight_lb="3.00", stock_qty=10)
    db.session.add_all([user, product, Robot(robot_code="TEST-R01")])
    db.session.flush()
    db.session.add(Address(user_id=user.id, line1="150 S 1st St", city="San Jose", postal_code="95113",
                           formatted_address="150 S 1st St, San Jose, CA 95113", latitude=37.333, longitude=-121.889))
    db.session.add(InventoryLog(product_id=product.product_id, before_qty=0, change_qty=10, after_qty=10, reason="RESTOCK"))
    db.session.commit()


def migrate():
    upgrade(directory=MIGRATIONS)
    if db.engine.dialect.name == "sqlite":
        db.session.execute(sa.text("PRAGMA foreign_keys=ON"))
        db.session.commit()


def test_fresh_migration_matches_models(database_app):
    migrate()
    assert set(sa.inspect(db.engine).get_table_names()) == TABLES
    assert db.session.execute(sa.text("SELECT version_num FROM alembic_version")).scalar() == "0002_foundation"
    check(directory=MIGRATIONS)
    inspector = sa.inspect(db.engine)
    for table in db.metadata.sorted_tables:
        actual = {c["name"] for c in inspector.get_check_constraints(table.name)}
        expected = {c.name for c in table.constraints if isinstance(c, sa.CheckConstraint)}
        assert actual == expected, table.name


def test_upgrade_and_downgrade_preserve_existing_rows(database_app):
    upgrade(directory=MIGRATIONS, revision="0001_baseline")
    with db.engine.begin() as c:
        c.execute(sa.text("INSERT INTO users (id,email,name,password_hash,role,created_at) VALUES (1,'existing@example.com','Existing','unchanged','customer',CURRENT_TIMESTAMP)"))
        c.execute(sa.text("INSERT INTO products (product_id,name,category,price,weight_lb,stock_qty,low_stock_threshold,active) VALUES (1,'Apples','Produce',5.99,3,12,5,true)"))
    upgrade(directory=MIGRATIONS)
    assert db.session.get(User, 1).password_hash == "unchanged"
    assert db.session.get(Product, 1).stock_qty == 12
    db.session.remove()
    downgrade(directory=MIGRATIONS, revision="0001_baseline")
    assert "robots" not in sa.inspect(db.engine).get_table_names()
    with db.engine.connect() as c:
        assert c.execute(sa.text("SELECT stock_qty FROM products WHERE product_id=1")).scalar() == 12
    upgrade(directory=MIGRATIONS)
    check(directory=MIGRATIONS)


def test_constraints_reject_invalid_rows_and_orphan_payments(database_app):
    migrate()
    add_test_rows()
    product = Product.query.first()
    robot = Robot.query.first()
    user = User.query.first()
    statements = [
        ("UPDATE products SET stock_qty=-1 WHERE product_id=:id", product.product_id),
        ("UPDATE products SET weight_lb=0 WHERE product_id=:id", product.product_id),
        ("UPDATE products SET price=-1 WHERE product_id=:id", product.product_id),
        ("UPDATE users SET role='admin' WHERE id=:id", user.id),
        ("UPDATE robots SET status='flying' WHERE id=:id", robot.id),
        ("UPDATE addresses SET latitude=91 WHERE id=:id", Address.query.first().id),
        ("UPDATE inventory_log SET after_qty=999999 WHERE id=:id", InventoryLog.query.first().id),
    ]
    for statement, ident in statements:
        with pytest.raises(IntegrityError):
            with db.session.begin_nested():
                db.session.execute(sa.text(statement), {"id": ident})
    with pytest.raises(IntegrityError):
        with db.session.begin_nested():
            db.session.add(Payment(user_id=user.id, amount_cents=1, idempotency_key="orphan-test", order_id=999999))
            db.session.flush()
    assert db.session.get(Product, product.product_id).stock_qty >= 0


def make_order(user, product):
    order = Order(user_id=user.id, subtotal=product.price, delivery_fee=0, total=product.price,
                  weight_lb=product.weight_lb, delivery_address="150 S 1st St", delivery_lat=37.333, delivery_lng=-121.889)
    order.lines.append(OrderLine(product_id=product.product_id, name=product.name, unit_price=product.price,
                                 weight_lb=product.weight_lb, quantity=1))
    db.session.add(order)
    db.session.flush()
    return order


def test_order_snapshot_and_trip_stop_integrity(database_app):
    migrate()
    add_test_rows()
    product = Product.query.first()
    customer = User.query.filter_by(email="customer@example.com").one()
    order = make_order(customer, product)
    original_price, original_weight = order.lines[0].unit_price, order.lines[0].weight_lb
    product.price = 99
    product.weight_lb = 9
    trip = Trip(robot_id=Robot.query.first().id)
    db.session.add(trip)
    db.session.flush()
    order.trip_id = trip.id
    stop = TripStop(trip_id=trip.id, order_id=order.id, stop_number=1, latitude=37.333, longitude=-121.889)
    db.session.add(stop)
    db.session.commit()
    assert (order.lines[0].unit_price, order.lines[0].weight_lb) == (original_price, original_weight)
    for number in (1, 11):
        with pytest.raises(IntegrityError):
            with db.session.begin_nested():
                another = make_order(customer, product)
                db.session.add(TripStop(trip_id=trip.id, order_id=another.id, stop_number=number, latitude=37.333, longitude=-121.889))
                db.session.flush()


def test_failed_delivery_can_ride_a_later_trip(database_app):
    # delivery_failed -> placed sends an Order back to the queue, so it can get a stop on a second
    # Trip; the first stop stays as history. Twice on the same Trip is still rejected.
    migrate()
    add_test_rows()
    customer = User.query.filter_by(email="customer@example.com").one()
    order = make_order(customer, Product.query.first())
    first, second = Trip(status="dispatched"), Trip()
    db.session.add_all([first, second])
    db.session.flush()
    db.session.add(TripStop(trip_id=first.id, order_id=order.id, stop_number=1, latitude=37.333,
                            longitude=-121.889, status="delivery_failed"))
    db.session.add(TripStop(trip_id=second.id, order_id=order.id, stop_number=1, latitude=37.333, longitude=-121.889))
    db.session.commit()
    assert TripStop.query.filter_by(order_id=order.id).count() == 2
    with pytest.raises(IntegrityError):
        with db.session.begin_nested():
            db.session.add(TripStop(trip_id=second.id, order_id=order.id, stop_number=2, latitude=37.333, longitude=-121.889))
            db.session.flush()


def test_trip_can_be_ready(database_app):
    # T13 locks full or overdue Trips as "ready" (BR-6/BR-7); the status check must allow it.
    migrate()
    db.session.add(Trip(status="ready", ready_reason="full"))
    db.session.commit()
    assert Trip.query.one().status == "ready"
