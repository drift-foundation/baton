# Plan

**Status — 2026-08-16:** signed off in
`review-2026-08-16T15-49-33Z.md`. The former W14 serial blocker is closed.

1. Replace the visible `b links` footer/help label with `[b] deps` everywhere
   it describes the dependency-neighbor view.
2. Preserve the `b` binding, graph projection, and empty-state behavior.
3. Add focused wide/narrow PTY assertions preventing the ambiguous label from
   returning.
4. Run focused coverage and `just test-v11`, then return for review.
