# Expedia Lite current handoff

Refreshed from repository and local runtime evidence on 2026-09-29. Recheck this record against Git and the named files before continuing in another thread. This snapshot includes uncommitted work and does not assert that a submission is complete.

## Objective and decisions

The active work is Assignment 2 Part 1: search live Geoapify hotel places by an exact five-digit U.S. ZIP code, then show and synchronize those places in a Vue list and Leaflet map. The original fictional hotel-name search and booking flow remain available as a separate search mode. Geoapify places are not presented as bookable inventory and have no invented prices, ratings, or availability.

Recent uncommitted UI work keeps Name and ZIP Code search in separate modes, uses the same hero sentence and search-control layout, aligns their empty states, applies a green brand palette, and uses a shared responsive heading size across Search, My trips, and Account. The ZIP search button says “Search.” The footer contains Expedia Lite, copyright 2026, and Jacob Lee's attribution. Nearby hotel cards now split provider display addresses into street lines and a city/state/ZIP line, omitting a repeated hotel name and U.S. country suffix. The map circle uses the current brand color and the attribution is placed at the bottom right.

Assignment 2 Part 2, the persistent shortlist, is described in docs/assignment2-description.md but has not been implemented on this branch.

## Architecture and file map

Vue View -> FastAPI routes -> framework-free Controllers -> Models/SQLite.

- frontend/src/App.vue owns view/search state, including the Name/ZIP switch and selected Geoapify place ID. frontend/src/assets/main.css owns layout.
- frontend/src/components/ZipLookupPanel.vue renders ZIP input and feedback. NearbyHotelsPanel.vue renders the places list, using hotelAddress.js for display formatting; NearbyHotelsMap.vue renders the Leaflet map and markers. frontend/src/api/locations.js makes proxied API requests, so the provider key does not enter the Vue bundle.
- backend/app/routes.py exposes the ZIP and nearby-hotel endpoints. backend/controllers/geocoding.py and the Places controller handle provider requests; backend/models/ contains framework-free data contracts.
- The original account, booking, and fictional stay flows use SQLite. CSV files in data/ seed the ignored runtime database once.
- README.md documents setup, run commands, both search modes, and API behavior. Assignment 2 scope is in docs/assignment2-description.md; research decisions and the implementation-time sketch are in docs/assignment2-part1-notes.md and docs/assignment2-part1-mockup.svg. docs/verification.md mainly describes the older name-search/booking workflow and historical results. report.md is the uncommitted Assignment 2 Part 1 submission draft; a1-report.md is also present but has not been reviewed for this handoff.

## Git state

- Root: /Users/jlee/Desktop/psu4/ist402/a1_expedia_lite
- Branch: zip-search; HEAD: 7dc9f5b7c0161742145987397ac56765843b9d88 (Add hotel icons to nearby result cards, 2026-09-29).
- Earlier Part 1 implementation: 8a2cd73 (Add ZIP-based Geoapify hotel search and map). geoapify-impl points to 8fdbb19, the earlier ZIP lookup demo.
- zip-search has no configured upstream. Local main tracks origin/main at ddb02a0. origin is configured for the GitHub Expedia Lite repository. No remote fetch was performed for this handoff, so remote freshness is unknown.
- The working tree is dirty. Modified tracked files: .gitignore, README.md, frontend/src/App.vue, frontend/src/assets/main.css, frontend/src/components/NearbyHotelsMap.vue, frontend/src/components/NearbyHotelsPanel.vue, frontend/src/components/ZipLookupPanel.vue, handoffs/current.md, and report.md. Expedia Lite Demo.mp4 is deleted. Untracked paths: Expedia Lite A1 Demo.mp4, Expedia Lite A2.1 Demo.mov, a1-report.md, docs/mockups/, frontend/src/components/hotelAddress.js, and frontend/tests/hotelAddress.test.js. README.md and this handoff were edited during this documentation refresh; other changes predated it. Video contents, a1-report.md, and mockup image contents were not reviewed here. No Git history change was made.
- .env, backend/.venv, frontend/node_modules, and frontend/dist are ignored by Git. No credentials or environment values were inspected.

## Completed and incomplete work

- Committed Part 1: exact U.S. ZIP resolution, Geoapify hotel places within 5 km, a 50-result provider cap, list/map selection in both directions, keyboard-selectable places, map pin labels, and OpenStreetMap attribution.
- Uncommitted UI: Name/ZIP mode switch with sliding indicator; matching search controls and empty states; green branding; consistent headings and footer; map attribution placement and brand-colored radius; removal of the provider name from a visible results label; formatted hotel card addresses. Review all modified and untracked files intentionally before any checkpoint.
- report.md has been rewritten as an Assignment 2 Part 1 draft. It records research, mockup choices, live-search observations, and AI use; it links the untracked Expedia Lite A2.1 Demo.mov file. It still has TODOs for the assessed commit and confirmation of the mockup's creation timing. The video contents and the report's manual observations were not independently verified during this refresh.
- The persistent shortlist required for Assignment 2 Part 2 remains future work. Do not infer live room availability from Geoapify places.

## Verification observed for this handoff

- On this documentation refresh, `backend/.venv/bin/python -m pytest backend/tests`: 118 passed, 2 dependency deprecation warnings.
- From `frontend/`, `npm test`: 16 passed, including three address-formatting cases.
- From `frontend/`, `./node_modules/.bin/oxlint .` and `./node_modules/.bin/eslint .`: both passed without output. These read-only commands avoid the `--fix` options in `npm run lint`.
- From `frontend/`, `npm run build`: passed; Vite transformed 27 modules.
- `git diff --check` passed after the documentation edits. An earlier UI-work turn reported `npm run lint` passing; that auto-fixing command was not rerun in this refresh.
- git check-ignore -v .env backend/.venv frontend/node_modules frontend/dist: all four paths ignored.

Browser checks during UI work showed the Name/ZIP switch, matching input and empty-state layouts, a one-line Search title at a 753 px viewport, and the Account title at the same computed font size. A live ZIP 16802 result was visible while verifying address display: the Scholar Hotel State College card showed “205 East Beaver Avenue” and “State College, PA 16801” on separate lines without the country; a provider address with an extra locality displayed three lines. This was not a complete integrated walkthrough. The My trips title shares the Search CSS rule; its signed-in view was not opened here. Historical live ZIP counts in report.md are not fixed expectations.

## Active services and limits of inspection

At this refresh, `lsof -nP -iTCP:5173 -iTCP:8000 -sTCP:LISTEN` found node listening at 127.0.0.1:5173 (PID 31052) and Python at 127.0.0.1:8000 (PID 31055). Their startup commands and ownership by this task were not verified; neither was current HTTP health. Earlier browser interactions are described above and in report.md, but no fresh integrated browser walkthrough was run during this documentation refresh. Do not stop these processes without confirming ownership; only stop processes started for the current task.

## Risks, next action, and verification boundary

- The Part 1 submission is due 2026-09-29 according to docs/assignment2-description.md. Research, an early mockup, a recorded demonstration, a Part 1 report, an assessed commit, and AI evidence are specified there. Confirm the actual submission requirements against the course source before final submission; the existing sketch was made during implementation, as its notes disclose.
- README.md now describes both search modes; docs/verification.md still focuses on the older name-search and booking workflow. Do not treat historical live ZIP counts in report.md as fixed expectations; provider coverage varies.
- Recommended next action: inspect the uncommitted frontend diffs and the newly present media/mockup changes before deciding what belongs in a checkpoint. Perform any remaining requested UI edits, then verify the Part 1 interaction and prepare the intended commit/report/demo. Read AGENTS.md, README.md, this handoff, docs/assignment2-description.md, docs/assignment2-part1-notes.md, and docs/verification.md first.

Verified in this refresh: local branch/HEAD/status, named source files and diffs, the current automated test/build/read-only lint results above, and listening ports. Verified in the preceding documentation review: ignore rules. Still to verify: actual remote freshness, service command lines and current HTTP health, a fresh live Geoapify search and complete browser walkthrough, contents and intended treatment of the new media/mockup artifacts, and the Part 1 submission evidence.
