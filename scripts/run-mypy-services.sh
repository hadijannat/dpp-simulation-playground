#!/usr/bin/env bash
set -euo pipefail

services=(
  simulation-engine
  compliance-service
  gamification-service
  edc-simulator
  collaboration-service
  platform-api
  platform-core
  aas-adapter
)

for svc in "${services[@]}"; do
  echo "Running mypy for ${svc}"
  (
    cd "services/${svc}"
    mypy app --config-file ../../mypy.ini
  )
done
