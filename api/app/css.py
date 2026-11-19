"""CSS Credential Status service: API-09 revokeCredential (T24–T27, FR-07, O-07).

API-11 createCorrectionVersion is specified only (FR-11 deferred) and is not built.
"""

from datetime import datetime
from typing import Annotated, Literal

from fastapi import APIRouter, Depends
from pydantic import Field

from app import aas, cis, rgs
from app.errors import ApiError
from app.ias import Conn, Principal, check_authorization, current_principal
from app.models import ApiModel

router = APIRouter()


class RevocationRequest(ApiModel):
    reason: str = Field(min_length=1, max_length=200)


class RevocationResult(ApiModel):
    credential_id: str
    status: Literal["revoked"]
    reason: str
    revoked_at: datetime
    tx_hash: str


@router.post("/credentials/{credential_id}/revocations", response_model=RevocationResult, tags=["CSS"])
def revoke_credential(
    credential_id: str,
    body: RevocationRequest,
    principal: Annotated[Principal, Depends(current_principal)],
    conn: Conn,
) -> RevocationResult:
    """API-09: only the original issuer revokes. The new status is a new registry transaction, so
    history is not overwritten, and the next verification reads REVOKED from the chain."""
    issuer = check_authorization(principal, conn)  # T25
    credential = cis.load_credential(conn, credential_id)
    if credential["issuer_id"] != issuer["issuer_id"]:
        raise ApiError(403, "ISSUER_NOT_AUTHORIZED", "Only the original issuer can revoke this credential.")
    if credential["status"] == "revoked":
        raise ApiError(409, "ALREADY_REVOKED", f"Credential {credential_id} is already revoked.")

    try:
        tx_hash = rgs.revoke_credential(credential_id, issuer["chain_account"])  # T26
    except rgs.RegistryUnavailable as exc:
        raise ApiError(503, "REGISTRY_UNAVAILABLE", "The registry cannot be written; the status did not change.") from exc
    except rgs.RegistryError as exc:
        if str(exc) == "AlreadyRevoked":  # the chain is the source of truth even if the row says active
            raise ApiError(409, "ALREADY_REVOKED", f"Credential {credential_id} is already revoked.") from exc
        if str(exc) == "NotOriginalIssuer":
            raise ApiError(403, "ISSUER_NOT_AUTHORIZED", "The registry refused this issuer.") from exc
        raise

    # T27: store the reason, audit, notify the holder (simulated email, OD-3).
    row = conn.execute(
        "UPDATE credentials SET status = 'revoked', revoked_at = now(), revocation_reason = %s"
        " WHERE credential_id = %s RETURNING revoked_at",
        (body.reason, credential_id),
    ).fetchone()
    assert row is not None
    aas.record_audit(conn, principal.role, "revokeCredential", credential_id, "success")
    conn.execute(
        "INSERT INTO notifications (holder_ref, subject, body) VALUES (%s, %s, %s)",
        (credential["holder_ref"], "Credential revoked",
         f"{issuer['name']} revoked credential {credential_id}. Reason: {body.reason}"),
    )
    conn.commit()
    return RevocationResult(
        credential_id=credential_id, status="revoked", reason=body.reason, revoked_at=row["revoked_at"], tx_hash=tx_hash
    )
