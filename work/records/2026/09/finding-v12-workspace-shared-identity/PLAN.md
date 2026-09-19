# Plan

Owner approved 2026-09-17; queued for v11-managed implementation and independent
review. FINDING.md owns the decision and acceptance boundary. Canonical ledger
owns current route/claim state.

## Current state — independently accepted; approver review next

Review `review-2026-09-17T15-56-45Z.md`, claim195787, independently verifies both
corrections and accepts the complete bounded candidate under the two current
owner rulings. All eleven candidate hashes match. The exact path/hash manifest
is `REVIEW-CANDIDATE-195787.json`, SHA256
`a82da7596fd37488dc4af34cc0c6dc28690a967f0208d6972e61df780f793c93`.
27 selected tests and the original counterexample reproductions pass; unchanged
prior evidence is reused. No blocking finding remains for this candidate.

Next: approver reviews the prepared working-tree diff and owns Git decisions.
Recheck manifest hashes; unrelated working-tree edits are not part of this
sign-off. Fresh timestamped deployment remains a subsequent owner-directed
action, preserving the old instance. No automatic probe, old-instance recovery,
live-engine/model run or deployment was added to this review.

## Previous corrected submission — now independently accepted above

Claim 195725 corrected the two findings of `review-2026-09-17T15-42-06Z.md`.
The owner decisions remain the current contract: no automatic runtime probe, no
activation registry, no old-instance recovery, and none was restored.

Both are one function, `workspaces.prove_line_integrity`. Two of the eleven
reviewer-bound paths changed — `workspaces.py` and `tests/manager/test_workspaces.py`
— and the other nine still carry the hashes claim 195685 verified.

1. **Symlink revalidation (P1) — done.** Every entry the walk observes is now
   fingerprinted through `account`, including the symlinks it never opens, so a
   recorded regular file or directory that becomes a symlink between the passes
   is a mismatch rather than a skipped entry. `st_mode` carries the type, so the
   transition fails in either direction. A same-pass transition between
   `entry.stat` and `os.open` raises `ELOOP` under `O_NOFOLLOW` and is refused as
   a change, not reported as an access failure. Stable symlinks, no-follow
   behaviour, depth-bounded descriptors and root-only permission setup are
   unchanged, with cases for the interleaving, the reverse direction and two
   positive controls.
2. **Access diagnostics (P2) — done.** The root open, the root `fstat`, an entry
   `stat`, an entry open, an entry `fstat` and directory enumeration each report
   through `_access_failure` with the operation, the failing entry, the errno
   name and the kernel's sentence. The relative entry occupies the rendered slot
   and the line root is named in the sentence after it, because a refusal renders
   a bounded prefix. A backstop handler keeps an unforeseen `OSError` from
   reaching a caller bare. No cause is inferred from `EACCES`, and a case proves a
   non-permission errno gets no mapping hint.
3. **Verification — the cadence, not a sweep.** `probes-195725.py` before and
   after; `InitialStableLineAccess` 24 checks; `test_workspaces` +
   `test_review_cycles` 298 checks in 2.309s; the reviewer's own selection, now
   71 checks. Two reversal probes in a removed scratch copy. Seven checks added,
   none changed or removed. The 763-check run from claim 195084 is reused, not
   re-measured. Evidence `EVIDENCE-195725.json`.

What remains is independent review of the corrected candidate. Fresh timestamped
deployment remains after acceptance; no update or recovery procedure is written,
on owner instruction.

## Superseded — the two corrections as they were requested

Independent review `review-2026-09-17T15-42-06Z.md` (claim 195685) superseded the
complete-candidate status below. All eight submitted hashes matched; 64 selected
independent tests passed.

1. Correct integrity revalidation when a previously recorded regular file or
   directory becomes a symlink. The new reproduction grants access while the
   historical function refuses. Keep stable symlinks/no-follow handling and
   depth-bounded descriptors; add the exact interleaving and positive controls.
2. Preserve failing operation and root/entry path in initial integrity access
   diagnostics. A real mode-0000 entry currently loses that context. Keep errno
   and ungranted failure state; do not infer an identity cause from EACCES.
3. Run the short failing reproductions and smallest adjacent regression set;
   reuse unchanged verified evidence. Return corrected candidate hashes for
   independent review. No source implementation is assigned to the reviewer.

Expected affected paths were `v12/python/src/baton_v12/worker_manager/workspaces.py`
and its directly related tests in `v12/python/tests/manager/test_workspaces.py`
and, if needed for the preparation refusal, `test_review_cycles.py`. Both
corrections landed in the first two; `test_review_cycles.py` needed no change.
Standing test authority applies; actual changed paths are recorded above and in
`EVIDENCE-195725.json`. Reviewer ownership that episode was the appended FINDING,
this PLAN, the review, reproduction and evidence. PROGRESS remains
implementer-owned.

## Previous candidate submission — completion status superseded by review above

`OWNER-TRUSTED-IDENTITY-20260917.md` (2026-09-17T14:28Z) and
`OWNER-VERIFICATION-CADENCE-20260917.md` (14:13Z) supersede the activation
design, the probe lifecycle and the update/recovery deliverable. This PLAN is
updated at the implementer's next owned edit, as the owner directed; the
sections below are retained as history and are NOT the current contract.

What the candidate now is, from claim 195084:

1. The probe and every part of the activation design are REMOVED, not unwired:
   `oci.observe_runtime_identity` and its helpers, the `workspaces` mapping
   registry and gate, `single_worker.activate_execution_identity`, and the test
   tree's activation seam. A case asserts the absence of all twelve names. The
   live-engine fail-fast guard in `tests/__init__.py` is kept on its own merits.
2. What replaces it is trust plus three cheap things: the supported
   host/container mapping DOCUMENTED at `workspaces.SUPPORTED_IDENTITY_MAPPING`;
   `declared_identity_mapping`, a structural `uid:gid` check called from both
   vectors that reaches no engine and no filesystem; and `_access_failure`,
   which turns an actual `EACCES`/`EPERM` into a refusal naming the operation,
   the path, the errno name, the kernel's sentence and the engine setting to
   check. Nothing claims the mapping was verified.
3. Remaining scope is closed: owner-only `0600`/`0700` in both directions is
   covered by cases (worker-created entries consumed with nothing repaired;
   manager-created entries owned by the uid the vector declares, with the limit
   of that assertion stated); private HOME/cache is PRESERVED and needed no
   product change, because the worker's home is made under the adapter's tmpfs
   and its environment is composed member by member; and the four compatibility
   conclusions -- `--group-add`, the `0640` credential slot, custody
   normalization and world-readable `/input` -- are recorded in PROGRESS as
   compatible-and-now-redundant, with the `0600` credential narrowing named as
   a follow-on that re-opens an approver ruling and is deliberately not taken.
4. NOT delivered, on owner instruction: installed-runtime update instructions
   and failed-attempt recovery. A fresh timestamped instance at
   `/home/sl/baton-v12-instance-<UTC-ISO-timestamp>` follows acceptance, the old
   instance is preserved as evidence, and the first Job's task is submitted
   afresh.

Verification follows the short-loop cadence: the focused suite after each
correction, the adjacent pairs actually touched, and ONE broad run because this
is a complete candidate -- 763 checks across seven suites pass, 20.131s by
unittest, 20.410025954s wall, 1 skip (the real-engine case). Two existing checks
changed because the messages they assert got strictly better; seven are new.
`test_boundary_inventory`'s 25 failures are reported with their limitation in
PROGRESS rather than claimed to be pre-existing.

Independent review is against the revised owner contract. Deployment is not
approved and is not performed by this claim.

## Previous completion sequence — placement clarified above

Review `review-2026-09-17T13-57-41Z.md` verifies both preceding cleanup corrections
on claim 195007 bytes; 272 independent focused tests pass. The prefix replacement
is preserved and an ownership-read exception still settles the engine. These
findings supersede the preceding open correction queue for this candidate.

1. Wire observation/refusal into production preflight and update deterministic
   engine fixtures. Verify matching acceptance and mismatch/failure refusal
   through launch coordination, with caller-visible unresolved cleanup evidence.
2. Finish private writable HOME/cache and owner-only 0600/0700 access both ways;
   record credential, custody-normalization and input-readability compatibility
   conclusions while preserving consent, mounts and independent-review isolation.
3. Supply written unexecuted installed-update/recovery instructions and submit
   the complete candidate with focused deterministic acceptance and provenance.
   Preserve verified helper/workspace corrections and existing evidence.

No further helper redesign or additional owner permission is requested. Work is
still incomplete; integration/deployment is not approved.

## Previous correction sequence — both findings now verified

Review `review-2026-09-17T13-52-10Z.md` verifies failed-listing refusal and
filesystem-cleanup outcome propagation. Independent 270 tests pass. Two residual
helper failures supersede the preceding correction queue for this candidate:

1. Obtain, validate, authenticate and remove the full immutable engine ID;
   the current formatted listing yields a short prefix without `--no-trunc`.
   Preserve an unrelated object that replaces the original prefix lookup.
2. Guarantee engine settlement after an attempted run even if observation raises;
   retain the original error and actionable unresolved-resource diagnostics.
3. Finish production preflight wiring/fake-engine support, private HOME/cache,
   restrictive-file checks both directions, compatibility conclusions and written
   unexecuted update/recovery instructions. Existing authority covers this scope.

## Previous matrix correction — partly verified, remaining gaps above

Review `review-2026-09-17T13-40-44Z.md` confirms rm-status and descriptor-cleanup
progress but reproduces false absence on inspect failure, removal of a replacement
container by mutable name, and positive mapping despite directory cleanup failure.

1. Enforce one complete acceptance invariant: successful run AND fresh valid
   observation AND exact engine cleanup/positive absence AND owned filesystem
   cleanup. Unknown outcomes refuse with caller-visible resource diagnostics.
2. Obtain positive absence evidence, not any nonzero inspect status. Inspect
   authenticated immutable object identity and remove by that exact ID. Return
   directory-cleanup failure to the caller rather than only appending a global
   diagnostic. Cover the review's outcome matrix and three reproductions.
3. Finish the already authorized preflight wiring/fake-engine support, private
   HOME/cache, restrictive-file checks both directions, compatibility decisions
   and written unexecuted update/recovery instructions. Preserve all prior fixes.

## Previous cleanup sequence — partially corrected, acceptance still incomplete

Review `review-2026-09-17T13-32-10Z.md` verifies removal of global reuse, unique
probe names and no-follow/single-link output checks. Independent 263 tests pass.
Cleanup still ignores nonzero engine status, deletes a name-collision container
without ownership proof, and has a directory replacement race after its pin check.

1. Make helper reclamation authenticate the exact invocation-owned object and
   evaluate command outcomes. Distinguish verified absence from unknown/failed
   removal, retain actionable unresolved-resource evidence and prevent success
   while cleanup is unknown. Preserve unrelated names on collision.
2. Make directory cleanup operate on the pinned object, not a pathname re-read
   after the identity check. Preserve replacement data on a concurrent rename;
   add the recorded deterministic interleaving regression.
3. Complete preflight wiring and its fake-engine fixtures, then private HOME/cache,
   restrictive access both directions and the remaining written compatibility/
   recovery scope. Existing authority covers these fixture changes; incomplete
   fixture support is not an approval gate or acceptance of a disconnected check.

## Previous correction sequence — cache/output/name issues partly addressed

Claim 194767 adds the observation helper but leaves preflight disconnected.
Independent review `review-2026-09-17T13-22-50Z.md` finds deletion of unowned
pre-existing probe data, stale cross-connection cache acceptance, symlink-based
false observation and missing daemon-side timeout cleanup. These are part of the
new helper's correction scope, not deferred hardening.

1. Correct probe resource ownership, unique names, no-follow result identity and
   cleanup before wiring the helper. Remove unsafe global reuse or validate its
   actual deployment/engine/filesystem provenance. Preserve pre-existing resources
   and fail closed on unknown cleanup. Add the recorded deterministic regressions.
2. Wire observation/refusal into real preflight/start and update affected fake
   engines to model it. Standing test-change authority already covers these
   fixture changes. Verify no Job execution follows mismatched/failed observations;
   do not weaken the guard or leave it commented out to make old fixtures pass.
3. Finish private HOME/cache, restrictive files both directions, compatibility
   decisions and written unexecuted update/recovery procedure from the existing
   scope below. Submit complete candidate and provenance for acceptance.

## Prior continuation — observation added, wiring still outstanding

Claim 194683 propagates the manager UID/configured workspace GID into worker and
custody vectors, preserving consent identity. Review
`review-2026-09-17T13-12-36Z.md` independently passes 409 focused tests, but the
new mapping predicate has no production launch caller. No deployment approval.

1. Implement the bounded runtime observation and enforce mapping refusal on the
   production preflight/start path before affected Job execution effects. Tie
   any reusable validation to the actual engine/deployment identity and fail
   closed on missing, malformed, failed or incompatible observations. Exercise
   real launch coordination with deterministic engine-boundary fixtures; a direct
   predicate unit test is insufficient. Preserve consent behavior.
2. Complete private writable HOME/cache and two-direction 0600/0700 filesystem
   acceptance. Revalidate credential mode, custody normalization and input
   readability with mount/privacy boundaries intact. These may remain compatible
   without changes; record the actual conclusion rather than invent an approval
   gate around each historical decision.
3. Supply the compatibility statement and written, unexecuted installed-update
   and supported failed-attempt recovery procedure, followed by complete candidate
   provenance and focused deterministic acceptance. Do not run a live engine or
   production retry merely to finish ordinary development verification.

## Prior continuation — vector propagation now implemented, mapping still open

Review `review-2026-09-17T12-58-44Z.md` verifies the reported race and syscall-count
corrections on claim 194622 bytes. Independent 277 tests pass and the original
race now refuses before access is granted. The prior findings 1 and 3 are
addressed for this slice; baseline evidence custody is repaired and intact.

The next implementation claim must advance the remaining shared-identity scope:
carry the trusted identity through worker/custody execution with early mapping
validation, preserve consent/private HOME/credential/mount boundaries, test
restrictive-file access both ways, and supply written compatibility/update/recovery
instructions. No integration or deployment is approved. Preserve the verified
workspace corrections, and use new evidence output names. No new owner decision
is required solely to continue this already authorized scope.

## Previous correction sequence — findings 1 and 3 now verified

Claim 194532 delivered a partial workspace candidate. Independent review
`review-2026-09-17T12-47-56Z.md` supersedes the prior queue status, not the owner
scope or prior decision history. The 272 focused tests pass, but a before-grant
hardlink race previously refused is now accepted. Implementation remains active
work to finish, with no integration/deployment sign-off.

1. Repair the dropped final integrity/race validation using bounded descriptors;
   add a regression for the recorded interleaving and preserve the earlier
   refusal before access is granted. Keep removal of recursive permission work.
2. Finish the existing identity/mapping/worker/custody and writable HOME/cache
   scope below. Fixed worker identity still defeats owner-only access, and
   removing normalization before launch is updated also leaves manager-created
   restrictive entries inaccessible to that worker. Test both directions.
3. Count actual filesystem permission calls in tests rather than trusting only
   the new product `PERMISSION_ACTS` counter. A newly introduced uninstrumented
   chmod/chown must be detected. Keep needed integrity costs separately counted.
4. Submit complete candidate provenance, deterministic boundary evidence and
   the written, unexecuted update/recovery procedure for independent review.
   Preserve previous evidence with new output names on every rerun.

## Prior implementation sequence — still applicable scope

At the prior return, claim 194465 had supplied revalidation only.
The original four steps below remain the accepted scope. Execute them using
`review-2026-09-17T12-32-56Z.md` and the dated FINDING clarification:

- Recheck overlapping claims and name product/test file ownership before edits.
  Canonical active tree snapshot 194499 showed only this review claim; that is
  not a guarantee that working-tree files are unchanged. Reviewer-owned paths
  for claim 194488 are FINDING, PLAN, the new review, reproduction and its JSON.
- Establish a provenance-bound shared identity across manager, worker and
  custody execution; explicitly validate supported host/container mapping.
  Revalidate fixed-65532 image/home, credential and input assumptions without
  weakening mount, credential or independent-review boundaries.
- Replace initial recursive permission provisioning with creation-time root
  access. Preserve no-follow/root pins and required integrity checks rather
  than dropping validation incidentally housed in the old permission walker.
- Bound descriptor lifetime in `_prove_line_consumable` as well. Necessary
  content checks may scale with content; permission setup must not walk unrelated
  contents. Do not raise descriptor limits as the fix.
- Record exact changed test paths/reasons under standing test-change authority.
  Cover >1,024 entries at a child soft limit of 1,024, measured peak descriptors,
  constant permission-operation counts across small/large unrelated trees,
  owner-only 0600/0700 files, repeated preparation/retry, incompatible identity
  and mapping, no-follow/root replacement, special files/hard links where
  applicable, read-only input/review and cross-Job/credential confinement.
- Submit reviewed-candidate provenance, focused deterministic results and a
  written compatibility/update/recovery procedure. Preserve the installed
  failed Work and attempt; do not execute recovery or deployment.

No additional owner choice is needed merely to select numeric IDs, update
superseded ownership tests, or run ordinary focused deterministic verification.
The reviewer reproduction is a failing baseline, not implementation acceptance.

## Accepted scope

1. Revalidate current workspace preparation, engine identity/mount configuration,
   manager consumption and review snapshot access. Identify affected existing
   tests and exact file ownership before edits; inspect active overlapping Work.
2. Implement shared execution identity at creation/launch and remove recursive
   permission provisioning. Scope: v12/python/src/baton_v12/worker_manager,
   directly related tools/single_worker.py and tools/stage_execution.py,
   v12 worker launch/image configuration, and directly affected deployment schema
   and documentation. Avoid unrelated refactors; record precise changed paths.
3. Add/update focused deterministic tests under v12/python/tests/manager and
   tests/tools for resource bounds, owner-only files, access mapping, read-only
   inputs/review, cross-Job confinement and retry preparation. Use sensible
   per-run timeouts; record timings and operation counts without live providers.
4. Hand off exact candidate and evidence for independent review. Include a
   concrete installed-runtime update and supported recovery plan; do not execute
   that plan against /home/sl/baton-v12-instance as part of implementation.

Keep this one bounded infrastructure correction. Discoveries about unrelated
submission UX, recovery API gaps or broad performance belong in separately
recorded Work, not an expanding implementation assignment.
