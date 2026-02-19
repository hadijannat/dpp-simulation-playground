# RBAC Matrix

Source of truth: `services/shared/rbac_matrix.yaml`.
Use `python scripts/sync-rbac-matrix.py` after changing endpoint role guards.
Per-service test suites enforce that route protections match the matrix.

| Endpoint | Roles |
| --- | --- |
| POST /api/v1/sessions | manufacturer, developer, admin, regulator, consumer, recycler |
| GET /api/v1/sessions/{id} | manufacturer, developer, admin, regulator, consumer, recycler |
| GET /api/v1/stories/{code} | manufacturer, developer, admin, regulator, consumer, recycler |
| POST /api/v1/sessions/{id}/stories/{code}/start | manufacturer, developer, admin, regulator, consumer, recycler |
| POST /api/v1/sessions/{id}/stories/{code}/steps/{idx}/execute | manufacturer, developer, admin, regulator, consumer, recycler |
| GET /api/v1/progress | manufacturer, developer, admin, regulator, consumer, recycler |
| POST /api/v1/aas/shells | manufacturer, developer, admin |
| GET /api/v1/aas/shells | manufacturer, developer, admin, regulator, consumer, recycler |
| POST /api/v1/aas/validate | regulator, developer, admin |
| POST /api/v1/compliance/check | manufacturer, regulator, developer, admin |
| GET /api/v1/rules | regulator, developer, admin |
| GET /api/v1/reports | regulator, developer, admin |
| GET /api/v1/achievements | developer, admin, manufacturer, consumer, regulator, recycler |
| GET /api/v1/leaderboard | developer, admin, manufacturer, consumer, regulator, recycler |
| GET /api/v1/streaks | developer, admin, manufacturer, consumer, regulator, recycler |
| POST /api/v1/points | developer, admin |
| GET /api/v1/edc/catalog | developer, manufacturer, admin, regulator, consumer, recycler |
| POST /api/v1/edc/negotiations | developer, manufacturer, admin |
| GET /api/v1/edc/negotiations/{id} | developer, manufacturer, admin, regulator |
| POST /api/v1/edc/negotiations/{id}/accept | developer, manufacturer, admin |
| POST /api/v1/edc/transfers | developer, manufacturer, admin |
| GET /api/v1/edc/transfers/{id} | developer, manufacturer, admin, regulator |
| POST /api/v1/edc/transfers/{id}/start | developer, manufacturer, admin |
| POST /api/v1/edc/policies/build | developer, manufacturer, admin |
| POST /api/v1/edc/policies/evaluate | developer, manufacturer, admin, regulator |
| GET /api/v1/edc/participants | developer, manufacturer, admin, regulator |
| GET /api/v1/annotations | developer, admin, regulator, manufacturer |
| POST /api/v1/annotations | developer, admin, manufacturer, regulator, consumer, recycler |
| GET /api/v1/gap_reports | developer, admin, regulator, manufacturer |
| POST /api/v1/gap_reports | developer, admin, manufacturer, regulator, consumer, recycler |
| GET /api/v1/votes | developer, admin, regulator, manufacturer |
| POST /api/v1/votes | developer, admin, manufacturer, regulator, consumer, recycler |
| GET /api/v1/comments | developer, admin, regulator, manufacturer |
| POST /api/v1/comments | developer, admin, manufacturer, regulator, consumer, recycler |
