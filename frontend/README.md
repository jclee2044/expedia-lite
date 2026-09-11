# Expedia Lite Frontend

This directory contains the Expedia Lite interface, built with Vue 3 and Vite. It sends hotel-name searches to the Python backend through the FastAPI `/api/hotels/search` endpoint and renders the joined hotel and trip records returned by the API.

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
npm run lint
npm run build
```

See the project-root `README.md` for backend setup, the complete API contract, and integrated verification guidance.
