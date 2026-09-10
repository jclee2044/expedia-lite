# [Assignment 1] From Application Decomposition to Working Implementation

## Background

Week 1 introduced application decomposition: interface, logic, data, and persistence. Week 2 connected this view to practical agentic development through visual references, project organization, manual review, Git, and browser verification. This assignment brings those skills together in one project with two submission points.

Each student submits an independently authored project. Peer discussion and feedback are encouraged; the student remains responsible for explaining the design, reviewing generated changes, and verifying the submitted application.

## Problem Statement

Study **Expedia** or a comparable travel-booking application. Develop a small local application around two connected flows:

1. **Make a booking:** move from a search or selection through a simulated booking confirmation.
2. **Review booking history:** find and inspect the record of bookings made in the application.

The student defines a manageable version of these flows. The Thursday submission establishes the intended behavior and the starting repository. The Monday submission implements that scope and includes the updated design and process evidence.

## Related Work

Use the selected travel application as an observable reference. Record its URL and use a small number of relevant screenshots, annotations, or sketches to communicate the chosen scope. Attribute any starter project, reused code, or external assets.

The course references for this work are:

- **Activity 1 — Agentic UI Development**
- **Activity 2 — Review, Version, and Share Agent Work**

Nearly every application separates into the same four concerns. A visible screen is evidence of those layers, not the whole system. The interface can be observed directly; data, logic, and persistence must be inferred from the values shown, the decisions made, and what the application remembers.

### The Four Layers Behind an Application Screen

| Layer | The question it answers | How to find it from the outside |
|---|---|---|
| **Data** | What things exist in this system, and what does each know about itself? | Every noun the interface shows is a candidate: property, offer, traveler, booking, and itinerary. |
| **Logic** | What decisions does the system make that the user does not? | Look for anything ranked, filtered, calculated, validated, classified, or refused. Why is this result shown first? |
| **Persistence** | What survives? What is remembered after the tab closes? | Return later or sign in again. What remains was persisted; what disappeared may have existed only in the interface. |
| **Interface** | What does the user see and manipulate? | This is the only layer that can be observed directly. Begin here, then infer what must exist underneath. |

The following figures read one Expedia screen from the outside in.

### Figure 1 — Evidence Available from Outside the Application

> Expedia mobile results screen showing selected dates and travelers, filter controls, two hotel cards, ratings, bundle savings, and package prices.

**Figure 1.** The evidence available from outside the application: one rendered results screen. Source: Expedia App Store listing. © Expedia Group.

### Figure 2 — Interface Structure

> Annotated Expedia screen with blue outlines identifying the page header, filter controls, repeated result-card template, and reusable price module.

**Figure 2.** Interface structure: stable regions that organize changing content. Annotation adapted from the Expedia App Store image. © Expedia Group.

### Figure 3 — Data and Logic

> Annotated Expedia screen with data values marked in green and logic outcomes marked in orange, including filters, ranking, refundability, and calculated savings.

**Figure 3.** Data and logic share the screen but answer different questions: what the system knows and what it decides. Annotation adapted from the Expedia App Store image. © Expedia Group.

### Figure 4 — Inferred System View

> Diagram showing a traveler interacting with an interface, the interface exchanging requests and ranked results with logic, logic querying data, and logic saving and retrieving persistent state.

**Figure 4.** An inferred system view. The screen is an assembled result of four interacting layers, not the system itself.

## Challenges

- Translate visible screens into actions, rules, data, and records that must remain available.
- Assign responsibilities to the frontend and backend, including how they communicate.
- Give the agent enough project context to proceed without inventing important requirements.
- Review changes against the intended scope, preserve useful Git checkpoints, and verify behavior in the browser.

## Objective and Scope

Deliver a working local prototype of both required flows at the scope established in Part 1.

The application must:

- Use synthetic travel records and simulated booking confirmations.
- Have a frontend and a backend with identifiable responsibilities.
- Use the backend for a meaningful part of the required workflow.
- Make booking records created through the interface available in the history flow.
- Keep booking records available after a browser refresh while the application is running.
- Document the storage choice and what survives an application restart.
- Make the lifetime of stored data explicit.
- Use a technology stack chosen and explained by the student.

The course starter may be reused with attribution. Choose tools that can be set up, understood at the level of their responsibilities, and completed within the assignment period.

Keep the scope small enough to finish both flows.

> **Design changes:** Treat a material change to the Thursday plan as a design decision. Record what changed, why, and how the revised behavior was verified.

# Implementation Phases

## Part 1 — Decomposition and Project Setup

**Due:** Thursday, September 10, during class, by **2:50 PM ET**

Prepare a design and a repository that can support implementation.

### 1. Decomposition and Flows

- Identify the interface, logic, data, and persistence responsibilities.
- Diagram both required flows.
- Describe their main steps.
- Describe meaningful failure or empty states.
- Connect each step to the responsible part of the application.

### 2. Technology Decisions

Identify:

- Frontend
- Backend
- Communication approach
- Data/storage approach

For each major choice:

- Give a practical reason for the choice.
- Explain how the pieces work together.

### 3. Folder Structure

Create the intended project structure in a repository and explain the purpose of its major folders and files.

Accurately mark:

- Starter code
- Placeholders
- Planned components

### 4. Git Starting Point

- Review the setup.
- Commit the planning checkpoint.
- Push it to GitHub.
- Identify the branch intended for implementation.
- The Canvas submission must identify the **exact Part 1 commit**.

### 5. Project Context and Handoff

Use the following files:

- `README.md` — orient the reader.
- `AGENTS.md` — state project-specific instructions.
- `handoffs/current.md` — maintain the current handoff.
- `prompts/` — preserve major project instructions in an ordered folder.

The current handoff must describe:

- What exists.
- What has been checked.
- What remains incomplete.
- The next concrete implementation task.

Link the `prompts/` materials from the evidence log as appropriate.

### Handoff Requirements

A handoff is a short continuation note for another person or a new agent session.

It must describe the repository **as it actually stands**.

Distinguish between:

- A plan
- A generated file
- A verified working feature

These are different states and should be labeled accordingly.

> The full application is due in Part 2. For Thursday, the repository must make the intended design, current state, and next work inspectable.

---

## Part 2 — Full Implementation and Final Submission

**Due:** Monday, September 14, at **11:59 PM ET**

Complete the planned application in the same repository.

### Implementation Requirements

- Implement both flows so that a booking made through the interface can be found in booking history.
- Use screenshots, sketches, and focused annotations to guide the interface.
- Explain important behavior that the visual reference leaves unspecified.
- Manually review changed files in VS Code.
- Exercise the application before asking the agent to commit accepted changes.
- Develop substantial changes on a feature branch.
- Merge reviewed and tested work into `main`.
- Check the combined application.
- Push the final `main` branch to GitHub.
- Update the following to match the completed repository:
  - Design
  - Folder map
  - README
  - Agent instructions
  - Selected prompts
  - Tool disclosure
  - Evidence log
  - Handoff
- Demonstrate both required flows.
- Demonstrate a meaningful failure or empty case.
- Include a brief record of using the handoff to resume work in a fresh agent session.
- Document what was inspected or checked before continuing.

The final submission includes the complete work, including the revised Part 1 documents.

> **Important:** Preserve the original Part 1 commit so the development from plan to implementation remains visible.

# Deliverables

## Thursday Submission

Submit **Part 1 — Decomposition and Project Setup**.

Submit one Canvas entry containing:

- Repository URL
- Part 1 commit link or identifier
- Links to the design files
- Links to the handoff files

The repository must contain:

- Decomposition
- Two flow descriptions
- Technology choices
- Explained folder structure
- Project instructions
- Current status

During class, the student should be able to locate these artifacts and explain how one user action moves from the interface to the backend and becomes a record available to the history flow.

## Monday Submission

Submit **Part 2 — Full Implementation and Final Submission**.

Submit:

- Repository URL
- Final `main` commit
- Short screencast demonstrating the required behavior
- Links to the final design
- Links to verification evidence
- Link to the handoff

The README must provide usable setup and run instructions.

Ensure that the instructor can access the submitted repository and media.

### Evidence Log

The evidence log should connect selected major instructions to:

1. The resulting change
2. A manual review or browser check
3. The decision taken
4. Any remaining limitation

Include a failed or revised approach when one occurred.

Also identify:

- AI tools used
- Models used
- Their roles

A concise, redacted record is sufficient.

# Evaluation Criteria

## Assignment 1 Submission Structure

| Submission | What is assessed | Canvas points |
|---|---|---:|
| **Part 1 — Decomposition and Project Setup** | A coherent, feasible design; justified technology choices; an inspectable repository and Git checkpoint; and a truthful, useful handoff. | **100** |
| **Part 2 — Full Implementation and Final Submission** | Working required flows; appropriate frontend/backend responsibilities; evidence of manual review and browser verification; and a reproducible final repository with current documentation. | **100** |

The two parts are separate **100-point Canvas submissions** and carry equal weight within the **10% Assignment 1 group**.

- Each part contributes **5% of the course grade**.
- The overview is not a separate graded submission.

### How Each Part Is Judged

**Part 1** is judged as the project's starting design and state at the Thursday checkpoint.

**Part 2** is judged as the implementation and evidence delivered on Monday.

Quality depends on the **coherence of the work and the evidence supporting it**, rather than the number of:

- Files
- Commits
- Screenshots
- Prompts

# Ethical Considerations

- Use synthetic identities and booking records in the local application.
- Observe the reference application without completing a real purchase.
- Do not copy private account information into the submission.
- Attribute reused material.
- Disclose AI assistance.
- Remove credentials and personal information from:
  - Screenshots
  - Logs
  - Repository files
  - Demonstrations
