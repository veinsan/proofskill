"""Security headers on every API response (security check 2026-11-20)."""

from fastapi.testclient import TestClient

from app.main import app


def test_security_headers_on_api_responses() -> None:
    response = TestClient(app).get("/api/v1/openapi.json")
    assert response.status_code == 200
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["Referrer-Policy"] == "no-referrer"
