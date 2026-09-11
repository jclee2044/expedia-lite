# Expedia Lite verification

Run commands from the project root unless a step says otherwise.

## Automated checks

```bash
backend/.venv/bin/python -m pytest backend/tests
cd frontend
npm run lint
npm run build
```

## Integrated check

1. Start FastAPI from the project root with `backend/.venv/bin/python -m uvicorn backend.app.main:app --reload`.
2. Start Vue from `frontend/` with `npm run dev`.
3. Open `http://127.0.0.1:5173` and search for `Harbor`.
4. Confirm the page reports one hotel and shows the `T001` and `T009` stays.
5. Search for an unknown name and confirm the no-results state.
6. Submit a blank search and confirm `Enter a hotel name.` appears.

The API contract can also be inspected at `http://127.0.0.1:8000/docs`.
