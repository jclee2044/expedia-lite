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
stored-base immutability, and history persistence across restart.

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
    searches show $100 nightly and the fourth shows $120. Confirm the customer
    sees only the effective price, then search again and confirm it stays $120
    rather than compounding.
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

## Frontend live verification evidence

On 2026-09-17, the integrated browser logged in as the fictional `demo_u001`
account and submitted `Valley Trail` four times. Searches 1–3 displayed the
$100 nightly rate; search 4 displayed a $120 nightly rate and $240 stay total
without exposing the stored base values. After switching
to `demo_u002`, that account's first identical search remained $100. Restarting
FastAPI cleared the process-local session but retained history; after logging
back in, `demo_u001` search 5 remained $120. The browser console contained no
warnings or errors.

The earlier account/booking browser walkthrough used fictional `demo_u006`.
`Harbor` returned one hotel and two stays, booking T001 produced B010, and
history, refresh, cancellation, logout, login errors, and guarded deletion all
behaved as documented.

B010 was synthetic verification data created during this check. It was removed
afterward with the ownership-aware controller, leaving the six supplied booking
rows intact. The durable booking counter remains at 10 by design, so the deleted
ID cannot be reused.

## Backend live verification evidence

On 2026-09-17, 82 backend tests passed. They covered fresh schema version 3,
transactional version-1 and version-2 migration, preserved IDs and foreign
keys, accounts and sessions, ownership-protected booking CRUD/history, pure
pricing calculations, query normalization, New York day boundaries, search
isolation, non-compounding adjustment, and restart persistence. The default
runtime database was migrated to schema version 3: it retained U001–U006 and
all six booking-user links, kept H008's stored base at 10,000 cents, and
`PRAGMA foreign_key_check` returned no violations.

Ten frontend API tests, frontend lint, and the production build passed. The
integrated servers were started only for this verification and stopped after
the check.
