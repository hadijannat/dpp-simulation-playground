# Adding Stories

This runbook covers how to add or modify simulation stories in a safe, non-breaking way.

## 1) Where stories live

- Story YAML files: `services/simulation-engine/data/stories/*.yaml`
- Validation schema: `services/simulation-engine/app/schemas/story_schema.py`
- Step plugin registry: `services/simulation-engine/app/core/step_executor.py`

## 2) Required story fields

Each story entry should include:

- `story_version` (integer, `>= 1`)
- `code` (stable unique identifier)
- `title`
- `steps` (list)

Supported optional fields:

- `description`
- `inputs`
- `validations`
- `role_constraints` (or `roles` alias)
- `difficulty`

## 3) Step actions

Use only registered step actions unless you add a plugin first. Current built-ins include:

- `user.input`
- `compliance.check`
- `edc.negotiate`
- `edc.transfer`
- `aas.create`
- `aas.submodel.add`
- `aas.submodel.patch`
- `aas.update`
- `aasx.upload`
- `api.call`
- `json_patch`

If a step action is unknown, execution returns `status=unknown_action`.

## 4) Authoring checklist

1. Add/update YAML in `services/simulation-engine/data/stories/`.
2. Keep `code` stable for existing stories (treat as API contract).
3. For breaking behavior changes, bump `story_version`.
4. Ensure `steps[*].action` maps to a registered plugin.
5. Add or update tests for story-specific behavior.

## 5) Validate before commit

Run:

```bash
make story-lint
pytest services/simulation-engine/tests -q
```

If you touched shared contracts or API responses, also run:

```bash
make openapi
make contract-check
```

## 6) Smoke test story manually

Use the platform API journey flow:

1. `POST /api/v2/journeys/runs`
2. `POST /api/v2/journeys/runs/{run_id}/steps/{step_id}/execute`
3. `GET /api/v2/journeys/runs/{run_id}`

Confirm:

- Step status transitions are deterministic.
- No duplicate side effects for retried calls with same idempotency key.
- Event stream emits expected events.

## 7) Rollback strategy

If a story rollout fails:

1. Revert the story YAML commit.
2. Re-run `make story-lint`.
3. Re-run affected tests.
4. If needed, keep old story with same `code` and increment `story_version` only for fixed variant.
