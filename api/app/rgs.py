"""RGS Registry service: the blockchain adapter and the only module that talks to the chain.

It speaks JSON-RPC to the local Hardhat node over httpx with a minimal ABI codec, because
web3.py pulls in native extensions (regex, bitarray) that Windows Application Control blocks
on the team's machines. Transactions are sent from the node's unlocked public test accounts,
so no private key lives in this repository (CLAUDE.md, assumption A6).
"""

import json
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
    """ABI-encodes (type, value) pairs for the types the registry calls use so far: string, address."""
    head, tail = b"", b""
    for kind, value in args:
        if kind == "string":
            data = value.encode()
            head += _word(32 * len(args) + len(tail))
            tail += _word(len(data)) + data.ljust(-(-len(data) // 32) * 32, b"\0")
        elif kind == "address":
            head += bytes.fromhex(value.removeprefix("0x")).rjust(32, b"\0")
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


def register_issuer(issuer_id: str, account: str) -> str:
    """ProofSkillRegistry.registerIssuer from the platform admin account. Returns the tx hash."""
    return _transact(
        "registerIssuer(string,address)",
        [("string", issuer_id), ("address", account)],
        _deployment()["owner"],
    )
