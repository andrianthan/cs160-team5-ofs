"""Create local demo users, products, and a saved customer cart.
    export DATABASE_URL=sqlite:///demo.db
    python seed_demo.py
"""
from decimal import Decimal

from app import create_app
from app.extensions import db
from app.models import Cart, CartLine, Product, User

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

app = create_app()
with app.app_context():
    db.create_all()

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
