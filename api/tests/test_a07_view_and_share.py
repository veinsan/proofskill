"""A-07 completion criteria: F-03 credential view and scoped share links (API-03, API-04, API-05)."""

from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from app import config, db
from tests.conftest import issue, login, share
from tests.test_a04_auth_rbac import assert_error

Conn = db.psycopg.Connection[db.DictRow]
LINK_BODY = {"scope": ["program.title", "completedAt", "skills"], "expiresInHours": 72}


# --- API-03 -----------------------------------------------------------------------------


def test_api03_holder_reads_the_full_view_with_share_links(client: TestClient) -> None:
    issued = issue(client)
    link = share(client, "CRD-0001")
    body = client.get("/api/v1/credentials/CRD-0001", headers=login(client, "holder.a")).json()
    assert body["credentialId"] == "CRD-0001"
    assert body["issuer"] == {"issuerId": "ISS-001", "name": "Unit Pelatihan Contoh"}
    assert body["holderDisplayName"] == "Peserta Contoh A"
    assert body["program"]["completedAt"] == "2026-10-20"
    assert [s["skillId"] for s in body["skills"]] == ["SK-014", "SK-021", "SK-033"]
    assert body["skills"][0]["label"] == "OWASP Top 10"
    assert (body["status"], body["commitment"], body["txHash"]) == ("active", issued["commitment"], issued["txHash"])
    assert body["revokedAt"] is None
    assert [(l["linkId"], l["url"]) for l in body["shareLinks"]] == [(link["linkId"], link["url"])]


def test_api03_original_issuer_reads_it_without_share_links(client: TestClient) -> None:
    issue(client)
    share(client, "CRD-0001")
    body = client.get("/api/v1/credentials/CRD-0001", headers=login(client, "admin.iss001")).json()
    assert body["credentialId"] == "CRD-0001"
    assert body["shareLinks"] is None


@pytest.mark.parametrize("username", ["holder.b", "admin.iss002", "verifier.a", "platform.admin", "admin.unregistered"])
def test_api03_anyone_else_gets_403_not_credential_owner(client: TestClient, username: str) -> None:
    issue(client)
    response = client.get("/api/v1/credentials/CRD-0001", headers=login(client, username))
    assert_error(response, 403, "NOT_CREDENTIAL_OWNER")


def test_api03_unknown_credential_gets_404(client: TestClient) -> None:
    assert_error(client.get("/api/v1/credentials/CRD-9999", headers=login(client, "holder.a")), 404, "CREDENTIAL_NOT_FOUND")


def test_api03_without_token_gets_401(client: TestClient) -> None:
    issue(client)
    assert_error(client.get("/api/v1/credentials/CRD-0001"), 401, "UNAUTHENTICATED")


# --- API-04 -----------------------------------------------------------------------------


def test_api04_holder_creates_a_link_whose_scope_and_expiry_live_on_the_server(client: TestClient, conn: Conn) -> None:
    issue(client)
    before = datetime.now(UTC)
    link = share(client, "CRD-0001", ["skills", "program.title", "skills"], hours=72)

    assert link["linkId"] == "SHL-0001"
    token = str(link["shareToken"])
    assert token.startswith("sk_") and len(token) == 35
    assert link["url"] == f"{config.WEB_BASE_URL}/v/{token}"  # the verifier route (report 9.3)
    assert link["scope"] == ["skills", "program.title"]
    expires = datetime.fromisoformat(str(link["expiresAt"]))
    assert timedelta(hours=71, minutes=59) < expires - before < timedelta(hours=72, minutes=1)

    stored = conn.execute("SELECT share_token, scope, expires_at FROM share_links").fetchone()
    assert stored == {"share_token": token, "scope": ["skills", "program.title"], "expires_at": expires}
    audit = conn.execute("SELECT operation, object_id FROM audit_events WHERE operation = 'createShareLink'").fetchone()
    assert audit == {"operation": "createShareLink", "object_id": "SHL-0001"}


@pytest.mark.parametrize("username", ["holder.b", "admin.iss001", "verifier.a"])
def test_api04_non_owner_gets_403_not_credential_owner(client: TestClient, username: str) -> None:
    issue(client)
    response = client.post("/api/v1/credentials/CRD-0001/share-links", json=LINK_BODY, headers=login(client, username))
    assert_error(response, 403, "NOT_CREDENTIAL_OWNER")


def test_api04_unknown_credential_gets_404(client: TestClient) -> None:
    response = client.post("/api/v1/credentials/CRD-9999/share-links", json=LINK_BODY, headers=login(client, "holder.a"))
    assert_error(response, 404, "CREDENTIAL_NOT_FOUND")


@pytest.mark.parametrize(
    "body",
    [
        {"scope": ["nik"], "expiresInHours": 72},
        {"scope": ["skills", "holderRef"], "expiresInHours": 72},
        {"scope": [], "expiresInHours": 72},
        {"scope": ["skills"], "expiresInHours": 0},
        {"scope": ["skills"], "expiresInHours": 721},
    ],
)
def test_api04_scope_or_expiry_outside_od4_gets_422_invalid_scope(client: TestClient, conn: Conn, body: dict[str, object]) -> None:
    issue(client)
    response = client.post("/api/v1/credentials/CRD-0001/share-links", json=body, headers=login(client, "holder.a"))
    assert_error(response, 422, "INVALID_SCOPE")
    assert conn.execute("SELECT count(*) AS n FROM share_links").fetchone() == {"n": 0}


def test_api04_wrong_types_get_400_malformed_request(client: TestClient) -> None:
    issue(client)
    response = client.post(
        "/api/v1/credentials/CRD-0001/share-links", json={"scope": "skills", "expiresInHours": "soon"}, headers=login(client, "holder.a")
    )
    assert_error(response, 400, "MALFORMED_REQUEST")


# --- API-05 -----------------------------------------------------------------------------


def test_api05_holder_revokes_a_link_and_repeating_it_is_harmless(client: TestClient, conn: Conn) -> None:
    issue(client)
    share(client, "CRD-0001")
    headers = login(client, "holder.a")
    assert client.delete("/api/v1/share-links/SHL-0001", headers=headers).status_code == 204
    first = conn.execute("SELECT revoked_at FROM share_links").fetchone()
    assert first is not None and first["revoked_at"] is not None

    assert client.delete("/api/v1/share-links/SHL-0001", headers=headers).status_code == 204
    assert conn.execute("SELECT revoked_at FROM share_links").fetchone() == first
    view = client.get("/api/v1/credentials/CRD-0001", headers=headers).json()
    assert view["shareLinks"][0]["revokedAt"] is not None


@pytest.mark.parametrize("username", ["holder.b", "admin.iss001", "verifier.a"])
def test_api05_non_owner_gets_403(client: TestClient, username: str) -> None:
    issue(client)
    share(client, "CRD-0001")
    assert_error(client.delete("/api/v1/share-links/SHL-0001", headers=login(client, username)), 403, "NOT_CREDENTIAL_OWNER")


def test_api05_unknown_link_gets_404(client: TestClient) -> None:
    assert_error(client.delete("/api/v1/share-links/SHL-9999", headers=login(client, "holder.a")), 404, "SHARE_LINK_NOT_FOUND")
