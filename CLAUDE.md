# CLAUDE.md: ProofSkill

ProofSkill is the Deliverable 3 prototype for course II3120, built by Kelompok 02. It is a credential issuance and verification service for nonformal training organizers:

- Issuers record a nonce-salted hash commitment, the issuer, and the status on a local blockchain registry.
- Holders share a scoped link.
- Verifiers check integrity, issuer, and status without contacting an admin, then read an AI skill-fit summary labeled `REKOMENDASI`.

## Read first

| Document | Use it for |
| --- | --- |
| [PRD.md](docs/PRD.md) | Scope, users, user stories, FR and NFR, open decisions |
| [ARCHITECTURE.md](docs/ARCHITECTURE.md) | Stack, service-to-endpoint mapping, API conventions, implementation steps A-01 to A-13 |
| [TODO.md](docs/TODO.md) | Current status, blockers, next step |
| [WORKFLOW.md](docs/WORKFLOW.md) | When to proceed, when to ask, when a task is done |
| [DESIGN.md](docs/DESIGN.md) | Visual tokens and UI rules |
| [PRODUCT.md](docs/PRODUCT.md) | Product context that the impeccable design skill loads |

The external sources of truth are the team's D1+D2 report (Google Doc) and deck (Google Slides). The API contract, codes, and enums in this repository must stay identical to report Bab IX.

## Tech Stack

The team locked the stack on 2026-11-19 (report Tabel 10.3). Versions were pinned at A-01 (2026-11-19); the lockfiles hold the exact tree.

| Tool | Version or role |
| --- | --- |
| Next.js with TypeScript | Next.js 16.4.6, React 19.3.0, TypeScript 5.9.3 (strict), ESLint 9. Web app with three portals in `web/` |
| FastAPI | FastAPI 0.165.0 on Python 3.13.17, Uvicorn 0.54.0, Pydantic 2.14.3, pytest 9.2.0. REST API under `/api/v1` in `api/`, one module per SoaML service |
| PostgreSQL | 17.11 (installed at `C:\Program Files\PostgreSQL\17`). Off-chain data, run as a project-local cluster by `scripts/db.ps1`: data in `.pgdata/`, port 5433, 127.0.0.1 only, trust auth |
| Hardhat with Solidity | Hardhat 3.22.0, ethers 6.17.0, Mocha 12.0.3, Chai 6.3.0, Solidity 0.8.28. Local chain and the `ProofSkillRegistry` contract in `contracts/` |
| `paraphrase-multilingual-MiniLM-L12-v2` | Sentence embeddings for AI matching, run locally |
| JWT Bearer tokens | Roles `issuer_admin`, `holder`, `verifier` (platform admin is pending, OD-1) |
| Node v26.13.0 | Node package manager: pnpm 12.18.0 (decided at A-01) |
| uv 0.13.7 | Python package manager: uv, lockfile `api/uv.lock` (decided at A-01) |

## Design system

- DESIGN.md is normative. Its YAML frontmatter holds the tokens and its prose holds the rules. It is a pre-build seed. After the first UI build, refresh it with `/impeccable document`.
- Implement the tokens as CSS custom properties in `web/app/globals.css` and load Archivo and Red Hat Mono through `next/font/google` (planned).
- When a token changes, update DESIGN.md and `globals.css` together.
- The color rule is 60/30/10: Paper White about 60%, Gate Navy `#0F1B3D` about 30%, and Signal Pink `#FF3D8B` only on the one action to press, with navy text on it.
- States use words, icons, and fill, never red, green, or amber.
- Use the impeccable skill for UI work. The verifier result page has a surface brief at `.impeccable/surfaces/web-app-v-sharetoken-page-tsx.md`, and its chosen sketch is `.impeccable/mocks/decision/assigned.html`.

## Project Structure

`contracts/`, `api/`, `web/`, and `scripts/` exist since A-01. The rest of the tree fills in as later steps land.

```text
contracts/        # Hardhat: ProofSkillRegistry.sol (registerIssuer, issueCredential, revokeCredential, getRecord), tests, deploy script
api/              # FastAPI app
  app/            # modules per SoaML service: ias, cis, css, aas, vrs, rgs (blockchain adapter), scs, ams
  tests/          # pytest; name tests after TC IDs, e.g. test_tc05_tampered_db_content
web/              # Next.js app: issuer portal, holder portal, verifier route /v/[shareToken]
scripts/          # db.ps1: start, stop, or check the project-local PostgreSQL cluster
docs/             # project docs: PRD, ARCHITECTURE, TODO, WORKFLOW, DESIGN, PRODUCT
  evidence/       # one record per TC (TC-01..TC-15) for the D3 report
skill/            # project skills: project-setup (docs workflow), run-test-scenario
.impeccable/      # impeccable design context (surface briefs, decision sketches)
```

- Endpoint code belongs to the module of the SoaML service that owns the operation (ARCHITECTURE.md mapping table).
- Only `rgs` talks to the chain.
- Only `ams` loads the embedding model.

## Code Conventions

- **API.**
  - Base URL `/api/v1`, JSON in UTF-8, times in ISO 8601 UTC.
  - ID prefixes `CRD-`, `ISS-`, `SHL-`, `VER-`, `MAT-`, `HLD-`, `SK-`.
  - Error body `{"error": {"code", "message", "requestId"}}`.
  - Use exactly the status codes and error codes in ARCHITECTURE.md.
  - A credential that fails verification still returns 200 with `result`.
- **Enums.** Copy them verbatim from the report:
  - Credential status: `active`, `revoked`.
  - Verification result: `VALID`, `REVOKED`, `TAMPERED`, `ISSUER_UNAUTHORIZED`.
  - Check values: `PASS`/`FAIL` and `ACTIVE`/`REVOKED`.
  - Roles: `issuer_admin`, `holder`, `verifier`.
  - AI label: `REKOMENDASI`.
- **Traceability.** Reference the report's IDs (FR-xx, NFR-xx, Txx BPMN activity, TC-xx, API-xx) in docstrings and test names where they explain why code exists.
- **Python.** Use type hints throughout, and Pydantic models that match the report's MessageTypes (`IssueCredentialRequest`, `CredentialIssued`, `VerificationResult`, `MatchingRequest`, `MatchingResult`, `RegistryRecord`, `AuditEvent`).
- **TypeScript.** Strict mode with no `any`. Write UI copy in English and keep enums and error codes verbatim.
- **Hashing.** Use SHA-256 over the canonical payload plus a random nonce. Exclude `holderDisplayName` and never include NIK. The canonical form is pending (OD-6).
- **Ambiguity.** If a request is ambiguous, or would change something the report defines, ask before writing code.

## Features

No feature is built yet. Tick an item only after its completion criteria in ARCHITECTURE.md pass.

- [ ] F-01 Authentication and RBAC (API-00, API-01)
- [ ] F-02 Credential issuance (API-02, API-08)
- [ ] F-03 Credential view and share links (API-03, API-04; API-05 optional)
- [ ] F-04 Verification (API-06)
- [ ] F-05 Revocation (API-09)
- [ ] F-06 Skill matching (API-07)
- [ ] F-07 Audit trail (API-10)
- [ ] F-08 Web interface for issuer, holder, and verifier

## Do Not

- **No candidate search.** Do not add any search, browse, list, or ranking endpoint or UI for candidates. Credential data leaves only through a share token its owner created.
- **No personal data on-chain.** Store only the commitment, issuer, status, and time on-chain. Never store NIK, names, GPA, or documents.
- **No identity for the AI.** Do not send holder identity to the AI. AMS reads skills through `VRS.getVerification` only, never from data the verifier sends.
- **No total score.** Do not return a total candidate score, and never drop the `REKOMENDASI` label or the limitations from AI output.
- **Verification never depends on AI.** If the AI is down, only API-07 returns 503.
- **Contract changes go through the user.** Do not change endpoints, payloads, status codes, error codes, or enums without the user's approval. If a change is approved, list the report and deck sections that must change with it.
- **Do not invent codes.** Never invent names for the unnamed error codes (OD-1) or settle any other open decision on your own.
- **No real secrets in git.** Keep secrets and private keys out of commits. Only the public Hardhat test accounts may appear in local config, and `.env` stays untracked.
- **No real data.** Use synthetic data only (assumption A6), and never connect to a public blockchain.
- **Pink only on the action.** Do not use Signal Pink anywhere except the single primary action.

## Testing and Build

Copy `.env.example` to `.env` first. Start each part from the repository root:

| Part | Command | Address |
| --- | --- | --- |
| Database | `powershell -ExecutionPolicy Bypass -File scripts/db.ps1 start` (also `stop`, `status`) | `postgresql://proofskill@127.0.0.1:5433/proofskill` |
| Chain | `cd contracts; pnpm install; pnpm chain`, then `pnpm deploy:local` in a second terminal | `http://127.0.0.1:8545`, contract address in `contracts/deployments/localhost.json` |
| API | `cd api; uv sync; uv run fastapi dev app/main.py` | `http://127.0.0.1:8000/api/v1/docs` |
| Web | `cd web; pnpm install; pnpm dev` | `http://localhost:3000` |

Checks: `pnpm test` in `contracts/`, `uv run pytest` in `api/`, and `pnpm lint` plus `pnpm build` in `web/`.

- **Contracts.** Hardhat tests cover issue, revoke, read, and the other-issuer revert (TC-14).
- **API.** pytest, one test per automatable TC (TC-01 to TC-15). Run them against the local Hardhat node and PostgreSQL.
- **Web.** Production build of the Next.js app, plus manual checks in a browser of the three flows: issue, share, verify with skill fit.
- **Evidence.** Use `skill/run-test-scenario/SKILL.md` to record each TC in `docs/evidence/` in the D3 format: scenario, steps or input, expected result, actual result, status, evidence.

## Git Rules

The user handles staging, commits, and pushes. When the code changes are done, summarize the result and give the commands in this order:

1. `git add -- <changed-file-paths>`
2. `git diff --cached`
3. `git commit -m "<message describing the change>"`
4. `git push origin main` (remote `origin` is `https://github.com/veinsan/proofskill`; use the current branch if it is not `main`)

Do not stage, commit, or push through any tool yourself.
