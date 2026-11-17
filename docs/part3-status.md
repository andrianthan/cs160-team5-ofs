---
title: "Project Status & Role Assignments"
subtitle: "OFS On-Demand Food Delivery · CS 160 Fall 2026 · Group 5"
author: "Karnani Shresthkumar, Nateras Jorge, Notario Ethan Rodriguez, Phat Kelvin, Sharma Anuj, Than Andrian"
date: "November 16, 2026"
---

# Timeline

| Part | Points | Due | Status |
|---|---|---|---|
| I — Requirement Doc + HLD | 35 | 9/17/26 | ✅ Submitted |
| II — LLD + Test Plan + Backlog | 35 | 9/24/26 | ✅ Submitted |
| **III — Build + 12-min presentation** | **270** | **11/23/26** | **🔵 In progress — ~3 weeks left** |
| IV — Black box testing | 30 | 12/1/26 | Not started |
| V — SW maintenance / bug fixing | 30 | 12/7/26 | Not started |
| VI — Scrum participation (individual) | 30 | ongoing | Ongoing |
| VII — Retrospective (individual) | 20 | — | Not started |

Part III is worth more than every other part combined (270 of ~500 points). It is the priority through 11/23.

# Immediate Blockers

Statuses below were re-checked against `main` on 11/16 (351 backend tests passing, 358 collected).

**Critical path is delivery.** Preparation Queue is in (Kelvin, PR #4): a `Trip` model, "mark prepared" assigns Orders to a Trip within 10 Orders / 200 lb (BR-2/BR-6), and over-200 lb Orders go to Manual Review. Delivery is now built end to end: 0.5 km trip grouping and the 30-minute dispatch timer (BR-7, Kelvin), `/api/trips` with Dispatch, the Mapbox route optimizer with a nearest-neighbour fallback (T14), the simulated robot fleet (T15) and the staff Dispatch page (PR #12). Still open: verification only (real SMTP provider, end-to-end demo).

**Not started anywhere in the code:** nothing. T20 (delivery pause and order override) is built.

**Hook for anyone who changes Order status outside `PATCH /api/orders/<id>/status`** (tracking/robot updates, order override): call `notifications.notify_status_change(order)` after committing, so customers and staff get their emails.

# Backlog (T01–T20)

Priority: 1 = High, 2 = Med, 3 = Low. Estimates are in days, from Part II.

| ID | Task | Owner | Priority | Est. | Status | Depends on |
|---|---|---|---|---|---|---|
| T01 | Repo and deployment skeleton | Anuj | 1 | 3d | ✅ Done (built by Andrian) | — |
| T02 | PostgreSQL schema and migrations | Anuj | 1 | 3d | ✅ Done (PR #7) — Alembic migrations, robots/trips/trip_stops/inventory_log tables, integrity checks in CI | — (blocks nearly everything) |
| T03 | Seed data, realistic organic catalog | Anuj | 2 | 2d | ✅ Done — `seed_demo.py` (demo users, products, cart) | T02 |
| T04 | Auth and Roles backend | Shresthkumar | 1 | 4d | ✅ Done (built by Kelvin, merged by Andrian) | — |
| T05 | Catalog and Inventory backend | Shresthkumar | 1 | 3d | ✅ Done | T02 |
| T06 | Storefront shell, routing and auth screens | Kelvin | 1 | 3d | ✅ Done | T04 (done) |
| T07 | Browse, search and product pages | Kelvin | 1 | 3d | ✅ Done | T05, T06 |
| T08 | Cart and Pricing backend | Andrian | 1 | 4d | ✅ Done | T02, T05 |
| T09 | Cart UI with live weight and fee preview | Kelvin | 2 | 3d | ✅ Done | T08 |
| T10 | Payments with Stripe test mode | Andrian | 1 | 4d | ✅ Done | T08 |
| T11 | Address Validation and Delivery Zone check | Andrian | 1 | 3d | ✅ Done — address validation, Mapbox autofill | — |
| T12 | Orders creation and status lifecycle | Shresthkumar | 1 | 3d | ✅ Done — orders via Stripe webhook, status lifecycle, Manager cancel override with audit record and stock return | T08, T10 |
| T13 | Delivery Planning and trip grouping | Ethan | 1 | 5d | ✅ Done — grouping (0.5 km radius, BR-2/BR-6), 30-min lock (BR-7) and `/api/trips` + dispatch built by Kelvin (`planning.py`) | T12 |
| T14 | Route Optimizer via Mapbox Optimization | Ethan | 1 | 3d | ✅ Done (PR #12) — `routing.py`: Mapbox Optimization roundtrip from the store, nearest-neighbour fallback, creates trip stops/route/ETA. Mapbox Optimization checked live on 11/16 | T13 |
| T15 | Simulated robot fleet service | Ethan | 2 | 4d | ✅ Done (PR #12) — robot state machine, background trip simulation (delivers orders, returns to store), reserve-robot logic, `GET /api/robots`, 3 seeded demo robots. Robots move in straight lines between stops | T13 |
| T16 | Order Tracking and live map | Jorge | 2 | 4d | ✅ Done — `GET /api/tracking/<id>` plus the storefront Track page with a live robot map (needs `npm install` for leaflet) | T15 |
| T17 | Notifications over SMTP | Jorge | 3 | 2d | ✅ Done (PR #5) — emails on placed / out for delivery / delivered / delivery failed / manual review, with dedup and retry. Needs a real SMTP provider test | T12 |
| T18 | Staff Dashboard UI, prep queue and dispatch | Kelvin | 1 | 5d | ✅ Done — Inventory, Prep Queue and Dispatch pages (fleet, live map, trips, dispatch, robot offline/online, Manager pause toggle) | T05, T13, T16 |
| T19 | Manager Reports | Andrian | 2 | 3d | ✅ Done (PR #1) — sales, inventory, delivery reports. On-time rate, delivery duration and trip utilization computed from trip stops | T12, T13 |
| T20 | Delivery Pause and Order Override | Jorge | 2 | 3d | ✅ Done — Manager pause/resume (BR-9) blocks checkout with a notice on the storefront; Manager order cancel override | T12, T13 |

**Done:** all of T01–T20. Remaining is verification, not features: SMTP against a real provider, and a full end-to-end demo run.

# Verification results — 11/16

Checked by hand against the running stack, not just in unit tests.

| What | Result |
|---|---|
| **Stripe test-mode payment** | ✅ Done. A real PaymentIntent (`pi_3Ucfhe2IaMg0E3ep0d7tHdFL`, $31.45) paid with card 4242…, the signed webhook arrived (`payment_intent.succeeded` → **200** on `/api/payments/webhook`) and the Order was created from it. |
| **Order flow through dispatch** | ✅ Done. `placed` → `planned` (Trip #1) → `out_for_delivery` → `delivered`, with the Trip, the Robot and the ETA all recorded. |
| **Customer map mid-trip** | ✅ Done. The Robot's position advanced every 2 s (the sim was slowed to 2 s per step for this run; the default is 1 s) — 37.335408, −121.881492 → 37.337700, −121.885780 — and the Track page rendered the marker moving, then the Robot returning to the depot. |
| **Mapbox** | ✅ Done. Geocoding and Search JS autofill live in checkout; the Optimization API returns the Trip route and per-stop ETAs (checked 11/16). |
| **SMTP against a real provider** | 🔶 Blocked on credentials. Transport, STARTTLS and the AUTH exchange are all verified against `smtp.gmail.com` — a wrong password now returns Gmail's real `535 Username and Password not accepted`. Only the Gmail address + app password are missing. |

Three defects found and fixed during this verification, all worth knowing about:

- The demo SQLite database was **missing 8 tables**, so `/api/settings/delivery-pause` returned 500 on every checkout page. `python seed_demo.py --with-orders` now recreates all 17 and seeds a week of Orders with the Trips that delivered them, so the Reports metrics have numbers from a fresh reset.
- The Flask reloader could lose its port on restart and **take the whole server down**. `FLASK_RELOAD=0` disables it; the demo run-of-show uses it.
- The Stripe webhook listener had **died from an expired CLI OAuth token**, and its signing secret no longer matched the one in `.env`. `backend/start_stripe_listener.sh` now starts the listener, syncs the secret into `.env` and refreshes the CLI token in one step — the old failure was silent, since payments simply stopped arriving.

# Remaining Work — through 11/23

| Area | Tasks | Notes |
|---|---|---|
| Delivery planning | T13, T14, T15 | Built (PR #12). Mapbox Optimization checked live on 11/16 (response matches the parser). |
| Tracking and dispatch | T16, T18 | Built. Checked by hand on 11/16: the customer Track map was watched while the Robot was mid-trip. |
| Overrides and pause | T20, T12 override | Built. Status-change code must call `notify_status_change`. |
| Reports | T19 | Done: on-time rate, delivery duration and trip utilization now computed from trip ETAs. The exact metric definitions are now copied into the Test Plan (Part II, Test Plan 3.1) from the `reports.py` header; LLD 4.3 still has a TO DO for the same definitions. |
| Verification | T10, T17 | Stripe, Mapbox and the customer map checked live on 11/16. SMTP transport and auth checked against Gmail; needs the account's app password. |
| Demo | Part III | `docs/part3-presentation.html` (12 slides, speaker notes, per-slide timings) and `docs/demo-run-of-show.md` (pre-flight, the four demo beats, failure playbook, rehearsal plan). |

# Everyone, ongoing

- **Part VI (Scrum participation)** is graded individually — show up and speak at every scrum/stand-up
- Keep PRs small; merge into `main` regularly, don't let branches sit (see `feat/authentication` — good work, almost stayed invisible for days)
- Flag blockers early — T02 is the critical path; anything stuck behind it should say so

# After T02–T20 (Parts IV–VII)

- **Part IV (12/1): Black box testing** — pulls from Test Plan's functional/component test descriptions (already written in Part II); someone needs to own writing the actual test cases once features exist
- **Part V (12/7): Maintenance/bug fixing** — whatever breaks during Part IV testing or the Part III demo
- **Part VII: Retrospective** — individual, no prep needed until closer to the date
