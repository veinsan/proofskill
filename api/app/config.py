"""Runtime settings read from the environment. Defaults match .env.example."""

import os
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://proofskill@127.0.0.1:5433/proofskill")
# Folder holding libpq.dll on Windows (same variable as scripts/db.ps1).
PG_BIN = os.environ.get("PG_BIN", r"C:\Program Files\PostgreSQL\17\bin")
CHAIN_RPC_URL =os.environ.get("CHAIN_RPC_URL", "http://127.0.0.1:8545")
# Written by `pnpm deploy:local` in contracts/: registry address, owner, and ABI.
REGISTRY_DEPLOYMENT = Path(
    os.environ.get("REGISTRY_DEPLOYMENT", _REPO / "contracts" / "deployments" / "localhost.json")
)
