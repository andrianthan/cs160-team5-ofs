"""Complete database foundation

Revision ID: 0002_foundation
Revises: 0001_baseline
Create Date: 2026-11-04 15:24:07.753813

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0002_foundation'
down_revision = '0001_baseline'
branch_labels = None
depends_on = None


# Alembic does not autogenerate changes to existing CHECK constraints.
EXISTING_CHECKS = {'users': [('ck_users_role', "role IN ('customer','employee','manager')")],
 'products': [('ck_products_price', 'price >= 0'),
              ('ck_products_stock', 'stock_qty >= 0'),
              ('ck_products_threshold', 'low_stock_threshold >= 0'),
              ('ck_products_weight', 'weight_lb > 0')],
 'cart_lines': [('ck_cart_lines_quantity', 'quantity > 0')],
 'orders': [('ck_orders_status',
             'status IN '
             "('placed','planned','out_for_delivery','delivered','delivery_failed','manual_review','cancelled')"),
            ('ck_orders_totals',
             'subtotal >= 0 AND delivery_fee IN (0,10) AND total = subtotal + delivery_fee'),
            ('ck_orders_weight', 'weight_lb > 0')],
 'order_lines': [('ck_order_lines_quantity', 'quantity > 0'),
                 ('ck_order_lines_snapshot', 'unit_price >= 0 AND weight_lb > 0')],
 'payments': [('ck_payments_amount', 'amount_cents >= 0'),
              ('ck_payments_status',
               "status IN ('pending','succeeded','failed','canceled','refunded')")],
 'trips': [('ck_trips_duration', 'estimated_duration_minutes >= 0'),
           ('ck_trips_status', "status IN ('open','dispatched','completed')")]}


def upgrade():
    # Reviewed migration; retains the existing API column names.
    op.create_table('robots',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('robot_code', sa.String(length=24), nullable=False),
    sa.Column('status', sa.String(length=24), server_default='available', nullable=False),
    sa.Column('current_latitude', sa.Numeric(precision=9, scale=6), nullable=True),
    sa.Column('current_longitude', sa.Numeric(precision=9, scale=6), nullable=True),
    sa.Column('max_order_count', sa.SmallInteger(), server_default='10', nullable=False),
    sa.Column('max_weight_lb', sa.Numeric(precision=8, scale=2), server_default='200', nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.CheckConstraint("status IN ('available','reserved','loading','out_for_delivery','returning','offline')", name='ck_robots_status'),
    sa.CheckConstraint('current_latitude BETWEEN -90 AND 90', name='ck_robots_latitude'),
    sa.CheckConstraint('current_longitude BETWEEN -180 AND 180', name='ck_robots_longitude'),
    sa.CheckConstraint('max_order_count = 10 AND max_weight_lb = 200', name='ck_robots_capacity'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('robot_code')
    )
    with op.batch_alter_table('robots', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_robots_status'), ['status'], unique=False)

    op.create_table('addresses',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('line1', sa.String(length=150), nullable=False),
    sa.Column('line2', sa.String(length=150), nullable=True),
    sa.Column('city', sa.String(length=80), nullable=False),
    sa.Column('state', sa.String(length=2), server_default='CA', nullable=False),
    sa.Column('postal_code', sa.String(length=12), nullable=False),
    sa.Column('formatted_address', sa.Text(), nullable=False),
    sa.Column('latitude', sa.Numeric(precision=9, scale=6), nullable=False),
    sa.Column('longitude', sa.Numeric(precision=9, scale=6), nullable=False),
    sa.Column('in_delivery_zone', sa.Boolean(), server_default=sa.false(), nullable=False),
    sa.Column('is_default', sa.Boolean(), server_default=sa.false(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.CheckConstraint('latitude BETWEEN -90 AND 90', name='ck_addresses_latitude'),
    sa.CheckConstraint('longitude BETWEEN -180 AND 180', name='ck_addresses_longitude'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('addresses', schema=None) as batch_op:
        batch_op.create_index('ix_addresses_user_default', ['user_id', 'is_default'], unique=False)

    op.create_table('app_settings',
    sa.Column('setting_key', sa.String(length=64), nullable=False),
    sa.Column('setting_value', sa.JSON().with_variant(postgresql.JSONB(), 'postgresql'), nullable=False),
    sa.Column('updated_by', sa.Integer(), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.ForeignKeyConstraint(['updated_by'], ['users.id'], ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('setting_key')
    )
    op.create_table('inventory_log',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('product_id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('order_id', sa.Integer(), nullable=True),
    sa.Column('before_qty', sa.Integer(), nullable=False),
    sa.Column('change_qty', sa.Integer(), nullable=False),
    sa.Column('after_qty', sa.Integer(), nullable=False),
    sa.Column('reason', sa.String(length=32), nullable=False),
    sa.Column('note', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.CheckConstraint("reason IN ('SALE','RESTOCK','RETURN','CORRECTION','CANCEL')", name='ck_inventory_reason'),
    sa.CheckConstraint('after_qty = before_qty + change_qty', name='ck_inventory_balance'),
    sa.CheckConstraint('before_qty >= 0 AND after_qty >= 0', name='ck_inventory_quantities'),
    sa.CheckConstraint('change_qty != 0', name='ck_inventory_change'),
    sa.ForeignKeyConstraint(['order_id'], ['orders.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['product_id'], ['products.product_id'], ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('inventory_log', schema=None) as batch_op:
        batch_op.create_index('ix_inventory_product_created', ['product_id', 'created_at'], unique=False)

    op.create_table('trip_stops',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('trip_id', sa.Integer(), nullable=False),
    sa.Column('order_id', sa.Integer(), nullable=False),
    sa.Column('stop_number', sa.SmallInteger(), nullable=False),
    sa.Column('latitude', sa.Numeric(precision=9, scale=6), nullable=False),
    sa.Column('longitude', sa.Numeric(precision=9, scale=6), nullable=False),
    sa.Column('estimated_arrival', sa.DateTime(timezone=True), nullable=True),
    sa.Column('arrived_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('status', sa.String(length=20), server_default='pending', nullable=False),
    sa.Column('failure_reason', sa.Text(), nullable=True),
    sa.CheckConstraint("status IN ('pending','arrived','delivered','delivery_failed')", name='ck_trip_stops_status'),
    sa.CheckConstraint('latitude BETWEEN -90 AND 90', name='ck_trip_stops_latitude'),
    sa.CheckConstraint('longitude BETWEEN -180 AND 180', name='ck_trip_stops_longitude'),
    sa.CheckConstraint('stop_number BETWEEN 1 AND 10', name='ck_trip_stops_number'),
    sa.ForeignKeyConstraint(['order_id'], ['orders.id'], ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['trip_id'], ['trips.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('order_id'),
    sa.UniqueConstraint('trip_id', 'stop_number', name='uq_trip_stops_sequence')
    )
    with op.batch_alter_table('cart_lines', schema=None) as batch_op:
        batch_op.create_index('ix_cart_lines_product', ['product_id'], unique=False)

    with op.batch_alter_table('order_lines', schema=None) as batch_op:
        batch_op.create_index('ix_order_lines_order', ['order_id'], unique=False)
        batch_op.create_index('ix_order_lines_product', ['product_id'], unique=False)

    with op.batch_alter_table('orders', schema=None) as batch_op:
        batch_op.create_index('ix_orders_status_created', ['status', 'created_at'], unique=False)
        batch_op.create_index('ix_orders_user_created', ['user_id', 'created_at'], unique=False)

    with op.batch_alter_table('payments', schema=None) as batch_op:
        batch_op.create_unique_constraint('uq_payments_order_id', ['order_id'])
        batch_op.create_foreign_key('fk_payments_order_id', 'orders', ['order_id'], ['id'], ondelete='RESTRICT')

    with op.batch_alter_table('products', schema=None) as batch_op:
        batch_op.create_index('ix_products_active_category_name', ['active', 'category', 'name'], unique=False)

    with op.batch_alter_table('trips', schema=None) as batch_op:
        batch_op.add_column(sa.Column('robot_id', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('route_geometry', sa.JSON().with_variant(postgresql.JSONB(), 'postgresql'), nullable=True))
        batch_op.add_column(sa.Column('estimated_duration_minutes', sa.Integer(), nullable=True))
        batch_op.create_index(batch_op.f('ix_trips_robot_id'), ['robot_id'], unique=False)
        batch_op.create_index('ix_trips_status_created', ['status', 'created_at'], unique=False)
        batch_op.create_foreign_key('fk_trips_robot_id', 'robots', ['robot_id'], ['id'], ondelete='SET NULL')

    for table, checks in EXISTING_CHECKS.items():
        with op.batch_alter_table(table) as batch_op:
            for name, sql in checks:
                batch_op.create_check_constraint(name, sql)


def downgrade():
    for table, checks in reversed(list(EXISTING_CHECKS.items())):
        with op.batch_alter_table(table) as batch_op:
            for name, sql in checks:
                batch_op.drop_constraint(name, type_="check")
    # Reviewed migration; retains the existing API column names.
    with op.batch_alter_table('trips', schema=None) as batch_op:
        batch_op.drop_constraint('fk_trips_robot_id', type_='foreignkey')
        batch_op.drop_index('ix_trips_status_created')
        batch_op.drop_index(batch_op.f('ix_trips_robot_id'))
        batch_op.drop_column('estimated_duration_minutes')
        batch_op.drop_column('route_geometry')
        batch_op.drop_column('robot_id')

    with op.batch_alter_table('products', schema=None) as batch_op:
        batch_op.drop_index('ix_products_active_category_name')

    with op.batch_alter_table('payments', schema=None) as batch_op:
        batch_op.drop_constraint('fk_payments_order_id', type_='foreignkey')
        batch_op.drop_constraint('uq_payments_order_id', type_='unique')

    with op.batch_alter_table('orders', schema=None) as batch_op:
        batch_op.drop_index('ix_orders_user_created')
        batch_op.drop_index('ix_orders_status_created')

    with op.batch_alter_table('order_lines', schema=None) as batch_op:
        batch_op.drop_index('ix_order_lines_product')
        batch_op.drop_index('ix_order_lines_order')

    with op.batch_alter_table('cart_lines', schema=None) as batch_op:
        batch_op.drop_index('ix_cart_lines_product')

    op.drop_table('trip_stops')
    with op.batch_alter_table('inventory_log', schema=None) as batch_op:
        batch_op.drop_index('ix_inventory_product_created')

    op.drop_table('inventory_log')
    op.drop_table('app_settings')
    with op.batch_alter_table('addresses', schema=None) as batch_op:
        batch_op.drop_index('ix_addresses_user_default')

    op.drop_table('addresses')
    with op.batch_alter_table('robots', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_robots_status'))

    op.drop_table('robots')
