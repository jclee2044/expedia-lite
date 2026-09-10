# Expedia Lite handoff procedure

Use these prompts when work must move to a new thread or model because the current thread is long, an account usage limit is reached, or another model will continue the project.

`handoffs/current.md` is intentionally not permanent history. Create or refresh it only when a handoff is needed, and verify it against the repository before resuming work.

## Prompt to create or refresh the handoff

```text
Create or refresh handoffs/current.md so a new coding agent can continue Expedia Lite without access to this conversation.

The current thread may be too long, the model may have reached an account usage limit, or another model may take over. Give the next agent enough verified context to continue without guessing.

Before writing, read AGENTS.md, README.md, docs/design-pipeline.md, docs/verification.md, and the relevant files under prompts/. If a named file does not exist, report that gap instead of inventing its contents. Use the repository as the source of truth; do not rely on chat memory. Check the Git root, current branch, HEAD commit, working-tree status, recent commits, configured remotes, and any running project services that can be inspected safely.

The handoff must contain:
1. the current objective and the user's important decisions;
2. a concise architecture and important-file map;
3. the current branch, HEAD commit, relevant branches, upstream relationships, and whether the working tree is clean;
4. completed work, with file paths and commit identifiers where available;
5. incomplete or requested work;
6. exact verification commands already run and their observed results;
7. active services, ports, and how they were started, or a clear statement that none were verified;
8. known failures, unresolved questions, risks, and assumptions;
9. the recommended next action and the files the next agent should read first; and
10. a short list separating verified facts from claims that still require verification.

Do not include secrets, tokens, private URLs, private traveler data, or unnecessary conversation. Do not claim that a check passed unless evidence is available. Do not change application code, dependencies, Git history, branches, remotes, or running services. Write only handoffs/current.md, then show its path and summarize the repository evidence used.
```

## Prompt to resume from the handoff

```text
Read AGENTS.md, README.md, handoffs/current.md, docs/design-pipeline.md, and docs/verification.md before editing. If a named file does not exist, report that gap instead of guessing.

You may not have access to the previous conversation. Reconstruct the current Expedia Lite state from repository evidence before making changes.

Verify the handoff before trusting it. Check the Git root, current branch, HEAD commit, working-tree status, and the files and verification results named in the handoff.

Report:
- which handoff claims still match the repository;
- which claims are stale, missing, or cannot be verified;
- the current objective and proposed next step;
- the expected file-level blast radius; and
- any decision or permission needed from me.

Do not modify files, install dependencies, change Git state, or start or stop services until I review the reconstruction and approve the next step.
```

A handoff is a starting point, not proof. The receiving agent must independently verify it against the repository before editing.
