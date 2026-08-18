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

## Reopened — 2026-08-18

**Status — signed off by `baton.codex` on 2026-08-18.** The same-phase
`M…`→`W…` retarget records its episode boundary on the causing response or
disposal, and the final-gate clear records exactly one boundary on the real
wake. See `review-2026-08-18T19-33-27Z.md`.

**Prior status — changes requested 2026-08-18 in
`review-2026-08-18T17-23-47Z.md`.** The terminal-gate P1 is fixed, but a
Message-to-Work retarget updates the stored gate silently: its causing
response/disposition event carries no `gate_now`, so the historical episode
boundary is lost.

**Prior status — 2026-08-18: changes requested in
`review-2026-08-18T15-44-49Z.md`.** Steps 5-9 were returned for independent
review: schema
20 commits one typed gate episode, projection 10.0 replaces `waiting_on` with
the structured `gate` and renames the phase to `block`, the TUI derives `Wait`
and `Held` from that structure alone, and
`tests/work/test_w78_typed_timed_gates.py` walks the revalidated acceptance
boundary clause by clause.

**Prior status — 2026-08-18:** reviewer revalidation complete;
implementation-ready for `baton.impl`. The exact authority gap and multi-gate selection/reset rules
are pinned in `FINDING.md` under "Implementation revalidation".

1. [superseded] Split obligation waiting from dependency blocking.
2. [confirmed] Use one blocked scheduler phase for every unsatisfied gate and
   identify its typed cause in `Wait`: `W…` for Work, `M…` for the source
   Message of a directed obligation.
3. [confirmed] Time every blocked row from when its displayed typed gate became
   active; reset only when that gate changes. Never use an unrelated older
   handoff or last-change instant.
4. [confirmed] Active rows time from the current claim. Queued, parked,
   unclaimed-handoff, terminal, and other non-active/non-blocked rows show `-`.
5. [ready] Replace public `waiting` with `block` and make the authority commit
   one typed current-gate episode plus its canonical start instant. A change of
   displayed gate is authoritative even when phase stays `block`.
6. [ready] Project the structured Work/Message gate; render `Wait=W…[/+N]` or
   `Wait=M…`, and derive blocked Held only from the projected episode start.
   Preserve structured handoff/pickup history without using it for Held.
7. [ready] Update CLI grammar/help, scheduler/wake/pass/release/request paths,
   Work detail/list projections, Events playback, TUI, and JSON/TUI parity.
8. [ready] Add focused coverage in `test_w38_scheduler_phase.py`,
   `test_w39_dependency_cue.py`, `test_w159_request_waits.py`,
   `test_dependency_correction.py`, `test_w47_event_phase_intervals.py`,
   `test_w226_held_pickup.py`, `test_phase.py`, and packaged TUI/parity tests.
   Include same-phase W1→W2 and M1→W1 episode resets plus unrelated-event
   non-resets.
9. [ready] Run focused gates and `just test-v11`, then return for independent
   review with the schema/projection version decision and break-sweep evidence.

10. [in progress] Clear the typed gate episode when blocked Work closes
    terminally, retain the added regression, rerun the focused and complete
    v11 gates, and return for review.
11. [changes requested] Record the same-phase `M...` to `W...` gate boundary
    on the causing response/disposition event without inventing a phase
    transition or duplicating the final-gate wake boundary. Retain the additive
    regression and rerun focused plus complete v11 gates.
