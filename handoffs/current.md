# Expedia Lite current handoff

Refreshed October 8, 2026 for the remaining Part 2 report review and video
recording. Reconstruct this snapshot using `handoffs/create-handoff.md`
and `AGENTS.md` before changing anything. The user authorized the readiness
repairs and implementation checkpoint; a future continuation must still
verify current Git/files/services before editing.

## Objective and decisions

The revised Assignment 2.2 endpoint and local-storage foundation are
implemented and verified on `rag_integration`. The October 8 critical
review found two actual grounding defects, repaired them, and tested the
complete workflow. The student will record the Part 2 demo. Remaining:
record it, test instructor access, add the link to `report.md`, review the
report and submit it. Do not invent a video link or claim submission.

Use Gemini 3.5 Flash-Lite (`gemini-3.5-flash-lite`) for both runtime model
requests. Today's Codex review/repair model is **GPT-6.1 Sol**, confirmed by
the student. Earlier Part 2 records say GPT-6; their exact selector name is
not independently established. Preserve the default database, synthetic
course data, Part 1 behavior and the student's mockup reorganization.
All keys remain in ignored root `.env`; no dependency change was made.
The final assistant message background is neutral off-white `#f7f7f7`.
The earlier warm off-white and cream previews were superseded by this choice.

## Architecture and files

Vue View → FastAPI routes → framework-free Controllers → Models/SQLite.

- `backend/models/schema.py`: schema 7, additive migrations from versions
  4–6; saved hotels, ZIPs, nights and durable chat messages/stages.
- `backend/controllers/saved_hotels.py`: transactional save/duplicate/remove.
  `frontend/src/api/zipSearch.js`: saved-local-first lookup.
- `backend/controllers/retrieval.py`: bounded parameterized SELECT, exact
  trusted binds, separate read-only connection, query_only, authorizer and
  execution budget; independently verifies nightly rows/totals and counts
  saved hotels for the ZIP.
- `backend/controllers/gemini.py`: backend-only provider calls. Second
  request uses JSON schema and requires normal completion.
- `backend/controllers/grounded_answer.py`: validates selected IDs/reason
  and renders factual names, dated cents/rooms and totals from checked rows.
- `rag_chat.py`, `chat_context.py`, `chat_history.py`: two-call flow,
  bounded context, trace and persistence. Model output is buffered until
  checked; no unchecked partial answer is sent to Vue.
- `prompts/hotel-assistant.md`: version 5, relevant schema/query rules,
  structured second answer. Result trace stores `second_model_answer` and
  `answer_validation` alongside checked retrieval.
- `frontend/src/components/ChatPopup.vue`: popup, keyboard controls,
  loading/Edit/Retry states and restored history.
- `backend/prepare_rag_demo.py` and `docs/part2-rag-fixture.json`: new
  synthetic databases only, refuses overwrite.
- `backend/inspect_rag_demo.py`: read-only trace CLI for recording.
- `backend/tests/browser_scenarios.py`: explicit isolated mock providers;
  normal application does not use these mocks.
- `docs/assignment2-part2-stage6.md`, `stage6-trace.txt`,
  `stage6-commands.txt`: audit, exact saved trace and shell command log.
  `docs/assignment2-part2-demo.md`: recording sequence.
  `report.md`: updated submission draft, assessed commit present, video TODO.
  `docs/rag-context.md`: current version 5 plus historical October 6 traces.

## Git evidence and checkpoint

Root: `/Users/jlee/Desktop/psu4/ist402/a1_expedia_lite`.
Branch: `rag_integration`, tracking `origin/rag_integration`.
Verified application HEAD: **`1e6825afc68f12b68c61a80e7f8968dd6d256d4b`**
(`Use neutral off-white for assistant messages`). The working tree was clean
immediately after this commit. It changes one CSS declaration and adds the
final browser/build evidence plus clearly labeled historical cream previews.
The earlier complete RAG checkpoint is `23b9dc2` (88 paths); its report and
handoff commit is `bf7e1b8`. Both were previously pushed. Anonymous GitHub
API access at that checkpoint returned 200 and `private=false`.
The new application and documentation commits are saved locally. Publishing
them is pending explicit user approval: automatic approval review rejected
the push because the latest request authorized commits and file updates but
did not explicitly authorize exporting this payload to the GitHub destination.
Recheck local/remote state before treating the assessed commit as published.

This handoff/report and updated verification log form a subsequent
documentation-only commit.
The SHA above identifies tested application source, not the self-referential
commit containing this file. Before this documentation commit, only
`report.md`, `handoffs/current.md` and the updated off-white verification
log are expected documentation changes.
Use `git log -2 --oneline`, `git status --short`, and
`git diff 1e6825a HEAD -- backend frontend prompts data`
to verify that later documentation did not alter tested code. Confirm the
final remote SHA with `git ls-remote --heads origin rag_integration`.

Local `main`, `assignment2_part2_in_class` and `origin/main` remain at
`d8edae8`; they do not contain Part 2. No merge or PR was requested.
`.env`, databases, venv, node_modules and dist are ignored and unstaged.
Staged credential-pattern/path checks and whitespace checks passed after
removing two extra final blank lines in documents.

## Completed work and observed checks

The latest UI check built 31 modules successfully with `npm run build`
from `frontend/`. Automated browser inspection restored saved messages,
confirmed five assistant bubbles at `rgb(247,247,247)`, and found no console
warnings/errors. Screenshot and command/results record:
`docs/test-screenshots/chat-off-white-background.png` and `.txt`.
No new model request or backend test run was needed for the CSS-only change.
Its task-owned services and temporary tab were closed. The current refresh
also found no listeners on the six project ports below.

The full regression and live checks below belong to the earlier integrated
audit at `23b9dc2`; they were not rerun while committing the color change.

Two review defects were reproduced: free prose misplaced a nightly date,
and filtered-empty candidates were mistaken for no saved hotels. Version 5
repairs both through validated selection/database rendering and independent
saved counting.

Commands actually run from root:

```bash
backend/.venv/bin/python -m pytest backend/tests/test_gemini.py backend/tests/test_grounded_answer.py backend/tests/test_retrieval.py backend/tests/test_rag_chat.py -q
backend/.venv/bin/python -m pytest backend/tests -q
git diff --check
backend/.venv/bin/python -m backend.inspect_rag_demo backend/db/part2-oct8-audit.sqlite3 --turn-id f2afaf26-5a1e-4a1c-870e-252b37e6b39c
```

Focused suite: **40 passed**. Full suite: **164 passed**, including final
repeat after singular/plural wording; two existing dependency deprecation
warnings. From `frontend/`, `npm test`: **26 passed**;
`npm exec -- oxlint .`, `npm exec -- eslint .`, `npm run build`: passed.
No code-test correction loop or dependency change was needed.

Actual live Gemini two-call browser evidence over synthetic ZIP 16803:
October 11–13 Campus $230, Valley $270; exact dated nightly facts and checkout
exclusion; zero-room Budget excluded. Budget under $50, missing October 15,
and absent ZIP 16804 produced distinct correct answers. The final successful
turn is `f2afaf26-5a1e-4a1c-870e-252b37e6b39c`, conversation
`7162961e-62a4-49b6-b727-850f7a0ffb91`.

Actual Geoapify ZIP 16802 returned 21 places. Browser Add saved Scholar with
five simulated default nights; duplicate API save preserved one record and
all nights; both backend and frontend were restarted, and reload restored
saved hotel/history with local-first lookup. Remove cascaded its ZIP/night
rows. Card/map selection, map Enter, chat Enter/Shift+Enter/Escape/Edit,
invalid ZIP, Harbor one hotel/two stays, blank and no-results were observed.

Separate mock browser checks covered leading-zero ZIP, empty/unresolved/
provider failure, quota, rejected UPDATE, unsupported answer and filtered
zero candidates with three saved hotels. Retry of the bad-answer mock
failed safely as expected. Both browser warning/error logs were empty.
The mock popup fit a measured 520px viewport; no horizontal overflow.
See stage6 for the full expected-versus-observed table and screenshots.

## Services and databases

All task-owned servers were stopped with Ctrl+C and both temporary tabs
closed; viewport override reset. Final `lsof` found no listeners on
8000/8001/8002/5173/5174/5175. No unrelated process was stopped.

Normal audit used ignored `backend/db/part2-oct8-audit.sqlite3`,
backend 8001/frontend 5174; mocks used `part2-oct8-mock.sqlite3`,
backend 8002/frontend 5175. See command log for exact startup commands.
Both fixture DBs: schema 7, 3 saved hotels/3 ZIPs/6 nights, no foreign-key
violations, original eight hotels/twelve trips/six seed bookings.
The default runtime was inspected read-only: schema 6,
8 hotels/12 trips/10 bookings, 1 saved/1 ZIP/5 nights, no violations.
It was not reset or migrated; normal next startup migrates to schema 7.

## Limits and next action

Verified: full regression/build/lint, current live model flow, direct SQLite
comparison, controlled failure UI, local CRUD/persistence, current branch
push/public repository, safe staging, 29 current Markdown files' references,
and service cleanup. No data CSV, Part 1 geocoding/place/map code, package
manifest or lockfile changed.

Unverified: Part 2 video/link/instructor access, student final report review
and submission, every natural-language query or provider failure, full
browser-process restart, and exact earlier Codex selector. These checks
establish synthetic saved inventory, not live rates or bookable rooms.
An archived `a1-report.md` references an absent local
`Expedia Lite Demo.mp4`; it was not recreated and is separate from Part 2.

Read AGENTS, README, this handoff, verification, stage6 and recording guide.
After reconstruction and the student's authorization, start a new fixture
for the video (or reuse the audit DB without resetting it), record the
question→SQL→records→second recommendation→displayed answer and expected
versus observed checks, add the accessible link, review/upload `report.md`.
