"""RGS Registry service: the blockchain adapter and the only module that talks to the chain.

It speaks JSON-RPC over httpx with a minimal ABI codec, because web3.py and eth-account pull in
native extensions (regex, bitarray, pydantic-core builds) that Windows Application Control blocks on
the team's machines. Locally, transactions are sent from the Hardhat node's unlocked public test
accounts. On the Base Sepolia testnet (B-03), RGS signs EIP-1559 transactions itself with the key of
the acting account (OD-12 custodial default): coincurve signs, and keccak-256 is written below because
pycryptodome is blocked too. Keys come only from the environment, never from this repository.
Signed transactions are serialized per account by a Postgres advisory lock (see _transact).
"""

import json
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from functools import cache
from typing import Any

import httpx
from coincurve import PrivateKey

from app import config, db

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


# --- keccak-256, RLP, and keys (B-03) ----------------------------------------------------


def _rol(lane: int, n: int) -> int:
    n %= 64
    return ((lane << n) | (lane >> (64 - n))) & 0xFFFFFFFFFFFFFFFF if n else lane


def _keccak_f(lanes: list[list[int]]) -> None:
    """Keccak-f[1600] in place, after the Keccak team's CompactFIPS202 reference."""
    r = 1
    for _ in range(24):
        c = [lanes[x][0] ^ lanes[x][1] ^ lanes[x][2] ^ lanes[x][3] ^ lanes[x][4] for x in range(5)]
        d = [c[(x + 4) % 5] ^ _rol(c[(x + 1) % 5], 1) for x in range(5)]
        for x in range(5):
            for y in range(5):
                lanes[x][y] ^= d[x]
        x, y, current = 1, 0, lanes[1][0]
        for t in range(24):
            x, y = y, (2 * x + 3 * y) % 5
            current, lanes[x][y] = lanes[x][y], _rol(current, (t + 1) * (t + 2) // 2)
        for y in range(5):
            row = [lanes[x][y] for x in range(5)]
            for x in range(5):
                lanes[x][y] = row[x] ^ (~row[(x + 1) % 5] & row[(x + 2) % 5])
        for j in range(7):
            r = ((r << 1) ^ ((r >> 7) * 0x71)) % 256
            if r & 2:
                lanes[0][0] ^= 1 << ((1 << j) - 1)


def keccak256(data: bytes) -> bytes:
    """Ethereum's keccak-256 (original Keccak padding, not NIST SHA3-256)."""
    rate = 136
    padded = bytearray(data) + b"\x01"
    padded += b"\0" * (-len(padded) % rate)
    padded[-1] |= 0x80
    lanes = [[0] * 5 for _ in range(5)]
    for start in range(0, len(padded), rate):
        block = padded[start : start + rate]
        for i in range(rate // 8):
            lanes[i % 5][i // 5] ^= int.from_bytes(block[8 * i : 8 * i + 8], "little")
        _keccak_f(lanes)
    return b"".join(lanes[i % 5][i // 5].to_bytes(8, "little") for i in range(4))


def _rlp(item: int | bytes | list[Any]) -> bytes:
    def length(size: int, offset: int) -> bytes:
        if size < 56:
            return bytes([offset + size])
        encoded = size.to_bytes((size.bit_length() + 7) // 8, "big")
        return bytes([offset + 55 + len(encoded)]) + encoded

    if isinstance(item, list):
        body = b"".join(_rlp(i) for i in item)
        return length(len(body), 0xC0) + body
    if isinstance(item, int):
        item = item.to_bytes((item.bit_length() + 7) // 8, "big")
    return item if len(item) == 1 and item[0] < 0x80 else length(len(item), 0x80) + item


def address_of(key: str) -> str:
    """Lowercase 0x address of a hex private key."""
    public = PrivateKey(bytes.fromhex(key.removeprefix("0x"))).public_key.format(compressed=False)
    return "0x" + keccak256(public[1:])[-20:].hex()


def account_for_issuer(issuer_id: str) -> str | None:
    """The chain account of an issuer whose key the API holds (OD-12), else None."""
    key = config.ISSUER_KEYS.get(issuer_id)
    return address_of(key) if key else None


def _key_for(sender: str) -> str | None:
    keys = [config.REGISTRY_OWNER_KEY, *config.ISSUER_KEYS.values()]
    return next((k for k in keys if k and address_of(k) == sender.lower()), None)


_RATE_LIMITED = {401, 429}  # the public Base Sepolia RPC answers these when it throttles (B-07)


def _rpc(method: str, params: list[Any]) -> Any:
    try:
        for attempt in range(3):
            response = httpx.post(
                config.CHAIN_RPC_URL,
                json={"jsonrpc": "2.0", "id": 1, "method": method, "params": params},
                timeout=10,
            )
            # A throttled request was never processed, so retrying it is safe, even a raw transaction.
            if response.status_code not in _RATE_LIMITED or attempt == 2:
                break
            time.sleep(0.5 * (attempt + 1))
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


def _send_signed(key: str, sender: str, data: str) -> str:
    """Signs and sends an EIP-1559 transaction. A revert surfaces at eth_estimateGas with the
    contract's custom error, before anything is sent (TC-14). Call only under the nonce lock."""
    to = _deployment()["address"]
    gas = int(_rpc("eth_estimateGas", [{"from": sender, "to": to, "data": data}]), 16)
    tip = int(_rpc("eth_maxPriorityFeePerGas", []), 16)
    base_fee = int(_rpc("eth_getBlockByNumber", ["latest", False])["baseFeePerGas"], 16)
    nonce = int(_rpc("eth_getTransactionCount", [sender, "pending"]), 16)
    fields: list[Any] = [
        int(_deployment()["chainId"]), nonce, tip, 2 * base_fee + tip, gas * 6 // 5,  # 20% gas margin
        bytes.fromhex(to.removeprefix("0x")), 0, bytes.fromhex(data.removeprefix("0x")), [],
    ]
    signature = PrivateKey(bytes.fromhex(key.removeprefix("0x"))).sign_recoverable(
        keccak256(b"\x02" + _rlp(fields)), hasher=None
    )
    r, s = int.from_bytes(signature[:32], "big"), int.from_bytes(signature[32:64], "big")
    raw = b"\x02" + _rlp([*fields, signature[64], r, s])
    tx_hash: str = _rpc("eth_sendRawTransaction", ["0x" + raw.hex()])
    return tx_hash


def _wait_mined(tx_hash: str) -> None:
    # Hardhat automines, so the receipt exists at once; Base Sepolia mines a block every 2 seconds.
    # shortcut: after 60 s this gives up with 503 although the transaction may still be mined later.
    deadline = time.monotonic() + 60
    while (receipt := _rpc("eth_getTransactionReceipt", [tx_hash])) is None:
        if time.monotonic() > deadline:
            raise RegistryUnavailable(f"transaction {tx_hash} not mined within 60 seconds")
        time.sleep(1)
    if receipt["status"] != "0x1":
        raise RegistryError(f"transaction {tx_hash} failed")


def _transact(signature: str, args: list[tuple[str, str]], sender: str) -> str:
    data = _calldata(signature, args)
    key = _key_for(sender)
    if not key:  # local Hardhat node: unlocked public test accounts
        tx_hash: str = _rpc("eth_sendTransaction", [{"from": sender, "to": _deployment()["address"], "data": data}])
        _wait_mined(tx_hash)
        return tx_hash
    # Nonce lock (B-05): on Vercel, one instance serves several requests at once and several
    # instances run side by side, so an in-process lock cannot order nonces. A Postgres advisory
    # lock per sender can, because every instance shares the database. It is held until the receipt,
    # so the next transaction from this account reads a settled nonce; any error releases it.
    with db.connect(config.DATABASE_URL) as lock:
        lock.execute("SELECT pg_advisory_xact_lock(hashtext(%s))", (sender.lower(),))
        tx_hash = _send_signed(key, sender, data)
        _wait_mined(tx_hash)
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


def revoke_credential(credential_id: str, issuer_account: str) -> str:
    """T26 setStatus: ProofSkillRegistry.revokeCredential sent by the issuer's account. The contract
    itself refuses any other issuer (RegistryError "NotOriginalIssuer", TC-14)."""
    return _transact("revokeCredential(string)", [("string", credential_id)], issuer_account)


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
