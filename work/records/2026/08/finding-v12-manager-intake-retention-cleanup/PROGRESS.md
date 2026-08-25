# Implementer progress — manager intake, retention and cleanup

Created 2026-08-24 by `baton.claude` on claiming W6629.

## Done under this claim

The canonical dossier the assignment required before implementation, and the
revalidation — which this time turned up an **absence** rather than a
confirmation.

**What is already decided and must be consumed:** the `cleanup` axis is frozen
as `pending, blocked-on-intake, complete, retained, failed`, and W4's
`TRANSITIONS` already pins every move. Two consequences an implementer could
get wrong: `blocked-on-intake` is a first-class state, so cleanup *waits on*
intake rather than racing it and an implementation that retried instead would
be inventing a mechanism the axis already has; and `retained` is terminal and
is **not** `complete`, so reporting retention as completion would erase the
reason the material still exists.

**What does not exist at all:** the frozen worker-control schema has **no
`$defs` for intake, retention or cleanup**. `retention_policy_digest` is a
digest of a policy document whose shape the contract never states. So
"retention policy" in this assignment names something that is not a contract
anywhere in the tree.

That is a question rather than a blocker I can resolve: either another Work owns
the retention policy document and must be named so this one can wait for it, or
this Job defines it — and defining it here is what the assignment's own "must
not reconstruct any of them" forbids by implication. I have recorded it as
PLAN item 2 so the next implementer meets it before writing code rather than
after.

## Not implemented

**W6629 → W6627, W6628, W6630** are installed. All three are open, and W6627
and W6628 are themselves blocked on W6592.

## State

**Dossier created, contracts revalidated, edges installed, no implementation.**
The retention-policy ownership question is open and needs a ruling.
