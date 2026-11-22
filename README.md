# OFS On-Demand Food Delivery (CS160 Team 5)

Web app for organic food delivery in Downtown San Jose.
Self-driving Robots carry up to 10 Orders / 200 lb per Trip.

## Stack

- **Frontend:** React + TypeScript + Vite + React Router + Tailwind CSS
- **Backend:** Flask REST API (Python) + SQLAlchemy, served by gunicorn
- **DB:** PostgreSQL via [Supabase](https://supabase.com) (free tier)
- **Maps & routing:** Mapbox GL JS, Geocoding API, Optimization API (`driving-traffic`)
- **Payments:** Stripe (test mode)
- **Auth:** Flask-Login, session-based

Apache (deployment reverse proxy) is set up in the Docker config (see Docker Setup). Not yet set up, but in the Part I HLD: Vitest (frontend tests).

## Team Roles (Part I)

| Person | Owns |
|---|---|
| P1 | Problem statement + 3 personas |
| P2 | 5 user stories + 1 flow diagram |
| P3 | Component architecture diagram |
| P4 | Component feature list + descriptions |
| P5 | Tools list + setup README |
| PM | Editor + integration + submission |

## Cadence

- Weekly meeting Mon [time]
- Async status by Fri 9pm in shared Doc
- Stuck >2hrs → ping teammate before PM

## Project Layout

```
/frontend/storefront/       → Customer Storefront (Vite + React + Tailwind + React Router)
/frontend/staff-dashboard/  → Staff Dashboard (Vite + React + Tailwind + React Router)
/frontend/shared/           → Shared auth, API, form, navigation, and layout package
/backend/                   → Flask API (app factory + blueprints, one per component group)
/backend/app/models/        → SQLAlchemy models, see LLD for the schema
/backend/tests/             → pytest
/ui-prototype/               → Standalone click-through HTML/JS mockup, no backend — see its own README
```

Every backend route is a stub (`501 not_implemented`) tagged with its owning backlog
task — e.g. `app/blueprints/cart.py` says `T08, Than Andrian`. Check
[Trello](https://trello.com/b/aw6ohAFJ) for the task card and pseudo code.

## Setup

Two ways to run the project. **Docker** needs only Docker; **local development** needs Python and
Node and reloads on every change. Commands are for macOS/Linux; Windows notes are inline.

### Docker (quickest)

Runs the Flask API (gunicorn) and both React apps (Apache, with `/api` proxied to the API) in
containers. You need Docker with Compose v2. Storefront: http://localhost:8080. Staff dashboard:
http://localhost:8081.

**Quick start: private database with demo data, no accounts needed** (use this to try or test it):
```
AUTO_SEED=1 docker compose -f docker-compose.yml -f docker-compose.localdb.yml up -d --build
```
PowerShell: `$env:AUTO_SEED=1; docker compose -f docker-compose.yml -f docker-compose.localdb.yml up -d --build`.
When `docker compose ps` shows the backend as healthy (under a minute), open the URLs above and log in
(see [Log in](#log-in)). This starts its own PostgreSQL container, creates the tables and loads the
demo data:

- 38 products in 6 categories (one low-stock, one out-of-stock, one inactive). `Spring Water (case
  of 24)` weighs 26 lb: one case triggers the $10 fee and 8 cases (208 lb) are blocked (Scenario 3).
- About 80 orders over the last 14 days in every status, with payments, trips, three Robots, a
  Manager cancel with a reason and stock edits, so the reports have numbers.
- Live state: new orders in the prep queue, a trip ready to dispatch, and a trip out for delivery
  with a Robot partway along its route (so the Track page has something to show).

`AUTO_SEED` is **off by default**: without it nothing is created. It is safe to leave on (it only adds
what is missing, and loads order history only into a database with no orders) and it **refuses to run
against the shared Supabase database**.

**Reset to a clean slate** (deletes every table and all data in the private database, then seeds again;
the stack can stay running):
```
docker compose -f docker-compose.yml -f docker-compose.localdb.yml run --rm backend python seed_demo.py --reset
```
`--reset` only works on the local database (Docker or a SQLite file) and always refuses Supabase.
Without Docker: `cd backend && python seed_demo.py --reset`. To delete the database volume instead, add
`down -v` to the same compose command.

**Checkout and the address map need keys** (everything else works without them). Put the server keys
in `backend/.env` (copy `backend/.env.example`, see [Backend settings](#backend-settings)) and the two
public browser keys in a root `.env` (copy `.env.example`):
```
VITE_STRIPE_PUBLISHABLE_KEY=pk_test_...
VITE_MAPBOX_TOKEN=pk....
```
The `VITE_*` values are baked into the storefront at **build** time and blank values fail silently, so
after changing them run `docker compose build storefront`. After changing `backend/.env` run
`docker compose up -d --force-recreate backend`.

**With the team's Supabase database:** put its connection string in `backend/.env` (see
[Database](#database)), then start everything, with or without the Stripe forwarder:
```
docker compose up -d --build                        # backend + both apps
docker compose --profile stripe up -d --build       # the same, plus the Stripe webhook forwarder
```
There is no `AUTO_SEED` here: the shared database already has its data, and `AUTO_SEED=1` refuses to
run against it. Seeding it would add the demo products and customers to the team's real data; if
that is really what you want, run `docker compose run --rm backend python seed_demo.py` by hand
(order history is only added to a database with no orders). Stop with
`docker compose --profile stripe down`. Until you do, the backend and both apps restart on their own
after a crash, a reboot or a Docker restart (`restart: unless-stopped`).

**Stripe webhooks** (an order is only created when Stripe's webhook arrives): add the optional
`stripe` service, which uses `STRIPE_SECRET_KEY` from `backend/.env`:
```
# Supabase:
docker compose --profile stripe up -d --build
# Private database with demo data (all in one):
AUTO_SEED=1 docker compose -f docker-compose.yml -f docker-compose.localdb.yml --profile stripe up -d --build
docker compose logs stripe          # prints "Your webhook signing secret is whsec_..." (add the same -f flags)
```
Put that `whsec_...` in `backend/.env` as `STRIPE_WEBHOOK_SECRET` (once; it stays the same), then
`docker compose up -d --force-recreate backend`. Test with the checkout page and card
`4242 4242 4242 4242`; `stripe trigger` fails on the newest Stripe API version.

**Which Stripe webhook option should I use?**

| You are running | Use | Notes |
|---|---|---|
| In Docker | the `stripe` service above | Starts with the stack, needs no Stripe CLI install, and authenticates with `STRIPE_SECRET_KEY`, so there is no login to expire. The signing secret stays the same across restarts |
| Locally without Docker (macOS) | `cd backend && ./start_stripe_listener.sh` | Starts the Stripe CLI on your machine, and writes the new signing secret into `backend/.env`. It forwards to port 5001 by default (`PORT=5000 ./start_stripe_listener.sh` for 5000), needs `stripe login` first (that login expires about daily), and uses macOS `sed`, so on Linux run `stripe listen` yourself (see Local development) |
| A real, public deployment | a webhook endpoint created in the Stripe Dashboard | Point it at `https://<your-site>/api/payments/webhook` and put its `whsec_...` in the server's `STRIPE_WEBHOOK_SECRET`. No CLI runs next to the backend. Neither option above is meant for this |

**Docker troubleshooting.** Run `docker compose logs --tail 40 backend` and read the last error.

| Symptom | Cause and fix |
|---|---|
| "Could not load products" but the backend is healthy | The database is unreachable; see the next rows |
| `Network is unreachable`, host `db.<ref>.supabase.co` | The Direct address is IPv6-only and Docker has no IPv6. Use the **Session pooler** string |
| `connection to server at "localhost" ... refused` | `DATABASE_URL` isn't being read. Check the name is spelled exactly `DATABASE_URL` (a typo like `DATABASE_UR` is silently ignored) |
| `Tenant or user not found` / `password authentication failed` | Wrong region or `postgres.<ref>` user (copy the string again), or brackets or a space in the password |
| `AUTO_SEED refused` | `DATABASE_URL` points at a non-local database. Use the local database override, or seed by hand |
| Backend stops answering after the computer sleeps | Its database connections died during sleep. It now drops them and reconnects within about 30 seconds; if yours stays frozen, the image predates that fix: `docker compose up -d --build backend` |
| Checkout form or address map blank | `VITE_*` keys were blank at build time; fill the root `.env` and rebuild the storefront |

### Local development

**1. Install:** [Git](https://git-scm.com/downloads), [Python](https://www.python.org/downloads/) 3.12+
(the team uses 3.14), [Node.js](https://nodejs.org/) 22 LTS, and optionally the
[Stripe CLI](https://github.com/stripe/stripe-cli/releases).

**2. Clone and install the backend:**
```
git clone https://github.com/andrianthan/cs160-team5-ofs.git && cd cs160-team5-ofs
cd backend
python3 -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env                                   # then fill it in (next section)
```
Activate the venv in every new backend terminal. (SQLAlchemy is pinned to 2.0.x because 2.1 looks
for the `psycopg` driver instead of our `psycopg2`.)

#### Backend settings

`backend/.env` is gitignored: never commit it or paste its contents anywhere.

| Setting | Needed for | Where to get it |
|---|---|---|
| `DATABASE_URL` | everything | the next section |
| `SECRET_KEY` | login sessions | any long random string |
| `STRIPE_SECRET_KEY` | checkout | [Stripe dashboard](https://dashboard.stripe.com) (test mode) → Developers → API keys → `sk_test_...` |
| `STRIPE_WEBHOOK_SECRET` | payment webhooks (optional) | `stripe listen --print-secret` |
| `MAPBOX_ACCESS_TOKEN` | address validation | [Mapbox](https://account.mapbox.com) → Access tokens → default public token `pk....` |
| `SMTP_*` | order emails (optional) | without `SMTP_HOST`, emails are skipped and recorded as `skipped` |

#### Database

**A. The team's shared Supabase database (normal setup).** In the Supabase dashboard click
**Connect → Direct → Connection String** and set **Method** to **Session pooler** (not "Direct
connection" or "Transaction pooler"). The string looks like
`postgresql://postgres.[PROJECT-REF]:[YOUR-PASSWORD]@aws-0-[REGION].pooler.supabase.com:5432/postgres`.
Replace `[YOUR-PASSWORD]` with the password (no brackets), add `?sslmode=require`, and put it in
`backend/.env`:
```
DATABASE_URL=postgresql://postgres.[PROJECT-REF]:[DB-PASSWORD]@aws-0-[REGION].pooler.supabase.com:5432/postgres?sslmode=require
```
Don't use the Direct address (`db.[PROJECT-REF].supabase.co`): it needs IPv6, which many networks and
Docker lack. The tables and demo data already exist there: **don't run the seed** against it. Every
table has row-level security on, so Supabase's public key can read nothing; the backend connects as the
tables' owner and is unaffected. Project owner: use a letters-and-digits password (`@ # / %` break the
URL) and run `flask --app app:create_app db upgrade` once after any PR with a new migration merges.

**B. A private local database (offline, your own data).** Set `DATABASE_URL=sqlite:///demo.db`, then
`python seed_demo.py` (creates `backend/instance/demo.db` with the same demo data as Docker). To start
over, run `python seed_demo.py --reset`.

**3. Frontend:** from the repo root run `npm install` (one install covers both apps and the shared
package). The storefront also needs two **public** keys in `frontend/storefront/.env` (gitignored;
restart Vite after changing it):
```
VITE_STRIPE_PUBLISHABLE_KEY=pk_test_...
VITE_MAPBOX_TOKEN=pk....
```

**4. Run it**, one terminal each:

| Terminal | Command | Opens |
|---|---|---|
| Backend | `cd backend && source .venv/bin/activate && python run.py` | http://localhost:5000/api/health |
| Storefront | `npm run dev:storefront` (repo root) | http://localhost:5173 |
| Staff dashboard | `npm run dev:staff` (repo root) | http://localhost:5174 |

Both apps forward `/api/*` to the backend on port 5000, so there are no CORS issues. Optional Stripe
webhooks (checkout also polls Stripe, so orders get placed without them):
```
stripe login
stripe listen --events payment_intent.succeeded,payment_intent.payment_failed,payment_intent.canceled \
  --forward-to localhost:5000/api/payments/webhook      # put the printed whsec_... in STRIPE_WEBHOOK_SECRET
```

### Log in

| Role | Email | Password | Use it in |
|---|---|---|---|
| Customer | `customer@example.com` | `customer123` | Storefront |
| Employee | `employee@example.com` | `employee123` | Staff dashboard |
| Manager | `manager@example.com` | `manager123` | Staff dashboard (includes Reports) |

The demo data also has customers `dana@`, `sam@`, `priya@`, `leo@` and `mia@example.com` (all
`customer123`). Test card: `4242 4242 4242 4242`, any future expiry, any CVC. Test addresses must be
inside the Downtown San Jose delivery zone (e.g. `200 E Santa Clara St, San Jose`).

### Checks and keeping up to date

```
cd backend && pytest        # backend tests (in-memory database; never touches yours)
npm run typecheck && npm run lint && npm run build        # repo root
```
After `git pull`: `pip install -r requirements.txt` if it changed, `npm install` if
`package-lock.json` changed. If the pull added a migration (a new file in `backend/migrations/versions/`):
run `flask --app app:create_app db upgrade` on a local database; on the shared Supabase database the
project owner does it once and nobody else does.

### Troubleshooting (local development)

- *Changes don't show up in Supabase.* Check the ` * Database: ...` line `python run.py` prints. A
  `DATABASE_URL` exported in your terminal overrides `backend/.env`: run `unset DATABASE_URL` and restart.
- *"table ... already exists" when seeding.* The SQLite file predates migrations: delete
  `backend/instance/demo.db` and seed again.
- *Port 5000 is taken (macOS AirPlay Receiver).* Turn that off, or start the backend with
  `PORT=5001 python run.py` and each frontend with `API_URL=http://localhost:5001 npm run dev:staff`
  (or `dev:storefront`); change the Stripe `--forward-to` port too.
- *Vite: "Cannot find native binding" / `@tailwindcss/oxide-darwin-arm64` (macOS).* The lockfile
  lists only the Linux binaries. Run
  `npm install --no-save @tailwindcss/oxide-darwin-arm64@4.3.3 -w staff-dashboard -w storefront`
  (`oxide-darwin-x64` on Intel Macs).

## Shared Frontend Package

The root npm workspace automatically links both Vite apps to `@ofs/shared` in
`frontend/shared`. The repository uses one root `package-lock.json` and one
dependency tree. The shared package contains:

- `AuthProvider`, `useAuth`, and the shared `AuthContext`
- `RequireAuth` with optional role checks
- the shared customer/staff login page
- the shared API client
- shared headers, navigation links, account menu, form fields, errors, and placeholders

The storefront configures `AuthProvider` with `portal="customer"`. The staff
dashboard uses `portal="staff"`; its operational pages accept Employee and
Manager accounts, while Reports accepts Manager accounts only. Cart and Product
code remains in the storefront because the staff dashboard does not use it.
