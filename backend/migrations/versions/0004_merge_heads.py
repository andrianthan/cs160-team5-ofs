"""Merge Supabase RLS and T20 manager override migration heads."""

from alembic import op

revision = "0004_merge_heads"
down_revision = ("0003_enable_rls", "0003_override")
branch_labels = None
depends_on = None


def upgrade():
    if op.get_bind().dialect.name == "postgresql":
        op.execute(
            'ALTER TABLE "delivery_settings" ENABLE ROW LEVEL SECURITY'
        )
        op.execute(
            'ALTER TABLE "order_override_audits" ENABLE ROW LEVEL SECURITY'
        )


def downgrade():
    pass