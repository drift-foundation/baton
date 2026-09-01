# Plan

1. [done] Preserve W52821 run5b, its source, its signed final candidate and the
   repository-level failure showing that six reported paths are not the full
   import closure.
2. [done, bounded stopgap] Permit one manual W52821 integration that preserves
   both the signed credential-source change and concurrent W61599 activity
   observation; verify before any commit.
3. [done, reviewer revalidation 2026-09-01] Trace source staging, input and
   output custody, dogfood proposal/evidence, v12 authority publication and
   integration, changed-path reporting and review sign-off. Preserve the
   measured W52821 lineage and seven-path closure in
   `evidence/research-2026-09-01/README.md`.
4. [pending approver ruling] Approve or replace the proposed separate import
   contract: immutable retained base artifact, ordered digest-linked inherited
   proposal lineage, and directly derived explicit path-state closure bound to
   the signed final candidate.
5. [pending approver ruling] Choose the repository-integrator exclusive
   write/fence boundary; require all-path three-way preflight, whole-import
   overlap refusal, no automatic merge and no integration receipt after a
   partial write.
6. [pending explicit scheduling] Implement the approved contract and exact
   conflict refusal in a fresh isolated v12 attempt. Preserve W61981 task/2 as
   the distinct verification-context owner.
7. [pending verification] Independently verify single-run, inherited-candidate,
   reversion, addition/deletion, disjoint current-work, idempotent and
   overlapping-conflict cases before import.
8. [pending independent gate] Inspect and rerun the isolated retained proposal,
   sign the base, closure and final-candidate digests, and only then permit the
   repository integrator to act.
