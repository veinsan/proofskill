"""B-03: RGS signs its own EIP-1559 transactions (OD-12 custodial default), as it must on Base Sepolia.

Runs against the local Hardhat node with the PUBLIC Hardhat test keys, which may appear in local
config (CLAUDE.md). A wrong signature recovers another sender, which the contract would reject.
"""

import json
import threading
import time
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app import config, rgs, seed
from tests.conftest import issue

# Public Hardhat test accounts #0 (registry owner), #1 (ISS-001), #2 (ISS-002). Never real keys.
OWNER_KEY = "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80"
ISS001_KEY = "0x59c6995e998f97a5a0044966f0945389dc9e86dae88c7a8412f4603b6b78690d"
ISS002_KEY = "0x5de4111afa1a4b94908f83103eb1f1706367c2e68ca870fc3fb9a804cdab365a"


def test_keccak256_matches_the_selectors_ethers_computed(registry: Any) -> None:
    assert rgs.keccak256(b"").hex() == "c5d2460186f7233c927e7db2dcc703c0e500b653ca82273b7bfad8045d85a470"
    deployment = json.loads(registry.read_text(encoding="utf-8"))
    for signature, selector in deployment["functions"].items():
        assert "0x" + rgs.keccak256(signature.encode())[:4].hex() == selector
    names = {name: selector for selector, name in deployment["errors"].items()}
    assert "0x" + rgs.keccak256(b"NotOriginalIssuer()")[:4].hex() == names["NotOriginalIssuer"]


def test_address_of_derives_the_hardhat_accounts() -> None:
    assert rgs.address_of(OWNER_KEY) == "0xf39fd6e51aad88f6f4ce6ab8827279cfffb92266"
    assert rgs.address_of(ISS001_KEY) == seed.ISSUERS[0][3].lower()
    assert rgs.address_of(ISS002_KEY) == seed.ISSUERS[1][3].lower()


@pytest.fixture
def signing(monkeypatch: pytest.MonkeyPatch) -> list[tuple[str, list[Any], Any]]:
    """Gives RGS the issuer and owner keys and records every JSON-RPC call."""
    monkeypatch.setattr(config, "REGISTRY_OWNER_KEY", OWNER_KEY)
    monkeypatch.setattr(config, "ISSUER_KEYS", {"ISS-001": ISS001_KEY, "ISS-002": ISS002_KEY})
    calls: list[tuple[str, list[Any], Any]] = []
    real_rpc = rgs._rpc

    def recording_rpc(method: str, params: list[Any]) -> Any:
        result = real_rpc(method, params)
        calls.append((method, params, result))
        return result

    monkeypatch.setattr(rgs, "_rpc", recording_rpc)
    return calls


def test_b03_tc01_issuance_is_signed_by_the_issuers_own_key(client: TestClient, signing: list[tuple[str, list[Any], Any]]) -> None:
    body = issue(client)
    sent = [(params[0], result) for method, params, result in signing if method == "eth_sendRawTransaction"]
    assert len(sent) == 1 and not any(method == "eth_sendTransaction" for method, _, _ in signing)
    raw, tx_hash = sent[0]
    assert tx_hash == body["txHash"] == "0x" + rgs.keccak256(bytes.fromhex(raw[2:])).hex()  # multi-block keccak
    receipt = rgs._rpc("eth_getTransactionReceipt", [tx_hash])
    assert receipt["from"].lower() == seed.ISSUERS[0][3].lower() and receipt["type"] == "0x2"
    assert rgs.get_record(str(body["credentialId"])).commitment == body["commitment"]


def test_b03_tc14_other_issuers_signed_revoke_reverts_before_sending(
    client: TestClient, signing: list[tuple[str, list[Any], Any]]
) -> None:
    credential_id = str(issue(client)["credentialId"])
    signing.clear()
    with pytest.raises(rgs.RegistryError, match="NotOriginalIssuer"):
        rgs.revoke_credential(credential_id, seed.ISSUERS[1][3])
    assert [method for method, _, _ in signing] == []  # eth_estimateGas raised; nothing was sent
    assert rgs.get_record(credential_id).status == "active"


def test_b03_registry_owner_key_signs_issuer_registration(client: TestClient, signing: list[tuple[str, list[Any], Any]]) -> None:
    tx_hash = rgs.register_issuer("ISS-003", "0x90F79bf6EB2c4f870365E785982E1f101E93b906")  # Hardhat account #3
    assert any(method == "eth_sendRawTransaction" for method, _, _ in signing)
    assert rgs._rpc("eth_getTransactionReceipt", [tx_hash])["from"].lower() == rgs.address_of(OWNER_KEY)
    assert rgs.issuer_account("ISS-003") == "0x90f79bf6eb2c4f870365e785982e1f101e93b906"


def test_b05_nonce_lock_serializes_one_account_across_connections(registry: Any, monkeypatch: pytest.MonkeyPatch) -> None:
    """Vercel runs requests concurrently in and across instances; the Postgres advisory lock must
    keep two signed sends from the same account apart until the first is mined."""
    monkeypatch.setattr(config, "REGISTRY_OWNER_KEY", OWNER_KEY)
    monkeypatch.setattr(config, "ISSUER_KEYS", {"ISS-001": ISS001_KEY, "ISS-002": ISS002_KEY})
    spans: dict[str, list[tuple[str, float, float]]] = {}

    def slow_send(key: str, sender: str, data: str) -> str:
        start = time.monotonic()
        time.sleep(0.6)
        spans.setdefault(sender, []).append((data, start, time.monotonic()))
        return "0xfeed"

    monkeypatch.setattr(rgs, "_send_signed", slow_send)
    monkeypatch.setattr(rgs, "_wait_mined", lambda tx_hash: time.sleep(0.2))
    iss001, iss002 = seed.ISSUERS[0][3], seed.ISSUERS[1][3]
    jobs = [("CRD-A", iss001), ("CRD-B", iss001), ("CRD-C", iss002)]
    threads = [threading.Thread(target=rgs.revoke_credential, args=job) for job in jobs]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    (_, a_start, a_end), (_, b_start, b_end) = sorted(spans[iss001], key=lambda span: span[1])
    assert b_start >= a_end + 0.15  # the second waited for the first send and its receipt
    (_, c_start, c_end), = spans[iss002]
    assert c_start < a_end and a_start < c_end  # another account is not held up
