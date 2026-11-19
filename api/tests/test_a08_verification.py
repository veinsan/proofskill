"""A-08 completion criteria: F-04 verification through API-06 (TC-04, TC-05, TC-07, TC-11,
TC-12, TC-16; FR-06, FR-12, NFR-04, NFR-05)."""

import statistics
import time

import pytest
from fastapi.testclient import TestClient

from app import config, db, rgs, vrs
from tests.conftest import ISSUE_REQUEST, issue, login, share
from tests.test_a04_auth_rbac import assert_error

Conn = db.psycopg.Connection[db.DictRow]
ALL_FIELDS = ["holderDisplayName", "program.title", "completedAt", "program.criteria", "skills"]


def verify(client: TestClient, token: object, username: str = "verifier.a"):  # type: ignore[no-untyped-def]
    return client.post("/api/v1/verifications", json={"shareToken": token}, headers=login(client, username))


def issued_and_shared(client: TestClient, scope: list[str] | None = None) -> tuple[dict[str, object], str]:
    issued = issue(client)
    return issued, str(share(client, "CRD-0001", scope)["shareToken"])


def test_tc04_intact_credential_verifies_valid_without_any_admin(client: TestClient, conn: Conn) -> None:
    issued, token = issued_and_shared(client)
    response = verify(client, token)
    assert response.status_code == 200
    body = response.json()
    assert body["verificationId"] == "VER-0001"
    assert body["result"] == "VALID"
    assert body["checks"] == {"integrity": "PASS", "issuerAuthorized": "PASS", "status": "ACTIVE"}
    assert body["chainRef"] == {"txHash": issued["txHash"]}
    assert "reason" not in body and body["verifiedAt"]
    # Only the scope the holder chose: program.title, completedAt, skills (report API-04/06 example).
    assert body["credential"] == {
        "credentialId": "CRD-0001",
        "issuer": {"issuerId": "ISS-001", "name": "Unit Pelatihan Contoh"},
        "program": {"title": ISSUE_REQUEST["program"]["title"], "completedAt": "2026-10-20"},  # type: ignore[index]
        "skills": [
            {"skillId": "SK-014", "label": "OWASP Top 10"},
            {"skillId": "SK-021", "label": "Web Security Testing"},
            {"skillId": "SK-033", "label": "Secure Coding"},
        ],
    }
    # Stored for API-07 ownership checks, and audited; no admin step anywhere on this path (T-02).
    stored = conn.execute("SELECT verifier, result FROM verifications").fetchone()
    assert stored == {"verifier": "verifier.a", "result": "VALID"}
    audit = conn.execute("SELECT actor_role, object_id, outcome FROM audit_events WHERE operation = 'verifyCredential'").fetchone()
    assert audit == {"actor_role": "verifier", "object_id": "VER-0001", "outcome": "VALID"}


def test_api06_returns_only_the_fields_in_scope(client: TestClient) -> None:
    _, token = issued_and_shared(client, ["holderDisplayName"])
    credential = verify(client, token).json()["credential"]
    assert credential == {
        "credentialId": "CRD-0001",
        "issuer": {"issuerId": "ISS-001", "name": "Unit Pelatihan Contoh"},
        "holderDisplayName": "Peserta Contoh A",
    }
    share_all = share(client, "CRD-0001", ALL_FIELDS)
    full = verify(client, share_all["shareToken"]).json()["credential"]
    assert full["program"]["criteria"] == ISSUE_REQUEST["program"]["criteria"]  # type: ignore[index]


@pytest.mark.parametrize(
    "tamper",
    [
        "UPDATE credentials SET program_title = 'Pelatihan Lanjutan' WHERE credential_id = 'CRD-0001'",
        "UPDATE credentials SET completed_at = '2025-01-01' WHERE credential_id = 'CRD-0001'",
        "INSERT INTO credential_skills VALUES ('CRD-0001', 'SK-040')",
        "UPDATE credentials SET holder_ref = 'HLD-2026-0008' WHERE credential_id = 'CRD-0001'",
    ],
)
def test_tc05_content_changed_in_the_database_verifies_tampered_without_data(client: TestClient, conn: Conn, tamper: str) -> None:
    _, token = issued_and_shared(client)
    conn.execute(tamper)  # type: ignore[arg-type]
    conn.commit()
    body = verify(client, token).json()
    assert body["result"] == "TAMPERED"
    assert body["checks"]["integrity"] == "FAIL"
    assert "credential" not in body  # FR-12: no credential data
    assert body["chainRef"]["txHash"]


def test_api06_display_name_is_not_hashed_so_changing_it_stays_valid(client: TestClient, conn: Conn) -> None:
    _, token = issued_and_shared(client)
    conn.execute("UPDATE credentials SET holder_display_name = 'Nama Baru' WHERE credential_id = 'CRD-0001'")
    conn.commit()
    assert verify(client, token).json()["result"] == "VALID"


def test_tc07_expired_or_revoked_link_returns_410(client: TestClient, conn: Conn) -> None:
    _, token = issued_and_shared(client)
    conn.execute("UPDATE share_links SET expires_at = now() - interval '1 second'")
    conn.commit()
    assert_error(verify(client, token), 410, "SHARE_LINK_EXPIRED")

    second = share(client, "CRD-0001")
    assert client.delete(f"/api/v1/share-links/{second['linkId']}", headers=login(client, "holder.a")).status_code == 204
    assert_error(verify(client, second["shareToken"]), 410, "SHARE_LINK_EXPIRED")


def test_tc11_on_chain_data_holds_no_personal_data(client: TestClient) -> None:
    issued, _ = issued_and_shared(client)
    personal = [
        ISSUE_REQUEST["holderDisplayName"],
        ISSUE_REQUEST["holderRef"],
        ISSUE_REQUEST["program"]["title"],  # type: ignore[index]
        ISSUE_REQUEST["program"]["criteria"],  # type: ignore[index]
    ]
    tx = rgs._rpc("eth_getTransactionByHash", [issued["txHash"]])
    raw_record = rgs._call("getRecord(string)", [("string", "CRD-0001")])
    for blob in (bytes.fromhex(tx["input"].removeprefix("0x")), raw_record):
        for value in personal:
            assert str(value).encode() not in blob
    # What the chain does hold: the credential ID, commitment, issuer, status, and time.
    record = rgs.get_record("CRD-0001")
    assert (record.commitment, record.issuer_id, record.status) == (issued["commitment"], "ISS-001", "active")


def test_tc12_verification_takes_less_than_5_seconds(client: TestClient) -> None:
    _, token = issued_and_shared(client)
    headers = login(client, "verifier.a")
    durations = []
    for _ in range(10):
        start = time.perf_counter()
        response = client.post("/api/v1/verifications", json={"shareToken": token}, headers=headers)
        durations.append(time.perf_counter() - start)
        assert response.json()["result"] == "VALID"
    print(f"TC-12 verification seconds: median {statistics.median(durations):.3f}, max {max(durations):.3f}")
    assert max(durations) < 5


def test_tc16_deactivated_issuer_verifies_issuer_unauthorized(client: TestClient) -> None:
    _, token = issued_and_shared(client)
    rgs._transact("deactivateIssuer(string)", [("string", "ISS-001")], rgs._deployment()["owner"])
    body = verify(client, token).json()
    assert body["result"] == "ISSUER_UNAUTHORIZED"
    assert body["checks"] == {"integrity": "PASS", "issuerAuthorized": "FAIL", "status": "ACTIVE"}
    assert body["credential"]["credentialId"] == "CRD-0001"


def test_api06_unknown_link_returns_404(client: TestClient) -> None:
    assert_error(verify(client, "sk_unknown"), 404, "SHARE_LINK_NOT_FOUND")


@pytest.mark.parametrize("username", ["holder.a", "admin.iss001", "platform.admin"])
def test_api06_other_roles_get_403_forbidden_role(client: TestClient, username: str) -> None:
    _, token = issued_and_shared(client)
    assert_error(verify(client, token, username), 403, "FORBIDDEN_ROLE")


def test_api06_without_token_returns_401(client: TestClient) -> None:
    assert_error(client.post("/api/v1/verifications", json={"shareToken": "sk_x"}), 401, "UNAUTHENTICATED")


def test_api06_registry_down_returns_503_and_stores_nothing(
    client: TestClient, conn: Conn, monkeypatch: pytest.MonkeyPatch
) -> None:
    _, token = issued_and_shared(client)
    headers = login(client, "verifier.a")
    monkeypatch.setattr(config, "CHAIN_RPC_URL", "http://127.0.0.1:1")
    response = client.post("/api/v1/verifications", json={"shareToken": token}, headers=headers)
    assert_error(response, 503, "REGISTRY_UNAVAILABLE")
    assert conn.execute("SELECT count(*) AS n FROM verifications").fetchone() == {"n": 0}


@pytest.mark.parametrize(
    ("integrity", "issuer", "status", "expected"),
    [
        ("PASS", "PASS", "ACTIVE", "VALID"),
        ("FAIL", "FAIL", "REVOKED", "TAMPERED"),
        ("PASS", "FAIL", "REVOKED", "REVOKED"),
        ("PASS", "FAIL", "ACTIVE", "ISSUER_UNAUTHORIZED"),
    ],
)
def test_decide_reports_the_main_cause(integrity: str, issuer: str, status: str, expected: str) -> None:
    checks = vrs.Checks(integrity=integrity, issuer_authorized=issuer, status=status)  # type: ignore[arg-type]
    assert vrs.decide(checks) == expected
