"""The demo data (demo_data.py) must obey the same rules the app enforces, so a seeded database
behaves like one built by real checkouts."""
from decimal import Decimal

import pytest

from app.extensions import db
from app.models import InventoryLog, Order, Payment, Product, Robot, Trip, User
from app.models.order import STATUSES
from demo_data import DEMO_PRODUCTS, DEMO_USERS, WATER, build_history


@pytest.fixture
def seeded(app):
    for email, name, role, password in DEMO_USERS:
        user = User(email=email, name=name, role=role)
        user.set_password(password)
        db.session.add(user)
    for name, category, price, weight, stock, threshold, active in DEMO_PRODUCTS:
        db.session.add(Product(name=name, category=category, price=Decimal(price), weight_lb=Decimal(weight),
                               stock_qty=stock, low_stock_threshold=threshold, active=active))
    db.session.commit()
    return build_history()


def test_every_status_is_represented(seeded):
    assert {o.status for o in Order.query.all()} == set(STATUSES)


def test_totals_follow_the_fee_rule(seeded):
    for order in Order.query.all():
        assert order.delivery_fee == (10 if order.weight_lb >= 20 else 0)
        assert order.total == order.subtotal + order.delivery_fee
        assert Payment.query.filter_by(order_id=order.id).one().amount_cents == int(order.total * 100)


def test_only_the_manual_review_order_is_over_the_robot_limit(seeded):
    heavy = [o for o in Order.query.all() if o.weight_lb > 200]
    assert [o.status for o in heavy] == ["manual_review"]


def test_water_case_demonstrates_the_20_lb_fee(seeded):
    water = Product.query.filter_by(name=WATER).one()
    assert water.weight_lb >= 20


def test_stock_matches_the_inventory_log(seeded):
    for product in Product.query.all():
        rows = InventoryLog.query.filter_by(product_id=product.product_id) \
            .order_by(InventoryLog.created_at, InventoryLog.id).all()
        expected = rows[-1].after_qty if rows else 0
        assert product.stock_qty == expected
        assert all(a.after_qty == b.before_qty for a, b in zip(rows, rows[1:]))


def test_trips_respect_capacity_and_two_robots_exist(seeded):
    assert Robot.query.count() == 2
    for trip in Trip.query.all():
        assert len(trip.orders) <= 10 and trip.weight_lb <= 200


def test_second_build_adds_nothing(seeded):
    before = Order.query.count()
    assert "left them alone" in build_history()
    assert Order.query.count() == before
