# ADR-006: RBAC with Keycloak and Dev Bypass Mode

## Status
Accepted

## Date
2026-02-05

## Context
The DPP Playground supports multiple user roles (manufacturer, auditor, recycler, regulator) that determine which journey flows, compliance checks, and dataspace operations are available. We need role-based access control (RBAC) that:

- Integrates with enterprise identity providers via standard protocols (OIDC/SAML).
- Supports fine-grained role assignments per user.
- Doesn't block local development when no IdP is available.
- Works with the BFF gateway pattern (ADR-001).

## Decision
Use **Keycloak** as the identity provider with the following architecture:

1. **Keycloak issues JWTs** with role claims embedded in the token payload.
2. **platform-api validates JWTs** on every request using Keycloak's JWKS endpoint.
3. **Role information** is extracted from the token's `realm_access.roles` claim and passed downstream via request headers.
4. **Dev bypass mode** (`AUTH_MODE=dev`): When this env var is set, platform-api skips JWT validation and uses a configurable default role. This enables local development without running Keycloak.
5. **Frontend role store** (Zustand) reflects the server-assigned role but also allows client-side role switching for simulation purposes (the switched role is sent as metadata, not as an auth claim).

Auth flow:
```
Browser → Keycloak login → JWT → platform-api (validate) → platform-core (trusted, no re-validation)
```

## Consequences
- **Positive:** Enterprise-grade SSO via Keycloak with OIDC/SAML support.
- **Positive:** Dev bypass eliminates auth friction for local development and CI.
- **Positive:** Stateless JWT validation — no session store needed at the gateway.
- **Negative:** Keycloak adds operational complexity (realm configuration, client setup, key rotation).
- **Negative:** Dev bypass mode must never be enabled in production — requires deployment safeguards.
- **Neutral:** platform-core trusts platform-api and does not re-validate tokens, which is acceptable because platform-core is not publicly accessible.
