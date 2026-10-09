# Part 2 Turn 3 — checked saved-hotel retrieval checkpoint

Observed October 6, 2026 on `rag_integration`. This turn adds a read-only
retrieval controller and schema version 7. The current `/api/chat/stream`
remains the raw Gemini preview; it does not generate or execute SQL. The
two-call grounded chatbot and durable history behavior are Turn 4 work.

## Contract and boundaries

`retrieve_saved_stays(database_path, proposed_sql, proposed_params, request)`
accepts one SQLite `SELECT` whose only output column is `hotel_id` and a
separate trusted backend `StayRequest`. Proposed bind values must exactly match
that request; the model cannot change the ZIP or stay dates. The proposal must
use exactly `:postcode`, `:check_in`, and `:check_out`. The ZIP is five ASCII
digits and the ISO-date stay is one to fourteen nights. SQL has a 4,000
character limit. The controller rejects comments, quoted literals,
positional binds, semicolons, and non-`SELECT` statements before execution.
SQLite provides the decisive boundary: a separate `mode=ro` connection with
`query_only`, an authorizer allowing only `SELECT` and reads of the three
saved-hotel tables, a progress-handler time budget, and a 50-row cap. It runs
in a consistent read transaction.

Proposed SQL supplies **candidate IDs only**. Trusted controller SQL then
checks the saved ZIP association and every date from check-in through the
night before checkout. It rejects a stay with any missing night or any night
with zero rooms, and sums actual nightly rates in integer cents. Eligible
stays are ordered by total then ID. The returned framework-free model keeps
verified stays separate from incomplete and unavailable IDs. All amounts and
rooms are simulated classroom data.

Schema version 7 adds `chat_conversations`, `chat_messages`, and
`chat_retrieval_stages`, including conversation and turn IDs, UTC timestamps,
and a prompt version on trace stages. The version-6 migration is additive.
Turn 3 creates no conversation records; Turn 4 will own their application
operations and the JSON/stream contract.

## Reviewed synthetic proposal and rows

The following is a **test fixture proposal**, not Gemini output. It targets
the recreated 16803 fixture in the isolated temporary database.

```sql
SELECT DISTINCT h.hotel_id AS hotel_id
FROM saved_hotels AS h
JOIN saved_hotel_zips AS z ON z.hotel_id = h.hotel_id
LEFT JOIN demo_hotel_nights AS n
  ON n.hotel_id = h.hotel_id
  AND n.stay_date >= :check_in AND n.stay_date < :check_out
WHERE z.postcode = :postcode
```

Bindings: `postcode=16803`, `check_in=2026-10-11`,
`check_out=2026-10-13`. Candidate IDs observed: Campus Lantern,
College Green, Nittany Budget, Valley Ridge (their `fixture:` IDs).

| Checked hotel | Oct 11 cents / rooms | Oct 12 cents / rooms | Result |
| --- | ---: | ---: | --- |
| Campus Lantern | 12000 / 2 | 11000 / 1 | Eligible, 23000 cents |
| Valley Ridge | 13000 / 2 | 14000 / 2 | Eligible, 27000 cents |
| College Green | 15000 / 1 | Missing | Incomplete; no total claimed |
| Nittany Budget | 10000 / 0 | 9000 / 3 | Unavailable; no recommendation |

The one-night October 11 test yielded Campus Lantern (12000), Valley Ridge
(13000), and College Green (15000), in that order. ZIP 16804 yielded no
matches. October 14–15 yielded four incomplete candidates and no matches.

## Expected versus observed

| Check | Expected | Observed |
| --- | --- | --- |
| Focused retrieval, database, and saved-hotel tests | Migration and safety checks pass | 27 passed before the final trace-schema refinement; final full suite includes them |
| Full backend suite | Existing behavior survives schema change | 140 passed after trace-schema refinement; two existing dependency deprecation warnings |
| Blocked SQL and bind changes | Writes, multiple statements, other tables, functions, or altered request values fail without changing counts | All rejected in temporary fixture; counts unchanged |
| Row and execution limits | Oversized candidate set and over-budget query fail | Both rejected in tests |
| Migration | Existing saved rows retained; new tables empty and valid | Version-6 fixture migrated to version 7 twice without reseeding; FK check clear; trace rows persisted after reopen |
| Live RAG | Not part of Turn 3 | Not run |

No source or schema change was applied to the default runtime database for
this check. The already-running preview backend may still be using its
pre-migration connection; restart verification belongs to Turn 4. No dependency
was added. Frontend behavior did not change, so frontend checks were not run.

## Commands and verification scope

- Read `AGENTS.md`, `README.md`, the handoff, Part 2 plan and brief, prior
  checkpoints, prompt, verification notes, schema, controller, and tests with
  `cat`, `sed`, and `rg`. Checked Git root, branch, HEAD, status, and listeners
  with `git` and `lsof`. The handoff's tracked-change count was one lower than
  current Git status because the handoff file itself was edited afterward.
- Ran `backend/.venv/bin/python -m pytest backend/tests/test_retrieval.py
  backend/tests/test_database.py backend/tests/test_saved_hotels.py -q`:
  27 passed; two existing dependency deprecation warnings.
- Ran `backend/.venv/bin/python -m pytest backend/tests/test_retrieval.py -q`:
  10 passed after adding the deadline check.
- Ran `backend/.venv/bin/python -m pytest backend/tests -q` after the final
  trace-schema refinement: 140 passed, two dependency deprecation warnings.
- Ran a `backend/.venv/bin/python` temporary-fixture script printing the
  proposal, binds, candidate IDs, verified stays, incomplete IDs, and
  unavailable IDs; the values are recorded above. The fixture was removed
  when the script exited.
- Ran a targeted `git diff --check` on changed tracked files. A subsequent
  whitespace search found no matches; `rg` returns status 1 for that case.
  Broad `git diff --stat` includes earlier uncommitted Part 2 work and is not
  a Turn 3-only diff.

## Post-turn AutoLoop and automated browser pass

Run October 6, 2026 after the Turn 3 checkpoint. Acceptance was a green
backend suite and frontend test/lint/build, the documented name-search states,
and a working raw-preview chat interaction in the automated browser. No
in-scope source failure occurred, so there were **zero correction cycles**.

- `backend/.venv/bin/python -m pytest backend/tests -q`: 140 passed; the same
  two dependency deprecation warnings.
- From `frontend/`, `npm test && npm run lint && npm run build`: 24 tests
  passed; Oxlint, ESLint, and Vite build passed. The project lint command
  includes `--fix`; no deliberate frontend source edit was made in this pass.
- Browser at `http://127.0.0.1:5173/`: `Harbor` displayed one hotel and two
  stays; `nonexistent` displayed zero hotels and the no-results message; a
  blank search displayed `Enter a hotel name.`
- Chat opened, Escape closed it and restored focus, and a live preview question
  received a completed reply explaining that saved-hotel facts are not yet
  connected. Closing and reopening retained that exchange in the page session.
  Browser warning/error log was empty. This was **live raw Gemini**, not RAG.
- Shell `curl` to both localhost ports failed to connect despite `lsof`
  showing listeners. The browser reached the Vue app, and its search and chat
  requests succeeded. Direct browser navigation to the health endpoint was
  blocked by the browser client. The health endpoint was therefore not
  independently verified in this pass.

No server was started or stopped for this pass. The default runtime database
was not changed by the tests or the name-search UI while logged out. The
Turn 3 retrieval controller was checked through temporary-database tests;
it is not yet callable from the browser.
