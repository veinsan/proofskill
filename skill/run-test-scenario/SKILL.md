---
name: run-test-scenario
description: Use when executing one of ProofSkill's test scenarios TC-01 to TC-15, or when recording test evidence for the Deliverable 3 report.
---

# Run Test Scenario

Run one test scenario (or all of them) against the local prototype and record the evidence in the format the course requires. That format has six fields: scenario, steps or input, expected result, actual result, status, and evidence.

## Inputs

- A TC ID from the table below (`TC-01` to `TC-15`), or `all`.
- A running prototype: the Hardhat node with `ProofSkillRegistry` deployed, PostgreSQL seeded with synthetic data (ISS-001, ISS-002, one account per role), the API, and the web app if the scenario has UI steps. The start commands are in CLAUDE.md.

## Scenarios (report Tabel 10.4)

| ID | Scenario | Expected result | Related |
| --- | --- | --- | --- |
| TC-01 | A registered issuer issues a valid credential | 201; commitment and `txHash` stored | API-02, FR-02, T-01 |
| TC-02 | An account that is not a registered issuer tries to issue | 403 `ISSUER_NOT_AUTHORIZED` | API-02, FR-01 |
| TC-03 | A skill outside the catalog is used | 422 `SKILL_NOT_IN_CATALOG` | API-02, FR-03 |
| TC-04 | An intact credential is verified without an admin | 200, result `VALID` | API-06, FR-06, T-01, T-02 |
| TC-05 | Credential content is changed directly in the database | 200, result `TAMPERED`, no credential data shown | API-06, FR-12 (differentiator test) |
| TC-06 | Verification after revocation, with the database status set back to active | 200, result `REVOKED` with the reason | API-06, API-09, FR-07, T-05 (differentiator test) |
| TC-07 | Expired share link | 410 `SHARE_LINK_EXPIRED` | API-06, FR-05, T-03 |
| TC-08 | Matching after a `VALID` verification | Matched skills, uncovered requirements, label `REKOMENDASI`, no total score | API-07, FR-08, 09, T-04 |
| TC-09 | Matching with a verification that is not `VALID` | 409 `VERIFICATION_NOT_VALID` | API-07, T-04 |
| TC-10 | The AI service is switched off | API-07 returns 503; API-06 keeps working | NFR-06 |
| TC-11 | On-chain data is inspected | Only commitment, issuer, and status, with no personal data | NFR-02, T-03 |
| TC-12 | Verification time on test data | Less than 5 seconds | NFR-05, T-01 |
| TC-13 | Key operations run, then the audit log is read | Every operation logged without sensitive payload | API-10, FR-10 |
| TC-14 | Another issuer's account calls `revokeCredential` directly on the contract | Transaction rejected (revert); status unchanged | RGS, FR-07, T-05 (differentiator test) |
| TC-15 | A verifier uses another verifier's `verificationId` | 403 `VERIFICATION_NOT_OWNED` | API-07, design rule 1.3, T-04 |

## Procedure

1. **Prepare the state the scenario needs.**
   - TC-05: issue and share a credential, then change its content with an SQL `UPDATE` on the off-chain table.
   - TC-06: revoke the credential through API-09, then set its database status back to active.
   - TC-14: use ISS-002's chain account against a credential ISS-001 issued.
   - TC-10: follow the switch-off method decided for OD-8. If OD-8 is still open, stop and report it as blocked.
2. **Execute.**
   - Prefer the automated test named after the TC (pytest, or a Hardhat test for TC-14).
   - Otherwise call the API with `curl` or the FastAPI docs page, using the role's Bearer token, or follow the UI steps.
   - For TC-12, run the verification at least 10 times on test data and report the median and the maximum.
3. **Capture evidence** in `docs/evidence/TC-xx/`:
   - The exact request: method, path, body, and the role used.
   - The response status and body.
   - Chain data: the transaction hash, `getRecord` output, or revert reason.
   - Any SQL that was run.
   - Timing data for TC-12.
   - Screenshots for UI steps.
   - Raw outputs: save them as text or JSON. Mask nothing, because all data is synthetic.
4. **Write the record** to `docs/evidence/TC-xx.md` using the template below.
5. **Set the status strictly.**
   - **Pass** only when the actual result matches the expected result exactly: HTTP status, error code, and result enum.
   - Otherwise **Fail**, with the difference stated.
   - Never change an expected result to fit the actual one. Expected results come from the report.
6. **Update TODO.md.**
   - Note progress on A-13.
   - For each Fail, add a task that names the defect and the TC.

## Record template

```markdown
# TC-xx: <scenario>

| Field | Value |
| --- | --- |
| Related | <API / FR / NFR / T-goal from the table> |
| Steps / input (Langkah/Input) | <numbered steps with exact requests, roles, SQL> |
| Expected (Hasil yang diharapkan) | <from the table, verbatim> |
| Actual (Hasil aktual) | <observed status, code, result, timing> |
| Status (Status pengujian) | Pass / Fail |
| Evidence (Bukti pengujian) | <links to files in docs/evidence/TC-xx/> |
| Date and environment | <YYYY-MM-DD, commit hash, local Hardhat + PostgreSQL> |
```

## Output

List each record path with a one-line result, for example `TC-05: Pass (200, TAMPERED, no data)`. List any scenario that could not run, with its blocker.
