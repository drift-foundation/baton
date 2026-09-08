Historical snapshot; superseded by revised PLAN.md. Not implementation instructions.

# Plan

## Current ruling — 2026-09-07

Owner authorized bounded revision now, assigned to tuner, followed by independent
review and exact implementation-scope disposition. Incorporate the FINDING's
approved revised-plan handoff. The separate live-session detach experiment does
not yet replace confirmed-stop production behavior. This assignment changes only
this dossier/evidence; do not edit shared production paths during plan revision.

The earlier six-path proposal below is SUPERSEDED where it requires private-group
modes, routine recursive handoff normalization, or mandatory recovery of arbitrary
restrictive worker files before the first demonstration. Revalidate before any
implementation: development files 0664, directories 02775, executables 0775;
stable shared-write permissions and read-only reviewer mounts. Credentials remain
outside this policy. Restrictive creations are exceptional compatibility cases,
not normal permission churn. The launch gate's exact 02770 requirement must be
updated consistently; identify the revised exact path/test scope for review.
No production edit is authorized by this plan update.

## Historical reviewed proposal — pending revision, not active implementation instructions

### Prior deliverable

Planning and locator verification completed on 2026-09-07 by baton.tuner.
Independent review `review-2026-09-07T00-51-29Z.md` recommends the proposed
policy WITH the FINDING's initial-publication/admission serialization amendment.
The amended policy and six-path scope await owner acceptance.
Implementation has not started. This replaces the earlier investigation outline;
the decision chronology remains in FINDING.md.

The capability is one populated persistent line that the configured fixed
runtime can edit, the manager can subsequently read and validate, and a later
serial writer can continue. Read-only source/review, line identity and fencing
must remain effective. Initial access and post-runtime custody are distinct
operations; the latter has its own owning record at
`../finding-v12-private-line-custody-locators/`.

## Proposed exact implementation scope

No path below is authorized for editing until the owner accepts the reviewed
plan. Existing test changes are additive only; no assertion or expected behavior
replacement is requested.

| Path | Bounded change |
| --- | --- |
| `v12/python/src/baton_v12/worker_manager/workspaces.py` | Private populated-line access helper: pinned no-follow traversal, complete preflight, configured-group adoption of manager-owned entries, executable distinction, proof-only handling of already-normalized worker-owned entries. Reuse group validation and limits; no Git parsing or public export. |
| `v12/python/src/baton_v12/worker_manager/review_cycles.py` | Call the helper after materialization and on fresh idle/correction writer admission. Preserve replay, pins and grant serialization; do not mutate permissions from live mount/replay readers. |
| `v12/python/tests/manager/test_workspaces.py` | Add an isolated test class for populated-tree modes, restrictive manager umask, unchanged contents/inodes, executables, nested entries and refusal boundaries. |
| `v12/python/tests/manager/test_review_cycles.py` | Add cases for helper composition, initial/correction admission, manager-created checkpoint entries, active/replayed grant non-mutation, stale/replaced identity and read-only review topology. |
| `v12/python/tests/manager/test_private_line_access_engine.py` (new) | One bounded serial gate for fixed-identity file/Git operations, manager validation, later serial access and read-only review. No model/provider call. |
| `v12/python/tools/parallel_test.py` | Append only the new engine module to `SERIAL_MODULES`; preserve existing members and scheduling behavior. |

This dossier remains the plan/progress/evidence owner. No changes to K's
`source_profiles/checkout.py`, `v12/worker/claude_agent.py`, their tests,
Dockerfiles, frozen schemas, custody/OCI/intake, job-manager or integration
code are included. The line-custody provider owns its separately reviewed
correction. Any required additional production or existing-test change returns
through scope review before edits.

## Implementation sequence after acceptance

1. Re-read current source and accepted rulings. `review_cycles.py`, its tests
   and the parallel registry already contain unrelated uncommitted changes;
   establish serial file ownership with their provider before editing. Preserve
   those bytes. Evidence fingerprints identify an inspected baseline, not
   immutable import approval.
2. Add the positive populated-tree regression, including nested manager-owned
   files and private metadata, and record the unprovisioned baseline. Implement
   the helper and initial composition. Directories are 02770; regular files
   0660/0770 according to owner-execute, in the configured group. Source bytes,
   line bytes, inode pins and checkpoint identities must remain unchanged.
3. Compose fresh writer admission safely. Preflight before mode mutation and
   hold the existing admission transaction through its final state/pin check,
   bounded pass and grant publication. No engine or profile invocation enters
   that write transaction. Already-held/replayed grants must not reprovision.
   Apply the same rule to initial provisioning: final materializing-state/pin
   check, permission pass and idle publication are serialized together. A late
   creation caller cannot chmod an advanced/live line. Admission also rechecks
   the generation and checkpoint identity underlying prior validation. Add the
   deterministic initial-creator and stale-admission interleavings pinned by
   the independent review; no existing assertion is replaced.
   If this cannot be done under the existing bounded lifecycle, return for a
   revised plan rather than inventing a new scheduler state.
4. Add focused refusal/replay tests. Worker-owned entries are handled only
   after the line-custody provider restores access; verify those grants and
   refuse contradictory ownership/modes instead of privileged repair.
5. Demonstrate real runtime access and manager/correction continuity using the
   engine gate below. Complete acceptance needs the separately verified
   line-custody ordering; initial-access evidence may be reviewed earlier
   without being reported as the full result.
6. Run one bounded relevant regression sweep and hand the exact candidate and
   evidence to independent review. No unrelated full-suite campaign or Git
   mutation. Return the reviewed scope/result to the owner for disposition.

## Focused verification contract

The new engine gate uses a real manager-created Git line through the existing
checkpoint profile, isolated from the canonical repository. Use the existing
`Dockerfile.claude` image recipe because the reference Python-only image lacks
Git; the recipe and concrete worker are read-only inputs. Follow the established
no-secret image build/probe procedure, record the resolved image digest, and do
not inherit unrelated image-test methods. Image provisioning is a named
prerequisite; do not hide a long network build in the file-access result.
Missing installed build/runtime authority is an actionable refusal.

Require explicit `BATON_V12_WORKSPACE_GROUP`, configure it through the manager
API, and prove the manager holds it. The operator must attest that it is a
dedicated non-authority group; numeric shape cannot prove that fact. Do not
silently use the fixture's login-group fallback. Capture container uid, primary
gid, supplementary groups, and host-observed created-file uid/gid, since
rootless/user-namespace mappings can differ. The proof fails if the manager
and runtime are effectively the same owner.

After accepted fixture scope, the harness performs private Git setup/commits
only in its disposable fixture; agents do not issue mutating Git commands or
touch the canonical index/history. Containers use 65532:65532 plus the configured
group, no network or credentials, read-only container root, dropped capabilities,
no-new-privileges, bounded scratch, and only mounts composed from the manager's
source/line/review boundaries. Bound engine calls to at most 300s each and use
fixture-owned cleanup.

Prove this sequence:

1. Under a restrictive manager umask, materialize populated tracked files,
   nested directories, an executable and actual Git metadata. Compare content
   and inode identities before/after provisioning; verify the launch root gate.
2. First runtime modifies an existing file, creates/removes paths, and commits
   via actual private Git metadata. Assert real uid/gid/group and actual writes,
   not only composed flags or `os.access` under the manager uid.
3. After the line-custody provider's authorized runtime ending, manager-side
   profile freeze/validation succeeds over the actual head. Include one
   restrictive runtime-created nested file/directory so success cannot be
   attributed solely to cooperative umask. Independently observe normalization
   of the line, not the ordinary unused attempt workspace.
4. A read-only reviewer can inspect the exact checkpoint but cannot alter a
   tracked file or metadata; it writes only its separate review output.
5. A second generation-fenced writer uses the same line device/inode, modifies
   earlier content and a worker-created path, and creates a descendant commit.
   The manager validates again and still resolves the old checkpoint.

Bounded unit negatives cover wrong/unheld gid, replaced/symlinked root, nested
symlink target non-mutation, hardlinks, special files, refusal before grant
publication, active/replay non-mutation, and stale generation. Existing refusal
assertions remain intact; add cases rather than editing them.

Planned commands from `v12/python` (new class names pinned in progress):

- Focused helper/lifecycle classes:
  `PYTHONPATH=src python3 -m unittest <new-helper-class> <new-lifecycle-class> -v`.
- Serial engine gate with the explicit approved workspace-group environment:
  `PYTHONPATH=src python3 -m unittest tests.manager.test_private_line_access_engine -v`.
- Once focused cases pass, bounded source sweep:
  `PYTHONPATH=src python3 -m unittest tests.manager.test_workspaces tests.manager.test_review_cycles -v`.
- `git diff --check` and exact changed-path/fingerprint review.

## Planning evidence and owner action

Source/locator verification and non-mutating environment checks are recorded in
`evidence/locator-trace.md`. No runtime test, permission repair, production change
or existing-test edit was performed during planning. PROGRESS.md stays untouched
because this assignment performed research/planning only.

Independent review is complete at the planning maturity only. Owner acceptance
should select the amended policy/scope and name the dedicated group plus
authorized image/runtime test boundary. This is the concrete decision needed
before implementation. W105982 remains a separate source-confirmed prerequisite
for full runtime/correction acceptance; W103068 now has its explicit dependency.
