# Part 2 Turn 2 — raw Gemini streaming checkpoint

Observed October 6, 2026 on `rag_integration`. This stage streams a live
Gemini response through FastAPI to the popup. It sends no SQLite records,
proposes no SQL, and makes no RAG claim.

## Provider and dependency check

- The project-root `.env` contains a nonblank `GEMINI_API_KEY`. The key was
  read only by the backend and never printed. A key-backed model metadata
  request returned HTTP 200 for `models/gemini-3.5-flash-lite`.
- The selected free-tier AI Studio project showed 15 requests/minute,
  250,000 input tokens/minute, and 500 requests/day for Gemini 3.5 Flash Lite
  on October 6. Limits vary by project and may change; see
  [Google's rate-limit guidance](https://ai.google.dev/gemini-api/docs/rate-limits).
- Google's [model page](https://ai.google.dev/gemini-api/docs/models/gemini-3.5-flash-lite)
  lists the selected model, and its [streaming API](https://ai.google.dev/api/generate-content)
  documents `streamGenerateContent`. The model metadata lists
  `generateContent` but does not enumerate the streaming method; the live
  streaming request below established that the endpoint works with this key.
- Project-owned `httpx==0.28.1` already supports the required async HTTP
  stream. No dependency was installed or changed.

## Expected versus observed

| Check | Expected | Observed |
| --- | --- | --- |
| Focused backend tests | Provider parsing, safe failures, JSON/SSE contract, validation | 10 passed initially; the added config test passed in the full suite |
| Full backend suite | Existing API and new chat route pass | 130 passed; two existing library deprecation warnings |
| Frontend tests, lint, build | Stream parsing/failure and existing UI pass | 24 tests passed; Oxlint, ESLint, and Vite build passed |
| First live browser question | Model states that no saved-hotel data is connected | “Saved-hotel retrieval is not connected yet”; no price was invented |
| Live follow-up | Prior conversation sent; model continues with preview limitation | “Room availability cannot be looked up yet”; no rooms were invented |
| Local endpoint timing | Multiple `delta` events precede one `done` | HTTP 200; 6 deltas, 1 done, 0 errors; first delta at 0.56 s, done at 0.91 s |
| Browser errors | None from chat app | Warning/error log empty |
| Mocked provider failure | No credential or raw provider text reaches UI | 429, 403, 500 sanitized; partial failure yields `error` without `done` |

The two browser answers and the timed local request were **live Gemini
calls**. Provider failure and interrupted-stream checks used labeled mocks;
they did not consume quota. The frontend posts to `/api/chat/stream` through
the existing Vite proxy and contains no key or direct Google request. Chat
history is bounded to six turns in both Vue and FastAPI; it is retained only
until page refresh. The Stage 1 deterministic stub and its tests were removed
after this connection replaced them.

A broad `git diff --check` reported trailing whitespace in the pre-existing
`report.md` change at line 5. Turn 2's tracked files passed a targeted
`git diff --check`; the report file was left alone as unrelated work.

The next checkpoint is safe, read-only SQL retrieval on a synthetic temporary
database. This stage does not verify SQL generation, records, rates, nightly
coverage, or durable conversation history.

## Commands and live tools used

- Read `AGENTS.md`, `README.md`, the plan, prompt, route, schema, config,
  frontend API/component, and relevant tests with `cat`, `sed`, and `rg`.
  Inspected the branch, working tree, file changes, and port listeners with
  `git status --short`, `git branch --show-current`, `git diff --check`, and
  `lsof -nP -iTCP:8000 -iTCP:5173 -sTCP:LISTEN`.
- Used `backend/.venv/bin/python -c` for a key-backed model metadata check,
  a safe print of advertised methods, an installed-plugin probe, and a timed
  local SSE request. The first metadata attempt failed because sandbox DNS
  was unavailable; the read-only retry with network access returned HTTP
  200. `pytest_asyncio` was absent, so tests use standard-library
  `asyncio.run` rather than adding a dependency.
- Ran `backend/.venv/bin/python -m pytest backend/tests/test_gemini.py
  backend/tests/test_config.py -q`, then
  `backend/.venv/bin/python -m pytest backend/tests -q` twice around the
  final documentation and config-test cleanup.
- Ran `npm test`, `npm exec -- oxlint .`, `npm exec -- eslint .`, and
  `npm run build` from `frontend/`; reran these after removing the old stub.
  A targeted `git diff --check` and `rg` whitespace check covered Turn 2
  files after the unrelated broad-check finding.
- Stopped only the task-owned backend process and relaunched it with
  `backend/.venv/bin/python -c` using the same ignored temporary database.
  Used the in-app browser for the AI Studio rate-limit page, two live chat
  questions, the final screenshot, and the browser warning/error check.
