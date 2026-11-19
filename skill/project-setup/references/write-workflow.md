# Writing WORKFLOW.md

Document how the coding agent should work across sessions. Make it clear when it can proceed, when it needs the user's decision, and what counts as finished.

## Working Rules

- **Proceed within scope.** Read the relevant project instructions and open tasks. Work independently on clear, authorized changes within the agreed scope.
- **Ask when a decision matters.** Clarify ambiguous requirements that affect the implementation. Ask before expanding the agreed scope or taking an action that requires permission under the project's rules.
- **Verify completion.** Check the task's completion criteria in `ARCHITECTURE.md` and any relevant acceptance criteria in `PRD.md`. Run the applicable tests, build, or manual checks. Record the result in `TODO.md` and surface any check that remains pending.
- **Hand off Git commands.** After code changes, summarize the work and provide `git add -- <changed-files>`, `git diff --cached`, `git commit -m "<message>"`, and `git push <remote> <branch>` for the user to run. Use known repository details and flag unknown values. The user performs staging, commits, and pushes.
- **Keep the project documents current.** When an agreed decision changes, update the relevant source document and any affected task entries.
