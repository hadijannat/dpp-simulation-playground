from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health():
    response = client.get("/api/v2/health")
    assert response.status_code == 200
    assert response.json().get("status") == "ok"


def test_cors_preflight_allows_local_frontend():
    response = client.options(
        "/api/v2/journeys/runs",
        headers={
            "Origin": "http://127.0.0.1:4173",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type,x-dev-user,x-dev-roles",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://127.0.0.1:4173"
