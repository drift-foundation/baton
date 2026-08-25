# Finding: manager intake, retention and cleanup

Canonical Baton Work: W6629, a separately scheduled M2 manager prerequisite
from the closed W4 and W5 PLAN item 8. Dossier created 2026-08-24 by
`baton.claude` on claiming, because the assignment requires one before
implementation.

## Confirmed boundary

Python manager intake, retention and cleanup state and operations **over
already-sealed artifacts and already-certified runtime observations**:
effectively-once durable identities, recoverable cancellation material,
retention policy, cleanup authorization, positive absence, and restart/retry
ordering.

**Not here:** collecting OCI files, issuing engine commands, defining
credential or redaction policy, running provider code, or inferring truth from
diagnostics.

## Revalidated against the current tree — and the sharpest finding is an absence

**The cleanup axis is frozen and already pinned.** `cleanup` is `pending,
blocked-on-intake, complete, retained, failed`, and W4's `TRANSITIONS` already
carries the moves: `pending → blocked-on-intake | complete | retained | failed`,
`blocked-on-intake → complete | retained | failed`, and `complete`, `retained`
and `failed` all terminal.

Two things that axis already decides:

1. **`blocked-on-intake` is a first-class cleanup state.** Cleanup explicitly
   waits on intake rather than racing it, and the contract says so — an
   implementation that treated "intake not done" as a retry loop would be
   inventing a mechanism the axis already has.
2. **`retained` is terminal and is not `complete`.** Material kept on purpose
   and material cleaned up are different endings, and a cleanup that reported
   retention as completion would erase the reason the material still exists.

**THE ABSENCE, which is the finding this Job most needs recorded.** The frozen
worker-control schema has **no `$defs` for intake, retention or cleanup at
all** — no `retentionPolicy`, no `intakeRecord`, nothing. `retention` occurs
seven times and `intake` four, and every one of those is a *reference*:
`retention_policy_digest` is a `digest` of a policy document whose **shape the
frozen contract never states**.

So "retention policy" in this assignment names something that does not exist as
a contract. Implementing it means either:

- consuming a retention policy shape that some other Work owns — in which case
  that Work must be named and this one must wait for it; or
- **inventing** the policy document here, which is the trap W6634 was blocked
  on and which this Job's own instruction ("must not reconstruct any of them")
  forbids by implication.

I am not resolving that by choosing. It is a question for the route handler and
it is recorded here so the next implementer meets it before writing code rather
than after.

## Dependencies

**W6629 → W6627, W6628, W6630.** Intake, retention and cleanup consume
certified runtime observations (W6627), sealed-artifact acceptance (W6628) and
§13 policy (W6630), and must not reconstruct any of them. All three are open;
W6627 and W6628 are themselves blocked on W6592.

## Acceptance

- Effectively-once durable identities through W4's existing journal.
- Recoverable cancellation material, distinguishable from material retained by
  policy.
- Cleanup authorization, with `blocked-on-intake` used as the state it is.
- `retained` and `complete` never conflated.
- Positive absence, and restart/retry ordering preserved.
- **Retention policy consumed from a named owner, not invented here.**

The implementer creates and exclusively owns `PROGRESS.md`.
