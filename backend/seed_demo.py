"""Create the tables (via migrations) plus demo users, products, and a saved customer cart.

Uses DATABASE_URL from backend/.env, like run.py does; a DATABASE_URL set in the terminal wins:
    python seed_demo.py                                   # whatever .env points at
    DATABASE_URL=sqlite:///demo.db python seed_demo.py    # one-off local SQLite
"""
import sys
from decimal import Decimal
from pathlib import Path

import sqlalchemy as sa
from dotenv import load_dotenv
from flask_migrate import upgrade

# Read backend/.env before importing the app: Config reads DATABASE_URL when it's imported.
load_dotenv(Path(__file__).resolve().parent / ".env")

from app import create_app  # noqa: E402
from app.extensions import db  # noqa: E402
from app.models import Cart, CartLine, Product, User  # noqa: E402

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
