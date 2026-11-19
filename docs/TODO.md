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
| A-03 | Off-chain schema and synthetic seed (ISS-001, ISS-002, accounts, catalog, positions) | Done | 2026-11-19. `api/migrations/001_init.sql` holds the schema, including fixed `holderRef` per holder (OD-5), nonce and commitment columns (OD-6), and `notifications` (OD-3). `uv run python -m app.seed --reset` loads 2 issuers, 8 accounts (all four roles, two verifiers, an issuer admin without an issuer for TC-02), 15 skills, and 3 positions, then registers both issuers on-chain. `uv run pytest`: 4 passed, covering migrations on an empty database, a repeatable seed, and database issuers matching registry issuers. |
| A-04 | F-01 auth and RBAC (API-00, API-01) | Done | 2026-11-19. API-00 returns a 1-hour HS256 JWT carrying the role (PyJWT), or 401 `INVALID_CREDENTIALS`. API-01 accepts only `platform_admin` and writes the issuer to the database and the registry. It returns 403 `FORBIDDEN_ROLE` to other roles, 409 `ISSUER_ALREADY_REGISTERED` for a duplicate, and 503 `REGISTRY_UNAVAILABLE` (storing nothing) when the chain is down. Errors use the uniform body with `requestId`. `uv run pytest`: 25 passed, repeatable, because each session deploys its own registry and each test reverts the chain with `evm_snapshot`. |
| A-05 | Skill catalog (API-08) | Done | 2026-11-19. `GET /api/v1/skills?query=&limit=&offset=` returns `{items: [{skillId, label, aliases}], total}` to any signed-in role. `query` matches label or alias case-insensitively, with `%` and `_` taken literally. `limit` defaults to 20 (1–100) and `offset` to 0; values out of range return 400 `MALFORMED_REQUEST`. `uv run pytest`: 39 passed. |
| A-06 | F-02 issuance (API-02) | Done | 2026-11-19. `POST /api/v1/credentials` checks the issuer (403 `ISSUER_NOT_AUTHORIZED`, also for an issuer deactivated on the registry) and the catalog (422 `SKILL_NOT_IN_CATALOG`). It stores metadata with a 32-byte nonce, hashes the OD-6 canonical payload, anchors it with `issueCredential` from the issuer's chain account, then stores `txHash`, writes an audit event and a simulated email, and returns 201. When the registry is down it returns 503 `REGISTRY_UNAVAILABLE` and stores nothing. TC-01, TC-02, and TC-03 pass. `uv run pytest`: 55 passed. |
| A-07 | F-03 credential view and share links (API-03, API-04; API-05 optional) | Done | 2026-11-19. API-03 lets the holder or the original issuer read the `CredentialView`; share links are shown to the holder only. Anyone else gets 403 `NOT_CREDENTIAL_OWNER`, and an unknown ID gets 404 `CREDENTIAL_NOT_FOUND`. API-04 stores the scope and expiry on the server, returns an `sk_` token (128-bit) and the URL `WEB_BASE_URL/v/<token>`, and enforces OD-4 with 422 `INVALID_SCOPE`. The optional API-05 was also built: 204, idempotent, 403 and 404 `SHARE_LINK_NOT_FOUND`. Both write audit events. `uv run pytest`: 80 passed. Opening the URL in the verifier page is checked in A-12. |
| A-08 | F-04 verification (API-06) | Done | 2026-11-19. `POST /api/v1/verifications` (verifier only) resolves the token (404, or 410 when expired or revoked) and recomputes the commitment from the current rows. It reads `getRecord` and reports `integrity`, `issuerAuthorized` (`issuerActive` and the matching issuer), and `status` (from the chain, never the database column). The result follows the main cause in the order TAMPERED, REVOKED, ISSUER_UNAUTHORIZED, then VALID. Only the scoped fields and `chainRef` are returned, with no credential data for TAMPERED. The verification is stored with its verifier for API-07 and audited, and a registry outage returns 503 and stores nothing. TC-04, TC-05, TC-07, TC-11, TC-12 (10 runs: median 0.064 s, max 0.070 s), and TC-16 pass. `uv run pytest`: 101 passed. |
| A-09 | F-05 revocation (API-09) | Done | 2026-11-19. `POST /api/v1/credentials/{id}/revocations` lets only the original issuer revoke (403 `ISSUER_NOT_AUTHORIZED`, 404, 409 `ALREADY_REVOKED`). It sends `revokeCredential` from the issuer's chain account, then stores the reason, writes an audit event and a simulated email, and returns `{credentialId, status, reason, revokedAt, txHash}`. When the registry is down it returns 503 and the status does not change. If the row was set back to active, a second revoke still gets 409 from the chain. TC-06 and TC-14 pass at API level, and TC-14 also at contract level in Hardhat. `uv run pytest`: 115 passed. |
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
| OD-10 | How the portals list a holder's own credentials and an issuer's issued credentials, since the report has no list endpoint | Pending | A-12 |

## D3 report and presentation

| ID | Task | Status | Next step or verification |
| --- | --- | --- | --- |
| D-01 | Write the Deliverable 3 chapter covering the prototype, the role of blockchain and AI with the differentiator tests, TC-01 to TC-16 documentation, results against T-01 to T-05, limitations, and the next development plan | Pending | Needs A-13. Each test row needs scenario, steps or input, expected result, actual result, status, and evidence. |
| D-02 | Add a D3 task-assignment table at the start of the report, update Penutup, and add Lampiran (repository link, evidence) | Pending | The report's structure must still match the course template: cover through Lampiran. |
| D-03 | Record the R1–R4 interview findings in report Tabel 4.17–4.18 and fix the "no interviews yet" statements, or reword the deck slide | Pending | Needs OD-9. |
| D-04 | Restore the body of "Catatan Revisi" in the Google Doc | Pending | The Daftar Isi and the task table point to it. The content exists in the D1 revision docx and the deck appendix. |
| D-05 | Align the deck's verification slides with the report's four results | Pending | Needs OD-9. |
| D-06 | Build the D3 deck: main service flow demo, API interactions, technology contribution, plus a recorded demo video as a backup | Pending | Needs A-12 and A-13. |
| D-08 | Update the report for the OD-1 to OD-8 decisions of 2026-11-19 | Pending | Tabel 9.15 and 9.16 plus the 9.5 error codes (`platform_admin`, named codes, `ISSUER_ALREADY_REGISTERED`); Tabel 8.5 `RegistryRecord` (`issuerActive`) and the Bab X contract function list (`deactivateIssuer`, read-only `issuerAccountOf`); Tabel 10.4 (TC-16); Gambar 10.1 (AMS as its own process); the API-02, API-04, and API-07 notes in 9.3 (canonical payload, scope and expiry limits, position-text limit, matching rules); T06/T27 and the deck blueprint (simulated email); Tabel 9.15 API-01 field names and the codes A-04 applies beyond the listed endpoints (see ARCHITECTURE.md, API conventions); Tabel 9.6 note that an unknown `holderRef` returns 400 `MALFORMED_REQUEST` (A-06); Tabel 9.15 `CredentialView` fields for API-03 (A-07); the API-06 note in 9.3 on result precedence when several checks fail (A-08). |
| D-07 | Export the final single PDF (D1+D2+D3) and the final deck | Pending | Needs D-01 to D-06 and D-08. Submit by 2026-11-27, 23:59 WIB. |
