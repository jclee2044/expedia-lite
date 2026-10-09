# Expedia Lite — Assignment 2, Part 2

## Scope and project access

Assignment 2.2 adds **question → LLM-proposed SQL → validated read-only local
retrieval → second LLM request with the original question and retrieved
records → grounded, actionable answer in Vue**. The local-storage foundation
is working and provides the saved records used by the chatbot.

Repository: [Expedia Lite](https://github.com/jclee2044/expedia-lite), branch
`rag_integration`.

Assessed Assignment 2.2 application commit: [`2eae498`](https://github.com/jclee2044/expedia-lite/commit/2eae4985184dce0c8924e0791b94fa3fed5a23de).
This includes ZIP-only hotel lists, corrected date clarifications, off-white
messages and the chat animation. The finalized report and recording are in
the later documentation commit on this branch.

Referenced commit: [`d8edae8077373528cfd4e690c212c4d0e9b1c9fc`](https://github.com/jclee2044/expedia-lite/commit/d8edae8077373528cfd4e690c212c4d0e9b1c9fc).
This is the earlier project checkpoint; the Assignment 2.2 implementation
was developed after it on `rag_integration`.

Use Python 3.12 and the Node.js version documented in [README.md](https://github.com/jclee2044/expedia-lite/blob/2eae4985184dce0c8924e0791b94fa3fed5a23de/README.md).
Create the project-owned environments with:

```bash
python3.12 -m venv backend/.venv
backend/.venv/bin/python -m pip install -r backend/requirements.txt
cd frontend
npm ci
```

Configure `GEOAPIFY_API_KEY` and `GEMINI_API_KEY` in the ignored root
`.env`; restart the backend after changing configuration. Keys and model
requests stay on the backend. The normal commands are
`backend/.venv/bin/python -m uvicorn backend.app.main:app --reload` from the
root and `npm run dev` from `frontend/`, with the UI on port 5173.
For the reproducible synthetic fixture on isolated ports 8001/5174, follow
the [recording guide](https://github.com/jclee2044/expedia-lite/blob/2eae4985184dce0c8924e0791b94fa3fed5a23de/docs/assignment2-part2-demo.md). Its preparation command
refuses to overwrite an existing database. It preserves the default runtime
database and the course CSVs.

## Research notes

I looked at chatbot interfaces and thought about my experiences with them
while deciding how I wanted the chatbot on my website to look and behave.

### Chatbots that get in the way

I've seen websites before where the chatbot is always open in the corner
and in the way. I don't like that pattern because it clogs up the interface
and makes it harder to see the actual webpage content when I don't need to
use the chatbot. I feel that it increases cognitive load, because there is
another panel competing for my attention. I wanted to make sure my website
didn't have that problem, so the chat stays closed until the user chooses
to open it.

### Expedia: a small button and a simple chat panel

I liked the small corner chat button on [Expedia](https://www.expedia.com/helpcenter/)
because it doesn't get in the way when I am using the rest of the website.
I also liked the sleek interface and smooth animation when opening the chat.
However, I didn't like how the chat panel was mostly a plain white background.
I felt that it didn't have enough visual contrast and could better match the
website's branding.

![Expedia Virtual Agent reference supplied by the student](https://raw.githubusercontent.com/jclee2044/expedia-lite/2eae4985184dce0c8924e0791b94fa3fed5a23de/docs/mockups/expedia-virtual-agent.png)

### Intercom: a branded chat interface

The green chat interface in [Intercom's Exemplary Bank demonstration](https://www.intercom.com/blog/videos/new-at-intercom-full/)
is closer to the final design I wanted. The demo uses a green header and
accent colors that complement the surrounding website.

I think this chatbot UI looks sleek and professional. It uses brand colors
and feels like part of the website instead of a separate box added on top.
Overall, it matches the type of chat interface I wanted my website to have:
a small launcher when it is closed, a clear header when it is open, and
colors that match the rest of the interface.

## Early mockup and changes to the original design

My [early Assignment 2.2 mockup](https://github.com/jclee2044/expedia-lite/blob/2eae4985184dce0c8924e0791b94fa3fed5a23de/docs/mockups/a2.2-mockups.png) shows the
Chat launcher and bordered popup.

![Early Assignment 2.2 mockup](https://raw.githubusercontent.com/jclee2044/expedia-lite/2eae4985184dce0c8924e0791b94fa3fed5a23de/docs/mockups/a2.2-mockups.png)

I originally planned for the banner to be the same light green color as the
user text bubbles, but I found that it felt too basic and needed more
contrast. So, I changed the top menu bar of the chat popup to darker green.
I felt that this looked much more stable and showed a clearer visual hierarchy
through the colors. The darker header separates the title and controls from
the conversation, while the lighter green still works for the user messages.

The chat button originally said “Chat with Gemini.” I requested that it just
say “Chat” because there was no need to clarify the model there. I felt that
the model name was distracting from the purpose of the website.

I originally asked for the assistant responses to have a cream background,
but the result looked too butter yellow. I had it changed again to off-white,
which was closer to what I wanted.

I kept the small corner button so the chat doesn't cover the page until it
is needed. The popup allows the page behind it to remain interactive and
supports keyboard opening, closing, and sending. The
[W3C dialog guidance](https://www.w3.org/WAI/ARIA/apg/patterns/dialog-modal/)
and [MDN log-role reference](https://developer.mozilla.org/en-US/docs/Web/Accessibility/ARIA/Reference/Roles/log_role)
were technical references for these behaviors.

Google's [generate-content API](https://ai.google.dev/api/generate-content)
informed the backend provider calls. Its [structured-output guide](https://ai.google.dev/gemini-api/docs/structured-output)
informed the second request's JSON schema.
SQLite's [authorizer documentation](https://www.sqlite.org/c3ref/set_authorizer.html)
informed the table/function allowlist for proposed SQL. Independent backend
queries verify ZIP membership, nightly coverage, rooms, and integer-cent
totals; the LLM receives no database connection.

## Local-storage foundation and implementation

Add to Local saves a hotel, its ZIP/location context, and dated simulated
nightly rates and room counts in SQLite. Duplicate saves preserve the existing
record. Remove from Local deletes the saved hotel and its related records.
ZIP searches check locally saved hotels first, and saved hotels and conversation
history persist across restarts. Geoapify supplies hotel identities and
locations, not prices or availability; the nightly values are classroom data.

The application follows Vue View → FastAPI routes → Controllers → Models/SQLite.
FastAPI handles HTTP requests, while controllers handle the database and
business logic.

The chatbot sends the question and relevant schema to Gemini 3.5 Flash-Lite,
which proposes SQL. The backend checks the proposal and permits only bounded,
read-only retrieval. It independently checks ZIP membership. For stays it also
checks complete nightly records, positive room counts and totals, excluding checkout.

The second model request includes the original question and checked records.
Gemini selects hotel IDs and a recommendation reason. The backend validates
that selection and displays the answer using facts from the retrieved records.
Missing nightly records mean unknown availability. ZIP-only questions can list
saved hotels without making price or availability claims.

The [system prompt](https://github.com/jclee2044/expedia-lite/blob/2eae4985184dce0c8924e0791b94fa3fed5a23de/prompts/hotel-assistant.md) defines the instructions.
Questions, SQL proposals, retrieved results, answers, and errors are saved
in SQLite with timestamps. The [saved trace](https://github.com/jclee2044/expedia-lite/blob/2eae4985184dce0c8924e0791b94fa3fed5a23de/docs/assignment2-part2-stage6-trace.txt)
shows the recorded workflow.

## Traced live demonstration — October 8, 2026

**Evidence: actual live Gemini calls through the normal application, over
the fixed synthetic SQLite fixture.** The failure harness was not used for
these calls. The readiness-audit browser question, after restarting both task-owned
servers, was:

> Compare saved hotels near ZIP 16803 from 2026-10-11 to 2026-10-13 by total cost.

Turn ID: `f2afaf26-5a1e-4a1c-870e-252b37e6b39c`. Prompt version: 5.
The saved SQL proposal was:

```sql
SELECT DISTINCT h.hotel_id AS hotel_id
FROM saved_hotels AS h
JOIN saved_hotel_zips AS z ON z.hotel_id = h.hotel_id
LEFT JOIN demo_hotel_nights AS n ON n.hotel_id = h.hotel_id
  AND n.stay_date >= :check_in AND n.stay_date < :check_out
WHERE z.postcode = :postcode
```

```json
{"postcode":"16803","check_in":"2026-10-11","check_out":"2026-10-13"}
```

The two joins connect saved hotel identities to ZIP associations and dated
nights. The proposed query retrieves candidates; trusted backend SQL checks
the source facts below.

| Hotel / ID | October 11 cents / rooms | October 12 cents / rooms | Checked result |
| --- | --- | --- | --- |
| Nittany Budget / `fixture:budget` | 10000 / 0 | 9000 / 2 | Excluded: one requested night has zero rooms |
| Campus Lantern / `fixture:campus` | 12000 / 2 | 11000 / 2 | Match: 23000 cents |
| Valley Ridge / `fixture:valley` | 13000 / 2 | 14000 / 2 | Match: 27000 cents |

The second live model request returned:

```json
{"hotel_ids":["fixture:campus","fixture:valley"],"reason":"lowest_total_cost"}
```

**Expected:** Campus $230, Valley $270, October 11 and 12 nightly rows,
checkout October 13 excluded, Budget omitted, simulated-data label.
**Observed:** the displayed answer showed exactly those facts and identified
Campus as the lowest checked total. In particular, Valley's $140 nightly
rate was attached to **October 12**, not October 14.

![Checked live two-night answer](https://raw.githubusercontent.com/jclee2044/expedia-lite/2eae4985184dce0c8924e0791b94fa3fed5a23de/docs/test-screenshots/part2-oct8-final-answer.png)

## Verification record

I used the [fixed JSON sample](https://github.com/jclee2044/expedia-lite/blob/2eae4985184dce0c8924e0791b94fa3fed5a23de/docs/part2-rag-fixture.json) to make the saved
hotel checks repeatable. It contains three fictional hotels, their ZIP
associations, six dated nightly records, and expected results. These rates
and room counts are simulated classroom data, not live hotel inventory.
The successful comparison and missing-data checks used live Gemini calls
over the synthetic fixture on October 8, 2026. Failure checks used labeled
mocks and temporary databases.

### Test 1: Successful two-night comparison

When the user asks “Compare saved hotels near ZIP 16803 from 2026-10-11 to
2026-10-13 by total cost”:

- Expected: Campus Lantern costs $230 and Valley Ridge costs $270 for October
  11 and 12. Checkout is excluded. Nittany Budget is excluded because it has
  zero rooms on October 11.
- Observed: The answer showed Campus at $230 and Valley at $270, with the
  correct nightly dates, prices, room counts, and simulated-data label.

### Test 2: Requested nightly data is missing

When the user asks for hotels near ZIP 16803 on October 15:

- Expected: The answer explains that availability cannot be verified because
  the sample has no nightly records for that date.
- Observed: The query found three hotel candidates, but all three lacked the
  requested night. The answer said availability could not be verified.

### Test 3: A disallowed query is proposed

When the labeled failure mock proposes an UPDATE query:

- Expected: The backend rejects it, the saved hotel records stay unchanged,
  and no successful assistant answer is saved.
- Observed: The interface showed the rejection. The temporary-database
  tests confirmed unchanged hotel, ZIP, and nightly-row counts.

## Reproducing the fixed-sample checks

Reproducing these checks means loading the same JSON sample into a fresh
SQLite database, asking the same questions, and comparing the checked
records and displayed facts with the sample's `expected` values. It does
**not** mean getting the entire fixture JSON back from the chatbot. A live
model can propose equivalent SQL or phrase/select its answer differently.
The important checks are the hotel IDs, dates, exclusions, totals, safe
failure behavior, and whether the answer is supported by retrieved records.

From the project root, configure `GEMINI_API_KEY` in the ignored `.env` and
choose a new database filename if the following one already exists. The
preparation command refuses to overwrite an existing database.

```bash
backend/.venv/bin/python -m backend.prepare_rag_demo backend/db/part2-report-check.sqlite3
backend/.venv/bin/python -c 'from pathlib import Path; import uvicorn; from backend.app.main import create_app; uvicorn.run(create_app(Path("backend/db/part2-report-check.sqlite3")), host="127.0.0.1", port=8001)'
```

In a second terminal, from `frontend/`:

```bash
EXPEDIA_API_TARGET=http://127.0.0.1:8001 npm run dev -- --host 127.0.0.1 --port 5174 --strictPort
```

Use an available port pair if those ports are already occupied; do not stop
an unrelated service. Open `http://127.0.0.1:5174/` and repeat Tests 1 and 2.
After each completed question, run this from the project root to show the
latest saved question, proposed SQL, bindings, checked records, second-model
selection, and displayed answer:

```bash
backend/.venv/bin/python -m backend.inspect_rag_demo backend/db/part2-report-check.sqlite3
```

Compare these facts with the fixed sample: October 11 gives Campus $120 and
Valley $130; October 12 gives Budget $90, Campus $110, and Valley $140;
October 11–13 gives Campus $230 and Valley $270; ZIP 16804 gives no matches;
October 15 gives missing-data exclusions. For Test 3 and repeatable failure
checks without live model calls, run:

```bash
backend/.venv/bin/python -m pytest backend/tests/test_retrieval.py backend/tests/test_grounded_answer.py backend/tests/test_rag_chat.py -q
```

These tests use their own labeled temporary fixtures and mocked model replies;
some include an extra incomplete hotel to exercise missing-data behavior.
They do not return the JSON sample or consume live model quota. The
[recording guide](https://github.com/jclee2044/expedia-lite/blob/2eae4985184dce0c8924e0791b94fa3fed5a23de/docs/assignment2-part2-demo.md) also explains how to run the
explicitly mocked browser failures and compare preserved rows. Stop only the
servers started for these checks when finished.

## Additional Part 2 verification

### Test 4: Save, duplicate, and remove a local hotel

- Expected: Saving a hotel creates one saved record and five simulated
  nights. Saving it again preserves those records. Removing it deletes its
  ZIP associations and nights.
- Observed: Scholar was saved with the default nights. A duplicate save kept
  one identical hotel record. Remove from Local deleted its ZIP links and nights.

### Test 5: Persisted hotels and conversation history

- Expected: Saved hotels and chat messages remain after restarting the
  servers and reloading the page. Saved ZIP lookup uses local records.
- Observed: The saved Scholar hotel and conversation returned after restart
  and reload, and the saved ZIP lookup did not need a provider call.

### Test 6: Chat controls

- Expected: Missing context gives an editable clarification; Enter sends,
  Shift+Enter adds a line, and Escape closes chat and restores launcher focus.
- Observed: Edit question restored the draft, Enter submitted it, Shift+Enter
  added a newline, and Escape returned focus to the launcher.

### Test 7: Mocked quota failure

- Expected: The labeled rate-limit mock shows a useful retry error without
  inventing an answer.
- Observed: The rate-limit message and Retry control appeared.

### Test 8: Automated checks and integrity

- Expected: Backend and frontend checks pass, the browser reports no
  application errors, and database relationships remain valid.
- Observed: The earlier October 8 readiness checks passed 164 backend tests, 26 frontend tests,
  Oxlint, ESLint, and the production build. Both browser warning/error logs
  were empty, and inspected databases had no foreign-key violations.

![Missing nightly data](https://raw.githubusercontent.com/jclee2044/expedia-lite/2eae4985184dce0c8924e0791b94fa3fed5a23de/docs/test-screenshots/part2-oct8-missing-night.png)


## Latest clarification and ZIP-only verification

The current prompt is version 6. “17042 has what hotels” performs a checked
ZIP-only lookup and reports no saved hotel in the demo database. “16803 has
what hotels” lists Campus Lantern, Nittany Budget and Valley Ridge without
inventing dates or availability. Price and availability questions still need
dates; missing dates now show “More information needed” with Edit question,
including after reload.

The [follow-up verification](https://github.com/jclee2044/expedia-lite/blob/2eae4985184dce0c8924e0791b94fa3fed5a23de/docs/assignment2-part2-stage7.md) records these
actual live Gemini calls over synthetic data and the corrected date query
(Campus $120, Valley $130). Its full checks passed **174 backend tests**,
**28 frontend tests**, Oxlint, ESLint and the production build. The browser
warning/error log was empty.

![Correct date clarification](https://raw.githubusercontent.com/jclee2044/expedia-lite/2eae4985184dce0c8924e0791b94fa3fed5a23de/docs/test-screenshots/chat-clarification-fixed.png)

## Rejected SQL proof

**Evidence label: deliberately mocked proposal and synthetic temporary
database; no live model was asked to issue a destructive query.**
The browser harness proposed `UPDATE saved_hotels SET name=:postcode`.
The controller rejected it before retrieval, recorded an error, and showed
no assistant answer. Regression tests also reject multiple statements,
unapproved tables, schema reads and SQL functions, checking unchanged
saved-hotel/ZIP/night rows. Application-owned history/error writes are
separate from model-proposed read-only retrieval.

![Explicitly mocked SQL rejection](https://raw.githubusercontent.com/jclee2044/expedia-lite/2eae4985184dce0c8924e0791b94fa3fed5a23de/docs/test-screenshots/part2-oct8-mock-rejected-sql.png)

## AI disclosure, limitations and recording

I used Codex with GPT-6.1 Sol for Assignment 2.2, including implementation,
review, tests, browser checks, and report updates. The in-site chatbot uses
Gemini 3.5 Flash-Lite for its two model requests.

### Assignment 2.2 sample prompts

```text
use computer use to access the browser and direct me to getting a free api key for gemini. select the model for assignment 2.2
```

This led to the [provider setup](https://github.com/jclee2044/expedia-lite/blob/2eae4985184dce0c8924e0791b94fa3fed5a23de/docs/assignment2-part2-stage2.md) and [backend Gemini requests](https://github.com/jclee2044/expedia-lite/blob/2eae4985184dce0c8924e0791b94fa3fed5a23de/backend/controllers/gemini.py); credentials remain in the ignored .env.

```text
[assignment description and requirements]
store these in docs for assignment 2 part 2.
identify dependencies and the foundation to build upon. what needs to be true and verified first before we can begin building, and what are the next steps from there? you must utilize best software engineering principles, keep it simple, and build and validate one step at a time. propose your detailed plan, separated by turn with human-in-the-loop checkpoints at each step.
```

The resulting [plan](https://github.com/jclee2044/expedia-lite/blob/2eae4985184dce0c8924e0791b94fa3fed5a23de/docs/assignment2-part2-plan.md) and [preflight](https://github.com/jclee2044/expedia-lite/blob/2eae4985184dce0c8924e0791b94fa3fed5a23de/docs/assignment2-part2-preflight.md) identify the foundation and verification checkpoints.

```text
create and switch to `rag_integration` feature branch
frontend considerations:
needs to be a popup chat window in the bottom right corner, with a border that matches the color scheme
llm responses must use streaming, and preserve the conversation as a scrollable chat interface.

for api we will use a free gemini api
do not implement rag right away, just show the working stubbed interface as stage one, then the connection with raw llm. then we will implement the rag functionality
need the hotel-assistant.md system prompt stored in prompts/

show me in chat what your final proposed turn by turn plan looks like
```

This guided the staged [popup](https://github.com/jclee2044/expedia-lite/blob/2eae4985184dce0c8924e0791b94fa3fed5a23de/frontend/src/components/ChatPopup.vue), [provider integration](https://github.com/jclee2044/expedia-lite/blob/2eae4985184dce0c8924e0791b94fa3fed5a23de/docs/assignment2-part2-stage2.md), and versioned [system prompt](https://github.com/jclee2044/expedia-lite/blob/2eae4985184dce0c8924e0791b94fa3fed5a23de/prompts/hotel-assistant.md).

```text
i need you to critically review the current implementation. is everything in place? does it match expectations? has everything been tested and is it working? is the handoff updated? the only thing remaining should be the report and the demo video recording. is that accurate?
```

The [readiness audit](https://github.com/jclee2044/expedia-lite/blob/2eae4985184dce0c8924e0791b94fa3fed5a23de/docs/assignment2-part2-stage6.md) and [clarification follow-up](https://github.com/jclee2044/expedia-lite/blob/2eae4985184dce0c8924e0791b94fa3fed5a23de/docs/assignment2-part2-stage7.md) record defects found, fixes, and observed checks.

A failed approach was accepting free-form second-model prose. A live review
found correct two-night totals with an incorrect nightly date. Another
controlled filtered query plus a live second request incorrectly described
zero candidates as no saved hotels. Version 5 replaces that prose with a
validated selection and database-rendered facts, and separately counts saved
hotels. Tests inject the wrong-date prose and filtered-empty case; the final
live and browser checks above verify the corrected behavior.

The rates and rooms are simulated and cannot be booked. Missing stay dates
receive clarification, and saved hotels do not represent a complete area
inventory. Persistence checks used page reloads and server restarts.

### Part 2 screen-recorded demo video

- [Watch the Expedia Lite A2.2 demo on Google Drive](https://drive.google.com/file/d/1J4udpc61lYgkqU2g-jq0wY48eyfSOIYj/view?usp=drive_link).
- [Expedia Lite A2.2 Demo.mov](https://github.com/jclee2044/expedia-lite/blob/rag_integration/Expedia%20Lite%20A2.2%20Demo.mov) — repository copy in the project root.
