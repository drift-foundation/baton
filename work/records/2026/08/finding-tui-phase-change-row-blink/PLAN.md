# Plan

**Status — signed off 2026-08-18.** All four steps are complete and the
independent review is clean; see `review-2026-08-18T19-49-09Z.md`.

**Prior status — 2026-08-18:** reviewer enrichment complete;
implementation-ready for `baton.impl` after W78, which changes the same
phase/TUI surfaces.

1. [done] Revalidate the existing phase-change observation and three-cycle
   countdown against the current TUI renderer.
2. [done] Compose `A_BLINK` into the complete painted Work-row attribute,
   preserve selection and personal bold semantics, and remove the Phase-only
   blink overpaint.
3. [done] Update `test_w33_claim_age.py`, `test_w336_blink_drain.py`,
   `test_w84_hot_cue.py`, `test_w23_bold_title.py`, and parity/PTY coverage for
   wide and narrow layouts, selection+bold composition, cold load, genuine
   phase change, countdown drain, heartbeat, failed refresh, and steady state.
4. [done] Run the focused TUI gate and `just test-v11`, then return for
   independent review.
