import os
import shutil
import subprocess
from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app import db  # first: app/__init__.py puts libpq on PATH before psycopg loads
from app import config, rgs, seed
from app.main import app

TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL", "postgresql://proofskill@127.0.0.1:5433/proofskill_test"
)
CONTRACTS = Path(__file__).resolve().parents[2] / "contracts"
TEST_DEPLOYMENT = CONTRACTS / "deployments" / "pytest.json"


def _ensure_test_database() -> None:
    info = db.psycopg.conninfo.conninfo_to_dict(TEST_DATABASE_URL)
    admin_url = db.psycopg.conninfo.make_conninfo(TEST_DATABASE_URL, dbname="postgres")
    with db.psycopg.connect(admin_url, autocommit=True) as admin:
        exists = admin.execute("SELECT 1 FROM pg_database WHERE datname = %s", (info["dbname"],)).fetchone()
        if not exists:
            admin.execute(f'CREATE DATABASE "{info["dbname"]}"')  # type: ignore[arg-type]  # name from local config


@pytest.fixture(scope="session")
def registry() -> Iterator[Path]:
    """Deploys a fresh ProofSkillRegistry to the running Hardhat node for this test session,
    so on-chain state from earlier runs cannot leak in. Restores the dev deployment after."""
    pnpm = shutil.which("pnpm")
    assert pnpm, "pnpm is needed to deploy the test registry"
    subprocess.run(
        [pnpm, "exec", "hardhat", "run", "scripts/deploy.ts", "--network", "localhost"],
        cwd=CONTRACTS,
        env={**os.environ, "DEPLOYMENT_OUT": str(TEST_DEPLOYMENT)},
        check=True,
        capture_output=True,
    )
    previous = config.REGISTRY_DEPLOYMENT
    config.REGISTRY_DEPLOYMENT = TEST_DEPLOYMENT
    rgs._deployment.cache_clear()
    yield TEST_DEPLOYMENT
    config.REGISTRY_DEPLOYMENT = previous
    rgs._deployment.cache_clear()


@pytest.fixture
def chain(registry: Path) -> Iterator[None]:
    """Reverts the chain after each test (Hardhat evm_snapshot), just as `conn` resets the database."""
    snapshot = rgs._rpc("evm_snapshot", [])
    yield
    rgs._rpc("evm_revert", [snapshot])


@pytest.fixture
def conn() -> Iterator[db.psycopg.Connection[db.DictRow]]:
    """An empty test database (separate from the dev database), reset for every test."""
    _ensure_test_database()
    with db.connect(TEST_DATABASE_URL) as connection:
        db.reset(connection)
        yield connection


@pytest.fixture
def client(conn: db.psycopg.Connection[db.DictRow], chain: None) -> Iterator[TestClient]:
    """The API on a migrated, seeded test database whose issuers are on the test registry."""
    db.migrate(conn)
    seed.seed(conn)
    seed.register_issuers_on_chain(conn)

    def test_conn() -> Iterator[db.psycopg.Connection[db.DictRow]]:
        with db.connect(TEST_DATABASE_URL) as connection:
            yield connection

    app.dependency_overrides[db.get_conn] = test_conn
    yield TestClient(app)
    app.dependency_overrides.clear()


ISSUE_REQUEST = {  # report API-02 example payload, synthetic
    "holderRef": "HLD-2026-0007",
    "holderDisplayName": "Peserta Contoh A",
    "program": {
        "title": "Pelatihan Keamanan Aplikasi Web Dasar",
        "completedAt": "2026-10-20",
        "criteria": "Kehadiran minimal 80 persen dan lulus proyek akhir",
    },
    "skills": ["SK-014", "SK-021", "SK-033"],
}


def issue(client: TestClient, issuer_admin: str = "admin.iss001", **overrides: object) -> dict[str, object]:
    """Issues the sample credential through API-02 and returns the 201 body."""
    response = client.post("/api/v1/credentials", json={**ISSUE_REQUEST, **overrides}, headers=login(client, issuer_admin))
    assert response.status_code == 201, response.text
    body: dict[str, object] = response.json()
    return body


def share(client: TestClient, credential_id: str, scope: list[str] | None = None, hours: int = 72) -> dict[str, object]:
    """Creates a share link as the sample holder through API-04 and returns the 201 body."""
    body = {"scope": scope or ["program.title", "completedAt", "skills"], "expiresInHours": hours}
    response = client.post(f"/api/v1/credentials/{credential_id}/share-links", json=body, headers=login(client, "holder.a"))
    assert response.status_code == 201, response.text
    link: dict[str, object] = response.json()
    return link


def login(client: TestClient, username: str) -> dict[str, str]:
    """Authorization header for a seeded account."""
    response = client.post("/api/v1/auth/token", json={"username": username, "password": seed.DEMO_PASSWORD})
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['accessToken']}"}
