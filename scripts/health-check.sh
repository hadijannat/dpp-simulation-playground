#!/usr/bin/env bash
set -euo pipefail

curl -s http://localhost:8001/api/v1/health | grep ok >/dev/null
curl -s http://localhost:8002/api/v1/health | grep ok >/dev/null
curl -s http://localhost:8003/api/v1/health | grep ok >/dev/null
curl -s http://localhost:8004/api/v1/health | grep ok >/dev/null
curl -s http://localhost:8005/api/v1/health | grep ok >/dev/null

echo "All services healthy."
