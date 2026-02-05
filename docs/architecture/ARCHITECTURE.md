# Architecture Overview

This document summarizes the DPP Simulation Playground architecture and runtime data flow.

## Layers
- **Frontend**: React + Vite SPA providing simulation canvas, API playground, compliance dashboards, EDC flows, and gamification UI.
- **API Gateway**: Kong (DB-less) for JWT validation, rate limiting, and routing to microservices.
- **Core Services**:
  - **Simulation Engine**: story/session orchestration, step execution, AAS operations.
  - **Compliance Service**: rule evaluation (JSONPath + YAML rules) and report persistence.
  - **Gamification Service**: points, achievements, streaks; consumes Redis events.
  - **EDC Simulator**: DSP negotiation & transfer state machines, ODRL policy checks.
  - **Collaboration Service**: annotations, gap reports, voting, comments.
- **Infrastructure**: Postgres (state), Redis (events/cache), MongoDB (BaSyx storage), MinIO (AASX artifacts), Keycloak (OIDC), BaSyx components.

## Data Flow
1. User authenticates via Keycloak and receives JWT.
2. Frontend calls Kong with JWT; Kong validates and routes.
3. Simulation Engine executes story steps and publishes events to Redis Streams.
4. Gamification Engine consumes events and awards points/achievements.
5. Compliance Service evaluates payloads and stores reports in Postgres.
6. EDC Simulator processes negotiation/transfer states, emits events on completion.

## Service Ports
- Simulation Engine: `8001`
- Compliance Service: `8002`
- Gamification Service: `8003`
- EDC Simulator: `8004`
- Collaboration Service: `8005`
- Kong Gateway: `8000`

## Deployment Targets
- **Docker Compose** for local development (all services + dependencies).
- **Kubernetes** for production (deployments + statefulsets + ingress + TLS).

## Security
- JWT validation at Kong and service middleware.
- RBAC enforced per endpoint.
- CORS configured at Kong.
- Secrets stored in Kubernetes Secrets.
