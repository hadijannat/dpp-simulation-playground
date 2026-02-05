# ADR-005: Data Migration Strategy with Alembic

## Status
Accepted

## Date
2026-02-05

## Context
The DPP Playground uses PostgreSQL as its primary data store with 15+ tables spanning multiple domains (users, sessions, stories, DPP instances, compliance, journeys, digital twins, feedback). Schema changes are frequent during active development. We needed a migration strategy that:

- Supports incremental, versioned schema changes.
- Works in CI/CD pipelines (automated `upgrade head`).
- Handles multiple developers working on migrations concurrently.
- Provides rollback capability for failed deployments.

## Decision
Use **Alembic** (SQLAlchemy's migration tool) with the following conventions:

1. **Single migration chain** in `services/simulation-engine/alembic/versions/` — all services share one PostgreSQL database and one migration history.
2. **Migrations numbered sequentially** (001 through 012+) with descriptive filenames.
3. **Each migration is idempotent** where possible — using `op.execute()` with `IF NOT EXISTS` guards.
4. **Backfill scripts** (`services/simulation-engine/scripts/`) handle data seeding separately from schema changes.
5. **ORM models** in `services/shared/models/` are the source of truth for the current schema. Alembic `env.py` imports `Base.metadata` from shared models to enable autogeneration.
6. **No down migrations in production** — we rely on forward-only migrations with compensating changes if rollback is needed.

Migration highlights:
- 001-005: Core tables (users, sessions, stories, DPP instances, compliance, achievements)
- 006: Journey templates and runs
- 007: Digital twin graph (snapshots, nodes, edges)
- 008: Compliance rule versions and run fixes
- 009: UX feedback
- 010-012: Indexes, session journey linking, gamification extensions

## Consequences
- **Positive:** All schema changes are version-controlled and reviewable in PRs.
- **Positive:** `alembic upgrade head` in CI ensures consistent schema across environments.
- **Positive:** Shared models package keeps ORM in sync with migrations.
- **Negative:** Single migration chain can cause merge conflicts when multiple PRs add migrations.
- **Negative:** Forward-only policy means fixing a bad migration requires a new compensating migration.
- **Neutral:** Backfill scripts run after migrations and are idempotent, safe to re-run.
