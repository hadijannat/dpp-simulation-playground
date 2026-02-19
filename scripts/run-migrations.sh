#!/usr/bin/env bash
set -euo pipefail

docker compose -f infrastructure/docker/docker-compose.yml exec -T simulation-engine \
  alembic -c /app/services/shared/migrations/alembic.ini upgrade head
