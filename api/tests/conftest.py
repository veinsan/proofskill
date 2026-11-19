import os
from collections.abc import Iterator

import pytest

from app import db  # first: app/__init__.py puts libpq on PATH before psycopg loads

TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL", "postgresql://proofskill@127.0.0.1:5433/proofskill_test"
)


def _ensure_test_database() -> None:
    info = db.psycopg.conninfo.conninfo_to_dict(TEST_DATABASE_URL)
    admin_url = db.psycopg.conninfo.make_conninfo(TEST_DATABASE_URL, dbname="postgres")
    with db.psycopg.connect(admin_url, autocommit=True) as admin:
        exists = admin.execute("SELECT 1 FROM pg_database WHERE datname = %s", (info["dbname"],)).fetchone()
        if not exists:
            admin.execute(f'CREATE DATABASE "{info["dbname"]}"')  # type: ignore[arg-type]  # name from local config


@pytest.fixture
def conn() -> Iterator[db.psycopg.Connection[db.DictRow]]:
    """An empty test database (separate from the dev database), reset for every test."""
    _ensure_test_database()
    with db.connect(TEST_DATABASE_URL) as connection:
        db.reset(connection)
        yield connection
