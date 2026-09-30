from datetime import datetime, timezone

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from ..extensions import db

CUSTOMER, EMPLOYEE, MANAGER = "customer", "employee", "manager"
ROLES = (CUSTOMER, EMPLOYEE, MANAGER)
STAFF_ROLES = (EMPLOYEE, MANAGER)

class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    name = db.Column(db.String(120), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default=CUSTOMER)
    created_at = db.Column(
        db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def is_staff(self):
        return self.role in STAFF_ROLES

    def to_dict(self):
        return {"id": self.id, "email": self.email, "name": self.name, "role": self.role}