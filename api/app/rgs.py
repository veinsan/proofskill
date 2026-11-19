"""RGS Registry service: the blockchain adapter and the only module that talks to the chain.

It speaks JSON-RPC to the local Hardhat node over httpx with a minimal ABI codec, because
web3.py pulls in native extensions (regex, bitarray) that Windows Application Control blocks
on the team's machines. Transactions are sent from the node's unlocked public test accounts,
so no private key lives in this repository (CLAUDE.md, assumption A6).
"""

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from functools import cache
from typing import Any

import httpx

from app import config

ZERO_ADDRESS = "0x" + "0" * 40


class RegistryError(Exception):
    """The registry reverted. The message is the contract's custom error name when known."""


class RegistryUnavailable(RegistryError):
    """The chain could not be reached; endpoints map this to 503 REGISTRY_UNAVAILABLE."""


@cache
def _deployment() -> dict[str, Any]:
    deployment: dict[str, Any] = json.loads(config.REGISTRY_DEPLOYMENT.read_text(encoding="utf-8"))
    return deployment


def _word(value: int) -> bytes:
    return value.to_bytes(32, "big")


def encode_args(args: list[tuple[str, str]]) -> bytes:
    """ABI-encodes (type, value) pairs for the types the registry calls use: string, address, bytes32."""
    head, tail = b"", b""
    for kind, value in args:
        if kind == "string":
            data = value.encode()
            head += _word(32 * len(args) + len(tail))
            tail += _word(len(data)) + data.ljust(-(-len(data) // 32) * 32, b"\0")
        elif kind == "address":
            head += bytes.fromhex(value.removeprefix("0x")).rjust(32, b"\0")
        elif kind == "bytes32":
            word = bytes.fromhex(value.removeprefix("0x"))
            if len(word) != 32:
                raise ValueError("bytes32 needs exactly 32 bytes")
            head += word
        else:
            raise ValueError(f"unsupported ABI type {kind}")
    return head + tail


def _rpc(method: str, params: list[Any]) -> Any:
    try:
        response = httpx.post(
            config.CHAIN_RPC_URL,
            json={"jsonrpc": "2.0", "id": 1, "method": method, "params": params},
            timeout=10,
        )
        response.raise_for_status()
    except httpx.HTTPError as exc:
        raise RegistryUnavailable(f"registry unreachable: {exc}") from exc
    body: dict[str, Any] = response.json()
    if "error" in body:
        error = body["error"]
        data = error.get("data")
        data = data.get("data") if isinstance(data, dict) else data
        name = _deployment()["errors"].get(data[:10]) if isinstance(data, str) else None
        raise RegistryError(name or error.get("message", "registry error"))
    return body["result"]


def _calldata(signature: str, args: list[tuple[str, str]]) -> str:
    return _deployment()["functions"][signature] + encode_args(args).hex()


def _call(signature: str, args: list[tuple[str, str]]) -> bytes:
    result: str = _rpc("eth_call", [{"to": _deployment()["address"], "data": _calldata(signature, args)}, "latest"])
    return bytes.fromhex(result.removeprefix("0x"))


def _transact(signature: str, args: list[tuple[str, str]], sender: str) -> str:
    tx_hash: str = _rpc(
        "eth_sendTransaction",
        [{"from": sender, "to": _deployment()["address"], "data": _calldata(signature, args)}],
    )
    receipt = _rpc("eth_getTransactionReceipt", [tx_hash])  # Hardhat automines, so it exists now
    if receipt is None or receipt["status"] != "0x1":
        raise RegistryError(f"transaction {tx_hash} failed")
    return tx_hash


def issuer_account(issuer_id: str) -> str | None:
    """Chain account bound to the issuer ID (lowercase hex), or None when it is not registered."""
    account = "0x" + _call("issuerAccountOf(string)", [("string", issuer_id)])[12:32].hex()
    return None if account == ZERO_ADDRESS else account


@dataclass(frozen=True)
class RegistryRecord:
    """report Tabel 8.5 RegistryRecord, plus issuer_active from OD-2."""

    commitment: str  # 0x-prefixed lowercase hex
    issuer_id: str
    status: str  # "active" or "revoked"
    timestamp: datetime
    issuer_active: bool


_STATUS = {1: "active", 2: "revoked"}


def issue_credential(credential_id: str, commitment: str, issuer_account: str) -> str:
    """T05 anchorCommitment: ProofSkillRegistry.issueCredential sent by the issuer's account."""
    return _transact(
        "issueCredential(string,bytes32)",
        [("string", credential_id), ("bytes32", commitment)],
        issuer_account,
    )


def get_record(credential_id: str) -> RegistryRecord:
    """T14 getRecord. Raises RegistryError("CredentialNotFound") for an unknown credential."""
    out = _call("getRecord(string)", [("string", credential_id)])
    words = [int.from_bytes(out[i : i + 32], "big") for i in range(0, 160, 32)]
    issuer_offset = words[1]
    issuer_length = int.from_bytes(out[issuer_offset : issuer_offset + 32], "big")
    issuer_id = out[issuer_offset + 32 : issuer_offset + 32 + issuer_length].decode()
    return RegistryRecord(
        commitment="0x" + out[0:32].hex(),
        issuer_id=issuer_id,
        status=_STATUS[words[2]],
        timestamp=datetime.fromtimestamp(words[3], UTC),
        issuer_active=bool(words[4]),
    )


def register_issuer(issuer_id: str, account: str) -> str:
    """ProofSkillRegistry.registerIssuer from the platform admin account. Returns the tx hash."""
    return _transact(
        "registerIssuer(string,address)",
        [("string", issuer_id), ("address", account)],
        _deployment()["owner"],
    )
