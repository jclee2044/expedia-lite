# Assignment 2 Part 2 — build plan and checkpoints

Read with the [revised brief](assignment2-part2-revised.md) and the
[supplied chatbot tutorial](assignment2-part2-instructor-chatbot-notes.txt).
The work is on `rag_integration`. Turns 0–5 are complete: local storage,
popup, provider integration, guarded SQL, two-call retrieval, and evidence.
The [October 8 readiness audit](assignment2-part2-stage6.md) repaired two
grounding defects, reran regression and live/browser checks, and updated
the recording and handoff instructions. Prompt version 5 validates the
second model's structured recommendation and renders facts from checked rows.
The report draft is updated; the student must record and link the Part 2
video, review the report, and submit it.

The baseline and turn table below are historical planning records, not a
description of today's unfinished implementation.

## Repository baseline observed October 6, 2026

- The branch `rag_integration` was created from `assignment2_part2_in_class`
  at HEAD `d8edae8`, carrying uncommitted local-storage work. Preserve that
  work and inspect its diff
  before editing overlapping files. No RAG endpoint, prompt, or chat UI is
  present in the inspected source.
- `backend/models/schema.py` defines schema version 6 and the approved
  retrieval tables: `saved_hotels` (provider ID, name, address, coordinates),
  `saved_hotel_zips` (hotel ID, ZIP and saved center), and
  `demo_hotel_nights` (hotel ID, date, rate in cents, rooms available).
  The ZIP and night tables join to `saved_hotels` by `hotel_id`. Assignment 1
  `hotels` and `trips` are separate and must not be confused with provider
  saved hotels.
- `backend/controllers/saved_hotels.py` saves hotel, ZIP association, and
  October 10–14 demo nights transactionally, and deletes those rows together.
  `backend/app/routes.py` has GET/POST/DELETE `/api/saved-hotels`; Vue's
  `frontend/src/api/zipSearch.js` prefers saved ZIP results and calls the
  provider only after an empty successful local lookup. The nearby panel
  labels rates and room counts simulated classroom data.
- The ignored runtime SQLite database was inspected **read-only**: schema 6;
  1 saved hotel, 1 ZIP association (16802), 5 nights (October 10–14), no
  foreign-key violations. It has no saved 16803 hotel, so the tutorial's
  16803/October 11/three-cheapest example needs labeled synthetic fixtures
  or a different truthful live question. The runtime database also contains
  additional prior demo account and booking records; preserve it.
- Existing environment: Python 3.12 project venv, FastAPI, `httpx`, pytest,
  `sqlite3`, and `python-dotenv` already imported by `backend/config.py`;
  Vue, Vite, Leaflet, and project-owned npm dependencies. No new SDK or
  database package is required by this plan. If the chosen provider's API
  cannot be used reliably with existing `httpx`, propose the exact minimal
  package and wait for approval before installation.
- Current checks: `backend/.venv/bin/python -m pytest backend/tests -q`
  passed **123** tests with two library deprecation warnings; `npm test`
  passed **21**; read-only `npm exec -- oxlint .` and
  `npm exec -- eslint .` passed; `npm run build` passed. These checks do not
  establish live provider, browser, or restart behavior.

## Conditions to verify before implementation

1. **Preservation gate:** The existing automated checks stay green; the
   Assignment 1 CSVs and frozen Part 1 routes remain unchanged. Compare
   relevant Git diff and API response contracts before touching them.
2. **Storage gate:** On a labeled temporary database or approved demo data,
   prove save, duplicate save, remove, ZIP association, edited nightly values,
   and persistence after a backend restart. Check the browser's local-first
   lookup and list/map selection. Do not modify or reset the existing runtime
   database merely to create a demo fixture.
3. **Data gate:** Choose a reproducible successful question whose ZIP and
   dates actually have saved hotel and nightly records. Record exact fixture
   IDs and expected rows. Also prepare no-match, missing-night, zero-room,
   and two-night cases. Keep names and traveler data synthetic.
4. **Provider gate:** Gemini API model `gemini-3.5-flash-lite` is selected.
   A nonblank `GEMINI_API_KEY` was found in the ignored project-root `.env`
   without displaying its value. Check the exact free-tier model
   available to the student's project and its account-specific quota in
   Google AI Studio before the first live call (verified in Turn 2). Google's
   [streaming API](https://ai.google.dev/api/generate-content) supports
   `streamGenerateContent`; its [rate-limit guidance](https://ai.google.dev/gemini-api/docs/rate-limits)
   says active limits vary by account and are viewed in AI Studio. Verify
   backend-only configuration without printing a key. The `.env` file is
   already ignored; never commit or screenshot it.
5. **Scope gate:** Agree on the chat stream and evidence expectations. The
   supplied tutorial asks for persisted conversation and retrieval trace;
   plan for that additive schema migration rather than silently omitting it.

The chat is a bottom-right popup with a border using the existing green
palette. It must remain usable at narrow widths, support keyboard open/close
and send, and show a scrollable conversation. Keep messages while the popup
closes and reopens in the same page session. Streaming must append chunks to
the current assistant bubble; scrolling should follow new text when the user
is near the bottom without pulling them away when reading earlier messages.
Stage 1 used a **clearly labeled stub** and did not call Gemini. Stage 2
streams **raw Gemini** through FastAPI without hotel retrieval. Turn 3 adds
checked, read-only SQL retrieval and the additive history schema. Turn 4
connects the two model calls and persists history across refresh/restart.
The [staged system prompt](../prompts/hotel-assistant.md) is loaded by the
two-call grounded chat; each persisted trace stage records its prompt version.

## Turn-by-turn execution

| Turn | Small deliverable | Validation and human checkpoint |
| --- | --- | --- |
| 0 — Preflight and mockup | Review the uncommitted storage diff and manually verify save, local-first lookup, and restart persistence. Research the popup pattern and draw the Part 2 early mockup showing narrow layout, streaming, empty, loading, and failure states. Pick truthful synthetic ZIP/date fixtures. | Show expected versus observed foundation behavior, screenshot/mockup, and fixture rows. Keep existing Part 1 checks green. |
| 1 — Working stub popup | Build a bottom-right Vue popup with a green border, accessible open/close controls, message input, send action, scrollable history, and a deterministic local stub that emits visible chunks. Preserve the conversation when the popup closes and reopens in the page session. Keep frontend request code separate from presentation. | Run frontend tests, read-only lint, and build; inspect desktop and narrow layouts, keyboard use, chunk updates, scroll behavior, and a clear **stub** label. Review the working UI before calling Gemini. |
| 2 — Raw Gemini stream | Check the student's free-tier model and quota in AI Studio. Define a documented POST request and streamed JSON event contract (`delta`, `done`, `error`) over a FastAPI `text/event-stream` response. Use the existing backend HTTP dependency if adequate; load a backend-only Gemini key from ignored `.env` and call Google's streaming endpoint. Send bounded prior chat context but no saved-hotel data. Stream through FastAPI to the same popup; handle partial responses, disconnects, timeouts, and 429 errors. | Mock stream parsing and failures in backend/frontend tests. Then show one labeled **live raw-model** exchange and follow-up, with incremental text and no key in browser traffic. Explain any exact dependency change and obtain approval before installing it. |
| 3 — Safe retrieval | Review the draft prompt against the actual schema. Add an additive migration for conversation and retrieval-stage records. Implement a controller that accepts proposed parameterized `SELECT` SQL, validates shape and binds, uses a separate read-only SQLite connection and an authorizer for the three saved-hotel tables, and enforces row and execution limits. Independently verify complete-night coverage, positive rooms, and total cents; checkout is excluded. | Temporary fixtures prove approved lookup, blocked write/multiple statement/table/function, unchanged counts, limits, missing nights, zero rooms, and correct two-night totals. Inspect proposed SQL and rows before live RAG. |
| 4 — Two-call RAG stream | Change the backend orchestration to question → Gemini SQL proposal → checked SQLite rows → second Gemini request containing the question and bounded rows → **streamed grounded answer**. Persist user, proposal, execution/result, assistant, and error stages with timestamps, conversation ID, and prompt version. Restore history after refresh/restart. Preserve the popup's streaming and scroll behavior. | Mock both model calls and failure states. Run one labeled live RAG question; compare returned facts with SQLite. Confirm follow-up context, no-match/insufficient-data answers, and durable history. Review trace and answer before reporting success. |
| 5 — Integrated proof and submission | Run regression and browser checks. Trace success through SQL and both joins; repeat with changed ZIP/date and no match. Prove rejected SQL against a temporary database. Record research, early mockup, screenshots/demo, expected-versus-observed checks, prompt excerpts, AI disclosure, assessed commit, and limitations in `report.md` and `docs/rag-context.md`. | Student reviews live versus mock labels, credential redaction, database comparison, demo link, and final diff before submission. |

## Design constraints for later turns

- The model proposes SQL; it never gets a database handle. Validation must
  reject anything beyond the allowed read-only shape before SQLite execution.
  SQLite read-only mode, authorizer, parameter binding, time budget, and row
  cap provide defense in depth; a leading `SELECT` check alone is inadequate.
- A generated query may narrow candidates, but backend logic must independently
  verify requested nightly coverage, positive rooms for **each** night, and
  sum rates in integer cents. No row for a night means insufficient data, not
  availability. Answer prompts must receive only the checked, bounded facts.
- Conversation/history writes are application operations, separate from the
  read-only model-proposed retrieval. Save only synthetic course questions and
  safe trace data. Errors receive a trace stage and a useful UI response;
  never manufacture a successful assistant response after failure.
- Keep one provider, one endpoint, and a small contract. Add no vector DB,
  agent framework, booking actions, or frontend credentials. Use mock calls
  for failure and SQL safety; identify real model calls explicitly.

## Historical decisions and remaining submission work

- **Selected model:** `gemini-3.5-flash-lite` for both the SQL-proposal and
  grounded-answer calls. Google's model documentation identifies this as a
  stable text-output model with structured-output support. On October 6, 2026,
  the selected free-tier AI Studio project showed 15 requests/minute,
  250,000 input tokens/minute, and 500 requests/day for this model; Google's
  pricing page listed free input and output tokens. Recheck model access and
  current limits in the dedicated Assignment 2 project before a live call.
- **Implemented:** The popup reloads persisted messages and errors after page
  reload and backend restart. No additional history interface was required by
  the supplied brief.
- **Turn 4 preview fixture:** Synthetic saved hotels and nights at ZIP 16803
  on October 11–12, 2026 are recorded in
  [the live trace](rag-context.md). The fixed submission fixture and October 8
  checks are reproducible. **TODO:** Student review of `report.md`, Part 2
  recording, accessible video link, and submission.
