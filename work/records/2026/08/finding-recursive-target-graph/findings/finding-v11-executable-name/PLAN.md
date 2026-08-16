# Plan

**Status — 2026-08-16:** active pre-cutover correction. W92 deployment is
blocked until this item is reviewed clean and committed.

1. Revalidate every current-facing `baton-work` occurrence against the
   confirmed product-name boundary; preserve frozen history and internal
   module/package names.
2. Rename the installed zipapp to `bin/baton` and update deploy result/next
   paths atomically with the artifact.
3. Update shipped docs, generated hints, current examples, W92 runbook, and
   recreation-script operator instructions to the exact renamed executable.
4. Update packaging, isolation, init/activate, and end-to-end artifact tests;
   add a negative assertion that a fresh release does not ship
   `bin/baton-work`.
5. Remove W2 from W92's recreation inventory/script, adjust all surviving
   counts, and rerun the scratch recreation/idempotence proof.
6. Run focused packaging/lifecycle tests, `git diff --check`, and the complete
   parallel-plus-serial v11 gate. Return for append-only review before commit
   or deployment.

**Closed satisfying — 2026-08-16 10:45Z.** Final review is clean at
`review-2026-08-16T10-44-47Z.md`; the live Work closed at authority sequence
132. The implementation reports 633 parallel plus 3 serial tests green and
the final targeted sweeps/diff check pass. Deployment remains held only by the
continuing pre-cutover audit and its other same-schema corrections.
