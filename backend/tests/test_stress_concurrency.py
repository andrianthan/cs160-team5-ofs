"""Concurrency stress tests: many people hitting the same rows at the same moment.

Owner: Karnani Shresthkumar (T04 sign-up, T05 Stock and its log, T12 orders). These need real
concurrent writers and row locks, so they run only on PostgreSQL (TEST_POSTGRES_URL, set in CI).
Each request runs in its own thread with its own test client, released together by a barrier.
"""
import os
import threading
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal

import pytest

from app.extensions import db
from app.models import InventoryLog, Order, OrderLine, OrderOverrideAudit, Payment, Product, User
from stress_support import (PASSWORD, FakeStripe, call, make_product, make_user, signed_in, start_payment,
                            stress_app, webhook)  # noqa: F401

pytestmark = pytest.mark.skipif(not os.getenv("TEST_POSTGRES_URL"),
                                reason="needs PostgreSQL (TEST_POSTGRES_URL); SQLite can't run concurrent writers")


@pytest.fixture
def pg(monkeypatch):
    with stress_app("postgresql") as app:
        yield app, FakeStripe(monkeypatch)


def all_at_once(fns):
    """Start every function at the same instant, each in its own thread. Returns results in order."""
    barrier = threading.Barrier(len(fns))

    def run(fn):
        barrier.wait(timeout=30)
        return fn()

    with ThreadPoolExecutor(max_workers=len(fns)) as pool:
        return list(pool.map(run, fns))


def statuses(results):
    return sorted(status for status, _ in results)


def no_crashes(results):
    crashes = [detail for status, detail in results if status >= 500]
    assert crashes == [], crashes[:5]


def stock_and_log(app, product_id):
    """Final Stock, and the product's log rows after checking they form one unbroken chain."""
    with app.app_context():
        rows = InventoryLog.query.filter_by(product_id=product_id).order_by(InventoryLog.id).all()
        stock = db.session.get(Product, product_id).stock_qty
        for prev, row in zip(rows, rows[1:]):
            assert row.before_qty == prev.after_qty, f"log chain broken at row {row.id}"
        if rows:
            assert rows[-1].after_qty == stock, "log doesn't end at the current Stock"
        return stock, [(r.reason, r.change_qty) for r in rows]


def customers_with_payments(app, n, product_quantities, prefix="c"):
    """n signed-in customers, each with a started checkout. Returns their PaymentIntent ids."""
    intents = []
    for i in range(n):
        make_user(app, f"{prefix}{i}@example.com")
        intents.append(start_payment(app, signed_in(app, f"{prefix}{i}@example.com"), product_quantities))
    return intents


def hook(app, intent):
    """Stripe's webhook for one PaymentIntent, from a fresh client: (status, detail)."""
    try:
        return webhook(app.test_client(), intent).status_code, None
    except Exception as exc:  # noqa: BLE001 - TESTING re-raises what production turns into a 500
        return 500, f"{type(exc).__name__}: {exc}"[:160]


# ============ T04: sign-up ============

def test_same_email_signed_up_at_once_makes_one_account(pg):
    app, _ = pg
    body = {"email": "rush@example.com", "name": "Rush", "password": PASSWORD}
    results = all_at_once([lambda: call(app.test_client(), "POST", "/api/auth/register", body)] * 15)
    no_crashes(results)
    assert statuses(results) == [201] + [409] * 14
    with app.app_context():
        assert User.query.filter_by(email="rush@example.com").count() == 1


# ============ T12 + T05: checkout and Stock ============

def test_customers_racing_for_the_last_units(pg):
    app, fake = pg
    product = make_product(app, stock=3)
    intents = customers_with_payments(app, 12, [(product, 1)])

    results = all_at_once([lambda i=i: hook(app, i) for i in intents])
    no_crashes(results)
    assert statuses(results) == [200] * 12
    with app.app_context():
        assert Order.query.count() == 3
        assert sorted(p.status for p in Payment.query.all()) == ["refunded"] * 9 + ["succeeded"] * 3
    assert len(fake.refunds) == 9
    assert stock_and_log(app, product) == (0, [("SALE", -1)] * 3)


def test_one_payment_webhook_storm_places_one_order(pg):
    app, fake = pg
    product = make_product(app, stock=5)
    [intent] = customers_with_payments(app, 1, [(product, 2)])

    results = all_at_once([lambda: hook(app, intent)] * 10)
    no_crashes(results)
    assert statuses(results) == [200] * 10
    with app.app_context():
        assert Order.query.count() == 1
    assert fake.refunds == []
    assert stock_and_log(app, product) == (3, [("SALE", -2)])


def test_crossed_carts_do_not_deadlock(pg):
    app, _ = pg
    apple, pear = make_product(app, "Apple", stock=100), make_product(app, "Pear", stock=100)
    # Half the carts add Apple then Pear, the other half Pear then Apple.
    intents = customers_with_payments(app, 6, [(apple, 1), (pear, 1)], prefix="a")
    intents += customers_with_payments(app, 6, [(pear, 1), (apple, 1)], prefix="p")

    results = all_at_once([lambda i=i: hook(app, i) for i in intents])
    no_crashes(results)
    assert statuses(results) == [200] * 12
    with app.app_context():
        assert Order.query.count() == 12
    assert stock_and_log(app, apple)[0] == 88 and stock_and_log(app, pear)[0] == 88


def test_stock_edits_during_sales_keep_the_log_unbroken(pg):
    app, _ = pg
    product = make_product(app, stock=100)
    intents = customers_with_payments(app, 10, [(product, 1)])
    make_user(app, "boss@example.com", "manager")
    managers = [signed_in(app, "boss@example.com") for _ in range(6)]

    sales = [lambda i=i: hook(app, i) for i in intents]
    edits = [lambda m=m, n=n: call(m, "PATCH", f"/api/products/{product}", {"stock_qty": 60 + 10 * n})
             for n, m in enumerate(managers)]
    results = all_at_once(sales + edits)
    no_crashes(results)
    assert statuses(results) == [200] * 16
    stock, log = stock_and_log(app, product)  # asserts the chain itself
    assert [reason for reason, _ in log].count("SALE") == 10
    with app.app_context():
        assert Order.query.count() == 10


# ============ T12: cancelling (Manager Order Override) ============

def test_managers_cancelling_one_order_at_once_restock_it_once(pg):
    app, _ = pg
    product = make_product(app, stock=8)
    customer = make_user(app, "c@example.com")
    with app.app_context():
        order = Order(user_id=customer, subtotal=Decimal("3.00"), delivery_fee=Decimal("0"), total=Decimal("3.00"),
                      weight_lb=Decimal("1.00"), delivery_address="1 Main St", delivery_lat=37.33,
                      delivery_lng=-121.89)
        order.lines.append(OrderLine(product_id=product, name="Apple", unit_price=Decimal("1.50"),
                                     weight_lb=Decimal("0.50"), quantity=2))
        db.session.add(order)
        db.session.commit()
        order_id = order.id
    make_user(app, "boss@example.com", "manager")
    managers = [signed_in(app, "boss@example.com") for _ in range(8)]
    body = {"action": "cancel", "reason": "customer called", "confirmed": True}

    results = all_at_once([lambda m=m: call(m, "POST", f"/api/orders/{order_id}/override", body) for m in managers])
    no_crashes(results)
    assert statuses(results) == [200] + [409] * 7
    assert stock_and_log(app, product) == (10, [("CANCEL", 2)])
    with app.app_context():
        assert OrderOverrideAudit.query.count() == 1
