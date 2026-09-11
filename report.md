# Expedia Lite — Part 1

## Repository and commit

GitHub repository URL: [https://github.com/jclee2044/expedia-lite](https://github.com/jclee2044/expedia-lite)

Commit ID: `71289a22a9c2112d956716e9a6567d6b4468f047`

## Implementation

The implemented flow lets a user search for hotels by name and view the matching offered stays. The Vue frontend owns the search form, loading and error states, and results table, while its request module sends the search to FastAPI. FastAPI owns the HTTP endpoint and JSON response validation, then delegates the work to framework-free Python backend logic. The backend reads `hotels.csv` and `trips.csv`, validates and joins their records through `hotel_id`, performs case-insensitive partial-name matching, and calculates the number of nights and total stay price for each result.

## Verification

When "hotel" is entered:

- Expected result: Each of the hotels appear.
- Observed result: Each of the hotels appear.

When "Harbor" or "harbor" is entered:

- Expected result: Only the Harbor Lantern Hotel appears.
- Observed result: Only the Harbor Lantern Hotel appears.

When "CAPITOL" is entered:

- Expected result: Only the Capitol Grove Hotel appears.
- Observed result: Only the Capitol Grove Hotel appears.

When "nonexistent" is entered:

- Expected result: No results are returned, and a clear message is shown that no results match.
- Observed result: No results are returned, and a clear message is shown that no results match.

## Project context and next steps

Project context is maintained in the [README](README.md), [project-specific agent instructions](AGENTS.md), [design note](docs/design-pipeline.md), [selected prompts](prompts/setup-prompts.md), and [current handoff](handoffs/current.md). The current implementation is limited to hotel search over read-only CSV data; booking creation, confirmation, booking history, SQLite initialization, and persistent storage are not yet implemented. The next task is to define the booking and persistence contract before implementing the first booking flow.
