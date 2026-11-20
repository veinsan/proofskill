"""Runtime settings read from the environment. Defaults match .env.example."""

import os
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://proofskill@127.0.0.1:5433/proofskill")
# Folder holding libpq.dll on Windows (same variable as scripts/db.ps1).
PG_BIN = os.environ.get("PG_BIN", r"C:\Program Files\PostgreSQL\17\bin")
CHAIN_RPC_URL = os.environ.get("CHAIN_RPC_URL", "http://127.0.0.1:8545")
# B-03, OD-12 custodial default: testnet keys RGS signs with, from the untracked .env.testnet or a
# Render secret, never committed. ISSUER_KEY_ISS_001 is ISS-001's key. Unset locally, where the
# Hardhat node's unlocked test accounts send the transactions.
REGISTRY_OWNER_KEY = os.environ.get("REGISTRY_OWNER_KEY", "")
ISSUER_KEYS = {
    name.removeprefix("ISSUER_KEY_").replace("_", "-"): key
    for name, key in os.environ.items()
    if name.startswith("ISSUER_KEY_") and key
}
# B-02: Supabase Auth holds the accounts. The URL and the publishable (anon) key are needed for
# API-00 sign-in and the JWKS that verifies tokens, locally as well. The service-role key and the
# accounts' password are used only by the seed to create the users; neither is ever committed.
SUPABASE_URL = os.environ.get("SUPABASE_URL", "").rstrip("/")
SUPABASE_ANON_KEY = os.environ.get("SUPABASE_ANON_KEY", "")
SUPABASE_SERVICE_ROLE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
SEED_PASSWORD = os.environ.get("SEED_PASSWORD", "")
# Gemini API key for AMS embeddings (B-04). Never committed. Unset switches the AI off (TC-10).
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
# Origin of the web app; share links point to its verifier route /v/<shareToken> (report 9.3).
WEB_BASE_URL = os.environ.get("WEB_BASE_URL", "http://localhost:3000")
# Written by `pnpm deploy:local` in contracts/: registry address, owner, and ABI.
REGISTRY_DEPLOYMENT = Path(
    os.environ.get("REGISTRY_DEPLOYMENT", _REPO / "contracts" / "deployments" / "localhost.json")
)
