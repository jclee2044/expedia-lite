# Part 2 Turn 5 — integrated proof and submission checkpoint

Observed October 6, 2026 on `rag_integration`. This checkpoint covers the
integrated RAG proof and the report draft. The verified site was the isolated
frontend at `http://127.0.0.1:5174/`, proxied to a task-owned backend on
8001. The preexisting 5173/8000 pair was left alone; its backend still lacks
the Turn 4 history route until its owner restarts it. All hotel names, rates,
room counts, questions, and database records used below are synthetic.

## Expected versus observed

| Check | Expected | Observed |
| --- | --- | --- |
| First live two-call trace | User → model SQL → safe execution → checked rows → streamed answer | The first saved turn contained UTC-stamped user/assistant messages and ordered `proposal`, `execution`, `result` stages; direct two-JOIN rows matched the answer |
| Changed ZIP | No invented hotel | ZIP 16804/October 12: zero ZIP associations, zero candidates/matches, live answer said no hotel was saved |
| Changed date | Missing nights are unknown availability | ZIP 16803/October 15: three ZIP candidates, zero night rows, three incomplete IDs, live answer said availability could not be verified |
| Rejected write | Temporary database remains unchanged | Model-style `UPDATE` rejected before execution; `Proof Hotel` unchanged; no foreign-key violations |
| Refresh and restart | Saved conversation survives | Chat history restored after both a browser reload and restart of the task-owned backend on 8001 |
| Reproducible fixture | New, ignored database; no overwrite | `backend.prepare_rag_demo` created schema 7 with 3 saved hotels, 3 ZIP links, 6 nights; repeat preparation refused the existing path; checked retrieval matched the JSON expectations |
| Clean live demo | Same two-call result using recreated fixture | Prompt version 4 trace and answer showed Campus Lantern $120 and Valley Ridge $130; Budget's zero-room night was excluded |
| Browser errors | None from the application | Warning/error console entries: none |
| Final AutoLoop | Backend/frontend checks, diff checks, browser proof | 146 backend and 26 frontend tests passed; Oxlint, ESLint, build, whitespace, ignore, credential-pattern, and browser checks passed |

## Reproducible data and evidence

The [fixture](part2-rag-fixture.json) is source-controlled and contains only
invented hotels. The preparation script refuses an existing output and
restricts its target to `backend/db/*.sqlite3`; it created the ignored
`backend/db/part2-submission-demo.sqlite3` without changing the default
runtime database. The [trace](rag-context.md) records the first and clean
conversation IDs, proposed SQL, exact binds, checked rows, changed-input
results, and the temporary rejected-write proof.

Automated browser screenshots are [clean question](test-screenshots/part2-rag-clean-question.jpg),
[clean answer](test-screenshots/part2-rag-clean-demo.jpg),
[changed ZIP](test-screenshots/part2-rag-no-match.jpg), and
[missing night](test-screenshots/part2-rag-missing-night.jpg). Earlier
price, question, and post-restart frames are also in `docs/test-screenshots/`.
These images show the local application and synthetic values; they do not
show API credentials.

## Files and commands

Turn 5 changed `README.md`, `report.md`, and `docs/rag-context.md`; added
`backend/prepare_rag_demo.py`, `docs/part2-rag-fixture.json`, this
checkpoint, and eight JPEG browser evidence files named `part2-rag-*` under
`docs/test-screenshots/`. Earlier Turn 0–4 work remains uncommitted until
the assessed checkpoint is finalized.

Read `AGENTS.md`, `README.md`, the Part 2 plan and revised brief, instructor
notes, preflight/stage checkpoints, report, retrieval controller/tests, and
Git state with `cat`, `sed`, `rg`, `git status`, `git branch`, `git rev-parse`,
`git log`, and `git diff`. Checked listeners with `lsof`. Reviewed official
W3C, MDN, Google Gemini, and SQLite documentation through web reads.

Ran project-owned Python read-only SQLite inspections of the proposal,
messages, retrieval stages, direct two-JOIN rows, changed ZIP/date counts,
and foreign keys; a temporary-database rejected-`UPDATE` script; the fixture
preparation module; a second-preparation refusal check; and checked
retrieval over the fresh fixture. Used automated browser control to send the
changed ZIP/date questions, inspect the live answers and error log, reload,
restart the task-owned backend, confirm history, and capture JPEG evidence.
Restarted only backend port 8001 through its task-owned terminal session;
Vite 5174 and the preexisting 5173/8000 services were not stopped.

Final AutoLoop acceptance check: all backend tests, frontend tests, both
read-only linters, production build, whitespace and credential checks, and
the clean-fixture browser answer must pass. Commands and results:

- `backend/.venv/bin/python -m pytest backend/tests -q`: 146 passed, two
  dependency deprecation warnings.
- From `frontend/`, `npm test && npm exec -- oxlint . && npm exec -- eslint .
  && npm run build`: 26 passed; both linters and build passed.
- `git diff --check` and a trailing-blank `rg` scan of new text files: passed.
- `git check-ignore -v .env backend/.venv frontend/node_modules frontend/dist
  backend/db/part2-submission-demo.sqlite3`: all five paths are ignored.
- Credential-pattern `rg -l` over source, docs, prompt, README, and report:
  no matching literal key-like strings.
- Automated browser on the clean generated database: live two-call answer
  matched the direct rows, with no warning/error console entries. Earlier
  changed ZIP/date and post-restart browser checks also passed.
- Read-only default runtime database inspection: schema 6, one saved hotel,
  one ZIP link, five nights, no foreign-key violations, matching the Turn 0
  preflight counts. Local Markdown link check found no missing file targets.

No source correction cycle was needed in the final AutoLoop. The only
implementation-time patch retry was a README insertion whose first context
did not match; the corrected patch applied. No dependency changed.

## Submission limits

`report.md` now covers Part 2 research, early mockup, screenshots, traced
expected-versus-observed checks, fixture reproduction, AI disclosure, and
limits. A Part 2 screen-recorded demo and instructor-accessible link are not
yet available. The assessed Part 2 commit and remote push have not been
created; the report marks those fields TODO rather than using the Part 1
commit. Student review of the live/mock labels, fixture, screenshots, and
final diff is still needed before submission. The saved hotel fixture is not
live Geoapify pricing, availability, or a complete area inventory.
