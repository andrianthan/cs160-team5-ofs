---
title: "User's Guide"
subtitle: "Basil — OFS On-Demand Food Delivery · CS 160 Fall 2026 · Group 5"
---

# User's Guide

Basil is an organic grocery store for Downtown San Jose that delivers by robot. It has two web apps
and one backend:

| Part | Who uses it | Address after installing |
|---|---|---|
| **Storefront** | Customers: browse, cart, pay, track the delivery robot | http://localhost:8080 |
| **Staff dashboard** | Employees and Managers: prepare orders, dispatch robots, inventory, reports | http://localhost:8081 |
| **Backend API** | Both apps (Flask + PostgreSQL). Not opened directly | proxied at `/api` on both addresses |

Contents: [1. Installation](#1-installation) · [2. Configuration](#2-configuration) ·
[3. Sample data](#3-sample-data) · [4. Using the Storefront](#4-using-the-storefront-customers) ·
[5. Using the Staff dashboard](#5-using-the-staff-dashboard-employees-and-managers) ·
[6. A complete walkthrough](#6-a-complete-walkthrough) · [7. Customization](#7-customization) ·
[8. Troubleshooting](#8-troubleshooting) · [9. Stopping, updating, removing](#9-stopping-updating-and-removing)

---

## 1. Installation

You need **Docker Desktop** (Windows, macOS) or **Docker Engine with Compose v2** (Linux). Nothing
else: no Python, Node or database install. Check with `docker compose version`. The first start
downloads and builds the images and takes a few minutes; later starts take seconds.

### Option A — From the repository, with its own database (recommended for testing)

This runs everything on your laptop, including a private PostgreSQL database that is filled with the
sample data on first start. No accounts or passwords are needed to start it.

```
git clone https://github.com/andrianthan/cs160-team5-ofs.git
cd cs160-team5-ofs
AUTO_SEED=1 docker compose -f docker-compose.yml -f docker-compose.localdb.yml up -d --build
```

Windows PowerShell, third line:
`$env:AUTO_SEED=1; docker compose -f docker-compose.yml -f docker-compose.localdb.yml up -d --build`

Wait until the backend is healthy (under a minute after the build):

```
docker compose -f docker-compose.yml -f docker-compose.localdb.yml ps
```

Then open http://localhost:8080 (Storefront) and http://localhost:8081 (Staff dashboard) and log in
with an account from [section 3](#3-sample-data).

`AUTO_SEED=1` is safe to leave on: it only adds sample data that is missing, and it refuses to run
against any database that is not the local one.

### Option B — Without cloning, from prebuilt images

The images are published to GitHub's container registry on every change. Download one file and run:

```
curl -LO https://raw.githubusercontent.com/andrianthan/cs160-team5-ofs/main/docker-compose.ghcr.yml
AUTO_SEED=1 docker compose -f docker-compose.ghcr.yml --profile localdb up -d
```

Nothing is built, so this starts in about a minute. It is for looking around: this file has no Stripe
webhook forwarder, and the Storefront's Stripe and Mapbox keys are built in only if the repository
owner configured them (see [2.3](#23-prebuilt-images-option-b)). To place new orders, use Option A.

### Option C — The team's shared Supabase database

For team members only. Put the Supabase connection string in `backend/.env` as `DATABASE_URL`
(see the README, "Database"), then `docker compose up -d --build`. Do not seed it: it already has
its data.

After any option, the containers restart on their own after a crash or a reboot until you stop them
([section 9](#9-stopping-updating-and-removing)).

---

## 2. Configuration

The app starts and the sample data can be browsed with no configuration at all. **Placing a new
order needs two free accounts**: Stripe (test mode, for payment) and Mapbox (for address lookup and
robot routes). Email notifications are optional.

| Without | What stops working | Everything else |
|---|---|---|
| Stripe keys | Paying at checkout ("Payments are temporarily unavailable") | Works |
| Mapbox token | Address check at checkout ("We couldn't find that address"), address autofill. Robot routes fall back to a straight nearest-stop order | Works |
| SMTP settings | Order status emails (they are recorded as skipped) | Works |

### 2.1 Where settings go

There are two settings files, both plain `NAME=value` lines. Neither is ever committed.

| File | Read by | Holds |
|---|---|---|
| `backend/.env` (copy `backend/.env.example`) | the backend, when its container starts | `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`, `MAPBOX_ACCESS_TOKEN`, `SMTP_*`, `DATABASE_URL` (Option C only) |
| `.env` in the repository root (copy `.env.example`) | the Storefront, **when its image is built** | `VITE_STRIPE_PUBLISHABLE_KEY`, `VITE_MAPBOX_TOKEN` |

After changing `backend/.env`: `docker compose ... up -d --force-recreate backend`.
After changing the root `.env`: rebuild the Storefront, `docker compose ... up -d --build storefront`.
Use the same `-f` flags you started with.

### 2.2 Getting the keys (about 10 minutes, both free)

**Stripe, test mode** (no real money moves):

1. Create an account at https://dashboard.stripe.com/register. You do not need to activate payments.
2. Make sure **Test mode** is on, then open **Developers → API keys**.
3. Copy the **Publishable key** (`pk_test_...`) into the root `.env` as `VITE_STRIPE_PUBLISHABLE_KEY`.
4. Copy the **Secret key** (`sk_test_...`) into `backend/.env` as `STRIPE_SECRET_KEY`.
5. Orders are created when Stripe's webhook reaches the backend. Start the bundled forwarder by adding
   `--profile stripe` to your start command, for example:
   ```
   AUTO_SEED=1 docker compose -f docker-compose.yml -f docker-compose.localdb.yml --profile stripe up -d --build
   docker compose -f docker-compose.yml -f docker-compose.localdb.yml logs stripe
   ```
   The log prints `Your webhook signing secret is whsec_...`. Put that value in `backend/.env` as
   `STRIPE_WEBHOOK_SECRET` and recreate the backend. You only do this once; the secret stays the same.

**Mapbox:**

1. Create an account at https://account.mapbox.com/auth/signup.
2. On the **Access tokens** page, copy the **Default public token** (`pk.ey...`).
3. Put it in **both** places: `backend/.env` as `MAPBOX_ACCESS_TOKEN` and the root `.env` as
   `VITE_MAPBOX_TOKEN`.

**Email (optional).** With a Gmail account that has 2-Step Verification, create an app password at
https://myaccount.google.com/apppasswords and run, from the `backend` folder of a local Python setup,
`python set_smtp_credentials.py` (it writes the settings and sends a test email). Or set
`SMTP_HOST=smtp.gmail.com`, `SMTP_PORT=587`, `SMTP_USERNAME`, `SMTP_PASSWORD` in `backend/.env` by hand.

### 2.3 Prebuilt images (Option B)

`docker-compose.ghcr.yml` reads a `.env` file **next to it** instead of `backend/.env`, with the same
backend settings. The Storefront keys cannot be added afterwards because they are built into the image;
the repository owner sets them as GitHub repository variables (README, "Docker without cloning").

---

## 3. Sample data

The first start with `AUTO_SEED=1` loads:

| What | Details |
|---|---|
| Accounts | See below. All passwords are shown here; this is demo data only |
| Catalog | 38 organic products in Produce, Dairy, Bakery, Pantry and more, including a 26 lb case of water that triggers the delivery fee on its own, a few low-stock and out-of-stock items, and inactive products |
| Robots and trips | Three robots, `OFS-R1` to `OFS-R3`. `OFS-R1` is out on a live trip, stopped partway along its route; select **Next stop** on Dispatch to move it on. Two more trips of prepared orders are waiting, one of them ready to dispatch, so Dispatch can be tried without placing an order |
| Order history | Two weeks of orders from six customers in every status (delivered, failed, cancelled, under review, out for delivery…), with payments, completed robot trips and an inventory log, so Reports has numbers from the first minute |
| A saved cart | `customer@example.com` starts with items in the cart |

| Role | Email | Password | Log in at |
|---|---|---|---|
| Customer | `customer@example.com` | `customer123` | Storefront |
| Employee | `employee@example.com` | `employee123` | Staff dashboard |
| Manager | `manager@example.com` | `manager123` | Staff dashboard |
| More customers | `dana@`, `sam@`, `priya@`, `leo@`, `mia@example.com` | `customer123` | Storefront |

**Test card:** `4242 4242 4242 4242`, any future expiry date, any CVC, any ZIP.

**Addresses inside the delivery zone** (Downtown San Jose): `200 E Santa Clara St, San Jose`,
`110 S Market St, San Jose`, `345 Park Ave, San Jose`, `201 S 2nd St, San Jose`,
`150 W San Carlos St, San Jose`. An address outside downtown is refused at checkout.

**Start over with fresh sample data** (deletes everything in the local database, never touches Supabase):

```
docker compose -f docker-compose.yml -f docker-compose.localdb.yml run --rm backend python seed_demo.py --reset
```

---

## 4. Using the Storefront (customers)

Open http://localhost:8080. Every page has the top bar with Browse, Cart, Orders and Track.

### Sign in or create an account
**Log in** with a sample customer, or choose **Create account** and enter your full name, email and a
password. New accounts are always customers; staff accounts cannot be created from the Storefront.

### Browse and search (`/browse`)
- Type in **Search products** to filter by name, or pick a **category**.
- Each tile shows price, weight and stock. Low-stock items are marked; out-of-stock items cannot be added.
- Select a product to see its details. **Add to cart** adds one; the button then shows how many are in the cart.
- Hover over the cart icon for a quick preview of the cart.

### Cart (`/cart`)
- Change quantities with **+** and **−**, or remove a line.
- The cart shows **Subtotal**, **Order Weight**, **Delivery Fee** and **Total**, updated as you change it:
  - Under 20 lb: delivery is free.
  - 20 lb or more: a $10 delivery fee is added.
  - Over 200 lb: a robot cannot carry it, and checkout is blocked until you remove items.
- Your cart is saved to your account, so it is still there after you log out or switch devices.

### Checkout (`/checkout`)
1. **Delivery address:** start typing and pick a suggestion. The address must be inside the Downtown
   San Jose delivery zone; otherwise checkout explains why and does not continue.
2. **Payment:** enter the test card. Select **Pay**.
3. The page shows *Payment received. Confirming your order.* and then the confirmation. The order
   appears in Orders within a few seconds (it is created when Stripe confirms the payment).

If the store has paused deliveries, checkout shows a notice and **Pay** is disabled; try again later.
If a payment fails, nothing is charged and no order is placed.

### Your orders (`/orders`)
Every order you have placed, newest first, with its items, subtotal, delivery fee, total and status:
*Order placed → Preparing delivery → Out for delivery → Delivered*, or *Delivery failed*,
*Under review* or *Cancelled*.

### Track a delivery (`/track`)
Choose an order to see its status, delivery address, delivery trip and the **Robot location** on a
live street map. While the order is out for delivery, the robot's marker moves along its route
and the page refreshes on its own. You receive an email when the order is placed, goes out for
delivery and is delivered (if email is configured).

---

## 5. Using the Staff dashboard (employees and managers)

Open http://localhost:8081 and log in as the employee or the manager. Customers cannot sign in here.

| Page | Employee | Manager |
|---|---|---|
| Preparation Queue | Prepare orders, move to Manual Review | Same, plus **Cancel Delivery** |
| Dispatch | Dispatch trips, Next stop, robot offline/online | Same, plus **Pause/Resume deliveries**, **Add robot**, **Remove** |
| Inventory | View products and stock | Same, plus edit, create and delete products |
| Reports | — | Sales, product demand, inventory and delivery performance |

### 5.1 Preparation Queue (`/queue`)
Orders from the Storefront arrive here; the page refreshes every 30 seconds (or select **Refresh**).
Three tabs:

- **To prepare** — newly placed orders. Pack the items, then select **Mark Prepared**. The order is
  put on a delivery trip automatically (see 5.2). If something is wrong with an order, select
  **Manual Review** instead.
- **Prepared** — packed orders waiting for a robot.
- **Manual Review** — orders that need a person to decide, including any order too heavy for a robot.

**Managers only — Cancel Delivery:** cancels an order after it was placed. You must enter a reason; the
cancellation is recorded with your name and the reason, the items go back into stock, and the
customer is notified. This cannot be undone.

### 5.2 Dispatch (`/dispatch`)
How trips are formed, automatically: prepared orders whose addresses are within 0.5 km of each other
and that were placed within 30 minutes of each other share a trip. A trip holds at most 10 orders and
200 lb. It becomes **Ready to dispatch** when it is full, or when its oldest order is 30 minutes old
(it then shows *past 30-min deadline* if it is still waiting).

The page has three parts:

- **Live map** — the store, the robots (dark labels; red means offline), the stops of dispatched trips
  (numbered circles; green when delivered) and prepared orders (small dots).
- **Trips** — every trip with its orders, weight and deadline.
  - **Dispatch** sends a free robot on the trip, along a route optimized by Mapbox, with an ETA for
    every stop. It is disabled when no robot is free. You may dispatch a trip before it is full.
  - The robot then drives itself: each stop is delivered in turn, the customer is emailed, and the
    robot returns to the store and the trip completes.
  - **Next stop** skips ahead: the robot goes straight to its next stop and delivers it (or returns to
    the store after the last one). Use it to speed up a demo, or to finish a trip that stopped moving
    because the backend restarted.
- **Robots** — each robot's status (*Available*, *Reserve*, *Loading*, *Out for delivery*,
  *Returning*, *Offline*).
  - **Take offline** removes a robot at the store from service (maintenance); **Back online** returns it.
    A robot out on a trip cannot be taken offline.
  - **Managers: + Add robot** adds a robot at the store with the next name (`OFS-R4`, ...).
    **Remove** deletes a robot that is at the store or offline; its past trips are kept.
  - **Managers: Pause deliveries** stops customers from checking out (for weather, an outage, ...);
    **Resume deliveries** reopens checkout. Orders already placed are not affected.

### 5.3 Inventory (`/inventory`)
All products, including inactive ones, with search. Employees can view only.

Managers can:
- Change **price** and **stock** directly in the row (the **+** and **−** buttons change stock by one).
- Open a product to **edit** its name, category, price, weight, stock and low-stock alert level, and
  to make it available or unavailable to customers. Every stock change, including each sale and
  cancellation, is recorded in the inventory log (read through the API at
  `GET /api/products/<id>/inventory-log`).
- **Create** a product, or **delete** one. A product that has orders or stock history cannot be deleted,
  only made unavailable, so past orders stay intact. A product whose stock reaches zero is hidden
  from customers automatically.

### 5.4 Reports (`/reports`, managers only)
Choose a **From** and **To** date. The page shows:

- **Sales** — orders, revenue, average order, delivery fees, and revenue by day.
- **Product demand** — units sold by product and by category.
- **Inventory** — units in stock, low-stock and out-of-stock products that need attention.
- **Delivery performance** — delivered and failed counts, success rate, **on-time rate** (stops that
  arrived by the ETA set at dispatch), average delivery time (from order to arrival), trips dispatched
  and **robot load** (average share of the 10-order and 200 lb limits).

The sample data covers the last two weeks, so the default range already shows numbers.

---

## 6. A complete walkthrough

About ten minutes, after [Stripe and Mapbox keys](#22-getting-the-keys-about-10-minutes-both-free)
are set. Use two browser windows, one per app.

**No keys yet?** Skip steps 1–3: log in to the Staff dashboard as the manager, open **Dispatch**, and
dispatch the trip that is ready (or select **Next stop** on `OFS-R1`'s trip). Then log in to the
Storefront as `customer@example.com` (who owns most of the sample orders) and follow one on **Track**. Steps 6 and 7 work as written.

1. **Storefront** — log in as `customer@example.com`. Search "water", add the case of water and a few
   other items. In the cart, see the $10 fee appear at 20 lb.
2. Check out with `200 E Santa Clara St, San Jose` and card `4242 4242 4242 4242`. Open **Orders**:
   the order is *Order placed*.
3. **Staff dashboard** — log in as `manager@example.com`. On **Preparation Queue**, select
   **Mark Prepared** on the new order.
4. Open **Dispatch**: the order is on a trip. Select **Dispatch**. The robot leaves the store on the map.
5. Back in the **Storefront**, open **Track** and choose the order: the robot moves toward the address,
   and the status changes to *Out for delivery*, then *Delivered*. (Select **Next stop** on Dispatch to
   hurry it along.)
6. On **Dispatch**, select **Pause deliveries**, and refresh Storefront checkout: Pay is disabled with
   a notice. Select **Resume deliveries**.
7. Open **Reports** to see today's order counted in sales and delivery performance. Open **Inventory**
   to see the stock reduced by what you bought.

---

## 7. Customization

| To change | Where | Then |
|---|---|---|
| Products, prices, stock | Inventory page (Manager) | Nothing; takes effect immediately |
| Robots in the fleet | Dispatch page (Manager): Add robot / Remove | Immediately |
| Business rules: free-delivery weight (20 lb), fee ($10), trip limits (10 orders, 200 lb), dispatch deadline (30 min), trip grouping radius (0.5 km) | `backend/app/config.py`, class `Config` | Rebuild the backend: `docker compose ... up -d --build backend` |
| Robot speed (for demos) | `backend/.env`: `ROBOT_SIM_TICK_S` (seconds per step, default 1), `ROBOT_SIM_STEPS` (steps per leg, default 10), `ROBOT_SIM_DWELL_S` (seconds at each stop, default 3) | Recreate the backend |
| Delivery zone boundary | `backend/app/blueprints/addresses.py`, `inside_delivery_zone` | Rebuild the backend |
| Sample data (accounts, catalog, history) | `backend/demo_data.py` | `seed_demo.py --reset` (section 3) |
| Email sender name | `backend/.env`: `SMTP_FROM` (default "Basil &lt;your address&gt;") | Recreate the backend |
| Database | `backend/.env`: `DATABASE_URL` (any PostgreSQL 16+) | Recreate the backend, then `flask --app app:create_app db upgrade` |

---

## 8. Troubleshooting

Start with the backend log: `docker compose ... logs --tail 40 backend` (with your `-f` flags).

| Symptom | Cause and fix |
|---|---|
| A page says "Could not load products" | The backend is not running or not healthy yet. Check `docker compose ... ps`; wait for *healthy*, or read the log |
| `docker compose` says the port is already allocated | Something else uses 8080 or 8081. Stop it, or change the `ports:` lines in the compose file |
| "Payments are temporarily unavailable" | `STRIPE_SECRET_KEY` is missing in `backend/.env` ([2.2](#22-getting-the-keys-about-10-minutes-both-free)); recreate the backend |
| Payment succeeds but no order appears | The webhook is not arriving: start with `--profile stripe`, and make sure `STRIPE_WEBHOOK_SECRET` equals the `whsec_...` in `logs stripe` |
| The card form or address box is blank | The root `.env` keys were empty when the Storefront was built. Fill them and rebuild the Storefront |
| "We couldn't find that address" for a real address | `MAPBOX_ACCESS_TOKEN` is missing in `backend/.env` |
| "Outside the Downtown San Jose Delivery Zone" | Expected for addresses outside downtown; use one from section 3 |
| A robot stopped moving mid-trip | The backend restarted during the trip. Select **Next stop** on Dispatch to finish it |
| The backend stops answering after the laptop sleeps | It reconnects within about 30 seconds. If it doesn't, the images are old: rebuild with `--build` |
| `AUTO_SEED refused` | `DATABASE_URL` points at a database that is not local. Use Option A, or seed by hand on purpose |

More setup problems and fixes are in the README, "Docker troubleshooting".

---

## 9. Stopping, updating and removing

Use the same `-f` and `--profile` flags you started with.

| To | Run |
|---|---|
| Stop, keeping data | `docker compose -f docker-compose.yml -f docker-compose.localdb.yml down` |
| Start again | the same `up -d` command as before (without `--build` it starts in seconds) |
| Update to the newest code | `git pull`, then the `up -d --build` command |
| Update prebuilt images (Option B) | `docker compose -f docker-compose.ghcr.yml pull`, then `up -d` |
| Remove everything, including the database | `down -v` instead of `down` |
