# OFS On-Demand Food Delivery (CS160 Team 5)

Web app for organic food delivery in San Jose Downtown.
Self-driving robot dispatches up to 10 orders / 200 lb per trip.

## Stack

- **Backend:** Flask (Python)
- **DB:** PostgreSQL w/ Supabase
- **Frontend:** HTML + Jinja + TypeScript
- **Maps:** Mapbox GL JS (free tier)

## Setup

```bash
pip install flask
# Mapbox API key needed — get from https://account.mapbox.com/
export MAPBOX_KEY="pk.your_key_here"
python app.py
```

Open `http://localhost:5000`.

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
/                  → Flask app entrypoint (app.py)
/templates/        → Jinja HTML
/static/           → CSS, JS, images
/db/               → SQLite + schema.sql + seed.sql
```