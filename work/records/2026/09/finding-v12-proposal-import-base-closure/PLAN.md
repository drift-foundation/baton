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
5. [pending explicit scheduling; clarified 2026-09-02] Make the generic manager
   directly bind-mount the nominated local source directory read-only beside a
   separate writable workspace, with no mandatory copy, snapshot, enumeration
   or hash prelude and no interpretation of source format. A Git profile names
   an exact base/ref in input metadata and tells the worker to clone from that
   mount into the workspace with copy-safe/no-hardlink semantics; Baton and the
   generic manager perform no Git operation. Remote/cache/snapshot preparation
   remains an explicit provider option rather than the local default.
6. [pending explicit scheduling; clarified 2026-09-02] Keep one private,
   manager-custodied development line across serial implementation and review
   assignments. Freeze an immutable read-only checkpoint for each review; on
   changes requested, return the same line at that checkpoint to implementation
   rather than restaging from the canonical repository. Fresh runtimes attach
   the existing workspace instead of cloning or copying it per iteration;
   replacement is an explicit recovery act. Make a dependent Job name the
   accepted predecessor commit as its base and record the Work dependency;
   never use another Work's uncommitted candidate as an implicit source.
7. [pending verification] From clean disposable worker contexts, prove one
   private line surviving implementation -> review -> correction -> review,
   including ten or more synthetic correction rounds without another clone or
   candidate-tree copy, with one writer at a time and every reviewed checkpoint
   retained. Also prove independent forks from one base, an explicit dependent
   Job and refusal of another Work's uncommitted candidate-tree source. Review
   the exact declared checkpoint each time.
8. [pending integration gate] Hand only the independently accepted checkpoint
   to the existing distinct Git-aware integration stage. Keep intermediate
   checkpoints out of the canonical repository, keep the Worker Manager
   artifact-neutral and use normal Git conflict/refusal behavior rather than a
   custom byte importer.
9. [pending bootstrap retirement] Remove the copied per-file-hashed source-tree
   path from Git-backed dogfood once the locator-and-commit profile can launch
   the same useful assignment. Keep it only for explicitly generic file-tree
   inputs whose own format contract requires a snapshot.
10. [pending with items 5-7; confirmed 2026-09-02] Mount the manager-custodied
    private workspace directly from disk-backed storage with a workload-
    appropriate explicit quota. Keep tmpfs bounded to ephemeral scratch and
    prove that checkout, builds, caches, test artifacts, output and logs do not
    depend on the current dogfood harness's 64 MiB `/tmp`.
11. [pending verification; confirmed 2026-09-02] Prove the zero-prelude direct
    read-only host-source mount plus writable-workspace contract with one Git-
    aware task that clones copy-safely into the workspace and one non-Git file
    transformation. The manager must perform no Git operation, source-tree
    copy or format inference, and neither worker may mutate the mounted source.
