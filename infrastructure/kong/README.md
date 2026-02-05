# Kong Gateway Configuration

This gateway uses the JWT plugin to validate Keycloak-issued tokens.

## Setup
1. Export Keycloak realm public key (Realm Settings → Keys → RSA public key).
2. Replace `REPLACE_WITH_KEYCLOAK_REALM_PUBLIC_KEY` in `kong.yml`.
3. Ensure `iss` claim matches `http://localhost:8080/realms/dpp`.

## Routes
The gateway routes `/api/v1/*` paths to the corresponding microservices.
