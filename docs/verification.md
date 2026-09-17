# Expedia Lite verification

Run commands from the project root unless a step says otherwise.

## Automated checks

```bash
backend/.venv/bin/python -m pytest backend/tests
cd frontend
npm run lint
npm run build
```

The focused SQLite foundation check is:

```bash
backend/.venv/bin/python -m pytest backend/tests/test_database.py
```

It uses temporary database files to verify initial seed counts, preserved
values, repeated initialization, persistence after reopen, monotonic booking
IDs, foreign-key enforcement, invalid seed handling, and refusal to merge an
unmarked partially populated database. It does not create the default runtime
database.

The search and API tests also use temporary databases. They verify the existing
search JSON contract, the reference queries shown in the screenshots, startup
initialization, and a second startup that continues serving search after the
temporary seed CSV files have been removed.

The focused booking checks are:

```bash
backend/.venv/bin/python -m pytest \
  backend/tests/test_bookings.py backend/tests/test_booking_api.py
```

They verify seeded and empty history, joined values across all four tables,
creation beginning at `B007`, server-assigned booking dates, missing-related
record errors, request validation, cancellation versus deletion, non-reused
IDs, and persistence through a second FastAPI application startup.

## Integrated check

1. Start FastAPI from the project root with `backend/.venv/bin/python -m uvicorn backend.app.main:app --reload`.
2. Start Vue from `frontend/` with `npm run dev`.
3. Open `http://127.0.0.1:5173` and search for `Harbor`.
4. Confirm the page reports one hotel and shows the `T001` and `T009` stays.
5. Search for an unknown name and confirm the no-results state.
6. Submit a blank search and confirm `Enter a hotel name.` appears.

The API contract can also be inspected at `http://127.0.0.1:8000/docs`.

## Backend live verification evidence

On 2026-09-17, the completed backend was exercised through Uvicorn against an
isolated temporary SQLite database. The project seed files and default runtime
database were not modified.

Observed first-run behavior:

- OpenAPI returned `200` and exposed every documented search, user, history,
  create, retrieve, update, and delete method.
- `Harbor` returned H001 with T001 and T009; `nonexistent` returned a valid
  empty `200` response.
- U001 history returned B002 and B001; U006 returned an empty history.
- Creating U006/T001 returned `201` with B007 and joined confirmation data.
- Updating B007 returned `200` with `cancelled`, and B007 remained in history.
- Creating U006/T009 returned B008; deleting B008 returned `204`, and its next
  retrieval returned `404`.
- An unknown user returned `404`, an unsupported status returned `422`, and a
  blank search returned `400`.

After stopping and restarting Uvicorn against the same database:

- B007 remained cancelled and present in U006 history.
- B008 remained deleted.
- Hotel search continued to return the seeded results without reseeding.
- The next created booking was B009, proving the durable counter was not reset
  and the deleted B008 ID was not reused.

After shutdown, a direct read of the closed database showed 8 hotels, 12 trips,
6 users, and 8 bookings: the 6 starter bookings plus B007 and B009. Both schema
and seed versions were `1`, the booking counter was `9`, and U006 owned
cancelled B007 and confirmed B009. The temporary server was stopped and its
temporary directory was removed.
