# CLAUDE.md: ProofSkill

ProofSkill began as the Deliverable 3 prototype for course II3120 (Kelompok 02) and is now being taken to a public deployment (PRD, Deployment decisions; ARCHITECTURE, steps B-01 to B-07). It is a credential issuance and verification service for nonformal training organizers:

- Issuers record a nonce-salted hash commitment, the issuer, and the status on a blockchain registry (a local Hardhat node in development; the Base Sepolia testnet when deployed).
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
| Next.js with TypeScript | Next.js 16.4.6, React 19.3.0, TypeScript 5.9.3 (strict), ESLint 9, qrcode 1.5.4 (share-link QR, approved 2026-11-19). Web app with three portals in `web/`. It proxies `/api/v1` to FastAPI (`API_ORIGIN`), so the API needs no CORS |
| FastAPI | FastAPI 0.165.0 on Python 3.13.17, Uvicorn 0.54.0, Pydantic 2.14.3, pytest 9.2.0, psycopg 3.3.9, httpx 0.28.1, PyJWT 2.15.1, numpy 2.5.5, coincurve 21.0.0 (transaction signing, approved 2026-11-20). REST API under `/api/v1` in `api/`, one module per SoaML service |
| Windows Application Control | Blocks some unsigned native wheels on this machine (`psycopg-binary`, `regex`, `bitarray`, `pycryptodome`, and the `pydantic-core` build that `eth-account` pulls in). So psycopg runs its pure-Python driver with `libpq.dll` from `PG_BIN`, RGS calls JSON-RPC through httpx with a minimal ABI codec instead of web3.py, and RGS signs testnet transactions with coincurve plus its own pure-Python keccak-256 and RLP instead of eth-account. Check new Python dependencies with an import before adopting them |
| PostgreSQL | 17.11 (installed at `C:\Program Files\PostgreSQL\17`). Off-chain data, run as a project-local cluster by `scripts/db.ps1`: data in `.pgdata/`, port 5433, 127.0.0.1 only, trust auth |
| Hardhat with Solidity | Hardhat 3.22.0, ethers 6.17.0, Mocha 12.0.3, Chai 6.3.0, Solidity 0.8.28, hardhat-verify 3.1.5 (Basescan verification, approved 2026-11-20). Local chain, the `baseSepolia` network, and the `ProofSkillRegistry` contract in `contracts/` |
| Gemini embeddings | `gemini-embedding-001` through the Gemini REST API (`batchEmbedContents`, called with httpx; no SDK). Requirements are embedded as `RETRIEVAL_QUERY` and skills as `RETRIEVAL_DOCUMENT`, threshold 0.72 (B-04). Needs `GEMINI_API_KEY`; replaced the local MiniLM model and its ONNX process on 2026-11-19 |
| Supabase Auth with JWT Bearer tokens | Since B-02, API-00 proxies Supabase's password sign-in (username `x` signs in as `x@proofskill.example`) and returns its ES256 access token; guards verify it against the project's JWKS with PyJWT plus cryptography 50.0.2 (approved 2026-11-20). Roles `issuer_admin`, `holder`, `verifier`, plus `platform_admin` for API-01 (OD-1), with `issuerId`, `holderRef`, and `username`, come from `app_metadata`, which only the service-role key can write |

**Deployment target (re-planned 2026-11-19, built in steps B-01 to B-07; B-01 to B-07 done; the API is live at https://proofskill-api.vercel.app and the web app at https://proofskill-two.vercel.app):**

| Tool | Role |
| --- | --- |
| Vercel | Hosts `web/` (B-06) and, since B-05, `api/` as a Python function (Hobby plan, no card; region `sin1`; `api/vercel.json` and `[tool.vercel]` in `api/pyproject.toml`). The web app's `API_ORIGIN` points at the API project. Render was dropped on 2026-11-20 because it refused the team's debit cards |
| Supabase | Postgres for off-chain data since B-01 (project in Singapore, reached through the session pooler; Row Level Security on every table, no policies) and Auth for accounts in B-02; API-00 proxies Supabase sign-in |
| Base Sepolia testnet | Hosts `ProofSkillRegistry` at `0xFB11769EBD22fe1Ac40391227e6526ccf077D136` (B-03, `api/deployments/baseSepolia.json`, inside the API's Vercel project). RGS signs with one key per issuer plus the registry owner's key, kept in the untracked `.env.testnet` and as Vercel environment variables (OD-12). Signed sends are serialized per account by a Postgres advisory lock, because Vercel runs requests concurrently in and across instances |
| Gemini embeddings (free tier) | Used by AMS since B-04 (done); the key is a Vercel environment variable of the API project |
| Reserved: OpenCV / YOLO / MediaPipe, RunPod, LangChain | Not used by any current feature. Add one only after the PRD scopes a feature that needs it |
| Node v26.13.0 | Node package manager: pnpm 12.18.0 (decided at A-01) |
| uv 0.13.7 | Python package manager: uv, lockfile `api/uv.lock` (decided at A-01) |

## Design system

- DESIGN.md is normative. Its YAML frontmatter holds the tokens and its prose holds the rules. It is a pre-build seed. After the first UI build, refresh it with `/impeccable document`.
- Implement the tokens as CSS custom properties in `web/app/globals.css` and load Plus Jakarta Sans and Red Hat Mono through `next/font/google`.
- When a token changes, update DESIGN.md and `globals.css` together.
- The direction (2026-11-20) is liquid glass over the deck's royal blue `#2453D6` and pink seal: frosted glass for floating surfaces, white for reading surfaces, and action pink `#FF7AAE` only on the one action to press, with ink `#0E1A3B` text on it. The 3D art lives in `web/public/art/` (DESIGN.md, 3D art).
- States use words, icons, and fill, never red, green, or amber.
- Use the impeccable skill for UI work. The verifier result page has a surface brief at `.impeccable/surfaces/web-app-v-sharetoken-page-tsx.md`, and its chosen sketch is `.impeccable/mocks/decision/assigned.html`.

## Project Structure

`contracts/`, `api/`, `web/`, and `scripts/` exist since A-01. The rest of the tree fills in as later steps land.

```text
contracts/        # Hardhat: ProofSkillRegistry.sol (registerIssuer, issueCredential, revokeCredential, getRecord, deactivateIssuer), tests, deploy script; the testnet deployment is written to api/deployments/baseSepolia.json, the only tracked one
api/              # FastAPI app
  app/            # modules per SoaML service: ias, cis, css, aas, vrs, rgs (blockchain adapter), scs, ams; plus config, db, seed
  migrations/     # plain SQL, applied in name order by app/db.py
  tests/          # pytest; name tests after TC IDs, e.g. test_tc05_tampered_db_content
web/              # Next.js app: landing /, sign in /signin, issuer portal /issuer, holder portal /holder, verifier /verifier and /v/[shareToken]
  app/            # routes; globals.css holds the DESIGN.md tokens as CSS custom properties
  components/     # Pass (signature), portal shell, skill fit, share QR, notices, icons
  lib/            # typed API client, per-tab session, formatting
scripts/          # db.ps1: start, stop, or check the project-local PostgreSQL cluster
docs/             # project docs: PRD, ARCHITECTURE, TODO, WORKFLOW, DESIGN, PRODUCT
  evidence/       # one record per TC (TC-01..TC-16) for the D3 report
skill/            # project skills: project-setup (docs workflow), run-test-scenario
.impeccable/      # impeccable design context (surface briefs, decision sketches)
```

- Endpoint code belongs to the module of the SoaML service that owns the operation (ARCHITECTURE.md mapping table).
- Only `rgs` talks to the chain.
- Only `ams` calls the embedding API (Gemini).

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
  - Roles: `issuer_admin`, `holder`, `verifier`, plus `platform_admin` (OD-1).
  - AI label: `REKOMENDASI`.
- **Traceability.** Reference the report's IDs (FR-xx, NFR-xx, Txx BPMN activity, TC-xx, API-xx) in docstrings and test names where they explain why code exists.
- **Python.** Use type hints throughout, and Pydantic models that match the report's MessageTypes (`IssueCredentialRequest`, `CredentialIssued`, `VerificationResult`, `MatchingRequest`, `MatchingResult`, `RegistryRecord`, `AuditEvent`).
- **TypeScript.** Strict mode with no `any`. Write UI copy in English and keep enums and error codes verbatim.
- **Hashing.** Use SHA-256 over the canonical payload plus a random nonce. Exclude `holderDisplayName` and never include NIK. The canonical form is in ARCHITECTURE.md (OD-6).
- **Ambiguity.** If a request is ambiguous, or would change something the report defines, ask before writing code.

## Features

Tick an item only after its completion criteria in ARCHITECTURE.md pass.

- [x] F-01 Authentication and RBAC (API-00, API-01)
- [x] F-02 Credential issuance (API-02, API-08)
- [x] F-03 Credential view and share links (API-03, API-04; API-05 optional)
- [x] F-04 Verification (API-06)
- [x] F-05 Revocation (API-09)
- [x] F-06 Skill matching (API-07)
- [x] F-07 Audit trail (API-10)
- [x] F-08 Web interface for issuer, holder, and verifier

## Do Not

- **No candidate search.** Do not add any search, browse, list, or ranking endpoint or UI for candidates. Credential data leaves only through a share token its owner created. The only lists are API-12 and API-13 (OD-10): the caller's own or own-issued credentials, with no query or filter.
- **No personal data on-chain.** Store only the commitment, issuer, status, and time on-chain. Never store NIK, names, GPA, or documents.
- **No identity for the AI.** Do not send holder identity to the AI, local or Gemini. AMS reads skills through `VRS.getVerification` only, never from data the verifier sends, and sends only skill and requirement text.
- **No total score.** Do not return a total candidate score, and never drop the `REKOMENDASI` label or the limitations from AI output.
- **Verification never depends on AI.** If the AI is down, only API-07 returns 503.
- **Contract changes go through the user.** Do not change endpoints, payloads, status codes, error codes, or enums without the user's approval. If a change is approved, list the report and deck sections that must change with it.
- **Do not invent codes.** Use only the error codes in ARCHITECTURE.md (OD-1 named the formerly unnamed ones), and never settle an open decision (OD-9 is still open) on your own.
- **No real secrets in git.** Keep secrets and private keys out of commits: issuer and deployer keys, the Etherscan key, the Supabase service-role key, the accounts' `SEED_PASSWORD`, and the Gemini API key live only in Vercel environment variables or the local untracked `.env` and `.env.testnet`. Only the public Hardhat test accounts may appear in local config and tests.
- **No real data, no mainnet.** Use synthetic data only (assumption A6) until a privacy review allows real participant data. Never deploy to or send transactions on a blockchain mainnet; the deployment uses the Base Sepolia testnet.
- **Pink only on the action.** Do not use action pink anywhere except the single primary action. The seal pink is reserved for the REKOMENDASI tag and soft glows.

## Testing and Build

The defaults match `.env.example`, so set an environment variable only to override one. AI matching needs `GEMINI_API_KEY`: copy `.env.example` to the untracked `.env`, add the key there, and pass `--env-file ../.env` to `uv run` (the API reads only real environment variables). Start each part from the repository root:

| Part | Command | Address |
| --- | --- | --- |
| Database | `powershell -ExecutionPolicy Bypass -File scripts/db.ps1 start` (also `stop`, `status`) | `postgresql://proofskill@127.0.0.1:5433/proofskill` |
| Chain | `cd contracts; pnpm install; pnpm chain`, then `pnpm deploy:local` in a second terminal | `http://127.0.0.1:8545`, contract address in `contracts/deployments/localhost.json` |
| Seed | `cd api; uv sync; uv run python -m app.seed --reset` (needs the database, the chain, and a deploy). It migrates, loads the synthetic seed, and registers ISS-001 and ISS-002 on-chain. The accounts are listed in `api/app/seed.py`; they live in Supabase Auth, and with `SUPABASE_SERVICE_ROLE_KEY` set (in `.env.testnet`) the seed creates or updates them there with the secret `SEED_PASSWORD` from `.env`. Sign in with that password; it is never in git | — |
| Deployed stack (B-01, B-03) | `.env.testnet` (untracked) holds `DATABASE_URL` (Supabase session pooler, `?sslmode=require`), `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `CHAIN_RPC_URL`, `REGISTRY_DEPLOYMENT`, `REGISTRY_OWNER_KEY`, `ISSUER_KEY_ISS_001`, `ISSUER_KEY_ISS_002`, and `ETHERSCAN_API_KEY`. Deploy: `cd contracts; pnpm deploy:base-sepolia`; verify: `pnpm hardhat verify etherscan --network baseSepolia <address>` (done; plain `verify` also tries Blockscout and Sourcify and can hang). Run any API command against the testnet by adding `--env-file ../.env.testnet` after `--env-file ../.env` (the later file wins), for example `uv run --env-file ../.env --env-file ../.env.testnet python -m app.seed --reset` | `https://sepolia.basescan.org/address/0xFB11769EBD22fe1Ac40391227e6526ccf077D136` |
| API on Vercel (B-05) | Vercel project with Root Directory `api/` (zero-config FastAPI through `[tool.vercel]` in `api/pyproject.toml`, region `sin1` in `api/vercel.json`). Environment variables: `DATABASE_URL` (Supabase transaction pooler, port 6543, `?sslmode=require`), `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `CHAIN_RPC_URL`, `REGISTRY_DEPLOYMENT=deployments/baseSepolia.json`, `REGISTRY_OWNER_KEY`, `ISSUER_KEY_ISS_001`, `ISSUER_KEY_ISS_002`, `GEMINI_API_KEY`, `WEB_BASE_URL`. Never set the seed-only `SUPABASE_SERVICE_ROLE_KEY` or `SEED_PASSWORD` there | `https://<project>.vercel.app/api/v1/docs` |
| API | `cd api; uv run --env-file ../.env fastapi dev app/main.py`. Without `GEMINI_API_KEY`, everything works except API-07, which returns 503 `AI_UNAVAILABLE` (TC-10) | `http://127.0.0.1:8000/api/v1/docs` |
| Web on Vercel (B-06) | Vercel project with Root Directory `web/`; environment variable `API_ORIGIN=https://proofskill-api.vercel.app` (the build fails without it). `web/vercel.json` installs pnpm 12.18.0 itself and calls it by path, because Vercel's own pnpm cannot read pnpm 12's lockfile. The API project's `WEB_BASE_URL` must be this site's URL so share links open its verifier page | `https://proofskill-two.vercel.app` |
| Web | `cd web; pnpm install; pnpm dev` (needs the API on port 8000). The landing page is `/`; sign in at `/signin` with a seeded account (`/signin?u=<username>` prefills it); the portal follows the role, and each browser tab keeps its own session | `http://localhost:3000` |

Checks: `pnpm test` in `contracts/`, `uv run --env-file ../.env pytest` in `api/` (needs the database cluster and a running chain; it uses the separate `proofskill_test` database, or whatever `TEST_DATABASE_URL` names, and empties that database before every test, so never point it at a database whose data matters; it deploys its own registry to `contracts/deployments/pytest.json`, and reverts the chain after each test; TC-08 calls the real Gemini API and is skipped without `GEMINI_API_KEY`, the other AI tests use a fake Gemini endpoint; sign-in always uses a fake Supabase Auth with a test-only signing key, so pytest never calls the real project), and `pnpm lint` plus `pnpm build` in `web/`.

- **Contracts.** Hardhat tests cover issue, revoke, read, the other-issuer revert (TC-14), and issuer deactivation (TC-16).
- **API.** pytest, one test per automatable TC (TC-01 to TC-16). Run them against the local Hardhat node and PostgreSQL.
- **Web.** Production build of the Next.js app, plus manual checks in a browser of the three flows: issue, share, verify with skill fit.
- **Evidence.** `cd api; uv run --env-file ../.env python -m scripts.evidence` (needs the database cluster, a running chain, and `GEMINI_API_KEY`; it starts its own API on port 8100 and restarts it without the key for TC-10) runs TC-01 to TC-16 and rewrites `docs/evidence/` in the D3 format: scenario, steps or input, expected result, actual result, status, evidence. `docs/evidence/README.md` summarizes the results and T-01 to T-05. With `--env-file ../.env.testnet --deployed https://proofskill-api.vercel.app` it runs the same scenarios against the deployed stack and writes `docs/evidence/deployed/` instead (B-07): nothing is reset, TC-10 pauses until the flag files `ai-off` and `ai-on` exist after redeploying the API without and with `GEMINI_API_KEY`, and TC-16 deactivates ISS-002 for good, so a repeat run needs another issuer for TC-16. `skill/run-test-scenario/SKILL.md` (local) describes the same format for manual runs.

## Git Rules

The user handles staging, commits, and pushes. When the code changes are done, summarize the result and give the commands in this order:

1. `git add -- <changed-file-paths>`
2. `git diff --cached`
3. `git commit -m "<message describing the change>"`
4. `git push origin main` (remote `origin` is `https://github.com/veinsan/proofskill`; use the current branch if it is not `main`)

Do not stage, commit, or push through any tool yourself.
