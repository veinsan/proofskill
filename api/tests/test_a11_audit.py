"""A-11 completion criteria: F-07 audit trail through API-10 (TC-13, FR-10, NFR-07)."""

from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from app import db
from tests.conftest import ISSUE_REQUEST, issue, login, share
from tests.test_a04_auth_rbac import assert_error
from tests.test_a08_verification import verify
from tests.test_a09_revocation import REASON, revoke
from tests.test_a10_matching import SECURITY, fake_ai, match  # noqa: F401  (fixture)

Conn = db.psycopg.Connection[db.DictRow]


def run_every_operation(client: TestClient) -> dict[str, str]:
    """Issue, share, verify, match, revoke a link, and revoke the credential (ISS-001)."""
    issue(client)
    link = share(client, "CRD-0001")
    verification = verify(client, link["shareToken"]).json()
    assert match(client, verification["verificationId"]).status_code == 200
    assert client.delete(f"/api/v1/share-links/{link['linkId']}", headers=login(client, "holder.a")).status_code == 204
    assert revoke(client).status_code == 200
    return {"token": str(link["shareToken"]), "verification": verification["verificationId"]}


def audit(client: TestClient, username: str = "admin.iss001", **params: object):  # type: ignore[no-untyped-def]
    return client.get("/api/v1/audit-logs", params=params, headers=login(client, username))


def test_tc13_every_key_operation_is_logged_without_sensitive_payload(client: TestClient, conn: Conn, fake_ai: None) -> None:
    secrets = run_every_operation(client)
    response = audit(client)
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 6
    assert [item["operation"] for item in body["items"]] == [  # newest first
        "revokeCredential", "revokeShareLink", "matchSkills", "verifyCredential", "createShareLink", "issueCredential",
    ]
    assert [item["objectId"] for item in body["items"]] == ["CRD-0001", "SHL-0001", "MAT-0001", "VER-0001", "SHL-0001", "CRD-0001"]
    assert {item["actorRole"] for item in body["items"]} == {"issuer_admin", "holder", "verifier"}
    assert body["items"][3]["outcome"] == "VALID"
    for item in body["items"]:
        assert set(item) == {"time", "actorRole", "operation", "objectId", "outcome"}

    # NFR-07: no payload anywhere in the trail, neither in the API nor in the table itself.
    sensitive = [
        ISSUE_REQUEST["holderDisplayName"], ISSUE_REQUEST["holderRef"], ISSUE_REQUEST["program"]["title"],  # type: ignore[index]
        ISSUE_REQUEST["program"]["criteria"], REASON["reason"], secrets["token"], SECURITY["description"], "verifier.a",  # type: ignore[index]
    ]
    rows = str(conn.execute("SELECT * FROM audit_events").fetchall())
    for value in sensitive:
        assert str(value) not in str(body) and str(value) not in rows
    columns = [r["column_name"] for r in conn.execute(
        "SELECT column_name FROM information_schema.columns WHERE table_name = 'audit_events' ORDER BY ordinal_position"
    )]
    assert columns == ["event_id", "time", "actor_role", "operation", "object_id", "outcome"]


def test_api10_filters_by_operation_and_time(client: TestClient, fake_ai: None) -> None:
    run_every_operation(client)
    only = audit(client, operation="verifyCredential").json()
    assert [(i["operation"], i["objectId"]) for i in only["items"]] == [("verifyCredential", "VER-0001")]

    now = datetime.now(UTC)
    assert audit(client, **{"from": (now - timedelta(minutes=5)).isoformat()}).json()["total"] == 6
    assert audit(client, **{"from": (now + timedelta(minutes=5)).isoformat()}).json()["total"] == 0
    assert audit(client, to=(now - timedelta(minutes=5)).isoformat()).json()["total"] == 0

    page = audit(client, limit=2, offset=1).json()
    assert [i["operation"] for i in page["items"]] == ["revokeShareLink", "matchSkills"] and page["total"] == 6


def test_api10_an_issuer_sees_only_events_about_its_own_credentials(client: TestClient, fake_ai: None) -> None:
    run_every_operation(client)
    assert audit(client, "admin.iss002").json() == {"items": [], "total": 0}
    issue(client, "admin.iss002")
    other = audit(client, "admin.iss002").json()
    assert [(i["operation"], i["objectId"]) for i in other["items"]] == [("issueCredential", "CRD-0002")]


@pytest.mark.parametrize("username", ["holder.a", "verifier.a", "platform.admin"])
def test_api10_other_roles_get_403_forbidden_role(client: TestClient, username: str) -> None:
    assert_error(audit(client, username), 403, "FORBIDDEN_ROLE")


def test_api10_issuer_admin_without_an_issuer_gets_403(client: TestClient) -> None:
    assert_error(audit(client, "admin.unregistered"), 403, "ISSUER_NOT_AUTHORIZED")


@pytest.mark.parametrize("params", [{"operation": "deleteEverything"}, {"from": "yesterday"}, {"limit": 0}, {"limit": 201}])
def test_api10_bad_filters_get_400(client: TestClient, params: dict[str, object]) -> None:
    assert_error(audit(client, **params), 400, "MALFORMED_REQUEST")


def test_api10_without_token_gets_401(client: TestClient) -> None:
    assert_error(client.get("/api/v1/audit-logs"), 401, "UNAUTHENTICATED")
