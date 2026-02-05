# Keycloak Configuration

This folder contains the realm export and a custom image for auto-import.

## Clients
- `dpp-frontend`: public client for the UI
- `dpp-api`: bearer-only client for API validation
- `dpp-services`: confidential client for service-to-service calls (client credentials)

## Usage

The Docker Compose stack builds the custom image and runs Keycloak with `--import-realm` to load `realm-export.json` automatically.
