# Expedia Lite Frontend

This directory contains the Expedia Lite interface, built with Vue 3 and Vite. It searches hotels, loads synthetic travelers, creates simulated bookings through FastAPI, and renders responsive stay cards, backend-sourced confirmation details, persisted traveler history, cancellation controls, and guarded permanent deletion.

The Vite development server proxies `/api` requests to `http://127.0.0.1:8000`, so the FastAPI backend must also be running for searches to succeed.

## Project setup

From this directory, install the locked project dependencies:

```sh
npm ci
```

## Development server

```sh
npm run dev
```

## Verification

```sh
npm test
npm run lint
npm run build
```

The frontend tests use Node's built-in test runner and do not add a testing
package. They verify the request methods, paths, JSON bodies, empty responses,
and error handling shared by hotel search, traveler selection, and booking
operations.

See the project-root `README.md` for backend setup, the complete API contract, and integrated verification guidance.
