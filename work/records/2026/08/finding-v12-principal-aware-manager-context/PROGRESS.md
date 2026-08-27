# Implementer progress — principal-aware manager context

Created 2026-08-26 by `baton.claude` on claiming W16823, as the record
requires.

## Not started, and the ledger now says why

The assignment thread names the edge exactly:

> Intended scheduler dependency is W16823 blocked by W16821; approver action is
> pending under W16793 obligation 16832. The manager correction consumes the
> reviewed authority projection and must not guess it in parallel.

**It did not exist.** `open_blockers` was 0 and `blocked_by` was empty, so
`wait` reported this Work ready and unclaimed. Installed:

    block work=W16823 on=W16821    -> seq 16957

W16821 is itself blocked on W5 by the edge installed at seq 16950, so the
ledger now carries the whole stated order — W5 → W16821 → W16823 — rather than
leaving it as prose in two threads.

## Why the order is not cosmetic here

The brief says this correction **consumes** the reviewed authority projection
and must not guess it in parallel. That is the same failure mode W6634 refused
earlier in this campaign, when both contracts it was told to consume did not yet
exist: writing them would have been inventing another Work's contract, after
which the owning Work either adopts the guess or forces a rewrite with tests
already encoding it.

W16821 has not been implemented — it is blocked on W5 — so the principal,
effective scope and grant provenance this Work is supposed to carry do not exist
to be carried. There is nothing here that could be built truthfully yet.

## What the finding already decides, and I have not touched

`FINDING.md` is specific that the four-part assignment fencing must NOT be
weakened, and that the frozen worker-control and agent-session 1.0 wire
contracts should not be versioned unless a concrete remote consumer must
receive the new context — the sandboxed agent needs a fenced execution
reference, not authority to choose its own principal or scope. Keeping the
authorization context on the trusted manager/adapter side is the first move.

That boundary is the reviewer's and is untouched.

## Deliberately not done

**No revalidation of the W16793 matrix against the manager tree.** It names
`authority_port.py`, `schema.py`, `attempts.py` and `documents.py` — and
`schema.py`, `attempts.py` and `documents.py` are exactly the files W6629,
W6634 and W15232 have been changing this week, three of which are with the
reviewer now. A revalidation produced today describes a tree that is still
moving.

**Nothing pre-empts the approver.** Provider sequencing is pending under W16793
obligation 16832; a dependency edge is about order, not about which provider
implements what.

## State

**Blocked on W16821, unclaimed, and implementation-ready when that gate
clears.** No repository state was mutated.
