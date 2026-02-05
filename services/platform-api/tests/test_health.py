from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health():
    response = client.get("/api/v2/health")
    assert response.status_code == 200
    assert response.json().get("status") == "ok"
