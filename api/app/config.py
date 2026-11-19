"""Runtime settings read from the environment. Defaults match .env.example."""

import os
import secrets
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://proofskill@127.0.0.1:5433/proofskill")
# Folder holding libpq.dll on Windows (same variable as scripts/db.ps1).
PG_BIN = os.environ.get("PG_BIN", r"C:\Program Files\PostgreSQL\17\bin")
CHAIN_RPC_URL =os.environ.get("CHAIN_RPC_URL", "http://127.0.0.1:8545")
# shortcut: without JWT_SECRET each API process signs with a random key, so tokens die on
# restart. Set JWT_SECRET (never committed) if tokens must survive restarts.
JWT_SECRET = os.environ.get("JWT_SECRET") or secrets.token_urlsafe(32)
# Origin of the web app; share links point to its verifier route /v/<shareToken> (report 9.3).
WEB_BASE_URL = os.environ.get("WEB_BASE_URL", "http://localhost:3000")
# Written by `pnpm deploy:local` in contracts/: registry address, owner, and ABI.
REGISTRY_DEPLOYMENT = Path(
    os.environ.get("REGISTRY_DEPLOYMENT", _REPO / "contracts" / "deployments" / "localhost.json")
)
