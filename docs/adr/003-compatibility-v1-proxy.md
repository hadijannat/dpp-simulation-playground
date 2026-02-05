# ADR-003: v1 Backward Compatibility via Proxy Layer

## Status
Accepted

## Date
2026-02-05

## Context
The v1 API (`/api/v1/`) was the original interface used by early frontend versions and external integrations. With the introduction of v2, we needed to decide how to handle existing v1 consumers:

1. **Drop v1** — force all clients to migrate immediately.
2. **Maintain v1 as separate endpoints** — duplicate route handlers.
3. **Proxy v1 to v2** — translate v1 requests into v2 equivalents transparently.

Option 1 breaks existing consumers. Option 2 creates long-term maintenance burden with two parallel implementations.

## Decision
Implement a **compatibility proxy layer** in `platform-api/app/api/compat.py` that:

1. Mounts v1 routes under `/api/v1/`.
2. Translates incoming v1 request shapes to their v2 equivalents.
3. Forwards the translated request to the v2 handler (which proxies to platform-core).
4. Transforms the v2 response back to the v1 shape before returning.

The compat layer is thin — it only maps field names and restructures payloads. No domain logic lives here.

## Consequences
- **Positive:** Existing v1 consumers continue working without changes.
- **Positive:** All domain logic improvements in v2 automatically benefit v1 consumers.
- **Positive:** Clear deprecation path — once v1 traffic drops to zero, remove the compat module.
- **Negative:** v1 response shapes are frozen. New v2 fields are not available through v1.
- **Negative:** Subtle differences between v1 and v2 semantics may cause edge-case bugs in translation.
- **Neutral:** v1 endpoints are documented as deprecated in OpenAPI with `deprecated=True`.
