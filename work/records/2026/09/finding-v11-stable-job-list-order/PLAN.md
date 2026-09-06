# Plan

**Status — implemented and independently signed off 2026-09-06.**

1. [done] Record the observed sibling inversion and supersede the shared
   human/readiness ordering rule for human-facing lists.
2. [done] Revalidate every human list and machine readiness consumer against
   the separate ordering contracts. `home`, `children`, and every `tree` read
   use display order; `participant_actions`, `_first_actionable`, and
   `actionable_work` (including its cursor binding) use dispatch order.
3. [done; baton.tuner 2026-09-06] In `src/baton_work/projection.py`, introduce explicitly named
   stable-display and dispatch orderings;
   preserve structural grouping, explicit priority, and creation order for
   display while retaining blocker-first pickup and current keyset cursor
   semantics for readiness.
4. [done; focused suite 19 passed] In `tests/work/test_w7_blocker_preference.py`, supersede the
   suite's shared-order expectations and add focused projection and TUI
   regressions for stable sibling order across state transitions,
   selection-preserving refresh, and retained blocker-first dispatch.
5. [done; baton.tuner 2026-09-06] In
   `tests/work/test_tui.py`, update only the two navigation sequences and
   adjacent stale W7 explanation in
   `test_the_focused_facts_and_collapse_come_from_the_projection`; retain all
   assertions and fixture behavior. Re-run focused and complete v11 gates and
   return the bounded change for independent review.
6. [done; baton.codex 2026-09-06] Verify the three digest-bound candidate
   paths, the focused projection/TUI behavior, diff hygiene, and the complete
   v11 gate. No findings remain.

Filters that hide parked or blocked Work remain a later UX enhancement.

The authorized change set is exactly:

- `src/baton_work/projection.py`
- `tests/work/test_w7_blocker_preference.py`
- `tests/work/test_tui.py` (only the named test's two navigation sequences and
  stale ordering explanation)
