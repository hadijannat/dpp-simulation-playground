# ADR-008: CSS Custom Property Design Token System

## Status
Accepted

## Date
2026-02-05

## Context
The frontend initially used hardcoded hex color values (`#cbd5f5`, `#dcfce7`, `#64748b`, etc.) scattered across component files. This caused:

- Inconsistent colors when similar-but-not-identical values were used for the same semantic purpose.
- No support for dark mode or theme switching without find-and-replace across all files.
- Difficulty auditing the visual design — no single source of truth for the color palette.
- Accessibility issues when contrast ratios weren't consistently maintained.

## Decision
Implement a **CSS custom property (variable) design token system** in `frontend/src/design/tokens.css`:

1. **Primitive tokens** define the raw palette: `--blue-600`, `--slate-300`, etc.
2. **Semantic tokens** map primitives to purposes: `--ink-primary`, `--surface-card`, `--accent`.
3. **Component tokens** map semantics to specific UI elements: `--canvas-node-bg`, `--canvas-node-completed`, `--progress-fill-start`, `--text-muted-light`.
4. **All component files** reference tokens via `var(--token-name)` instead of hex values.
5. **Dark mode** (future) can be implemented by redefining semantic tokens under a `[data-theme="dark"]` selector — no component changes needed.

Token hierarchy:
```
Primitives (--blue-600)
  → Semantics (--accent: var(--blue-600))
    → Components (--canvas-node-selected: var(--accent-light))
```

## Consequences
- **Positive:** Single source of truth for all colors, spacing, and motion values.
- **Positive:** Theme switching requires only redefining semantic tokens.
- **Positive:** Design audits are trivial — scan `tokens.css` instead of the entire codebase.
- **Positive:** Zero runtime cost — CSS custom properties are resolved by the browser engine.
- **Negative:** Developers must look up token names instead of typing hex values directly. Mitigated by IDE autocompletion.
- **Negative:** Deep token chains (`var(--a)` → `var(--b)` → `var(--c)`) can be hard to trace. We limit nesting to 2 levels.
- **Neutral:** Existing components were migrated from hardcoded values to tokens (SimulationCanvas, StoryNavigator, ProgressTracker, CatalogBrowser, AchievementPanel, StreakIndicator).
