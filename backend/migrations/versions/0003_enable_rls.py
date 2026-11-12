"""Enable row-level security on every table

Revision ID: 0003_enable_rls
Revises: 0002_foundation
Create Date: 2026-11-11 18:30:00

Why: Supabase publishes every table through its web API (the "Data API") and lets the public
"anon" key read and write them by default. Our app never uses that API; Flask connects straight
to Postgres as the table owner. Turning RLS on with no policies makes the API see zero rows and
reject every write, while the owner (our app) is exempt from RLS and keeps full access.

Any table added later must enable RLS in its own migration too;
tests/test_database_schema.py fails on PostgreSQL if one doesn't.
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0003_enable_rls'
down_revision = '0002_foundation'
branch_labels = None
depends_on = None


def _tables():
    """Every table in the schema the app uses (including alembic_version)."""
    rows = op.get_bind().execute(sa.text("SELECT tablename FROM pg_tables WHERE schemaname = current_schema()"))
    return [r[0] for r in rows]


def upgrade():
    if op.get_bind().dialect.name != "postgresql":
        return  # SQLite (local demo.db, tests) has no RLS and no web API to protect
    for table in _tables():
        op.execute(f'ALTER TABLE "{table}" ENABLE ROW LEVEL SECURITY')


def downgrade():
    if op.get_bind().dialect.name != "postgresql":
        return
    for table in _tables():
        op.execute(f'ALTER TABLE "{table}" DISABLE ROW LEVEL SECURITY')
