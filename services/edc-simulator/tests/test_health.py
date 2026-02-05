from fastapi.testclient import TestClient
from app.main import app


def test_health():
    client = TestClient(app)
    resp = client.get("/api/v1/health")
    assert resp.status_code == 200
