# Plan — claim the selected Work directly from the TUI

**Status — revalidated 2026-08-17:** implementation-ready as W235. The current
table handler has navigation, detail, unfold, dependency, and visibility keys
but no lowercase `c` branch. `Console.execute()` already routes typed commands
through the canonical CLI parser/authority operation and schedules the one
refresh path only after a committed mutation. Reuse those surfaces; do not
write claim state in the TUI.

1. **Decision** — **confirmed 2026-08-16:** lowercase `c` in the Work table
   applies canonical `claim` to the selected row.
2. **Implementation** — route the selected row's canonical id through the
   existing command executor and refresh scheduler; do not add a second
   authority mutation path. The shortcut is scoped to normal Work-table
   navigation, never command/batch/search-entry text or the detail panes.
3. **Regression coverage** — pin successful selection claim, selection
   preservation and refresh, plus blocked, ineligible, terminal, and competing
   claim diagnostics with no local-state fiction.
4. **Verification** — run focused TUI tests and `just test-v11` before
   independent review.
