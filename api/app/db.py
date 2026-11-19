"""PostgreSQL access and the plain-SQL migration runner (A-03)."""

from collections.abc import Iterator
from pathlib import Path

import psycopg
from psycopg.rows import DictRow, dict_row

from app import config

MIGRATIONS = Path(__file__).resolve().parent.parent / "migrations"


def connect(url: str = config.DATABASE_URL) -> psycopg.Connection[DictRow]:
    return psycopg.connect(url, row_factory=dict_row)


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
    """Drops every table in the local database. Development and tests only."""
    conn.execute("DROP SCHEMA public CASCADE")
    conn.execute("CREATE SCHEMA public")
    conn.commit()
