# ARCHITECTURE: ProofSkill Prototype

This plan turns [PRD.md](PRD.md) into implementation steps for Deliverable 3. Its content comes from the D1+D2 report: Bab VIII (SoaML), Bab IX (REST API), and Bab X (prototype plan). No code exists yet. Everything below is planned, and items still marked **Pending** need a team decision (see PRD [Open Decisions](PRD.md#open-decisions)).

## Technical Stack

The team locked the stack on 2026-11-19 (report Tabel 10.3). Library versions are pinned when each part is scaffolded (step A-01) and recorded in [CLAUDE.md](../CLAUDE.md).

| Area | Choice | Role |
| --- | --- | --- |
| Web interface | Next.js | One app with three portals (issuer admin, holder, verifier) that calls the REST API |
| API services | FastAPI (Python) | REST API under `/api/v1`; it shares the Python ecosystem with the AI module and generates OpenAPI from the contract |
| Off-chain database | PostgreSQL | Credential metadata, share links, skill catalog, verifications, matchings, and audit log |
| Registry | Hardhat local network with the Solidity contract `ProofSkillRegistry` | Registers issuers, records commitments, changes status, and reads records |
| AI | `paraphrase-multilingual-MiniLM-L12-v2` sentence embeddings, run locally | Semantic similarity between verified skills and position requirements in Indonesian and English, with no API cost |
| Authentication | Bearer JWT from API-00 | Roles `issuer_admin`, `holder`, and `verifier`, plus `platform_admin` for API-01 only (OD-1) |
| Hosting | Local machine for the demo | A public blockchain is out of scope. Whether the web app and API are also deployed is **Pending** |

## System Structure

### Components and data flow

This matches report Gambar 10.1 (Arsitektur prototipe).

1. **Web app (Next.js)** with three portals:
   - **Admin:** issue and revoke credentials, read the audit log.
   - **Holder:** view credentials, share them by link or QR code.
   - **Verifier:** verify a credential and run skill matching.

   It talks to the API over HTTPS/JSON with a Bearer token.
2. **REST API (FastAPI, `/api/v1`).** One module per SoaML service: IAS, CIS, CSS, AAS, VRS, AMS, and SCS. RGS is the adapter to the blockchain. The API enforces token auth and RBAC (NFR-01), keeps a consistent JSON contract and HTTP codes (NFR-08), and computes the nonce-salted SHA-256 hash of the canonical payload. It orchestrates validation, hashing, the registry call, and the audit record.
3. **Off-chain database (PostgreSQL).** Reached over SQL. It holds credential metadata, skills, share links, the audit log, and the skill catalog. All data is synthetic.
4. **Local blockchain (Hardhat).** Reached through web3/JSON-RPC. `ProofSkillRegistry` has the report's four functions, `registerIssuer`, `issueCredential`, `revokeCredential`, and `getRecord`, plus `deactivateIssuer` (OD-2). It stores only the hash commitment, issuer, issuer activity, status, and time.
5. **AI module.** AMS runs as its own process on port 8001, and the API calls it over HTTP (OD-8). It computes semantic similarity between skills and position requirements, groups requirements into matched and uncovered, and writes short reasons. Stopping that process is how TC-10 switches the AI off while verification keeps running (NFR-06).

### Services, operations, endpoints, and contract calls

Every endpoint maps to one SoaML operation and to BPMN To-Be activities (report Tabel 8.4, 9.2, and 9.17).

| Service (layer) | Operation | Endpoint | BPMN To-Be | Requirements |
| --- | --- | --- | --- | --- |
| IAS Issuer Authorization (utility) | `issueAccessToken` | API-00 `POST /auth/token` | Prerequisite | NFR-01 |
| | `registerIssuer` (also `ProofSkillRegistry.registerIssuer`) | API-01 `POST /issuers` | Prerequisite of T03 | FR-01 |
| | `checkAuthorization` | internal | T03, T25 | FR-01 |
| | `ProofSkillRegistry.deactivateIssuer` only (OD-2) | none: the platform admin account calls the contract directly (TC-16) | — | FR-01 |
| CIS Credential Issuance (task) | `issueCredential` | API-02 `POST /credentials` | T02–T06 | FR-02, 03, 04 |
| | `getCredential` | API-03 `GET /credentials/{id}` | T07, T28 | FR-05 |
| CSS Credential Status (task) | `revokeCredential` | API-09 `POST /credentials/{id}/revocations` | T24–T27 | FR-07 |
| | `createCorrectionVersion` | API-11 `POST /credentials/{id}/versions` (specification only) | Deferred | FR-11 |
| AAS Access & Audit (utility) | `createShareLink` | API-04 `POST /credentials/{id}/share-links` | T08, T09 | FR-05 |
| | `revokeShareLink` | API-05 `DELETE /share-links/{linkId}` (optional) | Optional | FR-05 |
| | `resolveShareLink` | internal | T12 | FR-05, 12 |
| | `recordAudit` | internal | T06, T16, T27 | FR-10 |
| | `queryAuditLog` | API-10 `GET /audit-logs` | Monitoring | FR-10 |
| VRS Verification (task) | `verifyCredential` | API-06 `POST /verifications` | T11–T17 | FR-06, 12 |
| | `getVerification` | internal | T19 | FR-08 |
| RGS Registry (utility, blockchain adapter) | `anchorCommitment` → `ProofSkillRegistry.issueCredential` | internal | T05 | FR-04 |
| | `setStatus` → `ProofSkillRegistry.revokeCredential` | internal | T26 | FR-07 |
| | `getRecord` → `ProofSkillRegistry.getRecord` | internal | T14 | FR-06 |
| SCS Skill Catalog (entity) | `listSkills` | API-08 `GET /skills` | T01, T20 | FR-03, 08 |
| AMS AI Matching (microservice) | `matchSkills` | API-07 `POST /matchings` | T18–T22 | FR-08, 09 |

CIS, CSS, VRS, and AMS call `AAS.recordAudit`. AMS always reads skills through `VRS.getVerification` (SC-9), never from data the verifier sends. This is what keeps the AI from being used as a candidate search.

### Data placement (report Tabel 8.6)

| Location | Data or function | Reason |
| --- | --- | --- |
| On-chain (smart contract) | Nonce-salted hash commitment, issuer identity, active or revoked status, time | A record that can be checked without relying on one operator. No personal data (UU PDP, NFR-02) |
| Off-chain (database) | Credential metadata, holder reference, skills, share links, audit log, skill catalog | Can be corrected and deleted as needed; size and privacy stay under control |
| AI | Input: verified skills and position text. Output: similarity, grouping, reasons | The AI never sees identity, never stores data, and never changes credential status |
| Human | Graduation validation (T01), hiring decision (T23), revocation decision (T24) | Accountability is not handed to the system |

**Hash commitment.**
- The canonical payload is hashed with SHA-256 together with a random nonce, so participant details cannot be guessed from the hash.
- `holderDisplayName` is stored off-chain only and is excluded from the hashed payload.
- NIK is never part of the payload.
- Canonical form (OD-6): JSON with sorted keys and no whitespace, encoded in UTF-8, over `credentialId`, `issuerId`, `holderRef`, `program.title`, `program.completedAt`, `program.criteria`, and `skills` (skill IDs sorted). `commitment = SHA-256(canonical JSON bytes ‖ 32-byte random nonce)`, and the nonce is stored off-chain.

### Request flows

- **Issuance (T01–T06).**
  1. The admin maps skills to the catalog (API-08) and submits API-02.
  2. CIS checks role and permission (403 `ISSUER_NOT_AUTHORIZED`) and validates the payload and skills (422 `SKILL_NOT_IN_CATALOG`).
  3. CIS stores metadata off-chain and computes the commitment.
  4. RGS calls `issueCredential`. If the registry cannot be reached, the API returns 503 `REGISTRY_UNAVAILABLE` and nothing is issued.
  5. CIS stores `txHash`, records an audit event, notifies the holder with a simulated email in the `notifications` table (OD-3), and returns 201.
- **Sharing (T07–T10).**
  1. The holder views the credential (API-03) and chooses the scope and expiry (API-04).
  2. AAS creates a random, time-limited `shareToken`. The scope is stored on the server, so a verifier cannot widen it. A non-owner gets 403 `NOT_CREDENTIAL_OWNER`, and an invalid scope gets 422 `INVALID_SCOPE`. Allowed scope fields are `holderDisplayName`, `program.title`, `completedAt`, `program.criteria`, and `skills`, and `expiresInHours` must be 1 to 720 (OD-4).
  3. The link format is `https://proofskill.example/v/sk_…`, and it works as a LinkedIn Credential URL.
- **Verification (T11–T17).**
  1. A verifier posts the `shareToken` to API-06.
  2. VRS resolves the token: 404 `SHARE_LINK_NOT_FOUND` if unknown, 410 `SHARE_LINK_EXPIRED` if expired or revoked.
  3. VRS loads the metadata, recomputes the hash, reads the record through RGS `getRecord`, and compares integrity, issuer authorization, and status as three separate checks.
  4. It returns 200 with `VALID`, `REVOKED` (with the issuer's reason), `TAMPERED` (integrity `FAIL`, no credential data), or `ISSUER_UNAUTHORIZED` (`issuerAuthorized` `FAIL` because `getRecord` reports the issuer as deactivated, OD-2). It returns only the fields in the scope, plus `chainRef`.
  5. It records an audit event. If the registry cannot be read, it returns 503 `REGISTRY_UNAVAILABLE`.
- **Skill matching (T18–T23).**
  1. The verifier posts a `verificationId` and a position (title and description) to API-07.
  2. AMS checks that the verification is `VALID` (409 `VERIFICATION_NOT_VALID`) and that this verifier owns it (403 `VERIFICATION_NOT_OWNED`).
  3. AMS reads the verified skills and the catalog, then computes per-pair similarity.
  4. It returns matched skills (skill, requirement, similarity, reason), missing requirements, limitations, label `REKOMENDASI`, and `modelVersion`. It never returns a total candidate score.
  5. When the AI is down, it returns 503 `AI_UNAVAILABLE`, and API-06 keeps working.
  6. Matching rules (OD-7): the description (1 to 2,000 characters, OD-4) is split into requirements at sentence ends, commas, semicolons, and "dan" or "and". Each requirement is compared with the label and aliases of every verified skill, and a cosine similarity of 0.60 or more is a match. The threshold is tuned on synthetic data.
- **Revocation (T24–T28).**
  1. The original issuer's admin posts a reason to API-09.
  2. CSS checks that the caller is the original issuer (403 `ISSUER_NOT_AUTHORIZED`) and that the credential is not already revoked (409 `ALREADY_REVOKED`).
  3. RGS calls `revokeCredential`. The contract itself rejects any other issuer's address. The new status is a new transaction, so history is not overwritten.
  4. CSS stores the reason, records an audit event, notifies the holder, and returns 200. The next verification reads `REVOKED`.

### API conventions (report Tabel 9.1 and 9.16)

- **Base URL and format:** `/api/v1`, JSON in UTF-8, times in ISO 8601 UTC.
- **ID prefixes:** `CRD-`, `ISS-`, `SHL-`, `VER-`, and `MAT-`, plus holder references `HLD-` and skills `SK-`.
- **Auth:** `Authorization: Bearer <accessToken>`. The token carries the role. Verifier accounts are free. In the prototype, accounts come from seed data, and one person may hold several accounts to play different roles.
- **HTTP methods:** POST creates a resource or runs an action, GET reads, and DELETE removes a share link.
- **Verification results:** a credential that fails verification still returns 200 with a `result` field, because the verification itself ran. HTTP error codes are reserved for request or access problems.
- **Error body:** `{"error": {"code": "...", "message": "...", "requestId": "..."}}`.
- **Enums:**
  - Credential status: `active` or `revoked`. `superseded` exists only if FR-11 is built.
  - Verification result: `VALID`, `REVOKED`, `TAMPERED`, or `ISSUER_UNAUTHORIZED`.
  - Checks: `integrity` PASS/FAIL, `issuerAuthorized` PASS/FAIL, `status` ACTIVE/REVOKED.
  - Roles: `issuer_admin`, `holder`, and `verifier`, plus `platform_admin` (OD-1).
  - AI label: `REKOMENDASI`.
- **Product boundary:** no search, browse, or candidate-list endpoint. Credential data leaves the system only through a share token its owner created.

| Code | HTTP status | Endpoints |
| --- | --- | --- |
| `INVALID_CREDENTIALS` | 401 | API-00 |
| `MALFORMED_REQUEST` | 400 | API-02 |
| `UNAUTHENTICATED` | 401 | API-02, API-06, API-07 |
| `ISSUER_NOT_AUTHORIZED` | 403 | API-02, API-09 |
| `FORBIDDEN_ROLE` | 403 | API-01 (OD-1), API-06, API-07 |
| `NOT_CREDENTIAL_OWNER` | 403 | API-03 (OD-1), API-04, API-05 (OD-1) |
| `VERIFICATION_NOT_OWNED` | 403 | API-07 |
| `CREDENTIAL_NOT_FOUND` | 404 | API-03 (OD-1), API-04, API-09 |
| `SHARE_LINK_NOT_FOUND` | 404 | API-05 (OD-1), API-06 |
| `VERIFICATION_NOT_FOUND` | 404 | API-07 |
| `ISSUER_ALREADY_REGISTERED` | 409 | API-01 (OD-1) |
| `VERIFICATION_NOT_VALID` | 409 | API-07 |
| `ALREADY_REVOKED` | 409 | API-09 |
| `SHARE_LINK_EXPIRED` | 410 | API-06 |
| `SKILL_NOT_IN_CATALOG` | 422 | API-02 |
| `INVALID_SCOPE` | 422 | API-04 |
| `INVALID_POSITION_TEXT` | 422 | API-07 |
| `REGISTRY_UNAVAILABLE` | 503 | API-02, API-06, API-09 |
| `AI_UNAVAILABLE` | 503 | API-07 |

The report gives some error responses without naming their codes: API-01's 403 and 409, API-03's 403 and 404, and API-05's 403 and 404. OD-1 named them on 2026-11-19, as marked in the table. Only `ISSUER_ALREADY_REGISTERED` is new. Do not invent any other code.

### Repository layout (proposed, created in A-01)

```text
proofskill/
  contracts/        # Hardhat project: ProofSkillRegistry.sol, contract tests, local deploy script
  api/              # FastAPI app: one module per SoaML service (ias, cis, css, aas, vrs, rgs, scs, ams)
    tests/          # automated tests named after TC IDs where a scenario is automatable
  web/              # Next.js app: issuer, holder, and verifier portals; verifier route /v/[shareToken]
  docs/             # project docs: PRD, ARCHITECTURE, TODO, WORKFLOW, DESIGN, PRODUCT
    evidence/       # TC-01..TC-16 evidence records for the D3 report
  skill/            # project skills (project-setup, run-test-scenario)
  .impeccable/      # impeccable design context: surface briefs and decision sketches
```

## Implementation Plan

The steps are in dependency order. The schedule starts on 2026-11-19 and replaces the dates in report Tabel 10.5, which must be updated to match:

- 19–20 Nov: A-01 to A-05
- 21–22 Nov: A-06 and A-08
- 23–24 Nov: A-07 and A-09 to A-11
- 25–26 Nov: A-12 and A-13
- 27 Nov: submission

As of 2026-11-19, no step has started. Following the report's risk mitigation, P0 features (F-02, F-04, F-05, F-06) come first, and F-03 and F-07 are simplified if time runs short.

| ID | Step | Depends on | Completion criteria |
| --- | --- | --- | --- |
| A-01 | Scaffold `contracts/` (Hardhat), `api/` (FastAPI), `web/` (Next.js), local PostgreSQL, and `.env.example` | — | Each part starts locally with one documented command. Versions are recorded in CLAUDE.md. No secrets are committed. |
| A-02 | `ProofSkillRegistry` contract: `registerIssuer`, `issueCredential`, `revokeCredential`, `getRecord`, plus `deactivateIssuer` (OD-2), storing only commitment, issuer, issuer activity, status, and time | A-01 | Contract tests pass for issue, revoke, and read. A revoke from a different issuer reverts and leaves the status unchanged (TC-14). An unregistered issuer cannot issue. A deactivated issuer's record reads `issuerActive` false (TC-16). |
| A-03 | Off-chain schema and synthetic seed: issuers ISS-001 and ISS-002 (also registered on-chain), one account per role, skill catalog, holder references, position descriptions | A-01, A-02 | Migrations apply to an empty database. The seed loads. All data is synthetic. Database issuers match registry issuers. |
| A-04 | F-01 authentication and RBAC: API-00 (JWT with role), API-01 (registers the issuer in the database and on-chain), role guards | A-03 | The three roles are separated. Cross-role calls return 403. A wrong password returns 401 `INVALID_CREDENTIALS`. API-01 accepts only `platform_admin`, returns 403 `FORBIDDEN_ROLE` for other roles, and 409 `ISSUER_ALREADY_REGISTERED` for a duplicate (OD-1). |
| A-05 | SCS skill catalog: API-08 `GET /skills?query=&limit=&offset=` | A-03 | Returns `{items: [{skillId, label, aliases}], total}`. |
| A-06 | F-02 issuance: API-02 with authorization, validation, off-chain storage, nonce-salted SHA-256 commitment, `issueCredential`, `txHash`, audit, notification | A-02, A-04, A-05 | TC-01, TC-02, and TC-03 pass. A registry outage returns 503 `REGISTRY_UNAVAILABLE` and issues nothing. |
| A-07 | F-03 credential view and share links: API-03 and API-04, with API-05 optional | A-06 | The owner or original issuer can read the credential, and anyone else gets 403 or 404. Scope and expiry are stored on the server. `INVALID_SCOPE` returns 422. The link URL opens the verifier route. |
| A-08 | F-04 verification: API-06 with token resolution, hash recomputation, `getRecord`, three checks, results with reasons, scoped data, `verificationId` ownership, audit | A-07 | TC-04, TC-05, TC-07, TC-11, TC-12, and TC-16 pass. A registry outage returns 503 `REGISTRY_UNAVAILABLE`. |
| A-09 | F-05 revocation: API-09 with the original-issuer check, `revokeCredential` on-chain, reason, audit, notification | A-08 | TC-06 and TC-14 pass. A second revoke returns 409 `ALREADY_REVOKED`. |
| A-10 | F-06 skill matching: API-07 with a VALID and owned verification, catalog terms, embeddings, matched and missing groups with reasons, limitations, `REKOMENDASI`, `modelVersion` | A-05, A-08 | TC-08, TC-09, TC-10, and TC-15 pass. The response has no total score. |
| A-11 | F-07 audit trail: `recordAudit` in CIS, CSS, VRS, and AMS, plus API-10 with filters by operation and time | A-06, A-08, A-09, A-10 | TC-13 passes: every operation is logged with time, actor role, operation, object ID, and outcome, and no sensitive payload. |
| A-12 | F-08 web interface: issuer, holder, and verifier portals following DESIGN.md and the surface brief in `.impeccable/surfaces/` | A-06 to A-11 | The three main flows run end to end in a browser. The impeccable detector and finish review have run on the verifier result page. |
| A-13 | Run TC-01 to TC-16 and measure T-01 to T-05 | A-12 | Every TC has a record with steps or input, expected result, actual result, status, and evidence in `docs/evidence/`. T-01 to T-05 have measured values for the D3 report. |
