# ADR-004: Server-Driven Journey Template Engine

## Status
Accepted

## Date
2026-02-05

## Context
The manufacturer journey (create DPP → compliance check → EDC negotiation → EDC transfer → feedback) was originally hardcoded in the React frontend with fixed step labels, payloads, and flow order. This caused several problems:

- Adding or reordering steps required a frontend deployment.
- Different roles (manufacturer, auditor, recycler) couldn't have different journey flows.
- Localization of step titles required frontend i18n changes for every new step.
- A/B testing different journey structures was impossible.

## Decision
Implement a **server-driven journey template engine** using two database tables:

1. **`journey_templates`** — defines a named flow (e.g., `manufacturer-core-e2e`) with metadata (target role, active/inactive, description).
2. **`journey_steps`** — ordered step definitions linked to a template, each specifying: `step_key`, `title`, `action` (e.g., `aas.create`, `compliance.check`, `edc.negotiate`), `order_index`, and `default_payload` (JSONB).

The frontend fetches the template via `GET /api/v2/journeys/templates/{code}` and renders steps dynamically. Each step's action maps to a handler function on the client side. The `default_payload` provides sensible defaults that can be edited in the payload editor.

Journey execution is tracked via `journey_runs` and `journey_step_runs` tables, enabling resume, audit trails, and analytics.

## Consequences
- **Positive:** New journey flows can be added via database seeding without frontend changes.
- **Positive:** Step titles and descriptions can be localized server-side per locale.
- **Positive:** A/B testing different step orders or default payloads is a DB-level change.
- **Positive:** Journey progress persists across sessions via `journey_runs`.
- **Negative:** Frontend needs a fallback for when the template API is unreachable (hardcoded step buttons).
- **Negative:** Adding a genuinely new step action requires both backend handler and frontend mapping.
- **Neutral:** Templates are seeded via `backfill_journeys.py` script, run as part of deployment.
