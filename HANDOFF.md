# Team 5 — CS160 Project Handoff

**Track:** OFS On-Demand Food Delivery (San Jose Downtown)
**Repo:** github.com/andrianthan/cs160-team5-ofs
**PM:** Andrianthan
**Date:** 2026-09-14 (Kickoff planning complete)

---

## Plan locked

- Stack: Flask + SQLite + HTML/Jinja + Mapbox + draw.io
- Sync: weekly Mon
- Pairing: skip (use 2hr stuck rule instead)
- Status tracking: 1 shared Google Doc (no Trello)

## Part I split (due 9/17/26)

| Person | Deliverable |
|---|---|
| P1 | Problem statement + 3 personas |
| P2 | 5 user stories + 1 flow diagram (draw.io) |
| P3 | Component architecture diagram (draw.io) |
| P4 | Component feature list + descriptions |
| P5 | Tools list + setup README |
| PM | Editor + integration + submit |

## Week 1 schedule

- **Tue 9/9:** Kickoff meeting, assign roles
- **Wed 9/10 - Fri 9/12:** Each owner drafts
- **Sat-Sun 9/13-14:** PM整合 all 5 docs into 1 PDF
- **Mon-Tue 9/15-16:** Polish, fix thin sections
- **Wed 9/17:** Submit

## Risks tracked

1. P3 (diagram) freezes → send draw.io tutorial link
2. Mapbox API key missing → P5 requests by Thu
3. Scope creep → frozen list of V2 features, ignore until Part III

## Artifacts (created in planning)

- `kickoff-agenda.md` — Tue 9/9 agenda
- `status-table-template.md` — weekly status Doc template
- `tech-stack.md` — locked stack + P5 setup checklist
- `component-diagram-starter.md` — boxes/arrows for P3

## Component architecture (planned)

**Frontend:** Customer Page, Manager Dashboard, Employee Dashboard
**Backend:** Flask APIs (`/api/items`, `/api/cart`, `/api/orders`, `/api/delivery`, `/api/manager`)
**DB tables:** items, users, orders, order_items, robots
**External:** Mapbox API

## Open questions deferred

- Auth (login) — Part III+
- Payment processing — Part III+
- Real robot hardware — mocked in code

---

## Next session TODO

1. Confirm kickoff happened + roles assigned
2. Check each person's draft progress (Fri 9/12)
3.整合 drafts weekend of 9/13-14
4. Submit Wed 9/17
5. Plan Part II (LLD + Test Plan) starting 9/17 evening

## Context notes for future-me

- PM = assigning role, not coding primary
- Team = 5 novices, drop not a risk, sync weekly
- Respect spec literally: 10 orders / 200 lb robot capacity
- All planning artifacts saved in `~/Desktop/projects/CS160/project1/`