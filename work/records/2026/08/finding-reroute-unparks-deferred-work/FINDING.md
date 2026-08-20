# Finding: reroute silently un-parks deliberately deferred Work

## Discovery context

Observed while implementing `W2571`
(`finding-recursive-target-graph/findings/finding-active-work-claim/findings/
finding-pass-requires-current-claim`). Filed rather than fixed inside Work
already held, per `AGENTS.md`. Not caused by that change; W2571 raises its
importance because it makes `reroute` the ONLY way to move unclaimed parked
Work.

## Observed — 2026-08-20

`transitions.reroute_work` re-derives the phase through `_unclaimed_state`,
which answers exactly two values: `block` when a gate is unsatisfied, and
`queued` otherwise. `parked` is not among them, so a reroute moves a
deliberately deferred Work back to `queued`:

    phase work=W2 to=parked reason="deferred to next cycle"   -> parked
    reroute work=W2 to=lang.rev reason="queue correction"     -> queued

Measured on a throwaway instance at `bafc74f` plus the W2571 gate; the
`reroute` event's own payload records `"phase": "queued"`.

## Why this looks wrong

The operation's own comment states the opposite intent:

> Everything else is deliberately untouched: the claim is already absent, the
> gates and dependencies are unchanged, and the planned Next is a separate
> decision this correction does not get to make. The phase is re-derived only
> because a route change can change nothing about readiness — it is asserted,
> not moved.

For `queued` and `block` that holds — the derivation reasserts what readiness
already implies. `parked` is not a readiness fact at all: it is a deliberate
human deferral with a recorded reason, on the same closed scheduler axis. A
correction to WHERE unclaimed Work is offered silently discards the decision
that it should not run yet, and the reason given for the park survives only in
the earlier event.

**Confirmed:** the behaviour, the derivation that causes it, and the payload.
**Inferred:** that it is unintended. The comment argues for preservation and
the code does not implement it, but no record rules on `parked` across a
reroute, which is why this is a finding and not a patch.

## Proposed direction

Preserve `parked` across a reroute — carry the phase through unless readiness
genuinely changed — and add a focused regression that a parked Work rerouted to
another endpoint is still parked, with its reason intact. `_unclaimed_state`
has other callers (`pass`, `release`, recovery, readiness recomputation) whose
contracts are pinned elsewhere, so the correction likely belongs in
`reroute_work` rather than in the shared derivation. **Open:** whether an
operator rerouting parked Work should instead be refused and told to unpark
deliberately, which would keep one meaning per operation.

## Confirmed decision — 2026-08-20

Rerouting changes where unclaimed Work is offered; it does not resume Work
that was deliberately parked. A reroute of parked Work therefore:

- preserves the `parked` scheduler phase and the durable park reason;
- changes the Route and starts the corresponding assignment episode for a
  future explicit resume, without making the Work runnable or waking an agent;
- records `parked` in the reroute event payload so the event agrees with the
  committed row.

Queued and blocked reroutes retain their existing readiness-derived behavior.
Only the explicit parked-to-queued phase transition resumes parked Work. The
alternative of refusing a parked reroute is rejected: Route and scheduler
phase answer separate questions, so correcting one must not require changing
the other.

## Acceptance boundary

1. A parked Work rerouted to another endpoint or route is still parked
   afterwards, with its recorded reason unchanged and no readiness wake.
2. `queued` and `block` reroutes keep deriving exactly as they do now,
   including the gated case W2571's restatements depend on.
3. The `reroute` event payload agrees with the committed row.
4. The complete v11 gate passes before independent review.
