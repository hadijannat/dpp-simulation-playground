from __future__ import annotations

from app.engine import event_consumer


def test_load_runtime_rules_uses_fallbacks_when_db_is_empty(monkeypatch):
    class _DummyDb:
        def close(self):
            return None

    monkeypatch.setattr(event_consumer, "SessionLocal", lambda: _DummyDb())
    monkeypatch.setattr(event_consumer, "load_active_point_rules", lambda _db: {})
    monkeypatch.setattr(event_consumer, "load_point_rules_from_yaml", lambda: {"story_completed": 25})
    monkeypatch.setattr(event_consumer, "_load_achievement_defs_from_db", lambda: [])
    monkeypatch.setattr(
        event_consumer,
        "load_achievements",
        lambda: [{"code": "story-complete", "criteria": {"event": "story_completed"}}],
    )
    event_consumer.invalidate_runtime_cache()

    point_rules, achievements = event_consumer._load_runtime_rules()

    assert point_rules == {"story_completed": 25}
    assert achievements and achievements[0]["code"] == "story-complete"


def test_invalidate_runtime_cache_resets_loaded_at():
    event_consumer._rules_cache["loaded_at"] = 123.0
    event_consumer.invalidate_runtime_cache()
    assert event_consumer._rules_cache["loaded_at"] == 0.0


def test_trim_stream_calls_xtrim_with_maxlen():
    class _Client:
        def __init__(self):
            self.calls = []

        def xtrim(self, stream, maxlen, approximate=True):
            self.calls.append((stream, maxlen, approximate))
            return 0

    client = _Client()
    event_consumer._trim_stream(client, "simulation.events", 100)
    assert client.calls == [("simulation.events", 100, True)]
