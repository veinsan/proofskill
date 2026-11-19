"""ProofSkill REST API entry point. Every route lives under /api/v1 (report Tabel 9.1)."""

from fastapi import FastAPI

from app import aas, ams, cis, css, errors, ias, scs, vrs

API_PREFIX = "/api/v1"

app = FastAPI(
    title="ProofSkill API",
    version="0.1.0",
    openapi_url=f"{API_PREFIX}/openapi.json",
    docs_url=f"{API_PREFIX}/docs",
)
errors.install(app)
app.include_router(ias.router, prefix=API_PREFIX)
app.include_router(scs.router, prefix=API_PREFIX)
app.include_router(cis.router, prefix=API_PREFIX)
app.include_router(aas.router, prefix=API_PREFIX)
app.include_router(vrs.router, prefix=API_PREFIX)
app.include_router(css.router, prefix=API_PREFIX)
app.include_router(ams.router, prefix=API_PREFIX)
