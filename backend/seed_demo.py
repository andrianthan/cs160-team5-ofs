"""Demo setup: create tables and three sample accounts. Safe to re-run.

    export DATABASE_URL=sqlite:///demo.db
    python seed_demo.py

Uses db.create_all() instead of migrations, so it is for local demos only.
"""
from app import create_app
from app.extensions import db
from app.models import User

DEMO_USERS = [
    ("customer@example.com", "Casey Customer", "customer", "customer123"),
    ("employee@example.com", "Eli Employee", "employee", "employee123"),
    ("manager@example.com", "Maya Manager", "manager", "manager123"),
]

app = create_app()
with app.app_context():
    db.create_all()
    for email, name, role, password in DEMO_USERS:
        if User.query.filter_by(email=email).first():
            continue
        user = User(email=email, name=name, role=role)
        user.set_password(password)
        db.session.add(user)
    db.session.commit()
    print("Demo accounts (email / password):")
    for email, _, role, password in DEMO_USERS:
        print(f"  {role:<9} {email} / {password}")
