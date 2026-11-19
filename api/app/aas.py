"""AAS Access & Audit service: scoped share links (API-04, API-05, T08–T09) and the audit trail
(FR-10, NFR-07)."""

import secrets
from datetime import datetime
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query, Response
from psycopg import Connection
from psycopg.rows import DictRow

from app import cis, config
from app.errors import ApiError
from app.ias import Conn, Principal, check_authorization, current_principal, require_roles
from app.models import ApiModel

router = APIRouter()

# OD-4: the credential fields a holder may share, and the link lifetime bounds in hours.
SCOPE_FIELDS = ("holderDisplayName", "program.title", "completedAt", "program.criteria", "skills")
MIN_EXPIRY_HOURS, MAX_EXPIRY_HOURS = 1, 720


def record_audit(conn: Connection[DictRow], actor_role: str, operation: str, object_id: str | None, outcome: str) -> None:
    """recordAudit: time, actor role, operation, object ID, and outcome only, never payload content.
    Runs inside the caller's transaction, so it commits or rolls back with the operation."""
    conn.execute(
        "INSERT INTO audit_events (actor_role, operation, object_id, outcome) VALUES (%s, %s, %s, %s)",
        (actor_role, operation, object_id, outcome),
    )


def share_url(share_token: str) -> str:
    """Verifier route for a share token; usable as a LinkedIn Credential URL."""
    return f"{config.WEB_BASE_URL}/v/{share_token}"


def _require_holder(principal: Principal, credential: DictRow) -> None:
    if not cis.is_holder(principal, credential):
        raise ApiError(403, "NOT_CREDENTIAL_OWNER", "Only the holder of this credential can manage its share links.")


# --- API-04 POST /credentials/{credentialId}/share-links -------------------------------


class ShareLinkRequest(ApiModel):
    scope: list[str]
    expires_in_hours: int


class ShareLink(ApiModel):
    link_id: str
    share_token: str
    url: str
    scope: list[str]
    expires_at: datetime


@router.post("/credentials/{credential_id}/share-links", status_code=201, response_model=ShareLink, tags=["AAS"])
def create_share_link(
    credential_id: str,
    body: ShareLinkRequest,
    principal: Annotated[Principal, Depends(current_principal)],
    conn: Conn,
) -> ShareLink:
    """API-04: the holder picks the shared fields and lifetime; the scope stays on the server so a
    verifier cannot widen it (T08, T09). 422 INVALID_SCOPE outside the OD-4 limits."""
    credential = cis.load_credential(conn, credential_id)
    _require_holder(principal, credential)

    scope = list(dict.fromkeys(body.scope))  # drop duplicates, keep the holder's order
    unknown = [field for field in scope if field not in SCOPE_FIELDS]
    if not scope or unknown:
        allowed = ", ".join(SCOPE_FIELDS)
        raise ApiError(422, "INVALID_SCOPE", f"Scope must list one or more of: {allowed}. Unknown: {', '.join(unknown) or 'none'}.")
    if not MIN_EXPIRY_HOURS <= body.expires_in_hours <= MAX_EXPIRY_HOURS:
        raise ApiError(422, "INVALID_SCOPE", f"expiresInHours must be {MIN_EXPIRY_HOURS} to {MAX_EXPIRY_HOURS}.")

    share_token = "sk_" + secrets.token_hex(16)
    row = conn.execute(
        "INSERT INTO share_links (credential_id, share_token, scope, expires_at)"
        " VALUES (%s, %s, %s, now() + make_interval(hours => %s)) RETURNING link_id, expires_at",
        (credential_id, share_token, scope, body.expires_in_hours),
    ).fetchone()
    assert row is not None
    record_audit(conn, principal.role, "createShareLink", row["link_id"], "success")
    conn.commit()
    return ShareLink(
        link_id=row["link_id"], share_token=share_token, url=share_url(share_token), scope=scope, expires_at=row["expires_at"]
    )


# --- API-05 DELETE /share-links/{linkId} (optional) -------------------------------------


@router.delete("/share-links/{link_id}", status_code=204, tags=["AAS"])
def revoke_share_link(
    link_id: str,
    principal: Annotated[Principal, Depends(current_principal)],
    conn: Conn,
) -> Response:
    """API-05: the holder revokes a link; later verifications get 410 SHARE_LINK_EXPIRED.
    404 SHARE_LINK_NOT_FOUND, 403 NOT_CREDENTIAL_OWNER (OD-1). Revoking twice is a no-op."""
    link = conn.execute("SELECT * FROM share_links WHERE link_id = %s", (link_id,)).fetchone()
    if link is None:
        raise ApiError(404, "SHARE_LINK_NOT_FOUND", f"Share link {link_id} does not exist.")
    _require_holder(principal, cis.load_credential(conn, link["credential_id"]))
    if link["revoked_at"] is None:
        conn.execute("UPDATE share_links SET revoked_at = now() WHERE link_id = %s", (link_id,))
        record_audit(conn, principal.role, "revokeShareLink", link_id, "success")
        conn.commit()
    return Response(status_code=204)


# --- API-10 GET /audit-logs -------------------------------------------------------------

Operation = Literal[
    "issueCredential", "createShareLink", "revokeShareLink", "verifyCredential", "matchSkills", "revokeCredential"
]

# Maps each event's object ID (CRD-, SHL-, VER-, MAT-) to the credential it concerns, so an issuer
# sees only events about its own credentials.
_SCOPED_EVENTS = """
    FROM audit_events e
    JOIN credentials c ON c.credential_id = CASE
        WHEN e.object_id LIKE 'CRD-%%' THEN e.object_id
        WHEN e.object_id LIKE 'SHL-%%' THEN (SELECT credential_id FROM share_links WHERE link_id = e.object_id)
        WHEN e.object_id LIKE 'VER-%%' THEN (
            SELECT l.credential_id FROM verifications v JOIN share_links l USING (link_id)
            WHERE v.verification_id = e.object_id)
        WHEN e.object_id LIKE 'MAT-%%' THEN (
            SELECT l.credential_id FROM matchings m JOIN verifications v USING (verification_id)
            JOIN share_links l USING (link_id) WHERE m.matching_id = e.object_id)
    END
    WHERE c.issuer_id = %(issuer)s
      AND (%(operation)s::text IS NULL OR e.operation = %(operation)s)
      AND (%(since)s::timestamptz IS NULL OR e.time >= %(since)s)
      AND (%(until)s::timestamptz IS NULL OR e.time <= %(until)s)
"""


class AuditEvent(ApiModel):
    """report Tabel 8.5 AuditEvent: time, actor role, operation, object, outcome, never payload (NFR-07)."""

    time: datetime
    actor_role: str
    operation: str
    object_id: str | None
    outcome: str


class AuditLog(ApiModel):
    items: list[AuditEvent]
    total: int


@router.get("/audit-logs", response_model=AuditLog, tags=["AAS"])
def query_audit_log(
    principal: Annotated[Principal, Depends(require_roles("issuer_admin"))],
    conn: Conn,
    operation: Operation | None = None,
    since: Annotated[datetime | None, Query(alias="from")] = None,
    until: Annotated[datetime | None, Query(alias="to")] = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> AuditLog:
    """API-10: the issuer admin reads the audit trail of its own credentials, newest first,
    filtered by operation and time (FR-10, TC-13)."""
    issuer = check_authorization(principal, conn)
    params = {"issuer": issuer["issuer_id"], "operation": operation, "since": since, "until": until, "limit": limit, "offset": offset}
    total = conn.execute(f"SELECT count(*) AS n {_SCOPED_EVENTS}", params).fetchone()  # type: ignore[arg-type]
    rows = conn.execute(
        f"SELECT e.time, e.actor_role, e.operation, e.object_id, e.outcome {_SCOPED_EVENTS}"  # type: ignore[arg-type]
        " ORDER BY e.time DESC, e.event_id DESC LIMIT %(limit)s OFFSET %(offset)s",
        params,
    ).fetchall()
    return AuditLog(items=[AuditEvent(**row) for row in rows], total=total["n"] if total else 0)
