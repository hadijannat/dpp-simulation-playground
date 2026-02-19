from __future__ import annotations

from datetime import datetime, timedelta, timezone

from services.shared.models.event_log import EventLog


PREFIX = "/api/v2/core/events"


def _seed_event(db_session, **kwargs):
    defaults = {
        "event_id": kwargs.get("event_id", "evt-default"),
        "event_type": kwargs.get("event_type", "story_step_completed"),
        "user_id": kwargs.get("user_id", "user-1"),
        "source_service": kwargs.get("source_service", "simulation-engine"),
        "version": kwargs.get("version", "1"),
        "session_id": kwargs.get("session_id"),
        "run_id": kwargs.get("run_id"),
        "request_id": kwargs.get("request_id"),
        "event_timestamp": kwargs.get("event_timestamp", datetime.now(timezone.utc)),
        "stream": kwargs.get("stream", "simulation.events"),
        "stream_message_id": kwargs.get("stream_message_id"),
        "published": kwargs.get("published", True),
        "publish_error": kwargs.get("publish_error"),
        "metadata_": kwargs.get("metadata", {}),
        "payload": kwargs.get("payload", {"event_type": kwargs.get("event_type", "story_step_completed")}),
    }
    row = EventLog(**defaults)
    db_session.add(row)
    db_session.commit()
    return row


def test_events_requires_session_or_run_filter(client):
    response = client.get(PREFIX)
    assert response.status_code == 422
    assert response.json()["detail"] == "Either session_id or run_id is required"


def test_events_list_by_session_id(client, db_session):
    now = datetime.now(timezone.utc)
    _seed_event(
        db_session,
        event_id="evt-1",
        session_id="sess-1",
        run_id="run-1",
        event_timestamp=now,
    )
    _seed_event(
        db_session,
        event_id="evt-2",
        session_id="sess-1",
        run_id="run-2",
        event_type="story_completed",
        event_timestamp=now + timedelta(seconds=10),
    )
    _seed_event(
        db_session,
        event_id="evt-3",
        session_id="sess-2",
        run_id="run-1",
        event_timestamp=now + timedelta(seconds=20),
    )

    response = client.get(f"{PREFIX}?session_id=sess-1&limit=10&offset=0")
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 2
    assert body["limit"] == 10
    assert body["offset"] == 0
    assert len(body["items"]) == 2
    assert {item["event_id"] for item in body["items"]} == {"evt-1", "evt-2"}
    assert all(item["session_id"] == "sess-1" for item in body["items"])


def test_events_list_by_run_and_source_filter(client, db_session):
    now = datetime.now(timezone.utc)
    _seed_event(
        db_session,
        event_id="evt-4",
        run_id="run-9",
        session_id="sess-9",
        source_service="simulation-engine",
        event_timestamp=now,
    )
    _seed_event(
        db_session,
        event_id="evt-5",
        run_id="run-9",
        session_id="sess-9",
        source_service="edc-simulator",
        event_timestamp=now + timedelta(seconds=5),
    )

    response = client.get(f"{PREFIX}?run_id=run-9&source_service=edc-simulator")
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert len(body["items"]) == 1
    assert body["items"][0]["event_id"] == "evt-5"
    assert body["items"][0]["source_service"] == "edc-simulator"


def test_events_enforce_limit_bounds(client, db_session):
    for index in range(3):
        _seed_event(
            db_session,
            event_id=f"evt-limit-{index}",
            session_id="sess-limit",
            run_id="run-limit",
            event_timestamp=datetime.now(timezone.utc) + timedelta(seconds=index),
        )

    response = client.get(f"{PREFIX}?session_id=sess-limit&limit=999&offset=-10")
    assert response.status_code == 200
    body = response.json()
    assert body["limit"] == 200
    assert body["offset"] == 0
    assert body["total"] == 3
    assert len(body["items"]) == 3
