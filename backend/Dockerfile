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
# One worker + threads: the app keeps up to 5 database connections per process, and the shared
# Supabase free tier has few. Notification emails run on background threads inside the worker.
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "1", "--threads", "4", \
     "--access-logfile", "-", "--error-logfile", "-", "run:app"]
