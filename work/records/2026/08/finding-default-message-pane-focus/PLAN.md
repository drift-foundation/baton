# Plan

**Status — 2026-08-20:** implemented and gated by `baton.claude` under Work
`W2597`; awaiting independent review.

1. [done] Revalidate every fresh Work-detail entry path and distinguish it
   from refresh/tab-return focus preservation. Three fresh paths (Jobs,
   search, Inbox); the only genuine "return" in this console is a detail TAB
   switch, which already preserves per-tab focus. Both asserted.
2. [done] Default fresh Messages-tab focus to the Message index while keeping
   the existing Topic autoselection and Message new-first selection:
   `DETAIL_ENTRY_FOCUS` and `Console._enter_detail`, one helper shared by all
   three paths.
3. [done] Cover Jobs, search, Inbox, multi-Topic, empty-Topic, and empty-Work
   entry without authority writes:
   `tests/work/test_w2597_detail_entry_focus.py`, 17 cases. NOTE: the
   empty-Work and empty-Topic states are unreachable through the public
   surface — see `PROGRESS.md`; the renderer's guard is covered directly and
   the reachable half is asserted for real.
4. [done] Run the focused TUI suite and the complete v11 gate: 2692 parallel,
   51 serial, 55 ACP after the round-1 correction.
5. [done] Independently review the behavior and regressions.
   Round 1 (`review-2026-08-20T12-31-04Z.md`) requested changes: a fresh entry
   retained `detail_tab`, so leaving from Events and opening another Work
   opened it on Events. Corrected in the shared fresh-entry boundary, together
   with the same leak in the Events cursor/page/focus found while fixing it;
   four regressions added and the gate re-run at 2692/51/55. Round 2
   (`review-2026-08-20T12-39-13Z.md`) signed off after independent focused
   verification.
