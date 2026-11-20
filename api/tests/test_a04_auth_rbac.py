"""A-04 completion criteria: F-01 authentication and RBAC (API-00, API-01, NFR-01, OD-1), with
Supabase Auth behind API-00 and Supabase JWTs verified against the JWKS since B-02."""

import httpx
import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import ec
from fastapi.testclient import TestClient

from app import config, ias, rgs, seed
from tests.conftest import SIGNING_KEY, SUPABASE_TEST_URL, TEST_PASSWORD, login, supabase_token

REAL_SIGNING_KEY = ias._signing_key  # saved before the autouse fixture replaces it

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
    response = client.post("/api/v1/auth/token", json={"username": username, "password": TEST_PASSWORD})
    assert response.status_code == 200
    body = response.json()
    assert set(body) == {"accessToken", "tokenType", "expiresIn", "role"}  # contract unchanged (B-02)
    assert body["tokenType"] == "Bearer"
    assert body["expiresIn"] == 3600
    assert body["role"] == role
    claims = jwt.decode(body["accessToken"], SIGNING_KEY.public_key(), algorithms=["ES256"], audience="authenticated")
    assert (claims["app_metadata"]["username"], claims["app_metadata"]["role"]) == (username, role)


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


@pytest.mark.parametrize(
    "token",
    [
        supabase_token("platform.admin", expires_in=-60),  # expired
        supabase_token("platform.admin", key=ec.generate_private_key(ec.SECP256R1())),  # another project's key
        jwt.encode({"sub": "x", "aud": "authenticated", "iss": f"{SUPABASE_TEST_URL}/auth/v1", "exp": 9999999999,
                    "app_metadata": {"role": "platform_admin", "username": "platform.admin"}}, "guessed-secret-guessed-secret-guessed", algorithm="HS256"),
        supabase_token("platform.admin", role=None),  # a Supabase user without a ProofSkill role
        supabase_token("platform.admin", role="superuser"),
    ],
    ids=["expired", "other-key", "hs256-forgery", "no-role", "unknown-role"],
)
def test_b02_tokens_that_are_not_valid_proofskill_tokens_get_401(client: TestClient, token: str) -> None:
    response = client.post("/api/v1/issuers", json=REGISTRATION, headers={"Authorization": f"Bearer {token}"})
    assert_error(response, 401, "UNAUTHENTICATED")


def test_b05_token_from_a_slightly_faster_clock_is_accepted(client: TestClient) -> None:
    """Supabase's clock may run ahead of the API host's; a fresh token must not read as not-yet-valid."""
    token = supabase_token("platform.admin", skew=5)
    response = client.post("/api/v1/issuers", json=REGISTRATION, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 201, response.text


def test_b02_guard_verifies_with_the_projects_jwks(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    jwk = {**jwt.algorithms.ECAlgorithm.to_jwk(SIGNING_KEY.public_key(), as_dict=True), "kid": "test-key", "alg": "ES256", "use": "sig"}
    fetched: list[str] = []

    def fake_fetch(self: jwt.PyJWKClient) -> dict[str, object]:
        fetched.append(self.uri)
        return {"keys": [jwk]}

    monkeypatch.setattr(ias, "_signing_key", REAL_SIGNING_KEY)
    monkeypatch.setattr(jwt.PyJWKClient, "fetch_data", fake_fetch)
    ias._jwks.cache_clear()
    response = client.post("/api/v1/issuers", json=REGISTRATION, headers=login(client, "platform.admin"))
    assert response.status_code == 201, response.text
    assert fetched == [f"{SUPABASE_TEST_URL}/auth/v1/.well-known/jwks.json"]
    ias._jwks.cache_clear()


def test_api01_registry_down_returns_503_and_stores_nothing(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    headers = login(client, "platform.admin")
    with monkeypatch.context() as down:
        down.setattr(config, "CHAIN_RPC_URL", "http://127.0.0.1:1")
        assert_error(client.post("/api/v1/issuers", json=REGISTRATION, headers=headers), 503, "REGISTRY_UNAVAILABLE")

    # Nothing was kept, so the same registration succeeds once the registry is back.
    assert client.post("/api/v1/issuers", json=REGISTRATION, headers=headers).status_code == 201


def test_api01_zero_address_returns_400_malformed_request(client: TestClient) -> None:
    zero = {**REGISTRATION, "registryAccount": "0x" + "0" * 40}
    response = client.post("/api/v1/issuers", json=zero, headers=login(client, "platform.admin"))
    assert_error(response, 400, "MALFORMED_REQUEST")


def test_b02_seed_creates_or_updates_supabase_users_with_app_metadata(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[str, str, dict[str, object] | None]] = []

    def fake(method: str):  # type: ignore[no-untyped-def]
        def send(url: str, **kwargs: object) -> httpx.Response:
            calls.append((method, url, kwargs.get("json")))  # type: ignore[arg-type]
            body = {"users": [{"email": "holder.a@proofskill.example", "id": "uid-holder-a"}]} if method == "GET" else {}
            return httpx.Response(200, json=body, request=httpx.Request(method, url))
        return send

    for method in ("get", "post", "put"):
        monkeypatch.setattr(httpx, method, fake(method.upper()))
    monkeypatch.setattr(config, "SUPABASE_SERVICE_ROLE_KEY", "sb_secret_test")
    monkeypatch.setattr(config, "SEED_PASSWORD", "short")
    with pytest.raises(SystemExit):
        seed.sync_auth_users()  # refuses a weak password before calling Supabase
    assert calls == []

    monkeypatch.setattr(config, "SEED_PASSWORD", "a-long-test-password")
    assert seed.sync_auth_users() == len(seed.ACCOUNTS)
    admin = f"{SUPABASE_TEST_URL}/auth/v1/admin/users"
    assert [c[0] for c in calls].count("PUT") == 1 and ("PUT", f"{admin}/uid-holder-a") in [(c[0], c[1]) for c in calls]
    created = {c[2]["email"]: c[2] for c in calls if c[0] == "POST"}  # type: ignore[index]
    assert len(created) == len(seed.ACCOUNTS) - 1
    assert created["admin.iss001@proofskill.example"]["app_metadata"] == {
        "role": "issuer_admin", "issuerId": "ISS-001", "holderRef": None, "username": "admin.iss001"
    }
    assert all(c[2]["password"] == "a-long-test-password" and c[2]["email_confirm"] for c in calls if c[2])  # type: ignore[index]
