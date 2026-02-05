# Kong Gateway Configuration

This gateway auto-fetches the Keycloak realm public key on startup and injects it into the declarative config.

## Environment
- `KEYCLOAK_URL` (default: http://keycloak:8080)
- `KEYCLOAK_REALM` (default: dpp)

## Flow
1. Kong waits for Keycloak.
2. Fetches realm public key from `/realms/<realm>`.
3. Writes `/kong/declarative/kong.yml` from template.
4. Starts Kong in DB-less mode.
