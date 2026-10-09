# Expedia Lite — Assignment 2, Part 2

## Scope and project access

Assignment 2.2 adds **question → LLM-proposed SQL → validated read-only local
retrieval → second LLM request with the original question and retrieved
records → grounded, actionable answer in Vue**. The local-storage foundation
is working and provides the saved records used by the chatbot. The [revised brief](docs/assignment2-part2-revised.md)
and [supplied tutorial](docs/assignment2-part2-instructor-chatbot-notes.txt)
define the scope. SQLite is sufficient; no vector database was added.

Repository: [Expedia Lite](https://github.com/jclee2044/expedia-lite), branch
`rag_integration`. **Assessed application commit:
[`bbff2ca`](https://github.com/jclee2044/expedia-lite/commit/bbff2ca32b3eb29a98954343ebee2d23a4a8e2da).**
This local implementation checkpoint includes the final off-white UI and
the chat popup's upward opening animation, quicker closing animation, and
reduced-motion support. [Animation verification](docs/chat-animation-verification.md)
records the frontend and browser checks and their limits. Publication of
this commit is pending; its GitHub link will work after it is pushed.
The report and refreshed handoff are saved in a subsequent documentation commit.

Use Python 3.12 and the Node.js version documented in [README.md](README.md).
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
the [recording guide](docs/assignment2-part2-demo.md). Its preparation command
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
website's branding. My screenshot below shows the opened Virtual Agent panel;
the button and animation comments describe my interaction with it, rather
than something that a still screenshot can demonstrate.

![Expedia Virtual Agent reference supplied by the student](/Users/jlee/Desktop/psu4/ist402/a1_expedia_lite/docs/mockups/expedia-virtual-agent.png)

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

My [early Assignment 2.2 mockup](docs/mockups/a2.2-mockups.png) shows the
Chat launcher and bordered popup. The [preflight notes](docs/assignment2-part2-preflight.md)
and [supporting layout sketch](docs/assignment2-part2-chat-mockup.svg)
record the planned chat states.

![Early Assignment 2.2 mockup](/Users/jlee/Desktop/psu4/ist402/a1_expedia_lite/docs/mockups/a2.2-mockups.png)

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
informed the second request's JSON schema. The implementation uses the
existing project-owned `httpx` dependency rather than adding a provider SDK.
SQLite's [authorizer documentation](https://www.sqlite.org/c3ref/set_authorizer.html)
informed the table/function allowlist for proposed SQL. Independent backend
queries verify ZIP membership, nightly coverage, rooms, and integer-cent
totals; the LLM receives no database connection.

## Local-storage foundation and architecture

Add to Local preserves the provider `place_id` as `saved_hotels.hotel_id`,
stores the searched ZIP and center in `saved_hotel_zips`, and creates dated
simulated rows in `demo_hotel_nights`. Duplicate saves preserve existing
hotel fields and edited nights and can add another ZIP association. Remove
from Local deletes the hotel, ZIP associations, and nights transactionally.
The ZIP view checks saved records first, with a **Saved locally** label, and
calls Geoapify only after a successful empty local lookup. SQLite retains
saved hotels and conversation history across restarts.

The default simulated nights are October 10–14, 2026, at 10000 cents with
20 rooms. Geoapify supplies identities and locations, not these rates or
vacancies. The fixed demonstration data overrides those defaults and is
explicitly labeled synthetic. The original hotel/trip/account/booking tables
remain separate from the saved-hotel records used by the chatbot.

The dependency direction is Vue View → FastAPI routes → framework-free
Controllers → Models/SQLite. Routes handle HTTP and validation; controllers
own retrieval, provider calls, transactions and persistence. Request helpers
remain separate from Vue presentation. Schema version 7 adds conversation,
message and retrieval-stage tables through an additive migration.

## Implemented two-call workflow

The first request sends the question, trusted ZIP/dates, relevant schema and
query rules to Gemini 3.5 Flash-Lite.
The model proposes one parameterized SELECT returning candidate hotel IDs.
The backend requires exact ZIP/date bindings, approved saved-hotel tables,
one statement, and a bounded query. A separate SQLite `mode=ro` connection,
`query_only`, authorizer, 50-candidate cap and execution budget enforce
read-only retrieval. Trusted SQL then checks each requested night, positive
rooms and total cents; checkout is excluded. Missing nightly rows mean
unknown availability. A separate saved-ZIP count prevents an empty filtered
candidate set from being described as no saved hotels.

The second request contains the **original question** and at most ten
checked stays, dated nightly records and exclusion counts. Prompt version
**5** requires only selected hotel IDs and a supported reason in JSON.
The backend requires normal provider completion and validates this
recommendation. It renders all factual text from checked records, saves
the answer and model selection together, and sends the checked text to Vue
in chunks. Unsupported IDs, extra prose fields and incomplete output produce
an error without a successful assistant message. This still uses the second
LLM call to choose a recommendation based on retrieved facts.

The [prompt](prompts/hotel-assistant.md), [retrieval controller](backend/controllers/retrieval.py),
[grounding controller](backend/controllers/grounded_answer.py) and
[orchestrator](backend/controllers/rag_chat.py) implement this contract.
SQLite stores question, proposal, attempted execution, checked result,
second-model selection, answer validation, answer, errors and timestamps.
The [read-only trace CLI](backend/inspect_rag_demo.py) makes these stages.

## Traced live demonstration — October 8, 2026

**Evidence: actual live Gemini calls through the normal application, over
the fixed synthetic SQLite fixture.** The failure harness was not used for
these calls. The final browser question, after restarting both task-owned
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

![Checked live two-night answer](docs/test-screenshots/part2-oct8-final-answer.png)

The final UI refinement changes assistant bubbles to neutral off-white
(`#f7f7f7`). Its [browser screenshot](docs/test-screenshots/chat-off-white-background.png)
and [verification record](docs/test-screenshots/chat-off-white-background.txt)
confirm the rendered color and a passing production build. This color-only
change did not repeat the earlier full backend regression or live model calls.

The [complete saved trace](docs/assignment2-part2-stage6-trace.txt) includes
the original question, proposed SQL, records, second-model JSON and displayed
answer. It was independently read from the ignored
`backend/db/part2-oct8-audit.sqlite3` database. [rag-context.md](docs/rag-context.md)
also retains the October 6 checkpoints as historical evidence.

## Verification record

I used the [fixed JSON sample](docs/part2-rag-fixture.json) to make the saved
hotel checks repeatable. It contains three fictional hotels, their ZIP
associations, six dated nightly records, and expected results. These rates
and room counts are simulated classroom data, not live hotel inventory.
The observations below come from the October 8 verification recorded in the
[readiness record](docs/assignment2-part2-stage6.md) and
[saved trace](docs/assignment2-part2-stage6-trace.txt); they were not new live
model calls made while editing this report.

### Test 1: Successful two-night comparison

When the user asks “Compare saved hotels near ZIP 16803 from 2026-10-11 to
2026-10-13 by total cost”:

- Expected: Campus Lantern costs $230 and Valley Ridge costs $270 for October
  11 and 12. Checkout is excluded. Nittany Budget is excluded because it has
  zero rooms on October 11.
- Observed: The answer showed Campus at $230 and Valley at $270, with the
  correct nightly dates, prices, room counts, and simulated-data label.

### Test 2: No hotel matches the requested budget

When the user asks for saved hotels near ZIP 16803 on October 11 for under
$50 a night:

- Expected: No hotel is recommended, but the answer does not claim that no
  hotels are saved for this ZIP.
- Observed: The model selected no hotels and the interface gave a no-match
  explanation. The retrieval trace still showed three saved hotels.

### Test 3: Requested nightly data is missing

When the user asks for hotels near ZIP 16803 on October 15:

- Expected: The answer explains that availability cannot be verified because
  the sample has no nightly records for that date.
- Observed: The query found three hotel candidates, but all three lacked the
  requested night. The answer said availability could not be verified.

### Test 4: No hotel is saved for the ZIP

When the user asks for hotels near ZIP 16804:

- Expected: No hotel is recommended or invented.
- Observed: The saved-hotel count and candidate count were zero, and the
  answer explained that no hotel was saved for this ZIP.

### Test 5: A disallowed query is proposed

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
an unrelated service. Open `http://127.0.0.1:5174/` and repeat Tests 1–4.
After each completed question, run this from the project root to show the
latest saved question, proposed SQL, bindings, checked records, second-model
selection, and displayed answer:

```bash
backend/.venv/bin/python -m backend.inspect_rag_demo backend/db/part2-report-check.sqlite3
```

Compare these facts with the fixed sample: October 11 gives Campus $120 and
Valley $130; October 12 gives Budget $90, Campus $110, and Valley $140;
October 11–13 gives Campus $230 and Valley $270; ZIP 16804 gives no matches;
October 15 gives missing-data exclusions. For Test 5 and repeatable failure
checks without live model calls, run:

```bash
backend/.venv/bin/python -m pytest backend/tests/test_retrieval.py backend/tests/test_grounded_answer.py backend/tests/test_rag_chat.py -q
```

These tests use their own labeled temporary fixtures and mocked model replies;
some include an extra incomplete hotel to exercise missing-data behavior.
They do not return the JSON sample or consume live model quota. The
[recording guide](docs/assignment2-part2-demo.md) also explains how to run the
explicitly mocked browser failures and compare preserved rows. Stop only the
servers started for these checks when finished.

## Additional Part 2 verification

### Test 6: Save, duplicate, and remove a local hotel

- Expected: Saving a hotel creates one saved record and five simulated
  nights. Saving it again preserves those records. Removing it deletes its
  ZIP associations and nights.
- Observed: Scholar was saved with the default nights. A duplicate save kept
  one identical hotel record. Remove from Local deleted its ZIP links and nights.

### Test 7: Persisted hotels and conversation history

- Expected: Saved hotels and chat messages remain after restarting the
  servers and reloading the page. Saved ZIP lookup uses local records.
- Observed: The saved Scholar hotel and conversation returned after restart
  and reload, and the saved ZIP lookup did not need a provider call.

### Test 8: Chat controls and narrow layout

- Expected: Missing context gives an editable error; Enter sends,
  Shift+Enter adds a line, and Escape closes chat and restores launcher focus.
  The popup and composer fit a narrow screen.
- Observed: Edit question restored the draft, Enter submitted it, Shift+Enter
  added a newline, and Escape returned focus to the launcher. At a 520px
  viewport, the page width was 520px and the panel and composer stayed inside it.

### Test 9: Mocked quota and unsupported-answer failures

- Expected: The labeled rate-limit mock shows a useful retry error. The
  bad-answer mock rejects unsupported prose without displaying or saving a
  successful answer.
- Observed: The rate-limit message and Retry control appeared. The invalid
  answer produced no successful assistant message or unchecked response text;
  retrying while the mock remained invalid failed safely.

### Test 10: Automated checks and integrity

- Expected: Backend and frontend checks pass, the browser reports no
  application errors, and database relationships remain valid.
- Observed: The October 8 checks passed 164 backend tests, 26 frontend tests,
  Oxlint, ESLint, and the production build. Both browser warning/error logs
  were empty, and inspected databases had no foreign-key violations.

![Budget no-match with saved hotels](docs/test-screenshots/part2-oct8-budget-no-match.png)

![Missing nightly data](docs/test-screenshots/part2-oct8-missing-night.png)

## Rejected SQL proof

**Evidence label: deliberately mocked proposal and synthetic temporary
database; no live model was asked to issue a destructive query.**
The browser harness proposed `UPDATE saved_hotels SET name=:postcode`.
The controller rejected it before retrieval, recorded an error, and showed
no assistant answer. Regression tests also reject multiple statements,
unapproved tables, schema reads and SQL functions, checking unchanged
saved-hotel/ZIP/night rows. Application-owned history/error writes are
separate from model-proposed read-only retrieval.

![Explicitly mocked SQL rejection](docs/test-screenshots/part2-oct8-mock-rejected-sql.png)

The [readiness record](docs/assignment2-part2-stage6.md) documents fixes,
commands, observed cases and limitations. The [command transcript](docs/assignment2-part2-stage6-commands.txt)
lists each shell command. The bounded AutoLoop passed the focused repair
suite, then the full regression checks; no dependency change was needed.
Two pre-existing dependency deprecation warnings remain.

## AI disclosure, limitations and recording

I used GPT-6.1 Sol for Assignment 2.2, including implementation,
review, tests, browser checks, and report updates. The in-site chatbot uses
Gemini 3.5 Flash-Lite for its two model requests.

### Assignment 2.2 sample prompts and evidence log

These are sample prompts I used to direct the Assignment 2.2 work.

I asked for help getting the Gemini API set up and choosing the runtime model:

```text
use computer use to access the browser and direct me to getting a free api key for gemini. select the model for assignment 2.2
```

The [provider setup record](docs/assignment2-part2-stage2.md) documents this
stage. The [Gemini controller](backend/controllers/gemini.py) contains the
selected model and backend-only requests; the key stays in the ignored `.env`.

I supplied the assignment description and asked for a plan that started with
the foundation and validated one step at a time:

```text
[assignment description and requirements]
store these in docs for assignment 2 part 2.
identify dependencies and the foundation to build upon. what needs to be true and verified first before we can begin building, and what are the next steps from there? you must utilize best software engineering principles, keep it simple, and build and validate one step at a time. propose your detailed plan, separated by turn with human-in-the-loop checkpoints at each step.
```

The bracketed line represents the assignment material supplied with the
prompt. The resulting [requirements record](docs/assignment2-part2-revised.md),
[preflight checks](docs/assignment2-part2-preflight.md), and
[turn-by-turn plan](docs/assignment2-part2-plan.md) document the foundation,
dependencies, validation, and checkpoints.

I then specified the branch, popup design, staged integration, and prompt file:

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

The [stub stage](docs/assignment2-part2-stage1.md) and
[raw-model stage](docs/assignment2-part2-stage2.md) record the incremental
approach before retrieval was connected. The final
[chat popup](frontend/src/components/ChatPopup.vue) has the scrollable
conversation, and [hotel-assistant.md](prompts/hotel-assistant.md) stores the
versioned instructions. The final implementation validates the complete
model recommendation before delivering checked answer text in chunks.

During visual review, I asked to change “Chat with Gemini” to “Chat” and
change the assistant bubble background from cream to off-white after the
cream looked too butter yellow. These are my descriptions of the revisions,
rather than verbatim prompt transcripts. The launcher is in the
[chat popup](frontend/src/components/ChatPopup.vue), and the bubble and
header colors are in [main.css](frontend/src/assets/main.css).

Before finishing, I asked for a critical review:

```text
i need you to critically review the current implementation. is everything in place? does it match expectations? has everything been tested and is it working? is the handoff updated? the only thing remaining should be the report and the demo video recording. is that accurate?
```

The [readiness review](docs/assignment2-part2-stage6.md),
[command transcript](docs/assignment2-part2-stage6-commands.txt), and
[saved trace](docs/assignment2-part2-stage6-trace.txt) record the corrections
and checks. The review did not simply assume the application was complete:
it identified the grounding issues described below, and those were corrected
and verified before the report and recording work.

A failed approach was accepting free-form second-model prose. A live review
found correct two-night totals with an incorrect nightly date. Another
controlled filtered query plus a live second request incorrectly described
zero candidates as no saved hotels. Version 5 replaces that prose with a
validated selection and database-rendered facts, and separately counts saved
hotels. Tests inject the wrong-date prose and filtered-empty case; the final
live and browser checks above verify the corrected behavior. Historical
October 6 fixes also included an ESLint `process` import and replacing a
failed-reply placeholder with an honest error/Edit state.

Limits: these rates and rooms are simulated and cannot be booked. The parser
accepts one five-digit ZIP and one or two ISO/full-month dates, with explicit
same-context follow-ups; other forms may need clarification. Up to 50 SQL
candidates and ten checked stays are considered for the second request.
The model still interprets natural-language preferences within this bounded
contract. No exhaustive hotel inventory, every provider failure, full browser
process restart, or instructor access to the recording was established.

### Part 2 screen-recorded demo video

- [Watch the Expedia Lite A2.2 demo on Google Drive](https://drive.google.com/file/d/1J4udpc61lYgkqU2g-jq0wY48eyfSOIYj/view?usp=drive_link).
- [Expedia Lite A2.2 Demo.mov](<Expedia Lite A2.2 Demo.mov>) — local copy in the project root.

TODO: Confirm the instructor can access the Drive recording without requesting
access, review this report, and upload it.
