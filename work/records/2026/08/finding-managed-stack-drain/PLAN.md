# Plan — Drain managed dispatch before maintenance

1. [completed 2026-08-22] Revalidate the confirmed drain boundary against the current
   lifecycle manager, Codex readiness paths, and ACP bridges. Identify the one
   authoritative deployment state and every dispatch edge it must gate.
2. [completed 2026-08-22] Specify the SQLite authority schema and durable `running` →
   `draining` → `paused` → `running` transitions, including the monotonic
   control generation, claimed-assignment boundary, claim-admission race,
   restart recovery, and explicit blocker reporting. Use one typed singleton
   table; derive remaining claims from canonical assignments and reserve JSON
   for protocol projection only. The implementation boundary and regression
   matrix are recorded. Drain/resume require the narrow accepted-config
   `dispatch` capability, initially granted only to `baton.slaw`; status is
   readable by every accepted participant, and no Route, runtime owner,
   `recover`, or `config` inference grants control.
3. [completed 2026-08-22] Implement drain/status/resume authority operations and projections
   without converting Work phase or agent prose into global lifecycle
   authority.
4. [completed 2026-08-22] Gate every managed readiness and ACP dispatch path at the same
   boundary while allowing snapshot claims to relinquish normally.
5. [completed 2026-08-22] Project the global state through home/root and readiness APIs,
   including generation, actor, time, and remaining blockers; add global
   control events and the persistent TUI/status presentation.
6. [completed 2026-08-22] Add focused race, failure, timeout, restart, discoverability, and
   resume tests plus operator documentation.
7. [changes requested 2026-08-22] Independently review the fail-closed
   boundary before deployment. Correct the three review findings in
   `review-2026-08-22T16-25-29Z.md`: lossless deterministic pagination for
   same-sequence control events, one-snapshot dispatch/action projection, and
   settlement timestamps from the authority's injected clock. Retain focused
   regressions for each boundary, then return for re-review.
7a. [done 2026-08-22] Corrected all three, each independently
   mutation-checked. `dispatch_history` pages whole INSTANTS with a
   deterministic sibling order and a cursor that names the last instant;
   `dispatch_view` is self-snapshotting and `wait` derives actions and
   dispatch under one outer reentrant snapshot, with the writer interposed
   INSIDE the read from a second connection; `_settle_dispatch` takes the
   writer's clock, covered for the immediate empty drain and a later final
   release. 31 focused cases, up from 27.
   Evidence: `evidence/correction-projection-edges-2026-08-22.txt`.
7b. [changes requested 2026-08-22] Independent correction re-review confirms
   the history and snapshot fixes, but finds one residual clock split: an
   empty drain samples the authority clock once for `drain_requested` and
   again for same-sequence `pause_reached`, so one indivisible authority
   instant can carry two timestamps. Review:
   `review-2026-08-22T17-57-11Z.md`; evidence:
   `evidence/re-review-single-instant-clock-2026-08-22.txt`.
7c. [done 2026-08-22] One sample per write. `Authority.instant()` is the
   sampled instant of the write in progress; `_write` takes it ONCE inside
   the transaction, after the operation-replay check, and clears it in a
   `finally` however the write ends. `drain_dispatch`, `resume_dispatch` and
   `_settle_dispatch` read it back, so an empty drain's two same-sequence
   control events carry one timestamp. `instant()` REFUSES outside a write
   rather than falling back to `clock()`, and both the refusal and the
   clearing are witnessed. The reviewer's ticking-clock case is retained;
   two added — a later final release carrying ITS act's instant, and the
   sampled instant not outliving its write. Four mutations, each fails
   exactly the case that names it. One call site outside this Work changed
   and is recorded: `create_trial`'s R42 in-lock recheck now reads
   `instant()`, which is what its own comment already asked for in words.
   2919 + 52 pytest, 297 Node, 55 ACP; the six other failures belong to
   W4996 and W2929 and were not touched from here.
   Evidence: `evidence/correction-single-instant-2026-08-22.txt`.
7d. [done 2026-08-22] Independent re-review confirms one sampled instant per
   real write, exact reuse by drain/resume/settlement, and unconditional
   clearing. The ticking empty-drain, later-release, refused-write leak, and
   WS-2 deadline cases pass. Signed off in
   `review-2026-08-22T18-38-04Z.md`; no reviewer finding remains.
8. [approved; next-deployment action] In the next fresh schema-28 authority,
   grant `dispatch` only to `baton.slaw`, accept that generation, and use
   lifecycle manifest version 2 with its explicit Baton binary/config/
   participant control triple. Keep ordinary `stop` as the emergency path and
   use `stop-drained` for planned maintenance. Before closing W4615, verify a
   live `running -> draining -> paused -> running` cycle, claim-admission
   refusal after the boundary, and `stop-drained` refusal/success on the
   corresponding states. Do not attempt this through deployed schema-27
   `c529b28`.

## Implementation notes — 2026-08-22

Landed under the pinned boundary, with the divergences recorded in
`FINDING.md` under "Implementation revalidation — 2026-08-22":

- authority schema 27 -> 28: `dispatch_control` singleton and the typed
  `dispatch_events` journal, seeded `running` at creation;
- `Authority._write` settles `paused` after every mutation, so ANY
  Handler-clearing path can end the finishing round;
- `claim_work` refuses admission in `draining`/`paused` inside the write
  transaction;
- `drain`/`resume` transitions gated on the accepted `dispatch` capability,
  checked in that same transaction;
- `dispatch_view`/`dispatch_history` projections, carried by `home` and by
  `wait`; `participant_actions` deliberately unfiltered;
- projection minor 12.3 -> 12.4 (additive);
- `drain`, `resume`, `dispatch` CLI verbs; `drain`/`resume` recorded as
  managed-workflow policy EXCLUSIONS;
- TUI dispatch label in both header paths through one shared painter;
- `infra.py` manifest version 2 with the named control triple, plus `drain`,
  `resume`, `dispatch` and the graceful `stop-drained`;
- 27 focused regressions in `tests/work/test_w4615_dispatch_drain.py`.
