"""
export DATABASE_URL=sqlite:///demo.db
python seed_demo.py
"""
from app import create_app
from app.extensions import db
from app.models import User, Product

from decimal import Decimal

DEMO_USERS = [
    ("customer@example.com", "Casey Customer", "customer", "customer123"),
    ("employee@example.com", "Eli Employee", "employee", "employee123"),
    ("manager@example.com", "Maya Manager", "manager", "manager123"),
]

DEMO_PRODUCTS = [
    ("Organic Gala Apples (3 lb bag)", "Produce", "5.99", "3.00", 40),
    ("Baby Spinach (5 oz)", "Produce", "3.49", "0.30", 25),
    ("Russet Potatoes (5 lb bag)", "Produce", "4.49", "5.00", 0),
    ("Free-Range Eggs (dozen)", "Dairy", "6.49", "1.60", 18),
    ("Whole Milk (half gallon)", "Dairy", "4.99", "4.30", 4),
    ("Sourdough Loaf", "Bakery", "5.50", "1.20", 12),
    ("Rolled Oats (2 lb)", "Pantry", "4.25", "2.00", 50),
    ("Olive Oil (500 ml)", "Pantry", "11.99", "2.20", 15),
]

app = create_app()
with app.app_context():
    db.create_all()

    # add demo users
    for email, name, role, password in DEMO_USERS:
        if User.query.filter_by(email=email).first():
            continue
        user = User(email=email, name=name, role=role)
        user.set_password(password)
        db.session.add(user)
    
    print("Demo accounts (email / password):")
    for email, _, role, password in DEMO_USERS:
        print(f"  {role:<9} {email} / {password}")

    # add demo products
    for name, category, price, weight_lb, stock_qty in DEMO_PRODUCTS:
        if Product.query.filter_by(name=name).first():
            continue
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
