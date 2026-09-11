# Expedia Lite current handoff

Verified from repository evidence on 2026-09-11. Recheck Git state and named files before continuing.

## Objective and decisions

The current milestone is a local hotel-name search. Vue owns the interface, FastAPI owns the HTTP/JSON boundary, and framework-free Python reads and validates the CSV data, joins hotels and trips through `hotel_id`, and calculates stay prices. The data is synthetic and the current CSV files are read-only.

## What works

- `frontend/src/App.vue` provides loading, results, no-results, and blank/error states; `frontend/src/api/hotels.js` owns requests.
- `GET /api/hotels/search?name=...` is implemented in `backend/app/main.py` with response models in `backend/app/schemas.py`.
- `backend/app/search.py` reads `data/hotels.csv` and `data/trips.csv`, validates IDs and dates, joins records by `hotel_id`, matches names case-insensitively, and calculates nights and stay prices.
- Vite proxies `/api` to FastAPI. The contract and run commands are documented in `README.md`.
- `docs/design-pipeline.md`, `docs/verification.md`, and `prompts/hotel-search.md` capture the current design, checks, and selected implementation prompt.

## Git state

- Root: `/Users/jlee/Desktop/psu4/ist402/a1_expedia_lite`
- Branch/upstream: `main` tracking `origin/main`
- The implemented hotel-search checkpoint is `71289a2 feat: add basic hotel search`.
- `basic-search` also points to `71289a2`.
- The Part 1 report and name/documentation consistency checkpoint has been committed and pushed to `main`. Verify the current tip with `git rev-parse HEAD` before relying on a copied commit ID.

## Checks observed on 2026-09-11

```bash
backend/.venv/bin/python -m pytest backend/tests
```

Result: 9 passed. Two dependency deprecation warnings came from FastAPI/Starlette test-client internals.

```bash
backend/.venv/bin/python -c "# load hotels.csv and trips.csv; assert every trip hotel_id resolves"
```

Result: valid relationship across 8 hotels and 12 trips.

```bash
cd frontend
npm run lint
npm run build
```

Result: lint passed; Vite 8.3.0 built 13 modules successfully.

```bash
git diff --check
```

Result: passed.

Local HTTP checks confirmed that `http://127.0.0.1:5173/` serves the Vue page and a `Harbor` API request returns one hotel with stays `T001` and `T009`.

## Active services

- FastAPI is listening on `127.0.0.1:8000` as PID 59670 from the project root.
- Vite is listening on `127.0.0.1:5173` as PID 59699 from `frontend/`.
- These existing services were verified but not started or stopped during the documentation refresh.

## Remaining limitations

- Booking creation, confirmation, history, SQLite initialization, and persistence are not implemented.
- The frontend has lint/build coverage but no dedicated component or end-to-end test suite.
- The current turn verified the served page and API response over HTTP but did not repeat the full interactive browser workflow.
- Python transitive dependencies are not fully pinned, and the test suite reports two upstream deprecation warnings.

## Next task

Define the booking/persistence contract before implementing the first booking flow.

Read `AGENTS.md`, `README.md`, `docs/design-pipeline.md`, `docs/verification.md`, and this handoff first. Treat the repository and fresh checks as authoritative if this note becomes stale.
