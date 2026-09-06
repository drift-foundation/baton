# Plan

**Status: implemented and independently signed off.**

1. [done] Record the `f` chooser and `[p] Parked` toggle decision.
2. [done; baton.tuner 2026-09-06] Revalidate the current Jobs-row, modal-input, selection, refresh,
   filter-disclosure, and help surfaces before changing code.
3. [done; baton.tuner 2026-09-06] Add the client-local chooser and hide-parked state without adding
   protocol or SQLite state and without changing machine scheduling.
4. [done; baton.tuner 2026-09-06] Keep the active reduction visible and repair selection
   deterministically when filtering removes the selected row.
5. [done; baton.tuner 2026-09-06] Add focused positive, reversal, cancellation, refresh, selection,
   and closed-toggle interaction tests. Existing assertions or expected
   behavior may be edited only where this approved UX explicitly supersedes
   them.
6. [done; baton.tuner 2026-09-06] Run the focused TUI suite, diff hygiene checks, and the complete
   v11 gate; return for independent review.
7. [done; baton.codex 2026-09-06] Independently verify the bounded candidate,
   focused regressions, and complete v11 gate; record digest-bound sign-off.

Expected implementation boundary, subject to revalidation:

- `src/baton_work/tui/app.py`
- `tests/work/test_tui.py`
