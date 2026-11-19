---
name: project-setup
description: >
  Use when starting a project, setting up its documentation, or resuming work that
  needs the project's requirements, agent instructions, design rules, implementation
  plan, task status, reusable prompts, or workflow.
---

# Project Documentation Workflow

## Language

Write and maintain the project documents in English. Use the project's own names, paths, and commands.

## Core Workflow

1. **Read the project first.** Find the brief, existing documents, repository structure, and available verification commands. Keep accurate documents and agreed decisions. Flag gaps that need the user's decision.
2. **Set up the seven core artifacts.** Read the matching references below. Create missing documents and update existing ones only where needed. Use the PRD as the source for scope, the architecture plan for implementation, and the task table for current status. Finish this setup before starting implementation when the request includes both.
3. **Start or resume work.** Read the instructions for the coding agent, `WORKFLOW.md`, and `TODO.md`. Use the PRD, architecture, design, and relevant local skill to work through the next task within the agreed scope.
4. **Verify and update.** Apply the task's completion criteria and record the result in `TODO.md`. Update the relevant document when a product, design, technical, or process decision changes. Record blockers and unverified work so the next session can pick up from the right point.

For a request about a single document, load its reference and the project context needed for that document.

## Project Structure

| Order | Artifact | Role | Reference |
| --- | --- | --- | --- |
| 1 | `PRD.md` | The project’s North Star. Explain what to build, for whom, and why. Define the MVP and what is out of scope. | [Writing PRD.md](references/write-prd.md) |
| 2 | `CLAUDE.md` or `AGENTS.md` | Instructions the coding agent and another developer can both follow. Choose the file for the agent in use. Keep shared rules consistent if both are needed. | [Writing CLAUDE.md](references/write-claude-md.md) |
| 3 | `DESIGN.md` | Shared visual rules for color, typography, spacing, shapes, layout, and components. Define tokens and explain how to apply them. | [Writing DESIGN.md](references/write-design.md) |
| 4 | `ARCHITECTURE.md` | Technical plan and stack, broken into small implementation steps with clear completion criteria. | [Writing ARCHITECTURE.md](references/write-architecture.md) |
| 5 | `TODO.md` | Local issue tracker. Use a Markdown table to record task status, blockers, and progress across sessions. | [Writing TODO.md](references/write-todo.md) |
| 6 | A project-local `<skill-name>/SKILL.md` | A reusable prompt and procedure for a task such as testing, security review, or refactoring. Use the project's skill directory convention, or `skills/` as a documentation default. Keep this package's entry point separate from skills it creates. | [Writing a Project Skill](references/write-skill.md) |
| 7 | `WORKFLOW.md` | Working rules for when the agent can proceed, when to ask, and when a feature is done. | [Writing WORKFLOW.md](references/write-workflow.md) |

If the project's recurring procedures are still taking shape, start with one useful task from the brief or verification plan. Keep uncertain commands and decisions visible as pending.

## Working Boundaries

- Use `CLAUDE.md` for Claude Code and `AGENTS.md` for agents that use that filename. When adapting the Claude example to `AGENTS.md`, adapt the agent references and preserve the project rules.
- The user handles Git staging, commits, and pushes. After completing code changes, provide the relevant `git add`, `git diff --cached`, `git commit`, and `git push` commands for the user to run.
- [Writing README.md](references/write-readme.md) is an additional reference for creating or refreshing the repository's public overview and setup instructions. Load it when the task includes a README.
