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
| A-01 | Scaffold `contracts/`, `api/`, `web/`, PostgreSQL, `.env.example` | Done | 2026-11-19. pnpm and uv chosen. PostgreSQL 17.11 runs as a project-local cluster (`scripts/db.ps1 start`, port 5433). Verified: `pnpm chain` serves 8545, `uv run pytest` 1 passed, `uv run fastapi dev app/main.py` serves `/api/v1/docs` (200), `pnpm lint` and `pnpm build` pass in `web/`. Versions and commands are in CLAUDE.md. |
| A-02 | `ProofSkillRegistry` contract and contract tests | Done | 2026-11-19. `pnpm test` in `contracts/`: 11 passing, covering issue, revoke, read, an unregistered issuer that cannot issue, and the other-issuer revoke that reverts with the status unchanged (TC-14). `pnpm deploy:local` deploys to the local node and writes `deployments/localhost.json`. OD-2 then added `deactivateIssuer` and `issuerActive` in `getRecord`: 14 passing, including TC-16 at contract level. |
| A-03 | Off-chain schema and synthetic seed (ISS-001, ISS-002, accounts, catalog, positions) | Pending | Needs A-01 and A-02. Follow OD-5 (fixed `holderRef` per holder account) and OD-6 (canonical payload, stored nonce). Include a `platform_admin` account (OD-1) and the `notifications` table (OD-3). |
| A-04 | F-01 auth and RBAC (API-00, API-01) | Pending | Needs A-03. API-01 accepts only `platform_admin` (OD-1). |
| A-05 | Skill catalog (API-08) | Pending | Needs A-03. |
| A-06 | F-02 issuance (API-02) | Pending | Needs A-02, A-04, and A-05. Verify with TC-01, TC-02, and TC-03. |
| A-07 | F-03 credential view and share links (API-03, API-04; API-05 optional) | Pending | Needs A-06. Scope fields and the 1–720 hour expiry follow OD-4. |
| A-08 | F-04 verification (API-06) | Pending | Needs A-07. Verify with TC-04, TC-05, TC-07, TC-11, TC-12, and TC-16. |
| A-09 | F-05 revocation (API-09) | Pending | Needs A-08. Verify with TC-06 and TC-14. |
| A-10 | F-06 skill matching (API-07) | Pending | Needs A-05 and A-08. Verify with TC-08, TC-09, TC-10, and TC-15. AMS runs as its own process on port 8001 (OD-8) and uses the OD-7 matching rules. |
| A-11 | F-07 audit trail (API-10) | Pending | Needs A-06, A-08, A-09, and A-10. Verify with TC-13. |
| A-12 | F-08 web interface for three portals | Pending | Needs A-06 to A-11. Follow DESIGN.md and `.impeccable/surfaces/`, and finish with the impeccable detector and finish review. |
| A-13 | Run TC-01 to TC-16 and measure T-01 to T-05 | Pending | Needs A-12. Use `skill/run-test-scenario` to write each record in `docs/evidence/`. |

## Decisions needed

Details are in [PRD.md Open Decisions](PRD.md#open-decisions).

| ID | Decision | Status | Blocks |
| --- | --- | --- | --- |
| OD-1 | Platform-admin role for API-01, and names for the unnamed error codes of API-01, API-03, and API-05 | Done (2026-11-19) | A-04, A-07 |
| OD-2 | How ISSUER_UNAUTHORIZED can occur, and the TC that covers it | Done (2026-11-19) | A-02, A-08 |
| OD-3 | Notification channel for T06 and T27 | Done (2026-11-19) | A-06, A-09 |
| OD-4 | Allowed share-scope fields, maximum link expiry, maximum position-text length | Done (2026-11-19) | A-07, A-10 |
| OD-5 | Mapping from a holder account to `holderRef` | Done (2026-11-19) | A-03 |
| OD-6 | Canonical payload form and field list for the hash commitment | Done (2026-11-19) | A-03, A-06 |
| OD-7 | Similarity threshold and how a position description is split into requirements | Done (2026-11-19) | A-10 |
| OD-8 | How the AI service is switched off for TC-10 | Done (2026-11-19) | A-10 |
| OD-9 | Report versus deck: three or four verification results, and interview status | Pending | D-03, D-05 |

## D3 report and presentation

| ID | Task | Status | Next step or verification |
| --- | --- | --- | --- |
| D-01 | Write the Deliverable 3 chapter covering the prototype, the role of blockchain and AI with the differentiator tests, TC-01 to TC-16 documentation, results against T-01 to T-05, limitations, and the next development plan | Pending | Needs A-13. Each test row needs scenario, steps or input, expected result, actual result, status, and evidence. |
| D-02 | Add a D3 task-assignment table at the start of the report, update Penutup, and add Lampiran (repository link, evidence) | Pending | The report's structure must still match the course template: cover through Lampiran. |
| D-03 | Record the R1–R4 interview findings in report Tabel 4.17–4.18 and fix the "no interviews yet" statements, or reword the deck slide | Pending | Needs OD-9. |
| D-04 | Restore the body of "Catatan Revisi" in the Google Doc | Pending | The Daftar Isi and the task table point to it. The content exists in the D1 revision docx and the deck appendix. |
| D-05 | Align the deck's verification slides with the report's four results | Pending | Needs OD-9. |
| D-06 | Build the D3 deck: main service flow demo, API interactions, technology contribution, plus a recorded demo video as a backup | Pending | Needs A-12 and A-13. |
| D-08 | Update the report for the OD-1 to OD-8 decisions of 2026-11-19 | Pending | Tabel 9.15 and 9.16 plus the 9.5 error codes (`platform_admin`, named codes, `ISSUER_ALREADY_REGISTERED`); Tabel 8.5 `RegistryRecord` (`issuerActive`) and the Bab X contract function list (`deactivateIssuer`); Tabel 10.4 (TC-16); Gambar 10.1 (AMS as its own process); the API-02, API-04, and API-07 notes in 9.3 (canonical payload, scope and expiry limits, position-text limit, matching rules); T06/T27 and the deck blueprint (simulated email). |
| D-07 | Export the final single PDF (D1+D2+D3) and the final deck | Pending | Needs D-01 to D-06 and D-08. Submit by 2026-11-27, 23:59 WIB. |
