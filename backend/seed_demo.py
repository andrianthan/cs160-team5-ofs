"""Create the tables (via migrations) plus demo data: accounts, a full catalog, a saved customer cart,
two Robots and two weeks of order history (see demo_data.py).

Uses DATABASE_URL from backend/.env, like run.py does; a DATABASE_URL set in the terminal wins:
    python seed_demo.py                                   # whatever .env points at
    DATABASE_URL=sqlite:///demo.db python seed_demo.py    # one-off local SQLite
    python seed_demo.py --auto                            # what Docker runs when AUTO_SEED=1

It is safe to run again: accounts and products are only added when missing, and the order history
is only written to a database that has no orders yet. --auto additionally refuses to touch any
database that is not local (the shared Supabase project).
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
from demo_data import DEMO_CART, DEMO_PRODUCTS, DEMO_USERS, build_history  # noqa: E402

# Hosts --auto may seed. Anything else (Supabase, a teammate's server) is refused.
LOCAL_HOSTS = {"db", "localhost", "127.0.0.1", "::1", None}

MIGRATIONS = Path(__file__).resolve().parent / "migrations"

AUTO = "--auto" in sys.argv

app = create_app()
if AUTO:
    _url = sa.engine.make_url(app.config["SQLALCHEMY_DATABASE_URI"])
    if _url.get_backend_name() != "sqlite" and _url.host not in LOCAL_HOSTS:
        sys.exit(
            f"AUTO_SEED refused: {_url.host} is not a local database. Automatic seeding only runs against\n"
            "the bundled database container. To seed this one on purpose, run: python seed_demo.py"
        )
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

    for name, category, price, weight_lb, stock_qty, threshold, active in DEMO_PRODUCTS:
        product = Product.query.filter_by(name=name).first()
        if product is None:
            db.session.add(
                Product(
                    name=name,
                    category=category,
                    price=Decimal(price),
                    weight_lb=Decimal(weight_lb),
                    stock_qty=stock_qty,
                    low_stock_threshold=threshold,
                    active=active,
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

    print(f"Order history: {build_history()}")

    print("Demo accounts (email / password):")
    for email, _, role, password in DEMO_USERS:
        print(f"  {role:<9} {email} / {password}")
    print(
        f"Created {len(DEMO_CART)} cart products for customer@example.com "
        f"(cart id {cart.id})."
    )
