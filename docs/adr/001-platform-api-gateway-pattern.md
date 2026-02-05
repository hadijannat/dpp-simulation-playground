# ADR-001: Platform API Gateway Pattern

## Status
Accepted

## Date
2026-02-05

## Context
The DPP Simulation Playground exposes functionality through multiple backend services: simulation-engine (story execution, AAS management), compliance-service (regulation checks), and platform-core (domain logic, persistence). Clients — the React SPA, future mobile apps, and third-party integrations — need a single, stable entry point rather than knowing about each internal service.

We also need a place to handle cross-cutting concerns: authentication, request logging, CORS, rate limiting, and API versioning (v1 legacy + v2 current).

## Decision
We adopt a **Backend-for-Frontend (BFF) gateway** implemented as `platform-api` (port 8006). This service:

1. **Exposes all public HTTP endpoints** under `/api/v1/` and `/api/v2/` prefixes.
2. **Proxies** requests to downstream services (`platform-core`, `simulation-engine`, `compliance-service`) using `httpx.AsyncClient`.
3. **Handles authentication** via Keycloak JWT validation (with a `dev` bypass mode for local development).
4. **Does not contain domain logic** — it only routes, authenticates, and transforms responses when needed.
5. **Supports v1 backward compatibility** through a `compat.py` proxy layer that maps legacy endpoints to v2 equivalents.

## Consequences
- **Positive:** Single origin for the frontend eliminates CORS complexity. Auth enforcement happens in one place. Services can be replaced or scaled independently without client changes.
- **Positive:** v1/v2 coexistence allows gradual migration without breaking existing consumers.
- **Negative:** Adds an extra network hop for every request. Latency increases by ~1-3ms per proxied call.
- **Negative:** platform-api must be updated whenever a new domain endpoint is added to platform-core.
- **Neutral:** OpenAPI docs at `/docs` reflect the public API surface, not the internal service topology.
