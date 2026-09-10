# Expedia Lite current handoff

Generated from repository evidence on 2026-09-10. Verify every claim again before editing.

## 1. Current objective and important decisions

The project is preparing a durable, verified initial scaffold for a local Expedia-inspired prototype. The intended user flows are browsing synthetic hotel data, creating a simulated booking, and reviewing booking history.

Standing decisions recorded in `README.md` and `AGENTS.md`:

- Vue 3 owns the interface; FastAPI owns HTTP/JSON; framework-free Python owns domain rules.
- Vue request code must remain separate from presentation, and FastAPI routes must remain separate from domain logic.
- Browser/backend communication must use a documented JSON contract.
- Project data must be synthetic. `data/` contains hotels, users, trips, and bookings linked by stable text IDs.
- Backend and frontend dependencies must remain project-owned; dependency changes require explanation.
- Part 1 reads the supplied CSV files. Part 2 uses them as initial SQLite records and must preserve application changes across restarts without reimporting or duplicating starter records.
- The API contract, Python transitive-dependency locking, and detailed flow/error behavior remain open decisions.

## 2. Architecture and important-file map

```text
a1_expedia_lite/
|-- AGENTS.md                      standing rules and permission boundaries
|-- README.md                      purpose, architecture, setup, and commands
|-- .gitignore                     generated files and secrets exclusions
|-- backend/
|   |-- requirements.txt           fastapi[standard] and pytest
|   |-- .venv/                     local generated Python environment (ignored)
|   |-- app/                       empty; intended backend source location
|   `-- tests/                     empty; intended backend test location
|-- frontend/
|   |-- package.json               Vue/Vite/ESLint toolchain declarations
|   |-- package-lock.json          npm lockfile
|   |-- src/App.vue                uncustomized create-vue starter view
|   |-- src/main.js                Vue application mount point
|   |-- vite.config.js             generated Vite configuration
|   |-- node_modules/              local generated dependencies (ignored)
|   `-- dist/                      generated production build (ignored)
|-- data/
|   |-- README.md                 schema, relationships, and expected examples
|   |-- hotels.csv                eight fictional hotels
|   |-- users.csv                 six demo travelers
|   |-- trips.csv                 twelve offered hotel stays
|   |-- bookings.csv              six simulated reservations
|   |-- relationships.png         relationship diagram
|   `-- relationships.svg         editable diagram source
|-- docs/                          assignment description and four reference images
|-- prompts/setup-prompts.md       reusable setup/checkpoint prompts
`-- handoffs/
    |-- create-handoff.md          handoff creation and resumption prompts
    `-- current.md                 this evidence-based continuation note
```

The planned runtime boundary is Vue -> frontend request module -> FastAPI route -> framework-free Python domain logic -> JSON response -> Vue. The request module, API route, and domain modules do not exist yet.

## 3. Git state

- Git root: `/Users/jlee/Desktop/psu4/ist402/a1_expedia_lite`
- Git executable/version: `/usr/bin/git`, Apple Git 2.50.1
- Current branch name: `main`
- HEAD: unborn; the repository has no commits
- Recent commits: none
- Other/relevant branches: none reported
- Upstream: none
- Remotes: none
- Working tree: not clean
- Git identity: `Jacob Lee <jclee2044@gmail.com>` is configured locally

Immediately before the approved initial commit, the original scaffold was staged, while current documentation, data files, handoff files, and `prompts/setup-prompts.md` still required staging. Generated environments, dependency directories, caches, and build output were ignored. This Git snapshot was recorded before the commit requested by the user; verify HEAD and status because they are expected to change immediately afterward.

## 4. Completed work

- Root project documentation exists in `README.md` and `AGENTS.md`.
- Root `.gitignore` covers Python environments/caches, Node dependencies, Vite output, environment files, editor files, and OS artifacts.
- `backend/.venv/bin/python` is a working project-owned Python 3.12.13 environment.
- `backend/requirements.txt` declares only `fastapi[standard]` and `pytest`.
- The minimal JavaScript Vue scaffold exists with Vue, Vite, ESLint, and the generated Oxlint integration.
- `frontend/package-lock.json` exists and installed direct packages resolve successfully.
- `docs/` contains `assignment-description.md` and four Expedia reference images.
- `data/` contains four synthetic CSV datasets, a schema/usage guide, and PNG/SVG relationship diagrams.
- `handoffs/create-handoff.md` contains reusable creation and resumption prompts.
- `prompts/setup-prompts.md` contains the setup/checkpoint prompt sequence.
- No commit identifiers exist because HEAD has no commit.

## 5. Incomplete or requested work

- Complete and verify the user-approved initial project-setup commit.
- Create `docs/design-pipeline.md`; it is referenced by the handoff procedure but missing.
- Create `docs/verification.md`; it is referenced by the handoff procedure but missing.
- Decide whether the single `prompts/setup-prompts.md` satisfies the required prompt library or should be split into ordered milestone files.
- Define the JSON API contract, exact feature scope, and empty/failure states.
- Implement Part 1 CSV reading, then implement the documented Part 2 SQLite initialization and persistence behavior without destructive reimports.
- Implement backend domain modules, FastAPI routes, backend tests, frontend request code, and project-specific Vue views only after those decisions are approved.
- Add a backend run command and later verify both required flows in a browser.

## 6. Verification commands and observed results

These commands were run while creating this handoff:

```bash
PYTHONDONTWRITEBYTECODE=1 backend/.venv/bin/python -B -c "import pathlib, sys, fastapi, pytest; print('python=' + sys.version.split()[0]); print('executable=' + sys.executable); print('belongs_to_venv=' + str(pathlib.Path(sys.executable).is_relative_to(pathlib.Path('backend/.venv').resolve()))); print('fastapi=' + fastapi.__version__); print('pytest=' + pytest.__version__)"
```

Observed: Python 3.12.13; executable `backend/.venv/bin/python`; `belongs_to_venv=True`; FastAPI 0.141.1; pytest 9.1.1.

```bash
node --version
command -v node
npm --version
command -v npm
npm --prefix frontend ls --depth=0
```

Observed: Node v26.6.0 at `/opt/homebrew/bin/node`; npm 11.18.0 at `/opt/homebrew/bin/npm`; the direct dependency tree resolved without an error and included Vue 3.5.42, Vite 8.3.0, ESLint 10.10.0, Oxlint 1.73.0, and their declared supporting tools.

```bash
PYTHONDONTWRITEBYTECODE=1 backend/.venv/bin/python -B -c "import csv, pathlib; root=pathlib.Path('data'); load=lambda n:list(csv.DictReader((root/n).open(encoding='utf-8-sig'))); hotels=load('hotels.csv'); users=load('users.csv'); trips=load('trips.csv'); bookings=load('bookings.csv'); assert [len(hotels),len(users),len(trips),len(bookings)]==[8,6,12,6]; h={r['hotel_id'] for r in hotels}; u={r['user_id'] for r in users}; t={r['trip_id'] for r in trips}; assert len(h)==8 and len(u)==6 and len(t)==12; assert all(r['hotel_id'] in h for r in trips); assert all(r['user_id'] in u and r['trip_id'] in t for r in bookings); print('rows=hotels:8 users:6 trips:12 bookings:6'); print('ids_and_foreign_keys=valid')"
```

Observed: all four documented row counts, unique primary IDs, and cross-file foreign-key relationships passed.

```bash
find backend/app backend/tests -type f ! -name '.DS_Store' -print
rg -n 'fetch\(|axios|/api/|FastAPI\(|APIRouter\(|@app\.' frontend/src backend/app backend/tests
git diff --check
git diff --cached --check
```

Observed: no backend source/test files, no API/FastAPI implementation markers, and no whitespace errors in either the unstaged or staged diff.

```bash
npm --prefix frontend run lint
npm --prefix frontend run build
```

Observed immediately before the initial commit: Oxlint and ESLint completed without errors; Vite 8.3.0 transformed 11 modules and produced the ignored `frontend/dist/` build successfully.

## 7. Active services and ports

- No listener was found on Vite's usual port 5173.
- No listener was found on FastAPI's usual port 8000.
- Process enumeration with `ps` was blocked by the managed environment (`operation not permitted`). Therefore, no related service process was verified as active, but the stronger claim that none exists could not be proven.
- No service was started or stopped while creating this handoff.

Commands used:

```bash
lsof -nP -iTCP:5173 -sTCP:LISTEN
lsof -nP -iTCP:8000 -sTCP:LISTEN
ps -axo pid=,command=
```

## 8. Known failures, unresolved questions, risks, and assumptions

- `docs/design-pipeline.md` and `docs/verification.md` are missing.
- At handoff-generation time, Git had no first commit, remote, or upstream; the local identity was configured.
- The Git snapshot in this document was recorded immediately before the approved initial commit and therefore requires verification after that commit.
- The frontend is only the generated starter and is not connected to a backend.
- No backend entry point exists, so the backend cannot be started.
- The Oxlint version in `frontend/package.json` is `~1.73.0`; README records that this was aligned with the generated ESLint integration's peer requirement.
- The complete user flows remain unimplemented and therefore cannot be verified.
- SQLite persistence is required for Part 2, but initialization and migration behavior still needs a precise implementation design.

## 9. Recommended next action

First read:

1. `AGENTS.md`
2. `README.md`
3. `handoffs/current.md`
4. `handoffs/create-handoff.md`
5. `docs/assignment-description.md`
6. `prompts/setup-prompts.md`

Then verify Git status, HEAD, and this handoff. The user approved an initial project-setup commit with the current project data and documentation. If that commit exists, report its identifier and continue by proposing the missing durable-context documents; if it does not, stop and reconcile the intended staged scope before committing.

## 10. Verified facts versus claims requiring verification

Verified from the repository and read-only checks:

- The Git root is this project; the branch name is `main`; HEAD is unborn; there are no remotes or upstreams.
- The working tree is not clean and contains staged, unstaged, ignored, and untracked files.
- Backend imports succeed through the project virtual environment.
- The installed frontend direct dependency tree resolves.
- Frontend lint and the production build passed immediately before the initial commit.
- CSV row counts, unique IDs, and foreign-key references passed validation.
- No project-specific backend implementation or API connection was found.
- The two referenced durable-context docs are missing; the four documented hotel-domain CSV files are present.
- No listeners were found on ports 5173 or 8000.

Requires fresh verification:

- Whether any relevant process exists outside the two checked ports.
- The post-handoff commit identifier and resulting clean/dirty status.
- Whether the supplied CSV relationships and example counts pass future automated validation.
- The API contract, persistence lifetime, and final feature behavior.
