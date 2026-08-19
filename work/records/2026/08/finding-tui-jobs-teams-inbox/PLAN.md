# Plan

1. Revalidate this record against the completed W17 projection and current
   projection/TUI code before implementation; append explicit supersession if
   W17 changes any shared assumptions. — **done** 2026-08-19. W17 and W39 both
   closed while this record waited; the supersessions (W17's `[poke:N]`
   counter, and the impl2 route's partial changes) are recorded in
   `PROGRESS.md`.
2. Define the typed CLI/JSON projections for the Teams roster and the
   participant-relative Inbox, including total, unseen, and owed-action state.
   — **done**: `projection.teams()`, `projection.inbox()`, the `teams` and
   `inbox` verbs, projection version 12.1.
3. Add the top-level `[Jobs] [Teams] [Inbox total/unseen]` shell, with tabs on
   the left, participant identity on the right, and no legacy
   `[oblig] [park] [due]` header counters. — **done**; `Tab`/`Shift-Tab`
   cycle, and `[`/`]` keep their Work-detail meaning.
4. Implement Teams navigation, member inspection, poke initiation, and raw
   structured poke-answer display. — **done**.
5. Implement Inbox rows, contextual navigation, supported actions, and bold
   owed-action signaling independent of seen state. — **done**.
6. Add focused model, JSON, navigation, rendering, narrow-terminal, and
   workflow tests, then run the complete v11 gate and return for independent
   review. — **done**: `tests/work/test_w25_jobs_teams_inbox.py` (32 cases,
   one real-pty), the gate green, passed back to `baton.bug`.

One question is deliberately left open for review rather than decided by the
implementer: whether the standalone poke record (`p`) should fold into Teams
entirely now that Inbox owns owed pokes. See `PROGRESS.md`.
