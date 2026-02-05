#!/usr/bin/env bash
set -euo pipefail

curl -s http://localhost:8101/api/v1/health | grep ok >/dev/null
curl -s http://localhost:8102/api/v1/health | grep ok >/dev/null
curl -s http://localhost:8103/api/v1/health | grep ok >/dev/null
curl -s http://localhost:8104/api/v1/health | grep ok >/dev/null
curl -s http://localhost:8105/api/v1/health | grep ok >/dev/null

curl -s -H "X-Dev-User: health" -H "X-Dev-Roles: developer" http://localhost:8104/api/v1/edc/catalog >/dev/null
curl -s -H "X-Dev-User: health" -H "X-Dev-Roles: developer" http://localhost:8101/api/v1/progress/epics >/dev/null

echo "All services healthy."
