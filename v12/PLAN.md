
## Implementation notes — 2026-08-22

Landed under the pinned boundary, with the divergences recorded in
`FINDING.md` under "Implementation revalidation — 2026-08-22":

- authority schema 27 -> 28: `dispatch_control` singleton and the typed
  `dispatch_events` journal, seeded `running` at creation;
- `Authority._write` settles `paused` after every mutation, so any
  Handler-clearing path can end the finishing round;
- `claim_work` refuses admission in `draining`/`paused` inside the write
  transaction;
- `drain`/`resume` transitions gated on the accepted `dispatch` capability,
  checked in the same transaction;
- `dispatch_view`/`dispatch_history` projections, carried by `home` and by
  `wait`; `participant_actions` deliberately unfiltered;
- projection minor 12.3 -> 12.4 (additive);
- `drain`, `resume`, `dispatch` CLI verbs; `drain`/`resume` recorded as
  managed-workflow policy EXCLUSIONS;
- TUI dispatch label in both header paths through one shared painter;
- `infra.py` manifest version 2 with the named control triple, plus `drain`,
  `resume`, `dispatch` and the graceful `stop-drained`;
- 27 focused regressions in `tests/work/test_w4615_dispatch_drain.py`.
