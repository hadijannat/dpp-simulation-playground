#!/usr/bin/env bash
set -euo pipefail

curl -s http://localhost:8101/api/v1/health | grep ok >/dev/null
curl -s http://localhost:8102/api/v1/health | grep ok >/dev/null
curl -s http://localhost:8103/api/v1/health | grep ok >/dev/null
curl -s http://localhost:8104/api/v1/health | grep ok >/dev/null
curl -s http://localhost:8105/api/v1/health | grep ok >/dev/null

echo "All services healthy."
