#!/usr/bin/env bash
set -euo pipefail

psql "$DATABASE_URL" -f data/seed/users.sql
psql "$DATABASE_URL" -f data/seed/epics.sql
psql "$DATABASE_URL" -f data/seed/user_stories.sql
psql "$DATABASE_URL" -f data/seed/achievements.sql
psql "$DATABASE_URL" -f data/seed/levels.sql
