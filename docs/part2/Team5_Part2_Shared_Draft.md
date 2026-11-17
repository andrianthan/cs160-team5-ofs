---
title: "Low-Level Design and High-Level Test Plan"
subtitle: "OFS On-Demand Food Delivery Service · CS 160 Fall 2026 · Group Project Part II · Group 5"
author: "Karnani Shresthkumar, Nateras Jorge, Notario Ethan Rodriguez, Phat Kelvin, Sharma Anuj, Than Andrian"
date: "Due September 24, 2026, 11:59 pm"
---

# How to use this document

This is the shared working draft for Part II. Each section has one owner and matches one card on the Trello board. Write your section directly under its heading. Every yellow [TO DO] note is yours to fill in. Replace it with your content.

**Rules**

- Draft deadline: **Tuesday 9/22, night.** Andrian merges and formats on Wednesday 9/23. Submission is Thursday 9/24.
- Use the glossary terms from CONTEXT.md exactly: Order, Order Line, Order Weight, Delivery Fee, Trip, Robot, Route, Dispatch, and so on.
- Use the business rule IDs (BR-1 to BR-9) when you mention a rule.
- Pseudo code goes in code blocks. Keep it readable, not language-specific.
- Do not write test cases in the Test Plan. Describe goals and expectations only.
- Andrian deletes this section, the owner tags, and every [TO DO] note before submission.

**Page targets.** The Low-Level Design needs at least 6 pages and the Test Plan at least 5. Aim for 1 to 2 pages per section.

| Section | Owner | Trello card |
|---|---|---|
| LLD 1. Auth, Catalog and Cart | Karnani Shresthkumar | P2 \| LLD 1 |
| LLD 2. Checkout, Address and Payments | Than Andrian | P2 \| LLD 2 |
| LLD 3. Delivery Planning and routing | Notario Ethan Rodriguez | P2 \| LLD 3 |
| LLD 4. Tracking, Notifications and Reports | Nateras Jorge | P2 \| LLD 4 |
| LLD 5. Frontend component breakdown | Phat Kelvin | P2 \| LLD 5 |
| LLD 6. Database detail and API contracts | Sharma Anuj | P2 \| LLD 6 |
| Test Plan 1. Strategy, methodology and tools | Sharma Anuj | P2 \| Test Plan 1 |
| Test Plan 2. Functional and component tests | Karnani Shresthkumar | P2 \| Test Plan 2 |
| Test Plan 3. Metrics and success criteria | Notario Ethan Rodriguez | P2 \| Test Plan 3 |
| Backlog | Than Andrian | P2 \| Export backlog |

**Business rules for reference**

| ID | Rule |
|---|---|
| BR-1 | Delivery Fee is $0 under 20 lb and $10 at 20 lb or more |
| BR-2 | A Robot carries at most 10 Orders and 200 lb per Trip |
| BR-3 | An Order over 200 lb is blocked at checkout |
| BR-4 | Stock is checked when adding to the Cart and again at checkout |
| BR-5 | The delivery address must geocode inside the Downtown San Jose Delivery Zone |
| BR-6 | Delivery Planning starts with the oldest Placed Order, then adds the nearest Orders within BR-2 |
| BR-7 | A Trip is dispatched when full, or 30 minutes after its oldest Order was Placed |
| BR-8 | A failed delivery returns to the store; Customer and Staff are notified |
| BR-9 | Delivery Pause disables checkout and shows a notice |


# Part A. Low-Level Design Document

## Overview

*[TO DO — Andrian: 1 short paragraph. Say this document breaks the 15 components in the Part I Architecture into implementable detail, and that logic is shown as pseudo code. Point to the Part I HLD for the component diagram.]*

## LLD 1. Auth and Roles, Catalog and Inventory, Cart and Pricing

**Owner:** Karnani Shresthkumar

*[TO DO — Shresthkumar: Cover, for each of the three components:]*

- *[TO DO — Shresthkumar: Modules or classes and what each is responsible for]*
- *[TO DO — Shresthkumar: Function signatures with inputs, outputs, and error cases]*
- *[TO DO — Shresthkumar: Pseudo code for: password hashing and session creation, role enforcement, stock check, Order Weight and Delivery Fee calculation]*
- *[TO DO — Shresthkumar: Validation rules and failure paths]*

*[TO DO — Shresthkumar: The fee pseudo code must show the BR-1 boundary: $0 below 20 lb, $10 at exactly 20 lb or more. Show the BR-3 overweight block too.]*

### 1.1 Auth and Roles

*[TO DO — Shresthkumar: write this subsection.]*

### 1.2 Catalog and Inventory

*[TO DO — Shresthkumar: write this subsection.]*

### 1.3 Cart and Pricing

*[TO DO — Shresthkumar: write this subsection.]*

## LLD 2. Checkout, Address Validation and Payments

**Owner:** Than Andrian

*[TO DO — Andrian: Cover Address Validation, Payments, and Orders:]*

- *[TO DO — Andrian: The full checkout sequence as pseudo code: address validation, zone check, overweight check, stock recheck, payment, then Order creation]*
- *[TO DO — Andrian: Geocoding request and response handling, and the point-in-polygon Delivery Zone test]*
- *[TO DO — Andrian: Stripe payment intent creation, confirmation, and idempotency so a double submit cannot double charge]*
- *[TO DO — Andrian: Order Status state machine with every allowed transition and who may trigger it]*
- *[TO DO — Andrian: Rollback when payment succeeds but Order creation fails]*

### 2.1 Checkout sequence

*[TO DO — Andrian: write this subsection.]*

### 2.2 Address Validation and Delivery Zone

*[TO DO — Andrian: write this subsection.]*

### 2.3 Payments

*[TO DO — Andrian: write this subsection.]*

### 2.4 Order Status state machine

*[TO DO — Andrian: write this subsection.]*

## LLD 3. Delivery Planning and Routing

**Owner:** Notario Ethan Rodriguez

*[TO DO — Ethan: Cover Delivery Planning, Route Optimizer, and Robot Fleet. This is the most algorithmic section, so expect the most pseudo code. Prototype the Mapbox Optimization call before writing it.]*

- *[TO DO — Ethan: Trip grouping algorithm as pseudo code: seed with the oldest Placed Order, add nearest candidates while both the 10 Order and 200 lb limits hold (BR-2, BR-6)]*
- *[TO DO — Ethan: The 30 minute Dispatch timer: how it is evaluated and what triggers finalizing a Trip (BR-7)]*
- *[TO DO — Ethan: Mapbox Optimization request construction and how the returned stop sequence maps back to Orders]*
- *[TO DO — Ethan: Robot state machine with every transition]*
- *[TO DO — Ethan: What happens when no Robot is available (Robot Queue), and when routing fails]*

### 3.1 Trip grouping

*[TO DO — Ethan: write this subsection.]*

### 3.2 Dispatch rule

*[TO DO — Ethan: write this subsection.]*

### 3.3 Route Optimizer

*[TO DO — Ethan: write this subsection.]*

### 3.4 Robot Fleet

*[TO DO — Ethan: write this subsection.]*

## LLD 4. Order Tracking, Notifications and Reports

**Owner:** Nateras Jorge

- *[TO DO — Jorge: How Robot position and stop events are ingested and turned into Order and Trip status updates]*
- *[TO DO — Jorge: Polling or push for the live map: the interval you chose and why]*
- *[TO DO — Jorge: Authorization check so a Customer can only track their own Order]*
- *[TO DO — Jorge: Notification trigger table: event, template, recipients. Plus deduplication and retry logic (BR-8)]*
- *[TO DO — Jorge: Report query shapes and the exact definition of every metric: on-time rate, delivery duration, Trip utilization, Product demand]*

*[TO DO — Jorge: Metric definitions must be identical wherever they appear. Two Reports must not compute on-time rate differently.]*

### 4.1 Order Tracking

*[TO DO — Jorge: write this subsection.]*

### 4.2 Notifications

*[TO DO — Jorge: write this subsection.]*

### 4.3 Reports

*[TO DO — Jorge: write this subsection.]*

## LLD 5. Frontend Component Breakdown

**Owner:** Phat Kelvin

*[TO DO — Kelvin: Cover the Customer Storefront and the Staff Dashboard. The handout grades reusable components, so make the sharing between the two SPAs explicit.]*

- *[TO DO — Kelvin: Component tree per SPA, showing which components are shared]*
- *[TO DO — Kelvin: Route table per SPA with the role required for each route]*
- *[TO DO — Kelvin: State management: server state versus local UI state]*
- *[TO DO — Kelvin: API client contract and error handling, including what the user sees on a failed call]*
- *[TO DO — Kelvin: Key wireframes or layout sketches: Cart, checkout, tracking, Preparation Queue]*
- *[TO DO — Kelvin: Reusable component inventory]*

### 5.1 Customer Storefront

*[TO DO — Kelvin: write this subsection.]*

### 5.2 Staff Dashboard

*[TO DO — Kelvin: write this subsection.]*

### 5.3 Shared components

*[TO DO — Kelvin: write this subsection.]*

## LLD 6. Database Detail and API Contracts

**Owner:** Sharma Anuj

*[TO DO — Anuj: Take the Part I data model to implementation level.]*

- *[TO DO — Anuj: Full column list per table: type, nullability, defaults, constraints]*
- *[TO DO — Anuj: Indexes and the query each one serves]*
- *[TO DO — Anuj: Foreign keys and cascade behavior]*
- *[TO DO — Anuj: Transaction boundaries, especially Order creation with the Stock decrement]*
- *[TO DO — Anuj: Request and response JSON for all 20 endpoints from the Part I API Overview, with status codes and error bodies]*

### 6.1 Tables

*[TO DO — Anuj: write this subsection.]*

### 6.2 Indexes and transactions

*[TO DO — Anuj: write this subsection.]*

### 6.3 API contracts

*[TO DO — Anuj: write this subsection.]*

## Backlog

**Owner:** Than Andrian

*[TO DO — Andrian: Andrian inserts the 20 task backlog table here (T01 to T20, 9 required columns). Do not edit. To change a task, edit its Trello card and tell Andrian.]*


# Part B. High-Level Test Plan

## Test Plan 1. Strategy, Methodology and Tools

**Owner:** Sharma Anuj

- *[TO DO — Anuj: Overall approach and how it follows test-driven development. Actual test cases are not required yet.]*
- *[TO DO — Anuj: Test levels: unit, component, integration, system, acceptance. What each one covers here.]*
- *[TO DO — Anuj: Test environments: local development, shared demo, seeded database]*
- *[TO DO — Anuj: Tools and why: pytest for the Flask backend, Vitest for the React frontend, Postman for manual endpoint checks]*
- *[TO DO — Anuj: How external services are handled in test: Stripe test mode, and whether Mapbox is called live or stubbed]*
- *[TO DO — Anuj: Entry and exit criteria, and roles across the six of us]*

*[TO DO — Anuj: Chapter 9 of the text has examples worth following.]*

### 1.1 Test approach

*[TO DO — Anuj: write this subsection.]*

### 1.2 Test levels

*[TO DO — Anuj: write this subsection.]*

### 1.3 Environments and tools

*[TO DO — Anuj: write this subsection.]*

### 1.4 Entry and exit criteria

*[TO DO — Anuj: write this subsection.]*

## Test Plan 2. Functional and Component Test Descriptions

**Owner:** Karnani Shresthkumar

*[TO DO — Shresthkumar: For each component, write the test goal and the expected result. These are descriptions of what will be verified, not test cases.]*

*[TO DO — Shresthkumar: Every business rule needs a named test area, including the boundaries:]*

- *[TO DO — Shresthkumar: BR-1: fee at 19.9 lb, exactly 20.0 lb, and 20.1 lb]*
- *[TO DO — Shresthkumar: BR-2: Trip at 10 Orders, at 200 lb, and one limit reached before the other]*
- *[TO DO — Shresthkumar: BR-3: Order at exactly 200 lb versus 200.1 lb]*
- *[TO DO — Shresthkumar: BR-4: Stock changing between add to Cart and checkout]*
- *[TO DO — Shresthkumar: BR-5: address just inside and just outside the Delivery Zone]*
- *[TO DO — Shresthkumar: BR-7: Dispatch at the 30 minute mark]*
- *[TO DO — Shresthkumar: BR-8: failed delivery path]*
- *[TO DO — Shresthkumar: BR-9: checkout blocked while Delivery Pause is on]*

*[TO DO — Shresthkumar: Also cover payment failure, duplicate submit, and role escalation attempts.]*

| Component | Test goal | Expected result |
|---|---|---|
| Auth & Roles | | |
| Catalog & Inventory | | |
| Cart & Pricing | | |
| Address Validation | | |
| Payments | | |
| Orders | | |
| Delivery Planning | | |
| Route Optimizer | | |
| Robot Fleet | | |
| Order Tracking | | |
| Notifications | | |
| Reports | | |
| Customer Storefront | | |
| Staff Dashboard | | |

## Test Plan 3. Metrics and Success Criteria

**Owner:** Notario Ethan Rodriguez

- *[TO DO — Ethan: Metrics: coverage percentage, pass rate, defect density, defects per component, open defects by severity]*
- *[TO DO — Ethan: Success criteria with actual target numbers for each metric]*
- *[TO DO — Ethan: Defect severity and priority definitions, and the triage process]*
- *[TO DO — Ethan: How the measurable goals from Requirement section 1 are verified: Order placed in under 3 minutes, 95 percent of Trips traffic-optimized, Inventory queried and updated in under 2 minutes]*
- *[TO DO — Ethan: Reporting cadence and where results are recorded]*

*[TO DO — Ethan: Use the same numbers as the Requirement Document goals.]*

### 3.1 Metric definitions for the Reports component

The delivery and sales metrics below are computed by the Reports component, `backend/app/blueprints/reports.py`. The definitions are copied verbatim from that module's header so the Test Plan and the code cannot drift apart — LLD 4 requires that "metric definitions must be identical wherever they appear", and `reports.py` states the same requirement against this document. Every metric is read from `GET /api/reports/sales`, `GET /api/reports/inventory` and `GET /api/reports/delivery`, all of which are Manager-only.

| Metric | Definition |
|---|---|
| Sales orders | Every Order in the period except Cancelled. Period = created_at, UTC, inclusive dates. |
| Revenue | sum(Order.total) = subtotal + delivery fee. |
| Average order value | revenue / order count (0 when there are no orders). |
| Product demand | units sold and line revenue per Product over the sales orders. |
| Delivery success rate | Delivered / (Delivered + Delivery Failed). None when neither exists. |
| On-time rate | delivered stops that arrived at or before their estimated arrival (set when the Trip was dispatched) / delivered stops that have an ETA. Stops belong to the period of their Order. None when there are none. |
| Delivery duration | minutes from the Order being placed to the Robot arriving at its stop, averaged over those same delivered stops. None when there are none. |
| Trip utilization | over Trips dispatched in the period: average orders per Trip, and the average fill of the Robot limits (orders / TRIP_MAX_ORDERS, weight / TRIP_MAX_WEIGHT_LB). None when no Trip went out. |

### 3.2 Targets and how each metric is measured

| Metric | Target | How measured |
|---|---|---|
| | | |
