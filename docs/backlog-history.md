---
title: "Backlog History"
subtitle: "OFS On-Demand Food Delivery · CS 160 Fall 2026 · Group 5"
---

# Backlog History (T01–T20)

Source of the task list: Part II LLD, Backlog section (owner: Than Andrian).
Source of the history: `git log --all` on `cs160-team5-ofs`, 161 commits, 2026-09-14 to 2026-11-21, including unmerged remote branches, read commit by commit (the diffs, not only the messages). Dates are commit dates. Last updated 2026-11-22.

**Assigned** is the Team Member from the Part II backlog. **Built by** is whoever actually committed the work. Where they differ, the Notes column says so.

## Author name mapping

| Person | Git identities | Commits (all) | Non-merge |
|---|---|---|---|
| Kelvin Phat | Kelvin Phat, kphat | 83 | 69 |
| Andrian Than | andrianthan, Andrian Than | 42 | 30 |
| Jorge Nateras | Jorge Nateras, Jorge | 14 | 10 |
| Anuj Sharma | AnujSharma837 | 3 | 3 |
| Ethan Notario Rodriguez | Ethan Notario | 10 | 9 |
| Shresthkumar Karnani | Shresthkumar Karnani | 9 | 9 |

Counts are as of 2026-11-21 and cover every branch. Squash-merged PRs (#12 to #16) add one commit on `main` for work whose original commits stay on their branches, so a person's work can appear twice in "all"; merges are counted under whoever clicked merge.

T04, T05 and T12 were assigned to Karnani. Kelvin built T04 and the first versions of T05 and T12. Karnani built the T05/T12 inventory log, the T12 customer order history page, and API stress tests with fixes for what they found on 2026-11-14, on branch `shresth/t05-t12-inventory-log-order-history`, merged on 2026-11-15 as PR #10 (`cd182be`).

## Backlog with status

Status below comes from reading the code on `origin/main` at `47af856` (PR #20, 2026-11-22) and running it: backend `pytest` gives 371 passed, 7 skipped; `npm run typecheck` passes on all three workspaces. Started and Finished are the first and last commits that touched the task, not planned dates.

| ID | Task | Assigned | Built by (from git) | Started | Finished | Status on `main` |
|---|---|---|---|---|---|---|
| T01 | Repo and deployment skeleton | Anuj | Andrian, Kelvin | 2026-09-14 | 2026-11-21 | Done. Repo, both frontends, Flask backend; Docker with gunicorn and Apache, local-database override, Stripe forwarder, auto-restart (PRs #17, #19); prebuilt images on GHCR (PR #20). |
| T02 | PostgreSQL schema and migrations | Anuj | Anuj, then Kelvin | 2026-11-04 | 2026-11-21 | Done. Alembic migrations, all tables, CI check, RLS migration, connection pool and timeouts. |
| T03 | Seed data, organic catalog | Anuj | Kelvin, Anuj, Andrian | 2026-09-30 | 2026-11-18 | Done. 38-product catalog, demo accounts, robots, two weeks of order history; `--auto` and `--reset` for local databases. |
| T04 | Auth and Roles backend | Karnani | Kelvin, Karnani | 2026-09-30 | 2026-11-14 | Done. Register, login, logout, hashed passwords, role gating; sign-up race and long-name crashes fixed by Karnani. |
| T05 | Catalog and Inventory backend | Karnani | Kelvin, Karnani | 2026-10-07 | 2026-11-14 | Done. Product list, create, edit, delete; every Stock change logged in `inventory_log` (Karnani, PR #10). |
| T06 | Storefront shell, routing, auth screens | Kelvin | Kelvin | 2026-09-30 | 2026-10-26 | Done. |
| T07 | Browse, search, product pages | Kelvin | Kelvin | 2026-10-06 | 2026-10-28 | Done. Search, categories, weight shown. |
| T08 | Cart and Pricing backend | Andrian | Andrian | 2026-10-13 | 2026-10-28 | Done. Server-side weight, fee, overweight check. |
| T09 | Cart UI, live weight and fee | Kelvin | Kelvin | 2026-10-14 | 2026-10-21 | Done. |
| T10 | Payments with Stripe test mode | Andrian | Andrian, Kelvin | 2026-10-13 | 2026-11-17 | Done. Idempotency keys, webhook, cancel, refund; paid end to end in test mode; listener script and Docker forwarder. |
| T11 | Address validation, delivery zone | Andrian | Andrian, Kelvin, Karnani | 2026-10-04 | 2026-11-14 | Done. |
| T12 | Orders creation and status lifecycle | Karnani | Kelvin, Karnani | 2026-11-02 | 2026-11-14 | Done. Order creation, transitions, stock decrement, customer order history page (Karnani, PR #10). Cancelling is a Manager Order Override (T20). |
| T13 | Delivery Planning, trip grouping | Ethan | Kelvin | 2026-10-14 | 2026-11-04 | Done. Grouping, 10-order and 200 lb limits, 30-minute lock, `/api/trips` and dispatch; feeds the T14 optimizer and T15 fleet. |
| T14 | Route Optimizer (Mapbox) | Ethan | Andrian (Ethan's draft, since overwritten) | 2026-11-02 | 2026-11-16 | Done. Mapbox Optimization in `routing.py` with a nearest-neighbour fallback (PR #12). |
| T15 | Simulated robot fleet service | Ethan | Ethan, Andrian, Kelvin | 2026-11-12 | 2026-11-18 | Done. Ethan's state machine in Andrian's rewrite (PR #12); offline/online (PR #14); Next stop, add and remove robots (PR #18). |
| T16 | Order Tracking and live map | Jorge | Jorge | 2026-10-06 | 2026-11-15 | Done. Tracking endpoint with ownership check, Track page and robot map (PR #11). |
| T17 | Notifications over SMTP | Jorge | Andrian | 2026-11-04 | 2026-11-16 | Done. Status-change emails with dedup and retry; Gmail login fix and SMTP setup and check scripts. |
| T18 | Staff Dashboard UI | Kelvin | Kelvin, Andrian | 2026-10-26 | 2026-11-18 | Done. Inventory, prep queue, reports, Dispatch page with street map, trips and robot controls (PRs #12, #14, #15, #18). |
| T19 | Manager Reports | Andrian | Andrian, Karnani | 2026-11-03 | 2026-11-16 | Done. Sales, inventory snapshot, delivery success rate, on-time rate, delivery duration, trip utilization (PR #16); stock history at the inventory-log endpoint. |
| T20 | Delivery Pause and Order Override | Jorge | Jorge, Andrian, Karnani | 2026-10-21 | 2026-11-16 | Done. Pause API and toggle, checkout notice and Pay disabled while paused (PRs #14, #15); cancel override with a required reason and audit log. |

Summary: all 20 done.

## Per-task history

### T01 Repo and deployment skeleton (assigned: Anuj)
- 2026-09-14 Andrian: initial commit with README, .gitignore and HANDOFF doc.
- 2026-09-29 Kelvin: README and .gitignore update.
- 2026-09-29 Andrian: UI prototype plus repo skeleton (Vite, React, Tailwind frontends, Flask backend, all blueprints as stubs).
- 2026-09-30 Kelvin: backend requirements updated for the project doc and Python 3.14.7.
- 2026-10-04 Andrian: TypeScript on both frontends. Decided DB hosting (Supabase).
- 2026-11-02 Kelvin: backend minor fixes (README, requirements, run.py).
- 2026-11-03 Andrian: dev port made configurable.
- 2026-11-15 Kelvin: Docker setup (`a26ba7c`): `backend/Dockerfile` runs the API under gunicorn (one worker, four threads, non-root user); `frontend/Dockerfile` builds either React app and serves it from Apache; `docker/apache-app.conf` proxies `/api` to the backend and falls back to `index.html` for browser routes; `docker-compose.yml` runs all three; `docker-compose.localdb.yml` swaps in a private PostgreSQL. README Supabase connection-string steps and a Docker troubleshooting table (`c6a48cd`). Optional `stripe` service that forwards webhooks (`b5d3857`).
- 2026-11-16 Kelvin: `AUTO_SEED=1` runs migrations and the demo seed before gunicorn starts, refusing any non-local database; `backend/.env` optional for the containers; `.gitattributes` keeps Docker and Apache files LF on Windows (`a77c834`). README start commands for both databases (`892e96d`).
- 2026-11-17 Andrian: frontend image builds on arm64 (Apple Silicon); the committed lockfile only had x64 native packages (`5aae6ba`).
- 2026-11-17 Kelvin: README table of the three Stripe webhook options (`1dae558`). Merged as PR #17 (`f9fcad4`).
- 2026-11-21 Kelvin: `restart: unless-stopped` on all three services (`737ade3`, PR #19).
- 2026-11-21 Kelvin: `.github/workflows/docker-images.yml` builds the three images for amd64 and arm64 and publishes them to GitHub's container registry on every push to `main`; `docker-compose.ghcr.yml` runs the site from them without a clone (`4dee3d7`, `d835a48`, PR #20).
- Anuj has no commits on this task.

### T02 PostgreSQL schema and migrations (assigned: Anuj)
- Before 11/4, models for users, products, carts, orders and payments were added piecemeal by Kelvin and Andrian as their features needed them.
- 2026-11-04 Anuj: database schema and Alembic migrations (`3cd1c7f`), automated database checks via GitHub Actions (`56c14fe`).
- 2026-11-04 Kelvin: schema update for the trip rework, seeding moved into migrations (`fc630b5`).
- 2026-11-05 Anuj: merged as PR #7 (`a17116d`).
- 2026-11-09 Jorge: migration 0003 for delivery pause and override (T20), later reverted.
- 2026-11-11 Kelvin: connection pool settings, RLS migration, seed reads `.env` (`0cd221d`), removed old DB backup file.
- 2026-11-21 Kelvin: connection timeout, TCP keepalives and `tcp_user_timeout` on PostgreSQL connections, so a connection that died while the host slept fails in seconds instead of hanging every gunicorn thread for about 15 minutes (`737ade3`, PR #19).

### T03 Seed data (assigned: Anuj)
- 2026-09-30 Kelvin: first `seed_demo.py` with demo users, in the auth commit.
- 2026-10-07 Kelvin: seeded products.
- 2026-10-14 Kelvin: seeded cart.
- 2026-11-04 Anuj and Kelvin: seed moved into migrations.
- 2026-11-16 Kelvin: `backend/demo_data.py` (`a77c834`): a 38-product catalog (including a 26 lb water case for the 20 lb fee), customers with delivery-zone addresses, robots, and two weeks of orders in every status with payments, trips and an inventory log replayed so final Stock matches; 7 tests in `test_demo_data.py`. `seed_demo.py --reset` wipes a local database and re-seeds, and refuses anything non-local (`90da132`).
- 2026-11-16 Andrian: `seed_demo.py --with-orders` seeded a week of orders and completed trips so Reports had numbers (`ee2e07e`).
- 2026-11-17 Kelvin: merge of the two (`823c7c7`): Kelvin's full history kept, `--with-orders` still accepted but no longer needed, Andrian's fleet and store location adopted.
- 2026-11-18 Kelvin: seeded robots renamed `OFS-R1` to `OFS-R3` (`8cfd9c8`).

### T04 Auth and Roles backend (assigned: Karnani)
- 2026-09-30 Kelvin: basic authentication and tests, `auth.py`, `user.py`, extensions (`120eb56`), more tests (`dcf0dc5`), fixes (`3a91276`).
- 2026-10-04 Andrian merged `feat/authentication`.
- 2026-11-14 Karnani: stress tests found two T04 crashes and fixed them: simultaneous sign-ups with one email (500 instead of 409), and names over 120 characters (500 on PostgreSQL) (`02dcf41`, branch `shresth/t05-t12-inventory-log-order-history`; merged in PR #10 on 2026-11-15).

### T05 Catalog and Inventory backend (assigned: Karnani)
- 2026-10-07 Kelvin: Product model and API (`1a2b81d`).
- 2026-10-12 Kelvin: product API and tests (`016554e`).
- 2026-10-27 to 2026-10-29 Kelvin: staff product editing, employee view of all products including inactive, create and delete product, auto-deactivate out-of-stock items.
- 2026-11-14 Karnani: every Stock change writes `inventory_log` in the same transaction (RESTOCK / RETURN / CORRECTION on Manager edits, SALE on checkout, CANCEL on Order Override), `GET /api/products/<id>/inventory-log`, products with orders or Stock history can only be deactivated (`e72987c`, branch `shresth/t05-t12-inventory-log-order-history`; merged in PR #10 on 2026-11-15).

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
- 2026-11-15 Kelvin: optional `stripe` Docker service that forwards test-mode webhooks to the backend (`b5d3857`).
- 2026-11-16 Andrian: a real test-mode PaymentIntent paid with card 4242 and its signed webhook, checked against the running stack (`ee2e07e`). `backend/start_stripe_listener.sh` starts the Stripe CLI and writes its signing secret into `backend/.env` (`4ce1022`).
- 2026-11-17 Kelvin: README table of which webhook option to use (`1dae558`).

### T11 Address validation (assigned: Andrian)
- 2026-10-04 Andrian: address validation and delivery zone check with tests.
- 2026-11-02 Kelvin: checkout address input with Mapbox autofill.
- 2026-11-04 Andrian: widened the zone west edge to include Diridon Station.

### T12 Orders creation and status lifecycle (assigned: Karnani)
- 2026-11-02 Kelvin: order creation from paid carts, order routes, tests (`fbe3ccd`).
- 2026-10-21 Jorge: authorization and validation tests for the override endpoint in `orders.py`.
- 2026-11-14 Karnani: SALE log on order creation; a cancelled Order's items go back into Stock with a CANCEL log (`e72987c`). Customer order history page `/orders` in the storefront (`bce268d`). Branch `shresth/t05-t12-inventory-log-order-history`, merged in PR #10 on 2026-11-15.

### T13 Delivery Planning and trip grouping (assigned: Ethan)
- 2026-10-14 Ethan: T13 with placeholder values in `trips.py`.
- 2026-11-04 Kelvin: Trip model, mark-prepared assigns orders to trips, staff queue page (`dc77d8a`, PR #4).
- 2026-11-04 Kelvin: grouping by proximity (0.5 km), lock trips when full or 30 minutes old, trip list and dispatch endpoints (`ffa235e`).
- Ethan's placeholder in `trips.py` was replaced. The working logic on `main` is Kelvin's (`planning.py`, `timeutil.py`, `trips.py`).

### T14 Route Optimizer (assigned: Ethan)
- 2026-11-02 Ethan: "T14 logic with placeholder values/variables" in `trips.py`.
- Ethan's draft computed nearest-neighbor distances through Mapbox in `trips.py`, but it was overwritten by Kelvin's trip code on 11/4.
- 2026-11-16 Andrian: the Mapbox Optimization call is now on `main`, in `backend/app/routing.py` (`optimize_route`), written as its own module instead of inside `trips.py`, with a nearest-neighbour fallback when Mapbox is unavailable. Merged in PR #12 (`b6bed4a`); checked live against the Mapbox API on 11/16.

### T15 Simulated robot fleet (assigned: Ethan)
- The `robots` table and model arrived with T02 (Anuj, Kelvin).
- 2026-11-12 Ethan: "partial T15", adds `backend/app/blueprints/robot.py` (`45642d0`). Ethan moved it to `backend/app/robot.py` on 2026-11-15 (`091e11e`); that file is the one continued below.
- Jorge's 2026-10-06 commit added robot tracking and ETA to the UI prototype only.
- 2026-11-15 to 2026-11-16 Ethan: continued `backend/app/robot.py` on `t15-fleet-sim` — "still partial t15" (`091e11e`), "transition logic should be done" (`9e339a3`), "travel simulation logic done i think" (`fd6ed96`), "comments and value changes while i try stuff" (`dbfb681`), "pseuodocode for new robot travel sim" (`eff4348`), "pseudocode for return home" (`cd5d36b`). At `cd5d36b` the file was 255 lines.
- 2026-11-16 Andrian: **Ethan's `backend/app/robot.py` was rewritten, and the rewrite is what shipped.** `e974248` and `6f52c6a` were committed on top of `t15-fleet-sim`, then merged to `main` as PR #12 (`b6bed4a`) and PR #14 (`6243191`). What changed: the `Robot` class became a thin wrapper over the `robots` row with module-level functions (`pick_robot`, `rebalance_reserve`, `start_trip`, `launch`, `run_trip`); `load_bot()`'s `input()` prompt became the Employee's Dispatch click; `do_trip()`'s stub became a real `run_trip()` that drives every stop and sends the customer delivery email; `reserve_bot()` became `rebalance_reserve()`; `return_home()` became the `last_stop` → `depot_reached` leg. What was kept: the state machine, every state and event name, and the header line "Owner: Notario Ethan Rodriguez". Ethan's commits are not ancestors of `main` (squash-merged), so `git log main` does not show them — his code is in `main`, his commits are not.
- 2026-11-16 Andrian: `ROBOT_SIM_*` speed settings read from the environment, so a demo can slow the Robot down (`ee2e07e`). `POST /api/robots/<id>/offline` and `/online` for staff; a reserved Robot can be taken offline and the reserve rebalances (`3855187`, squash-merged as PR #14, `6243191`).
- 2026-11-18 Kelvin: "Next stop", `POST /api/trips/<id>/advance`: moves the Robot to its next stop and delivers it by hand, then returns it and completes the Trip; it takes the Trip over from the auto-drive, which re-checks under a lock before each write, and it rescues Trips left stuck by a backend restart. Managers add Robots (`POST /api/robots`, parked at the store with the next code) and remove them (`DELETE /api/robots/<id>`, only from the depot or offline; past Trips keep their history). Robot codes are `OFS-R1`, `OFS-R2`, ... from `app/robot.py`. 13 new tests (`8cfd9c8`, PR #18).

### T16 Order Tracking and live map (assigned: Jorge)
- 2026-10-06 Jorge: robot tracking and ETA in the UI prototype.
- 2026-10-21 Jorge: tracking endpoint and tests (committed twice, `b41e579` and `12973de`).
- 2026-11-10 Jorge: full implementation with live robot map (`0fd6b9e`).
- 2026-11-12 Jorge: "fully completed manager override and tracking" (`0ccbde0`), now in `main`: tracking endpoint, tests, storefront map dependencies, and an import of `TrackOrdersPage` in the storefront `App.tsx`.
- 2026-11-14 Kelvin: a trial merge of `main` into the T16 branch, dropping a duplicate `TrackOrdersPage` import (`2acfb92`, `6eb8e1b`, branch `test/t16-merge`). Not merged; it only checked that the two combine.
- 2026-11-15 Jorge: restored `RobotMap.tsx` and `TrackOrdersPage.tsx` (`0579740`). Both files are byte-for-byte his 11/10 versions from `0fd6b9e`. Merged as PR #11 (`00df99b`).
- 2026-11-16 Andrian: the Track map watched with a Robot mid-trip, against the running stack (`ee2e07e`).

### T17 Notifications over SMTP (assigned: Jorge)
- 2026-11-04 Andrian: SMTP notifications with dedup and retry (`37edee6`).
- 2026-11-04 Andrian: staff emailed when an order goes to Manual Review.
- 2026-11-16 Andrian (`ee2e07e`): `notifications._login` does the PLAIN exchange itself. Python's `starttls()` drops the server's AUTH list, and `login()` then fell through to LOGIN, which Gmail answers by closing the connection, so a wrong password showed up as "Connection unexpectedly closed" instead of Gmail's `535`. `SMTP_TIMEOUT_S` raised from 10 to 30 s for Gmail's TLS handshake. `backend/smtp_check.py` logs in, or sends a test email, as a pre-demo check.
- 2026-11-16 Andrian: `backend/set_smtp_credentials.py` asks for the Gmail address and app password (not echoed), writes the SMTP values into `backend/.env` with a backup, and sends a test email. `SMTP_FROM` now defaults to "Basil <username>" (`ea1f5f2`).
- No Jorge commits on this task.

### T18 Staff Dashboard UI (assigned: Kelvin)
- 2026-10-26 Kelvin: shared components, frontend refactor.
- 2026-10-27 to 2026-10-29 Kelvin: inventory page with manager edit, category edit, create and delete product.
- 2026-11-03 Andrian: reports page (under T19).
- 2026-11-04 Kelvin: preparation queue page and trip/dispatch endpoints.
- 2026-11-04 Andrian: Basil branding and UI refresh across both apps.
- 2026-11-16 Andrian: Dispatch page with the robot fleet, a schematic live map and trips (`6f52c6a`, PR #12). Robot offline/online buttons and the Manager pause toggle (`3855187`, PR #14). Robots parked at one spot share a marker and label (`ad24c21`, PR #15).
- 2026-11-18 Kelvin: the schematic replaced by a street map, `StreetMap.tsx` with Leaflet and OpenStreetMap (`ef1b65d`). Next stop, Add robot and Remove buttons; map labels HTML-escaped (`8cfd9c8`). Merged as PR #18 (`f9c1151`).

### T19 Manager Reports (assigned: Andrian)
- 2026-11-03 Andrian: sales, inventory and delivery reports, backend plus reports page, with tests (PR #1).
- 2026-11-16 Andrian: on-time rate (delivered stops at or before their ETA, out of delivered stops with an ETA), average minutes from order to arrival, and trip utilization (average orders per Trip and fill of the 10-order and 200 lb limits), with tests and the Reports page fields (`5232658`, squash-merged as PR #16, `6edcd06`).
- Stock adjustment history: every Stock change is logged (T05, PR #10) and Managers read it at `GET /api/products/<id>/inventory-log`.

### T20 Delivery Pause and Order Override (assigned: Jorge)
- 2026-10-21 Jorge: override authorization and validation tests.
- 2026-11-04 Jorge: delivery pause work in progress (settings, audit model, staff settings page, storefront notice).
- 2026-11-09 Jorge: integrated override and added migration (`8002ed2`), merged as `t20-manager-override` (`fc6e844`), then reverted the merge the same day (`ee7fbb6`).
- 2026-11-12 Jorge: "Complete T20 manager override and order tracking" (`672252f`): delivery pause settings, override with audit log, migrations 0003 and 0004, staff queue UI, tests. Now in `main`.
- 2026-11-16 Andrian: Manager pause/resume toggle on the Dispatch page and a pause notice at checkout (`3855187`, PR #14); Pay disabled while paused and a duplicate pause banner removed (`ad24c21`, PR #15).

## Contributions outside the backlog

- Andrian: repo setup and docs, README and macOS setup notes, Part III status doc (`docs/part3-status.md`), PR merging. Demo materials on 2026-11-16 (`ee2e07e`): the Part III presentation, demo run-of-show and cheat sheet with screenshots, the Part II shared draft in the repo, the note to Ethan about the T15 rewrite (`docs/notes/ethan-robot-py.md`), and `FLASK_RELOAD=0` so the dev server can't lose its port mid-demo.
- Kelvin: README setup guide, Supabase hardening, removed stray binary files (`ui-prototype.zip`, `Archive.zip`, old DB backup). This backlog history (2026-11-14). Docker, demo data and GHCR images are under T01 and T03.
- Jorge: `ui-prototype` robot tracking.
- Karnani: API stress tests (`85cd5df`): access control on every route and role, junk input on every route, sign-in abuse, and concurrent checkout, webhook, stock-edit and cancel races on PostgreSQL. Fixes for what they found outside T04: NUL characters in any JSON body were a 500 on PostgreSQL (`5c734c7`), simultaneous Manager cancels each restocked the order and the override route took a text id (T20, `4dc69a6`), and crashes in address validation (T11) and report dates (T19) (`e47e471`). All on branch `shresth/t05-t12-inventory-log-order-history`, merged in PR #10 on 2026-11-15.
