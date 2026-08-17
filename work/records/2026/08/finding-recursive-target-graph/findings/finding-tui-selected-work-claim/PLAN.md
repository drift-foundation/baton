# Plan — claim the selected Work directly from the TUI

1. **Decision** — **confirmed 2026-08-16:** lowercase `c` in the Work table
   applies canonical `claim` to the selected row.
2. **Implementation** — queued as v11 Work `W235`. Route the shortcut through the existing command
   executor and refresh scheduler; do not add a second authority mutation path.
3. **Regression coverage** — queued. Pin successful selection claim, selection
   preservation and refresh, plus blocked, ineligible, terminal, and competing
   claim diagnostics with no local-state fiction.
4. **Verification** — queued. Run focused TUI tests and `just test-v11` before
   independent review.
