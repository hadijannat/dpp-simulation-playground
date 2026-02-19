from __future__ import annotations

import pytest
from fastapi import HTTPException

from app.core.session_state import (
    assert_transition_allowed,
    ensure_session_active,
    get_lifecycle_state,
    set_lifecycle_state,
)


def test_lifecycle_defaults_to_active():
    assert get_lifecycle_state({}, is_active=True) == "active"


def test_set_lifecycle_state_sets_timestamp():
    next_state = set_lifecycle_state({}, "paused")
    assert next_state["lifecycle_state"] == "paused"
    assert "state_updated_at" in next_state


def test_invalid_transition_raises_conflict():
    with pytest.raises(HTTPException) as exc:
        assert_transition_allowed("completed", "active")
    assert exc.value.status_code == 409


def test_ensure_session_active_rejects_paused():
    with pytest.raises(HTTPException) as exc:
        ensure_session_active({"lifecycle_state": "paused"}, is_active=False)
    assert exc.value.status_code == 409
