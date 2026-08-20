# Plan

1. [done] Confirm the inconsistent top-level versus Work-detail tab gestures
   and visual cues in the current tree.
2. [done] Record the superseding ruling: all tabs are bracketed, the active tab
   is highlighted, and `[`/`]` navigate tabs at the current view level.
3. [done 2026-08-19] Revalidate the ruling against the current TUI input modes, then
   implement the shared tab grammar without changing pane navigation.
4. [done 2026-08-19] Add focused virtual-screen and real-terminal regressions for both
   tab levels, wrap-around, context separation, aliases, command input, and
   narrow layouts; update operator documentation and hints.
5. [done 2026-08-19] Independent review found two narrow-layout violations
   and one initially unclaimed W137 scope leak; see
   `review-2026-08-19T20-22-46Z.md`. The two regressions now pass unedited,
   W137 was claimed and returned separately, and W110 passed independent
   focused review. Final disposition is recorded in
   `review-2026-08-19T20-36-56Z.md`.
