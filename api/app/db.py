"""PostgreSQL access and the plain-SQL migration runner (A-03)."""

from collections.abc import Iterator
from pathlib import Path

import psycopg
from psycopg.rows import DictRow, dict_row

from app import config

MIGRATIONS = Path(__file__).resolve().parent.parent / "migrations"


def connect(url: str = config.DATABASE_URL) -> psycopg.Connection[DictRow]:
    # Times leave the API in UTC (report Tabel 9.1), whatever the server's local time zone is.
    # No server-side prepared statements, which Supabase's transaction pooler cannot keep (B-01).
    return psycopg.connect(url, row_factory=dict_row, options="-c TimeZone=UTC", prepare_threshold=None)


def get_conn() -> Iterator[psycopg.Connection[DictRow]]:
    """FastAPI dependency: one connection per request; rolled back if the request raises."""
    with connect() as conn:
        yield conn


def migrate(conn: psycopg.Connection[DictRow]) -> list[str]:
    """Applies migrations/*.sql in name order, each once. Returns the names applied now."""
    conn.execute(
        "CREATE TABLE IF NOT EXISTS schema_migrations"
        " (name text PRIMARY KEY, applied_at timestamptz NOT NULL DEFAULT now())"
    )
    applied = {row["name"] for row in conn.execute("SELECT name FROM schema_migrations")}
    new: list[str] = []
    for path in sorted(MIGRATIONS.glob("*.sql")):
        if path.name in applied:
            continue
        conn.execute(path.read_text(encoding="utf-8"))  # type: ignore[arg-type]  # trusted repo file
        conn.execute("INSERT INTO schema_migrations (name) VALUES (%s)", (path.name,))
        new.append(path.name)
    conn.commit()
    return new


def reset(conn: psycopg.Connection[DictRow]) -> None:
    """Drops every table and sequence in the public schema: all ProofSkill data in that database.
    The schema itself stays, so Supabase keeps its grants on it (B-01). Development and tests only."""
    conn.execute(
        "DO $$ DECLARE r record; BEGIN"
        " FOR r IN SELECT tablename FROM pg_tables WHERE schemaname = 'public' LOOP"
        "  EXECUTE format('DROP TABLE public.%I CASCADE', r.tablename); END LOOP;"
        " FOR r IN SELECT sequence_name FROM information_schema.sequences WHERE sequence_schema = 'public' LOOP"
        "  EXECUTE format('DROP SEQUENCE public.%I CASCADE', r.sequence_name); END LOOP;"
        " END $$"
    )
    conn.commit()
