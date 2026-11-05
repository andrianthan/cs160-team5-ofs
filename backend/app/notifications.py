# T17 — Notifications over SMTP. Owner: Than Andrian.
# Trigger table (HLD: "Email Customers and Staff on Order Status changes and failed deliveries"):
#   event             fired when                    recipients
#   order_placed      payment succeeds, Order made  Customer
#   out_for_delivery  status -> Out for Delivery    Customer
#   delivered         status -> Delivered           Customer
#   delivery_failed   status -> Delivery Failed     Customer + all Staff   (BR-8)
#   manual_review     status -> Manual Review       all Staff
# Deduplication: one `notifications` row per (order, event, recipient); a sent row is never sent again.
# Retry: up to NOTIFY_MAX_ATTEMPTS sends per recipient, NOTIFY_RETRY_DELAY_S apart, then marked failed.
# A mail problem is logged and recorded; it never raises into checkout or a status change.
import smtplib
import threading
import time
from datetime import datetime, timezone
from email.message import EmailMessage

from flask import current_app
from sqlalchemy.exc import IntegrityError

from .extensions import db
from .models import Notification, Order, User
from .models.notification import FAILED, PENDING, SENT, SKIPPED
from .models.order import DELIVERED, DELIVERY_FAILED, MANUAL_REVIEW, OUT_FOR_DELIVERY
from .models.user import STAFF_ROLES

ORDER_PLACED = "order_placed"
OUT_FOR_DELIVERY_EVENT = "out_for_delivery"
DELIVERED_EVENT = "delivered"
DELIVERY_FAILED_EVENT = "delivery_failed"
MANUAL_REVIEW_EVENT = "manual_review"

# Order status -> event. Statuses not listed (Placed, Planned) send nothing.
STATUS_EVENTS = {
    OUT_FOR_DELIVERY: OUT_FOR_DELIVERY_EVENT,
    DELIVERED: DELIVERED_EVENT,
    DELIVERY_FAILED: DELIVERY_FAILED_EVENT,
    MANUAL_REVIEW: MANUAL_REVIEW_EVENT,
}
STAFF_EVENTS = {DELIVERY_FAILED_EVENT, MANUAL_REVIEW_EVENT}
CUSTOMER_EVENTS = {ORDER_PLACED, OUT_FOR_DELIVERY_EVENT, DELIVERED_EVENT, DELIVERY_FAILED_EVENT}


def notify_status_change(order):
    """Call after committing an Order's new status."""
    event = STATUS_EVENTS.get(order.status)
    if event:
        notify_order_event(order.id, event)


def notify_order_event(order_id, event):
    """Email everyone the event concerns. Safe to call twice; never raises."""
    if current_app.config.get("NOTIFICATIONS_ASYNC"):
        app = current_app._get_current_object()
        threading.Thread(target=_run_in_context, args=(app, order_id, event), daemon=True).start()
    else:
        _run(order_id, event)


def _run_in_context(app, order_id, event):
    with app.app_context():
        _run(order_id, event)
        db.session.remove()


def _run(order_id, event):
    try:
        order = db.session.get(Order, order_id)
        if order is None:
            return
        for name, email in _recipients(order, event):
            row = _claim(order.id, event, email)
            if row is not None:
                _send_with_retry(row, _build(order, event, name, email))
    except Exception:  # a mail problem must never break the caller
        db.session.rollback()
        current_app.logger.exception("Notification %s for order %s failed", event, order_id)


def _recipients(order, event):
    people = []
    if event in CUSTOMER_EVENTS:
        customer = db.session.get(User, order.user_id)
        if customer:
            people.append(customer)
    if event in STAFF_EVENTS:
        people += User.query.filter(User.role.in_(STAFF_ROLES)).order_by(User.id).all()
    seen, out = set(), []
    for p in people:
        if p.email not in seen:
            seen.add(p.email)
            out.append((p.name, p.email))
    return out


def _claim(order_id, event, email):
    """The row to send for, or None when it was already sent or is being sent."""
    existing = Notification.query.filter_by(order_id=order_id, event=event, recipient_email=email).first()
    if existing:
        return None if existing.status in (SENT, PENDING) else existing
    row = Notification(order_id=order_id, event=event, recipient_email=email, status=PENDING)
    db.session.add(row)
    try:
        db.session.commit()
    except IntegrityError:  # a concurrent caller got there first
        db.session.rollback()
        return None
    return row


def _send_with_retry(row, msg):
    cfg = current_app.config
    if not cfg.get("SMTP_HOST"):
        current_app.logger.warning("SMTP_HOST not set; %s to %s skipped", row.event, row.recipient_email)
        row.status = SKIPPED
        db.session.commit()
        return
    row.status = PENDING
    for attempt in range(1, cfg["NOTIFY_MAX_ATTEMPTS"] + 1):
        row.attempts += 1
        try:
            _send(msg)
        except Exception as exc:
            row.last_error = f"{type(exc).__name__}: {exc}"[:500]
            current_app.logger.warning("Email attempt %s to %s failed: %s", attempt, row.recipient_email, exc)
            if attempt < cfg["NOTIFY_MAX_ATTEMPTS"]:
                time.sleep(cfg["NOTIFY_RETRY_DELAY_S"])
            continue
        row.status, row.last_error, row.sent_at = SENT, None, datetime.now(timezone.utc)
        break
    else:
        row.status = FAILED
    db.session.commit()


def _send(msg):
    cfg = current_app.config
    with smtplib.SMTP(cfg["SMTP_HOST"], cfg["SMTP_PORT"], timeout=cfg["SMTP_TIMEOUT_S"]) as server:
        if cfg["SMTP_STARTTLS"]:
            server.starttls()
        if cfg.get("SMTP_USERNAME"):
            server.login(cfg["SMTP_USERNAME"], cfg.get("SMTP_PASSWORD") or "")
        server.send_message(msg)


def _build(order, event, name, email):
    subject, intro = {
        ORDER_PLACED: (f"OFS order #{order.id} confirmed", "Thanks for your order. We're getting it ready."),
        OUT_FOR_DELIVERY_EVENT: (f"OFS order #{order.id} is on its way", "Your order is out for delivery."),
        DELIVERED_EVENT: (f"OFS order #{order.id} was delivered", "Your order has been delivered. Enjoy!"),
        DELIVERY_FAILED_EVENT: (
            f"OFS order #{order.id}: delivery failed",
            "We couldn't hand over the order at the stop. It is back at the store and "
            "we'll reschedule it.",
        ),
        MANUAL_REVIEW_EVENT: (
            f"OFS order #{order.id} needs manual review",
            "This order was sent to Manual Review and needs a staff decision.",
        ),
    }[event]
    lines = "\n".join(f"  {l.quantity} x {l.name}" for l in order.lines)
    body = (
        f"Hi {name},\n\n{intro}\n\n"
        f"Order #{order.id}\nDeliver to: {order.delivery_address}\n{lines}\n"
        f"Total: ${order.total:.2f}\n\n- OFS On-Demand Delivery\n"
    )
    msg = EmailMessage()
    msg["Subject"], msg["From"], msg["To"] = subject, current_app.config.get("SMTP_FROM") or "no-reply@ofs.local", email
    msg.set_content(body)
    return msg
