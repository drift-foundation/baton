# Plan

0. [done]
   The first ordinary self-hosted attempt reached the real provider but exposed
   a worker-image Python-floor mismatch, verifier-created cache pollution, and
   loss of a durable faulted terminal after container exit. Retain that attempt
   only as diagnostic evidence. Retry from a fresh committed baseline after
   those generic runtime boundaries are independently corrected; do not import
   or manually promote the faulted proposal.
1. [done] Re-read the current source/workspace rulings and
   map current workspace allocation, OCI mounts, dogfood staging, and profile
   inputs. Preserve the accepted preflight-before-staging ordering invariant.
2. [corrected; awaiting fresh review] Define a generic nominated-source and manager-created persistent
   workspace capability with an explicit launch-time capacity preflight and
   bounded scratch. The workspace declaration is admission evidence only; do
   not claim a live byte or entry ceiling over it.
3. [corrected; awaiting fresh review] Implement direct read-only local source mounting and disk-backed
   writable workspace mounting without manager Git knowledge or a mandatory
   source walk/copy/hash step.
4. [corrected; awaiting fresh review] Add a Git-aware profile that names/verifies an immutable base and
   clones copy-safely inside the workspace, plus one non-Git fixture using the
   same generic mount boundary.
5. [corrected; awaiting fresh review] Retire ordinary copied/tmpfs Git staging after the replacement
   launches the same useful assignment; preserve explicit generic snapshots.
6. [corrected; awaiting fresh review] Prove source immutability, containment/replacement refusal,
   >64 MiB disk-backed work, capacity-preflight/scratch behavior, restart
   adoption, and no manager Git/source-enumeration operation.
7. [done; changes requested] Bind the immutable proposal and enumerate all
   changed test paths before integration. The run7 review found two P0 and four
   P1 defects; its proposal remains evidence only and is not integrated.
8. [done] Correct the production connection, exact-base checkout, mount-safe
   cleanup, restart-stable source identity, honest capacity terminology and
   behavior, and the two pre-existing focused regressions as one coherent
   source/workspace change. Live workspace enforcement is separate hardening.
9. [done; changes requested] Fresh independent review is recorded in
   `review-2026-09-05T05-51-35Z.md`. It reproduced nested mount cleanup data
   loss, cross-assignment source-boundary substitution, and malformed dogfood
   task acceptance; the source handoff and immutable-candidate gates also
   remain open.
10. [done] Bind each source boundary to the exact assignment roots it
    proved, stop cleanup before descending into any mount, re-prove the
    nominated object where the runtime binds are derived, validate the new
    workload task members at the sender through the profile owner, and restore
    allowlist-strength image-boundary coverage. The review's discriminating
    focused regressions are added and each is measured against the superseded
    behaviour.
11. [done; independently verified] Persist and prove the workspace OBJECT identity across
    same-incarnation adoption and manager restart, and re-prove it at the last
    manager-owned bind boundary. The durable pin records both roots' pairs in
    one four-column write, that write is a compare-and-set decided under the
    store's write lock so two competing first pins cannot both succeed, an
    exact repeat is still not a write, and a differing pair still refuses. The
    real-directory replacement cases and the forced two-connection regression
    are added, and the schema-16 cutover is named in the version history.
12. [done] Accept both residual engine pathname-resolution intervals for the
    trusted-host MVP. Every boundary the Worker Manager owns still proves the
    source and workspace objects immediately before composing the binds; the
    engine's later resolution of those two pathnames is explicitly accepted.
    Do not introduce descriptor-derived mount sources, daemon-namespace
    coupling, or restart-model changes in this Work.
13. [done; functional pass, gate cleanup required] Run the certified
    real-container provider gate against the rebuilt worker image at a durable
    operator boundary and run the broad real-Docker sweep there. The one-episode
    provider path completed, verified, retained its declared result and
    destroyed its runtime. Broad functional Docker coverage passed; its four
    cleanliness assertions saw only retained engine residue predating this run.
14. [done; superseded by item 16] The canonical parallel runner registers this Work's
    `tests.manager.test_source_boundary`, and the corrected gate ran: the
    source-boundary shards pass, and the serial real-Docker phase reports only
    ambient engine-residue cleanliness assertions. But the parallel boundary-
    inventory failures themselves contain new W71917 columns, operations,
    operands and types with no owner or probe. Add complete boundary-inventory
    ownership and discriminating probes, then rerun the gate.
15. [done; changes requested] Independent review verified the 30-path manifest
    and digest but found candidate-specific omissions inside failures reported
    as baseline. Digest
    `sha256:daf2bd4f13eb8d095efdd0098e258ba494d2b74467a41b8b2141da6d74d6f52f`
    is evidence only and is not approved for integration.
16. [done; changes requested] The boundary-inventory correction classifies all
    49 W71917 entries: 35 stated owners (correcting the reported count of 29),
    ten layer/delegated probes, and four STRICT-column exemptions. The gate's
    remaining failure sets contain no candidate-introduced entry. Two stated
    witnesses are nevertheless invalid: the exported mount-table diagnostic
    is caller-controlled despite an internal-call-site-only witness, and the
    OCI constructor witness bypasses the constructor through `run_vector`.
17. [done; changes requested] Independent digest-bound review is recorded in
    `review-2026-09-05T07-57-56Z.md`. Digest
    `sha256:cdd285d098dd67dc449be864a016f6cf3c539e9418a45de700eae7e39c140199`
    is exact evidence but is not approved for integration.
18. [done; independently verified] Both public mount-table doors bound their diagnostic noun with
    `label_of` before it can reach a message, and the witness drives all three
    doors on their own refusal paths with caller values no call site here would
    pass. The OCI witness reaches `OciAdapter.__init__` itself, exercises its
    exact-type and posture rules, and proves the constructor-HELD capability is
    what a start composes its binds from. Focused and canonical gates rerun and
    the correction frozen as a superseding aggregate digest.
19. [done; approved] Independent digest-bound review is recorded in
    `review-2026-09-05T08-20-30Z.md`. Exact digest
    `sha256:15291e091b85e5674dd074913eedd9a100e667dc1665fabd0a17af99c32c0a89`
    is approved for integration; any path, mode, byte, base, or aggregate drift
    requires a new manifest and review.
20. [queued] Approver rechecks the exact manifest against the current tree,
    exercises Git ownership, and decides the terminal Work disposition without
    absorbing the separately attributable baseline failures.

Do not add review-cycle or scheduler policy to this leaf.
