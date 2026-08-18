# Plan

**Superseded — 2026-08-17:** The original marker plan below is preserved as
decision history but is no longer actionable. The confirmed follow-up at the
end of this file replaces its `>` presentation steps.

1. Revalidate pickup projection, Phase cue, Held field, heartbeat suffix, and
   JSON/TUI parity against ready, blocked, waiting, parked, and terminal Work.
2. Project pickup overdue only where an actual ready unclaimed pickup exists;
   dependency-blocked, waiting, parked, and terminal Work must not claim an
   overdue pickup obligation.
3. Render `>` for every open unclaimed Work and remove elapsed `!` transitions
   and the claimed heartbeat suffix. Keep readiness/wait/park facts separate.
4. Add focused state, six-minute-boundary, heartbeat/no-heartbeat, release,
   pass, terminal, refresh, parity, and packaged-TUI regressions.
5. Run focused tests and `just test-v11`, then return for independent review.

## Current plan — remove the redundant marker

**Status — 2026-08-18:** implemented and returned for independent review.
Steps 1-4 done; `docs/BATON-WORK.md` still describes the retired glyph and is
deliberately left to W5, which owns it (see PROGRESS.md).

1. [done] Remove `>` from Phase and Held without changing canonical projection data.
2. [done] Preserve the Held timer origins and cap; use the blank/nonblank Current cell
   as the one claimant cue.
3. [done] Update state, parity, refresh, and packaged-TUI regressions for claimed,
   handed-off, fresh-unclaimed, blocked, waiting, parked, and terminal Work.
4. [done] Run focused tests and `just test-v11`, then return for independent review.
5. [done] Resolve first-round review gaps and receive independent sign-off in
   `review-2026-08-18T04-38-35Z.md`.
