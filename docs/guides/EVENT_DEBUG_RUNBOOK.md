# Event Debug Runbook

Use this when simulation/compliance/EDC/collaboration actions complete but gamification or timelines are wrong.

## 1) Confirm services are healthy

```bash
make health
```

Check at least:

- platform-api
- platform-core
- gamification-service
- redis

## 2) Trace by request id

All gateway requests should propagate `X-Request-ID`.

1. Capture the failing request id.
2. Search logs across services:

```bash
docker compose -f infrastructure/docker/docker-compose.yml logs --since=30m | rg "<request-id>"
```

If request id appears in platform-api but not downstream, inspect proxy/header forwarding.

## 3) Inspect queryable event timeline

Use platform timeline API first (Postgres-backed):

```bash
curl -H "Authorization: Bearer <token>" \
  "http://localhost:8000/api/v2/events?session_id=<session_id>&limit=100&offset=0"
```

Or by run:

```bash
curl -H "Authorization: Bearer <token>" \
  "http://localhost:8000/api/v2/events?run_id=<run_id>&limit=100&offset=0"
```

## 4) Inspect Redis stream operational state

From gamification admin endpoints:

```bash
curl -H "Authorization: Bearer <token>" http://localhost:8006/api/v1/admin/stream-status
curl -H "Authorization: Bearer <token>" "http://localhost:8006/api/v1/admin/stream/pending?limit=100"
curl -H "Authorization: Bearer <token>" "http://localhost:8006/api/v1/admin/stream/dlq?limit=100&offset=0"
```

Focus on:

- `pending.stream` and `pending.retry`
- DLQ growth
- stream lengths vs configured maxlen

## 5) Replay DLQ safely

Replay oldest items:

```bash
curl -X POST -H "Authorization: Bearer <token>" -H "Content-Type: application/json" \
  http://localhost:8006/api/v1/admin/stream/dlq/replay \
  -d '{"limit":20,"delete_after_replay":true}'
```

Replay specific message ids:

```bash
curl -X POST -H "Authorization: Bearer <token>" -H "Content-Type: application/json" \
  http://localhost:8006/api/v1/admin/stream/dlq/replay \
  -d '{"message_ids":["<id-1>","<id-2>"],"delete_after_replay":false}'
```

## 6) Common failure patterns

- Schema mismatch:
  - `event` payload missing required envelope fields (`event_id`, `event_type`, `source_service`, etc.)
  - Action: verify producers use shared event builder.
- Pending grows unbounded:
  - Consumer retries but never reaches terminal outcome.
  - Action: inspect retry stream + DLQ policy and failing rule logic.
- Points not updating:
  - Event exists in timeline but rule missing/inactive.
  - Action: verify point rule definitions and cache invalidation.

## 7) Recovery checklist

1. Confirm producer emits valid envelope.
2. Confirm event is visible in `/api/v2/events`.
3. Confirm stream pending is stable after replay.
4. Confirm points/achievements update in gamification endpoints.
