#!/bin/bash
# Start the Stripe CLI webhook listener for the local demo, and put its signing secret
# into backend/.env so the backend can verify the webhooks it forwards.
#
#   ./start_stripe_listener.sh          # start it and sync .env
#   ./start_stripe_listener.sh --stop   # stop it
#
# Two things make this worth a script:
#
#   1. `stripe listen` prints a NEW signing secret every time it starts, and the one in
#      .env only ever matches the run that produced it. Start the listener and the
#      backend then rejects every payment with "invalid_signature". This always syncs
#      the two.
#   2. The Stripe CLI's own OAuth token expires (about every 24h here). When it does,
#      the listener dies with "expired OAuth token" and every payment stops arriving --
#      silently, until someone tries to pay. `stripe whoami` below refreshes it.
#
# If this script says the CLI is not authenticated, run `stripe login` once, then run it again.
set -euo pipefail

cd "$(dirname "$0")"
PORT="${PORT:-5001}"
LOG="stripe-listen.log"
ENV_FILE=".env"

stop_listener() {
  if pgrep -f "stripe listen" > /dev/null 2>&1; then
    pkill -f "stripe listen" > /dev/null 2>&1 || true
    echo "Stopped the previous listener."
  fi
}

if [ "${1:-}" = "--stop" ]; then
  stop_listener
  exit 0
fi

if ! stripe whoami > /dev/null 2>&1; then
  echo "The Stripe CLI is not authenticated. Run 'stripe login' first, then run this again." >&2
  exit 1
fi

stop_listener
rm -f "$LOG"
stripe listen \
  --events payment_intent.succeeded,payment_intent.payment_failed,payment_intent.canceled \
  --forward-to "localhost:$PORT/api/payments/webhook" > "$LOG" 2>&1 &

SECRET=""
for _ in $(seq 1 30); do
  sleep 1
  SECRET=$(grep -o 'whsec_[A-Za-z0-9]*' "$LOG" | head -1 || true)
  [ -n "$SECRET" ] && break
done

if [ -z "$SECRET" ]; then
  echo "The listener did not report a signing secret. Tail of $LOG:" >&2
  tail -20 "$LOG" >&2
  exit 1
fi

if grep -q '^STRIPE_WEBHOOK_SECRET=' "$ENV_FILE"; then
  sed -i '' "s|^STRIPE_WEBHOOK_SECRET=.*|STRIPE_WEBHOOK_SECRET=$SECRET|" "$ENV_FILE"
else
  printf '\nSTRIPE_WEBHOOK_SECRET=%s\n' "$SECRET" >> "$ENV_FILE"
fi

sleep 1
if ! grep -q 'Your webhook signing secret is' "$LOG"; then
  echo "The listener did not come up cleanly. Tail of $LOG:" >&2
  tail -20 "$LOG" >&2
  exit 1
fi

echo "STRIPE_WEBHOOK_SECRET=$SECRET written to $ENV_FILE"
echo "Listening on -> localhost:$PORT/api/payments/webhook   (log: $LOG)"
echo
echo "Now restart the backend so it picks up the new secret:"
echo "  cd backend && PORT=$PORT .venv/bin/python run.py"
