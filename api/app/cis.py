"""CIS Credential Issuance service: API-02 issueCredential (T02–T06, FR-02, FR-03, FR-04)."""

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
