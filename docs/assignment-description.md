# Assignment 1 — Travel Application: CSV Search and SQLite CRUD

Adapt the course calculator project into a small local travel application.
Expedia Lite is a suggested name; students may choose any application name.
Use the chosen name consistently in the project folder, interface, and
documentation. Each student submits an independently authored project.

Use Vue for the frontend, Python for the backend, and FastAPI for communication
between them, with separate `frontend/` and `backend/` folders. A simple,
readable interface is sufficient. Use the supplied demo travelers and
simulated bookings; the scope is hotel stays, booking, and history.

## Requirements and submission checkpoints

| Checkpoint | Part 1 — CSV Search | Part 2 — SQLite CRUD |
| --- | --- | --- |
| Due | Friday, September 11, 2026, at 11:59 PM ET. | Monday, September 21, 2026, at 11:59 PM ET. |
| Application behavior | Provide a search input for a hotel name and a Search button. Display matching hotels and their available stays from the supplied data in a plain table with clear column labels. Show a clear message when no results match. | Improve the interface's appearance and usability using the UI research approach in In-class Activity 2: UI Research. Provide search, simulated booking, and booking history. All CRUD actions must be performed through the frontend: create a new booking, read it in history, update its status to cancel it while retaining the record, and delete a test booking. |
| Data | The Python backend reads `hotels.csv` and `trips.csv` and connects their records using `hotel_id`. FastAPI returns the matching records to the Vue frontend. | Seed a SQLite database with the supplied hotel, trip, user, and booking records. This is the initial data, not a fixed limit on the application's contents. After seeding, all application reads and writes use SQLite. Frontend actions send requests through FastAPI to the Python backend, which creates, retrieves, updates, and deletes the stored records. Users can add new bookings beyond the seeded examples. Preserve existing IDs and assign unique IDs to new records. Implement CRUD using the Model–View–Controller architecture discussed in class: Models hold the data and relationships, the View presents the interface, and a database controller performs CRUD operations. |
| Bonus (optional) | Not applicable. | Add functional demo user authentication and surge-pricing business logic, following In-class Activity 3: Accounts and Personalized Pricing. |
| Verification | Manually scan the changes in VS Code. Check a successful search using a hotel name from the supplied data and a search with no results in the browser. Record expected and observed results. | Manually scan the changes in VS Code. Demonstrate each CRUD action through the frontend, including records added after seeding. Verify that additions, updates, and deletions remain after a browser refresh and restarting the frontend and backend. Starting the app again must preserve saved changes without duplicating or reloading the starter records. |
| Git checkpoint | Ask the agent to commit the reviewed work, push it to GitHub, and identify the exact Part 1 commit. | Develop substantial changes on a feature branch. Merge reviewed and checked work into `main`, check the combined app, and push the final commit. Preserve the Part 1 checkpoint. |
| Submission | Upload `report.md` to Part 1 — Submission. | Upload the updated `report.md` to Part 2 — Submission. |
| Project context for both parts | Keep `README.md` setup/run instructions, project-specific `AGENTS.md`, a brief design note in `docs/`, selected prompts in `prompts/`, and `handoffs/current.md` current. The design note explains frontend, FastAPI, and backend responsibilities. The handoff states what works, what was checked, remaining limitations, and the next task. Keep these files concise and consistent with the submitted commit. | Same requirements as Part 1. |

Each part is worth 100 points, with equal weight in the 10% Assignment 1
group. Assessment follows the requirements and verification evidence in this
table. The overview is not a separate submission.

Follow CHECK → TAKE ACTION → VERIFY when adding dependencies, as practiced in
class.

## Report format

For each part, upload a single file named `report.md`. Write actual Markdown
with one level 1 heading (`#`) for the report title and level 2 headings (`##`)
for its sections. Use this structure, replacing the bracketed text and the part
number:

```markdown
# [Chosen application name] — Part 1

## Repository and commit

[GitHub repository URL and the exact commit submitted for this part.]

## Implementation

[Briefly explain the implemented flow and the responsibilities of the frontend,
FastAPI, and backend. For Part 2, summarize the changes since Part 1.]

## Verification

[Record the manual review and browser checks: action, expected result, and
observed result. Embed or link screenshots stored in the repository using URLs
the instructor can access.]

## Project context and next steps

[Link to the README, AGENTS.md, design note, selected prompts, and current
handoff. State any remaining limitations and the next task.]
```

For Part 2, use the Part 2 title and everything in the Part 1 report structure,
plus a demo video under three minutes showing a user interacting with the
application.

Use Upload on the appropriate submission page, attach `report.md`, and select
Submit Assignment. Keep the report and its screenshots in the repository and
ensure that the instructor can access every linked item.

## Sample data

Download the instructor's sample travel data pack: `hotels.csv`, `trips.csv`,
`users.csv`, and `bookings.csv`. A trip is one offered hotel stay with fixed
dates. Each trip refers to one hotel through `hotel_id`; each booking refers to
a demo traveler through `user_id` and a trip through `trip_id`. Every record
also has its own unique ID. Several trips can reference the same hotel, and
several bookings can reference the same traveler or trip.
