# Finding: failed managed turn misses a secondary claim

**Status:** confirmed v11 defect; live incident blocks the v12 dogfood critical
path

**Binding:** `baton:work/records/2026/08/finding-failed-turn-misses-secondary-claim`

**Work:** W39868

**Prior correction:** W4303,
`work/records/2026/08/finding-managed-turn-failure-orphans-claim/`

## Observed — 2026-08-29

The managed `baton.codex` turn
`01a04df9-58a3-7151-a75f-20aa8f624ad6` started while processing W39770. While
that turn remained active, readiness queued W39357 and the same participant
successfully claimed W39357 at sequence 39793 under assignment episode 39791.

The turn ended `failed` at 14:47:11Z. W4303 settlement reconciled only the
delivery attempt's bound action, W39770. Because the authority no longer
recorded that claim, the dispatcher logged “nothing was orphaned” and did not
fence or file an orphan incident. It did not inspect the participant's live
claim slot.

Canonical state still records W39357 `active`, Handler `baton.codex`, episode
39791. The runtime projection reports the same participant `idle` with no Work.
A recovery poke is forwarded but remains queued behind the dispatcher's
unavailable/active state. W39357 blocks W39358 on the first-useful v12 dogfood
critical path.

## Confirmed defect

W4303 assumes that a failed managed turn can orphan only the Work bound to the
turn's original delivery attempt. An agent that keeps readiness armed inside
the same turn can finish or release that action and then claim another queued
Work before the turn fails. Settlement proves only that the original action is
released and incorrectly publishes a free/idle lane while the participant's
one canonical claim slot remains occupied.

## Required correction

Terminal failed-turn settlement must reconcile the participant's canonical
live claim slot, not stop after checking the attempt's original action. If the
original action is released but the participant holds another exact claim,
fence the target, publish failed rather than idle, file the existing sticky
orphan incident with that Work and assignment episode, and retain queued
readiness until exact recovery.

The correction must preserve W4303's exact-action behavior and one-claim
invariant. It must not automatically release either claim, infer success from
the runtime projection, or discard useful work. Operator recovery remains the
episode-fenced `release` operation.

Implementation is routed through `baton.tune` to `baton.tuner`. This bounded
v11 bridge correction must not consume `baton.claude` from the v12 critical
path. Immediate episode-fenced recovery of W39357 is a separate operator
action and does not wait for the implementation.

## Acceptance boundary

- A failed turn whose original action is released and whose participant holds
  no claim remains deliverable.
- A failed turn whose original action is still claimed retains W4303 behavior.
- A failed turn whose original action is released but whose participant holds
  a different claim fences and identifies that exact Work and episode.
- Runtime state cannot publish `idle` with `work: null` over any canonical live
  claim held by that participant.
- The sticky incident and queued readiness survive restart and clear only
  after exact recovery; no later Work is claimed concurrently.
- Repeated completion, reconnect, early-completion, and same-turn readiness
  races are idempotent and covered by regressions.

## Implementation revalidation — 2026-08-29

**Confirmed:** W4303's shared settlement and durable fence remain the correct
mechanism. The defect is confined to `EventBridge.#readAssignment`: when the
delivered Work/episode is absent, it returns `released` without considering a
different claimed Work already present in the same participant-relative
`wait timeout=0` result. The fence, failed runtime publication, sticky
incident, restart restoration, and exact recovery machinery already accept
the replacement Work and episode once reconciliation returns them.

**Supersession:** W4303's four-valued reconciliation clarification is
superseded for a delivered action that carries a Work locator. `released` now
means the participant holds no canonical live claim. If the delivered exact
Work/episode is absent but another claimed Work is present, reconciliation
returns a distinct `secondary` result with that live Work, episode, and action
key. The older `held` result remains only for an uncorrelated legacy delivery.
This does not relax exact-episode matching, auto-release a claim, or inspect
runtime telemetry as authority.

## Implementation result — 2026-08-29

**Implemented by `baton.tuner`:** failed-turn settlement now uses the complete
claimed set returned by the participant-relative canonical read. It prefers
the exact delivered Work/episode when present; otherwise, a different claimed
entry becomes the `secondary` fence and supplies the durable incident's Work,
episode, and action key. Only an empty claimed set is `released`.

The existing W4303 fence owns the rest of the behavior unchanged: runtime
publishes failed rather than idle, later readiness stays retained, the sticky
marker restores the same secondary claim after dispatcher restart, duplicate
completion is idempotent, and clearing still requires canonical evidence that
the participant's claim slot is free. No claim is automatically released.
