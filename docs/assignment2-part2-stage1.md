# Part 2 Turn 1 — working stub chat checkpoint

Observed October 6, 2026 on `rag_integration`. This is a scripted frontend
preview, not a Gemini or SQLite-backed answer. The working preview is at
`http://127.0.0.1:5173/` while the task-owned development servers are running.

## What changed

- `frontend/src/components/ChatPopup.vue` adds a bottom-right, green-bordered,
  non-modal popup on every app view. It keeps the current page session's
  conversation when closed and reopened. Enter sends, Shift+Enter adds a line,
  and Escape closes and returns focus to the launcher.
- `frontend/src/chat/stubStream.js` emits four timed chunks. `/fail` triggers
  a labeled partial failure; Retry completes the existing question without
  creating a second user message.
- `frontend/src/assets/main.css` styles the scrollable log, composer,
  streaming and error states, and narrow layout. `frontend/src/App.vue`
  mounts the popup. `README.md` documents the preview and its limits.
- `frontend/tests/chatStub.test.js` checks chunk order, simulated failure,
  and cancellation. No dependency or backend code was added for chat.

## Expected versus observed

| Check | Expected | Observed |
| --- | --- | --- |
| `npm test` | Existing frontend and new stub tests pass | 24 passed |
| `npm exec -- oxlint .` and `npm exec -- eslint .` | No lint errors | Both passed |
| `npm run build` | Production build succeeds | Passed; 31 modules transformed |
| `git diff --check` on Turn 1 files | No whitespace errors | Passed |
| First message | Loading appears, then chunks append in one assistant bubble | Observed in browser |
| Close/reopen and view navigation | Existing conversation remains | Observed after reopening and moving between Search and Account |
| Failure and retry | Partial reply marked interrupted, then retry works | Observed with `/fail`; no duplicate user message |
| Scroll behavior | Log scrolls independently; reading earlier text is not pulled to the end | Measured overflow and scrolled to top; streaming did not force scroll to bottom |
| Keyboard | Escape restores launcher focus; Shift+Enter adds a line | Both observed; empty Enter prompted for a question |
| Narrow layout | Popup and input remain in viewport | At a 240 px requested viewport (320 CSS px minimum), document width stayed 320 px; log scrolled and input remained visible |
| Browser warnings/errors | None from the app | Browser warning/error log was empty |

The browser check used an ignored temporary SQLite database solely to run
the existing app; no hotel data was needed for the stub. The live preview
remains on the Search view with the chat open so the student can inspect it.
The task-owned backend and Vite servers are on ports 8000 and 5173.

The ignored project-root `.env` contains a nonblank `GEMINI_API_KEY`; only a
boolean presence check was printed. The selected model is
`gemini-3.5-flash-lite`. No model call was made in Turn 1, and access and
current free-tier limits remain to be verified before Turn 2's live call.
This checkpoint does not prove Gemini streaming, hotel retrieval, or history
after a page refresh.
