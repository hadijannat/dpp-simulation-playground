from __future__ import annotations

from types import SimpleNamespace

from fastapi.testclient import TestClient

from app import main


def _set_roles(roles: list[str]):
    def _verify(request):
        request.state.user = {"realm_access": {"roles": roles}}

    return _verify


def test_leaderboard_rejects_invalid_window(monkeypatch):
    monkeypatch.setattr(main, "verify_request", _set_roles(["developer"]))
    client = TestClient(main.app)

    response = client.get("/api/v1/leaderboard?window=yearly")

    assert response.status_code == 422
    assert "window must be one of" in response.json()["detail"]


def test_windowed_leaderboard_supports_role_filter(monkeypatch):
    monkeypatch.setattr(main, "verify_request", _set_roles(["developer"]))

    events = [
        SimpleNamespace(event_type="story_completed", user_id="u-1", metadata_={"role": "manufacturer"}),
        SimpleNamespace(event_type="story_completed", user_id="u-2", metadata_={"role": "regulator", "difficulty": "expert"}),
        SimpleNamespace(event_type="story_completed", user_id="u-1", metadata_={"role": "manufacturer", "difficulty": "expert"}),
    ]

    monkeypatch.setattr("app.api.v1.leaderboard._load_point_rules", lambda _db: {"story_completed": 25})
    monkeypatch.setattr("app.api.v1.leaderboard._load_events_for_window", lambda _db, **_kwargs: events)

    client = TestClient(main.app)

    full_resp = client.get("/api/v1/leaderboard?window=weekly")
    assert full_resp.status_code == 200
    full_items = full_resp.json()["items"]
    assert full_items[0]["user_id"] == "u-1"
    assert full_items[0]["total_points"] == 75
    assert full_items[1]["user_id"] == "u-2"
    assert full_items[1]["total_points"] == 55

    filtered_resp = client.get("/api/v1/leaderboard?window=weekly&role=manufacturer")
    assert filtered_resp.status_code == 200
    filtered_items = filtered_resp.json()["items"]
    assert len(filtered_items) == 1
    assert filtered_items[0]["user_id"] == "u-1"
    assert filtered_items[0]["total_points"] == 75
    assert filtered_resp.json()["role"] == "manufacturer"
