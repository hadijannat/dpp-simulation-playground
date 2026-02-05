# Architecture Overview

This document describes the system architecture for DPP Simulation Playground.

## Layers
- Frontend: React + Vite application.
- API Gateway: Kong for JWT validation and routing.
- Core Services: simulation, compliance, gamification, EDC simulator, collaboration.
- Infrastructure: Postgres, Redis, MongoDB, MinIO, BaSyx, Keycloak.
