"""Uniform error body {"error": {"code", "message", "requestId"}} (report Tabel 9.1, NFR-08).

Codes come only from ARCHITECTURE.md; never invent new ones here.
"""

import secrets

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


class ApiError(Exception):
    def __init__(self, status: int, code: str, message: str) -> None:
        super().__init__(message)
        self.status = status
        self.code = code
        self.message = message


def error_response(status: int, code: str, message: str) -> JSONResponse:
    request_id = "req_" + secrets.token_hex(8)
    return JSONResponse(status_code=status, content={"error": {"code": code, "message": message, "requestId": request_id}})


async def _api_error(_: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, ApiError)
    return error_response(exc.status, exc.code, exc.message)


async def _malformed(_: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, RequestValidationError)
    first = exc.errors()[0] if exc.errors() else {}
    where = ".".join(str(part) for part in first.get("loc", ()) if part != "body")
    return error_response(400, "MALFORMED_REQUEST", f"Invalid request: {where} {first.get('msg', '')}".strip())


def install(app: FastAPI) -> None:
    app.add_exception_handler(ApiError, _api_error)
    app.add_exception_handler(RequestValidationError, _malformed)
