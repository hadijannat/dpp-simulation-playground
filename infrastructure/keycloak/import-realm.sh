#!/usr/bin/env bash
set -euo pipefail

/opt/keycloak/bin/kc.sh import --file /opt/keycloak/data/import/realm-export.json
