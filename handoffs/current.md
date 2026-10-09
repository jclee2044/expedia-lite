# Expedia Lite current handoff

Final submission snapshot. Read AGENTS.md and handoffs/create-handoff.md,
then verify Git/files/services before editing. The latest human request
explicitly authorizes final report accuracy, handoff refresh, commit and push
to the existing Expedia Lite repository.

## Objective and current state

Assignment 2.2 is implemented: saved-local foundation plus question → Gemini
SQL proposal → validated read-only SQLite retrieval → second Gemini request
with the original question/checked records → validated, record-rendered answer.
Provider: gemini-3.5-flash-lite. Prompt version 6. Codex disclosure: GPT-6.1 Sol,
confirmed by the student.

Simple saved-hotel identity questions need a ZIP only. Price/availability
questions need dates. Missing context shows More information needed and Edit
question, also after reload. Preserve off-white #f7f7f7 assistant bubbles,
320ms upward opening / 200ms closing animation, reduced-motion support,
keyboard focus, drafts, saved data, course CSVs and frozen Part 1 behavior.

The report now has the assessed application SHA, portable pinned source/image
links, latest verification, linked AI prompt evidence, research/early mockup,
actual SQL/records/answer and live-versus-mock labels. The student's concise
report prose and historical d8edae8 baseline reference were preserved.
The A2.2 recording exists (42,665,203 bytes) and is included in the final
documentation commit, consistent with the repository's older assignment videos.
Drive's sharing control says anyone with the link can access, no sign-in required.
Its player loaded a 1:20 recording and a SQL-results frame around 0:33.
The full clip/audio was not exhaustively reviewed; no signed-out session was
created. The recording predates the latest ZIP-only/clarification follow-up;
those behaviors have their own live trace and screenshots in stage7.

Remaining student action: final report/video review and upload/submission.
No Canvas submission has been performed or claimed.

## Architecture and file map

Vue View → FastAPI routes → framework-free Controllers → Models/SQLite.

- backend/app/: HTTP/SSE routes and schemas.
- backend/models/schema.py: schema 7 and additive migrations.
- backend/models/retrieval.py: dated StayRequest/RetrievalResult and separate
  HotelListRequest/HotelListResult; metadata does not assert room availability.
- backend/controllers/saved_hotels.py: transactional Add/duplicate/Remove.
- backend/controllers/retrieval.py: exact trusted binds; one bounded SELECT;
  mode=ro/query_only/authorizer/time budget/50-candidate cap; independent ZIP,
  nightly coverage/rooms/totals and saved count. Metadata reuses read-only guards.
- backend/controllers/gemini.py, grounded_answer.py and rag_chat.py:
  two model calls; structured selection; normal completion required;
  buffer before validated text; checked facts rendered rather than model prose.
- chat_context.py/chat_history.py: context, messages and versioned trace.
- frontend/src/components/ChatPopup.vue and frontend/src/chat/replyFailure.js:
  presentation and correct new/restored clarification states.
- prompts/hotel-assistant.md: current version 6.
- backend/prepare_rag_demo.py + docs/part2-rag-fixture.json: new synthetic DBs,
  refuses overwrite. backend/inspect_rag_demo.py reads both request types.
- docs/assignment2-part2-stage6.md and stage7.md: historical integrated audit
  and latest identity/clarification checks. docs/chat-animation-verification.md:
  animation checks and limits. docs/rag-context.md: current/historical traces.
- docs/assignment2-part2-final-verification.md: final report/publish audit.
- report.md, Expedia Lite A2.2 Demo.mov, and screenshot references: submission assets.

## Git evidence

Root: /Users/jlee/Desktop/psu4/ist402/a1_expedia_lite.
Branch: rag_integration, tracking origin/rag_integration.
Assessed tested application: 2eae4985184dce0c8924e0791b94fa3fed5a23de.
Parent HEAD before the final documentation/media commit: 36060f5.
The documentation commit containing this file follows those checkpoints.
Use git log -1 and git status --short for its self-referential SHA/current state.
git diff 2eae498 HEAD -- backend frontend prompts data must be empty.
The report points to application source; the branch also contains final media/docs.

Before publishing, git ls-remote verified origin/rag_integration at bf7e1b8;
local branch was ahead nine commits. The final push is now explicitly authorized
by the latest user request. Confirm its actual outcome in the final audit and
with git ls-remote --heads origin rag_integration; do not infer remote state
solely from this pre-commit snapshot. No main merge, PR or branch switch was requested.
No secrets, runtime databases, venv, node_modules, caches or build output are staged.
The authorized documentation/media push succeeded at
84c6230997cad585fac9b1547d0ec589d87224b7: local/remote SHAs matched, checkout
was clean and no application code differed from 2eae498. Anonymous HEAD
checks returned 200 for the assessed source, report, pinned images and movie.
This documentation-only follow-up records those observed outcomes; verify
its own final SHA/remote with git log and git ls-remote on resumption.
Expected final checkout: clean after that follow-up.
A later user edit can change that; always recheck.

## Observed verification

Latest source repair checks:
- backend/.venv/bin/python -m pytest backend/tests -q: 174 passed,
  two pre-existing dependency deprecation warnings.
- frontend/: npm test: 28 passed; npm exec -- oxlint .;
  npm exec -- eslint .; npm run build: passed (32 modules).
- New identity suite: 10 passed; existing focused RAG suite: 40 passed.
- Automated live Gemini/browser: ZIP 17042 no saved rows; ZIP 16803 all three
  names without dates; missing-date clarification survives reload; Edit
  restores exact draft; October 11 returns Campus $120 / Valley $130 and
  excludes zero-room Budget. Browser warning/error logs empty.
- Read-only recording DB: 3 saved hotels, 3 ZIP links, 6 nights, no FK violations.
- Earlier stage6 evidence: two-night $230/$270, budget no-match, missing-night,
  absent ZIP, CRUD/duplicate/persistence, map/list and keyboard, Harbor/blank/
  no-results, mocked unsafe SQL/quota/bad-answer failures.
- Final audit: no application-source differences from assessed SHA; report
  source/assets exist at their pinned refs; no machine-local image paths;
  source/verification/model fields consistent. Only documentation/media changed.
Full tests were not needlessly rerun for these documentation edits.
The final audit logs exact reads/checks/staging/commit/push and any limitations.

## Active services

Left running at the student's request for recording:
- Backend session 75511 / PID 95962, 127.0.0.1:8001,
  create_app(Path("backend/db/part2-recording.sqlite3")) via uvicorn.
- Frontend session 70569 / PID 92029, 127.0.0.1:5174,
  EXPEDIA_API_TARGET=http://127.0.0.1:8001 npm run dev
  -- --host 127.0.0.1 --port 5174 --strictPort from frontend/.
Reconfirm process ownership before managing services. No unrelated process
was stopped. The default runtime database was never reset for the demo.
Temporary verification tabs closed; DB Browser was opened on the recording DB
and left with the read-only two-JOIN nightly comparison displayed.

## Limits and next action

Verified: tested implementation, current demo data, live/mocked distinctions,
latest UI behavior, submission source/assets and Drive sharing label.
Not established: exhaustive language/provider coverage, full clip/audio review,
signed-out playback, reduced-motion emulation, full browser-process restart,
or Canvas submission. Model preferences remain within the bounded contract;
rates/rooms are simulated and no booking is made.

Read the final audit and report. Verify the final push/cleanliness, review the
recording, and upload report.md with its accessible video/source links. If any
new code changes are requested, test the relevant behavior and update the
assessed source pointer rather than pointing graders to an older baseline.
