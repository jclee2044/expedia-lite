# Expedia Lite MVC contracts

## Boundaries

- **View:** `frontend/` displays data, captures user actions, and calls the documented JSON API. It does not read SQLite or enforce backend business rules.
- **Models:** `backend/models/` defines entity fields, read projections, table constraints, and relationships. Models do not depend on FastAPI or Controllers.
- **Controllers:** `backend/controllers/` validates business input, performs database operations and transactions, and returns Model objects or framework-independent errors.
- **HTTP adapter:** `backend/app/` validates request/response JSON, calls Controllers, and translates known errors into HTTP status codes.

```text
Vue View -> FastAPI route -> business Controller -> database Controller
                                                    |
                                                    v
                                               Models/SQLite
```

## Relationships

- `Trip.hotel_id` references `Hotel.hotel_id`.
- `Booking.user_id` references `User.user_id`.
- `Booking.trip_id` references `Trip.trip_id`.
- `SearchHistory.user_id` references `User.user_id`.
- SQLite foreign keys enforce these references in addition to controller checks.

`User.username` is case-insensitively unique. `AccountProfile` is the safe,
password-free projection exchanged outside persistence code.

## Controller contracts

### Search and personalized pricing

- **Input:** a hotel-name query, an open SQLite connection, and an optional authenticated user ID.
- **Database controller:** inserts a normalized query and UTC timestamp and returns raw history/stay rows. It performs no frequency count, multiplier choice, or price arithmetic.
- **Search controller:** rejects blank input, coordinates one authenticated write/read transaction, and delegates calculations.
- **Urgency controller:** maps raw rows to `SearchHistory` records and invokes the model frequency calculation.
- **Pricing controller:** maps a joined stay row to `HotelStay` and invokes model calculations for nights and prices.
- **Model:** normalizes query text, derives `America/New_York` day boundaries, counts same-user/same-query records, chooses either 1.00 or 1.20, and calculates effective prices from immutable base cents.
- **Output:** `HotelSearch` containing shared `SearchPricing` metadata and priced `HotelStay` read models.
- **Failure:** blank input raises `SearchValidationError`; no match is a successful empty result.

### Create account and authenticate

- **Create input:** username, plaintext classroom password, optional email, and an open connection.
- **Create work:** normalize and validate input, begin one write transaction, enforce case-insensitive username uniqueness, allocate the next durable user ID, insert the account, and commit.
- **Authenticate input:** username, password, and an open connection.
- **Output:** a password-free `AccountProfile`.
- **Failure:** invalid fields, duplicate usernames, and invalid credentials use distinct framework-free errors. Authentication never reveals whether the username or password failed.

### Track the current account

- **Input:** an opaque session token generated with the Python standard library.
- **Work:** store only the user ID, expire the token after eight hours, and invalidate it on logout. Sessions are process-local and are cleared by a backend restart.
- **HTTP boundary:** FastAPI alone reads and writes the `HttpOnly`, `SameSite=Lax` cookie.

### Create booking

- **Input:** the authenticated session's `user_id`, an existing `trip_id`, optional search context, and an open connection.
- **Work:** begin one write transaction, check both references, validate the trip against the submitted search, derive the effective quote from that account's recorded searches, allocate the next durable ID, snapshot the quoted nightly rate, insert a confirmed booking, and commit. Direct API calls without search context use the stored base rate.
- **Output:** the saved `BookingDetail`, including its server-issued ID and date.
- **Failure:** a missing reference raises `RecordNotFoundError`; the transaction rolls back, creates no record, and consumes no ID.

### Read booking or history

- **Input:** a booking ID or the authenticated session's user ID and an open connection.
- **Output:** a joined `BookingDetail` or `BookingHistory`. An existing user with no bookings receives an empty history.
- **Failure:** an unknown booking, user, or booking owned by another account raises `RecordNotFoundError`.

### Update booking

- **Input:** a booking ID and `confirmed` or `cancelled` status.
- **Work:** update the persisted status in one transaction.
- **Output:** the updated `BookingDetail`.
- **Failure:** an unknown booking or unsupported status changes no record.

### Delete booking

- **Input:** a booking ID and an open connection.
- **Work:** permanently delete that record in one transaction.
- **Output:** no model; the HTTP adapter returns `204`.
- **Failure:** an unknown booking raises `RecordNotFoundError`. Allocated IDs are never reused.
