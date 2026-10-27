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

## Getting Started

**Frontend** (install once from the repository root):
```
npm install
npm run dev:storefront # http://localhost:5173
npm run dev:staff      # http://localhost:5174, run in another terminal
```

Use `npm run build`, `npm run typecheck`, and `npm run lint` at the root to
check all frontend workspaces.

**Backend:**
NOTE: Python Version: 3.14.7
```
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in DATABASE_URL, STRIPE_*, MAPBOX_*, SMTP_* as you need them
python run.py           # http://localhost:5000, GET /api/health to check it's up
pytest                  # run the test suite
```

**DB (Supabase):** one shared Supabase project for the whole team — don't each spin up your own.
Whoever has it (currently: T02 owner) posts the connection string in the team chat, not committed
anywhere. Project Settings → Database → Connection string → URI, then:
```
DATABASE_URL=postgresql://postgres:[YOUR-PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres
```
goes in your own local `.env` (never `.env.example`, never committed — it's gitignored already).

Both frontend apps proxy `/api/*` to `localhost:5000` in dev (see each `vite.config.js`) —
no CORS headaches locally.

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
