"""A-06 completion criteria: F-02 issuance through API-02 (TC-01, TC-02, TC-03, FR-02..FR-04)."""

from datetime import date

import pytest
from fastapi.testclient import TestClient

from app import cis, config, db, rgs
from tests.conftest import ISSUE_REQUEST, issue, login
from tests.test_a04_auth_rbac import assert_error

Conn = db.psycopg.Connection[db.DictRow]


def count(conn: Conn, table: str) -> int:
    row = conn.execute(f"SELECT count(*) AS n FROM {table}").fetchone()  # type: ignore[arg-type]
    return int(row["n"]) if row else 0


def test_tc01_registered_issuer_issues_a_valid_credential(client: TestClient, conn: Conn) -> None:
    body = issue(client)
    assert body["credentialId"] == "CRD-0001"
    assert body["issuerId"] == "ISS-001"
    assert body["status"] == "active"
    assert str(body["txHash"]).startswith("0x") and body["issuedAt"]

    # The commitment on the registry is the one the API computed from the stored rows (FR-04).
    stored = conn.execute("SELECT * FROM credentials WHERE credential_id = 'CRD-0001'").fetchone()
    assert stored is not None
    assert stored["commitment"] == body["commitment"] == cis.commitment_of(conn, stored)
    record = rgs.get_record("CRD-0001")
    assert (record.commitment, record.issuer_id, record.status, record.issuer_active) == (
        body["commitment"], "ISS-001", "active", True,
    )
    assert stored["tx_hash"] == body["txHash"]
    assert stored["holder_display_name"] == "Peserta Contoh A"  # off-chain only

    # T06: audit event and simulated email (OD-3).
    audit = conn.execute("SELECT actor_role, operation, object_id, outcome FROM audit_events").fetchall()
    assert audit == [{"actor_role": "issuer_admin", "operation": "issueCredential", "object_id": "CRD-0001", "outcome": "success"}]
    note = conn.execute("SELECT holder_ref, body FROM notifications").fetchone()
    assert note is not None and note["holder_ref"] == "HLD-2026-0007" and "CRD-0001" in note["body"]

    assert issue(client, "admin.iss002")["credentialId"] == "CRD-0002"


@pytest.mark.parametrize("username", ["admin.unregistered", "holder.a", "verifier.a", "platform.admin"])
def test_tc02_account_that_is_not_a_registered_issuer_gets_403(client: TestClient, conn: Conn, username: str) -> None:
    response = client.post("/api/v1/credentials", json=ISSUE_REQUEST, headers=login(client, username))
    assert_error(response, 403, "ISSUER_NOT_AUTHORIZED")
    assert count(conn, "credentials") == 0


def test_tc02_issuer_deactivated_on_the_registry_gets_403(client: TestClient, conn: Conn) -> None:
    deployment = rgs._deployment()
    rgs._transact("deactivateIssuer(string)", [("string", "ISS-001")], deployment["owner"])
    response = client.post("/api/v1/credentials", json=ISSUE_REQUEST, headers=login(client, "admin.iss001"))
    assert_error(response, 403, "ISSUER_NOT_AUTHORIZED")
    assert count(conn, "credentials") == 0


def test_tc03_skill_outside_the_catalog_gets_422(client: TestClient, conn: Conn) -> None:
    request = {**ISSUE_REQUEST, "skills": ["SK-014", "SK-999"]}
    response = client.post("/api/v1/credentials", json=request, headers=login(client, "admin.iss001"))
    assert_error(response, 422, "SKILL_NOT_IN_CATALOG")
    assert "SK-999" in response.json()["error"]["message"]
    assert count(conn, "credentials") == 0


def test_api02_registry_down_returns_503_and_issues_nothing(
    client: TestClient, conn: Conn, monkeypatch: pytest.MonkeyPatch
) -> None:
    headers = login(client, "admin.iss001")
    monkeypatch.setattr(config, "CHAIN_RPC_URL", "http://127.0.0.1:1")
    assert_error(client.post("/api/v1/credentials", json=ISSUE_REQUEST, headers=headers), 503, "REGISTRY_UNAVAILABLE")
    for table in ("credentials", "credential_skills", "audit_events", "notifications"):
        assert count(conn, table) == 0


@pytest.mark.parametrize(
    "change",
    [
        {"skills": []},
        {"skills": "SK-014"},
        {"holderRef": "7"},
        {"program": {"title": "x", "completedAt": "not-a-date", "criteria": "y"}},
        {"nik": "3201xxxxxxxxxxxx"},  # unknown fields are refused, so NIK cannot slip in (NFR-02)
        {"holderRef": "HLD-2026-9999"},  # well formed but unknown
    ],
)
def test_api02_malformed_request_returns_400(client: TestClient, change: dict[str, object]) -> None:
    response = client.post("/api/v1/credentials", json={**ISSUE_REQUEST, **change}, headers=login(client, "admin.iss001"))
    assert_error(response, 400, "MALFORMED_REQUEST")


def test_api02_without_token_returns_401(client: TestClient) -> None:
    assert_error(client.post("/api/v1/credentials", json=ISSUE_REQUEST), 401, "UNAUTHENTICATED")


def test_commitment_excludes_display_name_and_depends_on_every_hashed_field() -> None:
    nonce = bytes(32)
    base = ("CRD-0001", "ISS-001", "HLD-2026-0007", "Pelatihan", date(2026, 10, 20), "Lulus", ["SK-021", "SK-014"])
    reference = cis.compute_commitment(cis.canonical_payload(*base), nonce)
    # Skill order does not matter; the canonical form sorts them.
    assert cis.compute_commitment(cis.canonical_payload(*base[:6], ["SK-014", "SK-021"]), nonce) == reference
    for index, changed in enumerate(["CRD-0002", "ISS-002", "HLD-2026-0008", "Pelatihan 2", date(2026, 10, 21), "Gagal", ["SK-014"]]):
        fields = list(base)
        fields[index] = changed
        assert cis.compute_commitment(cis.canonical_payload(*fields), nonce) != reference  # type: ignore[arg-type]
    assert cis.compute_commitment(cis.canonical_payload(*base), bytes([1]) * 32) != reference
    assert b"Peserta" not in cis.canonical_payload(*base)
