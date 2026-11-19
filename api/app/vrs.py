"""VRS Verification service: API-06 verifyCredential (T11–T17, FR-06, FR-12, NFR-04).

Verification never depends on the AI (NFR-06): this module does not import AMS.
"""

from datetime import date, datetime
from typing import Annotated, Literal

from fastapi import APIRouter, Depends
from psycopg import Connection
from psycopg.rows import DictRow
from pydantic import Field

from app import aas, cis, rgs
from app.cis import IssuerRef, SkillRef
from app.errors import ApiError
from app.ias import Conn, Principal, require_roles
from app.models import ApiModel

router = APIRouter()

Result = Literal["VALID", "REVOKED", "TAMPERED", "ISSUER_UNAUTHORIZED"]


class VerifyRequest(ApiModel):
    share_token: str = Field(min_length=1, max_length=100)


class Checks(ApiModel):
    integrity: Literal["PASS", "FAIL"]
    issuer_authorized: Literal["PASS", "FAIL"]
    status: Literal["ACTIVE", "REVOKED"]


class SharedProgram(ApiModel):
    title: str | None = None
    completed_at: date | None = None
    criteria: str | None = None


class SharedCredential(ApiModel):
    """Only credentialId, the issuer, and the fields in the link's scope (T-03, O-06)."""

    credential_id: str
    issuer: IssuerRef
    holder_display_name: str | None = None
    program: SharedProgram | None = None
    skills: list[SkillRef] | None = None


class ChainRef(ApiModel):
    tx_hash: str | None


class VerificationResult(ApiModel):
    verification_id: str
    result: Result
    checks: Checks
    reason: str | None = None  # REVOKED only: the issuer's short reason
    credential: SharedCredential | None = None  # withheld when TAMPERED (FR-12)
    chain_ref: ChainRef
    verified_at: datetime


def decide(checks: Checks) -> Result:
    """The main cause wins: changed data first (nothing else can be trusted), then the issuer's own
    revocation, then a deactivated issuer. VALID only when all three checks pass (report Tabel 9.16)."""
    if checks.integrity == "FAIL":
        return "TAMPERED"
    if checks.status == "REVOKED":
        return "REVOKED"
    if checks.issuer_authorized == "FAIL":
        return "ISSUER_UNAUTHORIZED"
    return "VALID"


def _resolve_share_link(conn: Connection[DictRow], share_token: str) -> DictRow:
    """AAS.resolveShareLink (T12): 404 SHARE_LINK_NOT_FOUND, 410 SHARE_LINK_EXPIRED if expired or revoked."""
    link = conn.execute(
        "SELECT *, (revoked_at IS NOT NULL OR expires_at <= now()) AS closed FROM share_links WHERE share_token = %s",
        (share_token,),
    ).fetchone()
    if link is None:
        raise ApiError(404, "SHARE_LINK_NOT_FOUND", "This share link is not known.")
    if link["closed"]:
        raise ApiError(410, "SHARE_LINK_EXPIRED", "This share link has expired or was revoked. Ask the holder for a new link.")
    return link


def _shared_credential(conn: Connection[DictRow], credential: DictRow, scope: list[str]) -> SharedCredential:
    issuer = conn.execute("SELECT issuer_id, name FROM issuers WHERE issuer_id = %s", (credential["issuer_id"],)).fetchone()
    program = SharedProgram(
        title=credential["program_title"] if "program.title" in scope else None,
        completed_at=credential["completed_at"] if "completedAt" in scope else None,
        criteria=credential["criteria"] if "program.criteria" in scope else None,
    )
    skills = None
    if "skills" in scope:
        rows = conn.execute(
            "SELECT s.skill_id, s.label FROM credential_skills cs JOIN skills s USING (skill_id)"
            " WHERE cs.credential_id = %s ORDER BY s.skill_id",
            (credential["credential_id"],),
        ).fetchall()
        skills = [SkillRef(**row) for row in rows]
    return SharedCredential(
        credential_id=credential["credential_id"],
        issuer=IssuerRef(**issuer) if issuer else IssuerRef(issuer_id=credential["issuer_id"], name=""),
        holder_display_name=credential["holder_display_name"] if "holderDisplayName" in scope else None,
        program=program if program.model_dump(exclude_none=True) else None,
        skills=skills,
    )


@router.post("/verifications", response_model=VerificationResult, response_model_exclude_none=True, tags=["VRS"])
def verify_credential(
    body: VerifyRequest,
    principal: Annotated[Principal, Depends(require_roles("verifier"))],
    conn: Conn,
) -> VerificationResult:
    """API-06: recompute the hash, read the registry, and report integrity, issuer authorization,
    and status separately. A credential that fails still returns 200 with its result (T16)."""
    link = _resolve_share_link(conn, body.share_token)
    credential = cis.load_credential(conn, link["credential_id"])

    try:
        record: rgs.RegistryRecord | None = rgs.get_record(credential["credential_id"])  # T14
    except rgs.RegistryUnavailable as exc:
        raise ApiError(503, "REGISTRY_UNAVAILABLE", "The registry cannot be read, so no result can be given.") from exc
    except rgs.RegistryError as exc:
        if str(exc) != "CredentialNotFound":
            raise
        record = None  # a row the registry never anchored cannot be trusted

    if record is None:
        checks = Checks(integrity="FAIL", issuer_authorized="FAIL", status=credential["status"].upper())
    else:
        checks = Checks(
            integrity="PASS" if cis.commitment_of(conn, credential) == record.commitment else "FAIL",  # T13, T15
            issuer_authorized="PASS" if record.issuer_active and record.issuer_id == credential["issuer_id"] else "FAIL",
            status="REVOKED" if record.status == "revoked" else "ACTIVE",  # the chain, never the database column
        )
    result = decide(checks)

    row = conn.execute(
        "INSERT INTO verifications (link_id, verifier, result, integrity, issuer_authorized, status_check)"
        " VALUES (%s, %s, %s, %s, %s, %s) RETURNING verification_id, verified_at",
        (link["link_id"], principal.username, result, checks.integrity, checks.issuer_authorized, checks.status),
    ).fetchone()
    assert row is not None
    aas.record_audit(conn, principal.role, "verifyCredential", row["verification_id"], result)
    conn.commit()

    return VerificationResult(
        verification_id=row["verification_id"],
        result=result,
        checks=checks,
        reason=(credential["revocation_reason"] or "No reason recorded.") if result == "REVOKED" else None,
        credential=None if result == "TAMPERED" else _shared_credential(conn, credential, link["scope"]),
        chain_ref=ChainRef(tx_hash=credential["tx_hash"]),
        verified_at=row["verified_at"],
    )
