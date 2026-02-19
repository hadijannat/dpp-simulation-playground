# DPP Simulation Playground

A microservices-based simulation environment for Digital Product Passport workflows. It combines a React frontend, FastAPI services, Keycloak auth, Kong gateway, and supporting infrastructure (Postgres, Redis, MongoDB, MinIO, BaSyx).

## Quick Start

1. Copy environment defaults:

```bash
cp infrastructure/docker/.env.example infrastructure/docker/.env
```

2. Start the stack:

```bash
make up
```

3. Run migrations:

```bash
make migrate
```

4. Backfill journey runs (v2 data model):

```bash
python services/simulation-engine/scripts/backfill_journeys.py
```

5. Seed initial data:

```bash
make seed
```

5. Open the UI:

- http://localhost:3000

## Default Credentials

- Username: `demo@example.com`
- Password: `demo1234`

## Service-to-Service Auth

Simulation Engine uses Keycloak client credentials:
- Client ID: `dpp-services`
- Client Secret: `dev-services-secret`

## Environment Variables (Common)

- `KEYCLOAK_URL` (default: `http://keycloak:8080`)
- `KEYCLOAK_REALM` (default: `dpp`)
- `KEYCLOAK_ISSUERS` (comma-separated; defaults to localhost + docker host issuers)
- `KEYCLOAK_AUDIENCES` / `KEYCLOAK_AUDIENCE` (optional, comma-separated; when set, bearer token `aud` must match one value)
- `REQUIRE_TOKEN_AUDIENCE` (default: `true`; enforce presence of token `aud` claim)
- `JWT_CLOCK_SKEW_SECONDS` (default: `30`; leeway used during JWT time-claim validation)
- `KEYCLOAK_JWKS_URL` (override JWKS endpoint)
- `DEV_BYPASS_AUTH` (set `true` for local header-based auth)
- `AUTH_MODE` (`keycloak`, `bypass`, or `auto`; default: `auto`)
- `ALLOW_DEV_HEADERS` (platform-api only; allows forwarding `X-Dev-*` headers when no bearer token. Keep `false` outside local/dev test environments.)
- `AAS_ADAPTER_URL` (default: `http://aas-adapter:8008`; simulation/platform compatibility AAS proxy target)
- `BASYX_BASE_URL` (default: `http://aas-environment:8081`)
- `AAS_REGISTRY_URL` (optional)
- `SUBMODEL_REGISTRY_URL` (optional)
- `MINIO_ENDPOINT`, `MINIO_ACCESS_KEY`, `MINIO_SECRET_KEY`, `MINIO_BUCKET`, `MINIO_PUBLIC_URL`

## Services

- API Gateway: http://localhost:8000
- Simulation Engine: http://localhost:8101 (gateway: http://localhost:8000)
- Compliance Service: http://localhost:8102 (gateway: http://localhost:8000)
- Gamification Service: http://localhost:8103 (gateway: http://localhost:8000)
- EDC Simulator: http://localhost:8104 (gateway: http://localhost:8000)
- Collaboration Service: http://localhost:8105 (gateway: http://localhost:8000)
- Platform API (v2 BFF): http://localhost:8106 (gateway: http://localhost:8000/api/v2)
- Platform Core: http://localhost:8107
- AAS Adapter: http://localhost:8108
- Keycloak: http://localhost:8080
- MinIO: http://localhost:9100 (console 9101)

## Development

- Frontend: `cd frontend && npm install && npm run dev`
- Backend: `cd services/<service> && uvicorn app.main:app --reload --port <port>`

## Documentation

See `docs/` for architecture, APIs, compliance, and guides.

Generate OpenAPI specs with:

```bash
make openapi
```

RBAC matrix sync:

```bash
python scripts/sync-rbac-matrix.py
```
