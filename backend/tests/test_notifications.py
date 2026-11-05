from datetime import datetime, timezone
from decimal import Decimal

import pytest

from app import notifications
from app.extensions import db
from app.models import Notification, Order, OrderLine, Product, User
from app.models.order import DELIVERED, DELIVERY_FAILED, MANUAL_REVIEW, OUT_FOR_DELIVERY, PLACED

PASSWORD = "johnathanpassword123"


class FakeSMTP:
    """Stands in for smtplib.SMTP. Class-level state so tests can inspect every connection."""
    sent, fail_times, logins, tls = [], 0, [], 0

    def __init__(self, host, port, timeout=None):
        self.host, self.port = host, port

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def starttls(self):
        FakeSMTP.tls += 1

    def login(self, user, pw):
        FakeSMTP.logins.append((user, pw))

    def send_message(self, msg):
        if FakeSMTP.fail_times > 0:
            FakeSMTP.fail_times -= 1
            raise OSError("smtp down")
        FakeSMTP.sent.append(msg)


@pytest.fixture(autouse=True)
def smtp(app, monkeypatch):
    FakeSMTP.sent, FakeSMTP.fail_times, FakeSMTP.logins, FakeSMTP.tls = [], 0, [], 0
    monkeypatch.setattr(notifications.smtplib, "SMTP", FakeSMTP)
    app.config.update(SMTP_HOST="smtp.test", SMTP_PORT=587, SMTP_USERNAME="apikey", SMTP_PASSWORD="pw",
                      SMTP_FROM="no-reply@ofs.test", NOTIFICATIONS_ASYNC=False,
                      NOTIFY_MAX_ATTEMPTS=3, NOTIFY_RETRY_DELAY_S=0)


def user(email, role="customer", name="Casey"):
    u = User(email=email, name=name, role=role)
    u.set_password(PASSWORD)
    db.session.add(u)
    db.session.flush()
    return u


def make_order(customer):
    p = Product(name="Apple", category="Produce", price=Decimal("2.00"), weight_lb=Decimal("1"), stock_qty=5)
    db.session.add(p)
    db.session.flush()
    o = Order(user_id=customer.id, status=PLACED, subtotal=Decimal("4.00"), delivery_fee=Decimal("0"),
              total=Decimal("4.00"), weight_lb=Decimal("2"), delivery_address="1 Main St, San Jose",
              delivery_lat=37.3, delivery_lng=-121.9)
    o.lines.append(OrderLine(product_id=p.product_id, name="Apple", unit_price=p.price,
                             weight_lb=p.weight_lb, quantity=2))
    db.session.add(o)
    db.session.commit()
    return o


def world():
    c = user("cust@example.com")
    user("emp@example.com", "employee", "Eli")
    user("mgr@example.com", "manager", "Maya")
    return make_order(c)


def to_of(msg):
    return msg["To"]


# ---------- triggers and recipients ----------

def test_order_placed_emails_customer_only(app):
    o = world()
    notifications.notify_order_event(o.id, notifications.ORDER_PLACED)
    assert [to_of(m) for m in FakeSMTP.sent] == ["cust@example.com"]
    m = FakeSMTP.sent[0]
    assert f"#{o.id}" in m["Subject"] and "$4.00" in m.get_content() and "1 Main St" in m.get_content()
    assert m["From"] == "no-reply@ofs.test"


@pytest.mark.parametrize("status,event", [(OUT_FOR_DELIVERY, "out_for_delivery"), (DELIVERED, "delivered")])
def test_status_change_emails_customer(app, status, event):
    o = world()
    o.status = status
    db.session.commit()
    notifications.notify_status_change(o)
    assert [to_of(m) for m in FakeSMTP.sent] == ["cust@example.com"]
    assert Notification.query.one().event == event


def test_delivery_failed_notifies_customer_and_all_staff(app):
    o = world()
    o.status = DELIVERY_FAILED
    db.session.commit()
    notifications.notify_status_change(o)
    assert sorted(to_of(m) for m in FakeSMTP.sent) == ["cust@example.com", "emp@example.com", "mgr@example.com"]


def test_manual_review_notifies_staff_only(app):
    o = world()
    o.status = MANUAL_REVIEW
    db.session.commit()
    notifications.notify_status_change(o)
    assert sorted(to_of(m) for m in FakeSMTP.sent) == ["emp@example.com", "mgr@example.com"]


def test_statuses_without_a_trigger_send_nothing(app):
    o = world()
    for status in ("placed", "planned"):
        o.status = status
        notifications.notify_status_change(o)
    assert FakeSMTP.sent == [] and Notification.query.count() == 0


# ---------- dedup ----------

def test_same_event_is_sent_once(app):
    o = world()
    for _ in range(3):
        notifications.notify_order_event(o.id, notifications.ORDER_PLACED)
    assert len(FakeSMTP.sent) == 1
    assert Notification.query.count() == 1


def test_different_events_both_send(app):
    o = world()
    notifications.notify_order_event(o.id, notifications.ORDER_PLACED)
    notifications.notify_order_event(o.id, notifications.DELIVERED_EVENT)
    assert len(FakeSMTP.sent) == 2


# ---------- retry and failure ----------

def test_retries_then_succeeds(app):
    o = world()
    FakeSMTP.fail_times = 2
    notifications.notify_order_event(o.id, notifications.ORDER_PLACED)
    n = Notification.query.one()
    assert n.status == "sent" and n.attempts == 3 and n.sent_at is not None
    assert len(FakeSMTP.sent) == 1


def test_gives_up_after_max_attempts_and_records_error(app):
    o = world()
    FakeSMTP.fail_times = 99
    notifications.notify_order_event(o.id, notifications.ORDER_PLACED)  # must not raise
    n = Notification.query.one()
    assert n.status == "failed" and n.attempts == 3 and "smtp down" in n.last_error
    assert FakeSMTP.sent == []


def test_failed_notification_can_be_retried_by_a_later_call(app):
    o = world()
    FakeSMTP.fail_times = 99
    notifications.notify_order_event(o.id, notifications.ORDER_PLACED)
    FakeSMTP.fail_times = 0
    notifications.notify_order_event(o.id, notifications.ORDER_PLACED)
    assert Notification.query.one().status == "sent" and len(FakeSMTP.sent) == 1


def test_one_bad_recipient_does_not_block_the_others(app):
    o = world()
    o.status = DELIVERY_FAILED
    db.session.commit()
    real = FakeSMTP.send_message

    def picky(self, msg):
        if msg["To"] == "emp@example.com":
            raise OSError("mailbox full")
        return real(self, msg)

    FakeSMTP.send_message = picky
    try:
        notifications.notify_status_change(o)
    finally:
        FakeSMTP.send_message = real
    assert sorted(to_of(m) for m in FakeSMTP.sent) == ["cust@example.com", "mgr@example.com"]
    assert {n.recipient_email: n.status for n in Notification.query} == {
        "cust@example.com": "sent", "emp@example.com": "failed", "mgr@example.com": "sent"}


def test_smtp_not_configured_is_skipped_not_fatal(app):
    app.config["SMTP_HOST"] = None
    o = world()
    notifications.notify_order_event(o.id, notifications.ORDER_PLACED)
    assert FakeSMTP.sent == [] and Notification.query.one().status == "skipped"


def test_smtp_auth_and_tls_used(app):
    o = world()
    notifications.notify_order_event(o.id, notifications.ORDER_PLACED)
    assert FakeSMTP.tls == 1 and FakeSMTP.logins == [("apikey", "pw")]


def test_missing_order_is_ignored(app):
    notifications.notify_order_event(9999, notifications.ORDER_PLACED)
    assert FakeSMTP.sent == []


# ---------- wiring ----------

def login(client, email):
    assert client.post("/api/auth/login", json={"email": email, "password": PASSWORD}).status_code == 200


def test_status_endpoint_sends_email_and_survives_smtp_failure(app, client):
    o = world()
    oid = o.id
    login(client, "emp@example.com")
    o_ = db.session.get(Order, oid)
    o_.status = "out_for_delivery"
    db.session.commit()

    FakeSMTP.fail_times = 99  # SMTP down: the status change must still succeed
    r = client.patch(f"/api/orders/{oid}/status", json={"status": "delivered"})
    assert r.status_code == 200 and r.get_json()["status"] == "delivered"
    assert db.session.get(Order, oid).status == "delivered"
    assert Notification.query.one().status == "failed"


def test_status_endpoint_emails_customer_on_delivery(app, client):
    o = world()
    oid = o.id
    login(client, "emp@example.com")
    db.session.get(Order, oid).status = "out_for_delivery"
    db.session.commit()
    client.patch(f"/api/orders/{oid}/status", json={"status": "delivered"})
    assert [to_of(m) for m in FakeSMTP.sent] == ["cust@example.com"]


def test_overweight_prepare_emails_staff_manual_review(app, client):
    o = world()
    oid = o.id
    db.session.get(Order, oid).weight_lb = Decimal("250")
    db.session.commit()
    login(client, "emp@example.com")
    r = client.post(f"/api/orders/{oid}/prepare")
    assert r.status_code == 409 and r.get_json()["error"] == "too_heavy_for_robot"
    assert sorted(to_of(m) for m in FakeSMTP.sent) == ["emp@example.com", "mgr@example.com"]
    assert {n.event for n in Notification.query} == {"manual_review"}
