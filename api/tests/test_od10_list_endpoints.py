"""OD-10: owner-scoped credential lists for the portals (API-12 holder, API-13 issuer)."""

import pytest
from fastapi.testclient import TestClient

from tests.conftest import issue, login
from tests.test_a04_auth_rbac import assert_error
from tests.test_a09_revocation import revoke


def listing(client: TestClient, path: str, username: str, **params: object):  # type: ignore[no-untyped-def]
    return client.get(f"/api/v1/{path}", params=params, headers=login(client, username))


def test_api12_holder_lists_only_their_own_credentials_newest_first(client: TestClient) -> None:
    issue(client)  # CRD-0001 to holder.a by ISS-001
    issue(client, "admin.iss002", holderRef="HLD-2026-0008", holderDisplayName="Peserta Contoh B")  # CRD-0002 to holder.b
    issue(client, "admin.iss002")  # CRD-0003 to holder.a by ISS-002
    assert revoke(client).status_code == 200

    body = listing(client, "holders/me/credentials", "holder.a").json()
    assert body["total"] == 2
    assert [i["credentialId"] for i in body["items"]] == ["CRD-0003", "CRD-0001"]
    first = body["items"][1]
    assert first["issuer"] == {"issuerId": "ISS-001", "name": "Unit Pelatihan Contoh"}
    assert (first["status"], first["program"]["completedAt"]) == ("revoked", "2026-10-20")
    assert first["revokedAt"] is not None

    other = listing(client, "holders/me/credentials", "holder.b").json()
    assert [i["credentialId"] for i in other["items"]] == ["CRD-0002"]


def test_api13_issuer_lists_only_what_its_issuer_issued(client: TestClient) -> None:
    issue(client)
    issue(client, "admin.iss002")
    issue(client, holderRef="HLD-2026-0008", holderDisplayName="Peserta Contoh B")

    body = listing(client, "issuers/me/credentials", "admin.iss001").json()
    assert body["total"] == 2
    assert [(i["credentialId"], i["holderDisplayName"]) for i in body["items"]] == [
        ("CRD-0003", "Peserta Contoh B"),
        ("CRD-0001", "Peserta Contoh A"),
    ]
    assert [i["credentialId"] for i in listing(client, "issuers/me/credentials", "admin.iss002").json()["items"]] == ["CRD-0002"]

    page = listing(client, "issuers/me/credentials", "admin.iss001", limit=1, offset=1).json()
    assert [i["credentialId"] for i in page["items"]] == ["CRD-0001"] and page["total"] == 2


def test_lists_accept_no_search_or_filter_parameters(client: TestClient) -> None:
    issue(client)
    response = listing(client, "holders/me/credentials", "holder.a", holderRef="HLD-2026-0008", query="x")
    assert [i["credentialId"] for i in response.json()["items"]] == ["CRD-0001"]  # extra parameters are ignored


@pytest.mark.parametrize(
    ("path", "username"),
    [
        ("holders/me/credentials", "admin.iss001"),
        ("holders/me/credentials", "verifier.a"),
        ("issuers/me/credentials", "holder.a"),
        ("issuers/me/credentials", "verifier.a"),
        ("issuers/me/credentials", "platform.admin"),
    ],
)
def test_other_roles_get_403_forbidden_role(client: TestClient, path: str, username: str) -> None:
    assert_error(listing(client, path, username), 403, "FORBIDDEN_ROLE")


def test_api13_issuer_admin_without_an_issuer_gets_403(client: TestClient) -> None:
    assert_error(listing(client, "issuers/me/credentials", "admin.unregistered"), 403, "ISSUER_NOT_AUTHORIZED")


@pytest.mark.parametrize("path", ["holders/me/credentials", "issuers/me/credentials"])
def test_lists_need_a_token(client: TestClient, path: str) -> None:
    assert_error(client.get(f"/api/v1/{path}"), 401, "UNAUTHENTICATED")
