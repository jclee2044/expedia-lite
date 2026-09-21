# Expedia Lite current handoff

Verified from repository and runtime evidence on 2026-09-21. Recheck the Git
state and named checks before continuing in a later task.

## Objective and architecture

Expedia Lite Part 2 is a Vue 3 and FastAPI travel prototype with account
creation/login, hotel search, simulated booking, persistent history,
cancellation, and guarded permanent deletion. The supplied CSV files seed
SQLite once; subsequent application reads and writes use SQLite.

The dependency direction is:

```text
Vue View -> FastAPI routes -> framework-free Controllers -> Models/SQLite
```

The runtime database is `backend/db/expedia_lite.sqlite3` and is ignored by
Git. Session tokens are process-local, so a FastAPI restart signs the browser
out while accounts, searches, and bookings remain persisted.

## Completed work

- Fixed the booking-price mismatch exposed by the personalized search rule.
  Bookings now snapshot the server-derived effective nightly rate shown for
  the submitted search, and confirmation/history read that quote rather than
  recalculating from the hotel's base rate.
- Advanced the schema from version 3 to version 4. Fresh seeds populate quoted
  rates, and supported version-1, version-2, and version-3 databases migrate
  transactionally without changing IDs or relationships.
- The create-booking JSON contract now accepts optional `search_query`.
  Browser bookings validate the trip against the recorded account search;
  missing or mismatched context is rejected. Direct API calls that omit the
  optional context retain the documented base-price behavior.
- Cleared stale confirmation on a new search or deletion. Cancelling the
  confirmed booking immediately changes its confirmation copy and status.
- Updated the README, design, MVC, persistence, and verification contracts.
- Replaced the obsolete local assignment summary with the current assignment
  text supplied by the student, including the correct dates and deliverables.
- Rebuilt `report.md` around the Part 2 assignment headings and current
  expected/observed evidence. Six current Part 2 screenshots are under
  `docs/test-screenshots/part2-*.png`; older Part 1 screenshots are preserved.

## Verification

Final automated checks on 2026-09-21:

```bash
backend/.venv/bin/python -m pytest backend/tests
cd frontend
npm test
npm run lint
npm run build
```

Results: 85 backend tests passed with two upstream TestClient deprecation
warnings; 10 frontend tests passed; lint passed; Vite built 20 modules.

The integrated browser walkthrough used the synthetic `audit_0921` account.
The fourth `Valley Trail` search showed $120 nightly and $240 total. Booking
B015 preserved the same quote in confirmation and history, cancellation kept
the record, guarded deletion removed it, and `nonexistent` produced the clear
no-results state. The browser console had no warnings or errors.

Direct inspection of the ignored runtime database showed schema version 4,
no foreign-key violations, and the following retained synthetic audit rows:

- B011: U008/T001, confirmed, quoted 15000 cents
- B012: U008/T008, confirmed, quoted 10000 cents (created before the fix)
- B013: U008/T008, confirmed, quoted 12000 cents (post-fix verification)

B014 and B015 were deleted through the application. The durable booking
counter is 15, so their IDs will not be reused. Seed CSV files were not changed.

## Git state at this checkpoint

- Root: `/Users/jlee/Desktop/psu4/ist402/a1_expedia_lite`
- Branch: `main`
- HEAD before the current uncommitted fixes: `ad00ac899ac4b17ad7101fab831ea768abaa11b1`
- `origin/main`: `a67b2e1fe9c699ad0dddfd0441ac429520b4616f`
- Local `main` is six commits ahead of `origin/main` before committing this
  final fix/documentation set.
- The quote fix, updated tests/docs/report/handoff, and new Part 2 screenshots
  are uncommitted. Inspect `git status --short` for the exact current list.
- No dependency declarations or lockfiles changed.

## Active services and cleanup

The task-owned FastAPI and Vite processes used for the final walkthrough were
stopped cleanly. No project service is intentionally left running. The ignored
runtime database deliberately retains synthetic local audit data.

## Remaining submission work

- Perform the student-only VS Code Search review requested by the assignment.
- Record the required under-three-minute demo video.
- Review `git diff` and the current screenshots, then create the final Git
  checkpoint and push when the student authorizes it.
- If the submission format requires the exact Part 2 commit inside `report.md`,
  replace its pending checkpoint line as part of the chosen final Git workflow.

Remote decorative hotel photos remain network-dependent, but all meaningful
hotel, stay, price, and booking information remains readable without them.
