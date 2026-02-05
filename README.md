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

4. Seed initial data:

```bash
make seed
```

5. Open the UI:

- http://localhost:3000

## Default Credentials

- Username: `demo@example.com`
- Password: `demo1234`

## Services

- Simulation Engine: http://localhost:8001
- Compliance Service: http://localhost:8002
- Gamification Service: http://localhost:8003
- EDC Simulator: http://localhost:8004
- Collaboration Service: http://localhost:8005
- Keycloak: http://localhost:8080

## Development

- Frontend: `cd frontend && npm install && npm run dev`
- Backend: `cd services/<service> && uvicorn app.main:app --reload --port <port>`

## Documentation

See `docs/` for architecture, APIs, compliance, and guides.
