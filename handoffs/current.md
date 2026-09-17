# Expedia Lite current handoff

Verified from repository evidence on 2026-09-17. Recheck Git state and the
named files before continuing.

## Objective and decisions

The backend-only SQLite persistence and booking CRUD milestone is complete and
committed on the `sqlite-crud` feature branch. Frontend steps 1 through 5 are
implemented and verified but not yet committed. The integrated browser has
verified search, traveler selection, booking creation and confirmation,
persistent history, cancellation, failed-mutation handling, the two-step
deletion guard, and permanent deletion of the non-seed B007 test record.
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
- The frontend booking lifecycle is complete through guarded deletion.

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
- `frontend/src/api/http.js` centralizes JSON success, empty `204`, backend
  detail-message, status-code, and fallback-error handling.
- `frontend/src/api/hotels.js`, `users.js`, and `bookings.js` cover search,
  traveler listing, history, booking creation/retrieval, status updates, and
  deletion without mixing request code into Vue components.
- `frontend/tests/api.test.js` provides dependency-free Node checks for the
  request contract. No frontend dependency was added.
- `frontend/src/components/StayCard.vue` renders the documented repeated-card
  structure using real hotel/trip values, derived price emphasis, and generic
  decorative Unsplash photography that is explicitly not presented as the
  fictional property.
- `frontend/src/assets/main.css` provides the mobile-first navy, blue, white,
  and yellow visual system, responsive card layout, visible focus treatment,
  reduced-motion handling, and styled initial/loading/empty/error states.
- `frontend/src/App.vue` loads travelers, requires explicit selection, locks all
  booking controls during a POST, and sends the selected user/trip identifiers
  through the request module.
- `frontend/src/components/BookingConfirmation.vue` renders only fields from
  the successful backend response, including the generated booking ID, status,
  dates, booked-on date, and estimated total.
- `frontend/src/components/BookingHistory.vue` renders loading, populated,
  empty, and retryable failure states from `GET /api/users/{user_id}/bookings`.
  The header navigation switches between `Find stays` and `My trips` without a
  router or additional dependency.
- Booking history now exposes cancellation and a two-step permanent deletion
  control. App-level mutation state locks every mutation control while a PATCH
  or DELETE is pending and refreshes history only after server success.

## Git state

- Root: `/Users/jlee/Desktop/psu4/ist402/a1_expedia_lite`
- Branch: `sqlite-crud`
- Backend feature checkpoint: `2c6fad6`
  (`feat: add SQLite booking persistence API`).
- Frontend feature checkpoint: `b4a167b`
  (`feat: add Expedia Lite booking frontend`), containing the completed Vue
  implementation, frontend tests, documentation, and this updated handoff.
- `main` and `origin/main` remain at the preserved Part 1 commit
  `a67b2e1fe9c699ad0dddfd0441ac429520b4616f`.
- The backend milestone is committed in 17 files at `2c6fad6`.
- `report.md` had an existing user change before this milestone and was not
  edited by the agent.
- The only current worktree change is the preserved user-owned `report.md`
  edit; it is intentionally excluded from the frontend feature checkpoint.

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

Frontend step 1 was checked with:

```bash
cd frontend
npm test
npm run lint
npm run build
```

Result: all 9 API-contract tests passed, lint passed, and Vite built 14 modules
successfully. The first AutoLoop check passed without a correction cycle.

Frontend step 2 repeated all three commands with the same passing result. The
integrated browser then verified the initial screen, a `Harbor` search with one
hotel and two stay cards, a `nonexistent` no-results state, blank validation,
an intentional backend-unavailable error, and recovery after backend restart.
Both remote decorative images loaded at 900 pixels, the page had no horizontal
overflow at the observed 575-pixel viewport, and browser error/warning logs
were empty.

Frontend step 3 repeated the 9 passing API tests, lint, and production build
(17 modules). The integrated browser verified traveler loading, required-field
focus without a database write, U006/T001 creation as B007, complete
backend-sourced confirmation, and an intentional failed POST while FastAPI was
stopped. Direct SQLite inspection confirmed B007 is `confirmed` and the runtime
database now contains 7 bookings.

Frontend step 4 repeated the 9 passing API tests, lint, and production build
(18 modules). In the integrated browser, history required an explicit traveler,
U006 history showed persisted B007 before and after a full browser refresh, and
an intentional backend stop produced the retryable failure state. A temporary
auto-cleaned SQLite database verified U006's genuine zero-booking state without
modifying the persistent runtime database. The normal backend was restored,
B007 remained present, and browser warning/error logs were empty.

Frontend step 5 passes the same 9 API tests, lint, and production build (18
modules). The integrated browser cancelled B007 and retained it in history;
direct SQLite inspection confirmed `status = cancelled`. With FastAPI
intentionally stopped, cancelling seeded B001 showed a recoverable error while
both U001 records remained visible. The deletion disclosure and `Keep booking`
path were verified. After explicit user authorization, the browser deleted only
B007 and rendered U006's empty-history state. Direct SQLite inspection then
showed exactly B001–B006, no B007, and a durable booking counter of 7.

The final AutoLoop verification passed on its first cycle: all 40 backend
tests, all 9 frontend API-contract tests, frontend lint, and the 18-module
production build succeeded. The integrated browser then reconfirmed `Harbor`
as one hotel and two stays, the no-result state, blank-query validation, U006's
post-deletion empty history, and the restored search view. At the observed
822-pixel viewport, document width matched viewport width and both decorative
images loaded at 900 natural pixels.

A follow-up integrated-browser button audit verified `Find stays`, `My trips`,
`Search`, both booking-button states, `Cancel booking`, `Delete permanently`,
`Keep booking`, `Yes, delete permanently`, traveler `Retry`, history `Try
again`, and the Expedia Lite home link. Every observed URL remained on
`127.0.0.1:5173`; the only anchor targets the local `#top` fragment, and no
clickable external target exists in the rendered page. The audit created,
cancelled, and deleted non-seed B008. Direct SQLite inspection afterward showed
only B001–B006 and no B008; the durable counter advanced to 8 as designed.

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

- FastAPI is currently running on `127.0.0.1:8000` in managed session 53897,
  and Vite is running on `127.0.0.1:5173` in managed session 92299. They were
  restarted at the user's request so the frontend can remain open for review.
- The temporary audit directory and database were removed.
- Starting the documented local server for integrated frontend testing created
  the ignored default runtime database at
  `backend/instance/expedia_lite.sqlite3`. It contains the six supplied booking
  rows after authorized deletion of the generated B007 test record. Its durable
  booking counter is 8 after the later B008 button audit, so neither deleted ID
  will be reused.
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

- The reference Expedia screenshots include photographs, ratings, amenities,
  savings, and flight/package claims that do not exist in this project's data.
  The frontend reproduces their layout hierarchy, palette, rounded card
  treatment, controls, and price emphasis without fabricating those values.
- Hotel imagery currently loads from three documented Unsplash URLs, so the
  decorative images require a network connection. A neutral background remains
  behind each image if the remote request is unavailable.
- The assignment's final manual browser demonstration, screenshots/screencast,
  evidence-log completion, final Git review/merge, and push remain future work.
- Python transitive dependencies are not fully pinned. The current suite has
  two upstream deprecation warnings.
- `report.md` contains an existing user edit and needs user-led reconciliation
  during final assignment documentation work.

## Recommended next task

Capture the course-submission screenshots/screencast and reconcile the
user-owned report/evidence log. Run the documented checks again only if source
changes are made after the frontend checkpoint.

Before changing frontend files, re-read `AGENTS.md`, `README.md`,
`docs/design-pipeline.md`, `docs/verification.md`, the assignment description,
and this handoff. Preserve the existing `report.md` change unless the user
explicitly includes it in the next task.
