# Backend: Flask API served by gunicorn. Build context is the repo root (see docker-compose.yml).
FROM python:3.14-slim

ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
WORKDIR /app

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ .
RUN useradd --create-home --uid 10001 app && chown -R app /app
USER app

EXPOSE 5000
# AUTO_SEED=1 runs the migrations and loads the demo data before the API starts (see seed_demo.py).
# It is off by default, and it refuses any database that is not the bundled one.
# One worker + threads: the app keeps up to 5 database connections per process, and the shared
# Supabase free tier has few. Notification emails run on background threads inside the worker.
CMD ["sh", "-c", "if [ \"$AUTO_SEED\" = \"1\" ]; then python seed_demo.py --auto || exit 1; fi; exec gunicorn --bind 0.0.0.0:5000 --workers 1 --threads 4 --access-logfile - --error-logfile - run:app"]
