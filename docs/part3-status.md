---
title: "Project Status & Role Assignments"
subtitle: "OFS On-Demand Food Delivery · CS 160 Fall 2026 · Group 5"
author: "Karnani Shresthkumar, Nateras Jorge, Notario Ethan Rodriguez, Phat Kelvin, Sharma Anuj, Than Andrian"
date: "November 4, 2026"
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

Statuses below were re-checked against `main` on 11/4 (234 backend tests passing).

**Critical path is delivery.** Preparation Queue is in (Kelvin, PR #4): a `Trip` model, "mark prepared" assigns Orders to a Trip within 10 Orders / 200 lb (BR-2/BR-6), and over-200 lb Orders go to Manual Review. Still missing: nearest-neighbor grouping and the 30-minute dispatch timer (BR-7), the `/api/trips` endpoints (still 501), T14 route optimizer, T15 robot simulator, and T16 tracking (`tracking.py` still 501). Dispatch UI, the on-time rate in T19, and the order override all depend on these.

**Not started anywhere in the code:** T20 (delivery pause in `settings.py`, and the order override endpoint in `orders.py`, are both still 501).

**Hook for anyone who changes Order status outside `PATCH /api/orders/<id>/status`** (tracking/robot updates, order override): call `notifications.notify_status_change(order)` after committing, so customers and staff get their emails.

# Backlog (T01–T20)

Priority: 1 = High, 2 = Med, 3 = Low. Estimates are in days, from Part II.

| ID | Task | Owner | Priority | Est. | Status | Depends on |
|---|---|---|---|---|---|---|
| T01 | Repo and deployment skeleton | Anuj | 1 | 3d | ✅ Done (built by Andrian) | — |
| T02 | PostgreSQL schema and migrations | Anuj | 1 | 3d | 🟨 Partial — models for users, products, carts, orders, payments exist; no robots/trips tables, no inventory_log | — (blocks nearly everything) |
| T03 | Seed data, realistic organic catalog | Anuj | 2 | 2d | ✅ Done — `seed_demo.py` (demo users, products, cart) | T02 |
| T04 | Auth and Roles backend | Shresthkumar | 1 | 4d | ✅ Done (built by Kelvin, merged by Andrian) | — |
| T05 | Catalog and Inventory backend | Shresthkumar | 1 | 3d | ✅ Done | T02 |
| T06 | Storefront shell, routing and auth screens | Kelvin | 1 | 3d | ✅ Done | T04 (done) |
| T07 | Browse, search and product pages | Kelvin | 1 | 3d | ✅ Done | T05, T06 |
| T08 | Cart and Pricing backend | Andrian | 1 | 4d | ✅ Done | T02, T05 |
| T09 | Cart UI with live weight and fee preview | Kelvin | 2 | 3d | ✅ Done | T08 |
| T10 | Payments with Stripe test mode | Andrian | 1 | 4d | ✅ Done | T08 |
| T11 | Address Validation and Delivery Zone check | Andrian | 1 | 3d | ✅ Done — address validation, Mapbox autofill | — |
| T12 | Orders creation and status lifecycle | Shresthkumar | 1 | 3d | 🟨 Mostly done — orders via Stripe webhook; override endpoint 501 | T08, T10 |
| T13 | Delivery Planning and trip grouping | Ethan | 1 | 5d | 🟨 Partial — Trip model and prepare-to-trip assignment (BR-2/BR-6) done; nearest-neighbor grouping, dispatch timer, `/api/trips` still missing | T12 |
| T14 | Route Optimizer via Mapbox Optimization | Ethan | 1 | 3d | ⬜ Pending | T13 |
| T15 | Simulated robot fleet service | Ethan | 2 | 4d | ⬜ Pending | T13 |
| T16 | Order Tracking and live map | Jorge | 2 | 4d | 🟨 Partial — `tracking.py` 501 with TODOs | T15 |
| T17 | Notifications over SMTP | Jorge | 3 | 2d | ✅ Done (PR #5) — emails on placed / out for delivery / delivered / delivery failed / manual review, with dedup and retry. Needs a real SMTP provider test | T12 |
| T18 | Staff Dashboard UI, prep queue and dispatch | Kelvin | 1 | 5d | 🟨 Partial — Inventory and Prep Queue pages done; Dispatch page is still a stub | T05, T13, T16 |
| T19 | Manager Reports | Andrian | 2 | 3d | ✅ Done (PR #1) — sales, inventory, delivery reports. On-time rate null until T13/T15 | T12, T13 |
| T20 | Delivery Pause and Order Override | Jorge | 2 | 3d | ⬜ Not started — `settings.py` 501 | T12, T13 |

**Done:** T01, T03, T04, T05–T11, T17, T19. **Partial:** T02, T12, T13, T16, T18. **Not started:** T14, T15, T20.

# Remaining Work — through 11/23

| Area | Tasks | Notes |
|---|---|---|
| Delivery planning | T13, T14, T15 | Biggest risk. Grouping into trips exists; add nearest-neighbor, the 30-min timer, real `/api/trips`, route optimizer, robot simulator. |
| Tracking and dispatch | T16, T18 | Need trips and a robot simulator. Dispatch page is a stub. |
| Overrides and pause | T20, T12 override | Needs T13. Status-change code must call `notify_status_change`. |
| Reports | T19 follow-up | Fill in on-time rate and trip utilization once trips carry ETAs. |
| Verification | T10, T17 | Stripe and Mapbox checked live on 11/4. SMTP checked only against a local sink; needs a real provider. |

# Everyone, ongoing

- **Part VI (Scrum participation)** is graded individually — show up and speak at every scrum/stand-up
- Keep PRs small; merge into `main` regularly, don't let branches sit (see `feat/authentication` — good work, almost stayed invisible for days)
- Flag blockers early — T02 is the critical path; anything stuck behind it should say so

# After T02–T20 (Parts IV–VII)

- **Part IV (12/1): Black box testing** — pulls from Test Plan's functional/component test descriptions (already written in Part II); someone needs to own writing the actual test cases once features exist
- **Part V (12/7): Maintenance/bug fixing** — whatever breaks during Part IV testing or the Part III demo
- **Part VII: Retrospective** — individual, no prep needed until closer to the date
