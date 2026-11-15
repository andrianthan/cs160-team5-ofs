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
| Shresthkumar Karnani | none | 0 | 0 |

Karnani has no commits under any name in this repo. T04, T05 and T12 were assigned to Karnani, and Kelvin built them. If Karnani worked on something that was never committed, it can't be credited from git.

## Backlog with status

Status is as of `origin/main` as of 2026-11-12. Date Started and Date Finished are the first and last commits that touched the task, not planned dates.

| ID | Task | Assigned | Built by (from git) | Started | Finished | Status |
|---|---|---|---|---|---|---|
| T01 | Repo and deployment skeleton | Anuj | Andrian (skeleton), Kelvin (README, requirements) | 2026-09-29 | 2026-10-04 | Done for repo, frontends and Flask. Apache and gunicorn config are not in git, so unverified. |
| T02 | PostgreSQL schema and migrations | Anuj | Anuj, then Kelvin | 2026-11-04 | 2026-11-11 | Done. Migrations 0001 and 0002 (Anuj, PR #7), 0003 RLS and pool settings (Kelvin). |
| T03 | Seed data, organic catalog | Anuj | Kelvin, Anuj | 2026-09-30 | 2026-11-11 | Done. |
| T04 | Auth and Roles backend | Karnani | Kelvin | 2026-09-30 | 2026-09-30 | Done. |
| T05 | Catalog and Inventory backend | Karnani | Kelvin | 2026-10-07 | 2026-10-29 | Done. |
| T06 | Storefront shell, routing, auth screens | Kelvin | Kelvin (Andrian: TypeScript migration) | 2026-09-30 | 2026-10-26 | Done. |
| T07 | Browse, search, product pages | Kelvin | Kelvin | 2026-10-06 | 2026-10-28 | Done. |
| T08 | Cart and Pricing backend | Andrian | Andrian (Kelvin: one bug fix) | 2026-10-13 | 2026-10-28 | Done. |
| T09 | Cart UI, live weight and fee | Kelvin | Kelvin | 2026-10-14 | 2026-10-21 | Done. |
| T10 | Payments with Stripe test mode | Andrian | Andrian, then Kelvin | 2026-10-13 | 2026-11-03 | Done. |
| T11 | Address validation, delivery zone | Andrian | Andrian (Kelvin: checkout autofill) | 2026-10-04 | 2026-11-04 | Done. |
| T12 | Orders creation and status lifecycle | Karnani | Kelvin | 2026-11-02 | 2026-11-02 | Done except override endpoint, which is T20. |
| T13 | Delivery Planning, trip grouping | Ethan | Kelvin (real logic), Ethan (placeholder) | 2026-10-14 | 2026-11-04 | Mostly done. See notes. |
| T14 | Route Optimizer (Mapbox) | Ethan | Ethan | 2026-11-02 | 2026-11-02 | Placeholder only. |
| T15 | Simulated robot fleet service | Ethan | Ethan | 2026-11-12 | 2026-11-12 | Partial, on unmerged branch `t15-fleet-sim` only. |
| T16 | Order Tracking and live map | Jorge | Jorge | 2026-10-06 | 2026-11-12 | Partial on `main`: backend tracking endpoint only. The live map UI is not on `main` (see notes). |
| T17 | Notifications over SMTP | Jorge | Andrian | 2026-11-04 | 2026-11-04 | Done. |
| T18 | Staff Dashboard UI | Kelvin | Kelvin (Andrian: branding, reports page) | 2026-10-26 | 2026-11-04 | Partial. |
| T19 | Manager Reports | Andrian | Andrian | 2026-11-03 | 2026-11-03 | Done. |
| T20 | Delivery Pause and Order Override | Jorge | Jorge | 2026-10-21 | 2026-11-12 | Done. |

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
- No Karnani commits.

### T05 Catalog and Inventory backend (assigned: Karnani)
- 2026-10-07 Kelvin: Product model and API (`1a2b81d`).
- 2026-10-12 Kelvin: product API and tests (`016554e`).
- 2026-10-27 to 2026-10-29 Kelvin: staff product editing, employee view of all products including inactive, create and delete product, auto-deactivate out-of-stock items.
- No Karnani commits.

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
- No Karnani commits.

### T13 Delivery Planning and trip grouping (assigned: Ethan)
- 2026-10-14 Ethan: T13 with placeholder values in `trips.py`.
- 2026-11-04 Kelvin: Trip model, mark-prepared assigns orders to trips, staff queue page (`dc77d8a`, PR #4).
- 2026-11-04 Kelvin: grouping by proximity (0.5 km), lock trips when full or 30 minutes old, trip list and dispatch endpoints (`ffa235e`).
- Ethan's `trips.py` is a 78-line placeholder. The working logic is Kelvin's (`planning.py`, `timeutil.py`).

### T14 Route Optimizer (assigned: Ethan)
- 2026-11-02 Ethan: "T14 logic with placeholder values/variables" in `trips.py`.
- No Mapbox Optimization integration beyond that placeholder.

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
