from fastapi.testclient import TestClient

from app.main import app


def test_openapi_served_under_api_v1() -> None:
    response = TestClient(app).get("/api/v1/openapi.json")
    assert response.status_code == 200
    assert response.json()["info"]["title"] == "ProofSkill API"
