"""Create the tables (via migrations) plus demo users, products, and a saved customer cart.

Uses DATABASE_URL from backend/.env, like run.py does; a DATABASE_URL set in the terminal wins:
    python seed_demo.py                                   # whatever .env points at
    DATABASE_URL=sqlite:///demo.db python seed_demo.py    # one-off local SQLite

Add --with-orders for a week of Orders and completed Trips, so the Reports page has
on-time rate, delivery duration and trip utilization to show:
    python seed_demo.py --with-orders
"""
import argparse
import sys
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

import sqlalchemy as sa
from dotenv import load_dotenv
from flask_migrate import upgrade

# Read backend/.env before importing the app: Config reads DATABASE_URL when it's imported.
load_dotenv(Path(__file__).resolve().parent / ".env")

from app import create_app  # noqa: E402
from app.extensions import db  # noqa: E402
from app.models import Cart, CartLine, Order, OrderLine, Product, Robot, Trip, TripStop, User  # noqa: E402

DEMO_USERS = [
    ("customer@example.com", "Casey Customer", "customer", "customer123"),
    ("employee@example.com", "Eli Employee", "employee", "employee123"),
    ("manager@example.com", "Maya Manager", "manager", "manager123"),
]

DEMO_PRODUCTS = [
    ("Organic Gala Apples (3 lb bag)", "Produce", "5.99", "3.00", 40),
    ("Baby Spinach (5 oz)", "Produce", "3.49", "0.30", 25),
    ("Russet Potatoes (5 lb bag)", "Produce", "4.49", "5.00", 20),
    ("Free-Range Eggs (dozen)", "Dairy", "6.49", "1.60", 18),
    ("Whole Milk (half gallon)", "Dairy", "4.99", "4.30", 4),
    ("Sourdough Loaf", "Bakery", "5.50", "1.20", 12),
    ("Rolled Oats (2 lb)", "Pantry", "4.25", "2.00", 50),
    ("Olive Oil (500 ml)", "Pantry", "11.99", "2.20", 15),
]

# Product name -> quantity in customer@example.com's saved cart.
DEMO_CART = {
    "Organic Gala Apples (3 lb bag)": 1,
    "Baby Spinach (5 oz)": 2,
    "Free-Range Eggs (dozen)": 1,
}

MIGRATIONS = Path(__file__).resolve().parent / "migrations"

# A week of Orders and the Trips that delivered them, so the Reports page has real
# on-time rate, delivery duration and trip utilization instead of nulls.
# product index, quantity, status, days ago, trip index, minutes late vs the ETA
DEMO_ORDERS = [
    (0, 3, "delivered", 1, 0, -3),
    (1, 2, "delivered", 1, 0, 2),
    (3, 2, "delivered", 2, 1, -1),
    (2, 4, "delivery_failed", 3, 2, None),
    (5, 1, "placed", 3, None, None),
    (6, 5, "cancelled", 3, None, None),
    (7, 2, "delivered", 6, 3, 5),
    (4, 1, "delivered", 5, 3, -2),
]

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument(
    "--with-orders",
    action="store_true",
    help="also seed a week of Orders and completed Trips, so the Reports page has numbers",
)
args = parser.parse_args()

def seed_orders(customer_id, products, robots):
    """Seed a week of Orders plus the Trips that delivered them.

    The Trips carry estimated_arrival and arrived_at on their stops, and those are what
    the Reports page reads for on-time rate and delivery duration. Without them both
    metrics are null until a live dispatch happens, so a demo that misses the dispatch
    shows an empty report.
    """
    if Order.query.count():
        print(f"Orders already seeded: {Order.query.count()}")
        return

    orders = []
    for pi, qty, status, days_ago, _trip, _late in DEMO_ORDERS:
        p = products[pi]
        subtotal = p.price * qty
        fee = Decimal("10.00") if p.weight_lb * qty >= 20 else Decimal("0")
        o = Order(
            user_id=customer_id,
            status=status,
            subtotal=subtotal,
            delivery_fee=fee,
            total=subtotal + fee,
            weight_lb=p.weight_lb * qty,
            delivery_address="200 East Santa Clara Street, San Jose",
            delivery_lat=37.3377,
            delivery_lng=-121.8858,
            created_at=datetime.now(timezone.utc) - timedelta(days=days_ago),
        )
        o.lines.append(OrderLine(product_id=p.product_id, name=p.name, unit_price=p.price,
                                  weight_lb=p.weight_lb, quantity=qty))
        db.session.add(o)
        orders.append(o)
    db.session.flush()

    trips, stop_numbers = {}, {}
    for idx, (_pi, _qty, status, _days, trip_idx, late) in enumerate(DEMO_ORDERS):
        if trip_idx is None:
            continue
        o = orders[idx]
        trip = trips.get(trip_idx)
        if trip is None:
            dispatched = o.created_at + timedelta(minutes=2)
            trip = Trip(
                status="completed",
                created_at=o.created_at,
                dispatched_at=dispatched,
                completed_at=dispatched + timedelta(minutes=35),
                estimated_duration_minutes=18,
                robot_id=robots[trip_idx % len(robots)].id if robots else None,
            )
            db.session.add(trip)
            db.session.flush()
            trips[trip_idx] = trip
            stop_numbers[trip_idx] = 0
        o.trip_id = trip.id

        stop_numbers[trip_idx] += 1
        stop = TripStop(
            trip_id=trip.id,
            order_id=o.id,
            stop_number=stop_numbers[trip_idx],
            latitude=37.3377,
            longitude=-121.8858,
            estimated_arrival=o.created_at + timedelta(minutes=14),
        )
        if status == "delivered":
            stop.arrived_at = stop.estimated_arrival + timedelta(minutes=late)
            stop.completed_at = stop.arrived_at + timedelta(minutes=1)
            stop.status = "delivered"
        else:
            stop.status = "delivery_failed"
            stop.failure_reason = "Nobody was home to take the delivery."
        db.session.add(stop)

    db.session.commit()
    print(f"Seeded {Order.query.count()} Orders across {Trip.query.count()} Trips.")


app = create_app()
print(f"Seeding {sa.engine.make_url(app.config['SQLALCHEMY_DATABASE_URI']).render_as_string(hide_password=True)}")
with app.app_context():
    # Build the schema through the migrations, not db.create_all(): that leaves the database
    # versioned (alembic_version), so a later `flask db upgrade` applies only what's new.
    tables = set(sa.inspect(db.engine).get_table_names())
    if tables and "alembic_version" not in tables:
        # Made by the old create_all() seed: it has tables but no version, so migrating would fail
        # with "table already exists". Demo data is disposable, so recreating it is the simple fix.
        sys.exit(
            f"{db.engine.url.database} was created before migrations existed.\n"
            "Delete it (or move it aside) and run seed_demo.py again. See docs/database.md."
        )
    upgrade(directory=str(MIGRATIONS))

    users = {}
    for email, name, role, password in DEMO_USERS:
        user = User.query.filter_by(email=email).first()
        if user is None:
            user = User(email=email, name=name, role=role)
            user.set_password(password)
            db.session.add(user)
        users[email] = user

    for name, category, price, weight_lb, stock_qty in DEMO_PRODUCTS:
        product = Product.query.filter_by(name=name).first()
        if product is None:
            db.session.add(
                Product(
                    name=name,
                    category=category,
                    price=Decimal(price),
                    weight_lb=Decimal(weight_lb),
                    stock_qty=stock_qty,
                )
            )

    for n in range(1, 4):  # the demo fleet, parked at the store
        code = f"ROBOT-{n:02d}"
        if Robot.query.filter_by(robot_code=code).first() is None:
            db.session.add(Robot(robot_code=code, status="available",
                                 current_latitude=app.config["STORE_LAT"],
                                 current_longitude=app.config["STORE_LNG"]))

    db.session.commit()

    customer = users["customer@example.com"]
    cart = Cart.query.filter_by(user_id=customer.id).first()
    if cart is None:
        cart = Cart(user_id=customer.id)
        db.session.add(cart)
        db.session.flush()

    # Rebuild the demo lines so changing DEMO_CART remains repeatable.
    for line in list(cart.lines):
        db.session.delete(line)
    db.session.flush()

    for product_name, quantity in DEMO_CART.items():
        product = Product.query.filter_by(name=product_name).one()
        db.session.add(
            CartLine(
                cart_id=cart.id,
                product_id=product.product_id,
                quantity=quantity,
            )
        )

    db.session.commit()

    print("Demo accounts (email / password):")
    for email, _, role, password in DEMO_USERS:
        print(f"  {role:<9} {email} / {password}")
    print(
        f"Created {len(DEMO_CART)} cart products for customer@example.com "
        f"(cart id {cart.id})."
    )

    if args.with_orders:
        seed_orders(customer.id, Product.query.order_by(Product.product_id).all(),
                    Robot.query.order_by(Robot.robot_code).all())
