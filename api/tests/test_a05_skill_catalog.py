"""A-05 completion criteria: API-08 returns {items: [{skillId, label, aliases}], total}."""

import pytest
from fastapi.testclient import TestClient

from app import seed
from tests.conftest import login
from tests.test_a04_auth_rbac import assert_error

ALL_IDS = sorted(skill_id for skill_id, _, _ in seed.SKILLS)


@pytest.mark.parametrize("username", ["platform.admin", "admin.iss001", "holder.a", "verifier.a"])
def test_api08_every_role_reads_the_whole_catalog(client: TestClient, username: str) -> None:
    response = client.get("/api/v1/skills", headers=login(client, username))
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 15
    assert [item["skillId"] for item in body["items"]] == ALL_IDS
    assert body["items"][1] == {
        "skillId": "SK-014",
        "label": "OWASP Top 10",
        "aliases": ["kerentanan aplikasi web", "web application vulnerabilities"],
    }


@pytest.mark.parametrize(
    ("query", "expected"),
    [("owasp", ["SK-014"]), ("VISUALISASI", ["SK-042"]), ("python", ["SK-040"]), ("%", []), ("_", [])],
)
def test_api08_query_matches_label_or_alias_case_insensitively(
    client: TestClient, query: str, expected: list[str]
) -> None:
    body = client.get("/api/v1/skills", params={"query": query}, headers=login(client, "verifier.a")).json()
    assert [item["skillId"] for item in body["items"]] == expected
    assert body["total"] == len(expected)


def test_api08_limit_and_offset_page_through_the_catalog(client: TestClient) -> None:
    params = {"limit": 5, "offset": 10}
    body = client.get("/api/v1/skills", params=params, headers=login(client, "admin.iss001")).json()
    assert [item["skillId"] for item in body["items"]] == ALL_IDS[10:15]
    assert body["total"] == 15


@pytest.mark.parametrize("params", [{"limit": 0}, {"limit": 101}, {"offset": -1}])
def test_api08_out_of_range_paging_returns_400_malformed_request(client: TestClient, params: dict[str, int]) -> None:
    response = client.get("/api/v1/skills", params=params, headers=login(client, "holder.a"))
    assert_error(response, 400, "MALFORMED_REQUEST")


def test_api08_without_token_returns_401_unauthenticated(client: TestClient) -> None:
    assert_error(client.get("/api/v1/skills"), 401, "UNAUTHENTICATED")
