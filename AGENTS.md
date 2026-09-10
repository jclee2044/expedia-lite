# Expedia Lite project rules

## Before making changes

- Work only inside the Expedia Lite project root (`a1_expedia_lite/`).
- Read `AGENTS.md` and `README.md` before changing the project.
- Ask targeted follow-up questions when missing information would materially change the work. Record unresolved decisions as TODOs instead of inventing requirements.
- Keep changes small, focused, and within the requested scope.

## Architecture and source organization

- Keep the application split between `backend/` and `frontend/`.
- Put backend application code in `backend/app/` and backend tests in `backend/tests/`.
- Keep framework-free Python domain logic separate from FastAPI routes. Routes handle HTTP concerns and delegate business behavior.
- Use type hints for Python functions and add or update tests when backend behavior changes.
- Put Vue source files in `frontend/src/` and prefer Vue 3 Composition API with `<script setup>`.
- Keep Vue presentation components separate from backend-request code. Extract reusable UI or logic when it improves clarity.
- Add or update appropriate frontend checks when frontend behavior changes.

## Data and API contracts

- Treat CSV files in `data/` as project data. Do not silently change their schema or meaning.
- Communicate between Vue and FastAPI through a documented JSON contract.
- Keep frontend request shapes, backend schemas, and documented examples synchronized.
- Never use real traveler identities, payment details, credentials, or private booking records; use synthetic data only.

## Dependencies and environments

- Treat `backend/.venv/` and `frontend/node_modules/` as project-owned generated environments; never commit them.
- Do not install Python or JavaScript project dependencies globally.
- Do not add, remove, or upgrade dependencies without explaining the concrete need.
- Keep dependency manifests and lockfiles synchronized after approved dependency changes.
- Do not add database, authentication, AI, formatting, linting, or deployment packages until project requirements justify them.

## Permissions and safety

- Ask before any machine-level installation, destructive action, or expansion beyond the requested scope.
- Never use `sudo` automatically or bypass managed-computer policies.
- Never commit secrets, local environment files, virtual environments, installed dependency directories, caches, or build output.
- Stop only processes started for the current task; never stop an unrelated process.

## Verification and reporting

- Run the smallest relevant checks, tests, and builds before considering a change complete.
- Use `backend/.venv/bin/python` for every backend verification command.
- Run frontend commands from `frontend/` with the project-owned npm dependencies.
- Update `README.md` when setup, run commands, dependencies, or project structure change.
- Report every command run, every file changed, checks performed, failures encountered, and anything not verified.

## Handoffs and durable context

- Use `handoffs/create-handoff.md` when work must continue in a new thread or with another model.
- Create or refresh `handoffs/current.md` only when a handoff is actually needed.
- Build each handoff from current repository evidence, not conversation memory, and distinguish verified facts from claims that still require verification.
- Include the objective, architecture, Git state, completed and incomplete work, observed verification, active services, risks, and recommended next action.
- Never include secrets, tokens, private URLs, private traveler data, or unnecessary conversation in a handoff.
- Before resuming, verify `handoffs/current.md` against the Git root, branch, HEAD, working tree, named files, and recorded checks.
- Do not edit, install dependencies, change Git state, or manage services while reconstructing a handoff; first report discrepancies and obtain approval for the next step.
