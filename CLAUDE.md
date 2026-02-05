# DPP Simulation Playground

## Architecture

**3-tier backend** with a React SPA frontend:

```
Frontend (React 19 + Vite 7)
  → platform-api   (BFF gateway, port 8006) — stateless proxy, CORS, auth
    → platform-core (domain logic, port 8007) — DB access, business rules
    → simulation-engine (story execution, port 8001) — step engine, Alembic migrations
```

All backend services are FastAPI. PostgreSQL is the primary data store.

### Key directories

- `frontend/` — React 19 + TypeScript SPA
- `services/platform-api/` — BFF gateway (v1 compat + v2 proxy)
- `services/platform-core/` — Domain logic with DB access
- `services/simulation-engine/` — Story step execution, Alembic migrations
- `services/shared/` — ORM models, repositories, tracing (imported by all services)
- `services/shared/models/` — SQLAlchemy ORM models (single source of truth)
- `services/shared/repositories/` — Plain functions with `db: Session` first arg
- `infrastructure/docker/` — docker-compose files (dev + test)
- `docs/adr/` — Architecture Decision Records (001-008)

## Conventions

### Backend (Python / FastAPI)

- ORM models live in `services/shared/models/` — never duplicate in individual services
- simulation-engine has a re-export shim at `app/models/__init__.py` importing from shared
- `Column("metadata", JSONB)` uses Python attribute `metadata_` to avoid `Base.metadata` clash
- Repository functions are plain functions with `db: Session` as first argument
- platform-api proxies requests via `app.core.proxy.request_json()`
- platform-core domain routes live under `app/api/v2/` (journeys, digital_twins, feedback, compliance)
- Auth: Keycloak JWTs in production, `AUTH_MODE=dev` bypasses validation for local dev/CI
- Alembic migrations in `services/simulation-engine/alembic/versions/` (forward-only, shared DB)
- Backfill scripts in `services/simulation-engine/scripts/` (idempotent, safe to re-run)
- Observability: `services/shared/tracing.py` provides opt-in OpenTelemetry + Prometheus

### Frontend (React / TypeScript)

- **State**: Zustand for client state (roleStore, sessionStore), TanStack Query for server state
- **i18n**: react-i18next with 6 namespaces (common, simulation, compliance, edc, gamification, journey) × 3 languages (en, de, fr)
- **Design tokens**: All colors/spacing via CSS custom properties in `frontend/src/design/tokens.css` — no hardcoded hex in components
- Token hierarchy: Primitives (`--blue-600`) → Semantics (`--accent`) → Components (`--canvas-node-bg`)
- Journey page is server-driven via `useJourneyTemplate(code)` hook
- Service functions in `frontend/src/services/platformV2Service.ts`
- Types in `frontend/src/types/v2.types.ts`

### Testing

- **Frontend unit**: Vitest + @testing-library/react
- **Frontend E2E**: Playwright with `mobile-chromium` (mocked) and `integration-chromium` (real backend) projects
- **Accessibility**: @axe-core/playwright in `frontend/e2e/a11y.spec.ts`
- **Backend**: pytest + httpx TestClient
- **platform-core tests**: SQLite in-memory via `conftest.py` with `app.dependency_overrides[get_db]`
- **platform-api proxy tests**: `monkeypatch.setattr("app.core.proxy.requests.request", ...)` with DummyResponse pattern

### CI

GitHub Actions workflow (`.github/workflows/ci.yml`) jobs:
- `lint-frontend`, `lint-backend` — ESLint + Ruff
- `test-frontend`, `test-backend` — unit tests
- `e2e-mobile-chromium` — Playwright mocked E2E
- `e2e-integration` — Playwright against real backend stack (docker-compose.test.yml)
- `a11y` — axe-core accessibility checks
- `lighthouse` — Lighthouse CI (performance ≥ 0.8, accessibility ≥ 0.9)

## Common commands

```bash
# Frontend
cd frontend && npm install && npm run dev     # Dev server
cd frontend && npm test                       # Vitest unit tests
cd frontend && npx playwright test            # E2E tests

# Backend
cd services/simulation-engine && pip install -r requirements.txt && uvicorn app.main:app --port 8001
cd services/platform-core && uvicorn app.main:app --port 8007
cd services/platform-api && uvicorn app.main:app --port 8006

# Tests
pytest services/simulation-engine/tests/ -v
pytest services/platform-core/tests/ -v
pytest services/platform-api/tests/ -v

# Docker (full stack)
docker compose -f infrastructure/docker/docker-compose.yml up
docker compose -f infrastructure/docker/docker-compose.test.yml up  # integration tests
```
