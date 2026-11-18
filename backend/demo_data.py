"""Demo data for seed_demo.py: accounts, a full catalog and two weeks of order history.

Everything here is made up for demos and testing. Two parts:
  - the lists below (users, addresses, products);
  - build_history(), which writes past orders, payments, trips, stops and the inventory log (the
    three Robots are created by seed_demo.py),
    spread over the last 14 days (relative to "now") so the manager reports have numbers to show.

build_history() only runs on a database with no orders at all, so it can never add to real data.
It draws from a fixed random seed: the same database state gives the same history shape.
"""
import random
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from app import inventory
from app.config import Config
from app.extensions import db
from app.models import (
    Address, Order, OrderLine, OrderOverrideAudit, Payment, Product, Robot, Trip, TripStop, User,
)
from app.models.order import (
    CANCELLED, DELIVERED, DELIVERY_FAILED, MANUAL_REVIEW, OUT_FOR_DELIVERY, PLACED, PLANNED,
)
from app.models.payment import REFUNDED, SUCCEEDED
from app.models.trip import COMPLETED, DISPATCHED, OPEN, READY
from app.planning import distance_km
from app.robot import robot_code

# (email, name, role, password). The first customer owns the saved cart and most of the live orders.
DEMO_USERS = [
    ("customer@example.com", "Casey Customer", "customer", "customer123"),
    ("employee@example.com", "Eli Employee", "employee", "employee123"),
    ("manager@example.com", "Maya Manager", "manager", "manager123"),
    ("dana@example.com", "Dana Rivera", "customer", "customer123"),
    ("sam@example.com", "Sam Okafor", "customer", "customer123"),
    ("priya@example.com", "Priya Nair", "customer", "customer123"),
    ("leo@example.com", "Leo Chen", "customer", "customer123"),
    ("mia@example.com", "Mia Alvarez", "customer", "customer123"),
]

# Downtown San Jose addresses, all inside the Delivery Zone (see blueprints/addresses.py).
# (line 1, postal code, latitude, longitude). Coordinates are approximate.
ADDRESSES = [
    ("200 E Santa Clara St", "95113", 37.33770, -121.88578),
    ("233 W Santa Clara St", "95113", 37.33540, -121.89330),
    ("87 N San Pedro St", "95110", 37.33670, -121.89460),
    ("110 S Market St", "95113", 37.33370, -121.89050),
    ("170 S Market St", "95113", 37.33300, -121.89030),
    ("345 Park Ave", "95110", 37.33050, -121.89350),
    ("201 S 2nd St", "95113", 37.33310, -121.88870),
    ("282 Almaden Blvd", "95113", 37.33170, -121.89350),
    ("150 W San Carlos St", "95113", 37.32970, -121.89200),
    ("525 W Santa Clara St", "95113", 37.33280, -121.90100),
]
# One address per customer (by position among the customers above).
CUSTOMER_ADDRESS_INDEX = {
    "customer@example.com": 0, "dana@example.com": 1, "sam@example.com": 3,
    "priya@example.com": 5, "leo@example.com": 6, "mia@example.com": 7,
}

STORE = (Config.STORE_LAT, Config.STORE_LNG)  # where the Robots start and return to (same as the simulator)

WATER = "Spring Water (case of 24)"

# (name, category, price, weight_lb, stock_after_history, low_stock_threshold, active)
# The first eight are the original demo products. The water case (26 lb) is what lets the
# 20 lb fee and the 200 lb limit be shown live (Scenario 3).
DEMO_PRODUCTS = [
    ("Organic Gala Apples (3 lb bag)", "Produce", "5.99", "3.00", 40, 5, True),
    ("Baby Spinach (5 oz)", "Produce", "3.49", "0.30", 25, 5, True),
    ("Russet Potatoes (5 lb bag)", "Produce", "4.49", "5.00", 20, 5, True),
    ("Free-Range Eggs (dozen)", "Dairy", "6.49", "1.60", 18, 5, True),
    ("Whole Milk (half gallon)", "Dairy", "4.99", "4.30", 4, 5, True),
    ("Sourdough Loaf", "Bakery", "5.50", "1.20", 12, 5, True),
    ("Rolled Oats (2 lb)", "Pantry", "4.25", "2.00", 50, 5, True),
    ("Olive Oil (500 ml)", "Pantry", "11.99", "2.20", 15, 5, True),
    ("Organic Bananas (bunch)", "Produce", "2.49", "2.00", 60, 8, True),
    ("Avocados (4 count)", "Produce", "5.99", "1.80", 30, 6, True),
    ("Carrots (2 lb bag)", "Produce", "3.29", "2.00", 35, 6, True),
    ("Roma Tomatoes (1 lb)", "Produce", "2.99", "1.00", 28, 6, True),
    ("Lemons (2 lb bag)", "Produce", "4.49", "2.00", 22, 5, True),
    ("Yellow Onions (3 lb bag)", "Produce", "3.99", "3.00", 26, 5, True),
    ("Blueberries (6 oz)", "Produce", "4.99", "0.50", 3, 5, True),
    ("Greek Yogurt (32 oz)", "Dairy", "5.99", "2.20", 24, 5, True),
    ("Butter (1 lb)", "Dairy", "5.49", "1.00", 20, 5, True),
    ("Cheddar Block (8 oz)", "Dairy", "4.79", "0.60", 18, 5, True),
    ("Oat Milk (64 oz)", "Dairy", "4.29", "4.40", 16, 5, True),
    ("Whole Wheat Bread", "Bakery", "4.99", "1.30", 14, 5, True),
    ("Bagels (6 count)", "Bakery", "4.49", "1.00", 10, 5, True),
    ("Butter Croissants (4 count)", "Bakery", "6.99", "0.70", 0, 5, True),
    ("Brown Rice (2 lb)", "Pantry", "4.99", "2.00", 30, 5, True),
    ("Black Beans (15 oz can)", "Pantry", "1.79", "1.00", 80, 10, True),
    ("Spaghetti (1 lb)", "Pantry", "2.49", "1.00", 60, 10, True),
    ("Peanut Butter (16 oz)", "Pantry", "5.99", "1.20", 25, 5, True),
    ("Maple Syrup (12 oz)", "Pantry", "9.99", "1.60", 12, 5, True),
    ("Marinara Sauce (24 oz)", "Pantry", "4.49", "1.60", 22, 5, True),
    ("Sea Salt (26 oz)", "Pantry", "3.49", "1.00", 20, 5, True),
    (WATER, "Beverages", "8.99", "26.00", 30, 5, True),
    ("Sparkling Water (12 pack)", "Beverages", "6.99", "10.00", 20, 5, True),
    ("Orange Juice (52 oz)", "Beverages", "5.99", "3.60", 16, 5, True),
    ("Cold Brew Coffee (32 oz)", "Beverages", "7.49", "2.40", 14, 5, True),
    ("Green Tea (20 bags)", "Beverages", "4.99", "0.40", 30, 5, True),
    ("Dark Chocolate Bar", "Snacks", "3.99", "0.20", 45, 8, True),
    ("Almonds (16 oz)", "Snacks", "9.49", "1.10", 18, 5, True),
    ("Trail Mix (14 oz)", "Snacks", "6.49", "0.90", 20, 5, True),
    ("Pumpkin Soup (discontinued)", "Pantry", "5.99", "1.50", 0, 5, False),
]

# Product name -> quantity in customer@example.com's saved cart.
DEMO_CART = {
    "Organic Gala Apples (3 lb bag)": 1,
    "Baby Spinach (5 oz)": 2,
    "Free-Range Eggs (dozen)": 1,
}

HISTORY_DAYS = 14
FAILURE_REASONS = ["Recipient not available", "Could not find the entrance", "Delivery refused"]


def _money(value):
    return Decimal(value).quantize(Decimal("0.01"))


def _utc(dt):
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


class _History:
    """Collects everything for one build so the pieces can refer to each other."""

    def __init__(self, now):
        self.now = now
        self.rng = random.Random(160)
        self.users = {u.email: u for u in User.query.all()}
        self.customers = [u for u in self.users.values() if u.role == "customer"]
        self.customers.sort(key=lambda u: u.id)
        self.manager = self.users["manager@example.com"]
        self.products = {p.name: p for p in Product.query.all()}
        self.stock_events = []   # (when, product, change, reason, user_id, order, note)
        self.counter = 0
        self.all_orders = []

    # ---- orders ----------------------------------------------------------------------------

    @staticmethod
    def _float_exact(lines):
        """SQLite stores money as floating point, so its total = subtotal + fee check can fail on
        baskets like 54.77 + 10.00. PostgreSQL is exact. Only use baskets that pass on both."""
        subtotal = sum((p.price * qty for p, qty in lines), Decimal("0"))
        weight = sum((p.weight_lb * qty for p, qty in lines), Decimal("0"))
        fee = Decimal(Config.DELIVERY_FEE_AMOUNT) if weight >= Config.DELIVERY_FEE_THRESHOLD_LB else Decimal("0")
        return float(_money(subtotal)) + float(_money(fee)) == float(_money(subtotal + fee))

    def _basket(self, heavy=False):
        """A float-safe basket (see above), drawn at random."""
        for _ in range(100):
            lines = self._draw_basket(heavy)
            if self._float_exact(lines):
                return lines
        raise RuntimeError("could not draw a basket with exact totals")

    def _draw_basket(self, heavy=False):
        """A list of (product, quantity). `heavy` adds a water case so the order reaches 20 lb."""
        sellable = [p for p in self.products.values()
                    if p.active and p.name != WATER and DESIRED[p.name] >= 10]
        lines = []
        for p in self.rng.sample(sellable, self.rng.randint(2, 6)):
            lines.append((p, self.rng.randint(1, 3)))
        if heavy:
            lines.append((self.products[WATER], self.rng.randint(1, 2)))
        return lines

    def make_order(self, customer, when, lines, status, address_index=None):
        """Create an Order + lines + a succeeded Payment, with totals by the business rules."""
        if address_index is None:
            address_index = CUSTOMER_ADDRESS_INDEX.get(customer.email, 0)
        line1, postal, lat, lng = ADDRESSES[address_index]
        subtotal = sum((p.price * qty for p, qty in lines), Decimal("0"))
        weight = sum((p.weight_lb * qty for p, qty in lines), Decimal("0"))
        fee = Decimal(Config.DELIVERY_FEE_AMOUNT) if weight >= Config.DELIVERY_FEE_THRESHOLD_LB else Decimal("0")
        order = Order(
            user_id=customer.id, status=status, subtotal=_money(subtotal), delivery_fee=_money(fee),
            total=_money(subtotal + fee), weight_lb=weight,
            delivery_address=f"{line1}, San Jose, CA {postal}", delivery_lat=lat, delivery_lng=lng,
            created_at=when, updated_at=when,
        )
        for p, qty in lines:
            order.lines.append(OrderLine(
                product_id=p.product_id, name=p.name, unit_price=p.price, weight_lb=p.weight_lb, quantity=qty))
            self.stock_events.append((when, p, -qty, inventory.SALE, customer.id, order, None))
        db.session.add(order)
        self.counter += 1
        order._payment = Payment(
            user_id=customer.id, idempotency_key=f"demo-{self.counter:04d}",
            stripe_payment_intent_id=f"pi_demo_{self.counter:04d}", amount_cents=int(order.total * 100),
            currency="usd", status=SUCCEEDED, delivery_address=order.delivery_address,
            delivery_lat=lat, delivery_lng=lng, created_at=when, updated_at=when)
        db.session.add(order._payment)
        self.all_orders.append(order)
        return order

    # ---- trips -----------------------------------------------------------------------------

    def _fits(self, trip_orders, order):
        if len(trip_orders) >= Config.TRIP_MAX_ORDERS:
            return False
        if sum((o.weight_lb for o in trip_orders), Decimal("0")) + order.weight_lb > Config.TRIP_MAX_WEIGHT_LB:
            return False
        return all(distance_km(order.delivery_lat, order.delivery_lng, o.delivery_lat, o.delivery_lng)
                   <= Config.TRIP_GROUP_RADIUS_KM for o in trip_orders)

    def _route(self, orders):
        """Nearest-neighbour order of stops starting at the store."""
        left, route, here = list(orders), [], STORE
        while left:
            nxt = min(left, key=lambda o: distance_km(here[0], here[1], o.delivery_lat, o.delivery_lng))
            route.append(nxt)
            left.remove(nxt)
            here = (nxt.delivery_lat, nxt.delivery_lng)
        return route

    def group_into_trips(self, orders):
        """Same grouping rules as the live system: within 0.5 km of each other, placed within 30 min."""
        trips = []  # list of (oldest_created_at, [orders])
        for order in sorted(orders, key=lambda o: o.created_at):
            for entry in trips:
                oldest, members = entry
                if (order.created_at - oldest <= timedelta(minutes=Config.TRIP_DISPATCH_TIMEOUT_MIN)
                        and self._fits(members, order)):
                    members.append(order)
                    break
            else:
                trips.append((order.created_at, [order]))
        return [members for _, members in trips]

    def completed_trip(self, members, robot, fail_order=None):
        """A finished run: dispatched 30 min after its oldest Order, every stop delivered (or failed)."""
        oldest = min(o.created_at for o in members)
        dispatched = oldest + timedelta(minutes=Config.TRIP_DISPATCH_TIMEOUT_MIN)
        route = self._route(members)
        trip = Trip(status=COMPLETED, created_at=oldest, ready_at=dispatched, ready_reason="deadline",
                    dispatched_at=dispatched, robot=robot, estimated_duration_minutes=10 + 7 * len(route))
        db.session.add(trip)
        clock = dispatched
        here = STORE
        for number, order in enumerate(route, start=1):
            clock += timedelta(minutes=max(4, round(distance_km(here[0], here[1], order.delivery_lat,
                                                                  order.delivery_lng) * 7)))
            estimated = clock
            # about 85% of deliveries arrive on or before the estimate (that is what the on-time report counts)
            offset = self.rng.randint(-3, 0) if self.rng.random() < 0.85 else self.rng.randint(1, 5)
            arrived = estimated + timedelta(minutes=offset)
            failed = order is fail_order
            done = arrived + timedelta(minutes=2)
            trip.stops.append(TripStop(
                stop_number=number, latitude=order.delivery_lat, longitude=order.delivery_lng,
                estimated_arrival=estimated, arrived_at=arrived, completed_at=done,
                status="delivery_failed" if failed else "delivered",
                failure_reason=self.rng.choice(FAILURE_REASONS) if failed else None))
            trip.stops[-1].order = order
            order.trip = trip
            order.status = DELIVERY_FAILED if failed else DELIVERED
            order.updated_at = done
            clock = done
            here = (order.delivery_lat, order.delivery_lng)
        trip.completed_at = clock + timedelta(minutes=8)
        return trip


def build_history(now=None):
    """Write the robots, past orders, payments, trips and inventory log. Returns a short summary."""
    if Order.query.count() > 0:
        return "orders already exist: left them alone"
    now = now or datetime.now(timezone.utc)
    h = _History(now)
    day = lambda n, hour, minute=0: (now - timedelta(days=n)).replace(  # noqa: E731
        hour=hour, minute=minute, second=0, microsecond=0)

    # Addresses saved on each customer's account.
    for email, index in CUSTOMER_ADDRESS_INDEX.items():
        user = h.users[email]
        if Address.query.filter_by(user_id=user.id).first() is None:
            line1, postal, lat, lng = ADDRESSES[index]
            db.session.add(Address(
                user_id=user.id, line1=line1, city="San Jose", state="CA", postal_code=postal,
                formatted_address=f"{line1}, San Jose, CA {postal}", latitude=lat, longitude=lng,
                in_delivery_zone=True, is_default=True))

    # The fleet: seed_demo.py creates OFS-R1..R3 parked at the store. Past trips are spread across
    # the first two; OFS-R1 is also the one out on the live trip below.
    fleet = {}
    for code in (robot_code(1), robot_code(2), robot_code(3)):
        fleet[code] = Robot.query.filter_by(robot_code=code).first() or Robot(robot_code=code)
        fleet[code].status = "available"
        fleet[code].current_latitude, fleet[code].current_longitude = STORE
        db.session.add(fleet[code])
    robot1, robot2 = fleet[robot_code(1)], fleet[robot_code(2)]

    # --- history: delivered orders in clusters of 1-3 per delivery window, two or three a day ---
    delivered = []
    for n in range(HISTORY_DAYS, 0, -1):
        for hour in h.rng.sample([17, 18, 19, 20, 21, 22, 23], h.rng.randint(2, 3)):  # 9am-4pm Pacific
            start = day(n, hour, h.rng.choice([0, 10, 20]))
            for k in range(h.rng.randint(1, 3)):
                customer = h.customers[0] if len(delivered) % 5 == 0 else h.rng.choice(h.customers)
                heavy = h.rng.random() < 0.2
                delivered.append(h.make_order(
                    customer, start + timedelta(minutes=4 * k), h._basket(heavy), DELIVERED,
                    address_index=h.rng.randrange(len(ADDRESSES))))
    failed = [delivered[len(delivered) // 4], delivered[len(delivered) // 2], delivered[-6]]
    robots = [robot1, robot2]
    for index, members in enumerate(h.group_into_trips(delivered)):
        fail = next((o for o in members if o in failed), None)
        h.completed_trip(members, robots[index % 2], fail_order=fail)

    audits = []
    # --- cancelled by a Manager (override with a reason, stock goes back, payment refunded) ---
    for n, reason in ((9, "Customer called to cancel before packing"), (4, "Item recalled by supplier")):
        order = h.make_order(h.rng.choice(h.customers), day(n, 11, 30), h._basket(), CANCELLED)
        order._payment.status = REFUNDED
        when = order.created_at + timedelta(minutes=12)
        order.updated_at = when
        for line in order.lines:
            h.stock_events.append((when, h.products[line.name], line.quantity, inventory.CANCEL,
                                   h.manager.id, order, reason))
        audits.append((order, OrderOverrideAudit(
            manager_id=h.manager.id, action="cancel", previous_status=PLACED,
            new_status=CANCELLED, reason=reason, created_at=when)))

    # --- too heavy for a Robot (over 200 lb): waits in Manual Review ---
    over_limit = [(h.products[WATER], 9)]
    assert h._float_exact(over_limit), "the over-200 lb demo basket must have exact totals"
    h.make_order(h.customers[2], day(2, 15, 5), over_limit, MANUAL_REVIEW, address_index=3)

    # --- live orders, relative to now, so the dashboards have work in every state ---
    c = h.customers
    cases = h._basket

    # Out for delivery on OFS-R1, a few minutes into its run.
    out = [h.make_order(c[0], now - timedelta(minutes=52), cases(), OUT_FOR_DELIVERY, address_index=0),
           h.make_order(c[1], now - timedelta(minutes=48), cases(), OUT_FOR_DELIVERY, address_index=2)]
    route = h._route(out)
    trip = Trip(status=DISPATCHED, created_at=now - timedelta(minutes=52), ready_at=now - timedelta(minutes=22),
                ready_reason="deadline", dispatched_at=now - timedelta(minutes=16), robot=robot1,
                estimated_duration_minutes=24)
    db.session.add(trip)
    clock = now - timedelta(minutes=16)
    for number, order in enumerate(route, start=1):
        clock += timedelta(minutes=8)
        trip.stops.append(TripStop(stop_number=number, latitude=order.delivery_lat,
                                   longitude=order.delivery_lng, estimated_arrival=clock, status="pending"))
        trip.stops[-1].order = order
        order.trip = trip
    first = route[0]
    # The route the Dispatch and Track maps draw: store -> each stop in order -> back to the store.
    trip.route_geometry = {"type": "LineString",
                           "coordinates": [[STORE[1], STORE[0]]]
                                          + [[o.delivery_lng, o.delivery_lat] for o in route]
                                          + [[STORE[1], STORE[0]]]}
    robot1.status = "out_for_delivery"
    robot1.current_latitude = round((STORE[0] + first.delivery_lat) / 2, 6)
    robot1.current_longitude = round((STORE[1] + first.delivery_lng) / 2, 6)

    # Locked and waiting for an Employee to Dispatch (oldest order is past 30 minutes).
    ready = [h.make_order(c[2], now - timedelta(minutes=39), cases(), PLANNED, address_index=3),
             h.make_order(c[3], now - timedelta(minutes=34), cases(), PLANNED, address_index=4)]
    ready_trip = Trip(status=READY, created_at=now - timedelta(minutes=39), ready_at=now - timedelta(minutes=9),
                      ready_reason="deadline")
    db.session.add(ready_trip)
    for order in ready:
        order.trip = ready_trip

    # Prepared, still taking more orders.
    prep = [h.make_order(c[4], now - timedelta(minutes=14), cases(), PLANNED, address_index=6),
            h.make_order(c[0], now - timedelta(minutes=10), cases(), PLANNED, address_index=6)]
    open_trip = Trip(status=OPEN, created_at=now - timedelta(minutes=14))
    db.session.add(open_trip)
    for order in prep:
        order.trip = open_trip

    # Just placed: waiting in the Preparation Queue.
    for minutes, customer, index in ((7, c[1], 1), (4, c[3], 4), (2, c[0], 0)):
        h.make_order(customer, now - timedelta(minutes=minutes), cases(), PLACED, address_index=index)

    # --- manager stock edits on top of the sales ---
    eggs, yogurt = h.products["Free-Range Eggs (dozen)"], h.products["Greek Yogurt (32 oz)"]
    h.stock_events.append((day(HISTORY_DAYS, 9), yogurt, 10, inventory.RESTOCK, h.manager.id, None,
                           "Weekly dairy delivery"))
    h.stock_events.append((day(6, 9), eggs, -2, inventory.CORRECTION, h.manager.id, None,
                           "Broken in storage"))

    db.session.flush()   # orders now have ids
    for order in h.all_orders:
        order._payment.order_id = order.id
    for order, audit in audits:
        audit.order_id = order.id
        db.session.add(audit)
    _write_inventory_log(h)
    db.session.commit()

    counts = {}
    for order in h.all_orders:
        counts[order.status] = counts.get(order.status, 0) + 1
    return "created " + ", ".join(f"{n} {s}" for s, n in sorted(counts.items()))


DESIRED = {name: stock for name, _, _, _, stock, _, _ in DEMO_PRODUCTS}


def _write_inventory_log(h):
    """Replay every stock change in time order, so each log row's before/after is consistent and the
    final Stock equals the figure in DEMO_PRODUCTS. An opening RESTOCK row starts each product."""
    by_product = {}
    for event in h.stock_events:
        by_product.setdefault(event[1].product_id, []).append(event)
    opening_time = min(e[0] for e in h.stock_events) - timedelta(days=1)

    for product in h.products.values():
        events = sorted(by_product.get(product.product_id, []), key=lambda e: e[0])
        target = DESIRED[product.name]
        opening = target - sum(e[2] for e in events)
        running, low = opening, opening
        for e in events:
            running += e[2]
            low = min(low, running)
        if low < 0:  # never let Stock dip below zero: start with more, end with more
            opening -= low
        product.stock_qty = 0
        if opening > 0:
            entry = inventory.change_stock(product, opening, inventory.RESTOCK, user_id=h.manager.id,
                                           note="Opening stock")
            entry.created_at = opening_time
        for when, _, change, reason, user_id, order, note in events:
            entry = inventory.change_stock(product, change, reason, user_id=user_id, order=order, note=note)
            entry.created_at = when
