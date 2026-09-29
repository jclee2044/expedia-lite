# Expedia Lite — Part 2

## Repository and commit

Repository: [https://github.com/jclee2044/expedia-lite](https://github.com/jclee2044/expedia-lite)

- Preserved Part 1 checkpoint: `a67b2e1fe9c699ad0dddfd0441ac429520b4616f`
- Final Part 2 checkpoint: `ddb02a09986a5bbdb6c2d7730c22eff5426704ec`

## Implementation

In Part 1, the bare-bones Vue search interface and CSV-backed hotel/booking data were established. Part 2 builds on top of that search experience with a more "Expedia-esque" UI, account creation and login, simulated booking, cancellation, and guarded permanent deletion.

Below are the specific changes since Part 1:
- Built out the full user interface
- Added complete frontend booking CRUD
- Moved app data to SQLite (one-time CSV seeding)
- Refactored the codebase to match MVC
- Added functionality of account creation and login/logout
- Added personalized search pricing (price gauging)


The application was designed to follow the Model–View–Controller (MVC) design pattern. The Vue frontend is the View and calls documented FastAPI endpoints. FastAPI routes conduct HTTP validation and delegate behavior to the Controllers. Controllers, in turn, use Python and SQLite to do search, pricing, account, booking, and database rules.

Booking prices are calculated by the backend from the signed-in user's search history. A booking snapshots the effective nightly rate shown for that search, so its confirmation and history total remain consistent even if later searches change the current offer.

## Verification

### Search and effective pricing

When the user searches for "Valley Trail" four times while signed in:
- Expected: Searches one through three show $100 per night; the fourth shows the adjusted price of $120 per night and $240 for two nights.
- Observed: Searches 1, 2, and each showed $100 for one night and $200 for two; the fourth search showed $120 per night and $240 total.

![Fourth Valley Trail search showing the effective price](docs/test-screenshots/part2-search-results.png)

### Create and read a booking

When the user books the displayed Valley Trail stay and opens My trips:
- Expected: The confirmation and history show all the confirmation information, including the ID, "confirmed" status, hotel, stay, dates, and the $240 total.
- Observed: Booking B015 was created as confirmed at $120 per night and $240 total, then was shown in the history with details that all matched.

![Booking confirmation preserving the searched price](docs/test-screenshots/part2-booking-confirmation.png)

### Update and delete a booking

The user cancels B015, then permanently deletes it.
- Expected: Cancellation keeps the record in view, just showing as cancelled. A confirmation message is displayed before permanent deletion, then that record is destroyed.
- Observed: B015 remained in the list after cancellation. After it was deleted, the page no longer showed B015.

![Cancelled booking retained in history](docs/test-screenshots/part2-booking-cancelled.png)

![History after permanent deletion of the test booking](docs/test-screenshots/part2-booking-deleted.png)

### Empty and error states

- Action: Search for nonexistent.
- Expected: No cards appear and the page gives a clear no-results message.
- Observed: The page reported zero matching hotels and suggested a different search.

![No-results state](docs/test-screenshots/part2-no-results.png)

Automated verification also passed on 2026-09-21, see below:

- 85 backend tests
- 10 frontend API-contract tests
- frontend lint
- frontend production build (20 transformed modules)

## Project context and next steps

The assignment requirements were all satisfied and the project is ready to be submitted.

The application includes the improved interface, SQLite persistence, complete booking CRUD functionality, unique record IDs, and the required MVC organization.

The optional account authentication and personalized pricing features are also complete.

Automated tests, frontend linting, the production build, and browser testing all passed successfully.

The README, design documentation, verification guide, screenshots, selected prompts, and current handoff have also been updated to reflect the finished application.

Demonstration video: [Expedia Lite Demo](<Expedia Lite Demo.mp4>)

## Assignment 2 — Part 1 working record (2026-09-29)

The current `zip-search` work adds a live Geoapify hotel search around the
resolved point of a five-digit U.S. ZIP. The hotel list and Leaflet map share
selection. The research decisions and implementation-time mockup are in
[Part 1 design notes](docs/assignment2-part1-notes.md). The sketch was not
prepared before implementation, so it does not fully meet that timing criterion.

Configuration: put `GEOAPIFY_API_KEY` in the ignored project-root `.env` and
start the backend and frontend using the README commands. Leaflet uses
OpenStreetMap tiles and requires no separate key. No live place data is treated
as evidence of prices or bookable rooms.

Verification input: ZIP `16802`, observed on 2026-09-29. Expected: an exact
U.S. ZIP center, hotel places within a 5 km circle, and a matching list and map.
Observed: the local API returned HTTP 200 with the requested center and 21
provider places; the browser displayed 21 entries, markers, the radius circle,
and tile attribution. Keyboard selection from the list selected a marker, and
selection from a marker selected the corresponding list item. The live count is
an observation, not a fixed expectation. Mocked backend tests cover the provider
request, validation, empty results, and failure handling; frontend API tests
cover the proxied request.

AI evidence: Codex (GPT-6) inspected the existing project, compared Geoapify
and Leaflet documentation, and implemented the request beginning “implement the
plan please.” The ZIP-only lookup was extended to one search flow that resolves
the ZIP and requests nearby places. An early browser click did not submit the
form; keyboard submission then verified the running flow. No credentials were
included in prompts, tests, or this report.

Before submission: add the assessed commit and repository link for this part,
record a screen demonstration, and confirm whether the course accepts the
implementation-time sketch despite the pre-implementation mockup requirement.
