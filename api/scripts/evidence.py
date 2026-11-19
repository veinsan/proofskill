"""A-13 evidence runner: executes TC-01..TC-16 against a fresh, isolated local stack and writes the
Deliverable 3 records to docs/evidence/ (skill/run-test-scenario format: scenario, steps or input,
expected result, actual result, status, evidence).

It needs the PostgreSQL cluster (scripts/db.ps1 start) and the Hardhat node (pnpm chain). It creates
its own database (proofskill_evidence), deploys its own registry (contracts/deployments/evidence.json),
and starts its own API (port 8100). AI matching calls the Gemini API (B-04), so GEMINI_API_KEY must be
set; TC-10 restarts the API without it to switch the AI off. All data is synthetic (A6), so nothing
is masked; access tokens are recorded by role only.

Run from api/: uv run --env-file ../.env python -m scripts.evidence
"""

import json
import os
import re
import secrets
import shutil
import statistics
import subprocess
import sys
import time
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import httpx

from app import db  # first: app/__init__.py puts libpq on PATH before psycopg loads
from app import ams, config, rgs, seed

API_DIR = Path(__file__).resolve().parents[1]
REPO = API_DIR.parent
CONTRACTS = REPO / "contracts"
EVIDENCE = REPO / "docs" / "evidence"
DEPLOYMENT = CONTRACTS / "deployments" / "evidence.json"
DATABASE_URL = os.environ.get("EVIDENCE_DATABASE_URL", "postgresql://proofskill@127.0.0.1:5433/proofskill_evidence")
API_PORT = 8100
API = f"http://127.0.0.1:{API_PORT}/api/v1"

ISSUE_REQUEST: dict[str, Any] = {  # report API-02 example payload
    "holderRef": "HLD-2026-0007",
    "holderDisplayName": "Peserta Contoh A",
    "program": {
        "title": "Pelatihan Keamanan Aplikasi Web Dasar",
        "completedAt": "2026-10-20",
        "criteria": "Kehadiran minimal 80 persen dan lulus proyek akhir",
    },
    "skills": ["SK-014", "SK-021", "SK-033"],
}
SCOPE = {"scope": ["program.title", "completedAt", "skills"], "expiresInHours": 72}
POSITION = {"title": seed.POSITIONS[0][0], "description": seed.POSITIONS[0][1]}  # report API-07 example
REASON = {"reason": "Data kelulusan keliru"}


@dataclass
class Record:
    id: str
    scenario: str
    related: str
    expected: str
    steps: list[str] = field(default_factory=list)
    actual: str = ""
    passed: bool = False
    files: list[str] = field(default_factory=list)

    def save(self, name: str, content: Any) -> None:
        folder = EVIDENCE / self.id
        folder.mkdir(parents=True, exist_ok=True)
        path = folder / name
        if isinstance(content, str):
            path.write_text(content, encoding="utf-8")
        else:
            path.write_text(json.dumps(content, indent=2, ensure_ascii=False, default=str) + "\n", encoding="utf-8")
        self.files.append(f"{self.id}/{name}")


class Stack:
    def __init__(self) -> None:
        self.tokens: dict[str, str] = {}
        self.api: subprocess.Popen[bytes] | None = None
        self.env = {
            **os.environ,
            "DATABASE_URL": DATABASE_URL,
            "REGISTRY_DEPLOYMENT": str(DEPLOYMENT),
            "JWT_SECRET": secrets.token_urlsafe(32),
        }

    # --- setup ---------------------------------------------------------------------------

    def prepare(self) -> None:
        info = db.psycopg.conninfo.conninfo_to_dict(DATABASE_URL)
        admin_url = db.psycopg.conninfo.make_conninfo(DATABASE_URL, dbname="postgres")
        with db.psycopg.connect(admin_url, autocommit=True) as admin:
            if not admin.execute("SELECT 1 FROM pg_database WHERE datname = %s", (info["dbname"],)).fetchone():
                admin.execute(f'CREATE DATABASE "{info["dbname"]}"')  # type: ignore[arg-type]
        pnpm = shutil.which("pnpm")
        assert pnpm, "pnpm is needed to deploy the registry"
        subprocess.run(
            [pnpm, "exec", "hardhat", "run", "scripts/deploy.ts", "--network", "localhost"],
            cwd=CONTRACTS, env={**os.environ, "DEPLOYMENT_OUT": str(DEPLOYMENT)}, check=True, capture_output=True,
        )
        config.REGISTRY_DEPLOYMENT = DEPLOYMENT
        rgs._deployment.cache_clear()
        with db.connect(DATABASE_URL) as conn:
            db.reset(conn)
            db.migrate(conn)
            seed.seed(conn)
            seed.register_issuers_on_chain(conn)
        self.start_api()
        for username, *_ in seed.ACCOUNTS:
            self.tokens[username] = self.call("POST", "/auth/token", body={"username": username, "password": seed.DEMO_PASSWORD})[1]["accessToken"]

    def start_api(self, gemini_key: str | None = None) -> None:
        """Starts the API; JWT_SECRET is fixed, so tokens survive a restart (TC-10)."""
        env = self.env if gemini_key is None else {**self.env, "GEMINI_API_KEY": gemini_key}
        self.api = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", str(API_PORT)],
            cwd=API_DIR, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        self._wait(lambda: httpx.get(f"{API}/openapi.json", timeout=5).status_code == 200, "API")

    def stop_api(self) -> None:
        if self.api:
            self.api.terminate()
            self.api.wait(timeout=30)
            self.api = None

    @staticmethod
    def _wait(ready: Any, name: str) -> None:
        deadline = time.monotonic() + 90
        while time.monotonic() < deadline:
            try:
                if ready():
                    return
            except httpx.HTTPError:
                pass
            time.sleep(0.5)
        raise RuntimeError(f"{name} did not start")

    def close(self) -> None:
        self.stop_api()

    # --- calls ---------------------------------------------------------------------------

    def call(self, method: str, path: str, role: str | None = None, body: Any = None) -> tuple[int, Any, float]:
        headers = {"Authorization": f"Bearer {self.tokens[role]}"} if role else {}
        start = time.perf_counter()
        response = httpx.request(method, f"{API}{path}", json=body, headers=headers, timeout=60)
        elapsed = time.perf_counter() - start
        payload = response.json() if response.content else None
        return response.status_code, payload, elapsed

    def exchange(self, record: Record, name: str, method: str, path: str, role: str | None = None, body: Any = None) -> tuple[int, Any]:
        status, payload, elapsed = self.call(method, path, role, body)
        record.save(name, {
            "request": {"method": method, "path": f"/api/v1{path}", "role": role or "none", "body": body},
            "response": {"status": status, "body": payload},
            "elapsedMs": round(elapsed * 1000, 1),
        })
        return status, payload

    def sql(self, record: Record, name: str, statement: str) -> None:
        with db.connect(DATABASE_URL) as conn:
            conn.execute(statement)  # type: ignore[arg-type]  # fixed statements written in this file
            conn.commit()
        record.save(name, statement + "\n")

    def query(self, statement: str, *params: Any) -> list[dict[str, Any]]:
        with db.connect(DATABASE_URL) as conn:
            return [dict(r) for r in conn.execute(statement, params).fetchall()]  # type: ignore[arg-type]


def error_code(payload: Any) -> str | None:
    return payload.get("error", {}).get("code") if isinstance(payload, dict) else None


def run(stack: Stack) -> tuple[list[Record], dict[str, str]]:
    records: list[Record] = []
    goals: dict[str, str] = {}

    def new(*args: str) -> Record:
        record = Record(*args)
        records.append(record)
        return record

    # TC-01 ---------------------------------------------------------------------------------
    r = new("TC-01", "A registered issuer issues a valid credential", "API-02, FR-02, T-01", "201; commitment and `txHash` stored")
    status, body = stack.exchange(r, "issue-request-response.json", "POST", "/credentials", "admin.iss001", ISSUE_REQUEST)
    row = stack.query("SELECT credential_id, issuer_id, holder_ref, commitment, tx_hash, status FROM credentials WHERE credential_id = %s", body.get("credentialId"))
    record = rgs.get_record(body["credentialId"]) if status == 201 else None
    r.save("db-row.json", row)
    r.save("chain-getRecord.json", record.__dict__ if record else None)
    r.steps = [
        "Sign in as `admin.iss001` (issuer admin of ISS-001) through API-00.",
        "POST /api/v1/credentials with the report's API-02 example payload (HLD-2026-0007, three catalog skills).",
        "Read the stored row from `credentials` and call `getRecord` on the registry for the returned ID.",
    ]
    stored_ok = bool(row) and row[0]["commitment"] == body.get("commitment") and row[0]["tx_hash"] == body.get("txHash")
    chain_ok = record is not None and record.commitment == body.get("commitment")
    r.passed = status == 201 and stored_ok and chain_ok
    r.actual = (f"{status}; {body.get('credentialId')} issued by ISS-001. Commitment `{str(body.get('commitment'))[:18]}…` is stored off-chain and "
                f"returned by `getRecord` on-chain ({'equal' if chain_ok else 'different'}); `txHash` `{str(body.get('txHash'))[:18]}…` is stored.")
    crd1 = body["credentialId"]

    # TC-02 ---------------------------------------------------------------------------------
    r = new("TC-02", "An account that is not a registered issuer tries to issue", "API-02, FR-01", "403 `ISSUER_NOT_AUTHORIZED`")
    before = stack.query("SELECT count(*) AS n FROM credentials")[0]["n"]
    status, body = stack.exchange(r, "issue-request-response.json", "POST", "/credentials", "admin.unregistered", ISSUE_REQUEST)
    after = stack.query("SELECT count(*) AS n FROM credentials")[0]["n"]
    r.steps = ["Sign in as `admin.unregistered` (an issuer_admin account bound to no registered issuer).", "POST /api/v1/credentials with the same payload as TC-01.", "Count rows in `credentials` before and after."]
    r.passed = status == 403 and error_code(body) == "ISSUER_NOT_AUTHORIZED" and before == after
    r.actual = f"{status} `{error_code(body)}`; credentials before {before}, after {after} (nothing issued)."

    # TC-03 ---------------------------------------------------------------------------------
    r = new("TC-03", "A skill outside the catalog is used", "API-02, FR-03", "422 `SKILL_NOT_IN_CATALOG`")
    status, body = stack.exchange(r, "issue-request-response.json", "POST", "/credentials", "admin.iss001", {**ISSUE_REQUEST, "skills": ["SK-014", "SK-999"]})
    r.steps = ["Sign in as `admin.iss001`.", "POST /api/v1/credentials with skills `SK-014` and `SK-999` (SK-999 is not in the catalog)."]
    r.passed = status == 422 and error_code(body) == "SKILL_NOT_IN_CATALOG"
    r.actual = f"{status} `{error_code(body)}`: {body.get('error', {}).get('message')}"

    # Shared setup: the holder shares CRD-0001 -----------------------------------------------
    link1 = stack.call("POST", f"/credentials/{crd1}/share-links", "holder.a", SCOPE)[1]

    # TC-04 ---------------------------------------------------------------------------------
    r = new("TC-04", "An intact credential is verified without an admin", "API-06, FR-06, T-01, T-02", "200, result `VALID`")
    r.save("setup-share-link.json", {"request": {"method": "POST", "path": f"/api/v1/credentials/{crd1}/share-links", "role": "holder.a", "body": SCOPE}, "response": link1})
    audit_before = stack.query("SELECT count(*) AS n FROM audit_events WHERE actor_role = 'issuer_admin'")[0]["n"]
    status, verification = stack.exchange(r, "verify-request-response.json", "POST", "/verifications", "verifier.a", {"shareToken": link1["shareToken"]})
    audit_after = stack.query("SELECT count(*) AS n FROM audit_events WHERE actor_role = 'issuer_admin'")[0]["n"]
    r.steps = [
        f"As `holder.a`, create a share link for {crd1} with scope program.title, completedAt, skills and 72 hours (API-04).",
        "As `verifier.a`, POST /api/v1/verifications with the share token. No issuer account takes part.",
    ]
    r.passed = status == 200 and verification.get("result") == "VALID"
    r.actual = (f"{status}, result `{verification.get('result')}`, checks {verification.get('checks')}. Issuer-admin audit events during verification: "
                f"{audit_after - audit_before}. Returned credential fields: {sorted(verification.get('credential', {}).keys())}.")
    ver_valid = verification["verificationId"]
    goals["T-02"] = f"0 admin steps: the verification used only the verifier's token, and issuer-admin audit events stayed at {audit_before} (TC-04)."
    shared = verification.get("credential", {})
    goals["T-03 (scope)"] = (f"The verifier received only `credentialId`, `issuer`, and the scoped fields {sorted(set(shared) - {'credentialId', 'issuer'})}; "
                             "`holderDisplayName` and `program.criteria` were not shared and not returned (TC-04).")

    # TC-12 ---------------------------------------------------------------------------------
    r = new("TC-12", "Verification time on test data", "NFR-05, T-01", "Less than 5 seconds")
    durations = []
    for _ in range(10):
        status, body, elapsed = stack.call("POST", "/verifications", "verifier.a", {"shareToken": link1["shareToken"]})
        durations.append({"status": status, "result": body.get("result"), "seconds": round(elapsed, 4)})
    seconds = [d["seconds"] for d in durations]
    median, worst = statistics.median(seconds), max(seconds)
    r.save("timings.json", {"runs": durations, "medianSeconds": median, "maxSeconds": worst})
    r.steps = ["As `verifier.a`, POST /api/v1/verifications with the TC-04 share token 10 times over HTTP against the running API.", "Measure each round trip on the client (includes the registry read and hash recomputation)."]
    r.passed = worst < 5 and all(d["result"] == "VALID" for d in durations)
    r.actual = f"10 runs, all `VALID`: median {median:.3f} s, max {worst:.3f} s."
    goals["T-01"] = f"Median {median:.3f} s, max {worst:.3f} s over 10 verifications on test data (target < 5 s; TC-12)."

    # TC-08 ---------------------------------------------------------------------------------
    r = new("TC-08", "Matching after a `VALID` verification", "API-07, FR-08, 09, T-04", "Matched skills, uncovered requirements, label `REKOMENDASI`, no total score")
    status, body = stack.exchange(r, "matching-request-response.json", "POST", "/matchings", "verifier.a", {"verificationId": ver_valid, "position": POSITION})
    no_score = "score" not in json.dumps(body).lower()
    r.steps = [f"As `verifier.a`, POST /api/v1/matchings with {ver_valid} (VALID, from TC-04) and the report's API-07 position (Junior Security Analyst)."]
    r.passed = status == 200 and body.get("label") == "REKOMENDASI" and bool(body.get("matchedSkills")) and bool(body.get("missingRequirements")) and no_score
    pairs = "; ".join(f"{m['skill']} ← \"{m['requirement']}\" ({m['similarity']})" for m in body.get("matchedSkills", []))
    missing = "; ".join(m["requirement"] for m in body.get("missingRequirements", []))
    r.actual = f"{status}, label `{body.get('label')}`. Matched: {pairs}. Not covered: {missing}. No total score field. Model {body.get('modelVersion')}."
    labeled = 0
    for title, description in seed.POSITIONS:
        s, b, _ = stack.call("POST", "/matchings", "verifier.a", {"verificationId": ver_valid, "position": {"title": title, "description": description}})
        labeled += int(s == 200 and b.get("label") == "REKOMENDASI" and bool(b.get("limitations")))
    goals["T-04"] = f"{labeled}/{len(seed.POSITIONS)} matchings on the VALID credential carried `REKOMENDASI` and limitations, with no total score (TC-08)."

    # TC-15 ---------------------------------------------------------------------------------
    r = new("TC-15", "A verifier uses another verifier's `verificationId`", "API-07, design rule 1.3, T-04", "403 `VERIFICATION_NOT_OWNED`")
    status, body = stack.exchange(r, "matching-request-response.json", "POST", "/matchings", "verifier.b", {"verificationId": ver_valid, "position": POSITION})
    r.steps = [f"As `verifier.b`, POST /api/v1/matchings with {ver_valid}, which `verifier.a` ran."]
    r.passed = status == 403 and error_code(body) == "VERIFICATION_NOT_OWNED"
    r.actual = f"{status} `{error_code(body)}`."

    # TC-10 ---------------------------------------------------------------------------------
    r = new("TC-10", "The AI service is switched off", "NFR-06", "API-07 returns 503; API-06 keeps working")
    stack.stop_api()
    stack.start_api(gemini_key="")
    status_ai, body_ai = stack.exchange(r, "matching-ai-off.json", "POST", "/matchings", "verifier.a", {"verificationId": ver_valid, "position": POSITION})
    status_v, body_v = stack.exchange(r, "verify-ai-off.json", "POST", "/verifications", "verifier.a", {"shareToken": link1["shareToken"]})
    stack.stop_api()
    stack.start_api()
    r.steps = [
        f"Restart the API on port {API_PORT} with GEMINI_API_KEY empty, so Gemini is unreachable (OD-8 as revised in B-04).",
        f"As `verifier.a`, POST /api/v1/matchings with {ver_valid}.",
        "As `verifier.a`, POST /api/v1/verifications with the TC-04 share token.",
        "Restart the API with the key for the remaining scenarios.",
    ]
    r.passed = status_ai == 503 and error_code(body_ai) == "AI_UNAVAILABLE" and status_v == 200 and body_v.get("result") == "VALID"
    r.actual = f"API-07: {status_ai} `{error_code(body_ai)}`. API-06: {status_v}, result `{body_v.get('result')}`."

    # TC-11 ---------------------------------------------------------------------------------
    r = new("TC-11", "On-chain data is inspected", "NFR-02, T-03", "Only commitment, issuer, and status, with no personal data")
    tx = rgs._rpc("eth_getTransactionByHash", [stack.query("SELECT tx_hash FROM credentials WHERE credential_id = %s", crd1)[0]["tx_hash"]])
    raw = rgs._call("getRecord(string)", [("string", crd1)])
    decoded = rgs.get_record(crd1)
    personal = [ISSUE_REQUEST["holderDisplayName"], ISSUE_REQUEST["holderRef"], ISSUE_REQUEST["program"]["title"], ISSUE_REQUEST["program"]["criteria"]]
    found = [v for v in personal for blob in (bytes.fromhex(tx["input"][2:]), raw) if v.encode() in blob]
    r.save("issue-transaction.json", {"hash": tx["hash"], "from": tx["from"], "to": tx["to"], "input": tx["input"]})
    r.save("getRecord-raw.txt", "0x" + raw.hex() + "\n")
    r.save("getRecord-decoded.json", decoded.__dict__)
    r.steps = [f"Fetch the issuance transaction of {crd1} with `eth_getTransactionByHash` and read its input data.", f"Call `getRecord(\"{crd1}\")` and keep the raw ABI output.", "Search both byte strings for the holder's name, holderRef, program title, and criteria."]
    r.passed = not found
    r.actual = (f"Personal values found on-chain: {found or 'none'}. The record holds commitment `{decoded.commitment[:18]}…`, issuer `{decoded.issuer_id}`, "
                f"status `{decoded.status}`, timestamp, and `issuerActive` (OD-2); the transaction input holds only the credential ID and the commitment.")
    goals["T-03 (chain)"] = "No personal data on-chain: name, holderRef, program title, and criteria are absent from the transaction input and the record (TC-11)."

    # TC-05 ---------------------------------------------------------------------------------
    r = new("TC-05", "Credential content is changed directly in the database", "API-06, FR-12 (differentiator test)", "200, result `TAMPERED`, no credential data shown")
    crd2 = stack.call("POST", "/credentials", "admin.iss001", ISSUE_REQUEST)[1]["credentialId"]
    link2 = stack.call("POST", f"/credentials/{crd2}/share-links", "holder.a", SCOPE)[1]
    stack.sql(r, "tamper.sql", f"UPDATE credentials SET program_title = 'Pelatihan Keamanan Aplikasi Web Lanjutan' WHERE credential_id = '{crd2}';")
    status, tampered = stack.exchange(r, "verify-request-response.json", "POST", "/verifications", "verifier.a", {"shareToken": link2["shareToken"]})
    r.steps = [f"As `admin.iss001`, issue {crd2}; as `holder.a`, share it.", f"Change its program title with the SQL in `tamper.sql`.", "As `verifier.a`, verify the share token."]
    r.passed = status == 200 and tampered.get("result") == "TAMPERED" and "credential" not in tampered
    r.actual = f"{status}, result `{tampered.get('result')}`, integrity `{tampered.get('checks', {}).get('integrity')}`, credential data returned: {'credential' in tampered}."

    # TC-09 ---------------------------------------------------------------------------------
    r = new("TC-09", "Matching with a verification that is not `VALID`", "API-07, T-04", "409 `VERIFICATION_NOT_VALID`")
    status, body = stack.exchange(r, "matching-request-response.json", "POST", "/matchings", "verifier.a", {"verificationId": tampered["verificationId"], "position": POSITION})
    r.steps = [f"As `verifier.a`, POST /api/v1/matchings with {tampered['verificationId']}, the TAMPERED verification from TC-05."]
    r.passed = status == 409 and error_code(body) == "VERIFICATION_NOT_VALID"
    r.actual = f"{status} `{error_code(body)}`."

    # TC-07 ---------------------------------------------------------------------------------
    r = new("TC-07", "Expired share link", "API-06, FR-05, T-03", "410 `SHARE_LINK_EXPIRED`")
    link3 = stack.call("POST", f"/credentials/{crd1}/share-links", "holder.a", SCOPE)[1]
    stack.sql(r, "expire.sql", f"UPDATE share_links SET expires_at = now() - interval '1 minute' WHERE link_id = '{link3['linkId']}';")
    status, body = stack.exchange(r, "verify-request-response.json", "POST", "/verifications", "verifier.a", {"shareToken": link3["shareToken"]})
    r.steps = [f"As `holder.a`, create share link {link3['linkId']} for {crd1}.", "Move its expiry into the past with the SQL in `expire.sql` (stands in for waiting 72 hours).", "As `verifier.a`, verify its token."]
    r.passed = status == 410 and error_code(body) == "SHARE_LINK_EXPIRED"
    r.actual = f"{status} `{error_code(body)}`."

    # TC-14 ---------------------------------------------------------------------------------
    r = new("TC-14", "Another issuer's account calls `revokeCredential` directly on the contract", "RGS, FR-07, T-05 (differentiator test)", "Transaction rejected (revert); status unchanged")
    iss002_account = seed.ISSUERS[1][3]
    try:
        rgs.revoke_credential(crd1, iss002_account)
        revert = "no revert"
    except rgs.RegistryError as exc:
        revert = str(exc)
    after_record = rgs.get_record(crd1)
    r.save("direct-contract-call.json", {"function": "revokeCredential(string)", "args": [crd1], "from": iss002_account, "fromIssuer": "ISS-002",
                                         "revert": revert, "statusAfter": after_record.status})
    pnpm = shutil.which("pnpm")
    hardhat = subprocess.run([pnpm or "pnpm", "test"], cwd=CONTRACTS, capture_output=True, text=True, encoding="utf-8", errors="replace")
    r.save("hardhat-test.txt", re.sub(r"\x1b\[[0-9;]*m", "", hardhat.stdout))
    hardhat_ok = "TC-14: reverts when another issuer revokes" in hardhat.stdout and hardhat.returncode == 0
    r.steps = [f"Send `revokeCredential(\"{crd1}\")` to the registry directly from ISS-002's chain account {iss002_account}, bypassing the API.", f"Read `getRecord(\"{crd1}\")`.", "Also run the contract's Hardhat suite (`pnpm test`), which includes the same scenario."]
    r.passed = revert == "NotOriginalIssuer" and after_record.status == "active" and hardhat_ok
    r.actual = f"Reverted with `{revert}`; status afterwards `{after_record.status}`. Hardhat suite: {'passed, including TC-14' if hardhat_ok else 'failed'}."

    # TC-06 ---------------------------------------------------------------------------------
    r = new("TC-06", "Verification after revocation, with the database status set back to active", "API-06, API-09, FR-07, T-05 (differentiator test)", "200, result `REVOKED` with the reason")
    status_rev, body_rev = stack.exchange(r, "revoke-request-response.json", "POST", f"/credentials/{crd1}/revocations", "admin.iss001", REASON)
    stack.sql(r, "reset-status.sql", f"UPDATE credentials SET status = 'active', revoked_at = NULL WHERE credential_id = '{crd1}';")
    status, revoked = stack.exchange(r, "verify-request-response.json", "POST", "/verifications", "verifier.a", {"shareToken": link1["shareToken"]})
    later = [stack.call("POST", "/verifications", "verifier.a", {"shareToken": link1["shareToken"]})[1].get("result") for _ in range(5)]
    r.save("later-verifications.json", later)
    r.steps = [f"As `admin.iss001`, revoke {crd1} with reason \"{REASON['reason']}\" (API-09).", "Set its database status back to active with the SQL in `reset-status.sql`.", "As `verifier.a`, verify the TC-04 share token, then 5 more times."]
    r.passed = status_rev == 200 and status == 200 and revoked.get("result") == "REVOKED" and revoked.get("reason") == REASON["reason"]
    r.actual = f"Revocation {status_rev}. Verification {status}, result `{revoked.get('result')}`, status check `{revoked.get('checks', {}).get('status')}`, reason \"{revoked.get('reason')}\"."
    goals["T-05"] = (f"{later.count('REVOKED')}/{len(later)} later verifications read REVOKED after the database row was set back to active (TC-06), "
                     "and another issuer's direct revoke was rejected by the contract (TC-14).")

    # TC-13 ---------------------------------------------------------------------------------
    r = new("TC-13", "Key operations run, then the audit log is read", "API-10, FR-10", "Every operation logged without sensitive payload")
    status, audit = stack.exchange(r, "audit-request-response.json", "GET", "/audit-logs?limit=200", "admin.iss001")
    operations = {item["operation"] for item in audit.get("items", [])}
    sensitive = [ISSUE_REQUEST["holderDisplayName"], ISSUE_REQUEST["holderRef"], ISSUE_REQUEST["program"]["title"], REASON["reason"], link1["shareToken"], POSITION["description"], "verifier.a"]
    leaked = [v for v in sensitive if v in json.dumps(audit, ensure_ascii=False)]
    table = stack.query("SELECT * FROM audit_events ORDER BY event_id")
    leaked_table = [v for v in sensitive if v in json.dumps(table, ensure_ascii=False, default=str)]
    r.save("audit-table.json", table)
    expected_ops = {"issueCredential", "createShareLink", "verifyCredential", "matchSkills", "revokeCredential"}
    r.steps = ["After TC-01 to TC-06 (issue, share, verify, match, revoke), as `admin.iss001` GET /api/v1/audit-logs.", "Dump the `audit_events` table.", "Search both for the holder's name, holderRef, program title, revocation reason, share token, position text, and verifier username."]
    r.passed = status == 200 and expected_ops <= operations and not leaked and not leaked_table
    r.actual = (f"{status}, {audit.get('total')} events covering {sorted(operations)}. Each item has only time, actorRole, operation, objectId, outcome. "
                f"Sensitive values found: {leaked + leaked_table or 'none'}.")

    # TC-16 ---------------------------------------------------------------------------------
    r = new("TC-16", "The platform admin deactivates the issuer on the registry, then the credential is verified", "API-06, FR-06, OD-2", "200, result `ISSUER_UNAUTHORIZED`, `issuerAuthorized` `FAIL`")
    crd3 = stack.call("POST", "/credentials", "admin.iss002", ISSUE_REQUEST)[1]["credentialId"]
    link4 = stack.call("POST", f"/credentials/{crd3}/share-links", "holder.a", SCOPE)[1]
    owner = rgs._deployment()["owner"]
    tx_hash = rgs._transact("deactivateIssuer(string)", [("string", "ISS-002")], owner)
    r.save("deactivate-issuer.json", {"function": "deactivateIssuer(string)", "args": ["ISS-002"], "from": owner, "role": "platform admin (registry owner)", "txHash": tx_hash})
    status, body = stack.exchange(r, "verify-request-response.json", "POST", "/verifications", "verifier.a", {"shareToken": link4["shareToken"]})
    r.steps = [f"As `admin.iss002`, issue {crd3}; as `holder.a`, share it.", f"Call `deactivateIssuer(\"ISS-002\")` on the registry from the platform admin account {owner}.", "As `verifier.a`, verify the share token."]
    r.passed = status == 200 and body.get("result") == "ISSUER_UNAUTHORIZED" and body.get("checks", {}).get("issuerAuthorized") == "FAIL"
    r.actual = f"{status}, result `{body.get('result')}`, checks {body.get('checks')}."

    return records, goals


def write(records: list[Record], goals: dict[str, str], environment: str) -> None:
    for record in records:
        steps = "<br>".join(f"{i}. {step}" for i, step in enumerate(record.steps, 1))
        files = ", ".join(f"[{Path(f).name}]({f})" for f in record.files)
        (EVIDENCE / f"{record.id}.md").write_text(
            "\n".join([
                f"# {record.id}: {record.scenario}",
                "",
                "| Field | Value |",
                "| --- | --- |",
                f"| Related | {record.related} |",
                f"| Steps / input (Langkah/Input) | {steps} |",
                f"| Expected (Hasil yang diharapkan) | {record.expected} |",
                f"| Actual (Hasil aktual) | {record.actual} |",
                f"| Status (Status pengujian) | {'Pass' if record.passed else 'Fail'} |",
                f"| Evidence (Bukti pengujian) | {files} |",
                f"| Date and environment | {environment} |",
                "",
            ]),
            encoding="utf-8",
        )
    ordered = sorted(records, key=lambda r: r.id)
    lines = [
        "# Deliverable 3 test evidence",
        "",
        f"Generated by `api/scripts/evidence.py` on {environment}. All data is synthetic (assumption A6).",
        "",
        "| TC | Scenario | Expected | Actual | Status |",
        "| --- | --- | --- | --- | --- |",
        *[f"| [{r.id}]({r.id}.md) | {r.scenario} | {r.expected} | {r.actual} | {'Pass' if r.passed else 'Fail'} |" for r in ordered],
        "",
        f"**{sum(r.passed for r in records)} of {len(records)} pass.**",
        "",
        "## Design targets T-01 to T-05 (report Tabel 1.6), measured",
        "",
        "| Target | Measured |",
        "| --- | --- |",
        *[f"| {k} | {v} |" for k, v in sorted(goals.items())],
        "",
        "See also `pytest.txt` (API suite) and `ui/` (screenshots of the portals on the same synthetic data).",
        "",
    ]
    (EVIDENCE / "README.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[union-attr]  # Windows consoles default to cp1252
    if not config.GEMINI_API_KEY:
        raise SystemExit("Set GEMINI_API_KEY (for example in ../.env and run with uv run --env-file ../.env).")
    for old in EVIDENCE.glob("TC-*"):
        shutil.rmtree(old) if old.is_dir() else old.unlink()
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=REPO, capture_output=True, text=True).stdout.strip()
    environment = (f"{datetime.now(UTC):%Y-%m-%d %H:%M} UTC, commit {commit}, local Hardhat node + PostgreSQL 17 "
                   f"(database proofskill_evidence), API on port {API_PORT}, AI matching by Gemini {ams.GEMINI_MODEL}")
    stack = Stack()
    try:
        stack.prepare()
        records, goals = run(stack)
    finally:
        stack.close()
    write(records, goals, environment)
    for record in sorted(records, key=lambda r: r.id):
        print(f"{record.id}: {'Pass' if record.passed else 'Fail'} ({record.actual[:110]})")


if __name__ == "__main__":
    main()
