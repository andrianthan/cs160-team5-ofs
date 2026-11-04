# T19 — Manager Reports. Owner: Than Andrian.
# LLD 4: metric definitions (on-time rate, delivery duration, trip utilization,
# product demand) must match the Test Plan's metric definitions exactly.
#
# Metric definitions used here (keep identical wherever they are quoted):
#   - Sales orders: every Order in the period except Cancelled. Period = created_at, UTC, inclusive dates.
#   - Revenue = sum(Order.total) = subtotal + delivery fee.
#   - Average order value = revenue / order count (0 when there are no orders).
#   - Product demand = units sold and line revenue per Product over the sales orders.
#   - Delivery success rate = Delivered / (Delivered + Delivery Failed). None when neither exists.
#   - On-time rate: None until Trips carry ETAs (T13/T15) — there is nothing to compare against yet.
from collections import defaultdict
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal

from flask import Blueprint, jsonify, request

from .auth import manager_required
from ..models import Order, OrderLine, Product
from ..models.order import CANCELLED, DELIVERED, DELIVERY_FAILED, STATUSES

bp = Blueprint("reports", __name__, url_prefix="/api/reports")

DEFAULT_DAYS = 30


def _money(value):
    return float(Decimal(value).quantize(Decimal("0.01")))


def _period():
    """Parse ?from= & ?to= (YYYY-MM-DD, inclusive). Returns (start, end_exclusive, from, to) or an error tuple."""
    today = datetime.now(timezone.utc).date()
    try:
        end_day = date.fromisoformat(request.args["to"]) if request.args.get("to") else today
        start_day = (
            date.fromisoformat(request.args["from"])
            if request.args.get("from")
            else end_day - timedelta(days=DEFAULT_DAYS)
        )
    except ValueError:
        return None, (jsonify(error="bad_date", message="Dates must be YYYY-MM-DD."), 400)
    if start_day > end_day:
        return None, (jsonify(error="bad_range", message="'from' must not be after 'to'."), 400)
    start = datetime.combine(start_day, time.min, tzinfo=timezone.utc)
    end = datetime.combine(end_day + timedelta(days=1), time.min, tzinfo=timezone.utc)
    return (start, end, start_day, end_day), None


def _orders_in(start, end):
    return Order.query.filter(Order.created_at >= start, Order.created_at < end).all()


@bp.get("/sales")
@manager_required
def sales_report():
    period, err = _period()
    if err:
        return err
    start, end, start_day, end_day = period
    orders = [o for o in _orders_in(start, end) if o.status != CANCELLED]

    subtotal = sum((o.subtotal for o in orders), Decimal("0"))
    fees = sum((o.delivery_fee for o in orders), Decimal("0"))
    revenue = sum((o.total for o in orders), Decimal("0"))

    days = defaultdict(lambda: [0, Decimal("0")])
    demand = {}
    for o in orders:
        d = days[o.created_at.date().isoformat()]
        d[0] += 1
        d[1] += o.total
        for line in o.lines:
            row = demand.setdefault(line.product_id, {"productId": line.product_id, "name": line.name,
                                                      "units": 0, "revenue": Decimal("0")})
            row["units"] += line.quantity
            row["revenue"] += line.unit_price * line.quantity

    product_demand = sorted(demand.values(), key=lambda r: (-r["units"], r["name"]))
    return jsonify(
        {
            "from": start_day.isoformat(),
            "to": end_day.isoformat(),
            "orderCount": len(orders),
            "subtotal": _money(subtotal),
            "deliveryFees": _money(fees),
            "revenue": _money(revenue),
            "averageOrderValue": _money(revenue / len(orders)) if orders else 0,
            "byDay": [{"date": k, "orders": v[0], "revenue": _money(v[1])} for k, v in sorted(days.items())],
            "productDemand": [{**r, "revenue": _money(r["revenue"])} for r in product_demand],
        }
    )


@bp.get("/inventory")
@manager_required
def inventory_report():
    # Snapshot of current Stock. There is no inventory_log table yet, so no change history.
    products = Product.query.filter_by(active=True).order_by(Product.name).all()
    out = [p for p in products if p.stock_qty <= 0]
    low = [p for p in products if 0 < p.stock_qty <= p.low_stock_threshold]

    cats = defaultdict(lambda: {"products": 0, "units": 0})
    for p in products:
        cats[p.category]["products"] += 1
        cats[p.category]["units"] += p.stock_qty

    def row(p):
        return {"id": p.product_id, "name": p.name, "category": p.category,
                "stock": p.stock_qty, "lowStockThreshold": p.low_stock_threshold}

    return jsonify(
        {
            "totalProducts": len(products),
            "totalUnits": sum(p.stock_qty for p in products),
            "outOfStock": len(out),
            "lowStock": len(low),
            "attention": [row(p) for p in out] + [row(p) for p in low],
            "byCategory": [{"category": k, **v} for k, v in sorted(cats.items())],
        }
    )


@bp.get("/delivery")
@manager_required
def delivery_report():
    period, err = _period()
    if err:
        return err
    start, end, start_day, end_day = period
    counts = {s: 0 for s in STATUSES}
    for o in _orders_in(start, end):
        counts[o.status] += 1

    delivered, failed = counts[DELIVERED], counts[DELIVERY_FAILED]
    finished = delivered + failed
    return jsonify(
        {
            "from": start_day.isoformat(),
            "to": end_day.isoformat(),
            "statusCounts": counts,
            "delivered": delivered,
            "failed": failed,
            "deliverySuccessRate": delivered / finished if finished else None,
            "onTimeRate": None,
        }
    )
