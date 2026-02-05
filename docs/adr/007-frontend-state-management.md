# ADR-007: Frontend State Management with Zustand + TanStack Query

## Status
Accepted

## Date
2026-02-05

## Context
The React SPA manages two categories of state:

1. **Server state** — journey runs, compliance results, digital twin graphs, templates. This data originates from the API and needs caching, refetching, and staleness management.
2. **Client state** — current role, active session ID, journey run ID, UI preferences. This data is local to the browser and needs persistence across page navigations and refreshes.

Common approaches (Redux, MobX, React Context) either blur the line between server and client state or add significant boilerplate.

## Decision
Use a **two-library approach**:

1. **TanStack Query (React Query)** for all server state:
   - `useQuery` for GET requests with automatic caching and refetch.
   - `useMutation` for POST/PUT/DELETE with optimistic updates.
   - Query keys follow the pattern `["resource", id]` (e.g., `["journey-run", runId]`).
   - Stale time defaults to 30 seconds; refetch on window focus is enabled.

2. **Zustand** for all client state:
   - `roleStore` — current active role with `persist` middleware (localStorage).
   - `sessionStore` — current session ID, journey run ID, with `persist` middleware.
   - Stores are minimal (2-5 fields each) with simple setter actions.

The two libraries do not overlap — TanStack Query never stores client-only state, and Zustand never caches server responses.

## Consequences
- **Positive:** Clear separation between server and client state eliminates the "stale cache" class of bugs.
- **Positive:** TanStack Query handles refetching, deduplication, and garbage collection automatically.
- **Positive:** Zustand stores are ~10 lines each — minimal boilerplate compared to Redux.
- **Positive:** Both libraries support React 18 concurrent features.
- **Negative:** Developers must learn two libraries instead of one unified store.
- **Negative:** Complex flows that need both server and client state (e.g., "create run then store ID") require coordination between useMutation callbacks and Zustand setters.
- **Neutral:** Bundle size impact is minimal (~13KB combined gzipped).
