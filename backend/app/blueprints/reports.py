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
#   - On-time rate = delivered stops that arrived at or before their estimated arrival (set when the Trip
#     was dispatched) / delivered stops that have an ETA. Stops belong to the period of their Order.
#     None when there are none.
#   - Delivery duration = minutes from the Order being placed to the Robot arriving at its stop, averaged
#     over those same delivered stops. None when there are none.
#   - Trip utilization, over Trips dispatched in the period: average orders per Trip, and the average fill
#     of the Robot limits (orders / TRIP_MAX_ORDERS, weight / TRIP_MAX_WEIGHT_LB). None when no Trip went out.
from collections import defaultdict
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal

from flask import Blueprint, jsonify, request

from .auth import manager_required
from ..config import Config
from ..models import Order, OrderLine, Product, Trip, TripStop
from ..models.order import CANCELLED, DELIVERED, DELIVERY_FAILED, STATUSES
from ..models.trip import DISPATCHED, COMPLETED
from ..timeutil import as_utc

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
        end_exclusive = end_day + timedelta(days=1)
    except (ValueError, OverflowError):  # OverflowError: to=9999-12-31 has no next day (was a 500)
        return None, (jsonify(error="bad_date", message="Dates must be YYYY-MM-DD."), 400)
    if start_day > end_day:
        return None, (jsonify(error="bad_range", message="'from' must not be after 'to'."), 400)
    start = datetime.combine(start_day, time.min, tzinfo=timezone.utc)
    end = datetime.combine(end_exclusive, time.min, tzinfo=timezone.utc)
    return (start, end, start_day, end_day), None


def _orders_in(start, end):
    return Order.query.filter(Order.created_at >= start, Order.created_at < end).all()


def _delivery_timing(start, end):
    """(on-time rate, average delivery minutes) over delivered stops with an ETA; (None, None) if none."""
    stops = (TripStop.query.join(Order, TripStop.order_id == Order.id)
             .filter(Order.created_at >= start, Order.created_at < end, TripStop.status == "delivered",
                     TripStop.estimated_arrival.isnot(None), TripStop.arrived_at.isnot(None)).all())
    if not stops:
        return None, None
    on_time = sum(1 for s in stops if as_utc(s.arrived_at) <= as_utc(s.estimated_arrival))
    minutes = [(as_utc(s.arrived_at) - as_utc(s.order.created_at)).total_seconds() / 60 for s in stops]
    return on_time / len(stops), sum(minutes) / len(minutes)


def _trip_utilization(start, end):
    trips = Trip.query.filter(Trip.status.in_((DISPATCHED, COMPLETED)),
                              Trip.dispatched_at >= start, Trip.dispatched_at < end).all()
    if not trips:
        return None
    n = len(trips)
    return {
        "trips": n,
        "avgOrdersPerTrip": sum(len(t.orders) for t in trips) / n,
        "avgOrderFill": sum(len(t.orders) / Config.TRIP_MAX_ORDERS for t in trips) / n,
        "avgWeightFill": sum(float(t.weight_lb) / Config.TRIP_MAX_WEIGHT_LB for t in trips) / n,
    }


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
    # Snapshot of current Stock. Per-product change history is GET /api/products/<id>/inventory-log.
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

    on_time_rate, avg_minutes = _delivery_timing(start, end)
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
            "onTimeRate": on_time_rate,
            "avgDeliveryMinutes": avg_minutes,
            "tripUtilization": _trip_utilization(start, end),
        }
    )
