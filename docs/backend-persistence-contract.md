# Expedia Lite backend persistence contract

This document defines the backend contract for the SQLite milestone. It is an
implementation contract, not a claim that the behavior is already available.
The implementation must keep framework-free persistence and business logic
separate from FastAPI routes.

Implementation status after Turn 5: the complete backend contract is
implemented and verified through automated tests and two live Uvicorn runs
against the same temporary SQLite database. Creation, cancellation, deletion,
history, search, error responses, restart persistence, and non-reused IDs were
observed over HTTP. Frontend booking/history work is a separate later
milestone.

## Scope

- The four supplied CSV files are immutable seed inputs.
- Hotels, trips, users, and bookings are copied into SQLite exactly once.
- After initialization, every application read and write uses SQLite.
- Hotels, trips, and users are read-only reference data through the public API.
- Bookings support create, retrieve, status update, and delete operations.
- Cancelling a booking preserves it with `status = "cancelled"`; deleting a
  booking removes it.
- Authentication, payments, room inventory, and duplicate-booking prevention
  are outside this milestone.

This scope supports the assignment's two flows: select a seeded stay and create
a simulated booking, then retrieve that booking in a traveler's history.

## Runtime database

The default database file will be
`backend/instance/expedia_lite.sqlite3`. The `backend/instance/` directory and
SQLite runtime files must be ignored by Git. Tests must supply a temporary
database path and must not read or write the default runtime database.

Every connection must:

- enable `PRAGMA foreign_keys = ON`;
- use named-row access;
- commit successful writes and roll back failed writes; and
- be closed by the code that opened it.

SQLite access will use Python's standard-library `sqlite3` module. No database
server, ORM, or migration package is required for this milestone.

## Schema version 1

### `hotels`

| Column | SQLite representation | Rules |
| --- | --- | --- |
| `hotel_id` | `TEXT` | Primary key; preserve values such as `H001` |
| `hotel_name` | `TEXT` | Required and non-blank |
| `city` | `TEXT` | Required and non-blank |
| `state` | `TEXT` | Required and non-blank |
| `nightly_rate_cents` | `INTEGER` | Required and non-negative |

The CSV's `nightly_rate_usd` value is converted to integer cents during
seeding. API responses continue to expose `nightly_rate_usd` as a JSON number.

### `trips`

| Column | SQLite representation | Rules |
| --- | --- | --- |
| `trip_id` | `TEXT` | Primary key; preserve values such as `T001` |
| `hotel_id` | `TEXT` | Required foreign key to `hotels.hotel_id` |
| `trip_name` | `TEXT` | Required and non-blank |
| `check_in` | `TEXT` | Required ISO date, `YYYY-MM-DD` |
| `check_out` | `TEXT` | Required ISO date later than `check_in` |

### `users`

| Column | SQLite representation | Rules |
| --- | --- | --- |
| `user_id` | `TEXT` | Primary key; preserve values such as `U001` |
| `display_name` | `TEXT` | Required and non-blank |

The seeded users are synthetic traveler choices, not authenticated accounts.

### `bookings`

| Column | SQLite representation | Rules |
| --- | --- | --- |
| `booking_id` | `TEXT` | Primary key; preserve values such as `B001` |
| `user_id` | `TEXT` | Required foreign key to `users.user_id` |
| `trip_id` | `TEXT` | Required foreign key to `trips.trip_id` |
| `booked_on` | `TEXT` | Required ISO date, `YYYY-MM-DD` |
| `status` | `TEXT` | Required; `confirmed` or `cancelled` |

Hotels, trips, and users cannot be deleted through the public API. This keeps
booking foreign keys stable. Multiple bookings for the same user and trip are
allowed because the project requirements do not define inventory or a
duplicate-booking restriction.

### Initialization metadata

The database also contains:

- `app_metadata(key TEXT PRIMARY KEY, value TEXT NOT NULL)` for
  `schema_version` and `seed_version`; and
- `id_counters(entity TEXT PRIMARY KEY, last_value INTEGER NOT NULL)` for
  durable public-ID assignment.

Schema version 1 starts the booking counter at the greatest numeric suffix in
the seeded booking IDs, which is `6`. Creating a booking increments the counter
inside the same write transaction and formats the result as `B007`, `B008`, and
so on. Deleting a booking never decrements the counter, so an issued ID is not
reused.

## One-time initialization

Initialization runs before application requests are served:

1. Create the schema and metadata tables when they do not exist.
2. If `seed_version = 1` is present, do not read any seed CSV.
3. If no seed marker exists and all four domain tables are empty, validate all
   four CSV files and insert every record in one transaction.
4. Initialize the booking counter and write the seed marker in that same
   transaction.
5. If the marker is absent but any domain table already contains data, stop
   with an initialization error instead of merging or overwriting records.

The transaction must roll back completely when any CSV record is invalid or a
foreign key cannot be resolved. Restarting the application must not duplicate
starter records, restore deleted records, undo status changes, or remove new
bookings.

## Derived values and ordering

The database stores source facts, not redundant totals:

- `nights` is `check_out - check_in` in calendar days;
- `nightly_rate_usd` is `nightly_rate_cents / 100`; and
- `stay_price_usd` is `nightly_rate_cents * nights / 100`.

Hotel search remains a trimmed, case-insensitive partial match on
`hotel_name`. Results are ordered by `trip_id`, which preserves the supplied
starter ordering. Booking history is ordered by `booked_on` descending, then
`booking_id` descending, so recent records appear first deterministically.

## HTTP and JSON contract

The current `GET /api/hotels/search?name=...` contract remains unchanged. Its
implementation will move from per-request CSV reads to SQLite queries.

### List users

`GET /api/users` returns status `200`:

```json
{
  "users": [
    {
      "user_id": "U001",
      "display_name": "Demo Traveler 1"
    }
  ]
}
```

Users are ordered by `user_id`.

### Create a booking

`POST /api/bookings` accepts:

```json
{
  "user_id": "U006",
  "trip_id": "T001"
}
```

The backend assigns the next booking ID, the server's current local calendar
date, and `confirmed` status. It returns status `201` with a booking detail
response.

### Retrieve a booking

`GET /api/bookings/{booking_id}` returns status `200` with a booking detail
response.

### Retrieve booking history

`GET /api/users/{user_id}/bookings` returns status `200`:

```json
{
  "user": {
    "user_id": "U001",
    "display_name": "Demo Traveler 1"
  },
  "booking_count": 1,
  "bookings": [
    {
      "booking_id": "B001",
      "user_id": "U001",
      "display_name": "Demo Traveler 1",
      "trip_id": "T001",
      "trip_name": "Boston Harbor Weekend",
      "hotel_id": "H001",
      "hotel_name": "Harbor Lantern Hotel",
      "city": "Boston",
      "state": "MA",
      "check_in": "2026-09-18",
      "check_out": "2026-09-20",
      "nights": 2,
      "nightly_rate_usd": 150.0,
      "stay_price_usd": 300.0,
      "booked_on": "2026-09-01",
      "status": "confirmed"
    }
  ]
}
```

An existing user with no bookings receives `booking_count: 0` and an empty
`bookings` list. An unknown user receives `404`.

### Update booking status

`PATCH /api/bookings/{booking_id}` accepts exactly the mutable field:

```json
{
  "status": "cancelled"
}
```

Both defined statuses are accepted, making the operation an explicit status
update rather than a special delete operation. The route returns status `200`
with the updated booking detail response.

### Delete a booking

`DELETE /api/bookings/{booking_id}` removes the record and returns status
`204` with no response body. A subsequent retrieval returns `404`.

### Booking detail response

Create, retrieve, and update routes return the joined booking object shown in
the history example. This gives the future frontend the traveler, trip, hotel,
date, status, and derived price information needed for confirmation and
history views without additional client-side joins.

## Error behavior

- Missing users, trips, or bookings return `404` without exposing SQL details.
- Malformed request bodies and unsupported status values return FastAPI's
  `422` validation response.
- A blank hotel search retains the existing `400` response and message.
- A valid hotel search with no matches retains the existing `200` empty result.
- Unexpected database or initialization failures return a generic `500`
  response and retain their underlying exception for server-side diagnosis.

## Backend acceptance criteria

- Initial counts are 8 hotels, 12 trips, 6 users, and 6 bookings.
- Initializing the same database repeatedly does not change those records.
- Search results for `Harbor`, `CAPITOL`, `hotel`, and an unknown name match
  the existing documented screenshots and API response structure.
- Demo Traveler 1 initially has bookings `B001` and `B002`; Demo Traveler 6
  initially has an empty history.
- The first created booking is `B007` and survives closing and reopening the
  database.
- Cancelling preserves the booking in history; deleting removes it.
- A deleted ID is not issued again.
- Tests use temporary database files and do not mutate the runtime database or
  seed CSV files.
