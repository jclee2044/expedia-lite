# Expedia Lite current handoff

Verified from repository and runtime evidence on 2026-09-21. Recheck Git state
and active services before continuing in a later task.

## Current objective and decisions

Expedia Lite Part 2 is implemented, verified, documented, and pushed to
`origin/main`. The remaining work is submission review rather than application
development: resolve the local screenshot edits, insert the chosen submitted
commit into `report.md` if required, and submit the report and demo video.

The project follows the supplied assignment rather than the obsolete earlier
assignment summary. No additional evidence-log deliverable is required. The
application keeps fixed trip dates; an unrestricted date picker was not added
because it would imply availability behavior outside the assignment data model.

## Architecture and important files

```text
Vue View -> FastAPI routes -> framework-free Controllers -> Models/SQLite
```

- `frontend/src/App.vue` coordinates search, accounts, booking confirmation,
  history, cancellation, and deletion.
- `frontend/src/components/` contains the reusable presentation components;
  `frontend/src/api/` contains browser request code.
- `backend/app/` contains FastAPI routes and JSON schemas.
- `backend/controllers/` contains account, search, pricing, persistence, and
  booking behavior.
- `backend/models/` contains framework-free entities, calculations, and schema
  version 4.
- `backend/db/expedia_lite.sqlite3` is the ignored runtime database. CSV files
  under `data/` seed it once; later reads and writes use SQLite.
- `README.md`, `docs/design-pipeline.md`, `docs/verification.md`, and
  `docs/backend-persistence-contract.md` describe the current implementation.
- `report.md` contains the Part 2 report and links the committed root-level
  `Expedia Lite Demo.mp4` demonstration video.

Sessions are process-local, so restarting FastAPI signs the browser out while
accounts, searches, and bookings remain persisted in SQLite.

## Completed work

- Hotel search, responsive result cards, clear empty/error states, account
  creation/login/logout, booking confirmation, history, cancellation, and
  guarded permanent deletion are implemented end to end.
- All frontend CRUD actions cross FastAPI and use SQLite after one-time CSV
  seeding. Existing IDs are preserved and new user/booking IDs are monotonic.
- Personalized search pricing is isolated by account, query, and New York
  calendar day. Bookings snapshot the effective quoted rate so confirmation
  and history retain the displayed price.
- Schema migrations support versions 1 through 4 while preserving records and
  relationships.
- Commit `88f9083` contains the quote fix, refreshed assignment documentation,
  automated coverage, and Part 2 screenshots.
- Commit `68ce6b0` contains the revised report and the 14 MB demonstration video.
  It was pushed to `origin/main`.

## Verification evidence

The final source verification commands were:

```bash
backend/.venv/bin/python -m pytest backend/tests
cd frontend
npm test
npm run lint
npm run build
```

Observed results: 85 backend tests passed with two upstream TestClient
deprecation warnings; 10 frontend API-contract tests passed; lint passed; and
Vite built 20 modules.

The integrated browser walkthrough verified successful and empty searches,
blank-search feedback, account behavior, booking creation/read/update/delete,
refresh and restart persistence, responsive cards, and an error-free browser
console. The fourth signed-in `Valley Trail` search displayed $120 nightly and
$240 total, and the booking retained that quote in confirmation and history.

Direct SQLite inspection showed schema version 4 and no foreign-key violations.
Synthetic audit bookings B014 and B015 were deleted through the application;
durable IDs were not reused. Seed CSV files were not modified.

These verification results were not rerun after commit `68ce6b0` because that
commit changed only `report.md` and added the video.

## Git state

- Root: `/Users/jlee/Desktop/psu4/ist402/a1_expedia_lite`
- Current branch: `main`
- Latest application-fix checkpoint: `88f9083`
- Latest report/video checkpoint before this handoff refresh: `68ce6b0`
- `main` and `origin/main` matched at `68ce6b0` before this documentation-only
  handoff refresh. After the refresh is pushed, the two refs should match again.
- Other retained branches: `basic-search` at `71289a2`, `sqlite-crud` at
  `6192f8f`, and `bonus-features` at `ad00ac8`.
- No dependency declarations or lockfiles changed during the final fixes.

The working tree is not otherwise clean. There are user-owned local changes to
five Part 2 screenshot PNGs and a local deletion of
`docs/test-screenshots/part2-booking-history.png`. These screenshot changes are
not part of the handoff update and must not be discarded or committed without
reviewing the intended final evidence set.

## Active services

Project-owned demo services were verified listening locally:

- FastAPI: `http://127.0.0.1:8000`, started from the project root with
  `backend/.venv/bin/python -m uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000`
- Vue/Vite: `http://127.0.0.1:5173`, started from `frontend/` with
  `npm run dev -- --host 127.0.0.1 --port 5173`

Stop only these project-owned services when the demo is complete.

## Remaining work, risks, and next action

- Review the five modified screenshots and the deleted booking-history image,
  then intentionally keep, restore, or commit that evidence in a separate step.
- `report.md` still uses a pending Part 2 checkpoint line. If the submission
  requires an exact hash inside the uploaded report, replace it with the chosen
  submitted checkpoint as part of the final submission workflow.
- The assignment's manual VS Code review and the actual Canvas submission are
  student actions and have not been independently verified here.
- Decorative Unsplash images require network access, although all meaningful
  application content remains readable if they fail to load.
- The two backend warnings are upstream TestClient deprecations, not test
  failures.

Recommended next action: review the local screenshot changes before making any
further Git commit. The next agent should first read `AGENTS.md`, `README.md`,
this handoff, `docs/verification.md`, and `report.md`, then compare
`git status --short` with the screenshot references in the report.

## Verification boundary

Verified facts: current architecture, schema version, committed demo video,
documented automated results, active local ports, branch names, pushed commit
history through `68ce6b0`, and the current local screenshot changes.

Still requiring user confirmation or fresh verification: whether the local
screenshot edits are intentional, whether the manual VS Code review is
complete, which exact commit should be named in the uploaded report, and
whether the external course submission has been completed.
