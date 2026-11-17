# Basil — Demo Run-of-Show

**Part III · 12-minute presentation + live demo · 11/23/2026**

Companion documents:
- `docs/part3-presentation.html` — the slides (open in a browser; `→`/`←` to navigate, `N` for speaker notes, `O` for the overview)
- `docs/demo-cheatsheet.html` — copy-paste reference for values, addresses, cards and commands
- `docs/part3-status.md` — the live status doc
- `docs/backlog-history.md` — who built what

---

## 0. The one-paragraph version

The presentation is 12 minutes: ~6 minutes of slides and ~6 minutes of live demo.
The live demo has four beats — **cart → pay → dispatch → watch** — and they are
**sequenced**, not independent. You place the order first, then pay for it, then dispatch
it as staff, then watch it as the customer. Every beat feeds the next, so if one breaks
you fall back to the next, not to the start.

---

## 1. Pre-flight (do this 30 minutes before)

### 1.1 Reset the demo data

> **Why:** the demo SQLite database can go stale relative to the Alembic migrations. On
> 11/16 it was missing 8 tables (`delivery_settings`, `robots`, `trip_stops`, `inventory_log`,
> `addresses`, `order_override_audits`, `app_settings`, `alembic_version`), and the result was
> `/api/settings/delivery-pause` returning **500 on every checkout page**.

```bash
cd backend
rm -f demo.db
export DATABASE_URL="sqlite:///$PWD/demo.db" PORT=5001
.venv/bin/python seed_demo.py --with-orders
```

One tracked command does it all: it builds the schema through the Alembic migrations, then
seeds the demo users, the catalog, the fleet, the saved cart **and** a week of Orders together
with the Trips that delivered them. Those Trips carry the ETAs, so the Reports page has on-time
rate (60%), delivery duration (14 min) and trip utilization to show — slide 8 has numbers even
if the live dispatch is slow. Without `--with-orders` all three metrics are null.

### 1.2 Start the Stripe webhook listener **first**, then copy its secret

> **Why:** `stripe listen` prints a **new signing secret every time it starts**. The secret in
> `backend/.env` belongs to whichever run produced it. If they disagree, every payment is
> rejected with `invalid_signature` and the Order is never created.

```bash
cd backend
stripe listen --events payment_intent.succeeded,payment_intent.payment_failed,payment_intent.canceled \
  --forward-to localhost:5001/api/payments/webhook
```

It prints:

```
Ready! ... Your webhook signing secret is whsec_XXXXXXXXXXXXXXXXXXXXXXXX
```

Copy that `whsec_...` into `backend/.env` as `STRIPE_WEBHOOK_SECRET`, **then** start the
backend. If you restart the listener later, you must copy the new secret and restart the
backend again.

### 1.3 Start the three services

```bash
# backend — from backend/, no reloader (see 1.4)
cd backend
export DATABASE_URL="sqlite:///$PWD/demo.db" PORT=5001 FLASK_RELOAD=0
.venv/bin/python run.py

# storefront + staff dashboard, from the repo root
API_URL=http://localhost:5001 npm run dev:storefront   # :5173
API_URL=http://localhost:5001 npm run dev:staff         # :5174
```

> **Port 5000 is macOS AirPlay Receiver.** It answers on 5000 and returns `403` for
> everything, which looks exactly like a broken backend. Always use **5001**. The
> `API_URL=http://localhost:5001` above points both frontends at it.

### 1.4 `FLASK_RELOAD=0` is not optional on demo day

> **Why:** the Flask reloader restarts on any file change. Its restart can lose the port to
> the process it is replacing, the new worker then fails with "Address already in use", and
> **the whole server dies** — which happened on 11/16 and took the backend down mid-run.
> With the reloader off, an edit cannot take the server down.

### 1.5 Smoke test (2 minutes)

| Check | Expected |
|---|---|
| `curl -s localhost:5001/api/health` | `{"status": "ok"}` |
| `curl -s localhost:5001/api/settings/delivery-pause` | `{"paused": false}` — **not** a 500 |
| Storefront `:5173` loads, product tiles visible | yes |
| Staff `:5174` loads, Dispatch page has trips | yes |
| `stripe listen` window shows a `whsec_` and stays running | yes |

### 1.6 SMTP (only if you want the emails in the demo)

The customer "order confirmed" email needs a real provider. Gmail with an app password
takes five minutes:

1. Turn on 2-Step Verification on the sending Google account.
2. `myaccount.google.com/apppasswords` → create a password (16 characters, no spaces).
3. `backend/.env`:

   ```
   SMTP_HOST=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USERNAME=youraddress@gmail.com
   SMTP_PASSWORD=abcdefghijklmnop
   SMTP_FROM=Basil <youraddress@gmail.com>
   SMTP_STARTTLS=1
   ```

4. Restart the backend.

Verify **before** the demo, not during it:

```bash
cd backend
.venv/bin/python smtp_check.py you@gmail.com          # connect + login, sends nothing
.venv/bin/python smtp_check.py you@gmail.com --subject "Basil" --body "hello"
```

> **If the login fails you will see `SMTPAuthenticationError 535: Username and Password not
> accepted`.** That is the server's real answer — we fixed a bug where Python's SMTP client
> masked it as `Connection unexpectedly closed`. A `535` means the password is wrong or is
> not an app password. A `Connection unexpectedly closed` means the connection itself died.

---

## 2. The demo, beat by beat

Set up **two browser windows side by side** before you start:

- **Window A** — Storefront, `localhost:5173`, logged in as `customer@example.com`
- **Window B** — Staff Dashboard, `localhost:5174`, logged in as `employee@example.com`

Log in during the pre-flight, not live. Both are seeded:

| Role | Email | Password |
|---|---|---|
| Customer | `customer@example.com` | `customer123` |
| Employee | `employee@example.com` | `employee123` |
| Manager | `manager@example.com` | `manager123` |

### Beat 1 — Cart and the pricing rules · 60 s

1. Window A → **Browse**. Point out the weight on each tile (`0.3 lb`, `3 lb`, `5 lb`).
2. Click **Add** on Russet Potatoes (5 lb bag) **three times**. The seeded cart is 5.2 lb
   (apples 3.0 + spinach 0.6 + eggs 1.6); three bags take it to **20.2 lb**, which crosses the
   20 lb threshold. Two bags only reaches 15.2 lb and the fee will **not** appear.
3. Open the cart. Say: *"Weight and fee are computed on the server — watch."*
4. Cross 20 lb and the **$10 delivery fee** appears. **The number changing on its own is the
   whole point of this beat.**
5. Close the cart preview. Move on.

> If the fee does not appear, your cart is under 20 lb — add potatoes. Do not add enough to
> exceed **200 lb** on stage: that sends the Order to Manual Review and the demo stalls.

### Beat 2 — A real Stripe test payment · 90 s

1. Window A → **Cart** → **Checkout**.
2. Click the delivery address field and type **`200 E Santa Clara St, San Jose, CA`**.
   Pick the first Mapbox suggestion.
3. The page resolves to *"Deliver to: 200 East Santa Clara Street, San Jose, California 95113"*.
   Say: *"Mapbox geocoded it, and we checked the point against our delivery-zone polygon."*
4. **Click the `Card` accordion to expand it.** Then type into the card field:
   - number `4242424242424242`
   - expiry `12/34`
   - CVC `123`
   - ZIP `95113`
5. Click **Pay**. Wait for *"Payment received. Confirming your order."*

> **The Card accordion is collapsed by default and the card field is hidden until you
> expand it.** If your keystrokes vanish, you typed into a hidden field. Click **Card** first.
>
> **Click Pay once.** A second click is declined as a duplicate idempotency key.
>
> If the payment stalls, do not click again — move to Beat 3 and come back. The Order will
> appear on the staff side regardless, because the storefront polls as a fallback.

### Beat 3 — Staff prepare and dispatch · 90 s

1. Window B → **Prep Queue**. Find the new Order (highest number, top of the list).
2. Click **Prepare**. Say: *"Staff mark it prepared and the system assigns it to a Trip —
   grouped by proximity, capped at ten Orders or two hundred pounds."*
3. Go to the **Dispatch** page. Say: *"Three Robots in the depot. Here is the route Mapbox
   optimised, and the ETA for each stop."*
4. Click **Dispatch** on the Trip. Say: *"A Robot is assigned and it starts driving."*
5. The Order flips to **Out for delivery** and the customer is emailed.

> If the Dispatch button is greyed out, the Trip has not hit its 30-minute lock yet. That is
> the rule working — say so, do not hunt for the button. The Order from Beat 2 is minutes
> old, so it should be dispatchable immediately.

### Beat 4 — The customer watches the Robot · 60 s

1. **Before** you dispatch, open a third tab in Window A: **`localhost:5173/track`**, pick the
   Order in the dropdown.
2. Now dispatch (Beat 3, step 4).
3. The page refreshes every 10 seconds. Say: *"This is the customer view of the same Trip."*
4. The stage bar advances: **placed → preparing → out for delivery → delivered**.
5. The Robot marker moves on the map; the email arrives.

> **Open the Track tab before you dispatch.** If you open it after the Robot has arrived,
> there is nothing to watch — the map will just say "Delivered".
>
> The Robot drives in a **straight line** between stops rather than along the road network.
> That is a simulation simplification. Say so if it comes up; it is in the backlog.

### Closing — 60 s

Back to the slides. Slide 8 (metrics), slide 9 (bugs the tests found), slide 10 (all 20 tasks —
drop it first if you are running long). Land on **slide 12** for Q&A and leave it up.

> The seeded Trips mean slide 8's on-time rate, delivery duration and trip utilization already
> have numbers, even if the live Robot was slow. Say what the live dispatch adds on top: it
> moves the customer map.

---

## 3. Timing

| Beat | Slides | Live | Running |
|---|---|---|---|
| Title, problem, architecture | 2:30 | — | 2:30 |
| Beat 1 — cart | — | 1:00 | 3:30 |
| Beat 2 — Stripe payment | — | 1:30 | 5:00 |
| Beat 3 — dispatch | — | 1:30 | 6:30 |
| Beat 4 — customer map | — | 1:00 | 7:30 |
| Reports, quality, status, next | 3:30 | — | 11:00 |
| Q&A | 1:00 | — | 12:00 |

If you are running long, **cut Beat 1 to 30 seconds** and skip the "all 20 tasks" slide.
Never cut the Stripe payment — it is the highest-value 90 seconds in the demo.

---

## 4. Failure playbook

| What breaks | Do this |
|---|---|
| Stripe says `invalid_signature` | The `whsec` in `.env` is not the one the listener printed. Copy the current one, restart the backend. |
| Stripe card field will not take input | Click the **Card** accordion first — it is collapsed by default. |
| Second Pay click declined | Expected. It is the duplicate idempotency key. Do not click again. |
| `/api/settings/delivery-pause` returns 500 | The demo DB is stale. Rerun 1.1 and restart the backend. |
| Backend is dead, `curl` returns nothing | The reloader killed it. Restart with `FLASK_RELOAD=0` (1.4). |
| Everything returns 403 | You are on port 5000 (macOS AirPlay). Move to 5001. |
| No Robot appears on the Dispatch page | The `robots` table is missing — rerun 1.1. |
| Map says "Robot location is not available yet" | The Order has not been dispatched yet. Dispatch it. |
| Map never updates | The page polls every 10 s; reload the Track tab to force an immediate fetch. |
| Reports page is empty | `seed_orders.py` did not run. Rerun 1.1. |
| Stripe CLI says "expired OAuth token" | `stripe login` — it re-authenticates the browser flow. Start the listener *after* logging in. |

---

## 5. Rehearsal plan

Three rehearsals, in this order. Each one is timed.

### Rehearsal 1 — mechanics only, ~45 min, solo

No slides. Just the four beats, end to end, with the stack up.

- Prove the **reset** works: `rm demo.db`, reseed, restart, and confirm
  `/api/settings/delivery-pause` is 200 and the Dispatch page has Robots.
- Prove the **Stripe secret** flow: start the listener, copy the secret, restart the backend,
  pay, and see the Order appear.
- Learn the two places you get stuck: the **Card accordion** and the **Track tab before dispatch**.

### Rehearsal 2 — full run, timed, ~45 min, whole team

- Run the whole 12 minutes with a stopwatch. Write down where you are at each minute mark.
- Every team member speaks at least once in the slides — Part VI is graded individually.
- Whoever presents the demo **narrates; whoever drives the mouse clicks.** Two brains, one
  story. If you present *and* drive, you will rush the words.
- Rehearse the ending: land on slide 12, and have someone play the grader for five minutes.

### Rehearsal 3 — dry run on the real machine, ~30 min, 11/22

- Same laptop, same projector, same browser, same window arrangement.
- Check the **display resolution**: the slides are sized for 1180×680. If the projector is
  16:10 or 4:3, the browser will letterbox them — that is fine, but check you can read the
  notes panel.
- Reset the data one final time and leave the stack running overnight.

### Rehearsal checklist

- [ ] Demo data reset; `/api/settings/delivery-pause` returns 200
- [ ] `stripe listen` running; its `whsec` is the one in `.env`; backend restarted after copying it
- [ ] Backend on **5001**, storefront on **5173**, staff on **5174**
- [ ] `FLASK_RELOAD=0` on the backend
- [ ] Both windows logged in (customer + employee); Track tab open on the right Order
- [ ] `smtp_check.py` passes, and you have read one real email end to end
- [ ] Card number, expiry, CVC and ZIP typed into the **expanded** Card field
- [ ] Cart crosses **20 lb** without crossing **200 lb**
- [ ] Whole run inside 12 minutes, with a stopwatch
- [ ] Slide 12 is what is on screen at the end
- [ ] Someone else has run the whole thing once without you

---

## 6. Who says what

Assign these now, not on the day.

| Slide / beat | Speaker |
|---|---|
| 1–3 (title, problem, architecture) | *assign* |
| Beat 1 — cart and pricing | *assign* |
| Beat 2 — Stripe payment | *assign* |
| Beat 3 — dispatch | *assign* |
| Beat 4 — customer map | *assign* |
| 8–10 (metrics, quality, status) | *assign* |
| 11–12 (next, Q&A lead) | *assign* |

Part VI (Scrum participation) is **graded individually** — every member should be audible
in the 12 minutes. If one person has to carry all twelve minutes, that person gets the
most credit and the other five get the least.

---

## 7. Known gaps — say them before they are asked

1. **No cancellation email.** `STATUS_EVENTS` has no cancel case, so a Manager cancel is
   silent even though backlog T17 asked for a refund message.
2. **Robots drive in straight lines**, not along the road network.
3. **The customer map polls every 10 seconds** instead of streaming — no websockets.
4. **The customer map is Leaflet + OpenStreetMap tiles**, not Mapbox GL JS, which is what
   our HLD originally specified. Mapbox does the geocoding, the address autofill and the
   route optimisation.
5. **Stripe is a PaymentIntent with the Elements form**, not a hosted Checkout page.
6. **No Apache deployment config** in the repo yet.
7. **T20's pause settings page** is on the staff dashboard, but the staff page itself is
   thin compared to the storefront.

Naming these is free credibility. Being caught by one is expensive.
