# Plan

**Status — 2026-08-20:** implemented and gated by `baton.claude`; independently
reviewed clean and approved for satisfying closure.

1. [done] Preserve `parked` and its reason across reroute; Route correction is
   independent of the explicit scheduler transition that resumes Work.
2. [done] Implement the ruling in `reroute_work` without disturbing
   `_unclaimed_state`'s other pinned callers. The derivation is untouched; the
   carve-out is local to `reroute_work` and mirrors the one
   `_recompute_ready` already makes for the same reason.
3. [done] Focused regressions for parked, queued and gated reroutes, and for
   the event payload agreeing with the committed row:
   `tests/work/test_w2645_reroute_preserves_parked.py`, 16 cases. The contract
   is also stated in `docs/EFFECTIVE-BATON.md` and the `reroute` CLI help.
4. [done] Focused suites and the complete v11 gate.
5. [done] Independent review is clean; see
   `review-2026-08-20T11-59-35Z.md`.
