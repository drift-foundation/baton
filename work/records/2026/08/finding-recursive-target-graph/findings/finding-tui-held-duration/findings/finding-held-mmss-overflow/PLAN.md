# Plan

**Status — 2026-08-17:** Confirmed and implementation-ready as a presentation-
only follow-up to closed W226.

1. Revalidate `held_cell`, `held_field`, the six-cell column budget, and W226's
   state-dependent origin/prefix/suffix tests against the current tree.
2. Change the pure formatter to elapsed whole seconds and `MM:SS`; render `∞`
   at 100 minutes and beyond while preserving the negative-clock clamp and
   no-origin dash.
3. Update claimed, pending, overdue, heartbeat-stale, repass, terminal,
   responsive-layout, parity, and packaged-TUI tests without changing JSON or
   authority behavior.
4. Run the focused Work TUI tests and `just test-v11`, then return for
   independent review.
