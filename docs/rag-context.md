# Saved-hotel RAG trace

## Current version 5 trace — October 8, 2026

The normal application made actual live Gemini calls over the synthetic
`backend/db/part2-oct8-audit.sqlite3` fixture. The final turn after both
task-owned services restarted was
`f2afaf26-5a1e-4a1c-870e-252b37e6b39c`, asking:
“Compare saved hotels near ZIP 16803 from 2026-10-11 to 2026-10-13 by total cost.”
The [complete read-only trace](assignment2-part2-stage6-trace.txt) shows the
original question, both-JOIN proposed SQL, exact bindings, direct nightly
rows, checked matches, second-model JSON, validation and displayed answer.

Campus Lantern had October 11/12 rates 12000/11000 cents with two rooms,
total 23000. Valley Ridge had 13000/14000 cents with two rooms, total 27000.
Nittany Budget was excluded because October 11 had zero rooms. Checkout
October 13 was excluded. The second live Gemini response selected
`fixture:campus` and `fixture:valley` with reason `lowest_total_cost`.
All displayed dates/rates/totals were rendered from checked records.

Live under-$50, missing October 15 and absent ZIP 16804 cases produced
distinct no-match, unknown availability and no-saved-hotel explanations.
The independent saved count remained 3 for the budget question. A separate
explicit mock filtered query returned zero candidates with saved count 3;
its answer correctly avoided claiming no hotels were saved. The
[readiness audit](assignment2-part2-stage6.md) records the exact cases,
browser behavior, regression results and limits. Provider/SQL failure mocks
are separate from these live calls.

## Historical Turn 4 preview — October 6, 2026

Observed October 6, 2026 in the ignored
`backend/db/turn4-rag-preview.sqlite3` database. This is a **live Gemini
two-call exchange over synthetic classroom records**, not a live provider
price or inventory check. Conversation ID:
`c5c401da-a312-48a1-b1ae-b798597b56fd`.

## Question and schema

Question: “What are the three cheapest available saved hotels near ZIP 16803
on October 11, 2026?” The backend parsed `postcode=16803`,
`check_in=2026-10-11`, `check_out=2026-10-12`; checkout is excluded.

The local tables are `saved_hotels(hotel_id, name, address, latitude,
longitude)`, `saved_hotel_zips(hotel_id, postcode, country_code, latitude,
longitude, locality)`, and `demo_hotel_nights(hotel_id, stay_date,
nightly_rate_cents, rooms_available)`. The first JOIN connects saved hotels to
their saved ZIP associations on `hotel_id`. The second JOIN connects those
hotels to dated simulated nights on `hotel_id`. The Assignment 1 `hotels` and
`trips` tables are separate.

## First model request and checked SQL

Gemini proposed the following SQL. The backend accepted it only as a source
of candidate hotel IDs and separately checked ZIP association, date coverage,
rooms, and totals using trusted SQL.

```sql
SELECT DISTINCT h.hotel_id AS hotel_id
FROM saved_hotels AS h
JOIN saved_hotel_zips AS z ON z.hotel_id = h.hotel_id
LEFT JOIN demo_hotel_nights AS n ON n.hotel_id = h.hotel_id
  AND n.stay_date >= :check_in AND n.stay_date < :check_out
WHERE z.postcode = :postcode
```

Bindings were `16803`, `2026-10-11`, and `2026-10-12` for `postcode`,
`check_in`, and `check_out`. The saved proposal, attempted execution, and
result trace stages have prompt version 3. The subsequent two-night exchange
after a prompt refinement has version 4.

| Direct SQLite row for October 11 | Rate | Rooms | Checked result |
| --- | ---: | ---: | --- |
| Nittany Budget | 10000 cents | 0 | Excluded: zero rooms |
| Campus Lantern | 12000 cents | 2 | Eligible: $120 one-night total |
| Valley Ridge | 13000 cents | 2 | Eligible: $130 one-night total |

The checked result contained Campus Lantern and Valley Ridge in total-price
order. The second Gemini request received the original question and these
bounded checked rows, plus counts for excluded candidates. Its streamed
answer named the two eligible hotels at $120 and $130, explained that fewer
than three were verified available, and labeled rates and room counts as
simulated classroom data. The answer matched the direct SQLite rows above.

The follow-up “For the same ZIP and dates, which one costs less?” reused the
stored stay context and identified Campus Lantern as $10 cheaper. A ZIP 16804
question returned no saved matches. An October 15 question found three ZIP
candidates but no nightly records, so availability could not be verified.
For check-in October 11 and checkout October 13, the live answer totaled
Campus Lantern at $230 and Valley Ridge at $270 from the October 11–12 rows.
The final browser check asked for October 12 alone and returned Nittany Budget
at $90, Campus Lantern at $110, and Valley Ridge at $140, all with two
simulated rooms. A direct read-only SQLite query returned the same three
nightly rows in that price order, and the browser console had no warnings or
errors.

Closing and reopening the popup, refreshing the page, and restarting the
task-owned backend preserved the conversation. A missing-ZIP question saved
the user message and an error trace without a successful assistant message.
SQL rejection and interrupted-stream behavior were checked with mocks in
temporary databases, not by asking the live model to produce a destructive
query. No live provider inventory, booking action, or other ZIP coverage was
verified.

## Turn 5 integrated proof — October 6, 2026

The first saved conversation has one `chat_conversations` row. A read-only
inspection found the first user and assistant messages with UTC timestamps and
three ordered retrieval stages: `proposal`, `execution`, and `result`. The
first proposal used both hotel JOINs above and exact binds for ZIP 16803,
October 11 check-in, and October 12 checkout. The `result` stage recorded
three candidate IDs, two checked matches (`fixture:campus` and
`fixture:valley`), and one unavailable ID (`fixture:budget`). The direct
two-JOIN query returned Budget at 10000 cents with zero rooms, Campus at
12000 cents with two rooms, and Valley at 13000 cents with two rooms. The
answer named the two available hotels and their matching prices.

| Fresh live Gemini browser question | Saved proposal binds | Checked result | Direct SQLite comparison |
| --- | --- | --- | --- |
| ZIP 16804, October 12 | `16804`, `2026-10-12`, `2026-10-13` | Zero candidates and matches; answer says no hotel is saved for this ZIP | Zero ZIP associations and zero joined night rows |
| ZIP 16803, October 15 | `16803`, `2026-10-15`, `2026-10-16` | Three candidates, zero matches, three incomplete; answer says availability cannot be verified | Three ZIP associations and zero joined night rows |

These are live model calls against the **ignored synthetic preview database**.
No provider room inventory was queried. The [question screen](test-screenshots/part2-rag-question.jpg)
and [price screen](test-screenshots/part2-rag-prices.jpg) show the October 12
success check; [no match](test-screenshots/part2-rag-no-match.jpg) and
[missing nights](test-screenshots/part2-rag-missing-night.jpg) show the two
changed-input checks. The browser warning/error log was empty.

For the disallowed-query proof, a separate temporary SQLite database held a
synthetic `fixture:proof` hotel. The retrieval controller rejected
`UPDATE saved_hotels SET name='Changed' WHERE hotel_id='fixture:proof'` with
“Proposed SQL must start with SELECT.” The name was `Proof Hotel` both before
and after the attempt, and `PRAGMA foreign_key_check` found no violations.
The temporary database was discarded. The broader parameterized rejection
tests also cover multiple statements, unapproved tables, SQL functions,
row limits, and execution-time limits.

The task-owned backend on port 8001 was stopped and restarted against the
same ignored preview database. After a browser reload, reopening the chat
restored the same saved questions and answers, including both changed-input
checks. The [post-restart screen](test-screenshots/part2-rag-history-after-restart.jpg)
shows the restored conversation. Earlier missing-context failures remain
recorded as user messages and error stages, with no successful assistant
message for those turns. `PRAGMA foreign_key_check` returned no violations.

## Reproducible clean fixture demo

The [fixed JSON fixture](part2-rag-fixture.json) and
`backend.prepare_rag_demo` create a new ignored database without replacing
the default runtime database. A fresh run created
`backend/db/part2-submission-demo.sqlite3` with schema version 7, three saved
hotels, three ZIP links, six nights, and no foreign-key violations. A second
preparation attempt refused the existing output. Running the checked
retrieval controller against this database produced the expected $120/$130
one-night result, $230/$270 two-night result, empty ZIP 16804 result, and
three incomplete candidates for October 15.

The fresh live browser question was “Show the three cheapest saved hotels
near ZIP 16803 with at least one room available for October 11, 2026.” Its
conversation ID is `3194b644-e677-4461-89ec-7bb08c7c4a84`, with user and
assistant messages under one turn ID and UTC timestamps. Prompt version 4
was recorded for the `proposal`, `execution`, and `result` stages. Gemini
proposed the same two-JOIN SQL shown above with binds `16803`,
`2026-10-11`, and `2026-10-12`. The checked result stored three candidate
IDs, Campus Lantern at 12000 cents and Valley Ridge at 13000 cents as
matches, and Nittany Budget in `unavailable_ids`. The second model request
streamed a response naming Campus at $120 and Valley at $130, each with two
simulated rooms. The [question frame](test-screenshots/part2-rag-clean-question.jpg)
and [answer frame](test-screenshots/part2-rag-clean-demo.jpg) show the clean
demonstration. Its browser warning/error log was empty.
