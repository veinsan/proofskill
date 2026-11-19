"""ProofSkill REST API entry point. Every route lives under /api/v1 (report Tabel 9.1)."""

from fastapi import FastAPI

from app import errors, ias

API_PREFIX = "/api/v1"

app = FastAPI(
    title="ProofSkill API",
    version="0.1.0",
    openapi_url=f"{API_PREFIX}/openapi.json",
    docs_url=f"{API_PREFIX}/docs",
)
errors.install(app)
app.include_router(ias.router, prefix=API_PREFIX)
