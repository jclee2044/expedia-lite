# Part 2 Turn 0 — storage preflight and early chat mockup

Observed October 6, 2026 on `rag_integration`. This page records checks made
before implementing the chat. The [early SVG mockup](assignment2-part2-chat-mockup.svg)
was drawn before chat source changes. It is a design proposal, not a screenshot
of implemented functionality.

## Foundation checked

The existing uncommitted local-storage changes add three SQLite tables,
saved-hotel API routes, local-first Vue lookup, and simulated nightly displays.
`saved_hotels` and `saved_hotel_zips` join on `hotel_id`; `saved_hotels` and
`demo_hotel_nights` join on `hotel_id`. The original Assignment 1 hotel/trip
tables remain separate. The ZIP interface calls the saved-hotel route first
and only calls Geoapify if a successful local response has no hotels.

The existing ignored runtime database was opened **read-only** before the
temporary check: schema 6; 8 Assignment 1 hotels, 12 trips, 11 users, 10
bookings; 1 saved hotel, 1 ZIP association for 16802, and 5 nights dated
October 10–14. `PRAGMA foreign_key_check` returned no violations. The
runtime database was not the target of any write in this preflight.

| Check | Expected | Observed |
| --- | --- | --- |
| Focused backend tests | Storage, existing API, and Part 1 behavior pass | 49 passed; two dependency deprecation warnings |
| Frontend tests, lint, build | Existing UI contract and build pass | 21 tests passed; read-only Oxlint and ESLint passed; Vite build passed |
| Duplicate save in temporary SQLite | No second hotel or replaced original details | One `Campus Lantern` row; changed duplicate name ignored |
| Remove in temporary SQLite | Hotel, ZIP association, and nights removed | `fixture:remove-me` absent; 4 hotels, 4 ZIP links, 19 nights; no foreign-key violations |
| Browser ZIP 16803 lookup | Four saved places, dated simulated nights, no live provider fallback | “Saved locally,” four places, correct rates and counts; backend log showed only `GET /api/saved-hotels?postcode=16803` for the lookup |
| Linked list/map selection | Selecting either selects the same place in both | Map selection checked `Campus Lantern` in both; list selection checked `Valley Ridge` in both |
| Backend process restart and page reload | Saved rows and edits remain | Same four places and edited nightly values appeared after restart and reload |
| Browser warnings/errors | None from the application | None reported in the browser console |

The save, duplicate, and remove actions above were exercised through the
FastAPI route with `TestClient`; the browser check exercised local lookup and
list/map selection. The Add to Local and Remove from Local buttons were not
manually clicked in this preflight; their request behavior is covered by the
existing automated tests. Live Geoapify search was not part of this check.
The existing nightly card renders `1 rooms` for a one-room fixture; this is a
small presentation issue outside Turn 0, recorded here rather than silently
changing the storage UI.

## Labeled temporary fixture for RAG checks

The manual check used an ignored temporary SQLite database, not the runtime
database or course CSVs. Saving each synthetic provider hotel with ZIP 16803
created the default October 10–14 demo nights. The following cells were
edited directly in that temporary database to make future RAG comparisons
meaningful; all unlisted cells kept the default $100 and 20 rooms.

| Synthetic hotel ID | Name | Oct 11 cents / rooms | Oct 12 cents / rooms |
| --- | --- | --- | --- |
| `fixture:campus-lantern` | Campus Lantern | 12000 / 2 | 11000 / 1 |
| `fixture:nittany-budget` | Nittany Budget | 10000 / 0 | 9000 / 3 |
| `fixture:college-green` | College Green | 15000 / 1 | **No record** |
| `fixture:valley-ridge` | Valley Ridge | 13000 / 2 | 14000 / 2 |

These are **simulated classroom rates and room counts**, not provider prices
or inventory. `fixture:remove-me` was saved and removed to check deletion.
The first hotel was saved a second time with altered provider text to check
duplicate preservation. No ZIP 16804 association was created.

Expected future questions and answers to check, before involving an LLM:

- For “three cheapest available saved hotels near 16803 on October 11,
  2026,” the three eligible hotels are Campus Lantern ($120), Valley Ridge
  ($130), and College Green ($150), in that order. Nittany Budget has zero
  rooms and must not be recommended.
- For check-in October 11 and checkout October 13, only October 11 and 12
  count. Campus Lantern totals $230; Valley Ridge totals $270. Nittany Budget
  has zero rooms on October 11. College Green lacks an October 12 row, so its
  two-night availability and total cannot be claimed.
- ZIP 16804 has no saved association in this fixture. October 15 has no
  nightly row. These are planned no-match and insufficient-data checks, not
  observed chatbot behavior.

The temporary database was removed after the browser check. Future automated
RAG tests should recreate these synthetic records in a test database, and the
report must label mocked or fixed data separately from live Gemini calls.

## Popup research and design decisions

- The [W3C disclosure pattern](https://www.w3.org/WAI/ARIA/apg/patterns/disclosure/)
  calls for a button whose `aria-expanded` reflects whether its controlled
  content is open. The floating chat launcher will use this pattern and
  return focus to the launcher when closed.
- The [W3C modal dialog pattern](https://www.w3.org/WAI/ARIA/apg/patterns/dialog-modal/)
  reserves `aria-modal="true"` for a popup that actually makes the page behind
  it inert. This chat should allow continued interaction with search and map,
  so the mockup is a **non-modal** popup with a visible close button and Escape
  handling, not a modal dialog.
- [MDN's log role guidance](https://developer.mozilla.org/en-US/docs/Web/Accessibility/ARIA/Reference/Roles/log_role)
  identifies ordered chat histories as logs. Use a named message log and a
  restrained status announcement for streaming completion or failure; avoid
  announcing every token. Keep the message list independently scrollable.
- Use the existing `--brand`, `--brand-dark`, `--brand-soft`, `--navy`, and
  `--surface` CSS palette. Mount the launcher at the app shell so it remains
  available across the current views. At desktop size, anchor the popup above the
  bottom-right launcher with a green border. At narrow width, use viewport
  margins and keep the input visible while the message area scrolls. Retain
  user and assistant messages when the popup closes and reopens. Show
  streaming, no-data, and retryable failure states without implying that
  stub or raw Gemini responses came from SQLite.

No dependency was added, and no chat source code was changed in Turn 0.
