# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Stack

Locked by the team on 2026-11-19 (D2 report, Tabel 10.3): Next.js for the web app with three portals, FastAPI for the REST API under `/api/v1`, PostgreSQL for off-chain data, Hardhat with the Solidity contract `ProofSkillRegistry` as the local chain, and the multilingual sentence-embedding model `paraphrase-multilingual-MiniLM-L12-v2` running locally for skill matching.

Re-planned on 2026-11-19 for a public deployment, with the same API contract: Next.js and FastAPI on Vercel, Supabase for Postgres and Auth, the registry on the Base Sepolia testnet, and Gemini embeddings plus a Gemini language-model judge (B-08) in place of the local model. OpenCV, YOLO, MediaPipe, RunPod, and LangChain are reserved for future features; none is used today.

## Users

- **Issuer admin (admin penerbit).** Works at a nonformal training organizer such as a campus unit, student association, laboratory, career center, or community. After a participant passes, they issue a credential and revoke it if it is wrong. The organizer is the paying customer.
- **Holder (peserta).** A training participant. They view their credentials and share a scoped link or QR code when they apply for an internship or job, or paste it into LinkedIn's Credential URL field. Free.
- **Verifier (pemeriksa).** A recruiter, selection committee member, or lecturer with a free verifier account. They check integrity, issuer, and status without contacting an admin, then ask for a skill-fit summary against the position they are filling.
- **Platform admin.** Registers issuers (API-01). It is not one of the three portals.
- **IT administrator (pengelola TI).** Keeps integrity, access, performance, and audit in order. The prototype has no portal for this role.

## Product Purpose

ProofSkill is a credential issuance and verification service for nonformal training organizers. A credential issued through ProofSkill can be checked for authenticity, issuer, and status without contacting an admin. It can then be read as a skill-fit summary for the position the verifier is filling.

For the D3 prototype, success means meeting the design targets in report Tabel 1.6, measured on test data:

- **T-01:** verification takes less than 5 seconds.
- **T-02:** zero admin steps on the verification path.
- **T-03:** verifiers see only the attributes the holder allowed, and no personal data goes on-chain.
- **T-04:** every valid credential gets a skill summary labeled as a recommendation.
- **T-05:** a revocation shows on 100% of later verifications, and other issuers are rejected.

These are design targets until D3 measures them.

## Positioning

ProofSkill has three differentiators (report Tabel 1.5):

1. **A shared registry across many small issuers with no single operator.** The registry contract is permissioned: only registered issuers write, and only the original issuer can change a credential's status. Status history is never overwritten. When deployed, the contract lives on a public testnet, so anyone can check it on a block explorer.
2. **A per-position skill-fit summary at verification time.** It is available only for credentials that just verified as VALID.
3. **A segment the formal channels leave out.** PISN, LSP/BNSP, and SiKompeten do not cover campus and community training.

ProofSkill is not a talent-search tool and not just certificate storage. It complements LinkedIn: a ProofSkill verification link fits LinkedIn's Credential URL field.

## Operating Context

- The core flow is issue, share, verify with a skill summary, then revoke if needed. It is modeled as BPMN To-Be activities T01–T28 across five subprocesses.
- Verification is self-service, with no admin involvement. A failed verification is still returned with its reason. It must not read as an accusation against the holder.
- Holders share links or QR codes through channels they choose, such as job applications or LinkedIn.
- The prototype runs on a local Hardhat chain with at least two test issuers, ISS-001 and ISS-002; the deployment runs on the Base Sepolia testnet. All data is synthetic (assumption A6). One person may play several roles through separate accounts.
- It started as the Deliverable 3 output of course II3120, demonstrated in a 10–15 minute presentation, and is now headed for a public deployment that real organizers could try.

## Capabilities and Constraints

- **Prototype features.** F-01 authentication and RBAC, F-02 credential issuance, F-03 credential view and scoped share links, F-04 verification, F-05 revocation, F-06 skill matching, F-07 audit trail, and F-08 the web interface for three roles.
- **Design rules** (report 1.3):
  - No candidate search, browsing, or candidate lists.
  - An AI summary is available only for a VALID verification that the requesting verifier ran.
  - The AI receives only verified skills and the position text, never the holder's identity.
  - The hiring decision stays with a human.
- **Verification results.** The only possible results are VALID, REVOKED, TAMPERED, and ISSUER_UNAUTHORIZED. Integrity, issuer authorization, and status are reported as three separate checks.
- **AI output.** It lists matched skills, missing requirements, and limitations, and carries the label REKOMENDASI. Similarity is shown per pair only, with no total candidate score.
- **AI outages.** Verification keeps working when the AI service is down; only matching returns 503.
- **Privacy.**
  - Only the commitment, issuer, status, and time are stored on-chain. No personal data and no NIK.
  - `holderDisplayName` is stored off-chain only.
  - The holder's scope and expiry decide which fields a verifier sees.
- **Terminology.** Enum values and error codes stay exactly as written in the report. That covers VALID, REVOKED, TAMPERED, ISSUER_UNAUTHORIZED, REKOMENDASI, active, revoked, and the codes in report 9.5. ID prefixes are CRD-, ISS-, SHL-, VER-, MAT-, HLD-, and SK-.
- **Out of scope.** Candidate search, PDDikti or PISN integration, ATS integration, payment, a blockchain mainnet (the deployment uses the Base Sepolia public testnet), storing original documents, and production-grade identity management. Correction versions (API-11, FR-11) are specified only, not built.
- **Decisions of 2026-11-19 (PRD Open Decisions):**
  - A `platform_admin` role registers issuers through API-01.
  - ISSUER_UNAUTHORIZED appears when the platform admin deactivates an issuer on the registry.
  - Notifications are simulated emails, not sent.
  - Share scopes may include holderDisplayName, program.title, completedAt, program.criteria, and skills. Links last 1 to 720 hours.
  - A position description is 1 to 2,000 characters.

## Brand Commitments

- The name is ProofSkill.
- The interface copy is in English (decided 2026-11-19). API enums and error codes keep the report's exact values.
- The app gets its own visual identity rather than reusing the slide deck's look (decided 2026-11-19).
- Color follows the user's 60/30/10 rule. Two colors do 90% of the work. One unexpected accent color takes the remaining 10%, and it appears only on the button the user should press.

## Evidence on Hand

- **Sources of truth.** The D1+D2 report (Google Doc "Laporan_Kelompok 02_Deliverable 1 II3120") and the deck (Google Slides "PPT_Kelompok 02_Deliverable 2 II3120").
- **Diagrams.** BPMN, SoaML, and architecture diagrams are in `../deliverable2/diagrams/`.
- **Interviews.** The deck has photos documenting the R1–R4 interviews. The detailed findings are not yet written into report Tabel 4.17 and 4.18.
- **Absent material.** There are no real users, testimonials, measured metrics, or production data. All demo data is synthetic, and the interface must say so wherever someone could mistake it for real data.

## Product Principles

1. **Verify before interpreting.** The AI reads only credentials that passed verification.
2. **Show the evidence.** Show the three checks and the chain reference, and claim nothing beyond what was checked.
3. **The holder controls disclosure.** Scope and expiry decide what a verifier sees.
4. **People decide.** AI output is a labeled recommendation with its limitations, never a score or a ranking.
5. **Explain failures without accusing anyone.**
