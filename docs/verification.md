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
search JSON contract, pure model pricing, New York day boundaries, current-search
inclusion, user/query/day isolation, non-compounding fourth-search pricing,
stored-base immutability, booking-price snapshots, and history persistence
across restart.

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
10. While signed in, search `Valley Trail` four times. Confirm the first three
    searches show $100 nightly and the fourth shows $120. Book the fourth result
    and confirm its confirmation and history retain the displayed $120 nightly
    and $240 total. Search again and confirm the current offer stays $120 rather
    than compounding.
11. Log into a different demo account and search `Valley Trail`; confirm its
    first result is $100. Confirm a different query is counted separately.
12. Search for `Harbor` and book T001. Confirm the server-issued booking ID,
    confirmed status, account, hotel, stay, dates, booked-on date, and estimated
    total appear in the confirmation card.
13. Open `My trips` and confirm the new booking appears. Refresh the browser,
    reopen `My trips`, and confirm the session and booking are restored.
14. Cancel the booking and confirm its status changes to `cancelled`
    while the record remains in history.
15. Log out and confirm the prior account's history and confirmation disappear.
    Log back in and confirm the persisted booking returns.
16. Stop FastAPI, attempt a mutation, and confirm the error is visible while
    the previously loaded records remain honest; restart FastAPI afterward.
17. Open `Delete permanently`, use `Keep booking` once to verify the guard,
    then explicitly confirm deletion of a non-seed test booking. Confirm the
    account returns to the empty-history state and verify directly that the
    six supplied booking IDs remain in SQLite.

Also confirm that results use the documented repeated-card structure with a
decorative image, hotel and trip facts, fixed dates, nights, nightly rate, and
estimated total. At a narrow viewport, cards must remain readable without
horizontal page overflow. Browser console warnings and errors should be empty.

The API contract can also be inspected at `http://127.0.0.1:8000/docs`.

## Current verification evidence

On 2026-09-21, 85 backend tests passed. They covered fresh schema version 4;
transactional version-1, version-2, and version-3 migration; preserved IDs and
foreign keys; accounts and sessions; ownership-protected booking CRUD/history;
pure pricing calculations; query normalization; New York day boundaries;
search isolation; non-compounding adjustment; booking-price snapshots; and
restart persistence. `PRAGMA foreign_key_check` reported no violations.

Ten frontend API-contract tests, frontend lint, and the production build passed.
The build transformed 20 modules.

The integrated browser walkthrough used the fictional `audit_0921` account.
Its fourth `Valley Trail` search displayed $120 nightly and $240 total. Booking
B015 preserved that exact quote in its confirmation and history. Cancellation
retained B015 with cancelled status; guarded permanent deletion then removed
only B015 and reduced the displayed history count from four to three. A
`nonexistent` search displayed the expected no-results state. The browser
console contained no warnings or errors. Screenshots from this walkthrough are
linked in `report.md`.

B015 was synthetic verification data and was removed through the application.
The database keeps its durable ID counter, so deleted booking IDs are not
reused. Other synthetic audit records in the ignored local runtime database do
not change the supplied CSV files or committed project data.
