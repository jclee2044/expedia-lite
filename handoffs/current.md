# Expedia Lite current handoff

Refreshed after the Assignment 2 Part 1 merge on 2026-09-29. Recheck this record against Git and the named files before continuing in another thread. The merge is pushed, but the course submission has not been verified.

## Objective and decisions

Assignment 2 Part 1 is implemented and merged into `main`: the application searches live Geoapify hotel places by an exact five-digit U.S. ZIP code and synchronizes them in a Vue list and Leaflet map. The original fictional hotel-name search and booking flow remain available as a separate search mode. Geoapify places are not presented as bookable inventory and have no invented prices, ratings, or availability.

The merged UI keeps Name and ZIP Code search in separate modes, uses the same hero sentence and search-control layout, aligns their empty states, applies a green brand palette, and uses a shared responsive heading size across Search, My trips, and Account. The ZIP search button says “Search.” The footer contains Expedia Lite, copyright 2026, and Jacob Lee's attribution. Nearby hotel cards split provider display addresses into street lines and a city/state/ZIP line, omitting a repeated hotel name and U.S. country suffix. The map circle uses the current brand color and the attribution is placed at the bottom right.

Assignment 2 Part 2, the persistent shortlist, is described in docs/assignment2-description.md but has not been implemented.

## Architecture and file map

Vue View -> FastAPI routes -> framework-free Controllers -> Models/SQLite.

- frontend/src/App.vue owns view/search state, including the Name/ZIP switch and selected Geoapify place ID. frontend/src/assets/main.css owns layout.
- frontend/src/components/ZipLookupPanel.vue renders ZIP input and feedback. NearbyHotelsPanel.vue renders the places list, using hotelAddress.js for display formatting; NearbyHotelsMap.vue renders the Leaflet map and markers. frontend/src/api/locations.js makes proxied API requests, so the provider key does not enter the Vue bundle.
- backend/app/routes.py exposes the ZIP and nearby-hotel endpoints. backend/controllers/geocoding.py and the Places controller handle provider requests; backend/models/ contains framework-free data contracts.
- The original account, booking, and fictional stay flows use SQLite. CSV files in data/ seed the ignored runtime database once.
- README.md documents setup, run commands, both search modes, and API behavior. Assignment 2 scope is in docs/assignment2-description.md; research decisions and the implementation-time sketch are in docs/assignment2-part1-notes.md and docs/assignment2-part1-mockup.svg. docs/verification.md mainly describes the older name-search/booking workflow and historical results. report.md is the Assignment 2 Part 1 submission draft and links the committed demo; a1-report.md preserves the earlier assignment report.

## Git state

- Root: /Users/jlee/Desktop/psu4/ist402/a1_expedia_lite
- Branch: `main`. Before this handoff-only refresh, HEAD and `origin/main` matched at merge commit `18f5d5d93d0c4c8b60d67e7c95c8b2939450c9fc` (Merge zip-search into main). This handoff refresh will be committed on top, so verify the latest HEAD when resuming.
- The merged feature tip is `6a91446` (report checkpoint update), following implementation checkpoint `929cb777ed0d8ded1e18a4d91f9b31bfcc5387a8` and earlier ZIP search commits `7dc9f5b`, `8a2cd73`, and `8fdbb19`. The `zip-search` branch remains local with no configured upstream; `main` tracks `origin/main`.
- `git fetch origin main` confirmed the remote baseline before merging. `git push origin main` advanced the remote from `ddb02a0` to `18f5d5d`. The working tree was clean immediately after that push; only this handoff is being edited afterward. The 80.08 MB demo video pushed successfully with GitHub's advisory warning about its recommended 50 MB limit.
- .env, backend/.venv, frontend/node_modules, and frontend/dist are ignored by Git. No credentials or environment values were inspected.

## Completed and incomplete work

- Merged Part 1: exact U.S. ZIP resolution, Geoapify hotel places within 5 km, a 50-result provider cap, list/map selection in both directions, keyboard-selectable places, map pin labels, and OpenStreetMap attribution.
- The merged UI includes the Name/ZIP mode switch, matching search controls and empty states, green branding, consistent headings and footer, brand-colored map radius, and formatted hotel-card addresses. The earlier Assignment 1 report/video are preserved under `a1-report.md` and `Expedia Lite A1 Demo.mp4`.
- report.md records research, mockup choices, live-search observations, AI use, and the assessed implementation checkpoint. It links `Expedia Lite A2.1 Demo.mov`. Its remaining TODO is to confirm the mockup's creation timing. The video contents and the report's manual observations were not independently verified during this merge task.
- The persistent shortlist required for Assignment 2 Part 2 remains future work. Do not infer live room availability from Geoapify places.

## Verification observed for this handoff

- Before the merge, `backend/.venv/bin/python -m pytest backend/tests`: 118 passed, 2 dependency deprecation warnings.
- From `frontend/`, `npm test`: 16 passed, including three address-formatting cases.
- From `frontend/`, `./node_modules/.bin/oxlint .` and `./node_modules/.bin/eslint .`: both passed without output. These read-only commands avoid the `--fix` options in `npm run lint`.
- From `frontend/`, `npm run build`: passed; Vite transformed 27 modules.
- `git diff --cached --check` passed before the feature commit. An earlier UI-work turn reported `npm run lint` passing; the read-only lint commands above were rerun before merging.
- git check-ignore -v .env backend/.venv frontend/node_modules frontend/dist: all four paths ignored.

Browser checks during UI work showed the Name/ZIP switch, matching input and empty-state layouts, a one-line Search title at a 753 px viewport, and the Account title at the same computed font size. A live ZIP 16802 result was visible while verifying address display: the Scholar Hotel State College card showed “205 East Beaver Avenue” and “State College, PA 16801” on separate lines without the country; a provider address with an extra locality displayed three lines. This was not a complete integrated walkthrough. The My trips title shares the Search CSS rule; its signed-in view was not opened here. Historical live ZIP counts in report.md are not fixed expectations.

## Active services and limits of inspection

At this refresh, `lsof -nP -iTCP:5173 -iTCP:8000 -sTCP:LISTEN` found node listening at 127.0.0.1:5173 (PID 31052) and Python at 127.0.0.1:8000 (PID 31055). Their startup commands and ownership by this task were not verified; neither was current HTTP health. Earlier browser interactions are described above and in report.md, but no fresh integrated browser walkthrough was run during this documentation refresh. Do not stop these processes without confirming ownership; only stop processes started for the current task.

## Risks, next action, and verification boundary

- The Part 1 submission is due 2026-09-29 according to docs/assignment2-description.md. Research, an early mockup, a recorded demonstration, a Part 1 report, an assessed commit, and AI evidence are specified there. Confirm the actual submission requirements against the course source before final submission; the existing sketch was made during implementation, as its notes disclose.
- README.md now describes both search modes; docs/verification.md still focuses on the older name-search and booking workflow. Do not treat historical live ZIP counts in report.md as fixed expectations; provider coverage varies.
- Recommended next action: review the Part 1 report and demo for course submission, especially the mockup timing TODO. For later development, plan the Part 2 shortlist separately. Read AGENTS.md, README.md, this handoff, docs/assignment2-description.md, report.md, and docs/verification.md first.

Verified in this merge task: remote baseline and successful push of the merge, source file inventory, staged diff check, automated test/build/read-only lint results, and a clean working tree immediately after the merge push. Still to verify: service command lines and current HTTP health, a fresh live Geoapify search and complete browser walkthrough, the video's contents, the mockup's creation timing, and the actual course submission.
