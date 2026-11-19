"""IAS Issuer Authorization service: accounts, roles, access tokens, and issuer registration.

API-00 issueAccessToken and API-01 registerIssuer (report Tabel 8.4, 9.3, 9.15), plus the
role guards every other service uses (NFR-01).
"""

import hashlib
import hmac
import secrets
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Annotated, Literal

import jwt
from fastapi import APIRouter, Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from psycopg import Connection
from psycopg.rows import DictRow
from pydantic import Field, field_validator

from app import config, db, rgs
from app.errors import ApiError
from app.models import ApiModel

Role = Literal["platform_admin", "issuer_admin", "holder", "verifier"]
TOKEN_TTL_SECONDS = 3600  # report API-00 example: expiresIn 3600
JWT_ALGORITHM = "HS256"

router = APIRouter()
Conn = Annotated[Connection[DictRow], Depends(db.get_conn)]


# --- Passwords --------------------------------------------------------------------------


def _scrypt(password: str, salt: bytes) -> bytes:
    return hashlib.scrypt(password.encode(), salt=salt, n=2**14, r=8, p=1)


def hash_password(password: str) -> str:
    """scrypt with a random 16-byte salt, stored as scrypt$<salt hex>$<digest hex>."""
    salt = secrets.token_bytes(16)
    return f"scrypt${salt.hex()}${_scrypt(password, salt).hex()}"


def verify_password(password: str, stored: str) -> bool:
    _, salt_hex, digest_hex = stored.split("$")
    return hmac.compare_digest(_scrypt(password, bytes.fromhex(salt_hex)), bytes.fromhex(digest_hex))


_DUMMY_HASH = hash_password(secrets.token_urlsafe(16))  # equalizes timing for unknown usernames


# --- Tokens and role guards -------------------------------------------------------------


@dataclass(frozen=True)
class Principal:
    username: str
    role: str
    issuer_id: str | None
    holder_ref: str | None


def issue_token(username: str, role: str, issuer_id: str | None, holder_ref: str | None) -> str:
    now = datetime.now(UTC)
    claims = {
        "sub": username,
        "role": role,
        "issuerId": issuer_id,
        "holderRef": holder_ref,
        "iat": now,
        "exp": now + timedelta(seconds=TOKEN_TTL_SECONDS),
    }
    return jwt.encode(claims, config.JWT_SECRET, algorithm=JWT_ALGORITHM)


_bearer = HTTPBearer(auto_error=False)


def current_principal(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> Principal:
    """Reads the Bearer token: 401 UNAUTHENTICATED when it is missing, invalid, or expired."""
    if credentials is None:
        raise ApiError(401, "UNAUTHENTICATED", "Access token is missing.")
    try:
        claims = jwt.decode(
            credentials.credentials,
            config.JWT_SECRET,
            algorithms=[JWT_ALGORITHM],
            options={"require": ["exp", "sub", "role"]},
        )
    except jwt.InvalidTokenError as exc:
        raise ApiError(401, "UNAUTHENTICATED", "Access token is invalid or expired.") from exc
    return Principal(claims["sub"], claims["role"], claims.get("issuerId"), claims.get("holderRef"))


def require_roles(*roles: Role) -> Callable[[Principal], Principal]:
    """Dependency that admits only the given roles: other roles get 403 FORBIDDEN_ROLE."""

    def guard(principal: Annotated[Principal, Depends(current_principal)]) -> Principal:
        if principal.role not in roles:
            raise ApiError(403, "FORBIDDEN_ROLE", f"This operation requires the role {' or '.join(roles)}.")
        return principal

    return guard


def check_authorization(principal: Principal, conn: Connection[DictRow]) -> DictRow:
    """checkAuthorization (T03, T25): the caller must be an issuer admin of a registered issuer.
    Returns that issuer's row, or raises 403 ISSUER_NOT_AUTHORIZED. The registry itself also
    refuses a deactivated issuer when the transaction is sent."""
    issuer = None
    if principal.role == "issuer_admin" and principal.issuer_id:
        issuer = conn.execute("SELECT * FROM issuers WHERE issuer_id = %s", (principal.issuer_id,)).fetchone()
    if issuer is None:
        raise ApiError(403, "ISSUER_NOT_AUTHORIZED", "This account is not an admin of a registered issuer.")
    return issuer


# --- API-00 POST /auth/token ------------------------------------------------------------


class TokenRequest(ApiModel):
    username: str
    password: str


class AccessToken(ApiModel):
    access_token: str
    token_type: Literal["Bearer"] = "Bearer"
    expires_in: int
    role: Role


@router.post("/auth/token", response_model=AccessToken, response_model_by_alias=True, tags=["IAS"])
def issue_access_token(body: TokenRequest, conn: Conn) -> AccessToken:
    """API-00: exchanges a seeded account's credentials for a role-bearing access token."""
    account = conn.execute("SELECT * FROM accounts WHERE username = %s", (body.username,)).fetchone()
    valid = verify_password(body.password, account["password_hash"] if account else _DUMMY_HASH)
    if account is None or not valid:
        raise ApiError(401, "INVALID_CREDENTIALS", "The username or password is wrong.")
    token = issue_token(account["username"], account["role"], account["issuer_id"], account["holder_ref"])
    return AccessToken(access_token=token, expires_in=TOKEN_TTL_SECONDS, role=account["role"])


# --- API-01 POST /issuers ---------------------------------------------------------------


class IssuerRegistration(ApiModel):
    name: str = Field(min_length=1, max_length=200)
    unit_type: str = Field(min_length=1, max_length=100)
    registry_account: str = Field(pattern=r"^0x[0-9a-fA-F]{40}$")

    @field_validator("registry_account")
    @classmethod
    def _not_zero(cls, value: str) -> str:
        if int(value, 16) == 0:
            raise ValueError("must not be the zero address")
        return value


class IssuerRecord(ApiModel):
    issuer_id: str
    name: str
    unit_type: str
    registry_account: str
    tx_hash: str
    registered_at: datetime


@router.post("/issuers", status_code=201, response_model=IssuerRecord, response_model_by_alias=True, tags=["IAS"])
def register_issuer(
    body: IssuerRegistration,
    _: Annotated[Principal, Depends(require_roles("platform_admin"))],
    conn: Conn,
) -> IssuerRecord:
    """API-01: registers an issuer off-chain and on the registry (prerequisite of T03, FR-01)."""
    taken = conn.execute(
        "SELECT 1 FROM issuers WHERE lower(chain_account) = lower(%s)", (body.registry_account,)
    ).fetchone()
    if taken:
        raise ApiError(409, "ISSUER_ALREADY_REGISTERED", "This registry account already belongs to an issuer.")

    row = conn.execute(
        "INSERT INTO issuers (issuer_id, name, unit_type, chain_account)"
        " SELECT 'ISS-' || lpad((coalesce(max(substr(issuer_id, 5)::int), 0) + 1)::text, 3, '0'), %s, %s, %s"
        " FROM issuers RETURNING issuer_id, created_at",
        (body.name, body.unit_type, body.registry_account),
    ).fetchone()
    assert row is not None
    try:
        tx_hash = rgs.register_issuer(row["issuer_id"], body.registry_account)
    except rgs.RegistryUnavailable as exc:
        conn.rollback()
        raise ApiError(503, "REGISTRY_UNAVAILABLE", "The registry cannot be reached; no issuer was registered.") from exc
    except rgs.RegistryError as exc:
        conn.rollback()
        if str(exc) == "IssuerAlreadyRegistered":
            raise ApiError(409, "ISSUER_ALREADY_REGISTERED", "This issuer is already on the registry.") from exc
        raise
    conn.commit()
    return IssuerRecord(
        issuer_id=row["issuer_id"],
        name=body.name,
        unit_type=body.unit_type,
        registry_account=body.registry_account,
        tx_hash=tx_hash,
        registered_at=row["created_at"],
    )
