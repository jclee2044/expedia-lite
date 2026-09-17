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
- SQLite foreign keys enforce these references in addition to controller checks.

## Controller contracts

### Search

- **Input:** a hotel-name query and an open SQLite connection.
- **Work:** trim and validate the query, read matching joined hotel/trip rows, and calculate nights and prices.
- **Output:** `HotelSearch` containing `HotelStay` read models.
- **Failure:** blank input raises `SearchValidationError`; no match is a successful empty result.

### Create booking

- **Input:** an existing `user_id`, existing `trip_id`, and an open connection.
- **Work:** begin one write transaction, check both references, allocate the next durable ID, insert a confirmed booking, and commit.
- **Output:** the saved `BookingDetail`, including its server-issued ID and date.
- **Failure:** a missing reference raises `RecordNotFoundError`; the transaction rolls back, creates no record, and consumes no ID.

### Read booking or history

- **Input:** a booking ID or user ID and an open connection.
- **Output:** a joined `BookingDetail` or `BookingHistory`. An existing user with no bookings receives an empty history.
- **Failure:** an unknown booking or user raises `RecordNotFoundError`.

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
