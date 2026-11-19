# Writing TODO.md

Use `TODO.md` as a local issue tracker and a record of progress between sessions. Start with tasks from `ARCHITECTURE.md` and preserve their IDs where possible.

## Task Table

Give each task one row. Record its status, next step or blocker, and any useful verification result. Use **Pending**, **In progress**, **Blocked**, or **Done** consistently.

~~~markdown
# Project Tasks

| ID | Task | Status | Next step or verification |
| --- | --- | --- | --- |
| A-01 | Save a new task | Done | Verified that the saved task can be retrieved after refresh. |
| A-02 | Show saved tasks | In progress | Implement and verify the empty state. |
~~~

Read the table when resuming work and update it when the status changes. For a blocked task, state what needs to happen before work can resume. Mark a task **Done** after its completion criteria have been checked.
