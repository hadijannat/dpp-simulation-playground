#!/usr/bin/env bash
set -euo pipefail

cp infrastructure/docker/.env.example infrastructure/docker/.env || true

echo "Setup complete."
