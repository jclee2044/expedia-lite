# Expedia Lite project rules

## Before making changes

- Work only inside the Expedia Lite project root (`a1_expedia_lite/`).
- Read `AGENTS.md` and `README.md` before changing the project.
- Ask targeted follow-up questions when missing information would materially change the work. Record unresolved decisions as TODOs instead of inventing requirements.
- Keep changes small, focused, and within the requested scope.

## Architecture and source organization

- Keep the application split between `backend/` and `frontend/`.
- Put FastAPI transport code in `backend/app/`, entity and relationship definitions in `backend/models/`, controller logic in `backend/controllers/`, and backend tests in `backend/tests/`.
- Follow MVC dependency direction: the Vue View calls FastAPI routes, routes call Controllers, and Controllers use Models and SQLite. Models must not import FastAPI or Controllers.
- Keep framework-free Python models and controllers separate from FastAPI routes. Routes handle HTTP concerns, translate controller errors, and delegate business behavior.
- Keep SQLite connections, reference checks, transactions, and CRUD in the database and business controllers. Controllers exchange model objects through documented contracts.
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

## Course macros

### AutoLoop

Trigger: When the user says **"AutoLoop"**, perform a bounded fix-and-verify loop.

1. Read `AGENTS.md`, `README.md`, and the relevant verification instructions.
2. State the acceptance check for the current task.
3. Run the smallest relevant check.
4. If the check fails for an in-scope source-code reason, inspect the evidence, make the smallest relevant correction, and rerun the check.
5. Repeat for no more than five correction cycles.
6. Stop early and ask for direction if the next action requires a dependency change, machine-level permission, destructive action, an unrelated process to be stopped, or broader scope.
7. Report every cycle, the final evidence, and anything not verified.

### SmokeTest

Trigger: When the user says **"Run the smoke test"**, verify the working application without changing source code or dependency declarations.

1. Read `AGENTS.md`, `README.md`, and `docs/verification.md`.
2. Run the backend pytest suite.
3. Run the frontend lint and production build.
4. Check the intended backend and frontend ports. Never stop an unrelated process.
5. Start only the backend and frontend processes needed for this test in Codex-managed terminals.
6. Verify a successful `Harbor` API search and the documented blank-query error.
7. Use automated browser control to search for `Harbor` and confirm that one hotel and two stays appear.
8. Confirm the no-results and blank-search UI states, check for application errors, and report any behavior that could not be tested.
9. Unless the user asks to keep the app running, stop only the processes created by this smoke test.
10. Report concise evidence from tests, builds, endpoints, the automated UI interaction, and service cleanup.

### Combined trigger

When the user says **"AutoLoop: run the smoke test"**, run the SmokeTest macro. If an in-scope check fails, use the AutoLoop rules to make the smallest correction and repeat the smoke test until it passes, five correction cycles are exhausted, or a stopping condition is reached.
