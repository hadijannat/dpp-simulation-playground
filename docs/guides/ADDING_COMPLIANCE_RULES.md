# Adding Compliance Rules

This runbook covers how to add, validate, version, and activate compliance rule sets.

## 1) Rule source of truth

Rules can come from:

- File-backed defaults in `services/compliance-service/data/compliance-rules/`
- DB-backed rule versions managed via API (`/api/v1/rules`)

At runtime, active DB versions take precedence over file defaults.

## 2) Rule schema essentials

Each rule must be an object and should include:

- `id` (required)
- `jsonpath` (for field match/presence checks)
- `message` and `severity` (`error` or warning-like)

Supported constraints include:

- `required`, `recommended`
- `type` (`string|number|integer|boolean|object|array`)
- `enum`
- `pattern` / `regex`
- `min`, `max`
- `min_length`, `max_length`
- `requires` (cross-field dependency)
- `if` + `then_required` (conditional requirement)
- `remediation` (recommended fix guidance)

Validator implementation: `services/compliance-service/app/engine/rule_loader.py`.

## 3) Upload and activate via API

List versions:

```bash
curl -H "Authorization: Bearer <token>" \
  "http://localhost:8000/api/v1/rules?regulation=ESPR&include_versions=true&limit=50&offset=0"
```

Upload new version:

```bash
curl -X POST -H "Authorization: Bearer <token>" -H "Content-Type: application/json" \
  http://localhost:8000/api/v1/rules \
  -d '{
    "regulation": "ESPR",
    "version": "v2.3.0",
    "activate": false,
    "rules": [ ... ]
  }'
```

Activate version:

```bash
curl -X POST -H "Authorization: Bearer <token>" \
  http://localhost:8000/api/v1/rules/<rule_version_id>/activate
```

## 4) Validate behavior end-to-end

1. Start a compliance run:

```bash
curl -X POST -H "Authorization: Bearer <token>" -H "Content-Type: application/json" \
  http://localhost:8000/api/v2/compliance/runs \
  -d '{"payload": {...}, "regulations": ["ESPR"]}'
```

2. Review violations/warnings/recommendations in the run response.
3. Exercise the fix loop:

```bash
curl -X POST -H "Authorization: Bearer <token>" -H "Content-Type: application/json" \
  http://localhost:8000/api/v2/compliance/runs/<run_id>/apply-fix \
  -d '{"operations":[{"op":"replace","path":"/product_name","value":"Battery Pack 01"}]}'
```

4. Re-fetch run and verify before/after deltas and fix history.

## 5) CI checks before merge

Run:

```bash
pytest services/compliance-service/tests -q
pytest services/platform-core/tests/test_compliance.py -q
```

If rule shape or API contracts changed, also run:

```bash
make openapi
make contract-check
```

## 6) Rollback strategy

1. Keep previous version in DB.
2. Re-activate the last known good rule version.
3. Re-run a known fixture payload to confirm expected status.
