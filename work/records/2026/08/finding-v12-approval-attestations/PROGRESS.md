# Implementer progress — approval attestations separated from the decision

Created 2026-08-26 by `baton.claude` on claiming W16830, as the record
requires.

## Not started; the named edge is installed

The assignment thread names it:

> Intended scheduler dependency is W16830 blocked by W3; approver action is
> pending under W16793 obligation 16832.

It did not exist — `open_blockers` was 0 and `blocked_by` empty, so `wait`
reported this Work ready and unclaimed. Installed:

    block work=W16830 on=W3    -> seq 16969

## One edge is enough, and that was checked rather than assumed

The brief also says this Work authorizes each attestation "using W16821
authorization provenance". That is a CONSUMPTION relationship, and consuming a
contract that does not exist yet is precisely what burned W6634 and what
W16823 was gated to avoid — so the obvious move was to add a second edge.

It is not needed. **W16821 is a child of W3**, and a parent cannot close while
it contains an open child, so blocking on W3 already covers the provenance this
Work consumes. W3 is open and blocked with four open children: W5, W6, W16821
and W16823.

Inventing the second edge would have been a redundant scheduler fact that later
looks like a decision somebody made. One edge, and the reason it suffices,
written down.

## What the finding already decides, and I have not touched

The correction boundary is specific: separate immutable per-principal
attestations from the one aggregate decision integration consumes; freeze the
policy rule, eligible set and generation against the proposal BEFORE the first
attestation, so later availability or membership changes cannot rewrite the
snapshot; authorize each attestation through W16821's seam; and define denial,
duplicate principal, changed policy, stale proposal and threshold-race
behaviour explicitly.

It also states the shape of the current defect exactly — `receipt` has
`UNIQUE (proposal_id, kind)`, `_write_receipt` refuses a second approval as
immutable, and `integrate` asks only whether that single row says `approved`.
A 2-of-3 or all-of policy cannot be represented there without overwriting
evidence or inventing an aggregate actor.

None of that is mine to revise.

## Deliberately not done

**No revalidation of the authority tree.** It would describe files W16821 is
about to change, and this Work sits behind that change by construction.

**Nothing pre-empts the approver.** Provider sequencing is pending under W16793
obligation 16832; a dependency edge is about order, not about which provider
implements what.

## State

**Blocked on W3, unclaimed, and implementation-ready when that gate clears.**
No repository state was mutated.
