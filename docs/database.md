# T02: database schema and migrations

The application has 14 tables: users, addresses, products, inventory_log, carts,
cart_lines, orders, order_lines, payments, robots, trips, trip_stops, app_settings, and notifications.
The models are registered in `backend/app/models/__init__.py`.

## Migrations

Run commands from `backend` with the virtual environment active and DATABASE_URL
set to the intended database (Flask loads `backend/.env` automatically).

```sh
flask --app app:create_app db upgrade
flask --app app:create_app db current
flask --app app:create_app db check
python seed_demo.py
```

`0001_baseline` recreates the nine application tables present on main at commit
ee31522. `0002_foundation` adds five tables, robot/route fields on trips, the payment
foreign key, named checks, and query indexes. Upgrade preserves valid existing
rows. A constraint violation stops the migration; inspect invalid records instead
of deleting them to force an upgrade.

For an existing unversioned database created with `db.create_all()`, back up first
and compare its tables, columns and constraints against `0001_baseline`. Only
when it matches that baseline should its owner run
`flask --app app:create_app db stamp 0001_baseline`, followed by `db upgrade`.
Stamp only records a revision; it does not create or repair tables. Older partial
schemas need an explicit reconciliation migration. Do not stamp `head` to hide
missing columns. The shared Supabase database has not been changed by this PR.

For future model changes, generate a revision with `db migrate -m "..."`, review
it, commit it, then apply with `db upgrade`. Alembic does not automatically detect
all CHECK changes; add them explicitly. Downgrading to the baseline drops the new
tables and their data; use it only on a backed-up/disposable database.

## Guarantees and integration boundaries

- Foreign keys connect customers, carts, products, orders, payments, trips and robots.
- Prices and weights use fixed-precision Numeric; payment amounts use integer cents.
- Order lines preserve price, weight and name snapshots after catalog changes.
- Named checks reject negative stock/prices, nonpositive quantities/weights, invalid
  statuses, inconsistent order totals and inventory-log arithmetic, invalid coordinates,
  and invalid robot capacities. Stop numbers are 1–10 and unique within a trip.
- Indexes support catalog filtering, customer/order queues, inventory history, and routes.
- Pending payments allow a null order_id; linked payments use a unique foreign key.
- InventoryLog storage is ready; T05/T12 must write sale/restock/cancel entries in the
  same transaction as stock changes. The current demo seed is unchanged and does not write inventory logs.
- Address CRUD, robot simulation, route population, tracking, and
  delivery-pause enforcement remain their feature owners' integration work.
- Route JSON uses PostgreSQL JSONB and SQLite JSON for local tests.

## Compatibility with Part II

The shared design and existing main branch differ. This implementation preserves
current APIs instead of renaming their working columns as part of a database task.

| Design | Current implementation retained |
| --- | --- |
| BIGINT keys and entity-specific key names | Existing Integer `id` keys; Product keeps `product_id` |
| First/last name and Supabase Auth in LLD 1 | Existing `name`, password hash, Flask-Login session, lowercase roles |
| Shared cart/order line table | Separate mutable `cart_lines` and snapshot `order_lines` |
| Order address JSON snapshot and saved-address FK | Existing delivery_address/lat/lng snapshots; saved addresses are separate |
| Checked-out cart history and checkout token | One mutable saved cart per user; payment idempotency keys |
| Payment always has an order | Pending/failed payments may have no order; paid orders are linked |
| Queued trip with stored count/weight totals | `open` trip; count/weight derived from its Orders to avoid stale totals |
| Reject every stored overweight order | Checkout rejects >200 lb; historical exceptions remain representable for Manual Review |

Order numbers/status audit history, richer profile fields, and optional address
linking need agreement with their feature owners before changing the API contract.
The LLD should be reconciled with these decisions before final submission.

## Verification

```sh
python -m pytest -q
# Optional: adds migration tests in temporary schemas on a disposable PostgreSQL DB.
TEST_POSTGRES_URL=postgresql://USER:PASSWORD@localhost/TEST_DB python -m pytest -q tests/test_database_schema.py
# Generate PostgreSQL DDL for review without connecting to the server:
flask --app app:create_app db upgrade --sql
```

The migration tests exercise a clean rebuild, baseline upgrade/downgrade with data,
model/migration agreement, constraints/foreign keys, and immutable order snapshots.
