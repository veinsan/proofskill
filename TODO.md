# Project Tasks

Deliverable 3 (prototype and testing) is due **Friday 2026-11-27, 23:59 WIB**. The D3 presentation is 2026-12-02 or 2026-12-04 (10–15 minutes). Read this file at the start of every session and update it whenever a status changes.

Status values: **Pending**, **In progress**, **Blocked**, **Done**. Task IDs match [ARCHITECTURE.md](ARCHITECTURE.md).

## Setup

| ID | Task | Status | Next step or verification |
| --- | --- | --- | --- |
| S-01 | Project documents: PRD, CLAUDE, DESIGN, ARCHITECTURE, TODO, WORKFLOW, `skill/run-test-scenario`, plus PRODUCT.md for impeccable | Done | Created 2026-11-19 from the D1+D2 report and deck. Re-check them against the report whenever a decision below is settled. |

## Prototype

| ID | Task | Status | Next step or verification |
| --- | --- | --- | --- |
| A-01 | Scaffold `contracts/`, `api/`, `web/`, PostgreSQL, `.env.example` | Blocked | PostgreSQL is not installed on this machine (`psql` and `docker` are not on PATH). Install PostgreSQL or choose another way to run it, and choose the Node and Python package managers. Then scaffold and record versions and commands in CLAUDE.md. |
| A-02 | `ProofSkillRegistry` contract and contract tests | Pending | Needs A-01. Done when issue, revoke, and read tests pass and a revoke from another issuer reverts (TC-14). Open Decision 2 may add an issuer-suspend function. |
| A-03 | Off-chain schema and synthetic seed (ISS-001, ISS-002, accounts, catalog, positions) | Pending | Needs A-01 and A-02. Open Decisions 5 and 6 affect the schema. |
| A-04 | F-01 auth and RBAC (API-00, API-01) | Pending | Needs A-03. API-01's role depends on Open Decision 1. |
| A-05 | Skill catalog (API-08) | Pending | Needs A-03. |
| A-06 | F-02 issuance (API-02) | Pending | Needs A-02, A-04, and A-05. Verify with TC-01, TC-02, and TC-03. |
| A-07 | F-03 credential view and share links (API-03, API-04; API-05 optional) | Pending | Needs A-06. Open Decision 4 sets the scope fields and maximum expiry. |
| A-08 | F-04 verification (API-06) | Pending | Needs A-07. Verify with TC-04, TC-05, TC-07, TC-11, and TC-12. |
| A-09 | F-05 revocation (API-09) | Pending | Needs A-08. Verify with TC-06 and TC-14. |
| A-10 | F-06 skill matching (API-07) | Pending | Needs A-05 and A-08. Verify with TC-08, TC-09, TC-10, and TC-15. Open Decisions 7 and 8 must be settled first. |
| A-11 | F-07 audit trail (API-10) | Pending | Needs A-06, A-08, A-09, and A-10. Verify with TC-13. |
| A-12 | F-08 web interface for three portals | Pending | Needs A-06 to A-11. Follow DESIGN.md and `.impeccable/surfaces/`, and finish with the impeccable detector and finish review. |
| A-13 | Run TC-01 to TC-15 and measure T-01 to T-05 | Pending | Needs A-12. Use `skill/run-test-scenario` to write each record in `docs/evidence/`. |

## Decisions needed

Details are in [PRD.md Open Decisions](PRD.md#open-decisions).

| ID | Decision | Status | Blocks |
| --- | --- | --- | --- |
| OD-1 | Platform-admin role for API-01, and names for the unnamed error codes of API-01, API-03, and API-05 | Pending | A-04, A-07 |
| OD-2 | How ISSUER_UNAUTHORIZED can occur, and the TC that covers it | Pending | A-02, A-08 |
| OD-3 | Notification channel for T06 and T27 | Pending | A-06, A-09 |
| OD-4 | Allowed share-scope fields, maximum link expiry, maximum position-text length | Pending | A-07, A-10 |
| OD-5 | Mapping from a holder account to `holderRef` | Pending | A-03 |
| OD-6 | Canonical payload form and field list for the hash commitment | Pending | A-03, A-06 |
| OD-7 | Similarity threshold and how a position description is split into requirements | Pending | A-10 |
| OD-8 | How the AI service is switched off for TC-10 | Pending | A-10 |
| OD-9 | Report versus deck: three or four verification results, and interview status | Pending | D-03, D-05 |

## D3 report and presentation

| ID | Task | Status | Next step or verification |
| --- | --- | --- | --- |
| D-01 | Write the Deliverable 3 chapter covering the prototype, the role of blockchain and AI with the differentiator tests, TC-01 to TC-15 documentation, results against T-01 to T-05, limitations, and the next development plan | Pending | Needs A-13. Each test row needs scenario, steps or input, expected result, actual result, status, and evidence. |
| D-02 | Add a D3 task-assignment table at the start of the report, update Penutup, and add Lampiran (repository link, evidence) | Pending | The report's structure must still match the course template: cover through Lampiran. |
| D-03 | Record the R1–R4 interview findings in report Tabel 4.17–4.18 and fix the "no interviews yet" statements, or reword the deck slide | Pending | Needs OD-9. |
| D-04 | Restore the body of "Catatan Revisi" in the Google Doc | Pending | The Daftar Isi and the task table point to it. The content exists in the D1 revision docx and the deck appendix. |
| D-05 | Align the deck's verification slides with the report's four results | Pending | Needs OD-9. |
| D-06 | Build the D3 deck: main service flow demo, API interactions, technology contribution, plus a recorded demo video as a backup | Pending | Needs A-12 and A-13. |
| D-07 | Export the final single PDF (D1+D2+D3) and the final deck | Pending | Needs D-01 to D-06. Submit by 2026-11-27, 23:59 WIB. |
