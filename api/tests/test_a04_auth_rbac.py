"""A-04 completion criteria: F-01 authentication and RBAC (API-00, API-01, NFR-01, OD-1)."""

import jwt
import pytest
from fastapi.testclient import TestClient

from app import config, rgs, seed
from tests.conftest import login

NEW_ACCOUNT = "0x90F79bf6EB2c4f870365E785982E1f101E93b906"  # public Hardhat test account #3


def assert_error(response, status: int, code: str) -> None:  # type: ignore[no-untyped-def]
    assert response.status_code == status, response.text
    error = response.json()["error"]
    assert error["code"] == code
    assert error["message"] and error["requestId"].startswith("req_")


# --- API-00 -----------------------------------------------------------------------------


@pytest.mark.parametrize(("username", "role", "_issuer", "_holder"), seed.ACCOUNTS)
def test_api00_issues_a_token_carrying_the_account_role(
    client: TestClient, username: str, role: str, _issuer: str | None, _holder: str | None
) -> None:
    response = client.post("/api/v1/auth/token", json={"username": username, "password": seed.DEMO_PASSWORD})
    assert response.status_code == 200
    body = response.json()
    assert body["tokenType"] == "Bearer"
    assert body["expiresIn"] == 3600
    assert body["role"] == role
    claims = jwt.decode(body["accessToken"], config.JWT_SECRET, algorithms=["HS256"])
    assert (claims["sub"], claims["role"]) == (username, role)


@pytest.mark.parametrize("username", ["holder.a", "nobody"])
def test_api00_wrong_password_or_unknown_user_returns_401_invalid_credentials(client: TestClient, username: str) -> None:
    response = client.post("/api/v1/auth/token", json={"username": username, "password": "wrong"})
    assert_error(response, 401, "INVALID_CREDENTIALS")


def test_api00_malformed_body_returns_400_malformed_request(client: TestClient) -> None:
    assert_error(client.post("/api/v1/auth/token", json={"username": "holder.a"}), 400, "MALFORMED_REQUEST")


# --- API-01 -----------------------------------------------------------------------------

REGISTRATION = {"name": "Lab Contoh", "unitType": "Laboratorium", "registryAccount": NEW_ACCOUNT}


def test_api01_platform_admin_registers_an_issuer_in_the_database_and_on_chain(client: TestClient) -> None:
    response = client.post("/api/v1/issuers", json=REGISTRATION, headers=login(client, "platform.admin"))
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["issuerId"] == "ISS-003"
    assert body["registryAccount"] == NEW_ACCOUNT
    assert body["txHash"].startswith("0x") and body["registeredAt"]
    assert rgs.issuer_account("ISS-003") == NEW_ACCOUNT.lower()


def test_api01_already_registered_account_returns_409(client: TestClient) -> None:
    taken = {**REGISTRATION, "registryAccount": seed.ISSUERS[0][3]}
    response = client.post("/api/v1/issuers", json=taken, headers=login(client, "platform.admin"))
    assert_error(response, 409, "ISSUER_ALREADY_REGISTERED")


@pytest.mark.parametrize("username", ["admin.iss001", "holder.a", "verifier.a"])
def test_api01_other_roles_get_403_forbidden_role(client: TestClient, username: str) -> None:
    response = client.post("/api/v1/issuers", json=REGISTRATION, headers=login(client, username))
    assert_error(response, 403, "FORBIDDEN_ROLE")


@pytest.mark.parametrize("headers", [{}, {"Authorization": "Bearer not-a-token"}])
def test_api01_missing_or_invalid_token_returns_401_unauthenticated(client: TestClient, headers: dict[str, str]) -> None:
    assert_error(client.post("/api/v1/issuers", json=REGISTRATION, headers=headers), 401, "UNAUTHENTICATED")


def test_api01_expired_token_returns_401_unauthenticated(client: TestClient) -> None:
    expired = jwt.encode({"sub": "platform.admin", "role": "platform_admin", "exp": 1}, config.JWT_SECRET, algorithm="HS256")
    response = client.post("/api/v1/issuers", json=REGISTRATION, headers={"Authorization": f"Bearer {expired}"})
    assert_error(response, 401, "UNAUTHENTICATED")


def test_api01_registry_down_returns_503_and_stores_nothing(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    headers = login(client, "platform.admin")
    monkeypatch.setattr(config, "CHAIN_RPC_URL", "http://127.0.0.1:1")
    assert_error(client.post("/api/v1/issuers", json=REGISTRATION, headers=headers), 503, "REGISTRY_UNAVAILABLE")
    monkeypatch.undo()

    # Nothing was kept, so the same registration succeeds once the registry is back.
    assert client.post("/api/v1/issuers", json=REGISTRATION, headers=headers).status_code == 201


def test_api01_zero_address_returns_400_malformed_request(client: TestClient) -> None:
    zero = {**REGISTRATION, "registryAccount": "0x" + "0" * 40}
    response = client.post("/api/v1/issuers", json=zero, headers=login(client, "platform.admin"))
    assert_error(response, 400, "MALFORMED_REQUEST")
