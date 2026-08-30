# Finding: Codex system-error target stays healthy and never drains

**Status:** confirmed v11 defect; correction delivered, awaiting independent review

**Binding:** `baton:work/records/2026/08/finding-codex-system-error-target-stays-healthy`

**Work:** W43539

## Observed — 2026-08-30

The managed `baton.codex` turn
`01a04fee-a8e7-7b72-9f01-2461f90f0789` started for W36540 at
23:50:36Z and ended `failed` at 23:52:23Z. Canonical Baton state no longer
recorded the claim, so failed-turn settlement correctly reported that nothing
was orphaned.

The app-server thread `01a04f97-8ee6-7f32-89ef-ebd03ea071af` did not return
to `idle`; `--list-threads` reports it as `systemError`. The dispatcher
nevertheless published `baton.codex` as `idle` with no Work, and managed
lifecycle status reports every service healthy.

Readiness re-admitted W36540 at 23:52:41Z and W39357 at 23:56:42Z. Both are
ready, unclaimed, and retained in the target queue. Every level-triggered retry
is refused as already in flight, while the dispatcher never starts another
turn because the target thread remains `systemError`. At the time of diagnosis
the authority had zero active claims and `baton.codex` had been pickup-overdue
for more than three hours.

## Confirmed defect

Turn settlement answers whether a Work claim survived; it does not make a
terminally broken app-server thread reusable. The dispatcher treats the empty
claim slot as permission to publish `idle`, but its own target status remains
non-idle and cannot drain. Runtime publication, lifecycle health, canonical
Work state, and actual deliverability therefore disagree indefinitely.

This is distinct from W39868. W39868 reconciles a different canonical claim
held when a managed turn fails. Here the canonical claim slot is empty and the
retained actions are legitimate queued deliveries; the unusable
`systemError` target is the blocker.

## Required correction

- Never publish `idle` for a target whose app-server thread is `systemError`
  or another terminal non-deliverable state.
- Publish a sticky failed runtime state with the participant, session, failed
  turn, status, and queued-action count; managed lifecycle status must not call
  the target healthy.
- Preserve admitted readiness identities without retrying them into the broken
  context.
- Provide one bounded recovery path that creates or activates a fresh
  configured context and then drains the retained queue exactly once. If v11
  cannot safely do that live, fail closed and name managed restart as the
  required operator action.
- Prove completed/idle, failed/systemError, failed-but-reusable, reconnect,
  duplicate completion, queued readiness, and restart recovery separately.

## Confirmed v11 boundary — 2026-08-30

The installed app-server contract and the current official app-server
documentation agree on the closed runtime thread-status model:
`notLoaded`, `idle`, `active`, and `systemError`. A configured target is
reusable only while its loaded status is `idle` or `active`. `systemError` is
terminal and non-deliverable for that configured context; an unrecognized
future status also fails health and delivery closed rather than being treated
as reusable.

The v11 bridge retains `inProgress` as the pre-v2 compatibility spelling for
`active`; it has the same reusable semantics and does not broaden the current
closed provider model.

V11 will not create a replacement context inside the dispatcher. The managed
lifecycle controller is the only existing boundary that starts a thread,
records the required bootstrap turn, proves a second-client resume, renders
the new thread id into the dispatcher configuration, and replaces the whole
managed context set coherently. A live dispatcher-created thread would be
process-local and would revert to the failed configured thread after a
dispatcher restart. Automatic live replacement remains v12 worker-supervisor
scope.

Therefore the bounded v11 correction is fail-closed recovery:

- retain the exact queued readiness events and their in-flight identities;
- publish a sticky `failed(internal)` runtime state naming the participant,
  configured session, failed turn when known, `systemError`, and the current
  queued-action count;
- make dispatcher control status and managed lifecycle health fail with the
  same terminal-target diagnosis; and
- name a full managed-stack stop/start as the recovery action. A
  dispatcher-only restart resumes the same failed context and is not recovery.

A failed turn whose authoritative thread status returns to `idle` is a
separate, reusable case: after failed-turn claim settlement it may publish
`idle` and drain normally. Turn outcome alone never decides context health.

## Immediate workaround

A full managed-stack restart creates fresh Codex contexts and clears the
process-local broken target. It is a workaround, not the fix. No claim release
is required in this incident because the authority records zero active claims.
