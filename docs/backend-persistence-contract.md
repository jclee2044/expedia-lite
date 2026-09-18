# Expedia Lite backend persistence contract

This document defines the backend contract for the SQLite milestone. It is an
implementation contract, not a claim that the behavior is already available.
The implementation must keep framework-free persistence and business logic
separate from FastAPI routes.

Implementation status: the persistence contract and its schema-version-3
search-history extension are implemented. Automated tests cover account creation,
authentication, process-local sessions, booking ownership, migration,
creation, cancellation, deletion, history, search, restart persistence, and
non-reused IDs.

## Scope

- The four supplied CSV files are immutable seed inputs.
- Hotels, trips, users, and bookings are copied into SQLite exactly once.
- After initialization, every application read and write uses SQLite.
- Seeded users become demo accounts, and new accounts may be created.
- Bookings support create, retrieve, status update, and delete operations.
- Cancelling a booking preserves it with `status = "cancelled"`; deleting a
  booking removes it.
- OAuth, password hashing/recovery, payments, room inventory, and
  duplicate-booking prevention are outside this classroom milestone.

This scope supports creating or logging into an account, booking a seeded stay,
and retrieving that booking in the signed-in account's history.

## Runtime database

The default database file will be
`backend/db/expedia_lite.sqlite3`. The `backend/db/` directory and
SQLite runtime files must be ignored by Git. Tests must supply a temporary
database path and must not read or write the default runtime database.

Every connection must:

- enable `PRAGMA foreign_keys = ON`;
- use named-row access;
- commit successful writes and roll back failed writes; and
- be closed by the code that opened it.

SQLite access will use Python's standard-library `sqlite3` module. No database
server, ORM, or migration package is required for this milestone.

## Schema version 3

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
| `username` | `TEXT COLLATE NOCASE` | Required, 3–32 allowed characters, unique without regard to case |
| `password` | `TEXT` | Required 4–72 character classroom password; never returned by the API |
| `email` | `TEXT` or `NULL` | Optional syntactically checked fictional email |

Version 1 databases are migrated transactionally: the users table is rebuilt,
every existing ID and booking reference is preserved, deterministic fictional
demo credentials are assigned, metadata is advanced, and
`PRAGMA foreign_key_check` must succeed before commit.

### `search_history`

| Column | SQLite representation | Rules |
| --- | --- | --- |
| `search_id` | `INTEGER` | Auto-generated primary key |
| `user_id` | `TEXT` | Required foreign key to `users.user_id` |
| `query` | `TEXT` | Required normalized, nonblank hotel query |
| `searched_at_utc` | `TEXT` | Required aware ISO timestamp stored in UTC |

There is one shared table for all accounts. Version 2 databases migrate to
version 3 by creating this table and its `(user_id, searched_at_utc)` index;
existing users, bookings, IDs, and hotel base rates are unchanged.

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

Schema version 3 starts booking and user counters at the greatest numeric
suffix in their seeded IDs, both `6`. Creating a booking or account increments
its counter inside the same write transaction and formats the result as
`B007`/`U007` and so on. Issued IDs are never reused.

## One-time initialization

Initialization runs before application requests are served:

1. Create the schema and metadata tables when they do not exist.
2. If `seed_version = 2` is present, do not read any seed CSV.
3. If no seed marker exists and all four domain tables are empty, validate all
   four CSV files and insert every record in one transaction.
4. Initialize the booking and user counters and write the seed marker in that same
   transaction.
5. If the marker is absent but any domain table already contains data, stop
   with an initialization error instead of merging or overwriting records.

The transaction must roll back completely when any CSV record is invalid or a
foreign key cannot be resolved. Restarting the application must not duplicate
starter records, restore deleted records, undo status changes, or remove new
bookings.

## Derived values and ordering

The database stores source facts and raw history, not calculated prices or urgency totals:

- pure model logic calculates `nights` as `check_out - check_in`;
- pure model logic counts equivalent searches for the same user during the
  current `America/New_York` calendar day; and
- pure model logic returns the base rate for counts 1–3 and base × 1.20 for
  count 4 onward, rounded half-up to cents without compounding.

Hotel search remains a trimmed, case-insensitive partial match on
`hotel_name`. Results are ordered by `trip_id`, which preserves the supplied
starter ordering. Booking history is ordered by `booked_on` descending, then
`booking_id` descending, so recent records appear first deterministically.

## HTTP and JSON contract

`GET /api/hotels/search?name=...` returns base/effective prices plus a
`pricing` object containing `daily_search_count`, `multiplier`,
`adjustment_applied`, and `time_zone`. A valid session causes the normalized
nonblank query to be recorded before its frequency is measured. Guest searches
have a null count, use the base price, and do not write history.

### Accounts and login

`POST /api/accounts` accepts a username, password, and optional email. It
returns a password-free account profile with status `201` and starts a login
session. Duplicate usernames return `409` even when the capitalization differs.

`POST /api/auth/login` accepts a username and password. Invalid credentials
always return the same `401` message. `GET /api/auth/session` restores the
current password-free profile, and `POST /api/auth/logout` invalidates the
session and returns `204`.

Sessions are opaque random tokens stored in an `HttpOnly`, `SameSite=Lax`
cookie. The process-local session store keeps only user IDs, expires tokens
after eight hours, and intentionally signs everyone out after a backend
restart. Account records remain in SQLite.

### Create a booking

`POST /api/bookings` accepts:

```json
{
  "trip_id": "T001"
}
```

The backend derives `user_id` from the authenticated session, assigns the next
booking ID, the server's current local calendar date, and `confirmed` status.
It returns status `201` with a booking detail response.

### Retrieve a booking

`GET /api/bookings/{booking_id}` returns status `200` with a booking detail
response only when the current account owns it.

### Retrieve booking history

`GET /api/account/bookings` returns status `200` for the current account:

```json
{
  "user": {
    "user_id": "U001",
    "display_name": "Demo Traveler 1",
    "username": "demo_u001",
    "email": "demo_u001@example.test"
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

An account with no bookings receives `booking_count: 0` and an empty
`bookings` list. A missing session receives `401`.

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
- Missing or expired sessions return `401`; another account's booking is hidden
  behind `404`.
- Duplicate usernames return `409`; invalid credentials return a generic `401`.
- Malformed request bodies and unsupported status values return FastAPI's
  `422` validation response.
- A blank hotel search retains the existing `400` response and message.
- A valid hotel search with no matches retains the existing `200` empty result.
- Unexpected database or initialization failures return a generic `500`
  response and retain their underlying exception for server-side diagnosis.

## Backend acceptance criteria

- Initial counts are 8 hotels, 12 trips, 6 users, and 6 bookings.
- Initializing the same database repeatedly does not change those records.
- Schema versions 1 and 2 migrate to version 3 without changing user IDs,
  booking relationships, or stored hotel base rates.
- The first new account is `U007`; duplicate usernames are rejected without
  consuming an ID, and account records persist after restart.
- Login/logout and session expiration work without returning passwords.
- Search results for `Harbor`, `CAPITOL`, `hotel`, and an unknown name match
  the existing documented screenshots and API response structure.
- For a $100 base hotel, one account sees $100 for searches 1–3 and $120 from
  search 4 onward; another user, query, or application day starts at $100.
- Search history survives restart, while the stored hotel rate remains $100.
- Demo Traveler 1 initially has bookings `B001` and `B002`; Demo Traveler 6
  initially has an empty history.
- A signed-in account cannot read, cancel, or delete another account's booking.
- The first created booking is `B007` and survives closing and reopening the
  database.
- Cancelling preserves the booking in history; deleting removes it.
- A deleted ID is not issued again.
- Tests use temporary database files and do not mutate the runtime database or
  seed CSV files.
