"""IAS Issuer Authorization service: accounts, roles, access tokens, and issuer registration.

API-00 issueAccessToken and API-01 registerIssuer (report Tabel 8.4, 9.3, 9.15), plus the
role guards every other service uses (NFR-01).

Since B-02, accounts live in Supabase Auth. API-00 proxies Supabase's password sign-in, so the
contract stays the same, and every guard verifies the Supabase-issued ES256 JWT against the
project's JWKS. The ProofSkill role, issuerId, holderRef, and username come from the token's
app_metadata, which only the service-role key (the seed) can write, never the user.
"""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from functools import cache
from typing import Annotated, Any, Literal, get_args

import httpx
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
ROLES: tuple[str, ...] = get_args(Role)
# Supabase Auth needs an email; API-00 keeps the report's username (shortcut: one fixed reserved
# domain for the seeded accounts; real addresses arrive with self sign-up, OD-11).
EMAIL_DOMAIN = "proofskill.example"

router = APIRouter()
Conn = Annotated[Connection[DictRow], Depends(db.get_conn)]


def auth_email(username: str) -> str:
    return f"{username}@{EMAIL_DOMAIN}"


# --- Tokens and role guards -------------------------------------------------------------


@dataclass(frozen=True)
class Principal:
    username: str
    role: str
    issuer_id: str | None
    holder_ref: str | None


@cache
def _jwks(url: str) -> jwt.PyJWKClient:
    return jwt.PyJWKClient(url, cache_keys=True)  # keys are cached; Supabase rotates them rarely


def _signing_key(token: str) -> Any:
    """The project's public key that signed this token (Supabase JWKS)."""
    return _jwks(f"{config.SUPABASE_URL}/auth/v1/.well-known/jwks.json").get_signing_key_from_jwt(token).key


_bearer = HTTPBearer(auto_error=False)


def current_principal(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> Principal:
    """Reads the Bearer token: 401 UNAUTHENTICATED when it is missing, invalid, expired, or not
    a ProofSkill account (no role in app_metadata)."""
    if credentials is None:
        raise ApiError(401, "UNAUTHENTICATED", "Access token is missing.")
    token = credentials.credentials
    try:
        claims = jwt.decode(
            token,
            _signing_key(token),
            algorithms=["ES256", "RS256"],  # asymmetric only, so a forged HS256 token never passes
            audience="authenticated",
            issuer=f"{config.SUPABASE_URL}/auth/v1",
            options={"require": ["exp", "sub"]},
        )
    except (jwt.InvalidTokenError, jwt.PyJWKClientError) as exc:
        raise ApiError(401, "UNAUTHENTICATED", "Access token is invalid or expired.") from exc
    meta = claims.get("app_metadata") or {}
    if meta.get("role") not in ROLES or not meta.get("username"):
        raise ApiError(401, "UNAUTHENTICATED", "This account has no ProofSkill role.")
    return Principal(meta["username"], meta["role"], meta.get("issuerId"), meta.get("holderRef"))


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
def issue_access_token(body: TokenRequest) -> AccessToken:
    """API-00: proxies Supabase's password sign-in (B-02) and returns its access token."""
    response = httpx.post(
        f"{config.SUPABASE_URL}/auth/v1/token",
        params={"grant_type": "password"},
        headers={"apikey": config.SUPABASE_ANON_KEY},
        json={"email": auth_email(body.username), "password": body.password},
        timeout=15,
    )
    if response.status_code == 400:  # Supabase: invalid_credentials (also unknown user)
        raise ApiError(401, "INVALID_CREDENTIALS", "The username or password is wrong.")
    response.raise_for_status()  # anything else is a server-side fault, not the caller's
    session = response.json()
    role = (session["user"].get("app_metadata") or {}).get("role")
    if role not in ROLES:
        raise ApiError(401, "INVALID_CREDENTIALS", "This account has no ProofSkill role.")
    return AccessToken(access_token=session["access_token"], expires_in=session["expires_in"], role=role)


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
