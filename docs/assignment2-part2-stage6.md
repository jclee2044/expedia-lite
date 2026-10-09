# Assignment 2 Part 2 — October 8 readiness audit

## Acceptance and outcome

The user asked for a critical readiness review and then authorized resolving
the identified gaps step by step. Acceptance: the revised two-call endpoint
must produce checked factual answers, distinguish filtered no-match from
absence of saved hotels, preserve Part 1/local storage, pass regression and
reachable browser checks, and have reproducible report/demo/handoff evidence.

The application checks passed after the repairs. The report draft and demo
guide are updated. The student must still record the Part 2 video, verify its
sharing, add the link, review the report and submit it. The recording is not
presented as complete. No dependency, authentication, vector database or
deployment feature was added.

## Defects found and corrections

1. A live two-night answer had correct $230/$270 totals but attributed
   Valley's $140 rate to October 14 instead of its actual October 12 row.
   Merely instructing the model to be grounded did not prevent invented prose.
   Prompt version 5 asks the second model for selected IDs and a supported
   reason in structured JSON. The backend validates those values and renders
   names, dates, cents, rooms and totals from the checked records.
2. A controlled valid SQL filter of nightly rates <=5000 returned zero
   candidate IDs, despite three saved hotels at ZIP 16803. A live second-model
   request interpreted the old candidate count as no hotels saved. Retrieval
   now independently counts saved ZIP associations in the same read-only
   snapshot; prompt and renderer distinguish saved count from candidate count.
3. The earlier handoff referenced old services, prompt version 4, 146 tests,
   uncommitted work and no upstream. The readiness work reran current checks,
   restarted only task-owned isolated servers, prepared the trace inspector
   and mock browser harness, repaired links after the student's mockup
   reorganization, and refreshed documentation and handoff from evidence.

The second provider stream must finish normally. Incomplete/truncated
responses, extra prose fields, unknown/unavailable/duplicate IDs, and
inconsistent reasons are rejected. Output is buffered until validation
passes. No unchecked partial answer is displayed or saved as a success.

## AutoLoop and verification

The focused repair suite passed **40 tests** on its first run. The full
suite then passed **164 tests**, with two pre-existing dependency deprecation
warnings; it passed again after the final singular/plural text correction.
There was no failing source-test correction cycle. Frontend checks passed
**26 tests**, read-only Oxlint and ESLint, and a production build. No package
manifest or lockfile changed. Documentation reference repair and its check
were performed separately. The patch tool initially rejected two documentation
patches because their contexts/operations did not match; corrected patches
succeeded without a source-code failure.

The repository-wide link check found the archived `a1-report.md` references
an absent local `Expedia Lite Demo.mp4`; that historical recording was not
recreated. The 29 current Markdown files passed their local-reference check.

The staged whitespace check flagged extra final blank lines in the recording
guide and supplied tutorial copy. Their final newlines were normalized;
the tutorial text was preserved. The staged check was repeated.

Commands from the project root:

```bash
backend/.venv/bin/python -m pytest backend/tests/test_gemini.py backend/tests/test_grounded_answer.py backend/tests/test_retrieval.py backend/tests/test_rag_chat.py -q
backend/.venv/bin/python -m pytest backend/tests -q
git diff --check
```

Commands from `frontend/`:

```bash
npm test
npm exec -- oxlint .
npm exec -- eslint .
npm run build
```

The [command transcript](assignment2-part2-stage6-commands.txt) records all
shell commands from the authorized repair turn, including inspection,
fixture preparation, checks, service startup, trace read and cleanup.
Browser automation used Codex's CUA controls, not a shell-driven browser.
The [recording guide](assignment2-part2-demo.md) documents reproducible inputs.

## Current observed live/browser checks

Normal backend: `create_app(Path("backend/db/part2-oct8-audit.sqlite3"))`,
port 8001. Vite proxy: 8001, frontend port 5174. These services used real
Gemini calls and actual Geoapify place lookup. All stored rates and rooms
were simulated fixture values.

| Input/action | Expected | Observed |
| --- | --- | --- |
| Compare ZIP 16803, October 11–13 | Campus 23000 cents; Valley 27000; actual nightly dates; exclude zero-room Budget | Final live two-call turn `f2afaf26-5a1e-4a1c-870e-252b37e6b39c` and UI agreed; second JSON selected Campus/Valley and lowest_total_cost |
| Under $50 October 11 | No preference match while saved hotels exist | Empty selection/no_match; saved count 3; correct no-match explanation |
| October 15 | Missing rows mean unknown availability | Three candidates and three incomplete; no matches; insufficient_data |
| ZIP 16804 | No saved hotel without invented recommendations | Saved count 0 and candidate count 0; no hotel saved |
| Missing ZIP/date | Editable error, no assistant success | Edit question restored exact draft; failed turn retained user/error only |
| Keyboard | Enter send, Shift+Enter newline, Escape close/focus launcher | All observed |
| ZIP 16802 Geoapify | Five-digit ZIP resolved, real places and linked map | State College center 40.803167822/-77.861384958, 5 km, 50 max, 21 places observed |
| Card/map keyboard selection | Both selections synchronize | Scholar card selected its pin; Enter on Nittany pin selected its card |
| Add Scholar to Local | One saved hotel with five dated simulated nights | Saved label, disabled Add, $100/20 rooms on October 10–14 |
| Duplicate local API save | Existing hotel/nights preserved | 200, one identical hotel/nights; totals temporarily 4 saved/4 ZIP/11 nights |
| Restart both task-owned servers, reload | Saved hotel and chat restored; local-first | Same saved Scholar and history; saved ZIP request needed no provider lookup |
| Remove Scholar | Hotel, all ZIP links and nights removed | Final 3 saved/3 ZIP/6 nights; provider cards returned with enabled Add |
| Invalid abcde ZIP | Inline validation | Five-digit error displayed |
| Harbor, nonexistent name, blank | One hotel/two stays; no-results; blank error | All three observed through browser; Harbor/blank APIs also verified |
| Console | No application warning/error entries | Empty live browser logs |

The final successful trace is [stage6-trace.txt](assignment2-part2-stage6-trace.txt).
Its direct two-JOIN rows agree with all checked matches, and the result stage
stores `second_model_answer` plus `answer_validation`. Earlier successful
turns in the same conversation include two-night `e5dee3ad-d6e3-4fb2-b9a5-5d2d50a51609`,
budget `3416497f-8245-4799-b898-ef6463c6381b`, missing-night
`586508a3-3f08-4b67-bab9-54395c10a7c4`, absent ZIP
`c034b4f1-1ec1-48d6-b36c-8a0df57909e4`, and failed missing-context
`2cd91bf6-cfc6-4c11-89da-9abb02967b10`.

## Explicitly mocked browser failures

Separate synthetic database `part2-oct8-mock.sqlite3`, backend 8002 and
frontend 5175. `backend.tests.browser_scenarios` mocks both providers only
when explicitly launched. Normal production routes are not patched by
importing the test module.

| Input | Expected | Observed |
| --- | --- | --- |
| ZIP 00501 | Leading zero retained; labeled mock places | Two MOCK places |
| ZIP 16804 | Successful empty provider response | Empty-result UI |
| ZIP 00000 | Unresolved ZIP distinct from empty | ZIP-not-resolved error |
| ZIP 99999 | Provider failure distinct from empty | Provider-unavailable error |
| MOCK rate-limit | Safe error and Retry | Both shown, no assistant success |
| MOCK rejected-sql | UPDATE rejected before retrieval | Safe error, no result or assistant success; fixture domain rows preserved |
| MOCK bad-answer | Wrong-date prose field rejected | Validation error, no unchecked delta/assistant; Retry repeated the expected safe failure |
| MOCK filtered under $50 | Zero candidates but 3 saved hotels | Correct no-match answer; no false no-saved claim |
| Narrow viewport | Panel/composer fit, no horizontal overflow | Measured 520px CSS viewport; page width 520px; panel within x8–512; composer inside viewport |
| Console | No application warning/error entries | Empty mock browser logs |

No deliberate live quota or destructive-query request was made.
Provider-failure outcomes are mocked evidence, not live model successes.

## Data preservation and verification limits

Read-only inspections found:

| Database | Schema | A1 hotels/trips/bookings | Saved hotels/ZIPs/nights | Integrity |
| --- | ---: | --- | --- | --- |
| Default runtime | 6 | 8/12/10 | 1/1/5 | Zero foreign-key violations |
| October 8 live fixture after removal | 7 | 8/12/6 | 3/3/6 | Zero foreign-key violations |
| October 8 mock fixture | 7 | 8/12/6 | 3/3/6 | Zero foreign-key violations |

The default runtime was inspected read-only and not migrated/reset during
this audit. The normal application upgrades schema 6 to 7 on its next startup.
Fixture preparation and migrations are covered by tests. No `data/` CSV,
`geocoding.py`, `places.py` or `NearbyHotelsMap.vue` changed from the
original HEAD. Ignored databases, keys, environments and build output are
excluded from the implementation checkpoint.

Verification proves the documented inputs, not every natural-language
question, live provider failure, geographic coverage or bookable inventory.
The measured narrow viewport was 520px, not 390px. Page reload and service
restart were tested; the full browser process was not restarted.
The Part 2 video and instructor access to it remain unverified.
All four task-owned services exited after Ctrl+C; `lsof` found no listeners
on 8000/8001/8002/5173/5174/5175. Both temporary verification tabs closed and
the viewport override was reset. Unrelated processes were not stopped.
The exact earlier Codex selector is not independently established; the
student confirmed today's review/repair model as **GPT-6.1 Sol**.

## File-level change record

This audit modified `backend/controllers/retrieval.py`, `gemini.py`,
`rag_chat.py`, `chat_history.py`, `backend/models/retrieval.py`,
`backend/tests/test_gemini.py`, `test_rag_chat.py`, `test_retrieval.py`,
`frontend/src/components/ChatPopup.vue` and `prompts/hotel-assistant.md`.
It added `grounded_answer.py`, `test_grounded_answer.py`,
`backend/inspect_rag_demo.py` and `backend/tests/browser_scenarios.py`.
It updated README, report, the archived A2.1 report's moved-image links,
verification guidance, the Part 2 plan, RAG trace and current handoff.
It added this audit, its command/trace files, the recording guide, and
`docs/test-screenshots/part2-oct8-*.png`. One invalid task-created crop was
discarded; the corrected full answer screenshot is retained.

The checkpoint also preserves and commits the pre-existing Part 2
implementation, stage documents, tests and screenshots, plus the student's
mockup reorganization; it does not treat those older changes as new repairs.
Inspect the checkpoint's Git file list for the complete included paths.
