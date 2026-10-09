# Assignment 2 Part 2 — clarification and ZIP-only lookup repair

Observed October 8, 2026. The user asked to resolve the screenshot where a
simple hotel question was rejected for lacking dates and labeled “Reply
interrupted.” Acceptance: a general saved-hotel list needs only a ZIP;
price/availability questions need dates; missing context is displayed and
restored as a clarification; both modes retain bounded checked two-call RAG.

## Changes and contracts

- Separate framework-free HotelListRequest, SavedHotelFact and HotelListResult.
  General hotel identity questions use postcode-only binds; dated prices/
  rooms/availability still use StayRequest with the three original binds.
- Both modes ask Gemini for SQL, validate and execute a bounded read-only
  SELECT, independently recheck ZIP membership, send the question and checked
  records to Gemini again, and validate its selection before displaying
  database-rendered facts. ZIP-only answers never claim dates, rates or rooms.
- The same read-only SQLite connection, table/function authorizer, time budget,
  50-candidate cap and ten-record second request apply to both modes.
- Prompt version 6 records the distinction. History can restore ZIP-only
  context; it cannot invent dates from a prior identity list. The trace CLI
  handles both kinds of stored request.
- Missing-context replies display their question directly with “More
  information needed,” a neutral status banner and Edit question. They do not
  show “No answer was saved” or “Reply interrupted.” Other failures retain a
  failure state. New and restored messages use the same classification helper.

## Expected versus observed

Normal application/live Gemini over the synthetic recording SQLite database:

| Question/action | Expected | Observed |
| --- | --- | --- |
| 17042 has what hotels | ZIP-only lookup, no fabricated date or hotel | Live two-call result saved count 0; no hotel saved; suggested ZIP search/Add to Local |
| 16803 has what hotels | List checked identities regardless of nightly eligibility | Live two-call result included Campus Lantern, Nittany Budget and Valley Ridge; no price/availability claims |
| Which saved hotels near ZIP 16803 are available? | Clarify dates before any model call | missing_context stage; readable date question, More information needed, Edit control |
| Reload/reopen after that clarification | Restore correct message/state | Zero Reply interrupted labels and zero No answer was saved placeholders; status banner rgb(247,247,247) |
| Click Edit question | Restore exact original draft | Exact availability question restored |
| Add on 2026-10-11 and send | Existing dated query remains correct | Live Campus $120 and Valley $130; Budget excluded for zero rooms; error cleared |
| Browser logs | No application warnings/errors | Empty |

Stored prompt-6 turns:
- Empty ZIP: ed57f32e-8222-4868-b82f-9cf452513b9c.
- Populated ZIP identities: a1584810-ec40-4b22-8205-637472ccba96.
- Clarification: 95209d1b-978f-4914-9b56-0c5fdbed4559.
- Dated success: da2fb719-ed4b-4773-bcce-7589384805a2.

The result stages retain proposed SQL, checked records, second_model_answer
and answer_validation. The missing-context turn has an error and user
message, not a fabricated successful assistant message. Read-only inspection
found 3 saved hotels/3 ZIP links/6 nights and no foreign-key violations.

## AutoLoop and checks

Existing focused backend suite: 40 passed. New identity regression suite:
10 passed on its first run. Full backend: **174 passed** with two existing
dependency deprecation warnings. Frontend: **28 passed**, read-only Oxlint,
ESLint and production build passed (32 modules). No correction cycle for a
failing source test, no package/dependency change and no schema migration.
The CSS clarification selector was made more specific before browser testing
so the later generic error style could not override its neutral appearance.

Backend tests cover undated questions, missing dates for prices/rooms,
leading-zero ZIP, ambiguous ZIP, same-context follow-up, incomplete/zero-room
hotels in identity lists, independent ZIP verification, blocked writes,
multiple statements, unapproved tables/functions, changed binds, unsupported
model fields/IDs/reasons, second-call metadata and restore/trace inspection.
Frontend tests cover new/restored clarification states and preserving text
for actual interrupted/provider failures. Browser checks establish the
reachable integrated behavior; mocked tests are not live provider evidence.

## Files changed by this repair

README.md; backend/controllers/chat_context.py, chat_history.py, gemini.py,
grounded_answer.py, rag_chat.py, retrieval.py; backend/models/retrieval.py;
backend/inspect_rag_demo.py; backend/tests/browser_scenarios.py,
test_rag_chat.py; new backend/tests/test_hotel_list.py;
frontend/src/components/ChatPopup.vue, frontend/src/assets/main.css;
new frontend/src/chat/replyFailure.js and frontend/tests/replyFailure.test.js;
prompts/hotel-assistant.md; docs/assignment2-part2-demo.md; this record;
docs/test-screenshots/chat-zip-only.png and chat-clarification-fixed.png.

Concurrent report edits and the student's untracked A2.2 movie were preserved;
this repair did not edit or assess that video. The Git HEAD moved through
separate concurrent work to ad818056 while the repair was in progress.
The repair is saved as a separate local application checkpoint; its exact
SHA is recorded in the updated report and current handoff. No push was
performed by this repair; external publication is still awaiting the earlier
explicit-destination approval. Concurrent report edits and the movie are not
included in the source checkpoint.

## Commands and service actions

Reads:
- git status --short; cat frontend/src/api/chatStream.js;
  cat frontend/tests/chatStream.test.js; cat frontend/package.json;
  sed -n '1,230p' frontend/src/components/ChatPopup.vue
- cat backend/models/retrieval.py backend/controllers/retrieval.py backend/controllers/chat_history.py
- cat backend/controllers/grounded_answer.py backend/controllers/gemini.py backend/controllers/rag_chat.py
- cat backend/tests/test_retrieval.py backend/tests/test_gemini.py; cat AGENTS.md
- rg -n '"5"|three named binds|Version: 5' backend/tests README.md;
  sed -n '1850,1910p' frontend/src/assets/main.css
- cat backend/prepare_rag_demo.py;
  sed -n '129,176p' backend/controllers/gemini.py;
  sed -n '1,72p' backend/tests/test_rag_chat.py;
  sed -n '1910,1950p' frontend/src/assets/main.css

Checks:
```bash
backend/.venv/bin/python -m pytest backend/tests/test_retrieval.py backend/tests/test_rag_chat.py backend/tests/test_gemini.py backend/tests/test_grounded_answer.py -q
backend/.venv/bin/python -m pytest backend/tests/test_hotel_list.py -q
backend/.venv/bin/python -m pytest backend/tests -q
git diff --check && git status --short
backend/.venv/bin/python -m backend.inspect_rag_demo backend/db/part2-recording.sqlite3
git diff --check && git diff --stat && git diff --name-only -- data backend/controllers/geocoding.py backend/controllers/places.py frontend/src/components/NearbyHotelsMap.vue backend/requirements.txt frontend/package.json frontend/package-lock.json && git log -1 --format='%H %s' && lsof -nP -iTCP:8001 -iTCP:5174 -sTCP:LISTEN
```

From frontend/:
```bash
npm test && npm exec -- oxlint . && npm exec -- eslint . && npm run build
```

A project-Python heredoc opened part2-recording.sqlite3 with mode=ro,
selected the latest four prompt-version-6 result/error stages joined to
their user messages, parsed detail_json, counted saved hotel/ZIP/night rows,
and ran PRAGMA foreign_key_check. Its observed values are recorded above.

Task-owned backend session 88606 (PID 94017) received Ctrl+C, then was
restarted with:
```bash
backend/.venv/bin/python -c 'from pathlib import Path; import uvicorn; from backend.app.main import create_app; uvicorn.run(create_app(Path("backend/db/part2-recording.sqlite3")), host="127.0.0.1", port=8001)'
```
New backend session 75511/PID 95962 serves port 8001. Existing task-owned Vite
PID 92029/session 70569 remains on 5174. Both are deliberately left running
because the student requested them for recording. No unrelated process was
stopped; the default runtime DB and course CSVs were untouched.
The temporary browser verification tab was closed.

## Limits

Checkpoint commands:
git add with explicit paths for the repair files listed above;
git diff --cached --check && git diff --cached --stat;
git commit -m "Support ZIP-only hotel chat and clarify missing dates";
git rev-parse HEAD; sed -n '1,24p' report.md; sed -n '1,28p' handoffs/current.md.
Application checkpoint: 2eae4985184dce0c8924e0791b94fa3fed5a23de.
Documentation checkpoint: 0c64799. It preserves the concurrently edited
student report as its current snapshot, updates the assessed source pointer,
adds a version-6 verification paragraph and refreshes the handoff. Concurrent
student report prose was not rewritten by this repair.
Documentation commands: cat handoffs/current.md;
rg -n 'version|prompt' report.md; git diff --check && git diff --stat &&
git status --short && git diff 2eae498 HEAD -- backend frontend prompts data;
git add -- report.md handoffs/current.md; git diff --cached --check &&
git diff --cached --stat; git commit -m "Update report and handoff for clarified hotel chat";
git status --short && git log -2 --oneline && git diff 2eae498 HEAD -- backend frontend prompts data.

This is saved-local hotel identity lookup, not automatic discovery of every
hotel near a ZIP. Dates remain required for simulated prices and availability.
Not every natural-language question or provider failure was tested. The
recording file's contents and instructor access were not checked here.
