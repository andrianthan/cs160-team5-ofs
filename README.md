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
address needs IPv6, which many networks lack). `?sslmode=require` encrypts the connection.

Step by step in the Supabase dashboard (the labels may move slightly between versions):
1. Open the project and click **Connect** at the top of the page.
2. Choose the **Direct** tab, then **Connection String**. (The tab is called Direct, but you pick
   the connection type in the next step.)
3. Set **Method** to **Session pooler** (not "Direct connection" and not "Transaction pooler").
4. Copy the string. It looks like
   `postgresql://postgres.[PROJECT-REF]:[YOUR-PASSWORD]@aws-0-[REGION].pooler.supabase.com:5432/postgres`.
   Check that the user is `postgres.[PROJECT-REF]` (with the project reference), the host ends in
   `pooler.supabase.com` and the port is `5432`.
5. Replace `[YOUR-PASSWORD]` with the database password, **without the square brackets**, and add
   `?sslmode=require` to the end.
6. Paste it into `backend/.env` as `DATABASE_URL=...`. The name must be spelled exactly
   `DATABASE_URL`. A typo such as `DATABASE_UR` is ignored without any warning, and the app then
   quietly falls back to `localhost:5432`.
The tables and demo data already exist there: **don't run the seed** against the shared database.

Every table has row-level security on (migration `0003_enable_rls`), so Supabase's public API key
can't read or change anything; the backend connects as the tables' owner and isn't affected.
Project owner: give the database a letters-and-digits password (`@ # / %` break the URL), and run
`flask --app app:create_app db upgrade` once after any PR with a new migration merges.

**B. A private local database (works offline, your own data).** Set
```
DATABASE_URL=sqlite:///demo.db
```
then create the tables and demo data (the file lands in `backend/instance/demo.db`):
```
python seed_demo.py              # reads backend/.env and prints which database it's seeding
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

- *My changes don't show up in Supabase.* Check the ` * Database: ...` line `python run.py` prints on
  start (password hidden). A `DATABASE_URL` set in your terminal (e.g. from
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

Runs the whole site in containers: the Flask API on gunicorn, and both React apps behind Apache
(static files, browser-route fallback, `/api/*` proxied to the API). It is optional; day-to-day
development still uses `npm run dev` (section 7). You need Docker with Compose v2.

| Service | URL |
|---|---|
| Storefront | http://localhost:8080 |
| Staff dashboard | http://localhost:8081 |

**Against the shared Supabase database** (needs `backend/.env` from section 4):
```
cp .env.example .env     # then fill in the two VITE_* values (the same as frontend/storefront/.env)
docker compose up --build
```
Don't run the seed against the shared database. New migrations are still applied by the project
owner (see "Keeping up to date").

**Against a private throwaway database** (a PostgreSQL 16 container; safe for seeding and testing):
```
docker compose -f docker-compose.yml -f docker-compose.localdb.yml up -d --build
docker compose -f docker-compose.yml -f docker-compose.localdb.yml run --rm backend flask --app app:create_app db upgrade
docker compose -f docker-compose.yml -f docker-compose.localdb.yml run --rm backend python seed_demo.py
```
The seed prints the demo logins. `docker compose ... down -v` also deletes the database volume.

Good to know:
- The `VITE_*` values are baked into the storefront at **build** time. Change them, then run
  `docker compose build storefront`.
- `DATABASE_URL` is set by the override file for the local database; otherwise it comes from
  `backend/.env`.
- **Stripe webhooks** (orders are only created when Stripe's webhook arrives). Either run the
  Stripe CLI on your machine (`stripe listen --forward-to localhost:8080/api/payments/webhook`), or
  let Docker do it with the optional `stripe` service, which uses `STRIPE_SECRET_KEY` from
  `backend/.env`:
  ```
  docker compose --profile stripe up -d
  docker compose logs stripe          # prints "Your webhook signing secret is whsec_..."
  ```
  Put that `whsec_...` value in `backend/.env` as `STRIPE_WEBHOOK_SECRET` (once; it stays the same
  across restarts), then `docker compose up -d --force-recreate backend`. The service is not started
  by a plain `docker compose up`. Stop it with `docker compose --profile stripe stop stripe`.
  (`stripe trigger` fails with the newest Stripe API version; test with the checkout page and card
  `4242 4242 4242 4242` instead.)
- The API runs one gunicorn worker with 4 threads, so it holds at most 5 database connections
  (the Supabase free tier is shared by the whole team).

Troubleshooting (Docker):
- **"Could not load products. Check that the backend is running." in the browser, but
  `docker compose ps` says the backend is healthy.** The API is up and the database isn't
  reachable. Run `docker compose logs --tail 40 backend` and read the last error:
  - `Network is unreachable` and a host like `db.[PROJECT-REF].supabase.co`: that is the Direct
    connection address, which is IPv6-only, and Docker has no IPv6. Use the **Session pooler**
    string (section 5).
  - `Tenant or user not found`: the region in the host or the `postgres.[PROJECT-REF]` user is
    wrong. Copy the string again from the dashboard.
  - `password authentication failed`: wrong password, or the brackets or a space ended up in it.
- **After changing `backend/.env`, run
  `docker compose up -d --force-recreate backend`.** The file is read when the container starts,
  so there is no need to rebuild.
- `docker compose config` prints what Compose will actually use, **including secrets**. Don't paste
  its output anywhere.

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
