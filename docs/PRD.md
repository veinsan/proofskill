# PRD: ProofSkill

> **Status** Approved scope for the Deliverable 3 prototype (from the D1+D2 report, Bab X), built and tested locally. Re-planned on 2026-11-19 as a deployed product; see [Deployment decisions](#deployment-decisions).
> **Author** Kelompok 02, II3120 Layanan Sistem dan Teknologi Informasi
> **Last updated** 2026-11-19
> **Sources of truth** Report "Laporan_Kelompok 02_Deliverable 1 II3120" (Google Doc, D1+D2) and deck "PPT_Kelompok 02_Deliverable 2 II3120" (Google Slides). When the two disagree, this PRD follows the report and lists the difference under [Open Decisions](#open-decisions).

## 1. Problem Statement

A training certificate is only useful as proof of competence if others can confirm who issued it, what it states, and whether it is still valid. Certificates from nonformal training run by campus units, student associations, laboratories, career centers, and communities have no shared verification channel. The formal channels cover other documents:

- PISN and digital diplomas cover diplomas and professional certificates.
- LSP/BNSP covers competency certification.
- SiKompeten covers course institutions.

The team concluded from these documents, without confirmation from the agencies, that nonformal certificates fall outside these channels.

Employers do run into credential problems. The HireRight Global Benchmark Report 2025 found that more than three quarters of employers saw candidate data discrepancies in the last 12 months. That survey is global, so it is used only as an indication of risk, not as a measure for Indonesia.

The As-Is case is a representative campus training organizer described by open assumptions A1–A6:

- Graduation is recorded first.
- Certificates are PDFs made from a template.
- PDFs are shared by email, messaging, or file storage.
- A verifier contacts the admin when in doubt.
- There is no ready skill catalog.
- Synthetic or approved data may be used for the prototype.

The resulting gaps (report Tabel 2.4) are hypotheses about the service problem:

| Code | As-Is condition | Potential consequence |
| --- | --- | --- |
| G-01 | Certificates are PDF files with no shared verification channel. | Verifiers need extra steps to confirm origin and status. |
| G-02 | Issuance information is scattered across admin archives. | Clarification depends on admin working hours and archive order. |
| G-03 | Competency metadata is poorly structured. | Skills are hard to compare across certificates. |
| G-04 | Qualification matching is manual. | Verifiers read and judge a lot of information. |
| G-05 | Corrections and revocations are communicated informally. | Old versions may circulate without their current status. |
| G-06 | Use and requests are poorly documented. | Hard to audit; personal data spreads when files are forwarded. |

**Validation status.** The interviews with R1 (issuer), R2 (HR), and R3–R4 (job seekers) appear in the deck's "Dokumentasi wawancara" slide. Their detailed findings are not yet recorded in report Tabel 4.17–4.18. Until they are, the needs above stay hypotheses.

## 2. Goals

ProofSkill is a credential issuance and verification service for nonformal training organizers. A credential issued through ProofSkill can be checked for authenticity, issuer, and status without contacting an admin, then read as a skill-fit summary for the position the verifier is filling.

The targets below are design targets: acceptance criteria tested on the Deliverable 3 prototype, not performance claims. Measured values are reported only after D3.

| Code | For | Goal | Indicator | Design target | Basis |
| --- | --- | --- | --- | --- | --- |
| T-01 | Verifier | Confirm authenticity, issuer, and status without contacting an admin | Verification time per credential | Less than 5 seconds on test data | O-03, O-04, NFR-05 |
| T-02 | Issuer admin | Remove manual confirmation for active credentials | Number of admin steps on the verification path | Zero | G-02, O-03 |
| T-03 | Holder | Share proof without exposing unnecessary data | Attributes visible to the verifier | Only permitted attributes, no personal data on-chain | O-06, NFR-02 |
| T-04 | Verifier | Read skill relevance to a position | Summary of matched skills, uncovered requirements, and reasons | Available for every valid credential and labeled as a recommendation | O-05, FR-08, FR-09 |
| T-05 | Governance | Revocation takes effect immediately and cannot be changed unilaterally | Status on the next verification | 100% shown as revoked, other issuers rejected | O-07, FR-07, NFR-01 |

## 3. Target Users

- **Issuer admin (admin penerbit).** The admin of a nonformal training organizer, which is the paying primary customer. They validate graduation, issue credentials, revoke them with a reason, and read the audit log.
- **Holder (peserta).** A training participant. Free. They view their credentials and share them with a scope and expiry through a link or QR code, including as a LinkedIn Credential URL.
- **Verifier (pemeriksa).** A recruiter, selection committee member, or lecturer with a free verifier account. They verify integrity, issuer, and status, then request a skill-fit summary for a position.
- **Platform admin.** Registers issuers (API-01).
- **IT administrator (pengelola TI).** Keeps integrity, access, performance, and audit in order. There is no portal for this role in the prototype.
- **Stakeholders.** Kelompok 02 owns the project, and the II3120 teaching team evaluates the deliverables.
- **Builders.** The team, with Claude Code as the coding agent. This PRD, CLAUDE.md, ARCHITECTURE.md, and WORKFLOW.md guide both.

Design rules that keep ProofSkill a verification service and not a talent-search tool (report 1.3):

1. No candidate search, browsing, or candidate lists.
2. An AI summary can be requested only for a credential that just passed verification, by the verifier who verified it.
3. The AI receives only verified skills and the position text, without the holder's identity.
4. The hiring decision stays with a human.

## 4. User Stories

- **US-01:** As an issuer admin, I want to issue a credential to a participant who passed so that the achievement is recorded correctly.
  - **Acceptance criteria:**
    - A registered issuer's valid request returns 201 with `credentialId`, `commitment`, and `txHash`, and the commitment is recorded on the registry (TC-01).
    - An account that is not a registered issuer gets 403 `ISSUER_NOT_AUTHORIZED` (TC-02).
    - A skill outside the catalog gets 422 `SKILL_NOT_IN_CATALOG` (TC-03).
- **US-02:** As a holder, I want to share a credential link so that the verifier sees the legitimate status.
  - **Acceptance criteria:**
    - A share link stores its scope and expiry on the server, and the response includes the URL.
    - A non-owner gets 403 `NOT_CREDENTIAL_OWNER`.
    - An unknown scope field or an out-of-range expiry gets 422 `INVALID_SCOPE`.
    - An expired link gets 410 `SHARE_LINK_EXPIRED` at verification (TC-07).
- **US-03:** As a verifier, I want to check issuance and revocation status so that I do not depend on an uploaded PDF.
  - **Acceptance criteria:**
    - An intact credential returns 200 with `VALID` and no admin involvement (TC-04).
    - Content changed directly in the database returns 200 with `TAMPERED` and no credential data (TC-05).
    - Verification on test data takes less than 5 seconds (TC-12).
    - A credential whose issuer was deactivated on the registry returns 200 with `ISSUER_UNAUTHORIZED` (TC-16, OD-2).
- **US-04:** As a verifier, I want to compare verified skills with a position's needs so that my initial review is supported.
  - **Acceptance criteria:**
    - After a `VALID` verification, the result shows matched skills, uncovered requirements, limitations, and the label `REKOMENDASI`, with no total score (TC-08).
    - A verification that is not `VALID` gets 409 `VERIFICATION_NOT_VALID` (TC-09).
    - With the AI service off, matching returns 503 `AI_UNAVAILABLE` while verification keeps working (TC-10).
    - Another verifier's `verificationId` gets 403 `VERIFICATION_NOT_OWNED` (TC-15).
- **US-05:** As an issuer admin, I want to revoke a wrong credential so that the new status applies to the next verification.
  - **Acceptance criteria:**
    - After revocation, verification returns `REVOKED` with the reason, even if the database status is set back to active (TC-06).
    - A different issuer calling `revokeCredential` directly on the contract is rejected with a revert, and the status does not change (TC-14).
    - Revoking twice gets 409 `ALREADY_REVOKED`.
- **US-06:** As a holder, I want to know what data is shared and control access so that my privacy is protected.
  - **Acceptance criteria:**
    - A verifier sees only the fields in the link's scope.
    - On-chain data holds only the commitment, issuer, and status, with no personal data (TC-11).

## 5. Functional Requirements

Report Tabel 4.11. Priorities: P0 decides whether issuance and verification can run at all, P1 clarifies the experience, and P2 is an advanced capability.

| ID | Requirement | Actor | Priority |
| --- | --- | --- | --- |
| FR-01 | The admin manages authorized issuer identities. | Admin | P0 |
| FR-02 | The admin issues a credential after graduation is validated. | Admin | P0 |
| FR-03 | The system stores credential metadata and document references off-chain. | System | P0 |
| FR-04 | The system records a nonce-salted hash commitment and status on the local blockchain. | System | P0 |
| FR-05 | The holder can view and share a credential with access limits. | Holder | P1 |
| FR-06 | The verifier can check integrity, issuer identity, and status. | Verifier | P0 |
| FR-07 | An authorized admin can revoke a credential with a short reason. | Admin | P0 |
| FR-08 | The AI computes similarity and groups skills into matched and insufficiently covered. | Verifier | P0 |
| FR-09 | The system shows that the AI result is a recommendation, with short reasons. | Verifier | P0 |
| FR-10 | The system logs issuance, verification, revocation, and matching. | System | P1 |
| FR-11 | The admin can correct non-sensitive data through a new version instead of overwriting history. | Admin | P1 |
| FR-12 | The verifier sees an informative failure message for a changed document or denied permission. | Verifier | P1 |

D2 adjustments: FR-05 is in prototype scope because the issue-to-verify flow needs share links. FR-11 is specified only (API-11) and is not built.

## 6. Non-Functional Requirements

Report Tabel 4.12. The targets are acceptance criteria for the design, not measured performance.

| ID | Requirement | Target or test |
| --- | --- | --- |
| NFR-01 | Access control and role restriction. | Issuance and revocation are rejected for accounts without permission (negative test). |
| NFR-02 | Participant privacy. | Identity, GPA, and full documents are not stored on-chain. Demo data is synthetic (UU PDP). |
| NFR-03 | Explainable AI output. | The result shows matched skills, uncovered requirements, and a note that the decision stays human. |
| NFR-04 | Status integrity. | A changed document fails the hash commitment check, and a revoked credential never appears active. |
| NFR-05 | Performance on the local prototype. | Verification on test data takes less than 5 seconds (initial target, to be tested and revisable). |
| NFR-06 | Reliability when AI fails. | Verification keeps working when the AI service is unavailable. |
| NFR-07 | Auditability. | The log records time, actor, operation, and status without exposing sensitive data. |
| NFR-08 | API testability. | Responses are consistent, and errors use the correct HTTP codes with a JSON payload. |

## 7. Scope

- **In scope (build):**
  - Endpoints API-00, 01, 02, 03, 04, 06, 07, 08, 09, and 10, plus API-12 and API-13 (OD-10), and the web portal for three roles.
  - Features F-01 to F-08.
  - Test scenarios TC-01 to TC-15, plus TC-16 (added by OD-2).
  - Data that is entirely synthetic (assumption A6): at least two test issuers (ISS-001 and ISS-002) to test the original-issuer rule, one small skill catalog, and several position descriptions.
- **Optional:** API-05 (revoke a share link), built if time remains.
- **Specification only:** API-11 (correction version, FR-11 deferred).
- **Out of scope:**
  - Candidate search (deliberately not built).
  - PDDikti or PISN integration.
  - ATS integration.
  - Payment.
  - A public blockchain mainnet. The deployment uses a public testnet (Base Sepolia); see [Deployment decisions](#deployment-decisions).
  - Storing original documents.
  - Production-scale identity management.
  - From the D1 MVP boundary: full profiles, a job marketplace, HRIS or government integration, and a national consortium network.
  - Deferred features P-06 (follow-up training recommendations) and P-07 (ATS/HRIS integration).
- **Changes:**
  - D2 broke the candidate services from D1 Tabel 6.3 into eight SoaML services. It moved FR-05 into the prototype and limited FR-11 to a specification.
  - On 2026-11-19, the team locked the stack from Tabel 10.3, set the interface language to English, and adopted a new visual identity defined in DESIGN.md.
  - Also on 2026-11-19, after the prototype passed TC-01 to TC-16 locally, the project was re-planned as a deployed product. See below.

## Deployment decisions

Decided 2026-11-19. They change the infrastructure only. Users, user stories, FR and NFR, endpoints, payloads, codes, enums, and the design rules of section 3 stay as they are.

| Area | Prototype | Deployment | Why |
| --- | --- | --- | --- |
| Web | Next.js, local | Next.js on Vercel | Same app; free hosting for Next.js |
| API | FastAPI, local | FastAPI on Render (free tier; it sleeps when idle and wakes in about 30 seconds) | Same app; no extra cost |
| Database | PostgreSQL 17, local cluster | Supabase Postgres, with Row Level Security on and no policies so only the API's connection can read or write | Managed Postgres that the same SQL migrations apply to |
| Authentication | API-signed JWT, seeded passwords | Supabase Auth. API-00 stays as a proxy so the contract and tests do not change | Managed accounts, password reset, and future self sign-up (OD-11) |
| Blockchain | Hardhat local node | `ProofSkillRegistry` on the Base Sepolia public testnet. Issuer keys are kept as secrets on the API (OD-12). Hardhat stays for contract tests and local development | A registry anyone can check on a block explorer, at no cost. Only commitments, issuer, status, and time go on-chain, as before (NFR-02) |
| AI | MiniLM through ONNX Runtime in its own process | Gemini embeddings (free tier) from the AMS module | No 470 MB model in the deployment, so free hosting is enough. Only skill and requirement text is sent to Gemini, never holder identity (design rule 3) |
| Reserved stack | — | OpenCV, YOLO, or MediaPipe (computer vision), RunPod (training compute), LangChain (multi-agent) | Not used by any current feature. A future feature that needs them, such as importing scanned legacy certificates, enters this PRD first |

Consequences:
- On a public testnet the registry is no longer a permissioned network. It is a permissioned contract: only issuers the platform admin registered can write, and only the original issuer can revoke. Positioning text that says "permissioned blockchain" needs this nuance (report Tabel 1.5).
- Demo data stays synthetic (assumption A6). Real participant data needs a privacy review under UU PDP before it is allowed.
- Gemini's free tier may use submitted text to improve Google's products, which is acceptable only because the text carries no personal data.
- The report sections these decisions affect are tracked as D-08 in TODO.md.

## Open Decisions

These gaps or conflicts in the source documents need a team decision. Until each is decided, no document or code treats it as settled. OD-1 to OD-8 were decided on 2026-11-19. The report sections each decision changes are tracked as D-08 in TODO.md. OD-10 was decided the same day. OD-9, OD-11, and OD-12 are still open.

1. **Platform admin role and unnamed error codes.** API-01 requires a "platform admin", but the role enum in Tabel 9.16 lists only `issuer_admin`, `holder`, and `verifier`. Some error responses also have no code names: API-01 (403, 409), API-03 (403, 404), and API-05 (403, 404).
   - **Decided 2026-11-19:** add the role `platform_admin`, used only by API-01. API-01 403 is `FORBIDDEN_ROLE` and 409 is the one new code, `ISSUER_ALREADY_REGISTERED`. API-03 403 is `NOT_CREDENTIAL_OWNER` and 404 is `CREDENTIAL_NOT_FOUND`. API-05 403 is `NOT_CREDENTIAL_OWNER` and 404 is `SHARE_LINK_NOT_FOUND`.
2. **How ISSUER_UNAUTHORIZED can happen.** F-04 requires four verification results, but the four-function contract cannot deactivate an issuer, and no TC covers this result.
   - **Decided 2026-11-19:** the contract gets a fifth function, `deactivateIssuer(issuerId)`, callable only by the platform admin account, with no endpoint. `getRecord` also returns `issuerActive`. A credential whose issuer is deactivated verifies as `ISSUER_UNAUTHORIZED`, covered by the new scenario TC-16.
3. **Notification channel** for T06 and T27. The deck's To-Be blueprint says "notifikasi surel" (email notification), and the report does not specify a channel.
   - **Decided 2026-11-19:** a simulated email recorded in a `notifications` table. Nothing is sent over SMTP, because all data is synthetic (A6).
4. **Share and matching limits.** The allowed share-scope fields and maximum link lifetime behind `INVALID_SCOPE`, and the maximum position-text length behind `INVALID_POSITION_TEXT`.
   - **Decided 2026-11-19:** scope fields are `holderDisplayName`, `program.title`, `completedAt`, `program.criteria`, and `skills`. `expiresInHours` must be 1 to 720. A position description must be 1 to 2,000 characters.
5. **Holder accounts.** How a holder account maps to `holderRef` (for example HLD-2026-0007).
   - **Decided 2026-11-19:** each holder account has one fixed `holderRef`, created in the seed. A holder sees only the credentials issued to that `holderRef`.
6. **Canonical payload.** The exact canonical form and field list hashed with the nonce. `holderDisplayName` is excluded, and NIK is never included.
   - **Decided 2026-11-19:** JSON with sorted keys and no whitespace, encoded in UTF-8, over `credentialId`, `issuerId`, `holderRef`, `program.title`, `program.completedAt`, `program.criteria`, and `skills` (skill IDs sorted). `commitment = SHA-256(canonical JSON bytes ‖ 32-byte random nonce)`.
7. **Matching mechanics.** The similarity threshold separating matched from uncovered requirements, and how a position description is split into requirements.
   - **Decided 2026-11-19:** split the description into requirements at sentence ends, commas, semicolons, and the word "dan" or "and". Compare each requirement with the label and aliases of every verified skill. A cosine similarity of 0.60 or more is a match, and the rest go to `missingRequirements`. Tune the threshold on synthetic data and record the result. A-10 tuned it to 0.55 for MiniLM, and B-04 re-tuned it to 0.72 for Gemini embeddings (see TODO.md A-10 and B-04).
8. **TC-10 setup.** How the AI service is switched off for TC-10.
   - **Decided 2026-11-19:** AMS runs as its own process on port 8001, and the API calls it over HTTP. TC-10 stops that process.
   - **Revised in B-04 (2026-11-19):** AMS is a module inside the API that calls Gemini. TC-10 leaves `GEMINI_API_KEY` unset, so API-07 returns 503 `AI_UNAVAILABLE` while API-06 keeps working.
9. **Report versus deck.**
   - The deck's verification slides (BPMN To-Be 3, To-Be blueprint) list three results (VALID, REVOKED, TAMPERED). The report lists four (adding ISSUER_UNAUTHORIZED), and this PRD follows the report.
   - The deck shows interviews as done, while the report's Executive Summary, Tabel 4.1, and Tabel 4.17–4.18 still mark them as not done or empty.
10. **Portal lists (found in A-07).** The report has no endpoint that lists credentials. API-03 reads one credential by ID, so the holder portal cannot show "my credentials" and the issuer portal cannot show the credential table DESIGN.md describes. The design rule against candidate search (report 1.3) rules out any cross-holder listing. Options:
    - Add two owner-scoped list endpoints: the holder's own credentials, and the credentials the caller's issuer issued. Neither can search across holders.
    - Add no endpoint. The holder opens a credential from the ID in the simulated email, and the issuer portal lists the IDs it can see in its own audit log (API-10).
    - **Decided 2026-11-19:** add the two owner-scoped endpoints. API-12 `GET /holders/me/credentials` lists the signed-in holder's credentials. API-13 `GET /issuers/me/credentials` lists the credentials the caller's issuer issued. Both take only `limit` and `offset`, with no query or filter, so neither can search across holders.
11. **Self sign-up for holders and verifiers (from the deployment re-plan).** The prototype seeds every account. A deployed service needs verifiers to sign up for their free account, and holders to claim the `holderRef` an issuer used (OD-5) without anyone being able to claim someone else's. The options include an issuer-sent invitation link, or an email match recorded at issuance. Until decided, accounts are created by the seed and by Supabase's admin API.
12. **Issuer key custody on the testnet (from the deployment re-plan).** The contract checks the sender's address, so each issuer needs its own key. The default for B-03 is custodial: the API holds one key per issuer as a Render secret and signs for it. The alternative is that issuers sign in their own wallet, which changes the issuance flow. Until decided, B-03 uses the custodial default.
