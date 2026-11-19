"""CIS Credential Issuance service: API-02 issueCredential (T02–T06, FR-02, FR-03, FR-04) and
API-03 getCredential (T07, T28, FR-05)."""

import hashlib
import json
import secrets
from datetime import date, datetime
from typing import Annotated, Any, Literal

from fastapi import APIRouter, Depends
from psycopg import Connection
from psycopg.rows import DictRow
from pydantic import Field

from app import aas, rgs
from app.errors import ApiError
from app.ias import Conn, Principal, check_authorization, current_principal
from app.models import ApiModel

router = APIRouter()


# --- Commitment (OD-6) ------------------------------------------------------------------


def canonical_payload(
    credential_id: str, issuer_id: str, holder_ref: str, title: str, completed_at: date, criteria: str, skills: list[str]
) -> bytes:
    """OD-6: JSON with sorted keys and no whitespace, UTF-8. holderDisplayName and NIK are
    deliberately absent (NFR-02), so changing the display name never breaks integrity."""
    payload: dict[str, Any] = {
        "credentialId": credential_id,
        "issuerId": issuer_id,
        "holderRef": holder_ref,
        "program": {"title": title, "completedAt": completed_at.isoformat(), "criteria": criteria},
        "skills": sorted(skills),
    }
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def compute_commitment(canonical: bytes, nonce: bytes) -> str:
    """commitment = SHA-256(canonical JSON bytes || 32-byte nonce), as 0x-prefixed hex."""
    return "0x" + hashlib.sha256(canonical + nonce).hexdigest()


def commitment_of(conn: Connection[DictRow], credential: DictRow) -> str:
    """Recomputes a stored credential's commitment from its current off-chain rows (T13)."""
    skills = [r["skill_id"] for r in conn.execute(
        "SELECT skill_id FROM credential_skills WHERE credential_id = %s", (credential["credential_id"],)
    )]
    canonical = canonical_payload(
        credential["credential_id"], credential["issuer_id"], credential["holder_ref"],
        credential["program_title"], credential["completed_at"], credential["criteria"], skills,
    )
    return compute_commitment(canonical, bytes(credential["nonce"]))


# --- API-02 POST /credentials -----------------------------------------------------------


class Program(ApiModel):
    title: str = Field(min_length=1, max_length=200)
    completed_at: date
    criteria: str = Field(min_length=1, max_length=500)


class IssueCredentialRequest(ApiModel):
    holder_ref: str = Field(pattern=r"^HLD-[0-9]{4}-[0-9]{4}$")
    holder_display_name: str = Field(min_length=1, max_length=200)
    program: Program
    skills: list[Annotated[str, Field(pattern=r"^SK-[0-9]{3}$")]] = Field(min_length=1, max_length=30)


class CredentialIssued(ApiModel):
    credential_id: str
    issuer_id: str
    status: Literal["active"]
    commitment: str
    tx_hash: str
    issued_at: datetime


@router.post("/credentials", status_code=201, response_model=CredentialIssued, tags=["CIS"])
def issue_credential(
    body: IssueCredentialRequest,
    principal: Annotated[Principal, Depends(current_principal)],
    conn: Conn,
) -> CredentialIssued:
    """API-02: validates, stores metadata off-chain, anchors the commitment, audits, notifies."""
    issuer = check_authorization(principal, conn)  # T03 -> 403 ISSUER_NOT_AUTHORIZED

    skills = sorted(set(body.skills))
    known = {r["skill_id"] for r in conn.execute("SELECT skill_id FROM skills WHERE skill_id = ANY(%s)", (skills,))}
    missing = [s for s in skills if s not in known]
    if missing:
        raise ApiError(422, "SKILL_NOT_IN_CATALOG", f"Not in the skill catalog: {', '.join(missing)}.")
    if not conn.execute("SELECT 1 FROM accounts WHERE holder_ref = %s", (body.holder_ref,)).fetchone():
        # shortcut: reuses MALFORMED_REQUEST because the report names no code for an unknown holderRef.
        raise ApiError(400, "MALFORMED_REQUEST", f"Unknown holderRef {body.holder_ref}.")

    # T04: store metadata and compute the commitment.
    id_row = conn.execute("SELECT 'CRD-' || lpad(nextval('credential_seq')::text, 4, '0') AS id").fetchone()
    assert id_row is not None
    credential_id: str = id_row["id"]
    nonce = secrets.token_bytes(32)
    program = body.program
    commitment = compute_commitment(
        canonical_payload(
            credential_id, issuer["issuer_id"], body.holder_ref, program.title, program.completed_at, program.criteria, skills
        ),
        nonce,
    )
    row = conn.execute(
        "INSERT INTO credentials (credential_id, issuer_id, holder_ref, holder_display_name, program_title,"
        " completed_at, criteria, nonce, commitment) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING issued_at",
        (credential_id, issuer["issuer_id"], body.holder_ref, body.holder_display_name, program.title,
         program.completed_at, program.criteria, nonce, commitment),
    ).fetchone()
    assert row is not None
    with conn.cursor() as cur:
        cur.executemany(
            "INSERT INTO credential_skills (credential_id, skill_id) VALUES (%s, %s)",
            [(credential_id, s) for s in skills],
        )

    # T05: anchor on the registry. Any failure rolls back, so nothing is issued.
    try:
        tx_hash = rgs.issue_credential(credential_id, commitment, issuer["chain_account"])
    except rgs.RegistryUnavailable as exc:
        conn.rollback()
        raise ApiError(503, "REGISTRY_UNAVAILABLE", "The registry cannot be reached; no credential was issued.") from exc
    except rgs.RegistryError as exc:
        conn.rollback()
        if str(exc) in {"IssuerNotActive", "IssuerNotRegistered"}:
            raise ApiError(403, "ISSUER_NOT_AUTHORIZED", "The registry does not authorize this issuer.") from exc
        raise

    # T06: store txHash, audit, notify the holder (simulated email, OD-3).
    conn.execute("UPDATE credentials SET tx_hash = %s WHERE credential_id = %s", (tx_hash, credential_id))
    aas.record_audit(conn, principal.role, "issueCredential", credential_id, "success")
    conn.execute(
        "INSERT INTO notifications (holder_ref, subject, body) VALUES (%s, %s, %s)",
        (body.holder_ref, "New credential issued",
         f"{issuer['name']} issued credential {credential_id} for \"{program.title}\". Open ProofSkill to view and share it."),
    )
    conn.commit()
    return CredentialIssued(
        credential_id=credential_id,
        issuer_id=issuer["issuer_id"],
        status="active",
        commitment=commitment,
        tx_hash=tx_hash,
        issued_at=row["issued_at"],
    )


# --- API-03 GET /credentials/{credentialId} ---------------------------------------------


def load_credential(conn: Connection[DictRow], credential_id: str) -> DictRow:
    """The credential row, or 404 CREDENTIAL_NOT_FOUND."""
    credential = conn.execute("SELECT * FROM credentials WHERE credential_id = %s", (credential_id,)).fetchone()
    if credential is None:
        raise ApiError(404, "CREDENTIAL_NOT_FOUND", f"Credential {credential_id} does not exist.")
    return credential


def is_holder(principal: Principal, credential: DictRow) -> bool:
    return principal.role == "holder" and principal.holder_ref == credential["holder_ref"]


def is_original_issuer(principal: Principal, credential: DictRow) -> bool:
    return principal.role == "issuer_admin" and principal.issuer_id == credential["issuer_id"]


class IssuerRef(ApiModel):
    issuer_id: str
    name: str


class ProgramView(ApiModel):
    title: str
    completed_at: date
    criteria: str


class SkillRef(ApiModel):
    skill_id: str
    label: str


class ShareLinkSummary(ApiModel):
    link_id: str
    url: str
    scope: list[str]
    expires_at: datetime
    revoked_at: datetime | None


class CredentialView(ApiModel):
    credential_id: str
    issuer: IssuerRef
    holder_ref: str
    holder_display_name: str
    program: ProgramView
    skills: list[SkillRef]
    status: Literal["active", "revoked"]
    commitment: str
    tx_hash: str | None
    issued_at: datetime
    revoked_at: datetime | None
    revocation_reason: str | None
    share_links: list[ShareLinkSummary] | None  # holder only; the issuer never sees how it was shared


@router.get("/credentials/{credential_id}", response_model=CredentialView, tags=["CIS"])
def get_credential(
    credential_id: str,
    principal: Annotated[Principal, Depends(current_principal)],
    conn: Conn,
) -> CredentialView:
    """API-03: the holder or the original issuer reads a credential and its status (T07, T28).
    404 CREDENTIAL_NOT_FOUND if it does not exist, 403 NOT_CREDENTIAL_OWNER for anyone else (OD-1)."""
    credential = load_credential(conn, credential_id)
    holder = is_holder(principal, credential)
    if not holder and not is_original_issuer(principal, credential):
        raise ApiError(403, "NOT_CREDENTIAL_OWNER", "Only the holder or the original issuer can read this credential.")

    issuer = conn.execute("SELECT issuer_id, name FROM issuers WHERE issuer_id = %s", (credential["issuer_id"],)).fetchone()
    skills = conn.execute(
        "SELECT s.skill_id, s.label FROM credential_skills cs JOIN skills s USING (skill_id)"
        " WHERE cs.credential_id = %s ORDER BY s.skill_id",
        (credential_id,),
    ).fetchall()
    links = None
    if holder:
        rows = conn.execute(
            "SELECT link_id, share_token, scope, expires_at, revoked_at FROM share_links"
            " WHERE credential_id = %s ORDER BY link_id",
            (credential_id,),
        ).fetchall()
        links = [ShareLinkSummary(url=aas.share_url(r["share_token"]), **{k: r[k] for k in r if k != "share_token"}) for r in rows]
    return CredentialView(
        credential_id=credential_id,
        issuer=IssuerRef(**issuer) if issuer else IssuerRef(issuer_id=credential["issuer_id"], name=""),
        holder_ref=credential["holder_ref"],
        holder_display_name=credential["holder_display_name"],
        program=ProgramView(
            title=credential["program_title"], completed_at=credential["completed_at"], criteria=credential["criteria"]
        ),
        skills=[SkillRef(**s) for s in skills],
        status=credential["status"],
        commitment=credential["commitment"],
        tx_hash=credential["tx_hash"],
        issued_at=credential["issued_at"],
        revoked_at=credential["revoked_at"],
        revocation_reason=credential["revocation_reason"],
        share_links=links,
    )
