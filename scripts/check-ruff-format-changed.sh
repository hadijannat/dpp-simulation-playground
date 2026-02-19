#!/usr/bin/env bash
set -euo pipefail

BASE_REF="${1:-}"
if [[ -z "$BASE_REF" ]]; then
  if git rev-parse --verify origin/main >/dev/null 2>&1; then
    BASE_REF="$(git merge-base HEAD origin/main)"
  elif git rev-parse --verify HEAD~1 >/dev/null 2>&1; then
    BASE_REF="HEAD~1"
  else
    BASE_REF="HEAD"
  fi
fi

if ! git rev-parse --verify "$BASE_REF" >/dev/null 2>&1; then
  if git rev-parse --verify HEAD~1 >/dev/null 2>&1; then
    BASE_REF="HEAD~1"
  else
    BASE_REF="HEAD"
  fi
fi

files=()
while IFS= read -r file; do
  if [[ -n "$file" ]]; then
    files+=("$file")
  fi
done < <(git diff --name-only --diff-filter=ACMR "$BASE_REF" HEAD -- '*.py')

if [[ ${#files[@]} -eq 0 ]]; then
  echo "No changed Python files to format-check."
  exit 0
fi

ruff format --check "${files[@]}"
