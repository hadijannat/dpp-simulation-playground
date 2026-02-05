#!/usr/bin/env bash
set -euo pipefail

cd services/simulation-engine
alembic upgrade head
