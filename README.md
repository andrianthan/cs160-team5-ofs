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

Not yet set up, but in the Part I HLD: Apache (deployment reverse proxy), Vitest (frontend tests).

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

Step by step, from a fresh machine to the app running locally. Commands are for macOS/Linux
(bash/zsh); Windows notes are inline.

### 1. Install the tools

| Tool | Version | Check with |
|---|---|---|
| [Git](https://git-scm.com/downloads) | any recent | `git --version` |
| [Python](https://www.python.org/downloads/) | 3.12 or newer (the team uses 3.14) | `python3 --version` |
| [Node.js](https://nodejs.org/) (includes npm) | 22 LTS | `node --version` |
| [Stripe CLI](https://github.com/stripe/stripe-cli/releases) | optional, for payment webhooks | `stripe --version` |

### 2. Clone the repository

```
git clone https://github.com/andrianthan/cs160-team5-ofs.git
cd cs160-team5-ofs
```

### 3. Backend: Python environment

```
cd backend
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Activate the venv (`source .venv/bin/activate`) in every new terminal you use for the backend.
SQLAlchemy is pinned to 2.0.x because 2.1 looks for the `psycopg` driver instead of our `psycopg2`.

### 4. Backend: secrets and settings (`backend/.env`)

```
cp .env.example .env
```

Then fill in `backend/.env`. It's gitignored: never commit it or paste its contents anywhere.

| Setting | Needed for | Where to get it |
|---|---|---|
| `DATABASE_URL` | everything | step 5 |
| `SECRET_KEY` | login sessions | any long random string |
| `STRIPE_SECRET_KEY` | checkout | [Stripe dashboard](https://dashboard.stripe.com) (test mode) → Developers → API keys → `sk_test_...` |
| `STRIPE_WEBHOOK_SECRET` | payment webhooks (optional) | `stripe listen --print-secret` (step 7) |
| `MAPBOX_ACCESS_TOKEN` | address validation at checkout | [Mapbox account](https://account.mapbox.com) → Access tokens → default public token `pk....` |
| `SMTP_*` | order emails (optional) | without `SMTP_HOST`, emails are skipped and recorded as `skipped` |

### 5. Database: pick one

**A. The team's shared Supabase database (normal setup).** The project owner sends you the
connection string privately. In the Supabase dashboard it's under
**Connect → Connection string → Method: Session pooler**:
```
DATABASE_URL=postgresql://postgres.[PROJECT-REF]:[DB-PASSWORD]@aws-0-[REGION].pooler.supabase.com:5432/postgres?sslmode=require
```
Use the **Session pooler**, not "Direct connection" (the direct `db.[PROJECT-REF].supabase.co`
address needs IPv6, which many networks lack). The tables and demo data already exist there:
**don't run the seed** against the shared database.

**B. A private local database (works offline, your own data).** Set
```
DATABASE_URL=sqlite:///demo.db
```
then create the tables and demo data (the file lands in `backend/instance/demo.db`):
```
set -a; source .env; set +a      # load .env into this terminal
python seed_demo.py
```
To start over, delete `backend/instance/demo.db` and run the seed again.

### 6. Frontend: install and keys

From the **repository root** (not `backend/`):
```
cd ..                            # back to cs160-team5-ofs/
npm install
```
One install covers both apps and the shared package (npm workspaces).

The storefront also needs two **public** keys in `frontend/storefront/.env` (gitignored):
```
VITE_STRIPE_PUBLISHABLE_KEY=pk_test_...   # Stripe → Developers → API keys → publishable key
VITE_MAPBOX_TOKEN=pk....                  # same Mapbox public token as above
```
Restart the storefront after changing it; Vite only reads `.env` on start.

### 7. Run it

Use a separate terminal for each:

| Terminal | Command | Opens |
|---|---|---|
| Backend | `cd backend && source .venv/bin/activate && python run.py` | http://localhost:5000/api/health → `{"status":"ok"}` |
| Storefront | `npm run dev:storefront` (repo root) | http://localhost:5173 |
| Staff dashboard | `npm run dev:staff` (repo root) | http://localhost:5174 |
| Stripe (optional) | see below | |

Both frontend apps forward `/api/*` to the backend on `localhost:5000` (see each
`vite.config.ts`), so there are no CORS issues locally.

**Stripe webhooks (optional).** The checkout page also polls Stripe, so orders get placed without
this. Run it to test webhook delivery, failed payments and cancellations:
```
stripe login
stripe listen --print-secret   # put this whsec_... in STRIPE_WEBHOOK_SECRET (it's per machine)
stripe listen --events payment_intent.succeeded,payment_intent.payment_failed,payment_intent.canceled \
  --forward-to localhost:5000/api/payments/webhook
```

### 8. Log in

| Role | Email | Password | Use it in |
|---|---|---|---|
| Customer | `customer@example.com` | `customer123` | Storefront |
| Employee | `employee@example.com` | `employee123` | Staff dashboard |
| Manager | `manager@example.com` | `manager123` | Staff dashboard (includes Reports) |

Test card: `4242 4242 4242 4242`, any future expiry, any CVC. Test addresses must be inside the
Downtown San Jose delivery zone (e.g. `150 S 1st St, San Jose`).

### 9. Run the checks

```
cd backend && pytest             # backend tests (in-memory database; never touches yours)
npm run typecheck                # repo root: type-check all frontend workspaces
npm run lint
npm run build
```

### Keeping up to date

After `git pull`:
```
cd backend && source .venv/bin/activate
pip install -r requirements.txt  # if requirements.txt changed
cd .. && npm install             # if package-lock.json changed
```
If the pull added a migration (a new file in `backend/migrations/versions/`):
- **Local database:** `cd backend && flask --app app:create_app db upgrade`, or delete
  `backend/instance/demo.db` and re-seed.
- **Shared Supabase database:** the project owner runs `db upgrade` once after the merge; nobody
  else does.

### Troubleshooting

- *My changes don't show up in Supabase.* A `DATABASE_URL` set in your terminal (e.g. from
  `export DATABASE_URL=...`) overrides `backend/.env`. Run `unset DATABASE_URL` or open a new
  terminal, then restart the backend.
- *"table ... already exists" or "was created before migrations existed" when seeding.* The
  database file is from before migrations. Delete `backend/instance/demo.db` and seed again.
- *Port 5000 is taken (macOS).* macOS uses it for AirPlay Receiver (System Settings → General →
  AirDrop & Handoff → AirPlay Receiver). Either turn that off, or run on another port: start the
  backend with `PORT=5001 python run.py`, and each frontend with
  `API_URL=http://localhost:5001 npm run dev:staff` (or `dev:storefront`). If you use Stripe,
  change the `--forward-to` port too.
- *Vite fails with "Cannot find native binding" / `@tailwindcss/oxide-darwin-arm64` (macOS).* The
  lockfile only lists the Linux binaries (an npm optional-dependency bug). Run
  `npm install --no-save @tailwindcss/oxide-darwin-arm64@4.3.3 -w staff-dashboard -w storefront`
  (use `oxide-darwin-x64` on Intel Macs). `--no-save` keeps `package-lock.json` unchanged.

## Docker Setup

Not set up yet. This section will cover running the whole app (backend, both frontends, and a
database) with `docker compose up`.

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
