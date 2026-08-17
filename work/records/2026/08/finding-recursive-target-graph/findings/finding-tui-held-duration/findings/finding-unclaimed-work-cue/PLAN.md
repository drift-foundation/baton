# Plan

**Status — 2026-08-17:** Confirmed; queue after the overlapping W55 Held-scale
follow-up.

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
