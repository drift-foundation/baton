# Plan: manager intake, retention and cleanup

1. [done 2026-08-24] Create this dossier and revalidate worker-control and the
   closed W4 record. Recorded in `FINDING.md`: the cleanup axis and its
   transitions are already pinned by W4; `blocked-on-intake` is a first-class
   state rather than a retry condition; `retained` is terminal and is not
   `complete`; and THE FROZEN SCHEMA HAS NO DEFINITION FOR INTAKE, RETENTION OR
   CLEANUP AT ALL -- `retention_policy_digest` is a digest of a document whose
   shape no contract states.
2. [needs a ruling] Name the owner of the retention policy DOCUMENT, or rule
   that this Job defines it. It cannot be consumed from a contract that does
   not exist, and inventing it here is what the assignment's own "must not
   reconstruct any of them" forbids by implication.
3. [blocked on W6627, W6628, W6630 and item 2] Intake over sealed artifacts and
   certified observations, through W4's existing journal rather than a second.
4. [blocked on item 3] Recoverable cancellation material, kept distinguishable
   from material retained by policy -- two different reasons for the same bytes
   still being there.
5. [blocked on item 4] Cleanup authorization and positive absence, with
   restart/retry ordering preserved.
6. [blocked on item 5] Tests, evidence and independent review.
