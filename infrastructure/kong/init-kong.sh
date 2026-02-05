#!/usr/bin/env sh
set -e

KEYCLOAK_URL=${KEYCLOAK_URL:-http://keycloak:8080}
KEYCLOAK_REALM=${KEYCLOAK_REALM:-dpp}
TEMPLATE=/kong/kong.template.yml
OUTPUT=/kong/declarative/kong.yml
mkdir -p /kong/declarative

# Wait for Keycloak
until curl -sf "$KEYCLOAK_URL/realms/$KEYCLOAK_REALM" >/dev/null; do
  echo "Waiting for Keycloak..."
  sleep 2
done

# Fetch realm public key
PUB_KEY=$(python3 - <<PY
import json, urllib.request
url = "${KEYCLOAK_URL}/realms/${KEYCLOAK_REALM}"
with urllib.request.urlopen(url) as resp:
    data = json.loads(resp.read().decode())
print(data.get("public_key", ""))
PY
)

if [ -z "$PUB_KEY" ]; then
  echo "Failed to fetch Keycloak public key"
  exit 1
fi

python3 - <<PY
import os
from pathlib import Path
pub = """$PUB_KEY"""
text = Path("$TEMPLATE").read_text()
text = text.replace("REPLACE_WITH_KEYCLOAK_REALM_PUBLIC_KEY", pub)
allow = os.getenv("KONG_ALLOW_ANONYMOUS", "true").lower() in ("1", "true", "yes")
if allow:
    text = text.replace("__ANON_CONSUMER__", "  - username: anonymous\n")
    text = text.replace("__ANON_CONFIG__", "      anonymous: anonymous\n")
else:
    text = text.replace("__ANON_CONSUMER__", "")
    text = text.replace("__ANON_CONFIG__", "")
origins = os.getenv("KONG_CORS_ORIGINS", "http://localhost:3000")
items = [o.strip() for o in origins.split(",") if o.strip()]
origin_list = "[" + ", ".join(f'\"{o}\"' for o in items) + "]" if items else "[]"
text = text.replace("__CORS_ORIGINS__", origin_list)
Path("$OUTPUT").write_text(text)
PY

exec /docker-entrypoint.sh kong docker-start
