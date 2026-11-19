"""AAS Access & Audit service: audit trail (FR-10, NFR-07). Share links arrive in A-07."""

from psycopg import Connection
from psycopg.rows import DictRow


def record_audit(conn: Connection[DictRow], actor_role: str, operation: str, object_id: str | None, outcome: str) -> None:
    """recordAudit: time, actor role, operation, object ID, and outcome only, never payload content.
    Runs inside the caller's transaction, so it commits or rolls back with the operation."""
    conn.execute(
        "INSERT INTO audit_events (actor_role, operation, object_id, outcome) VALUES (%s, %s, %s, %s)",
        (actor_role, operation, object_id, outcome),
    )
