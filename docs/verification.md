# Expedia Lite verification

Run commands from the project root unless a step says otherwise.

## Automated checks

```bash
backend/.venv/bin/python -m pytest backend/tests
cd frontend
npm test
npm run lint
npm run build
```

The dependency-free frontend API checks verify the documented hotel, user,
history, create, retrieve, status-update, and delete request contracts. They
also verify `204` handling, backend detail messages, status preservation, and
operation-specific fallbacks for non-JSON failures.

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
7. Search for `Harbor`, try booking without a traveler, and confirm the traveler
   selector receives focus with a clear validation message.
8. Select Demo Traveler 6 and book T001. Confirm the server-issued booking ID,
   confirmed status, traveler, hotel, stay, dates, booked-on date, and estimated
   total appear in the confirmation card.
9. Open `My trips` for the same traveler and confirm the new booking appears.
10. Refresh the browser, select the traveler again, reopen `My trips`, and
    confirm the booking is still retrieved from SQLite.
11. Verify an empty traveler history and an unavailable-backend history error
    with a visible retry action.
12. Cancel a confirmed booking and confirm its status changes to `cancelled`
    while the record remains in history.
13. Stop FastAPI, attempt a mutation, and confirm the error is visible while
    the previously loaded records remain honest; restart FastAPI afterward.
14. Open `Delete permanently`, use `Keep booking` once to verify the guard,
    then explicitly confirm deletion of a non-seed test booking. Confirm the
    traveler returns to the empty-history state and verify directly that the
    six supplied booking IDs remain in SQLite.

Also confirm that results use the documented repeated-card structure with a
decorative image, hotel and trip facts, fixed dates, nights, nightly rate, and
estimated total. At a narrow viewport, cards must remain readable without
horizontal page overflow. Browser console warnings and errors should be empty.

The API contract can also be inspected at `http://127.0.0.1:8000/docs`.

## Frontend live verification evidence

On 2026-09-17, the integrated browser completed the search, traveler,
creation, confirmation, persisted-history, cancellation, failed-mutation, and
two-step deletion flows against the default local SQLite database. B007 was
created for U006/T001, persisted across a full browser refresh, was cancelled
while remaining in history, and was then deleted only after the permanent
deletion disclosure was explicitly confirmed. The UI returned to U006's empty
history state. A direct SQLite read showed exactly the supplied B001–B006 rows,
no B007 row, and a booking counter of 7, proving that deletion did not alter
seed records or make the generated ID reusable.

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
