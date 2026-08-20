# Finding: readiness queues forever behind a wedged target turn

## Observed — 2026-08-20

The `baton.codex` readiness producer continued to consume canonical actions
and forward them to the `baton-reviewer` dispatcher target. The configured
Codex target Thread had entered `waiting-input(approval)` at
`2026-08-20T04:07:47Z`, however, and never completed that turn.

The dispatcher logged every later readiness event as:

```text
event received: v11-action-ready
unavailable or active; queued (N)
```

By the time W2938 returned for review at `14:47:55Z`, 24 events were queued
behind that one turn. No wake reached the live reviewer conversation. The
reviewer found W2938 only by manually invoking canonical `wait`, then claimed
it at sequence 3238.

This is not a Baton authority/readiness-producer failure: the producer log
shows `work:bcbb9dbf-W2938:3231:g2` forwarded, and the dispatcher log shows it
received. It is a delivery-target liveness failure after receipt.

## Confirmed expectation

Readiness delivery is independent of whether the reviewer happens to type or
manually poll in another conversation. A target turn waiting indefinitely on
an approval cannot silently absorb all later readiness wakes while the stack
continues to present that target as healthy.

The product must detect that the configured target cannot accept a wake and
surface/recover the condition without approving the blocked command. Manual
`wait`, manually inspecting dispatcher logs, or remembering to poll during
ordinary conversation are diagnostics/workarounds, not the delivery model.

## Relationship to earlier findings

W482 (`finding-dispatcher-target-readiness`) proved that every configured
target is connected and loadable. This episode is different: the target is
loaded but its active turn is permanently waiting for input, so the dispatcher
reports it as active and retains every event behind it.

W484 (`finding-codex-turn-completion-race`) fixed a completion arriving before
the waiter was installed. This episode never completes at all.

## Acceptance boundary

- A target turn that enters a non-self-resolving `waiting-input` state does
  not leave later readiness events silently queued forever.
- The dispatcher never approves or answers an agent's approval request.
- Target health/status distinguishes loadable-and-idle from loaded-but-unable
  to accept delivery, with the participant, Thread, turn, cause, queue depth,
  and oldest queued instant available to operators.
- Recovery has an explicit safe policy: either fail the target and require a
  fresh context, or deliver to a newly registered live context for the same
  participant. It must not send one participant's actions to another identity.
- Pending canonical actions remain level-triggered and are redelivered after
  recovery; an event is not lost merely because its first target wedged.
- Regressions cover an approval-waiting turn, more than one queued readiness
  event, recovery/redelivery, identity isolation, and stack health reporting.

## Confirmed v11 ruling — 2026-08-20

Treat dispatcher-owned readiness turns as non-interactive execution. When such
a turn requests command approval, the dispatcher must never approve it and
must not leave the request unanswered:

1. explicitly deny the request when the app-server protocol permits;
2. cancel/fail the managed turn within a bounded interval;
3. retain the queued readiness events and drain them once the target is idle;
4. report the target and managed stack unhealthy until that turn has actually
   ended; and
5. expose participant, Thread, turn, cause, queue depth, and oldest queued age
   through dispatcher status and lifecycle diagnostics.

Do not dynamically create a replacement Codex context in this v11 correction.
If denial/cancellation cannot end the target, the operator restarts the managed
stack, whose already-approved fresh-context-per-start policy supplies a clean
target. V12's worker supervisor owns automatic replacement. This boundary
restores delivery without adding a second context-selection policy that will
soon be discarded.
