# ADR-002: v2 Runtime Split — platform-api vs platform-core

## Status
Accepted

## Date
2026-02-05

## Context
Early in v2 development, all domain logic (journey management, compliance orchestration, digital twin graphs, feedback collection) lived inside `platform-api` using in-memory Python dicts. This was fast to prototype but meant:

- Data was lost on every restart.
- No path to horizontal scaling (each instance had its own dict).
- Auth concerns were mixed with domain logic in the same codebase.
- Testing domain logic required spinning up the full gateway with auth middleware.

## Decision
Split the v2 runtime into two services:

1. **platform-api** (port 8006) — Stateless gateway. Handles auth, CORS, rate limiting, and proxies to downstream services. Contains zero domain logic.
2. **platform-core** (port 8007) — Domain service. Owns journey lifecycle, digital twin graphs, compliance run management, and UX feedback. Connects directly to PostgreSQL via SQLAlchemy.

platform-api forwards v2 domain requests to platform-core over HTTP. platform-core is not exposed to the public network — only platform-api can reach it.

## Consequences
- **Positive:** Domain logic is independently testable with a real database, no auth mocking needed.
- **Positive:** Data persists across restarts. Horizontal scaling is possible since all state is in PostgreSQL.
- **Positive:** Clear separation of concerns — gateway team and domain team can work in parallel.
- **Negative:** Two services to deploy and monitor instead of one.
- **Negative:** Debugging request flows requires tracing across two service logs (mitigated by OpenTelemetry).
- **Neutral:** Both services share ORM models via the `services/shared/` package to avoid duplication.
