"""A-09 completion criteria: F-05 revocation through API-09 (TC-06, TC-14, FR-07, T-05)."""

import pytest
from fastapi.testclient import TestClient

from app import config, db, rgs, seed
from tests.conftest import issue, login, share
from tests.test_a04_auth_rbac import assert_error
from tests.test_a08_verification import verify

Conn = db.psycopg.Connection[db.DictRow]
REASON = {"reason": "Data kelulusan keliru"}


def revoke(client: TestClient, username: str = "admin.iss001", credential_id: str = "CRD-0001"):  # type: ignore[no-untyped-def]
    return client.post(f"/api/v1/credentials/{credential_id}/revocations", json=REASON, headers=login(client, username))


def test_api09_original_issuer_revokes_and_the_next_verification_reads_revoked(client: TestClient, conn: Conn) -> None:
    issue(client)
    token = share(client, "CRD-0001")["shareToken"]
    response = revoke(client)
    assert response.status_code == 200, response.text
    body = response.json()
    assert (body["credentialId"], body["status"], body["reason"]) == ("CRD-0001", "revoked", REASON["reason"])
    assert body["txHash"].startswith("0x") and body["revokedAt"]

    assert rgs.get_record("CRD-0001").status == "revoked"
    result = verify(client, token).json()
    assert result["result"] == "REVOKED"
    assert result["checks"] == {"integrity": "PASS", "issuerAuthorized": "PASS", "status": "REVOKED"}
    assert result["reason"] == REASON["reason"]

    audit = conn.execute("SELECT actor_role, object_id FROM audit_events WHERE operation = 'revokeCredential'").fetchone()
    assert audit == {"actor_role": "issuer_admin", "object_id": "CRD-0001"}
    note = conn.execute("SELECT subject, body FROM notifications WHERE subject = 'Credential revoked'").fetchone()
    assert note is not None and REASON["reason"] in note["body"]
    view = client.get("/api/v1/credentials/CRD-0001", headers=login(client, "holder.a")).json()
    assert (view["status"], view["revocationReason"]) == ("revoked", REASON["reason"])


def test_tc06_revoked_stays_revoked_after_the_database_status_is_set_back_to_active(client: TestClient, conn: Conn) -> None:
    issue(client)
    token = share(client, "CRD-0001")["shareToken"]
    assert revoke(client).status_code == 200
    conn.execute("UPDATE credentials SET status = 'active', revoked_at = NULL WHERE credential_id = 'CRD-0001'")
    conn.commit()

    result = verify(client, token).json()
    assert result["result"] == "REVOKED"
    assert result["checks"]["status"] == "REVOKED"
    assert result["reason"] == REASON["reason"]
    # Trying to revoke again is refused by the chain, the source of truth, despite the row.
    assert_error(revoke(client), 409, "ALREADY_REVOKED")


def test_tc14_another_issuer_calling_the_contract_directly_is_reverted(client: TestClient) -> None:
    issue(client)
    iss002_account = seed.ISSUERS[1][3]
    with pytest.raises(rgs.RegistryError, match="NotOriginalIssuer"):
        rgs.revoke_credential("CRD-0001", iss002_account)
    assert rgs.get_record("CRD-0001").status == "active"


def test_tc14_another_issuer_through_the_api_gets_403(client: TestClient) -> None:
    issue(client)
    assert_error(revoke(client, "admin.iss002"), 403, "ISSUER_NOT_AUTHORIZED")
    assert rgs.get_record("CRD-0001").status == "active"


@pytest.mark.parametrize("username", ["admin.unregistered", "holder.a", "verifier.a", "platform.admin"])
def test_api09_accounts_that_are_not_issuers_get_403(client: TestClient, username: str) -> None:
    issue(client)
    assert_error(revoke(client, username), 403, "ISSUER_NOT_AUTHORIZED")


def test_api09_second_revocation_gets_409(client: TestClient) -> None:
    issue(client)
    assert revoke(client).status_code == 200
    assert_error(revoke(client), 409, "ALREADY_REVOKED")


def test_api09_unknown_credential_gets_404(client: TestClient) -> None:
    assert_error(revoke(client, credential_id="CRD-9999"), 404, "CREDENTIAL_NOT_FOUND")


def test_api09_registry_down_returns_503_and_the_status_does_not_change(
    client: TestClient, conn: Conn, monkeypatch: pytest.MonkeyPatch
) -> None:
    issue(client)
    headers = login(client, "admin.iss001")
    with monkeypatch.context() as down:  # undo only this patch, not the autouse fake Supabase
        down.setattr(config, "CHAIN_RPC_URL", "http://127.0.0.1:1")
        response = client.post("/api/v1/credentials/CRD-0001/revocations", json=REASON, headers=headers)
        assert_error(response, 503, "REGISTRY_UNAVAILABLE")
    assert conn.execute("SELECT status, revocation_reason FROM credentials").fetchone() == {"status": "active", "revocation_reason": None}
    assert rgs.get_record("CRD-0001").status == "active"


@pytest.mark.parametrize("body", [{}, {"reason": ""}, {"reason": "x" * 201}])
def test_api09_missing_or_oversized_reason_gets_400(client: TestClient, body: dict[str, str]) -> None:
    issue(client)
    response = client.post("/api/v1/credentials/CRD-0001/revocations", json=body, headers=login(client, "admin.iss001"))
    assert_error(response, 400, "MALFORMED_REQUEST")
