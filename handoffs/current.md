# Expedia Lite current handoff

Verified from repository evidence on 2026-09-17. Recheck Git state and the
named files before continuing.

## Objective and decisions

The backend-only SQLite persistence and booking CRUD milestone is complete and
committed on the `sqlite-crud` feature branch. Frontend implementation is the
next milestone.
The implemented contract is
[`docs/backend-persistence-contract.md`](../docs/backend-persistence-contract.md).

Final backend decisions:

- The supplied hotel, trip, user, and booking CSV files are immutable initial
  data imported into a new SQLite database exactly once.
- The default runtime database is
  `backend/instance/expedia_lite.sqlite3`; runtime SQLite files are ignored.
- FastAPI initializes the database before requests. After initialization, all
  application reads and writes use SQLite; only the seeder accesses CSV files.
- Hotels, trips, and users are read-only reference data. Bookings support
  create, retrieve, joined history, status update, and deletion.
- Existing IDs are preserved. New booking IDs begin at B007, advance
  monotonically, survive restart, and are not reused after deletion.
- Cancellation preserves history while deletion removes the booking.
- Multiple bookings for the same user/trip are allowed because inventory and
  duplicate-booking restrictions are outside the documented scope.
- Frontend booking and history work remains a separate next milestone.

## What works

- `backend/app/database.py` provides the constrained version 1 schema,
  request-safe connections, foreign keys, case-folding, initialization, and
  durable booking-ID allocation.
- `backend/app/seed.py` validates and transactionally imports all four CSV
  files. It prevents re-import, unsafe partial merges, and unsupported
  schema/seed versions.
- `backend/app/search.py` performs SQLite-backed, trimmed, case-insensitive
  partial hotel-name search with deterministic ordering and derived prices.
- `backend/app/bookings.py` provides framework-free user lookup, joined booking
  detail/history, and transactional create, update, and delete behavior.
- `backend/app/main.py` provides a configurable application factory, lifespan
  initialization, request-scoped connections, HTTP error translation, and all
  documented routes.
- Implemented API routes:
  - `GET /api/hotels/search`
  - `GET /api/users`
  - `GET /api/users/{user_id}/bookings`
  - `POST /api/bookings`
  - `GET /api/bookings/{booking_id}`
  - `PATCH /api/bookings/{booking_id}`
  - `DELETE /api/bookings/{booking_id}`
- Booking responses join traveler, trip, hotel, dates, status, nights, nightly
  rate, and stay price for future confirmation and history views.
- Empty history and no-result search return valid empty `200` responses.
  Unknown related records return `404`; invalid bodies/statuses return `422`;
  blank search returns `400`.
- README, design, verification, and persistence documentation match the
  completed backend and explain database lifetime across restarts.

## Git state

- Root: `/Users/jlee/Desktop/psu4/ist402/a1_expedia_lite`
- Branch: `sqlite-crud`
- Backend feature checkpoint: `2c6fad6`
  (`feat: add SQLite booking persistence API`). The branch tip also contains
  this handoff-only frontend planning checkpoint.
- `main` and `origin/main` remain at the preserved Part 1 commit
  `a67b2e1fe9c699ad0dddfd0441ac429520b4616f`.
- The backend milestone is committed in 17 files at `2c6fad6`.
- `report.md` had an existing user change before this milestone and was not
  edited by the agent.
- This handoff was updated after the backend checkpoint to record the frontend
  implementation plan and is not part of the backend feature commit.

## Automated verification

```bash
backend/.venv/bin/python -m compileall -q backend/app backend/tests
backend/.venv/bin/python -m pytest backend/tests
```

Result: 40 tests passed in the final run. Coverage includes exact seed data,
one-time initialization, rollback and version failures, persistence, foreign
keys, reference searches, user listing, seeded/empty history, booking CRUD,
request errors, status semantics, ID behavior, and application restarts. Two
existing deprecation warnings come from FastAPI/Starlette test-client
dependencies.

```bash
cd frontend
npm run lint
npm run build
```

Result: lint passed and Vite 8.3.0 built 13 modules successfully. This was a
compatibility regression only; no frontend booking/history code was added.

## Live backend verification

Two real Uvicorn processes were run sequentially against the same isolated
temporary SQLite file. Live HTTP observations included:

- OpenAPI `200` with every documented route and method.
- `Harbor` `200` with T001/T009 and `nonexistent` `200` with no results.
- U001 history `200` with B002/B001 and initial U006 history `200` empty.
- Create U006/T001 `201` as B007; cancel B007 `200`; history retained cancelled
  B007.
- Create U006/T009 `201` as B008; delete B008 `204`; retrieve B008 `404`.
- Unknown user `404`, unsupported status `422`, and blank search `400`.

After the first Uvicorn process shut down, the second process used the same
database:

- B007 remained cancelled.
- B008 remained deleted.
- U006 history contained only B007.
- Search continued to return the correct SQLite results.
- The next booking was B009, proving the counter persisted and B008 was not
  reused.

After final shutdown, direct inspection of the closed database showed 8
hotels, 12 trips, 6 users, and 8 bookings; schema/seed version 1; counter 9;
and U006 bookings B007 cancelled plus B009 confirmed.

The first sandboxed bind attempt failed with `Errno 1`, and sandboxed HTTP
clients could not reach the approved listener. The same commands were rerun in
the approved host context, where all application checks passed. This was an
execution-environment boundary, not an application correction.

## Cleanup and current services

- Both temporary Uvicorn processes shut down cleanly.
- No process is listening on ports 8000 or 5173.
- The temporary audit directory and database were removed.
- The project default runtime database does not exist and was not modified.
- Seed CSV files were not modified.

## Requirement audit

- Four supplied datasets seeded into SQLite: verified by automated and direct
  count checks.
- Seed data is initial rather than a fixed limit: verified by B007, B008, and
  B009 creation.
- SQLite-only reads/writes after seeding: verified by source audit, restart
  tests without seed files, and live persistence.
- FastAPI boundary for frontend actions: verified through OpenAPI and live
  HTTP requests.
- Create/retrieve/update/delete booking behavior: verified over live HTTP.
- Existing IDs preserved and new IDs unique: verified through seeded records,
  counter state, deletion, restart, and B009 allocation.
- Booking becomes available in history and remains across restart: verified for
  U006/B007.
- Meaningful empty and failure states: verified for empty history, no search
  results, blank search, invalid status, and missing records.
- Storage choice and lifetime documented: verified in README, design,
  persistence contract, and verification guide.

## Remaining limitations

- The Vue frontend still exposes only a minimally styled hotel search. Booking,
  confirmation, history, cancellation, deletion, and the reference-inspired
  visual treatment remain required.
- The reference Expedia screenshots include photographs, ratings, amenities,
  savings, and flight/package claims that do not exist in this project's data.
  The frontend should reproduce their layout, hierarchy, palette, rounded card
  treatment, controls, and price emphasis without fabricating those values or
  copying copyrighted Expedia assets.
- No local hotel imagery currently exists. Before final visual polish, use
  original/generated local synthetic hotel imagery or another clearly
  attributable source; do not crop images from the Expedia reference.
- The assignment's final manual browser demonstration, screenshots/screencast,
  evidence-log completion, final Git review/merge, and push remain future work.
- Python transitive dependencies are not fully pinned. The current suite has
  two upstream deprecation warnings.
- `report.md` contains an existing user edit and needs user-led reconciliation
  during final assignment documentation work.

## Recommended next task

Implement the frontend in narrow, verified increments:

1. Define shared request/error helpers plus typed-by-convention API modules for
   users, booking creation, history, status updates, and deletion. Add focused
   dependency-free checks for request shapes and error handling.
2. Establish the mobile-first Expedia-inspired shell and convert the existing
   search table into reusable stay cards. Preserve and verify blank, loading,
   results, no-results, and backend-error states before adding booking actions.
3. Add explicit demo-traveler selection, a book action on each stay, and a
   confirmation view using the backend response as the source of truth.
4. Add a history view for the selected traveler, including loading, populated,
   empty, and failure states. Refresh it from SQLite after booking and whenever
   the user enters the history view.
5. Add cancellation and two-step deletion, update the displayed records only
   after successful API responses, and verify failed mutations remain honest.
6. Complete responsive/accessibility polish, then run lint, build, backend
   tests, and a browser walkthrough of both required flows plus blank search,
   no results, empty history, cancellation, deletion, refresh, and restart
   persistence. Update documentation, screenshots, evidence, and this handoff.

Critical dependencies are sequential: the API client layer precedes booking
UI; traveler selection precedes both creation and history; booking creation
precedes confirmation; history rendering precedes cancellation/deletion; and
all behavior must pass before final visual/evidence work. Avoid Vue Router, a
state library, or a CSS framework unless an observed requirement makes one
necessary; local component state and plain CSS are sufficient for this scope.

The first implementation task is step 1 only. Do not combine it with visual or
booking UI changes. Verify its request/response behavior before starting the
search-card redesign.

Before changing frontend files, re-read `AGENTS.md`, `README.md`,
`docs/design-pipeline.md`, `docs/verification.md`, the assignment description,
and this handoff. Preserve the existing `report.md` change unless the user
explicitly includes it in the next task.
