# Expedia Lite design pipeline

Expedia Lite implements SQLite-backed hotel search, synthetic traveler
selection, booking creation, confirmation, history, cancellation, and deletion
end to end.

## Responsibilities

- **Vue frontend:** `frontend/src/App.vue` owns the search, traveler, booking, history, and mutation state. `frontend/src/components/StayCard.vue`, `BookingConfirmation.vue`, and `BookingHistory.vue` own the reusable presentation structures identified in the visual references, while `frontend/src/assets/main.css` provides the responsive interface system. The modules in `frontend/src/api/` own HTTP requests. Vite proxies `/api` to FastAPI during development.
- **FastAPI boundary:** `backend/app/main.py` initializes the configured SQLite database before serving requests, exposes search, user, booking, and history routes, provides request-scoped database connections, translates domain/database errors into HTTP responses, and validates JSON with `backend/app/schemas.py`.
- **Python backend:** `backend/app/database.py` and `backend/app/seed.py` own SQLite connections, schema creation, seed validation, and one-time import. `backend/app/search.py` queries joined hotel and trip rows. `backend/app/bookings.py` owns user lookup, joined history, and transactional booking create, status-update, and delete behavior. These modules do not depend on FastAPI.

## Data flow

```text
search form -> frontend request module -> FastAPI route
            -> Python SQLite/search logic -> response schema
            -> JSON -> Vue stay cards
```

The CSV files are read-only starter data. FastAPI seeds them into SQLite on the
first startup for a database path and uses SQLite thereafter. Authentication
is outside scope. All frontend booking actions cross the FastAPI boundary and
refresh their displayed state from SQLite-backed responses.

## Booking and history data flow

```text
Vue stay-card action -> FastAPI booking route -> framework-free booking service
                  -> SQLite transaction/query -> joined response schema
                  -> Vue confirmation view

Vue My trips view -> FastAPI traveler-history route -> joined SQLite query
                  -> populated, empty, loading, or error history state
```

Creating a booking validates the selected seeded user and trip, advances the
durable booking ID counter, and inserts a confirmed row in one transaction.
History joins bookings to users, trips, and hotels. Cancellation updates the
stored status while deletion removes the booking, matching the distinction in
the sample-data guide.

## Approved backend persistence milestone

The current milestone has a defined backend contract in
[`backend-persistence-contract.md`](backend-persistence-contract.md). The
implemented foundation validates and imports all four CSV files into SQLite
exactly once. It also provides schema metadata, foreign-key enforcement, and a
durable booking-ID counter. Hotels, trips, and users are read-only reference
data through the API; bookings support create, retrieve, status-update, and
delete behavior.

```text
CSV seed files --one-time import--> SQLite
                                      ^
                                      |
Vue -> FastAPI -> framework-free repositories and booking logic
```

The existing hotel-search response stayed stable while its data source moved
from CSV reads to SQLite. Booking detail and history responses join booking,
user, trip, and hotel data and calculate nights and stay price in the backend.
The SQLite schema, seeding layer, application startup integration, hotel
search, user lookup, booking CRUD, joined history routes, and corresponding Vue
flows are implemented and tested.
