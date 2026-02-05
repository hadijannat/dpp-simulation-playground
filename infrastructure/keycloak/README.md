# Keycloak Configuration

This folder contains the realm export and a custom image for auto-import.

## Usage

The Docker Compose stack builds the custom image and runs Keycloak with `--import-realm` to load `realm-export.json` automatically.
