# Development Guide

## Environment Variables

### Auth
- `KEYCLOAK_URL` (default: `http://keycloak:8080`)
- `KEYCLOAK_REALM` (default: `dpp`)
- `KEYCLOAK_ISSUERS` (optional, comma-separated)
- `KEYCLOAK_AUDIENCES` / `KEYCLOAK_AUDIENCE` (optional, comma-separated allowlist)
- `REQUIRE_TOKEN_AUDIENCE` (default: `true`)
- `JWT_CLOCK_SKEW_SECONDS` (default: `30`)
- `KEYCLOAK_JWKS_URL` (optional override)
- `DEV_BYPASS_AUTH` (set `true` for local testing)
- `X-Dev-User` (header used when `DEV_BYPASS_AUTH=true`)
- `X-Dev-Roles` (header used when `DEV_BYPASS_AUTH=true`, comma-separated)

### Backend
- `DATABASE_URL` (default: `postgresql://dpp:dpp@postgres:5432/dpp_playground`)
- `REDIS_URL` (default: `redis://redis:6379/0`)
- `COMPLIANCE_URL` (simulation-engine -> compliance service)
- `EDC_URL` (simulation-engine -> edc service)
- `AAS_ADAPTER_URL` (simulation-engine/platform-api -> aas-adapter service)
- `BASYX_BASE_URL` (default: `http://aas-environment:8081`)
- `AAS_REGISTRY_URL` (optional)
- `SUBMODEL_REGISTRY_URL` (optional)
- `IDTA_TEMPLATES_DIR` (optional override for template lookup)
- `EVENT_STREAM_MAXLEN` (default: `50000`; producer-side trim target)
- `STREAM_MAXLEN` (default: `50000`; `simulation.events` trim target)
- `RETRY_STREAM_MAXLEN` (default: `20000`; retry stream trim target)
- `DLQ_STREAM_MAXLEN` (default: `20000`; DLQ stream trim target)
- `STREAM_TRIM_INTERVAL_SECONDS` (default: `300`; periodic stream trim interval)

## Local Dev Tips

- Use `make up` to start the full stack.
- Use `DEV_BYPASS_AUTH=true` with headers for local API calls.
- The Kong gateway runs at `http://localhost:8000` and routes `/api/v1/*`.

## Runbooks

- Story authoring: `docs/guides/ADDING_STORIES.md`
- Compliance rules lifecycle: `docs/guides/ADDING_COMPLIANCE_RULES.md`
- Event and stream debugging: `docs/guides/EVENT_DEBUG_RUNBOOK.md`
- Step execution failure debugging: `docs/guides/STEP_FAILURE_DEBUG_RUNBOOK.md`
