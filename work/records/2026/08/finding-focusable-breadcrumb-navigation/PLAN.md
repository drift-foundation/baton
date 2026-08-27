# Plan

1. [done 2026-08-27] Confirm focusable breadcrumbs, `h`/`l` and cursor parity,
   Enter navigation, region cycling, horizontal visibility, textual selection
   feedback, and history-versus-hierarchy semantics.
2. [done 2026-08-27] Revalidated every breadcrumb page, focus graph,
   viewport/key owner, one-step Back contract, narrow behavior, and the W26328
   interaction. Recorded exact decision support and a 10-case green baseline
   in `evidence/reviewer-research-2026-08-27.md`.
3. [done approver 2026-08-27] Confirmed the structured location-reset model,
   Tab/Shift-Tab and Work-detail Ctrl-W graph, boundary Up/Down, same-tab Work
   jumps, exact page restoration, focused Left-versus-Esc rule, compact
   selectors, whole-token `…` viewport, and footer/narrow refusal.
4. [next implementation] Add the shared breadcrumb focus model, rendering,
   navigation and deep/history/narrow-terminal regressions.
5. [then review] Independently verify direct ancestor navigation, one-step
   Back restoration, key parity, focus visibility and no page-specific drift.
