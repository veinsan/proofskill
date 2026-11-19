# WORKFLOW: ProofSkill

How the coding agent works on this repository across sessions. Deliverable 3 is due 2026-11-27, 23:59 WIB.

## Start of every session

1. Read CLAUDE.md, this file, and TODO.md.
2. Pick the first task in TODO.md that is **Pending** or **In progress** and has no unresolved blocker.
3. Before touching code, read that task's step in ARCHITECTURE.md and the related user story in PRD.md.

## Working Rules

- **Proceed within scope.**
  - Work independently on clear tasks inside the agreed scope: PRD.md section 7, ARCHITECTURE.md steps A-01 to A-13, and the report's Bab X.
  - When time runs short, follow the report's mitigation: build the P0 features first (F-02, F-04, F-05, F-06), then simplify F-03 and F-07.
- **Ask when a decision matters.** Stop and ask the user before any of these:
  - Settling an Open Decision (OD-1 to OD-9).
  - Changing anything the report defines: endpoints, payloads, HTTP and error codes, enums, roles, BPMN-to-API mapping, features, or test scenarios.
  - Adding a dependency outside the locked stack.
  - Expanding scope beyond PRD.md, for example candidate search, a public chain, payments, or ATS integration.
  - Any action that needs permission under CLAUDE.md, such as staging or pushing.

  When a decision is needed, ask with concrete options and a recommended default.
- **Verify completion.**
  - A task is **Done** only after its completion criteria in ARCHITECTURE.md pass and its TCs pass.
  - Run the applicable checks: Hardhat tests, pytest, the Next.js build, and a browser check for UI.
  - Record the result and the command used in TODO.md.
  - For every TC, write an evidence record with `skill/run-test-scenario`.
  - If a check could not run, mark the task **Blocked** or **In progress** and say what is missing.
- **Hand off Git commands.** After code changes, summarize the work and give the user:
  - `git add -- <changed-files>`
  - `git diff --cached`
  - `git commit -m "<message>"`
  - `git push origin <branch>`

  The user stages, commits, and pushes.
- **Keep the project documents current.**
  - When a decision changes, update the source document first (PRD.md, ARCHITECTURE.md, DESIGN.md, or CLAUDE.md), then the affected TODO.md rows.
  - If the change also differs from the D1+D2 report or deck, name the exact report section or deck slide that must be updated (for example "report Tabel 9.2" or "deck slide REST API – Endpoint"). This repository must never drift silently from the report.

## Definition of done for Deliverable 3

- All in-scope endpoints work: API-00, 01, 02, 03, 04, 06, 07, 08, 09, 10.
- The web interface runs the three main flows.
- TC-01 to TC-16 each have an evidence record.
- T-01 to T-05 have measured values.
- The limitations and the next development plan are written down for the report.
