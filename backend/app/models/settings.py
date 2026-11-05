from sqlalchemy.dialects.postgresql import JSONB

from ..extensions import db


class AppSetting(db.Model):
    __tablename__ = "app_settings"

    setting_key = db.Column(db.String(64), primary_key=True)
    setting_value = db.Column(db.JSON().with_variant(JSONB(), "postgresql"), nullable=False)
    updated_by = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"))
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, server_default=db.func.now(), onupdate=db.func.now())
