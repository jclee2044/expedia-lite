# Assignment 2 Part 2 — revised requirements (October 1, 2026)

This records the revised brief supplied for this project on October 6, 2026.
It supersedes the Part 2 scope and October 6 deadline in
[`assignment2-description.md`](assignment2-description.md). The original
assignment's research, early mockup, report, demonstration, and verification
requirements still apply. The separately supplied, more detailed chatbot
tutorial is preserved in
[`assignment2-part2-instructor-chatbot-notes.txt`](assignment2-part2-instructor-chatbot-notes.txt).

## Objective and endpoint

Continue from the October 1 local-storage tutorial checkpoint. Add business
intelligence to the Part 1 app through a RAG-based LLM chatbot. Full credit
requires the complete **question → proposed SQL → checked backend retrieval →
second LLM request with retrieved records → grounded frontend answer** flow.
The in-class activity and its graded companion have their own mandatory
stopping point; Part 2 goes beyond that point.

Part 2 is worth 100 points and is due **Thursday, October 8, 2026, at
11:59 PM Eastern** (extended from Tuesday, October 6). The [local-storage
tutorial](https://psu.instructure.com/courses/2484533/pages/in-class-activity-local-hotel-storage-and-manual-verification)
and [graded companion](https://psu.instructure.com/courses/2484533/assignments/18765499)
are the stated foundation. Their linked pages have not been independently
verified in this planning pass.

## Functional requirements

1. Preserve saved API hotels, ZIP/location context, and dated simulated
   nightly rates and room availability in SQLite. Preserve Add to Local,
   Remove from Local, persistence, local-first lookup, the frozen Part 1 API,
   ZIP search, linked list/map behavior, Assignment 1 tables, and supplied
   records. Label demo rates and availability as simulated course data.
2. Accept natural-language hotel search and comparison questions in a chat
   interface with loading, answer, and failure states.
3. Send the question, relevant schema, and query rules from the backend to
   **one** selected model provider. The model proposes or adjusts SQL. The
   backend validates it and executes only a bounded, read-only query over the
   approved local hotel and demo-night tables. The model never receives direct
   SQLite access.
4. Send the original question and limited retrieved records in a **second**
   model request. Require an answer grounded in those records; missing hotels,
   prices, or vacancies must not be guessed.
5. Show matching hotels, dates, costs, availability, and recommendation reasons.
   Explain no matches and insufficient data. For a multi-night stay, use the
   requested nights, exclude checkout, total the actual nightly prices, and
   never treat a missing nightly record as available.
6. Keep model requests and credentials in the backend. Chat must only retrieve
   and explain; it must not change hotel data or make bookings. SQL retrieval
   uses SQLite; a vector database is not required.

## Provider and dependency gate

Select **one** of paid OpenAI API, Gemini API, or the free Nemotron option via
OpenRouter demonstrated in class. Use the class configuration if choosing
Nemotron. Verify the selected model's current availability and usage limits
before integration. Before **any** dependency change, check the existing
environment, explain the exact package and installation action, obtain the
student's approval, then verify it. Preserve existing behavior.

## Demonstration and submission evidence

The report and demo must show a question, proposed query, retrieved records,
and final answer with expected-versus-observed checks. Include a successful
question, a no-match or insufficient-data case, and a blocked invalid or
disallowed query that leaves the database unchanged. Label fixtures and mocks
used for failure checks, and distinguish them from successful live model calls.
Retain the original assignment's research, early mockup, report, demonstration,
and verification requirements in
[`assignment2-description.md`](assignment2-description.md).

The supplied chatbot tutorial additionally asks for a versioned prompt in
`prompts/hotel-assistant.md`, saved conversation messages and retrieval stages,
a follow-up exchange, persisted history across refresh/restart, and
`docs/rag-context.md` with the traced SQL, rows, answer, and conversation ID.
Treat these as implementation and evidence requirements unless the instructor
clarifies otherwise. Its OpenAI-specific setup is an example; the revised
brief permits any one of the three provider choices above.
