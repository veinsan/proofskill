"""A-03 completion criteria: migrations apply to an empty database, the synthetic seed loads,
and the database issuers match the registry issuers. Needs the local PostgreSQL cluster, the
Hardhat node, and `pnpm deploy:local` (see CLAUDE.md)."""

from app import db, rgs, seed


def test_migrations_apply_once_to_an_empty_database(conn: db.psycopg.Connection[db.DictRow]) -> None:
    assert db.migrate(conn) == ["001_init.sql", "002_enable_rls.sql"]
    assert db.migrate(conn) == []

    columns = {row["column_name"] for row in conn.execute("SELECT column_name FROM information_schema.columns")}
    assert "nik" not in columns  # NFR-02: no national ID anywhere off-chain either


def test_b01_every_table_has_row_level_security(conn: db.psycopg.Connection[db.DictRow]) -> None:
    """On Supabase, RLS with no policies keeps the public Data API out of every table."""
    db.migrate(conn)
    tables = conn.execute(
        "SELECT relname, relrowsecurity FROM pg_class WHERE relnamespace = 'public'::regnamespace AND relkind = 'r'"
    ).fetchall()
    assert len(tables) == 11  # ten from 001_init.sql plus schema_migrations
    assert [t["relname"] for t in tables if not t["relrowsecurity"]] == []


def test_b01_reset_empties_the_schema_but_keeps_it(conn: db.psycopg.Connection[db.DictRow]) -> None:
    db.migrate(conn)
    db.reset(conn)
    left = conn.execute(
        "SELECT count(*) AS n FROM pg_class WHERE relnamespace = 'public'::regnamespace AND relkind IN ('r', 'S')"
    ).fetchone()
    assert left == {"n": 0}
    assert conn.execute("SELECT to_regnamespace('public') IS NOT NULL AS kept").fetchone() == {"kept": True}


def test_seed_loads_synthetic_rows_and_can_run_again(conn: db.psycopg.Connection[db.DictRow]) -> None:
    db.migrate(conn)
    seed.seed(conn)
    seed.seed(conn)

    count = {t: conn.execute(f"SELECT count(*) AS n FROM {t}").fetchone()["n"] for t in ("issuers", "accounts", "skills")}  # type: ignore[index, arg-type]
    assert count == {"issuers": 2, "accounts": 8, "skills": 15}

    accounts = conn.execute("SELECT role, holder_ref, password_hash FROM accounts").fetchall()
    assert {a["role"] for a in accounts} == {"platform_admin", "issuer_admin", "holder", "verifier"}
    assert {a["holder_ref"] for a in accounts if a["holder_ref"]} == {"HLD-2026-0007", "HLD-2026-0008"}
    assert all(a["password_hash"].startswith("scrypt$") for a in accounts)


def test_database_issuers_match_registry_issuers(conn: db.psycopg.Connection[db.DictRow], chain: None) -> None:
    db.migrate(conn)
    seed.seed(conn)
    seed.register_issuers_on_chain(conn)

    for row in conn.execute("SELECT issuer_id, chain_account FROM issuers"):
        assert rgs.issuer_account(row["issuer_id"]) == row["chain_account"].lower()
    assert rgs.issuer_account("ISS-404") is None
