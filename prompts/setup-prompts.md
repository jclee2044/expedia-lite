# Reusable Codex Project Setup Prompt Guide

## 1. Define the Project and Create the Bounded Scaffold

```text
Project scaffold: Inspect the existing docs/ directory first and use its contents as the primary source of truth for the project's purpose, users, requirements, constraints, and terminology. Then prepare the initial project structure.

This project will use:
- Python for backend logic;
- FastAPI for the backend API layer;
- Vue for the frontend;
- Node.js and npm for the Vue development environment, tooling, and build process.

Do not begin with follow-up questions. First inspect docs/ and the existing project files. If information is still missing, preserve the uncertainty as an explicit TODO when it can safely wait. Ask a concise follow-up question only when the missing information blocks or would materially change the initial scaffold, project rules, dependency setup, or verification.

After inspecting the available documentation and resolving only genuinely blocking questions, create only this initial structure:
- backend/
- frontend/
- docs/
- README.md
- AGENTS.md
- .gitignore

README.md must document:
- the project's name and current purpose;
- the selected architecture and the responsibility of each layer;
- that backend and frontend environments are project-owned;
- setup, verification, and local-development commands as they become known;
- any unresolved decisions as explicit TODOs rather than invented requirements.

AGENTS.md must establish these durable rules:
- work only inside this project;
- read AGENTS.md and README.md before making changes;
- ask targeted follow-up questions when missing information would materially change the work;
- keep framework-free Python domain logic separate from FastAPI routes;
- keep frontend presentation separate from backend-request code;
- communicate between Vue and FastAPI through a documented JSON contract;
- do not install Python or JavaScript project dependencies globally;
- do not add, remove, or upgrade dependencies without explaining why;
- ask before any machine-level installation, destructive action, or scope expansion;
- never use sudo automatically or bypass managed-computer policies;
- stop only processes started for the current task;
- report commands run, files changed, checks performed, and anything not verified.

Create a suitable .gitignore for Python virtual environments, Python caches, Node dependencies, Vue/Vite build output, environment files, editor files, and operating-system artifacts. Do not ignore dependency manifests or lockfiles.

Do not create a virtual environment, initialize Vue, install dependencies, initialize Git, or write application code yet. Report every file and directory created.
```

## 2. Run a Read-Only Development Environment Preflight

```text
Environment preflight: Verify this project's development environment without changing it.

Verify the development environment without creating files, installing software, changing dependencies, or writing application code.

Confirm:
- the operating system;
- every available Python executable, version, and path;
- whether Python 3.10 or higher is available;
- whether a project-owned backend virtual environment already exists;
- whether FastAPI and pytest are declared in a project dependency manifest;
- the Node.js and npm versions and executable paths;
- whether the installed Node.js version meets the current official Vue Quick Start requirement;
- whether frontend/package.json, a lockfile, and frontend/node_modules exist;
- whether the current folder is inside a Git repository;
- the current project inventory.

Distinguish computer-level tools from project-owned environments. A globally importable package does not prove that this project owns or can reproduce it.

Ask a concise follow-up question only if ambiguity about the project folder or intended architecture prevents accurate verification.

Report each check as passed, missing, partial, or not applicable. Partial readiness is expected for a new scaffold. Report the commands used and confirm that the preflight changed nothing.
```

## 3. Check and Prepare Git

```text
Git setup: Check whether Git is ready for this project without changing the repository.

Run only the Git checkpoint of the check-action-verify loop.

CHECK
- identify the operating system;
- run the Git version command;
- check whether the current project is already inside a Git repository;
- inspect repository status if a repository already exists;
- do not initialize a repository, stage files, commit, switch branches, or edit project files during this check.

TAKE ACTION
- if Git is available, do not reinstall it;
- if Git is missing or an ordinary setup problem exists, identify the safest supported installation or correction from an official source;
- explain the exact download or system change and whether it requires administrator access, then stop for my permission;
- after I approve, perform only the approved action when the computer permits it;
- never use sudo automatically and never bypass a managed-computer policy.

VERIFY
- report the Git version and executable path;
- confirm whether the project is inside a Git repository;
- report repository status if applicable;
- confirm whether the Git checkpoint passed.

Ask a targeted follow-up question if the correct repository boundary is unclear. Do not change project files or repository history.
```

## 4. Check and Prepare Python

```text
Python setup: Check and, when necessary, prepare a compatible computer-level Python installation.

Run only the Python checkpoint of the check-action-verify loop.

CHECK
- detect the operating system;
- report every available Python executable, version, and path;
- treat Python 3.10 or higher as compatible;
- identify the best compatible interpreter for this project without changing anything.

TAKE ACTION
- if a compatible Python already exists, do not reinstall it;
- if Python is missing or incompatible, identify the safest supported installation method from an official source;
- explain the exact download or system change and whether it requires administrator access, then stop for my permission;
- after I approve, perform only the approved Python installation when the computer permits it;
- never use sudo automatically and never bypass a managed-computer policy.

VERIFY
- report the compatible Python version and executable path;
- confirm whether the Python checkpoint passed.

Ask a concise follow-up question only if multiple compatible installations create a meaningful project choice. Do not create a virtual environment, install packages, or write application code yet.
```

## 5. Create the Project-Owned Backend Environment

```text
Backend environment setup: Create and verify this project's isolated Python environment and declared backend dependencies.

Do not write backend functions, FastAPI routes, tests, or frontend application code.

Before changing files, ask me a targeted follow-up question if the existing project files reveal an unresolved dependency-management choice or a conflict with this prompt. Otherwise continue.

Prepare the backend development environment:
- create backend/.venv using the compatible Python that passed verification;
- create backend/requirements.txt containing only fastapi[standard] and pytest;
- install only those declared dependencies into backend/.venv;
- use the virtual environment's Python for every backend verification command;
- verify that the interpreter path belongs to backend/.venv;
- verify that fastapi and pytest import successfully;
- record exact reproducible setup and verification commands in README.md.

Do not install Python packages globally. Do not add optional database, authentication, AI, formatting, linting, or deployment packages before project requirements justify them. Ask before any machine-level change.

Report every command run, every file or directory created or modified, installed dependency evidence, interpreter evidence, and any check that did not pass.
```

## 6. Check and Prepare Node.js and npm

```text
Node.js setup: Check and, when necessary, prepare compatible computer-level Node.js and npm installations.

Run only the Node.js checkpoint of the check-action-verify loop.

CHECK
- read the current official Vue Quick Start requirement for supported Node.js versions;
- report the installed Node.js and npm versions and executable paths;
- compare the installed Node.js version with the current Vue requirement.

TAKE ACTION
- if the installed version is compatible, do not reinstall it;
- if Node.js is missing or incompatible, identify a supported LTS installation from an official source;
- explain the exact download or system change and whether it requires administrator access, then stop for my permission;
- after I approve, perform only the approved Node.js installation when the computer permits it;
- never use sudo automatically and never bypass a managed-computer policy.

VERIFY
- report the Node.js and npm versions and executable paths;
- confirm whether the Node.js checkpoint passed.

Ask a concise follow-up question only if multiple supported installation choices would materially affect reproducibility. Do not initialize Vue, install frontend packages, or write application code yet.
```

## 7. Initialize the Project-Owned Vue Environment

```text
Vue environment setup: Initialize and verify this project's project-owned Vue environment and frontend dependencies.

Before changing files, inspect frontend/. If it is not empty or the current official create-vue workflow presents materially different choices from those below, stop and ask me concise follow-up questions. Otherwise continue.

Initialize a minimal JavaScript Vue project inside the existing frontend/ folder:
- use the current official create-vue workflow;
- do not create a second nested frontend folder;
- use Node.js and npm only as the Vue toolchain; do not create a separate Node server;
- do not install Vue or Vue CLI globally;
- omit Router, Pinia, TypeScript, JSX, unit testing, end-to-end testing, and experimental options;
- include ESLint for code-quality checks;
- install all dependencies declared by the generated package.json;
- retain and report the generated lockfile;
- run the frontend lint and production-build checks;
- add exact reproducible setup, lint, build, and development commands to README.md.

The generated Vue starter files are allowed, but do not implement a project-specific interface or connect the frontend to FastAPI. Do not change backend files or add undeclared dependencies.

Report every command run, every file or directory created or modified, the dependency-installation evidence, and the results of lint and production build.
```

## 8. Verify the Complete Initial Scaffold

```text
Scaffold verification: Verify that the complete initial project scaffold is reproducible and ready for feature development.

Verify the complete initial project scaffold without changing source files, dependency declarations, or installed dependencies.

Confirm:
- the project contains backend/, frontend/, docs/, README.md, AGENTS.md, and .gitignore;
- README.md accurately records the architecture and reproducible commands;
- AGENTS.md contains the project boundary, separation-of-concerns rules, permission rules, and reporting requirements;
- the exact Python interpreter used for backend checks belongs to backend/.venv;
- backend/requirements.txt declares fastapi[standard] and pytest;
- fastapi and pytest import successfully through backend/.venv;
- the Node.js and npm versions and executable paths;
- Node.js satisfies the current official Vue requirement;
- frontend/package.json declares Vue and ESLint-related tooling;
- the frontend lockfile exists;
- the installed frontend packages match the lockfile;
- frontend lint and production build pass;
- .gitignore excludes generated environments, dependency directories, build output, caches, and secrets while preserving manifests and lockfiles;
- no project-specific backend function, FastAPI route, backend test, API connection, or application interface has been implemented.

Report every verification command and classify every check as passed, failed, partial, or not applicable. Do not hide partial readiness. If missing information prevents a reliable conclusion, ask a targeted follow-up question instead of guessing.
```

## 9. Initialize the Repository and Create the Scaffold Commit

```text
Initial Git checkpoint: Review and, after approval, commit the verified project scaffold.

The verified initial scaffold is ready for its first Git checkpoint.

CHECK
- confirm that the complete scaffold verification passed;
- inspect Git status;
- confirm the intended repository root;
- inspect the exact files that would be included and verify that no virtual environment, node_modules directory, build output, cache, secret, or environment file would be committed.

If the repository root, included files, Git identity, remote strategy, or an existing repository state is ambiguous, ask me a concise follow-up question before taking action.

TAKE ACTION
- if this folder is not yet a repository, initialize Git only at the confirmed project root;
- stage only the verified scaffold, documentation, dependency manifests, and lockfile;
- show me the proposed commit scope and commit message, then ask for approval before creating the commit;
- after approval, create one initial scaffold commit;
- do not configure a remote, push, rewrite history, or switch branches unless I explicitly request it.

VERIFY
- show the resulting concise Git status;
- report the commit identifier and message if a commit was approved and created;
- confirm that generated environments, dependencies, build output, and secrets were not committed;
- report any check or action that did not complete.
```

## Completion Checklist

- [ ] Project boundary and architecture are documented.
- [ ] Necessary missing information was gathered without inventing project requirements.
- [ ] Read-only preflight was completed before installation.
- [ ] Git, Python, Node.js, and npm were verified.
- [ ] Any machine-level change required explanation and permission.
- [ ] `backend/.venv` belongs to the project.
- [ ] `backend/requirements.txt` declares `fastapi[standard]` and `pytest`.
- [ ] FastAPI and pytest import through the project interpreter.
- [ ] Vue and ESLint are declared in `frontend/package.json`.
- [ ] The frontend lockfile and installed dependencies are present.
- [ ] Frontend lint and production build pass.
- [ ] README.md contains reproducible commands.
- [ ] No project-specific application code was implemented.
- [ ] The verified scaffold was committed only after approval.
