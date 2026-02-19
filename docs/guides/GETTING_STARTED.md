# Getting Started

1. Copy environment defaults:

```
cp infrastructure/docker/.env.example infrastructure/docker/.env
```

2. Start the stack:

```
make up
```

3. Run migrations:

```
make migrate
```

4. Seed initial data:

```
make seed
```

5. Use the operational runbooks:

- `docs/guides/ADDING_STORIES.md`
- `docs/guides/ADDING_COMPLIANCE_RULES.md`
- `docs/guides/EVENT_DEBUG_RUNBOOK.md`
- `docs/guides/STEP_FAILURE_DEBUG_RUNBOOK.md`
