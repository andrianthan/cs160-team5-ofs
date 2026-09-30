# OFS UI Prototype

Click-through UI prototype for the OFS On-Demand Food Delivery system (Team 5, CS160).
No backend — runs entirely in the browser, fake data, state saved to your browser's
local storage. Not synced with anyone else who opens these files.

## How to use

Unzip, then just double-click to open in a browser:

- `storefront.html` — Customer-facing app
- `staff-dashboard.html` — Employee/Manager dashboard

## Logins (any password works, type is checked but content isn't — use these exact ones)

| App | Email | Password | Role |
|---|---|---|---|
| Storefront | customer@ofs.test | demo | Customer |
| Staff Dashboard | employee@ofs.test | demo | Employee |
| Staff Dashboard | manager@ofs.test | demo | Manager (sees Reports + Delivery Pause) |

## Try the full order flow

1. Open `storefront.html`, log in, browse, add items to cart, checkout
   - Address must contain "Downtown San Jose" to pass validation
   - Card `4242 4242 4242 4242` succeeds; `4000 0000 0000 0002` simulates a decline
   - Add ~7x Spring Water (30 lb each) to see the 200 lb overweight block
2. Open `staff-dashboard.html` in **another tab of the same browser** and log in as Employee
   - Your order appears in the Prep Queue → "Mark Prepared" groups it into a Trip
   - Go to Dispatch → "Assign next available Robot" → "Confirm load & Dispatch"
   - Mark the order "Delivered" or "Failed" to complete the lifecycle
3. Flip back to the Storefront's Track tab — status updates live (same browser, same
   machine — this relies on browser localStorage, which isn't shared across different
   computers or browsers)

## Notes

- This is a prototype for exploring layout/flow, not the real system.
- Real implementation is the Flask + PostgreSQL backend described in
  `docs/part1/` (HLD) and `docs/part2/` (LLD) — see the backlog (T01-T20)
  for what actually gets built.
