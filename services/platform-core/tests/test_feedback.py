"""Tests for the feedback CSAT API route on platform-core.

Covers:
- POST /api/v2/core/feedback/csat  (create feedback entry)
- POST /api/v2/core/feedback/csat  (response contains id and created_at)
"""
from __future__ import annotations


PREFIX = "/api/v2/core/feedback"


def test_submit_csat_creates_feedback(client):
    """POST /csat creates a CSAT feedback entry and returns it."""
    response = client.post(
        f"{PREFIX}/csat",
        json={
            "score": 4,
            "locale": "de",
            "role": "manufacturer",
            "flow": "manufacturer-core-e2e",
            "comment": "Great experience",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["score"] == 4
    assert body["locale"] == "de"
    assert body["role"] == "manufacturer"
    assert body["flow"] == "manufacturer-core-e2e"
    assert body["comment"] == "Great experience"


def test_submit_csat_returns_id_and_created_at(client):
    """The response must include an ``id`` (UUID string) and ``created_at``
    ISO-formatted timestamp."""
    response = client.post(
        f"{PREFIX}/csat",
        json={
            "score": 3,
            "role": "developer",
            "flow": "developer-onboarding",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert "id" in body
    assert body["id"]  # non-empty
    assert "created_at" in body
    assert body["created_at"]  # non-empty


def test_submit_csat_defaults_locale_and_flow(client):
    """When optional fields are omitted the endpoint should apply defaults."""
    response = client.post(
        f"{PREFIX}/csat",
        json={"score": 5, "role": "admin"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["locale"] == "en"
    assert body["flow"] == "manufacturer-core-e2e"


def test_submit_csat_rejects_out_of_range_score(client):
    """Score must be between 1 and 5."""
    response = client.post(
        f"{PREFIX}/csat",
        json={"score": 0, "role": "manufacturer"},
    )
    assert response.status_code == 422

    response = client.post(
        f"{PREFIX}/csat",
        json={"score": 6, "role": "manufacturer"},
    )
    assert response.status_code == 422
