#!/usr/bin/env bash
set -euo pipefail

if [ ! -f infrastructure/docker/.env ]; then
  cp infrastructure/docker/.env.example infrastructure/docker/.env
fi

docker compose -f infrastructure/docker/docker-compose.yml up -d

echo "Deployment started."
