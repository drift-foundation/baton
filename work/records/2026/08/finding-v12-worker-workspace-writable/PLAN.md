# Plan

1. Revalidate workspace ownership, fixed worker identity, and cleanup owners.
2. Pin the least-privilege writable-root boundary.
3. Correct workspace preparation and add real-container positive/negative,
   retry, restart, and sibling-isolation regressions.
4. Run focused and package gates, then return for independent review.


## 2026-08-28

1. [done] Ownership, worker identity and every manager-owned mode measured from
   inside the exact composed container: `evidence/w33936-probe.py`.
2. [done] The boundary is the writable root's GROUP, chosen from that table.
   `WORKSPACE_DIR` is established exactly at `0o775`.
3. [returned] `run_vector` takes the group as an operand; wiring the adapter
   needs two mechanical alignments in closed Works' suites, and my attempt at
   the first destroyed uncommitted changes in `test_oci.py`.
4. [not reached] The acceptance's real-container positive, denial, retry and
   sibling-isolation cases all need the wiring.

## 2026-08-28 — independent review changes requested and decision required

1. [confirmed incomplete] Preserve the exact-mode improvement, but do not call
   it the correction: the adapter never supplies `workspace_gid`, the vector
   remains `65532:65532`, and the worker still lacks workspace write.
2. [decision required] Approver must choose the worker-write authority. The
   current proposal changes the primary identity pinned by W6632/W6633 and
   blindly inherits any workspace gid, including gid 0. Recommended direction:
   retain primary `65532:65532` and provision a dedicated non-authority
   workspace group, granted as execution-only supplementary authority; compare
   it explicitly with ACL/id-mapped or host-private/world-writable alternatives.
3. [required after ruling] Record the supersession or clarification in this
   finding and every owning closed record it changes before implementation.
   Define consent behavior, gid validation/provisioning, exact workspace mode,
   Docker/Podman argv and inspected state, created-file ownership, manager
   collection, retry/restart, cleanup, and sibling/other-path denial.
4. [required operational recovery] Restore `test_oci.py` from an authoritative
   copy, or obtain explicit owner authority for a fresh full recertification;
   do not infer the destroyed accepted assertions from current failures.
5. [verification] Add real-container create/update/remove and negative group-
   reachability cases, mutation coverage of the actual authority grant, focused
   adapter/workspace/lifecycle gates, then the package gate with the restored
   OCI module. Docker verification remains unavailable to this managed reviewer.

## 2026-08-28 — approver ruling M34630, implementation-ready boundary

1. [done] Preserve primary `--user 65532:65532`; supersede the dynamic-primary-
   gid proposal. The configured workspace gid is explicit, nonzero and never
   inferred from manager or filesystem ownership.
2. [required] Prepare each attempt workspace with the configured group and
   exact `02770` mode. Hold group-setting and mode-setting against the exact
   directory object; refuse inability to establish either rather than silently
   falling back to process gid/umask.
3. [required] For execution only, verify the canonical workspace root has the
   configured gid and compose supplementary `--group-add <gid>`. Consent and
   any missing/mismatched/zero group refuse or receive no grant as ruled;
   `--user` remains unchanged.
4. [required] Add pure vector/config/root mismatch cases and real-engine proof
   of exact primary uid/gid, applied supplementary groups, workspace create/
   update/remove, setgid created-file ownership and manager collection. Prove
   no additional access to input, launch, credentials, repository, manager or
   sibling paths, plus retry/restart and exact cleanup.
5. [authorized recovery] Freshly recertify `tests/manager/test_oci.py` against
   the pinned current launch and OCI contracts. Record it as new certification,
   never as restoration or reconstruction of the destroyed assertions.
6. [verification] Run workspace/vector/adapter/lifecycle/inventory/dependency
   gates, mutation coverage of group preparation and grant, required Docker and
   compatible Podman gates, then the complete source/package gate with exact
   unrelated-failure attribution and return for independent review.

## 2026-08-28 — changes requested by independent review

1. [required] Replace the inert `0o770`/optional-group path with canonical
   workspace adoption at exact `0o2770`; verify the exact root group before
   engine invocation.
2. [required] Refuse execution when the configured group is absent, invalid,
   unusable or mismatched. Preserve no supplementary grant for consent and
   every non-execution posture.
3. [required] Complete fresh `test_oci.py` recertification and the full ruled
   Docker/compatible-Podman positive, denial, retry, isolation, collection and
   cleanup proof. A denied write or skipped compatible engine is not closure.
4. [required] Return the correction for independent review with the newest
   review path and exact verification evidence.

## 2026-08-29 — the review's three [P0]s

1. [done] `assignment_workspace` takes the configured group as a required
   operand and adopts it with exact `02770` at the canonical boundary.
2. [done] An execution start without the configured group refuses before the
   engine, at the vector and at the adapter. Consent still refuses one.
3. [done] `prove_workspace_group` measures the exact root's group and mode
   immediately before the engine call.
4. [done] The positive matrix on Docker: applied group, unchanged primary
   identity, worker create/update/remove, inherited group, manager collection,
   owner-only refusal without widening, sibling isolation, denial at every
   non-workspace surface. Podman absent and named.
5. [done] `tests/manager/test_oci.py` recertified afresh, 83 cases green.
6. [raised, not decided] Manager cleanup cannot remove a populated
   worker-created directory. Measured, failing closed with the ownership named,
   and put to the approver rather than remedied under this Work's authority.

## 2026-08-29 — the cleanup ruling, and what it leaves here

6. [ruled and routed] M36166 requires unconditional manager custody and names
   the mechanism: a short-lived manager-controlled custody helper on the exact
   attempt directory. Umask 002 is explicitly NOT it. Pinned and created as
   **W36540**, a separate provider Work with its own record.
7. [this record's remainder] The workspace-write round is complete and
   reviewable. Full cleanup acceptance stays open until W36540 closes.

## 2026-08-29 — independent review changes requested

8. [changes requested] Replace the raw per-call gid convention with one
   deployment-owned configured workspace-group source or immutable capability.
   Validate candidates against that separate authority so another nonzero
   group the manager happens to hold is refused, then use the same frozen
   configuration for allocation and adapter launch.
9. [changes requested] Add the two-held-groups negative regression and durable
   provisioning documentation. Preserve positive Docker and compatible Podman
   evidence using a genuinely dedicated non-authority group; the current login-
   group proof and Podman skip do not satisfy the pinned authority boundary.
10. [still gated] W36540 separately owns unconditional manager custody and
    must close before this parent can close.

## 2026-08-29 — independent re-review changes requested

11. [required correction] Make `configured_workspace_group` verify the
    committed `workspace-group.configure` operation and exact result before it
    mints a capability. A `meta` gid differing from the journaled deployment
    choice must refuse as durable integrity failure even when both groups are
    usable by the manager.
12. [required regression] Make
    `test_the_projection_cannot_rewrite_the_journalled_group` pass while
    preserving exact replay and refusal of reconfiguration to another group.
13. [still required evidence] Add durable deployment provisioning/use
    documentation and retain engine evidence from an actual dedicated
    non-authority group on Docker and compatible Podman. The login-group
    fixture and Podman skips remain named operational limits, not closure.
14. [still gated] W36540 continues to own unconditional manager custody; this
    review does not move that provider boundary back into W33936.

## 2026-08-29 — the projection [P1] and the dedicated-group evidence

11. [done] `configured_workspace_group` verifies the committed
    `workspace-group.configure` operation — kind, answer decoded through
    `store.replay`, signature recomputed from that answer, and the gid rules
    applied to the committed value — and mints only when the journal and the
    projection name the same group. Every direction of disagreement is
    `integrity/schema` and none is a repair; the un-provisioned case keeps
    `policy/denied`. `configure_workspace_group`'s reconfiguration guard reads
    the journal too.
12. [done] `test_the_projection_cannot_rewrite_the_journalled_group` passes,
    with exact replay and the changed-group refusal preserved. Nine mutations,
    nine named cases.
13. [done] `v12/python/DEPLOYMENT.md` carries the provisioning and use
    documentation. The ruled engine matrix ran under an actual dedicated
    non-authority group (gid 8291, measured to name no group and own no file on
    the host) in a provisioned deployment image, launching siblings on the same
    real daemon: 54 tests OK. NOT closed: compatible Podman is absent and
    cannot be obtained on this host, and no deployment caller was added because
    this component has no entry point in the tree to add one to.
14. [still gated] W36540 continues to own unconditional manager custody.

## 2026-08-29 — independent review disposition

15. [accepted] The journal/projection correction and dedicated-group Docker
    evidence satisfy the prior [P1] and Docker half of the authority proof.
16. [required documentation correction] Qualify the deployment guide's
    collection claim: the configured group permits cooperative group-readable
    collection, while unconditional custody remains W36540's separate provider
    boundary.
17. [operationally blocked] Run the documented matrix on compatible Podman, or
    obtain an explicit approver supersession of M34630's two-engine proof.
    Skipped Podman classes remain evidence of absence, not acceptance.
18. [still gated] W36540 is open and must close before this parent can close.

## 2026-08-29 — the guide, and Podman run rather than skipped

15. [done] `DEPLOYMENT.md` distinguishes the two boundaries: the workspace
    group buys ordinary group-readable collection and NOT custody, owner-only
    worker output fails closed on purpose, and **W36540** is named as the
    provider of the unconditional property under M36166.
16. [done] Compatible Podman 5.8.4 provisioned in an image and RUN. Rootful:
    the ruled mechanism holds exactly — untouched primary identity, applied
    dedicated group, workspace written, every other surface denied.
17. [reported, not fixed] Rootless Podman applies the group but does not map
    the manager's supplementary gid through its user namespace, so the
    workspace arrives owned by `nobody` and the worker cannot write. A
    rootless deployment needs `--gidmap`/`--userns=keep-id:gid=`, which is a
    change to the launch vector M34630/M34916 pinned — raised for a ruling,
    written into `DEPLOYMENT.md`, and not patched under this Work's authority.
18. [still gated] W36540 remains open and independently prevents this parent
    from closing.

## 2026-08-29 — independent re-review disposition

19. [accepted] Keep the custody qualification in `DEPLOYMENT.md`, the
    journal/configuration correction and the dedicated-group Docker evidence.
20. [changes requested] Do not treat the one-case ROOTFUL Podman probe as the
    full M34630 matrix. Retain exact reproducible commands and complete output,
    and run the portable created-file, retry, isolation, collection and cleanup
    cases in an environment where their manager-side permission assertions are
    meaningful.
21. [changes requested] Qualify the guide's "use rootful Podman" direction
    until W32391 certifies it or the approver explicitly narrows the required
    matrix. Preserve the measured ROOTLESS gid-map constraint as evidence, not
    as an unruled launch-vector patch.
22. [coordination gate] W32391 owns Podman lifecycle/security certification;
    W36540 owns unconditional custody. Both remain open providers for the
    corresponding parent acceptance.
