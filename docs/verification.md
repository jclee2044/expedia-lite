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

The dependency-free frontend API checks verify the documented hotel, account,
login/session/logout, authenticated history, create, retrieve, status-update,
and delete request contracts. They also verify `204` handling, backend detail
messages, status preservation, and operation-specific fallbacks.

The focused SQLite foundation check is:

```bash
backend/.venv/bin/python -m pytest backend/tests/test_database.py
```

It uses temporary database files to verify initial seed counts, preserved
values, repeated initialization, schema-version-1 migration, persistence after
reopen, monotonic booking and user IDs, foreign-key enforcement, invalid seed
handling, and refusal to merge an unmarked partially populated database. It
does not create the default runtime database.

The focused account checks are:

```bash
backend/.venv/bin/python -m pytest \
  backend/tests/test_accounts.py backend/tests/test_account_api.py
```

They verify validation, case-insensitive duplicate rejection, account
persistence, generic login errors, opaque session creation/expiration/logout,
password-free responses, authenticated booking identity, and ownership.

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
7. Try booking without an account and confirm the Account screen opens with a
   clear login/create message.
8. Create an account using a made-up username and password. Confirm its username
   appears in the header and on the signed-in account card.
9. Log out, attempt the same username with different capitalization, and confirm
   duplicate feedback. Then verify a wrong password produces the generic login
   error and a correct password logs in.
10. Search for `Harbor` and book T001. Confirm the server-issued booking ID,
    confirmed status, account, hotel, stay, dates, booked-on date, and estimated
    total appear in the confirmation card.
11. Open `My trips` and confirm the new booking appears. Refresh the browser,
    reopen `My trips`, and confirm the session and booking are restored.
12. Cancel the booking and confirm its status changes to `cancelled`
    while the record remains in history.
13. Log out and confirm the prior account's history and confirmation disappear.
    Log back in and confirm the persisted booking returns.
14. Stop FastAPI, attempt a mutation, and confirm the error is visible while
    the previously loaded records remain honest; restart FastAPI afterward.
15. Open `Delete permanently`, use `Keep booking` once to verify the guard,
    then explicitly confirm deletion of a non-seed test booking. Confirm the
    account returns to the empty-history state and verify directly that the
    six supplied booking IDs remain in SQLite.

Also confirm that results use the documented repeated-card structure with a
decorative image, hotel and trip facts, fixed dates, nights, nightly rate, and
estimated total. At a narrow viewport, cards must remain readable without
horizontal page overflow. Browser console warnings and errors should be empty.

The API contract can also be inspected at `http://127.0.0.1:8000/docs`.

## Frontend live verification evidence

On 2026-09-17, the integrated browser logged in as the fictional `demo_u006`
account and displayed that username in the header and Account screen. `Harbor`
returned one hotel and two stays. Booking T001 produced B010, personalized
history showed it, and both the session and booking remained visible after a
full browser refresh. Cancellation changed B010 to `cancelled` without removing
it. The permanent-delete action exposed its second-step disclosure, and `Keep
booking` closed the guard without deleting. Logout removed the account identity
and protected history; opening `My trips` then returned to Account with useful
feedback. A wrong password displayed the generic login error, the Create
Account form exposed username/password/optional-email fields, and the browser
console contained no warnings or errors.

B010 was synthetic verification data created during this check. It was removed
afterward with the ownership-aware controller, leaving the six supplied booking
rows intact. The durable booking counter remains at 10 by design, so the deleted
ID cannot be reused.

## Backend live verification evidence

On 2026-09-17, 63 backend tests passed. They covered fresh schema version 2,
transactional version-1 migration, preserved IDs and foreign keys, account
creation and persistence, case-insensitive uniqueness, monotonic user IDs,
generic authentication failure, expiring/logout sessions, password-free
responses, ownership-protected booking CRUD/history, search, and the existing
booking lifecycle. The default runtime database was also migrated from schema
and seed version 1 to version 2: it retained U001–U006 and all six booking-user
links, and `PRAGMA foreign_key_check` returned no violations.

Ten frontend API tests, frontend lint, and the production build passed. The
integrated servers were started only for this verification and stopped after
the check.
