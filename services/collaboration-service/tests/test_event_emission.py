from __future__ import annotations

from uuid import uuid4

from fastapi.testclient import TestClient

from app import main
from services.shared import events


def _set_roles(roles: list[str]):
    def _verify(request):
        request.state.user = {"sub": "test-user", "realm_access": {"roles": roles}}

    return _verify


def _setup_auth(monkeypatch):
    monkeypatch.setattr(main, "verify_request", _set_roles(["developer"]))


def test_annotation_created_emits_event(monkeypatch):
    _setup_auth(monkeypatch)
    emitted: list[dict] = []

    monkeypatch.setattr("app.api.v1.annotations.resolve_user_id", lambda *_args, **_kwargs: uuid4())
    monkeypatch.setattr("app.api.v1.annotations.get_redis", lambda *_args, **_kwargs: None)

    def _fake_publish(_client, _stream, payload, **_kwargs):
        emitted.append(payload)
        return True, "1-0"

    monkeypatch.setattr("app.api.v1.annotations.publish_event", _fake_publish)

    client = TestClient(main.app)
    response = client.post(
        "/api/v1/annotations",
        json={
            "story_id": 42,
            "target_element": "header",
            "annotation_type": "comment",
            "content": "needs clarification",
        },
    )

    assert response.status_code == 200
    assert emitted
    assert emitted[0]["event_type"] == events.ANNOTATION_CREATED
    assert emitted[0]["metadata"]["annotation_type"] == "comment"


def test_comment_added_emits_event(monkeypatch):
    _setup_auth(monkeypatch)
    emitted: list[dict] = []

    monkeypatch.setattr("app.api.v1.comments.resolve_user_id", lambda *_args, **_kwargs: uuid4())
    monkeypatch.setattr("app.api.v1.comments.get_redis", lambda *_args, **_kwargs: None)

    def _fake_publish(_client, _stream, payload, **_kwargs):
        emitted.append(payload)
        return True, "1-0"

    monkeypatch.setattr("app.api.v1.comments.publish_event", _fake_publish)

    client = TestClient(main.app)
    response = client.post(
        "/api/v1/comments",
        json={"target_id": str(uuid4()), "content": "please add source"},
    )

    assert response.status_code == 200
    assert emitted
    assert emitted[0]["event_type"] == events.COMMENT_ADDED


def test_vote_cast_emits_event(monkeypatch):
    _setup_auth(monkeypatch)
    emitted: list[dict] = []

    monkeypatch.setattr("app.api.v1.votes.resolve_user_id", lambda *_args, **_kwargs: uuid4())
    monkeypatch.setattr("app.api.v1.votes.get_redis", lambda *_args, **_kwargs: None)

    def _fake_publish(_client, _stream, payload, **_kwargs):
        emitted.append(payload)
        return True, "1-0"

    monkeypatch.setattr("app.api.v1.votes.publish_event", _fake_publish)

    client = TestClient(main.app)
    response = client.post(
        "/api/v1/votes",
        json={"target_id": str(uuid4()), "value": 1},
    )

    assert response.status_code == 200
    assert emitted
    assert emitted[0]["event_type"] == events.VOTE_CAST
    assert emitted[0]["metadata"]["value"] == 1
