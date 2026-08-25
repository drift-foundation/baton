# Plan: worker-control section 13 security surfaces

1. [done 2026-08-24] Create this dossier and revalidate §13 and the closed W4
   record. Recorded in `FINDING.md`: the contract anchor is the `secret-leak`
   code, already in Python's closed `integrity` pairing, and §13 has no `$defs`
   because it is behaviour rather than a shape. The frozen host carries a
   complete reference whose five design decisions this Job should port rather
   than re-derive -- the walk at any depth, both halves being independent,
   value CONTAINMENT rather than equality, the named-field set, and the
   live-secret registry with synchronous cleanup.
2. [blocked on W6592] The leak refusal itself, applied to W6592's public and
   durable surfaces rather than to a parallel set this Job names.
3. [blocked on item 2] The live-secret registry and assignment-scoped delivery
   authority, with restart and cancellation FORGETTING rather than persisting.
4. [blocked on item 3] Bounded diagnostics that cannot themselves leak -- the
   place this Job meets W1593, since a refusal that quotes an operand is a
   durable surface like any other.
5. [blocked on item 4] The sweep: every durable and public surface this manager
   has -- operations, labels, logs, store rows, artifacts and refusals --
   enumerated rather than probed, in the manner the boundary inventory already
   uses, so a surface added later without a check fails the gate.
6. [blocked on item 5] Tests, evidence and independent review.
