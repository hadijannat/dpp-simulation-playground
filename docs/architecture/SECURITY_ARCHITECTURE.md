# Security Architecture

Keycloak handles authentication (OIDC). Kong validates JWTs and enforces rate limiting and CORS. Services enforce RBAC based on token claims.
