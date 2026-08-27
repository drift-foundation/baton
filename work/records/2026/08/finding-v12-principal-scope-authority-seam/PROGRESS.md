# Implementer progress — the principal/scope authority seam

Created 2026-08-26 by `baton.claude` on claiming W16821, as the record
requires.

## Not started, and the reason is the assignment's own second message

The thread says it plainly:

> Preserve the current serial item W5; intended order is
> W5 -> W16821 -> W16823 -> W6, with W16830 after W3. Do not treat readiness
> before those dependency edges as authorization to interrupt the current
> implementation.

**Readiness surfaced this Work anyway, because the edge it names did not
exist.** W16821 had no blocker, so `wait` reported it ready and unclaimed for
`baton.impl` — exactly the situation the message anticipates. Checked rather
than assumed: W5 is open and in `block`, with five open children (W6633,
W6634, W6636, W14251, W15232), four of which are with the reviewer now.

So the correction is not to start implementing and not to hand the Work back
with a note. It is to put the stated order **on the ledger**, where a later
wake cannot walk past it:

    block work=W16821 on=W5

That moved the Work to `block` and released the claim in the same act, which is
the protocol behaving exactly as it should. Reviewer authority cannot mutate
impl-routed Work — the same reason W6629 and W6634 asked their route handler to
install edges before implementation — so installing it is the route handler's
job and this is it.

## What was deliberately NOT done

**No revalidation of W9901 or the W16793 matrix.** PLAN item 1 asks for it, and
doing it now would produce an answer that is stale before it is used: the
authority tree is exactly what W5's five open children are changing, and this
Work's own FINDING is specific about which files it depends on
(`authority/schema.py`, `identity.py`, `api.py`, `session.py`, `core.py`,
`store.py`). A revalidation is worth having when the tree it revalidates
against has stopped moving.

**No dependency edges for W16823, W6 or W16830.** The thread names them, but
those Works are not routed to me and this handler's authority is over the Work
it holds. The edge installed here is the one that gates W16821 itself.

**Provider sequencing remains the approver's.** The thread records it as
pending under W16793 obligation 16832, and nothing here pre-empts it: a
dependency on W5 is about order, not about which provider implements what.

## State

**Blocked on W5, unclaimed, and implementation-ready when that gate clears.**
The acceptance and the correction boundary in `FINDING.md` are the reviewer's
and are untouched. No repository state was mutated.
