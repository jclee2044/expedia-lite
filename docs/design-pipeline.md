# Expedia Lite design pipeline

Expedia Lite implements SQLite-backed hotel search, synthetic traveler
selection, booking creation, confirmation, history, cancellation, and deletion
end to end.

## Responsibilities

- **Vue frontend:** `frontend/src/App.vue` owns the search, traveler, booking, history, and mutation state. `frontend/src/components/StayCard.vue`, `BookingConfirmation.vue`, and `BookingHistory.vue` own the reusable presentation structures identified in the visual references, while `frontend/src/assets/main.css` provides the responsive interface system. The modules in `frontend/src/api/` own HTTP requests. Vite proxies `/api` to FastAPI during development.
- **View:** `frontend/src/App.vue` owns screen state and user actions. Components own reusable presentation, CSS owns responsive styling, and `frontend/src/api/` owns JSON requests.
- **FastAPI boundary:** `backend/app/main.py` composes the application and initializes SQLite. `backend/app/routes.py` exposes thin search, user, booking, and history routes, supplies request-scoped connections, and translates controller errors. `backend/app/schemas.py` validates the public JSON contract.
- **Models:** `backend/models/entities.py` defines framework-free Hotel, Trip, User, Booking, search, detail, and history objects. `backend/models/schema.py` defines their SQLite fields, constraints, and foreign-key relationships.
- **Controllers:** `backend/controllers/database.py` owns connections and database operations; `seed.py` owns initial CSV validation/import; `search.py`, `users.py`, and `bookings.py` own their business operations. Controllers return Models and never raise FastAPI exceptions.

The enforced dependency direction is `View -> FastAPI routes -> Controllers -> Models/SQLite`. Models do not import FastAPI or Controllers. Detailed contracts are recorded in [`mvc-contracts.md`](mvc-contracts.md).

## Data flow

```text
search form -> frontend request module -> FastAPI route
            -> search controller -> database controller -> Models/SQLite
            -> response schema
            -> JSON -> Vue stay cards
```

The CSV files are read-only starter data. FastAPI seeds them into SQLite on the
first startup for a database path and uses SQLite thereafter. Authentication
is outside scope. All frontend booking actions cross the FastAPI boundary and
refresh their displayed state from SQLite-backed responses.

## Booking and history data flow

```text
Vue stay-card action -> FastAPI booking route -> booking controller
                  -> database controller transaction -> Booking model
                  -> joined response schema
                  -> Vue confirmation view

Vue My trips view -> FastAPI traveler-history route -> user controller
                  -> database controller joined query
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
Vue -> FastAPI routes -> Controllers -> Models/SQLite
```

The existing hotel-search response stayed stable while its data source moved
from CSV reads to SQLite. Booking detail and history responses join booking,
user, trip, and hotel data and calculate nights and stay price in the backend.
The SQLite schema, seeding layer, application startup integration, hotel
search, user lookup, booking CRUD, joined history routes, and corresponding Vue
flows are implemented and tested.
