---
title: "Backlog History"
subtitle: "OFS On-Demand Food Delivery · CS 160 Fall 2026 · Group 5"
---

# Backlog History (T01–T20)

Source of the task list: Part II LLD, Backlog section (owner: Than Andrian).
Source of the history: `git log --all` on `cs160-team5-ofs`, 101 commits, 2026-09-14 to 2026-11-12, including unmerged remote branches. Dates are commit dates.

**Assigned** is the Team Member from the Part II backlog. **Built by** is whoever actually committed the work. Where they differ, the Notes column says so.

## Author name mapping

| Person | Git identities | Commits (all) | Non-merge |
|---|---|---|---|
| Kelvin Phat | Kelvin Phat, kphat | 61 | 51 |
| Andrian Than | andrianthan, Andrian Than | 22 | 14 |
| Jorge Nateras | Jorge Nateras, Jorge | 11 | 9 |
| Anuj Sharma | AnujSharma837 | 3 | 3 |
| Ethan Notario Rodriguez | Ethan Notario | 4 | 3 |
| Shresthkumar Karnani | Shresthkumar Karnani | 9 | 9 |

T04, T05 and T12 were assigned to Karnani. Kelvin built T04 and the first versions of T05 and T12. Karnani built the T05/T12 inventory log, the T12 customer order history page, and API stress tests with fixes for what they found on 2026-11-14, on branch `shresth/t05-t12-inventory-log-order-history` (not yet merged, so after the 2026-11-12 snapshot used for the status column).

## Backlog with status

Status below comes from reading the code on `origin/main` (2026-11-12) and running it: backend `pytest` gives 271 passed, 1 skipped; `tsc` on the storefront fails (see T16). Date Started and Date Finished are the first and last commits that touched the task, not planned dates.

| ID | Task | Assigned | Built by (from git) | Started | Finished | Status on `main` |
|---|---|---|---|---|---|---|
| T01 | Repo and deployment skeleton | Anuj | Andrian, Kelvin | 2026-09-29 | 2026-10-04 | Partial. Repo, both frontends, Flask and gunicorn dependency are in. No Apache config; the README says Apache is "not yet set up". |
| T02 | PostgreSQL schema and migrations | Anuj | Anuj, then Kelvin | 2026-11-04 | 2026-11-11 | Done. Alembic migrations, all tables, CI check, RLS migration. |
| T03 | Seed data, organic catalog | Anuj | Kelvin, Anuj | 2026-09-30 | 2026-11-11 | Done. |
| T04 | Auth and Roles backend | Karnani | Kelvin | 2026-09-30 | 2026-09-30 | Done. Register, login, logout, hashed passwords, role gating. |
| T05 | Catalog and Inventory backend | Karnani | Kelvin, Karnani | 2026-10-07 | 2026-11-14 | Partial. Product list, create, edit, delete work. Nothing writes `inventory_log`, so the "log every sale, restock, return or correction" requirement is unmet. |
| T06 | Storefront shell, routing, auth screens | Kelvin | Kelvin | 2026-09-30 | 2026-10-26 | Done. |
| T07 | Browse, search, product pages | Kelvin | Kelvin | 2026-10-06 | 2026-10-28 | Done. Search, categories, weight shown. |
| T08 | Cart and Pricing backend | Andrian | Andrian | 2026-10-13 | 2026-10-28 | Done. Server-side weight, fee, overweight check. |
| T09 | Cart UI, live weight and fee | Kelvin | Kelvin | 2026-10-14 | 2026-10-21 | Done. |
| T10 | Payments with Stripe test mode | Andrian | Andrian, Kelvin | 2026-10-13 | 2026-11-03 | Done. Idempotency keys, webhook, cancel, refund. |
| T11 | Address validation, delivery zone | Andrian | Andrian, Kelvin | 2026-10-04 | 2026-11-04 | Done. |
| T12 | Orders creation and status lifecycle | Karnani | Kelvin, Karnani | 2026-11-02 | 2026-11-14 | Mostly done. Order creation, transitions, stock decrement. No customer order-history page and no customer self-cancel in the storefront. |
| T13 | Delivery Planning, trip grouping | Ethan | Kelvin | 2026-10-14 | 2026-11-04 | Mostly done. Grouping, 10-order and 200 lb limits, 30-minute lock, `/api/trips` and dispatch. No route optimizer or robot queue. |
| T14 | Route Optimizer (Mapbox) | Ethan | Ethan (draft, since overwritten) | 2026-11-02 | 2026-11-02 | Not on `main`. Ethan's draft in `trips.py` was replaced by Kelvin's trip code. No Mapbox Optimization call exists. |
| T15 | Simulated robot fleet service | Ethan | Ethan | 2026-11-12 | 2026-11-12 | Not on `main`. "partial T15" is on `origin/t15-fleet-sim` only. |
| T16 | Order Tracking and live map | Jorge | Jorge | 2026-10-06 | 2026-11-12 | Partial. Backend endpoint with ownership check is in. Map UI is missing and the storefront does not typecheck (see below). |
| T17 | Notifications over SMTP | Jorge | Andrian | 2026-11-04 | 2026-11-04 | Done for status-change emails with dedup and retry. Not checked against a real SMTP server. |
| T18 | Staff Dashboard UI | Kelvin | Kelvin, Andrian | 2026-10-26 | 2026-11-04 | Partial. Inventory, prep queue, reports are in. Dispatch route is a placeholder stub; no scan/load flow, no trip map. |
| T19 | Manager Reports | Andrian | Andrian | 2026-11-03 | 2026-11-03 | Partial. Sales, inventory snapshot, delivery success rate. No stock adjustment history (no log), and I found no trip utilization metric. |
| T20 | Delivery Pause and Order Override | Jorge | Jorge | 2026-10-21 | 2026-11-12 | Partial. Pause API works and blocks payment creation. Override supports cancel with a required reason. The pause settings page and the storefront pause notice are not on `main`. |

Summary: 10 done (T02, T03, T04, T06, T07, T08, T09, T10, T11, T17), 8 partial or mostly done (T01, T05, T12, T13, T16, T18, T19, T20), 2 not on `main` (T14, T15).

### Known problems on `main`
- The storefront fails `tsc`: `src/App.tsx` imports `./pages/TrackOrdersPage`, which does not exist on `main`. `RobotMap.tsx` and `TrackOrdersPage.tsx` are only on `origin/t16-order-tracking`.
- `frontend/staff-dashboard/src/pages/DispatchPage.tsx` is an empty component, and the `/dispatch` route renders a placeholder stub instead.
- Stale comment in `reports.py` says there is no `inventory_log` table, but the table exists and is simply never written.

## Per-task history

### T01 Repo and deployment skeleton (assigned: Anuj)
- 2026-09-14 Andrian: initial commit with README, .gitignore and HANDOFF doc.
- 2026-09-29 Kelvin: README and .gitignore update.
- 2026-09-29 Andrian: UI prototype plus repo skeleton (Vite, React, Tailwind frontends, Flask backend, all blueprints as stubs).
- 2026-09-30 Kelvin: backend requirements updated for the project doc and Python 3.14.7.
- 2026-10-04 Andrian: TypeScript on both frontends. Decided DB hosting (Supabase).
- 2026-11-02 Kelvin: backend minor fixes (README, requirements, run.py).
- 2026-11-03 Andrian: dev port made configurable.
- No Apache or gunicorn config appears in the repo.
- Anuj has no commits on this task.

### T02 PostgreSQL schema and migrations (assigned: Anuj)
- Before 11/4, models for users, products, carts, orders and payments were added piecemeal by Kelvin and Andrian as their features needed them.
- 2026-11-04 Anuj: database schema and Alembic migrations (`3cd1c7f`), automated database checks via GitHub Actions (`56c14fe`).
- 2026-11-04 Kelvin: schema update for the trip rework, seeding moved into migrations (`fc630b5`).
- 2026-11-05 Anuj: merged as PR #7 (`a17116d`).
- 2026-11-09 Jorge: migration 0003 for delivery pause and override (T20), later reverted.
- 2026-11-11 Kelvin: connection pool settings, RLS migration, seed reads `.env` (`0cd221d`), removed old DB backup file.

### T03 Seed data (assigned: Anuj)
- 2026-09-30 Kelvin: first `seed_demo.py` with demo users, in the auth commit.
- 2026-10-07 Kelvin: seeded products.
- 2026-10-14 Kelvin: seeded cart.
- 2026-11-04 Anuj and Kelvin: seed moved into migrations.

### T04 Auth and Roles backend (assigned: Karnani)
- 2026-09-30 Kelvin: basic authentication and tests, `auth.py`, `user.py`, extensions (`120eb56`), more tests (`dcf0dc5`), fixes (`3a91276`).
- 2026-10-04 Andrian merged `feat/authentication`.
- 2026-11-14 Karnani: stress tests found two T04 crashes and fixed them: simultaneous sign-ups with one email (500 instead of 409), and names over 120 characters (500 on PostgreSQL) (`02dcf41`, branch `shresth/t05-t12-inventory-log-order-history`, not merged).

### T05 Catalog and Inventory backend (assigned: Karnani)
- 2026-10-07 Kelvin: Product model and API (`1a2b81d`).
- 2026-10-12 Kelvin: product API and tests (`016554e`).
- 2026-10-27 to 2026-10-29 Kelvin: staff product editing, employee view of all products including inactive, create and delete product, auto-deactivate out-of-stock items.
- 2026-11-14 Karnani: every Stock change writes `inventory_log` in the same transaction (RESTOCK / RETURN / CORRECTION on Manager edits, SALE on checkout, CANCEL on Order Override), `GET /api/products/<id>/inventory-log`, products with orders or Stock history can only be deactivated (`e72987c`, branch `shresth/t05-t12-inventory-log-order-history`, not merged).

### T06 Storefront shell and auth screens (assigned: Kelvin)
- 2026-09-30 Kelvin: login and register pages.
- 2026-10-04 Andrian: converted both frontends to TypeScript.
- 2026-10-04 to 2026-10-06 Kelvin: login page, auth components, register page, nav buttons, require-auth for cart.
- 2026-10-26 Kelvin: shared component library refactor, which T18 reuses.

### T07 Browse, search, product pages (assigned: Kelvin)
- 2026-10-06 Kelvin: browse page placeholders.
- 2026-10-13 Kelvin: search, category filters and product tiles.
- 2026-10-20 Kelvin: detailed item preview.
- 2026-10-28 Kelvin: inactive and low-stock products visually distinct.

### T08 Cart and Pricing backend (assigned: Andrian)
- 2026-10-13 Andrian: cart and pricing backend with tests, with T10 in one commit (`cd57bf8`).
- 2026-10-28 Kelvin: cart product removal bug fix.

### T09 Cart UI (assigned: Kelvin)
- 2026-10-14 Kelvin: cart context and provider, add to cart from browse, cart page.
- 2026-10-20 to 2026-10-21 Kelvin: cart preview, changed to hover, removed from the cart page.

### T10 Payments with Stripe (assigned: Andrian)
- 2026-10-13 Andrian: Stripe payments backend with tests.
- 2026-11-02 Kelvin: orders created from paid carts via Stripe webhook.
- 2026-11-03 Kelvin: payment backend changes, payment step in checkout.

### T11 Address validation (assigned: Andrian)
- 2026-10-04 Andrian: address validation and delivery zone check with tests.
- 2026-11-02 Kelvin: checkout address input with Mapbox autofill.
- 2026-11-04 Andrian: widened the zone west edge to include Diridon Station.

### T12 Orders creation and status lifecycle (assigned: Karnani)
- 2026-11-02 Kelvin: order creation from paid carts, order routes, tests (`fbe3ccd`).
- 2026-10-21 Jorge: authorization and validation tests for the override endpoint in `orders.py`.
- 2026-11-14 Karnani: SALE log on order creation; a cancelled Order's items go back into Stock with a CANCEL log (`e72987c`). Customer order history page `/orders` in the storefront (`bce268d`). Branch `shresth/t05-t12-inventory-log-order-history`, not merged.

### T13 Delivery Planning and trip grouping (assigned: Ethan)
- 2026-10-14 Ethan: T13 with placeholder values in `trips.py`.
- 2026-11-04 Kelvin: Trip model, mark-prepared assigns orders to trips, staff queue page (`dc77d8a`, PR #4).
- 2026-11-04 Kelvin: grouping by proximity (0.5 km), lock trips when full or 30 minutes old, trip list and dispatch endpoints (`ffa235e`).
- Ethan's placeholder in `trips.py` was replaced. The working logic on `main` is Kelvin's (`planning.py`, `timeutil.py`, `trips.py`).

### T14 Route Optimizer (assigned: Ethan)
- 2026-11-02 Ethan: "T14 logic with placeholder values/variables" in `trips.py`.
- Ethan's draft computed nearest-neighbor distances through Mapbox in `trips.py`, but it was overwritten by Kelvin's trip code on 11/4. `main` has no Mapbox Optimization call.

### T15 Simulated robot fleet (assigned: Ethan)
- The `robots` table and model arrived with T02 (Anuj, Kelvin).
- 2026-11-12 Ethan: "partial T15", adds `backend/app/blueprints/robot.py` (`45642d0`). It exists only on `origin/t15-fleet-sim` and is not merged into `main`.
- Jorge's 2026-10-06 commit added robot tracking and ETA to the UI prototype only.

### T16 Order Tracking and live map (assigned: Jorge)
- 2026-10-06 Jorge: robot tracking and ETA in the UI prototype.
- 2026-10-21 Jorge: tracking endpoint and tests (committed twice, `b41e579` and `12973de`).
- 2026-11-10 Jorge: full implementation with live robot map (`0fd6b9e`).
- 2026-11-12 Jorge: "fully completed manager override and tracking" (`0ccbde0`), now in `main`: tracking endpoint, tests, storefront map dependencies, and an import of `TrackOrdersPage` in the storefront `App.tsx`.
- The map UI itself (`RobotMap.tsx`, `TrackOrdersPage.tsx`) was only in `0fd6b9e` on `origin/t16-order-tracking` and was never merged. `main` imports a page file that does not exist there, so the storefront will not build until those files are merged.
- T15 is not merged, so tracking has no real simulated robot positions to consume yet.

### T17 Notifications over SMTP (assigned: Jorge)
- 2026-11-04 Andrian: SMTP notifications with dedup and retry (`37edee6`).
- 2026-11-04 Andrian: staff emailed when an order goes to Manual Review.
- No Jorge commits on this task.

### T18 Staff Dashboard UI (assigned: Kelvin)
- 2026-10-26 Kelvin: shared components, frontend refactor.
- 2026-10-27 to 2026-10-29 Kelvin: inventory page with manager edit, category edit, create and delete product.
- 2026-11-03 Andrian: reports page (under T19).
- 2026-11-04 Kelvin: preparation queue page and trip/dispatch endpoints.
- 2026-11-04 Andrian: Basil branding and UI refresh across both apps.
- `DispatchPage` is still a stub.

### T19 Manager Reports (assigned: Andrian)
- 2026-11-03 Andrian: sales, inventory and delivery reports, backend plus reports page, with tests (PR #1).

### T20 Delivery Pause and Order Override (assigned: Jorge)
- 2026-10-21 Jorge: override authorization and validation tests.
- 2026-11-04 Jorge: delivery pause work in progress (settings, audit model, staff settings page, storefront notice).
- 2026-11-09 Jorge: integrated override and added migration (`8002ed2`), merged as `t20-manager-override` (`fc6e844`), then reverted the merge the same day (`ee7fbb6`).
- 2026-11-12 Jorge: "Complete T20 manager override and order tracking" (`672252f`): delivery pause settings, override with audit log, migrations 0003 and 0004, staff queue UI, tests. Now in `main`.

## Contributions outside the backlog

- Andrian: repo setup and docs, README and macOS setup notes, Part III status doc (`docs/part3-status.md`), PR merging.
- Kelvin: README setup guide, Supabase hardening, removed stray binary files (`ui-prototype.zip`, `Archive.zip`, old DB backup).
- Jorge: `ui-prototype` robot tracking.
- Karnani: API stress tests (`85cd5df`): access control on every route and role, junk input on every route, sign-in abuse, and concurrent checkout, webhook, stock-edit and cancel races on PostgreSQL. Fixes for what they found outside T04: NUL characters in any JSON body were a 500 on PostgreSQL (`5c734c7`), simultaneous Manager cancels each restocked the order and the override route took a text id (T20, `4dc69a6`), and crashes in address validation (T11) and report dates (T19) (`e47e471`). All on branch `shresth/t05-t12-inventory-log-order-history`, not merged.
