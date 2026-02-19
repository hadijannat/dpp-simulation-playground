# Step Failure Debug Runbook

Use this when a simulation/journey step returns `error`, `unknown_action`, or produces incorrect side effects.

## 1) Reproduce with a stable request id

Send request with explicit `X-Request-ID` so logs correlate across services:

```bash
curl -X POST \
  -H "Authorization: Bearer <token>" \
  -H "X-Request-ID: debug-step-001" \
  -H "Content-Type: application/json" \
  "http://localhost:8000/api/v2/journeys/runs/<run_id>/steps/<step_id>/execute" \
  -d '{"payload":{},"metadata":{"role":"manufacturer"}}'
```

## 2) Inspect run state and execution payload

```bash
curl -H "Authorization: Bearer <token>" \
  "http://localhost:8000/api/v2/journeys/runs/<run_id>"
```

Verify:

- `status`
- `current_step`
- latest `steps[*].status`
- latest `steps[*].payload` and `steps[*].metadata`

## 3) Check step action plugin mapping

Step actions are resolved in:

- `services/simulation-engine/app/core/step_executor.py`

If response includes `unknown_action`, the story action is not registered in `STEP_PLUGINS`.

## 4) Validate story definition

Run schema lint:

```bash
make story-lint
```

For story file review:

- `services/simulation-engine/data/stories/*.yaml`
- `services/simulation-engine/app/schemas/story_schema.py`

## 5) Idempotency and concurrency checks

If duplicate side effects appear:

1. Retry the same step with the same idempotency key.
2. Confirm result is reused and no duplicate event is emitted.
3. Inspect execution receipt records and session lock behavior.

## 6) Downstream dependency checks

Many step plugins call external services:

- compliance-service (`compliance.check`)
- edc-simulator (`edc.negotiate`, `edc.transfer`)
- aas-adapter (`aas.*`, `aasx.upload`)

If plugin returns `error`, inspect downstream service logs with request id:

```bash
docker compose -f infrastructure/docker/docker-compose.yml logs --since=30m | rg "debug-step-001"
```

## 7) Verify events and gamification side effects

1. Query timeline:

```bash
curl -H "Authorization: Bearer <token>" \
  "http://localhost:8000/api/v2/events?run_id=<run_id>&limit=100&offset=0"
```

2. Confirm expected event types exist.
3. If missing, inspect producer path and publish helper retry logs.

## 8) Exit criteria

A step failure fix is complete when:

1. The failing step succeeds in reproducible runs.
2. Idempotent retries do not duplicate state/events.
3. Downstream side effects and event timeline are consistent.
4. Relevant unit/integration tests pass.
