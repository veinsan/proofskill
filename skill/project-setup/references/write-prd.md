---
name: write-prd-md
description: Use when an application needs a new or revised PRD.md to align product goals, user needs, requirements, and MVP scope before coding.
---

# Writing PRD.md

Create one `PRD.md` (Product Requirements Document) as a shared reference for the project owner and the AI before coding. Explain what to build, who it serves, and why, so feature and flow decisions are clear from the start.

## How to Write the PRD

Use the project brief to fill in the seven main sections in the order below. Flag important decisions that still need confirmation, including metric targets or MVP boundaries that have yet to be set. Add the title, status, author, and last-updated date at the top where that information is available.

1. **Problem Statement** — Explain the current problem and its impact on users. Give enough context to understand the need for the product.
2. **Goals** — State the intended outcomes and the metrics used to assess success. Include agreed targets.
3. **Target Users** — Identify who uses the finished product, who manages or owns the project, and who builds it (AI or developer). Include the roles relevant to the project.
4. **User Stories** — Use the form `As a [user], I want [feature] so that [benefit]`. Add testable *acceptance criteria* to each story so it is clear when the story is complete.
5. **Functional Requirements** — List the essential features and behaviors the app must provide. Separate requirements so each can be tested individually. Keep the list within the MVP and describe observable behavior.
6. **Non-Functional Requirements** — State relevant quality requirements such as performance, security and privacy, capacity for user growth, and responsive layouts. Use thresholds or conditions that can be checked.
7. **Scope** — Separate **In scope** items for the current version from **Out of scope** items that are deferred. Keep the PRD up to date. Record agreed scope changes here and update any sections they affect.

Before coding, check that every story has completion criteria, every essential feature is in scope, and deferred features are listed separately.

## Example PRD.md

Adapt this example to your project's needs and boundaries.

~~~markdown
# PRD — To-Do List

> **Status** Draft

## 1. Problem Statement

Users often forget tasks, struggle to prioritize them, and keep disorganized manual notes. Important tasks get missed, and daily productivity drops.

## 2. Goals

Provide a simple task tracker for recording tasks, setting priorities, and marking tasks as complete.

- The task completion rate increases compared with the period before using the app.
- Opening the app takes less than one minute.

## 3. Target Users

- **End users** — Students, freelancers, and workers who want to organize daily tasks.
- **Stakeholder** — The project owner who defines what the app needs.
- **AI/developer** — The party that builds the app from this PRD.

## 4. User Stories

- As a user, I want to add a task so that I remember it.
  - **Acceptance criteria** — A newly saved task appears in the list.
- As a user, I want to mark a task complete so that I can track my progress.
  - **Acceptance criteria** — A task marked complete displays the completed status.
- As a user, I want to sort tasks by priority so that I can focus on important tasks.
  - **Acceptance criteria** — When priority sorting is active, higher-priority tasks appear first.

## 5. Functional Requirements

- Users can add tasks.
- Users can view the task list.
- Users can edit tasks.
- Users can delete tasks.
- Users can mark tasks as complete.
- Users can filter tasks by priority.
- Users can sort tasks by priority.

## 6. Non-Functional Requirements

- The initial view loads in less than one second.
- Task data stays in the browser in `localStorage` and is never sent to a server.
- The layout is responsive on mobile and desktop devices.

## 7. Scope

- **In scope** — Add, view, edit, and delete tasks. Mark tasks complete and filter and sort by priority.
- **Out of scope** — Login, team collaboration, reminder notifications, and cloud sync.
- **Changes** — Record agreed changes to scope here.
~~~
