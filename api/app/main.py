"""ProofSkill REST API entry point. Every route lives under /api/v1 (report Tabel 9.1)."""

from collections.abc import Awaitable, Callable

from fastapi import FastAPI, Request, Response

from app import aas, ams, cis, css, errors, ias, scs, vrs

API_PREFIX = "/api/v1"

app = FastAPI(
    title="ProofSkill API",
    version="0.1.0",
    openapi_url=f"{API_PREFIX}/openapi.json",
    docs_url=f"{API_PREFIX}/docs",
)
errors.install(app)


@app.middleware("http")
async def security_headers(request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
    """No MIME sniffing, no framing, no referrer: the API serves JSON plus the Swagger docs page."""
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    return response



app.include_router(ias.router, prefix=API_PREFIX)
app.include_router(scs.router, prefix=API_PREFIX)
app.include_router(cis.router, prefix=API_PREFIX)
app.include_router(aas.router, prefix=API_PREFIX)
app.include_router(vrs.router, prefix=API_PREFIX)
app.include_router(css.router, prefix=API_PREFIX)
app.include_router(ams.router, prefix=API_PREFIX)
