# Finding: active Work must be atomically claimed before work begins

## Observed

W92 was passed to `baton.impl` and implementation began while its canonical
phase remained `queued`. With one handler this produced a misleading Work
view. With two or more eligible handlers behind the same route, both could
begin the same work because neither has atomically established that they are
the active worker.

## Confirmed decision — 2026-08-16

**Confirmed by Slawomir during the fresh-authority cutover.** No participant
starts work while a Work item is merely queued. Beginning work requires one
eligible handler to atomically claim the Work as active. `active` is therefore
an authority-backed work claim, not only a descriptive phase.

- The first eligible handler that successfully performs `queued → active`
  becomes the active participant recorded by the authority.
- A concurrent or later attempt by another handler must refuse without
  changing state and expose that the Work is already active. Two agents must
  never both believe they acquired it.
- Clients project the active participant so humans and agents can see who is
  working, rather than inferring from route membership or audit history.
- Discussion and planning may occur while queued, but implementation, review,
  or other execution owned by the current endpoint starts only after the
  active claim succeeds.
- Leaving active through pass, waiting, parking, terminal close, or an explicit
  recovery/handoff releases or replaces the claim according to a ruled
  transition. A transfer does not silently claim active for the recipient.
- Exact retry by the successful claimant must not create a second transition;
  conflicting claim attempts fail closed.

The transition matrix for release/recovery and whether the public verb remains
`phase ... active` or gains a clearer `start` spelling must be resolved before
implementation. The invariant and atomic claimant identity are not optional.

This is a next-schema requirement and must be present before the fresh v11
authority becomes the release candidate.

## Classification clarification — 2026-08-16

**Confirmed by Slawomir.** The fresh schema requires the submitter to choose a
concrete classification when creating Work. `unknown` is not accepted for new
Work. The current handler may reclassify at any later open-state point, but
activation does not require a second classification act merely to repeat what
submission already established.

The atomic start/active claim and required submission classification are two
independent invariants: classification says what the Work is currently
believed to be; the active claim says exactly which eligible participant is
executing it.

## Readiness and pass clarification — 2026-08-16

**Confirmed by Slawomir after W92 exposed the stale-active case.** The
authority must refuse an attempt to mark or claim Work `active` while that
Work has any unmet dependency or unresolved child. This is an in-transaction
readiness check, not a client-side convention: observing `ready` before the
attempt is only advisory, and a dependency arriving before commit must make
the claim lose.

Passing Work releases its active claimant and never makes the recipient
active implicitly. The passed Work becomes `queued` when it is ready to run,
or `waiting` when an unresolved dependency/child prevents progress. Its new
Current handler must later acquire the active claim explicitly after the Work
is ready. Consequently, Work may never project `phase=active` together with
`ready=false`, and an active participant from before a pass may never survive
that pass.

## Active ownership is orthogonal to phase — 2026-08-16

**Confirmed by Slawomir to permit pipeline parallelism. This explicitly
supersedes the earlier wording that defined acquisition as `queued → active`
and the derived `phase=active` invariant above.** Active ownership is its own
authority state, not a phase value.

- `active_team` / `active_member` answer who, if anyone, is executing the
  Work now.
- `phase` answers what kind of work is happening: for example `research`,
  `active` implementation, or `review`.
- Claiming Work records the participant without silently changing its phase.
  A reviewer may therefore be the active claimant while phase is `review`.
- Each Work has at most one active claimant. Independent Work may have
  different active claimants concurrently: while a reviewer handles Work A,
  an implementer may claim and execute unrelated Work B.
- Claim acquisition still requires open, ready, non-waiting/non-parked Work
  and a participant authorized by the live Current endpoint, all rechecked in
  the write transaction. Waiting, parked, blocked, and terminal Work cannot be
  claimed.
- Pass, entry into waiting/parked, close, and explicit recovery release the
  claimant. A recipient is never auto-claimed.

The earlier pass outcome remains: pass leaves runnable Work queued and blocked
Work waiting. The recipient explicitly claims it and may then set the honest
work phase. This small unclaimed handoff interval is not duplicate execution;
clients and runners must make ready queued Work prominent so it is claimed
promptly.

## Current and phase move together on handoff — 2026-08-16

**Confirmed by Slawomir. This supersedes the generic queued/waiting pass
outcome in the two sections immediately above.** Phase describes the stage of
work expected from Current, so changing Current without changing phase leaves
a false handoff.

- A pass atomically records the destination Current endpoint and the
  destination phase. K assigning Work to the reviewer sets the reviewer route
  as Current and phase `review` in that same event.
- The pass releases the sender's active claim and never auto-claims the
  recipient. The reviewer claims it separately before beginning review.
- Returning changes to an implementation Current similarly records the
  implementation-stage phase in the pass; research and other handoffs record
  their honest destination phase rather than carrying the sender's phase.
- Dependency-derived readiness remains orthogonal. Work assigned for review
  may project phase `review` while `ready=false` because another Work blocks
  it; that prevents active acquisition but does not relabel the intended stage
  as `waiting`.
- `waiting` and `parked` remain explicit handler decisions with their ruled
  conditions/reasons. A dependency edge alone does not silently rewrite the
  phase. New unclaimed Work may begin `queued`; a handoff does not use queued
  as a generic substitute for its actual destination phase.

Thus a pipeline can show Work A as Current reviewer, phase `review`, claimant
reviewer while Work B independently shows Current implementer,
implementation phase, claimant implementer. Current+phase communicate the
stage; claimant identity prevents duplicate execution.

## Research is active work — 2026-08-16

**Confirmed by Slawomir while multiplexing W3 implementation with W5 design
research.** Substantive research is work and may last long enough that the
team needs to see who is doing it. Before research begins, the responsible
member records phase `research` and acquires the Work's active claim. The
claimant identity prevents duplicate investigation; claim Age and heartbeat
apply exactly as they do to implementation and review.

`queued` means no participant is currently executing the Work. Reading a
title or doing a momentary prioritization pass does not require a claim, but
repository investigation, contract design, reproductions, or other sustained
research does. Finishing research either passes the Work with its honest next
phase, releases it with a reason, parks/waits it through the ruled transition,
or closes it; it does not leave a claimed Work labelled queued.

## Effective-Baton release-documentation gate — 2026-08-16

**Confirmed by Slawomir.** When protocol 11 lands,
`docs/EFFECTIVE-BATON.md` must teach these phase/claim transitions as critical
operating practice, not merely describe their fields. As long as open Work is
neither parked nor condition-bound waiting, the team pipeline should expose
something genuinely being done: sustained research, implementation, and
review use their honest phase plus an active claimant; queued means awaiting
pickup. Independent Work may be claimed concurrently to keep the pipeline
saturated, while overlapping review/implementation surfaces remain serialized
or explicitly partitioned so nobody reviews a moving target.

The current document is explicitly a protocol-10 guide, so this requirement
is pinned here until the v11 documentation cutover. V11 is not considered
landed if the released Effective Baton guide omits it.

## Approval is visible claimed Work — 2026-08-16

**Confirmed by Slawomir.** When progress needs a human product ruling, the
question must not live only in chat while Baton still claims somebody else is
working. Pass the Work to the configured approval endpoint with phase
`review`, record the return endpoint as Next, and release the researcher's
claim atomically. The approver explicitly claims it before deciding, so
Current names the approver, the claim timer measures the approver's actual
decision time, and the Work is visibly parked in approval rather than hidden
behind a stale research state.

This is a transfer (`=>`), not merely an `@` obligation: the ruling is the
Work's current blocking activity. It is not dependency-blocked or
condition-bound `waiting`, because those states refuse claims and therefore
cannot truthfully time active approval. On disposition, the approver passes
the Work to its recorded Next with the honest destination phase, or closes it
when the ruling itself terminates the Work.

## Explicit claimant recovery — 2026-08-16

**Confirmed by Slawomir. This resolves the recovery authority left open in
the original active-claim decision.** An abandoned or intentionally yielded
claim is released through one explicit authority operation:

```text
release WORK --expect team.member --reason TEXT
```

- Any participant who is a currently resolved handler of the Work's live
  Current endpoint may release it, including the claimant releasing their own
  claim. Participation, discussion, or an `@` obligation does not grant this
  authority.
- `--expect` is mandatory compare-and-swap against the exact recorded
  claimant. No claim or a different claimant refuses inside the write
  transaction; recovery never guesses whose execution it is interrupting.
- `--reason` is mandatory, normalized non-empty durable evidence. Self-release
  and forced recovery use the same honest operation and both explain why the
  Work became unclaimed.
- A successful release clears only `active_team` / `active_member`. It does
  not change phase, Current, Next, readiness, dependencies, waiting state, or
  any discussion/obligation state.
- The mutation is effectively-once. An exact retry replays; changed expected
  claimant or rationale under the same operation id conflicts without
  mutation.
- Canonical transition discovery advertises `release` only to a resolved
  Current handler while a claimant exists. The write transaction remains the
  final authority under races and configuration changes.

This is recovery of execution ownership, not a workflow handoff. Passing,
waiting, parking, and close retain their separately ruled claimant-release
effects.

## Route-derived handoff phase — 2026-08-17

**Confirmed by Slawomir after the live ACP handoff exposed `impl + queued`.**
This supersedes the earlier allowance for a caller to state an explicit
destination phase on `pass`. A handoff already chooses a destination route;
the resolved route's stage role is the sole source of its destination phase.

- `pass` accepts no `phase=` operand. It resolves the destination endpoint and
  derives `research`, `active`, or `review` from that route's configured role
  inside the same authority transaction that changes Current and releases the
  sender's claim.
- Every role usable as a handoff destination must have one canonical stage
  mapping. Implementation maps to `active`; research maps to `research`;
  reviewer and approver map to `review`. A destination with no stage mapping
  refuses rather than asking the caller to repair the route with ad-hoc phase
  input.
- Explicit phase mutation remains available to the live Current handler when
  the same route changes stage without a handoff. It is not a second way to
  describe a route transfer.
- `queued` remains intake awaiting pickup. It is never the phase produced by
  a route transfer.

The live W49 counterexample was caused by passing to `baton.impl` with an
explicit `phase=queued`; Claude then acquired the orthogonal claim and began
execution while the TUI truthfully retained the false caller-supplied phase.
With more handlers, the atomic claim still prevents two winners, but clients
would schedule from misleading state and repeatedly lose acquisition races.
The authority must prevent the contradiction rather than relying on every
caller to remember a phase convention.
