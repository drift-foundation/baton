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
4. [done, superseding ruling 2026-09-01] Reject the proposed custom retained-
   base, inherited-proposal-lineage and byte-closure importer for Git-backed
   Work. Preserve the reproduction as evidence that uncommitted candidate-tree
   overlays are not valid assignment bases.
5. [pending explicit scheduling] Make the dogfood Git path name one exact base
   commit, give the private worker durable access to its objects, and require
   the declared output to retain an immutable proposal head plus the objects
   needed to inspect it.
6. [pending explicit scheduling] Make correction revisions use additional
   immutable commits on the same private history. Make a dependent Job name
   the accepted predecessor commit as its base and record the Work dependency;
   never stage an uncommitted retained candidate as an implicit source.
7. [pending verification] From a clean context, prove independent forks from
   one base, a review correction revision, an explicit dependent Job and
   refusal of an uncommitted candidate-tree source. Review the exact declared
   base-to-head commit range.
8. [pending integration gate] Hand an accepted immutable proposal to the
   existing distinct Git-aware integration stage. Keep the Worker Manager
   artifact-neutral and use normal Git conflict/refusal behavior rather than a
   custom byte importer.
