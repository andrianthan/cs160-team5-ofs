# OFS On-Demand Food Delivery (CS160 Team 5)

Web app for organic food delivery in Downtown San Jose.
Self-driving Robots carry up to 10 Orders / 200 lb per Trip.

## Stack

- **Frontend:** React + Vite + React Router + Tailwind CSS
- **Backend:** Flask REST API (Python) + SQLAlchemy, served by gunicorn
- **DB:** PostgreSQL
- **Maps & routing:** Mapbox GL JS, Geocoding API, Optimization API (`driving-traffic`)
- **Payments:** Stripe (test mode)

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
/backend/                   → Flask API (app factory + blueprints, one per component group)
/backend/app/models/        → SQLAlchemy models, see LLD for the schema
/backend/tests/             → pytest
/ui-prototype/               → Standalone click-through HTML/JS mockup, no backend — see its own README
```

Every backend route is a stub (`501 not_implemented`) tagged with its owning backlog
task — e.g. `app/blueprints/cart.py` says `T08, Than Andrian`. Check
[Trello](https://trello.com/b/aw6ohAFJ) for the task card and pseudo code.

## Getting Started

**Frontend** (run each app in its own terminal):
```
cd frontend/storefront && npm install && npm run dev      # http://localhost:5173
cd frontend/staff-dashboard && npm install && npm run dev # http://localhost:5174
```

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

Both frontend apps proxy `/api/*` to `localhost:5000` in dev (see each `vite.config.js`) —
no CORS headaches locally.
