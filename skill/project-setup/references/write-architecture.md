# Writing ARCHITECTURE.md

Use `PRD.md` to turn the agreed scope into an implementation plan. For an existing project, distinguish the current system from planned changes.

## Structure

1. **Technical stack** — Record the framework, database, and hosting choice. Mark decisions that still need confirmation.
2. **System structure** — Describe the main components, their responsibilities, and how they exchange data. Use repository paths where they help developers find the implementation.
3. **Implementation plan** — Break the work into small steps in dependency order. For each step, give it a stable ID, describe the deliverable, and say how to tell when it is done.

~~~markdown
## Technical Stack

| Area | Choice |
| --- | --- |
| Framework | [Chosen framework] |
| Database | [Chosen database] |
| Hosting | [Chosen host or pending decision] |

## System Structure

[Describe the main components and the data flow between them.]

## Implementation Plan

| ID | Step | Depends on | Completion criteria |
| --- | --- | --- | --- |
| A-01 | Save a new task | — | A valid task is saved and can be retrieved after a refresh. |
| A-02 | Show saved tasks | A-01 | The task list displays saved tasks and shows an empty state when there are none. |
~~~

Use the same IDs in `TODO.md` where possible so progress can be traced back to the implementation plan.
