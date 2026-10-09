# Part 2 Turn 4 — two-call grounded chat checkpoint

Observed October 6, 2026 on `rag_integration`. The chat now follows question
→ Gemini SQL proposal → checked read-only SQLite retrieval → second Gemini
request with bounded checked facts → streamed answer. The browser stores only
an opaque conversation ID; messages and proposal, execution, result, and
error stages are persisted in SQLite with turn IDs, UTC timestamps, and prompt
version. `docs/rag-context.md` holds the traced live synthetic exchange.

## Expected versus observed

| Check | Expected | Observed |
| --- | --- | --- |
| Focused mocked orchestration | Two model calls, safe SQL rejection, no-match, failure trace, history restore | Passed in `backend/tests/test_rag_chat.py` and `test_gemini.py` |
| Full backend suite | Existing routes and schema behavior remain green | 146 passed; two dependency deprecation warnings |
| Frontend tests, lint, build | New SSE metadata and history contract works | 26 passed; oxlint, ESLint, and production build passed after the missing Node `process` import was fixed |
| Live one-night question | Verified $120 Campus Lantern and $130 Valley Ridge, zero-room hotel excluded | Answer matched direct SQLite rows; two Gemini calls through backend |
| Live follow-up | Reuse same ZIP/date and persisted context | Campus Lantern identified as $10 cheaper |
| Live no-match and missing night | No invented hotel or availability | ZIP 16804 had no saved matches; October 15 had three candidates with missing nights and no verified availability |
| Live two-night question | Exclude checkout and total both actual nights | Campus Lantern $230, Valley Ridge $270; zero-room hotel excluded |
| Final live browser question | October 12 single-night results match direct SQLite rows | Nittany Budget $90, Campus Lantern $110, Valley Ridge $140; all had two simulated rooms |
| Refresh and backend restart | Saved history returns | Browser displayed the same conversation after each; `GET /api/chat/history` returned 200 |
| Failure state | Missing context is recorded without assistant success | Browser showed an error and Edit question; the draft returned for correction |
| Browser warnings/errors | None | Empty warning/error log |

The successful, follow-up, no-match, missing-night, and two-night questions
were **live Gemini** calls against an ignored synthetic preview database.
Provider and SQL-failure tests used labeled mocks. The preview database was
created for this turn at `backend/db/turn4-rag-preview.sqlite3`; the default
runtime database and course CSVs were not changed. Existing services on
8000/5173 were left alone. A task-owned backend on 8001 and Vite on 5174
served the browser pass and remain running for review at
`http://127.0.0.1:5174/`.

## Corrections and limits

- Initial backend route tests still targeted the retired raw-preview route;
  they were replaced with two-call and persistence tests. No dependency was
  added.
- The frontend lint check found `process` undefined in the new Vite proxy
  override. Importing Node's `process` module resolved it; lint and build
  passed on rerun.
- Browser review found that a failed response kept the streaming placeholder
  and repeated an incomplete question. The UI now says no answer was saved,
  and missing-context failures offer Edit question. The backend persists a
  safe error code so the state survives refresh.
- The parser accepts an explicit five-digit ZIP and one or two ISO or full
  month dates. It conservatively asks for clarification when context is
  missing or ambiguous. Broader natural-language date forms, live provider
  prices, booking, and a complete hotel inventory are outside this turn.
- The first live answers used prompt version 3; a refinement to version 4
  clarified no-match and missing-night wording and requested plain text.
  The version is recorded on each trace stage.

## Commands and evidence

Turn 4 changed `README.md`; `backend/app/main.py`, `routes.py`, and
`schemas.py`; `backend/controllers/chat_context.py`, `chat_history.py`,
`gemini.py`, and `rag_chat.py`; `backend/models/chat.py`;
`backend/tests/test_gemini.py` and `test_rag_chat.py`;
`frontend/src/api/chatStream.js`, `frontend/src/components/ChatPopup.vue`,
`frontend/tests/chatStream.test.js`, and `frontend/vite.config.js`;
`prompts/hotel-assistant.md`; and this checkpoint,
`docs/rag-context.md`, and `docs/assignment2-part2-plan.md`. All remain
uncommitted alongside earlier in-progress project changes.

Read `AGENTS.md`, `README.md`, the Turn 3 and revised Part 2 plans, prompt,
controllers, schemas, route, Vue component, and tests with `cat`, `sed`, and
`rg`; checked Git status and listeners with `git` and `lsof`. Ran the focused
backend and frontend commands during implementation, then the final AutoLoop
commands listed below. Used a project-owned Python script to create and inspect
the ignored synthetic preview database (schema 7, three saved hotels, three
ZIP links, six nights, no FK violations). Used automated browser control for
all live questions, refresh, history, and error checks. A read-only SQLite
query printed the first proposal, bindings, trace, checked rows, direct source
rows, and conversation ID without displaying credentials. A broad `git diff
--check` still reports the pre-existing trailing space in `report.md:5`; the
Turn 4 files pass a targeted check.

Final AutoLoop acceptance check: the complete backend suite, frontend tests,
both linters, production build, targeted diff whitespace check, and a fresh
automated browser question must pass. Commands and observed results:

- `backend/.venv/bin/python -m pytest backend/tests -q`: 146 passed, two
  dependency deprecation warnings.
- From `frontend/`, `npm test && npm exec -- oxlint . && npm exec -- eslint .
  && npm run build`: 26 passed, both linters passed, production build passed.
- `git diff --check -- AGENTS.md README.md backend/app backend/controllers
  backend/models backend/tests frontend/src frontend/tests
  frontend/vite.config.js prompts/hotel-assistant.md
  docs/assignment2-part2-stage4.md docs/rag-context.md`: passed. New files
  are untracked and therefore are not covered by this Git diff command.
- Automated browser on port 5174: October 12 question completed with three
  price-ordered hotels and no warning/error console entries. Direct read-only
  SQLite query returned the same 9000, 11000, and 14000 cent nightly rows and
  `PRAGMA foreign_key_check` returned no violations.

No correction cycle was needed after the final AutoLoop acceptance run. A
shell `curl` from the sandbox could not connect to the already listening
preview port, while `lsof` showed both preview listeners and the automated
browser completed the live request. Direct shell HTTP reachability was not
verified in that sandbox.
