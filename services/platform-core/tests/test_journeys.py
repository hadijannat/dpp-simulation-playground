"""Tests for the journeys API routes on platform-core.

Covers:
- GET  /api/v2/core/journeys/templates          (list templates)
- GET  /api/v2/core/journeys/templates/{code}    (get template / 404)
- POST /api/v2/core/journeys/runs                (create run)
- GET  /api/v2/core/journeys/runs/{run_id}       (get run)
- POST /api/v2/core/journeys/runs/{run_id}/steps/{step_id}/execute (execute step)
"""
from __future__ import annotations

from uuid import uuid4


PREFIX = "/api/v2/core/journeys"


def test_list_templates_returns_empty_when_no_templates(client):
    response = client.get(f"{PREFIX}/templates")
    assert response.status_code == 200
    body = response.json()
    assert body == {"items": []}


def test_list_templates_returns_seeded_templates(client, seed_template):
    template, _steps = seed_template
    response = client.get(f"{PREFIX}/templates")
    assert response.status_code == 200
    body = response.json()
    assert len(body["items"]) == 1
    item = body["items"][0]
    assert item["code"] == "manufacturer-core-e2e"
    assert item["name"] == "Manufacturer Core E2E"
    assert item["is_active"] is True


def test_get_template_returns_404_for_unknown_code(client):
    response = client.get(f"{PREFIX}/templates/nonexistent-code")
    assert response.status_code == 404
    body = response.json()
    assert "nonexistent-code" in body["detail"]


def test_get_template_returns_template_with_steps(client, seed_template):
    template, steps = seed_template
    response = client.get(f"{PREFIX}/templates/{template.code}")
    assert response.status_code == 200
    body = response.json()
    assert body["code"] == template.code
    assert len(body["steps"]) == 2
    step_keys = [s["step_key"] for s in body["steps"]]
    assert "create-product" in step_keys
    assert "submit-compliance" in step_keys


def test_create_run_with_valid_template(client, seed_template):
    template, _steps = seed_template
    response = client.post(
        f"{PREFIX}/runs",
        json={"template_code": template.code, "role": "manufacturer", "locale": "en"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["template_code"] == template.code
    assert body["role"] == "manufacturer"
    assert body["locale"] == "en"
    assert body["status"] == "active"
    assert body["id"]  # a UUID string
    assert body["current_step"] == "create-product"


def test_create_run_returns_404_for_unknown_template(client):
    response = client.post(
        f"{PREFIX}/runs",
        json={"template_code": "does-not-exist", "role": "manufacturer"},
    )
    assert response.status_code == 404
    assert "does-not-exist" in response.json()["detail"]


def test_get_run_returns_run_data(client, seed_template):
    template, _steps = seed_template
    create_resp = client.post(
        f"{PREFIX}/runs",
        json={"template_code": template.code, "role": "manufacturer"},
    )
    assert create_resp.status_code == 200
    run_id = create_resp.json()["id"]

    response = client.get(f"{PREFIX}/runs/{run_id}")
    assert response.status_code == 200
    body = response.json()
    assert body["id"] == run_id
    assert body["template_code"] == template.code
    assert body["role"] == "manufacturer"
    assert body["status"] == "active"
    assert isinstance(body["steps"], list)


def test_get_run_returns_404_for_unknown_id(client):
    fake_id = str(uuid4())
    response = client.get(f"{PREFIX}/runs/{fake_id}")
    assert response.status_code == 404
    assert "Run not found" in response.json()["detail"]


def test_execute_step_returns_step_result(client, seed_template):
    template, steps = seed_template
    # Create a run first
    create_resp = client.post(
        f"{PREFIX}/runs",
        json={"template_code": template.code, "role": "manufacturer"},
    )
    assert create_resp.status_code == 200
    run_id = create_resp.json()["id"]

    # Execute the first step
    step_id = steps[0].step_key  # "create-product"
    response = client.post(
        f"{PREFIX}/runs/{run_id}/steps/{step_id}/execute",
        json={"payload": {"product_name": "Battery"}, "metadata": {}},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["run_id"] == run_id
    assert body["execution"]["step_id"] == step_id
    assert body["execution"]["status"] == "completed"
    assert body["execution"]["payload"] == {"product_name": "Battery"}
    # After executing step 0, next_step should be step 1
    assert body["next_step"] == steps[1].step_key


def test_execute_step_advances_to_done_on_last_step(client, seed_template):
    template, steps = seed_template
    create_resp = client.post(
        f"{PREFIX}/runs",
        json={"template_code": template.code, "role": "manufacturer"},
    )
    run_id = create_resp.json()["id"]

    # Execute step 0
    client.post(
        f"{PREFIX}/runs/{run_id}/steps/{steps[0].step_key}/execute",
        json={"payload": {}, "metadata": {}},
    )
    # Execute step 1 (last step)
    response = client.post(
        f"{PREFIX}/runs/{run_id}/steps/{steps[1].step_key}/execute",
        json={"payload": {}, "metadata": {}},
    )
    assert response.status_code == 200
    assert response.json()["next_step"] == "done"


def test_execute_step_returns_404_for_unknown_run(client):
    fake_id = str(uuid4())
    response = client.post(
        f"{PREFIX}/runs/{fake_id}/steps/some-step/execute",
        json={"payload": {}, "metadata": {}},
    )
    assert response.status_code == 404
    assert "Run not found" in response.json()["detail"]
