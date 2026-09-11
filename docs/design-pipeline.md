# Expedia Lite design pipeline

Expedia Lite currently implements one flow: search synthetic hotel data by hotel name and display each matching offered stay.

## Responsibilities

- **Vue frontend:** `frontend/src/App.vue` owns the search form and result, loading, empty, and error states. `frontend/src/api/hotels.js` owns the HTTP request. Vite proxies `/api` to FastAPI during development.
- **FastAPI boundary:** `backend/app/main.py` exposes `GET /api/hotels/search`, translates query and data errors into HTTP responses, and validates the documented JSON response with the models in `backend/app/schemas.py`.
- **Python backend:** `backend/app/search.py` reads `data/hotels.csv` and `data/trips.csv`, validates the records, joins trips to hotels through `hotel_id`, matches normalized hotel names, and calculates nights and stay prices. It has no FastAPI dependency.

## Data flow

```text
search form -> frontend request module -> FastAPI route
            -> Python CSV/search logic -> response schema
            -> JSON -> Vue results table
```

The CSV files are read-only starter data. Authentication, booking creation/history, and persistent SQLite storage are not implemented yet.
