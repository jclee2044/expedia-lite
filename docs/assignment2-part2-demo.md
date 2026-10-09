# Assignment 2.2 recording guide

The implementation and October 8 checks are complete. The student must still
record a Part 2 video, verify instructor access, add its link to `report.md`,
review the report and submit it. Do not present screenshots or this guide as
an existing recording.

## Prepare a fresh synthetic live demonstration

From the project root, choose a new filename if this one already exists.
Preparation refuses an existing path and never resets the default database.
Configure the ignored root `.env` beforehand; keep it off-screen.

```bash
backend/.venv/bin/python -m backend.prepare_rag_demo backend/db/part2-recording.sqlite3
backend/.venv/bin/python -c 'from pathlib import Path; import uvicorn; from backend.app.main import create_app; uvicorn.run(create_app(Path("backend/db/part2-recording.sqlite3")), host="127.0.0.1", port=8001)'
```

In a second terminal, from `frontend/`:

```bash
EXPEDIA_API_TARGET=http://127.0.0.1:8001 npm run dev -- --host 127.0.0.1 --port 5174 --strictPort
```

If these ports are occupied, inspect ownership and use another pair. Never
stop an unrelated service. Open http://127.0.0.1:5174/. This normal backend
uses actual Gemini and Geoapify requests. Label saved rates and rooms
**synthetic fixture**, not provider inventory. Model: Gemini 3.5 Flash-Lite;
prompt version 6. A fresh database lacks the browser's old conversation ID;
opening chat handles an unknown ID by beginning a new conversation.

## Suggested recording sequence

Simple questions such as “16803 has what hotels” now list checked saved
identities without dates. Prices and availability still need dates. A
missing-date question shows “More information needed” with Edit question,
including after reload. The [clarification follow-up](assignment2-part2-stage7.md)
records the ZIP-only and dated live checks. Use the dated comparison below
for the required nightly-data/two-JOIN demonstration.

1. In ZIP mode, show saved ZIP 16803 with three fixture hotels and dated
   simulated nights. Explain the local-first lookup and separate Part 1
   live-place search. If demonstrating Add/Remove, use ZIP 16802 to fetch
   provider places, save one, show the simulated default nights and disabled
   Add, refresh/restart to confirm persistence, then remove it.
2. Open chat and ask:
   **Compare saved hotels near ZIP 16803 from 2026-10-11 to 2026-10-13 by total cost.**
   State the expectation first: Campus $230, Valley $270, October 11–12,
   checkout excluded, Budget excluded for zero rooms.
3. In a separate terminal run the read-only trace command below. Show the
   question, generated SQL and bindings, both hotel joins, checked records,
   second-model selection and validation. Return to the popup and compare
   the dates/rates/totals and simulated-data label. The latest completed
   turn is selected by default; use `--turn-id UUID` to choose an earlier one.
4. Ask **Which saved hotels near ZIP 16803 on 2026-10-11 cost under $50?**
   Expect no qualifying recommendation while three hotels remain saved.
   Then ask **Which saved hotels near ZIP 16803 are available on 2026-10-15?**
   Expect missing records/unknown availability. ZIP 16804 instead proves
   absence of saved hotels. Inspect each trace to show changed binds/results.
5. Reload the page and reopen chat. Stop and restart only the backend and
   frontend you started, using the same database; reopen the same URL.
   Confirm persisted messages and saved hotels. State that this proves page
   reload/service restart, not restarting the entire browser application.
6. Show the deliberate SQL safety test or the clearly labeled mock harness
   below. Compare expected rejection and preserved rows with observed
   results. Do not label this as a live model success.
7. Show the passing regression evidence and explain limits: simulated rates,
   bounded saved inventory, no booking, and provider quotas. Add the final
   video link to the report and test its sharing settings from a signed-out
   or instructor-equivalent browser.

```bash
backend/.venv/bin/python -m backend.inspect_rag_demo backend/db/part2-recording.sqlite3
backend/.venv/bin/python -m pytest backend/tests/test_retrieval.py -q
```

## Optional explicitly mocked browser failures

This isolated harness mocks both providers. It is a test helper, not the
normal application. Use a second fresh database and separate ports:

```bash
backend/.venv/bin/python -m backend.prepare_rag_demo backend/db/part2-recording-mock.sqlite3
backend/.venv/bin/python -m backend.tests.browser_scenarios backend/db/part2-recording-mock.sqlite3 --port 8002
```

From `frontend/`:

```bash
EXPEDIA_API_TARGET=http://127.0.0.1:8002 npm run dev -- --host 127.0.0.1 --port 5175 --strictPort
```

Open http://127.0.0.1:5175/ and explicitly say **mocked provider failure test**.

| Question or ZIP | Expected |
| --- | --- |
| `MOCK rejected-sql near 16803 on 2026-10-11` | UPDATE proposal rejected; no retrieved result or assistant success |
| `MOCK rate-limit near 16803 on 2026-10-11` | Safe quota error and Retry |
| `MOCK bad-answer near 16803 on 2026-10-11` | Extra invented prose rejected; no unchecked answer |
| `MOCK filtered saved hotels under $50 near 16803 on 2026-10-11` | Zero candidates, three saved hotels, correct no-match |
| ZIP `00501` | Leading zero retained; two MOCK hotels |
| ZIP `16804` / `00000` / `99999` | Successful empty / unresolved ZIP / provider error |

For the rejected turn, use the trace command with its turn ID to show the
proposal and error. The retrieval tests assert unchanged hotel/ZIP/night
rows. Stop each service with Ctrl+C in its own terminal after recording.
