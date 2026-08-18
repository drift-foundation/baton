# Finding: make Phase a scheduler state

Parent: `work/records/2026/08/finding-recursive-target-graph/findings/finding-active-work-claim/`

## Observed — 2026-08-18

W4 was claimed by Claude and genuinely executing, while W15 and W25 had only
been passed to `baton.impl`. All three displayed phase `active`; only W4 had a
non-null Current claimant. Slawomir reasonably read all three as concurrent
execution.

The authority was encoding destination workflow role into phase: an
implementation handoff became `active` before pickup and a reviewer handoff
became `review`. This duplicates route/role, while making the ordinary word
active mean something other than active work.

## Confirmed decision

Phase is a closed scheduler-state axis:

- `queued`: open, runnable, unclaimed;
- `active`: open and claimed;
- `waiting`: open, unclaimed, not runnable because a recorded dependency or
  condition-bound obligation is unsatisfied;
- `parked`: open, unclaimed, deliberately deferred without an automatic wake
  condition;
- terminal: phase is `null` in JSON and `-` in the TUI.

Route and its configured role say whether the work is implementation, review,
research, or approval. Current says which exact participant holds the claim.
Those meanings are not duplicated into Phase.

## Naming clarification — 2026-08-18

**Confirmed by Slawomir before implementation.** `Current` in the decision
above is renamed `Handler`. The final vocabulary is:

- Route: responsible endpoint now;
- Handler: exact claimed member, nullable;
- Next: planned future endpoint, nullable.

Route and Next are the same endpoint type. Handler is deliberately a member,
so the three concepts do not masquerade as one axis. Past assignments are
available through Events.

## Transition invariants

- `active` if and only if Handler is non-null. No public or internal operation
  may commit unclaimed active Work or a claimant under another phase.
- `claim` requires queued, ready Work and atomically sets Handler plus active.
- `pass` changes Route, clears Handler, and derives queued versus waiting from
  the resulting readiness. The destination role never selects phase.
- `release`, dependency insertion, condition-bound waiting, and every other
  claimant-releasing transition derive queued/waiting from the committed gate
  state. Satisfying the last gate wakes waiting Work back to queued; it never
  claims automatically.
- `parked` remains an explicit loose end. Terminal closure clears Phase and
  Handler atomically.
- Status remains the lifecycle axis (`open`/`closed` plus terminal outcome),
  and priority/classification remain orthogonal.

## Compound-wait clarification — 2026-08-18

Scheduler readiness is level-triggered over every live condition, not the
first condition that happened to put Work into `waiting`. If Work is waiting
on one directed obligation and acquires an independent dependency, resolving
the obligation does not make it runnable: it remains `waiting`, retargeted to
the aggregate dependency gate. Only satisfaction of the final live condition
moves it to `queued`, and only that false-to-true readiness transition mints a
new actionable episode.

## Acceptance

1. The authority rejects every phase/handler contradiction under direct,
   retry, and race paths.
2. Implementer, reviewer, researcher, and approver handoffs all land queued
   when runnable; claiming any of them produces active.
3. Dependency and obligation gates produce waiting and wake exactly once to
   queued when satisfied, without claiming.
4. Release, pass, park, close, dependency changes, and configuration changes
   preserve the invariant atomically.
5. JSON uses full state names and terminal `null`; the TUI uses compact labels
   and terminal `-`, with Route/Handler/Next showing responsibility, exact
   claimant, and planned destination.
6. Workflow stories, readiness episodes, Events, operator documentation, and
   a fresh authority all agree on the simplified model.

## Compatibility

This is intentional protocol-11 trial evolution. Client compatibility is not
a release constraint yet. The projection must advance if the participant
action contract changes, and all co-deployed readiness consumers must be
updated in the same candidate.
