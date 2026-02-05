#!/usr/bin/env bash
set -euo pipefail

COMPOSE_FILE="${COMPOSE_FILE:-infrastructure/docker/docker-compose.yml}"
POSTGRES_DB="${POSTGRES_DB:-dpp_playground}"
POSTGRES_USER="${POSTGRES_USER:-dpp}"

run_psql() {
  if [ -n "${DATABASE_URL:-}" ]; then
    psql "$DATABASE_URL" -f "$1"
  else
    docker compose -f "$COMPOSE_FILE" exec -T postgres psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" < "$1"
  fi
}

run_psql data/seed/users.sql
run_psql data/seed/epics.sql
run_psql data/seed/user_stories.sql
run_psql data/seed/achievements.sql
run_psql data/seed/levels.sql
