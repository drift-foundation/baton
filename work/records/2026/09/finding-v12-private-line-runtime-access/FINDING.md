# Provision persistent private lines for runtime access

Ledger Work: W105706. Filed by baton.codex, 2026-09-06.

Discovery: W105575 concrete-worker plan revalidation, independently reviewed
in `baton:work/records/2026/09/finding-v12-concrete-worker-proposal-head/`.
Logical parent: standalone stage composition, W103068. This flat permanent
record avoids extending the already deep dossier hierarchy.

## Confirmed provisioning gap

`worker_manager/workspaces.py:line_assignment_workspace` obtains the ordinary
attempt roots but replaces their workspace with the persistent line directory.
It validates containment and the recorded device/inode; it does not establish
runtime access on the replacement tree. `review_cycles.writer_boundary` uses
that result for the direct writable mount. The ordinary allocator's
`adopt_workspace_group` therefore does not provision this mounted tree.

`review_cycles.create_line` delegates materialization to the chosen profile.
`checkpoint_profiles.GitCheckpointProfile.materialize` clones under the
manager's identity without a recursive access-provisioning step. OCI preserves
the pinned `65532:65532` identity and supplies a configured supplemental group.
Neither a writable bind mount nor Git `safe.directory` grants filesystem write
permission to a differently owned checkout.

**Precision correction:** `_line_place` creates the custody root and per-line
HOME with mode 0700. The checkout below them is created by the profile; this
function does not set the checkout root itself to 0700. Ancestor permissions
on the host do not establish the permissions seen below the container's direct
checkout bind. The confirmed defect is the missing provisioning contract and
operation for the populated mounted tree. A default manager-owned clone is
inferred to deny the worker necessary writes; exact deployed modes and runtime
access were not measured in this research turn.

## Proposed bounded result

Pin one manager/runtime sharing policy and its implementation owner before
editing. The worker must be able to change existing tracked files, add/remove
paths, and operate its private Git metadata. The manager must continue to read
and validate the resulting objects/checkpoints, and later serial workers must
be able to correct the same line. A top-directory-only group change is not
sufficient for an already populated tree.

Keep the source read-only, the runtime identity fixed, the existing inode pin
and generation-fenced grants intact, and reviewers read-only. Do not copy or
reclone a line to repair access, grant broad host privileges, or mutate the
canonical repository/index/history. The generic manager owns permissions and
lifecycle, not Git interpretation. Account for new files from the runtime as
well as the initial manager-created population.

Likely implementation boundary: `worker_manager/workspaces.py`, any narrowly
required lifecycle caller supplying the configured sharing policy, and focused
tests. This is a proposed boundary, not accepted path or test-change authority.

## Verification needed

Use the actual configured runtime uid/gid/supplemental group against a
manager-created populated line: modify an existing file, create a new one,
prove private metadata write access, then prove the manager can validate the
result and a second serial writer can continue. Prove a reviewer attachment
cannot write, and stale/replaced line identities still refuse. A test under
the manager's own uid alone cannot establish this capability. Required runtime
execution needs installed test authority; a managed participant reports any
missing authority and does not bypass a denied command.

This is required for the first live composition demonstration, not exhaustive
later hardening. Concrete-worker unit implementation can advance independently.
No production edit, runtime permission mutation, or Git operation was performed
while filing this finding.

## Coordination evidence — 2026-09-06

The reviewer's canonical `block work=W103083 on=W105706` and subsequent
asynchronous directed request on W103083 both refused: baton.codex is not a
resolved handler of its `baton.impl` route. No edge or obligation was created.
The W105575 implementer handoff asks the eligible implementation route to
record the assembly prerequisite. The refusals are expected authority behavior,
not a reason to bypass Baton or widen the worker's scope.

## Related locator triage — 2026-09-07 — baton.codex

**Observed during W105575 plan re-review:** `line_assignment_workspace`
substitutes the persistent checkout as the runtime workspace, whereas
`custody._target` derives the ordinary attempt workspace from configured
storage and the attempt ID. That allocator already created its result root.
The implementer's M105776 claim that custody necessarily refuses because no
result directory exists inside the line is therefore not established; the
owning W105575 FINDING explicitly supersedes that claim.

**Open, for this provider's triage before live assembly:** prove which roots
the live ending normalizes and how it protects the actual mounted line and
retained results. Do not add a line result directory based on the disproved
locator assumption. This records an integration question, not accepted
manager-change scope. If the trace confirms an independent defect, bind its
bounded correction to separate Work before implementing it.

W103083 now has the W105706 dependency (event 105757), confirmed by canonical
detail. The earlier failed reviewer operations remain history.

## Approved planning assignment — 2026-09-07 — baton.prompt for Slawomir

Slawomir approved bounded provisioning planning and locator verification by
baton.tuner, parallel with K's concrete-worker implementation. This authorizes
dossier/evidence work and relevant non-mutating inspection, not a still-unselected
permission policy or production repair. Pin exact production/test paths, initial
and runtime-created file access, manager readability, later serial writer access,
and a focused actual-runtime identity proof. Independently review that plan and
return for owner scope acceptance before implementation.

Trace the actual mounted and retained roots before proposing any locator repair;
the alleged missing-directory refusal remains superseded. A separately confirmed
defect needs its own bounded Work. Do not touch K's source-profile/Claude-worker
paths or tests. Preserve fixed runtime identity, read-only source/review mounts,
inode pins, fencing and private-line lifetime; no copying/recloning or broad host
privilege grants. This is an enabling happy-path seam, not an exhaustive hardening
campaign. Report a specific authority blocker rather than bypassing it.

## Planning revalidation — 2026-09-07 — baton.tuner

Claim event 105966. Inspected the current working tree, including existing
uncommitted review-cycle and stage-driver changes. No production path or test
was edited. The exact source trace and inspected fingerprints are in
`evidence/locator-trace.md`.

**Confirmed:** the launch gate is stricter than the initial finding described.
`OciAdapter.start` calls `prove_workspace_group` on the actual substituted
workspace immediately before the engine call. It requires the configured gid
and mode **02770 exactly**. A default clone without that mode therefore refuses
at the launch gate; even a top-level-only repair would leave populated children
unprovisioned. This qualifies the earlier inferred mid-runtime denial: which
failure occurs first depends on the actual root mode, and ordinary root modes
are already rejected before runtime start.

**Confirmed:** a recursive policy must cover all manager-owned private contents,
including the profile's metadata. Git stays with the profile: `clone_vector`
already uses `--no-hardlinks --no-local`, and generic access provisioning needs
no Git commands or metadata path special cases. Runtime-owned creations and
manager-owned checkpoint references need a stated path into later writer access.

**Confirmed separate defect:** the mounted line and sealed custody differ from
the directories normalized at ordinary ending. That trace is now filed as
W105982 at `baton:work/records/2026/09/finding-v12-private-line-custody-locators/`.
Its correction is not initial populated-tree provisioning. The earlier
missing-directory claim remains superseded. No empty result directory is
proposed inside the line. The new Work's first parent attachment refused due
to route authority; its successful top-level creation leaves the eligible
composition owner to add containment and any required dependency.

### Proposed access policy for independent review and owner acceptance

This is a proposal, not an approved permission mutation.

1. Use only `configured_workspace_group(store)`, with the existing validation
   and immutable deployment choice. Keep the manager as owner of the initial
   line and its files, runtime uid/gid 65532:65532, and the configured gid as a
   supplemental group. Never infer the gid from the checkout or login group.
2. On the private line only, give each manager-owned directory mode 02770 and
   the configured gid. Give manager-owned regular files 0660, or 0770 when the
   original owner-execute bit is set. Preserve content and Git's executable
   distinction. Remove no files, replace no inode, and grant no other-user
   access. Custody parents, source, inputs and sealed artifacts are not subjects.
3. Traverse a pinned root and descendants through no-follow descriptors.
   Symlink entries may remain as profile content but are never followed or
   chmodded; refuse special files and regular files with multiple hardlinks
   before applying grants. Refuse a changed root pin, untraversable tree, or
   unsupported ownership rather than using privilege, a copy, or a replacement.
   Preflight the complete bounded path set before mutation, and preserve the
   existing filesystem depth/entry limits. An OS failure publishes no successful
   line/grant; retry can complete partial grants on the same private tree.
4. Establish initial access after materialization while the line is still
   `materializing`, before publishing its first idle result. Repeat the same
   manager-owned access policy on fresh writer admission, including correction
   writers, so manager-created checkpoint files are covered. Admission must
   serialize the final pin/state check, bounded permission pass and writer-grant
   publication; another writer must not start midway through it. A replayed
   grant or `writer_boundary` is a read/proof path and must never chmod a live
   writer's tree. Existing materialized lines are provisioned at fresh admission,
   without rewriting prior creation evidence.
5. Runtime-created files inherit the group through setgid directories on the
   normal path. This is **not** an unconditional readability guarantee:
   restrictive creation modes, explicit chmod, and moves from scratch can
   defeat it. The separate line-custody provider must establish group/read/
   traversal access before manager consumers, and restore sharing needed by a
   later writer. The access pass never tries to chmod worker-owned objects as
   the manager: after custody it verifies the required group/access instead.
   Do not offer ACL defaults, umask 002, Git safe.directory, or recursive host
   privilege as substitutes for that custody result.
6. Review continues to mount the checkpoint read-only, with an independent
   writable review workspace. Source remains read-only. Existing line/grant
   revocation, authority generation, source/line inode pins and no-copy lifetime
   are unchanged. A shared gid does not authorize concurrent line writers.

The exact proposed path set, bounded tests, execution preconditions and
handoff sequence are in PLAN.md. The full runtime-created-file and second-writer
acceptance composes this initial-access change with the separate custody result;
passing a manager-uid filesystem test alone must not close this capability.

### Operational observations

Read-only `docker version --format '{{.Server.Version}}'` succeeded and reported
29.1.3. The current process reports uid/gid 1000:1000 and
`BATON_V12_WORKSPACE_GROUP` is unset. No dedicated test-group grant has been
identified by this evidence; the common fixture's fallback to `os.getgid()` is
not the deployment proof this Work needs. Owner acceptance should name the
dedicated group and authorized exact-image test harness before runtime testing.
Daemon reachability alone does not authorize image builds or permission repair.

Inspection corrected stale/guessed locators: the current custody resolver is
`custody._derived_root`, not `_target`; the checkpoint profile is
`v12/python/src/baton_v12/checkpoint_profiles.py`, not under `worker_manager`;
there is no `worker_manager/ending.py` or `endings.py`, and the relevant ending
owner is `intake.py`. These initial reads failed with missing-path errors and
were resolved through repository file search. All required bound dossier files
and the actual owning sources were readable.

## Independent planning review — 2026-09-07 — baton.codex

Claim 106042; handoff M106031. Review:
`review-2026-09-07T00-51-29Z.md`.

**Confirmed:** independently read the launch proof, materialization/admission,
seal/custody locators, ordinary normalization, and implementation-ending order.
The six inspected production fingerprints match `evidence/locator-trace.md`.
The launch root must carry the configured gid and exact 02770 mode. Ordinary
normalization targets neither the mounted line nor its sibling sealed custody,
and occurs after the earlier manager reads. W105982 is a distinct enabling
subject/order correction; initial group provisioning cannot replace it.

**Proposed for owner acceptance:** accept the six-path policy/plan with this
serialization amendment. It clarifies and supersedes any reading of policy
item 4 that permits an initial permission pass outside the final serialized
`materializing`-to-`idle` publication. `create_line` currently materializes
outside its final transaction. A second caller can hold an earlier
`materializing` observation while the first finishes and a writer starts.
Therefore the initial permission pass, like fresh writer admission, must run
after a fresh state/root-pin check and before publication under the same
existing transaction boundary. A late/replayed creator performs no permission
mutation once the line is idle, writing, or otherwise advanced. Profile and
engine calls remain outside that transaction. This amendment does not authorize
a general materialization redesign.

At fresh writer admission the final transaction must recheck the assignment
generation, exact line identity, admitted state and current checkpoint identity
that justified the earlier profile validation before changing permissions.
If those facts have changed, refuse/retry rather than applying a stale pass.
Add deterministic interleaving cases for a late initial creator versus an
admitted writer and a changed admission generation/checkpoint. Keep all new
cases in the two pinned unit-test files and retain existing assertions.

The proof-only path for worker-owned entries depends on W105982 actually
restoring the configured group and usable access, including restrictive nested
creations. Existing `custody` normalization merely ORs group mode bits on
owned descendants; it does not establish the proposed complete group policy.
Do not treat its ordinary receipt as satisfying this prerequisite. This
restoration belongs to W105982, not a hidden seventh path in this Work.

**Owner decision still required:** accept the amended policy and six paths;
identify a dedicated non-authority workspace group held by the manager and
authorize the exact-image isolated runtime harness. The reported unset group
and Docker version are environment observations, not runtime-access proof.
No production/test change, permission mutation, image build or test execution
was performed in this independent plan review. PROGRESS remains unchanged.

**Coordination:** W103068 now explicitly depends on W105982 (event 106054),
so composition cannot finish without line custody. Initial access implementation
remains independently schedulable; its full runtime/correction acceptance still
needs that provider. The requested parent attachment is unavailable in the
deployed CLI: full help exposes parent selection at creation but no existing-
Work containment mutation. W106052 records that limitation before using the
stopgap documentary index. W105982 remains canonically top-level; no containment
or database repair is claimed. The guessed `--help relate` and initially
qualified `create kind=baton.ops` were operator mistakes, corrected through
help and `kind=ops`; they are not Baton defects.

## Superseding workspace access ruling — 2026-09-07 — baton.prompt for Slawomir

Slawomir approved a trusted development-workspace policy: ordinary files 0664,
directories 02775 (setgid), and executable files 0775. Owner and configured
workspace group may write; others may read/traverse. These defaults explicitly
supersede the earlier proposed 0660/02770/0770 private-group-only modes and any
acceptance requirement treating world-readability of development contents as a
defect. They do not permit other-user writes.

Credentials do not belong in development workspaces. Credential-provider mounts
remain separate and restrictive; this ruling does not chmod credentials, source
mounts, authority stores, or immutable retained evidence. Reviewers get read-only
Docker mounts. The same writable private development line is reused across
implementation/review/correction; review does not require making it read-only on
disk and then changing it back. Normal operation uses stable sharing, setgid
inheritance and cooperative creation defaults, not recursive permission changes
at every handoff. Do not claim these defaults override explicit restrictive
creation modes, chmod, or restrictive files moved from elsewhere.

Restrictive worker-created entries are exceptional compatibility failures to
report or handle through a separately specified, quiescent recovery path. The
earlier mandatory noncooperative-file restoration proof is superseded as a
first-demonstration gate; do not expand it into production-style isolation or a
general hardening project. Correct line identity, non-overlapping writers and
manager access before result consumption remain required.

Revalidate the proposed six-path implementation boundary: the current OCI launch
proof requires exactly 02770 and must be made consistent with this ruling. This
decision authorizes updating the plan, not an unreviewed additional source/test
path or broad existing-test weakening. Exact group, focused execution setup and
revised implementation scope remain to be resolved. The reviewed prior plan is
historical evidence and is not implementation authority for the superseded modes.

## Approved revised-plan handoff — 2026-09-07 — baton.prompt for Slawomir

Slawomir approved proceeding with bounded plan revision incorporating the new
permissions/mounting rulings. Tuner owns this dossier revision; do not implement
the obsolete six-path proposal. Pin updated exact launch/access path and additive
test scope for stable 0664/02775/0775 development sharing. Distinguish initial
provisioning from exceptional repair, and use read-only review mounts rather than
normal-cycle mode changes. State any unresolved dedicated-group or exact-image
execution choice explicitly for the owner.

The live-session detach experiment is separately owned by
`../finding-v12-live-session-workspace-detach/`. Until its proof is independently
accepted and adopted, use confirmed container stop before consuming results.
Any proposed alternative must require verified ordinary unmount in the actual
writer namespace, no alternate writable access, and a durable handoff gate;
busy/omitted/failed/uncertain detach requires confirmed shutdown before reuse or
consumption, including after manager restart. This is not permission to implement
dynamic mount control in access provisioning. Coordinate possible shared
workspaces/review-cycle paths with the custody plan; return exact revised scope
through independent review before production edits.

## Revised stable-access proposal — 2026-09-07 — baton.tuner

**Confirmed scope:** owner handoff 106713 authorizes dossier/evidence revision
only. Source revalidation under claim 106738 confirms that initial populated-line
provisioning is still absent and OCI start still requires exact 02770 through
prove_workspace_group. This section supersedes the prior six-path proposal,
admission-time permission mutation and mandatory restrictive-file recovery
wherever they remain in historical text or the prior review. The owner's
0664/02775/0775 ruling is the active development-line policy.

**Proposed:** the revised PLAN enumerates eight exact paths: workspaces.py,
review_cycles.py, oci.py, their three test modules, one new serial engine module
and the append-only parallel registry entry. Preserve ordinary allocation's
02770 contract; select exact 02775 only for a manager-minted persistent writer
line with its pin and live grant. OCI preserves AllocatedRoots rather than
flattening it, so a specific internal line-policy marker can survive to launch.
A grant alone is insufficient: review_boundary also attaches one to ordinary
review output. Do not use a pathname spelling or a caller-supplied expected-mode
integer as authority. Preserve boundary/revocation checks and refusal settlement.

**Proposed lifecycle:** provision the manager-owned populated line only in the
initial final-publication transaction, after rechecking materializing state and
the captured root pin. Complete preflight precedes any mutation; partial OS
failure leaves an ungranted materializing line for explicit initial retry.
Late/replayed creation and fresh/replayed admission must never repair a live
line. Fresh grant checks revalidate assignment generation/current checkpoint
and root access without chmod/chown. The prior independent review's initial
publication race and admission freshness amendments remain relevant, while
its per-admission permission pass is explicitly superseded. This bounded helper
does not redesign the separately running profile materialization operation.

**Confirmed creation seam / open owner choice:** setgid and initial modes do
not set the creation umask. No explicit umask is established by the inspected
Dockerfile entrypoint/dogfood_entry.py, and GitCheckpointProfile receives a
deployment-supplied runner. The fixture must explicitly select cooperative 0002
creation for both worker and manager Git commands without temporarily mutating
the manager's process-global umask. The eight-path access proposal does not
silently change concrete-worker, profile or recipe paths. Owner disposition
must select exact dedicated group, installed image/runner authority and the
production cooperative-creation setup or schedule its additional bounded scope.
Configured demonstration success would not prove all existing deployments
already establish those defaults. Actual Git metadata behavior remains part of
the runtime proof, including manager-created checkpoint entries reused by a
later writer; no routine recursive repair can make that proof pass.

**Coordination:** W105982's planner identified overlapping review-cycle/OCI
sources and tests in M106747. Tuner agreed in M106761 to access-provider edits
first and custody edits serially afterward, each revalidated against the
reviewed predecessor bytes. This is an implementation order proposal, not
permission to edit either source now. W105982 owns confirmed-stop line-aware
access before consumption; W106673 remains a separately gated experiment.
Busy/omitted/failed/uncertain detach must still block reuse and consumption
until confirmed shutdown, including restart, if a future detach gate is adopted.

Evidence: evidence/stable-access-revalidation.md and
evidence/stable-access-source-hashes.json. Historical plan preserved at
evidence/historical-plan-before-stable-access-revision.md. No production or test
edits, runtime execution, permission mutation or Git mutation in this planning
revision. PROGRESS.md remains unchanged; independent revised-plan review and
owner disposition are next.

## Independent revised-plan review — 2026-09-07 — baton.codex

Claim 106831; handoff M106804. Read the entire current dossier, revised evidence
and owning source seams. All ten SHA-256 values in
`evidence/stable-access-source-hashes.json` independently match current bytes.
No implementation candidate exists. Review:
`review-2026-09-07T03-02-35Z.md`.

**Confirmed:** the eight-path revision follows the stable-mode ruling: initial
provisioning only, proof-only admission/launch, ordinary 02770 versus persistent
writer 02775, read-only review mounts, no mandatory arbitrary restrictive-file
repair. It retains initial publication and admission-freshness serialization.
The cooperative runner/worker setup is an explicit deployment decision rather
than an asserted capability of the existing entrypoint. The full serial runtime
proof includes manager-created checkpoint metadata and retained old checkpoints.

**Proposed clarification within the same scope:** the persistent-line marker
selects a policy; it is not itself authority for a host path. `AllocatedRoots`
explicitly records that even nominally immutable Python slots can be replaced,
and the present `_writer_grant` checks writer/line state but does not bind an
arbitrary roots mapping to the durable line object at launch. Compose the access
proof with a lifecycle-owned resolution of the writer, attempt, generation,
configured storage, line path and pin at use. Compare the actual OCI workspace
against that current answer. A copied marker/pin and a live grant from another
line must not make a cross-wired directory eligible. Preserve the existing
runtime-storage/source-boundary checks too. This gives substance to the PLAN's
already-required forged-roots negatives; it adds no schema or production path.

**Scope clarification:** existing idle/materialized lines that fail the new
proof remain refused; this one-time initial provisioning plan does not authorize
retrofitting them during admission. Migration/recovery needs explicit separate
scope. Start the configured demonstration with a fresh isolated line.

**Recommendation for owner:** accept the revised eight-path plan with these
clarifications, then choose the dedicated group, exact installed image/runner
authority and cooperative production setup boundary. Access edits precede custody
edits; shared ownership includes workspaces.py, review_cycles.py, oci.py, all
three corresponding test modules and the shared engine module. M106761 agrees
to the access-first sequence; implementation still awaits owner disposition.
Initial-only evidence can be reviewed before custody, but cannot close the full
runtime-access capability. W106673 remains experimental; confirmed stop stands.

This review changes only FINDING/PLAN and the append-only review. No runtime test,
permission mutation, source/test edit, group/image setup or Git mutation occurred.
PROGRESS remains unchanged. Prior review requirements inconsistent with stable
initial-only provisioning stay superseded, not silently reinstated.

## Owner implementation approval and acceptance split — 2026-09-07

baton.prompt records Slawomir's approval of the eight exact paths in PLAN with
`review-2026-09-07T03-02-35Z.md` durable launch-binding and pre-existing-line
clarifications. This supersedes pending scope approval, not operational setup
requirements. Tuner may implement the bounded provider; existing tests receive
additions only and the serial registry only its new entry. Stable 0664/02775/0775
private-line modes, ordinary 02770 compatibility, initial-only provisioning and
proof-only fresh admission/launch remain the accepted semantics.

Use a fresh isolated demonstration line and explicit cooperative umask 0002 in
the fixture worker and injected manager command runner, not process-global umask
changes. No pre-existing-line migration, production service/entrypoint change,
hidden image build, host group modification or broader authority is approved.
Identify the dedicated non-authority group held by the manager and exact installed
image/runner boundary before live testing; return exact missing setup to the owner.

Avoid a circular acceptance dependency: lightweight child W106896 implements and
independently reviews the initial-access code/interface checkpoint, using this
dossier as its sole evidence owner. It owns the eight paths first. W105982 waits
for that checkpoint, then revalidates accepted bytes before shared-path edits.
W105706 stays the overall runtime-access capability and waits for custody before
the full manager/reviewer/correction live proof. Closing the initial checkpoint
does not falsely claim full capability. Dependencies live in Baton, not plan text.

## Initial-access candidate and guard scope — 2026-09-07 — baton.tuner

W106896 claim 106921 executed the owner's initial-code checkpoint using this
dossier. Revalidated the whole finding, active plan and revised review before
changes. The three production modules now provision only initial manager-owned
contents under the final materializing transaction, preserve ordinary 02770
roots, and prove durable writer/attempt/generation/principal/configured group/
actual roots before allowing a marked 02775 line to launch. Fresh admission
rechecks generation/checkpoint identity without permission repair. Pre-existing
unprovisioned lines still refuse. No custody/detach or production creation-default
change is included.

Added cases cover real restrictive initial creation in a separate process,
content/inode preservation, symlink-target non-mutation, hardlink/special/limit/
ownership refusals, partial failure and retry, initial publication interleavings,
stale generation/checkpoint/principal, cross-wired roots, copied markers,
revocation and ordinary launch compatibility. Existing test bytes are preserved
as exact prefixes of the three amended test files.

The new opt-in serial engine module implements only initial populated Git-line
launch/first-writer evidence. It requires explicit approved group/image/runner
setup and does not build/pull images. It was not enabled or run live. Full
custody/manager/reviewer/correction coverage remains the subsequent W105706/W105982
composition; no stub or disabled full-capability assertion claims it done.

Observed verification: 251 focused tests ran, 250 passed, one engine test skipped
because runtime setup is not enabled. Additional dependency/source-boundary/
registry checks found the exact expected-list counterpart missing in a ninth
test path. Boundary ownership inventory needs two constructor ownership entries
and one capability association in a tenth test path. Existing unrelated failures
are separated by the saved-source comparative probe. No guard was weakened or
edited beyond accepted scope. The accepted PLAN requires returning these exact
paths/behavior changes for review rather than making an unapproved test edit.

Evidence: evidence/initial-access-manifest.json binds eight saved candidate
paths and seven saved pre-edit paths; evidence/initial-access.patch is only this
claim's diff. evidence/initial-access-scope-request.md specifies the additional
two-test-path request, validation failures and next disposition. This candidate
is not signed off and does not release the custody dependency yet.

## Independent initial checkpoint review — 2026-09-07 — baton.codex

W106896 claim 107030 independently reviewed the eight-path candidate, matched
saved/current hashes and the incremental patch digest, and confirmed all three
existing test files preserve their pre-edit bytes exactly. No additional
blocking code issue found. The recorded focused result is 250 passes and one
explicit live-engine skip; it does not establish runtime success.

Recommended, not yet authorized: the exact two-test-path extension in
evidence/initial-access-scope-request.md. Add the serial expected-list member
and precise boundary ownership/capability/witness coverage without weakening
assertions or repairing unrelated baseline inventory. Return future exact guard
bytes and focused verification for independent review. The checkpoint remains
open and shared paths stay reserved until then. Full live setup and subsequent
custody/reviewer/correction proof remain with W105706. See append-only
review-2026-09-07T03-37-28Z.md for evidence, authority assessment and limits.

## Owner-approved guard scope extension — 2026-09-07 — baton.prompt for Slawomir

Slawomir approved the independently recommended two-test-path extension in
evidence/initial-access-scope-request.md. This explicitly supersedes the earlier
not-yet-authorized disposition for those additions only. Tuner may append the
exact serial-module expected tuple member in tests/tools/test_parallel_runner.py
and add the precise constructor ownership, launch-proof capability association
and executable refusal witnesses in tests/manager/test_boundary_inventory.py,
both under v12/python/. Preserve all existing assertions and table members;
no wildcard exclusions, guard weakening or unrelated baseline repairs.

Return exact guard bytes and focused verification for independent review before
closing the initial-access checkpoint or transferring shared-path ownership.
This authorizes the bounded edits, not advance acceptance of future bytes or
the separately pending full runtime/custody proof. Finish this critical-path
checkpoint ahead of the live-Claude detach experiment preparation.

## Guard extension candidate — 2026-09-07 — baton.tuner

Executed owner message M107203 under W106896 claim 107206 after revalidating
the active plan, exact scope request and independent review. Changed only the
two authorized guard paths: the exact serial expected tuple gains the engine
module, and the inventory gains one stated constructor owner, one delegated
launch-proof owner, its exact refusing probe, and a live durable-binding witness.
The witness first proves both legitimate lines launch, then proves copied grant/
marker/proof metadata cannot cross-wire either actual roots or assignment labels.
Unminted roots and a non-callable launch proof also refuse.

Four focused checks pass. The preservation audit removes only the approved
additions from parsed candidate guards and proves the complete remaining AST
equals the saved base, preserving every existing assertion and table entry.
All eight initial candidate path hashes still match the independently reviewed
manifest. git diff --check passes.

The broader 13-check ownership/probe catalog sample has nine passes and four
failures: existing 172 unowned entries, 55 orphan validator associations, missing
persisted columns operation_id/settled_at, and 59 owned entries without probes.
Comparing saved pre-checkpoint production ASTs with current ASTs under the same
current guard bytes confirms no added unowned/orphan/missing-probe entries.
The checkpoint's two constructor gaps and launch-proof association are resolved.
The comparative probe output also exposes 11 unrelated excess declared probes;
the initial-source baseline has the same 11 plus this newly added checkpoint
probe whose production owner is absent in that substituted baseline. These
unrelated guards remain failures; no broad-suite success is claimed.

Exact evidence: evidence/initial-access-guard-manifest.json binds the saved
two-path base/candidate and evidence/initial-access-guard.patch (SHA-256
19df2debd00d4a6fc07bd75fdf149e49f62475cfa651cfa8022bcf0ca95768e2), and links the
unchanged initial manifest/patch. Preservation, focused results, broader output
and comparative probes are retained under evidence/initial-access-guard-*.
Return to independent review before acceptance or shared-path transfer.
No live engine, runtime setup, custody or full capability proof was performed.

## Independent initial checkpoint sign-off — 2026-09-07 — baton.codex

W106896 claim 107258 reviewed M107203's exact authorized guard extension and
M107254's candidate. All ten candidate paths are bound by the initial/guard
manifests; the initial eight are unchanged. Saved/current guard hashes and both
patches match. AST preservation confirms all prior assertions/table members are
preserved except the explicitly authorized added serial expected-list member.
The exact capability probe and two-live-line durable-binding witness are sound;
independent focused execution passes all four checks with captured output.

**Signed off at initial code/interface maturity.** This explicitly supersedes
the earlier awaiting-review/unsigned checkpoint state, including the guard gate
in review-2026-09-07T03-37-28Z.md. See append-only
review-2026-09-07T04-10-27Z.md for exact candidate digests, all five changed
existing test paths, authority assessment, verification and baseline limitations.
The wider baseline inventory still fails; no broad success is claimed.

Recommend owner closure of W106896 and release to W105982, which must revalidate
the reviewed shared-path bytes before editing. This sign-off is not full runtime
access acceptance: no live engine ran, and dedicated deployment setup plus the
custody/reviewer/correction sequence remain W105706. No production-adoption or
detach authority is added by this review.

## Owner releases live composition — 2026-09-07 — baton.prompt for Slawomir

The corrected custody code checkpoint is independently signed off in
../finding-v12-private-line-custody-locators/review-2026-09-07T05-16-52Z.md and
owner-accepted. Its eight current hashes match its corrected manifest. Slawomir
approved releasing W105706's code prerequisite without waiting for full W105982
closure: this Work supplies that provider's remaining live proof, so the previous
full-closure edge would deadlock acceptance. The detach experiment is not a live
composition prerequisite. Preserve the accepted stop-before-consume boundary.

Revalidate accepted code, then prepare/perform only the already scoped composed
runtime proof under explicit group/image/runner authority. No new deployment
choice or full capability success is implied. Historical full-closure sequencing
above is superseded by this code-checkpoint acceptance; live requirements remain.

## Owner-approved parallel handoff — 2026-09-07 — baton.prompt for Slawomir

Slawomir approved moving W105706 to baton.claude while baton.tuner continues
W106673's independent detach experiment. This changes remaining-checkpoint
ownership only: it grants no new runtime setup, production adoption, or test
mutation scope. Claude owns this access dossier and accepted access fixture/
correction scope; tuner retains the separate detach-experiment dossier only.
The current PLAN.md records the disjoint boundary and review-first return.
Earlier tuner ownership for the remaining live checkpoint is superseded;
historical initial implementation attribution is unchanged. Missing exact
group/image/runner authority must be surfaced before executing the live proof.

## Owner approves demonstration setup — 2026-09-07 — baton.prompt for Slawomir

For M107820 Slawomir approved a dedicated host group named baton-workspace,
membership for the sl test-runner account, and the installed image
sha256:979f11d53433f2930d69b70d81e265332547895cbd674e3e8b190cafb236243f,
subject to the fixture's compatibility checks. The bounded fixture may enable
BATON_V12_INITIAL_ACCESS_ENGINE=1, use the resolved dedicated gid as
BATON_V12_WORKSPACE_GROUP and that exact image as BATON_V12_PRIVATE_LINE_IMAGE.
Cooperative umask 0002 for the fixture worker and injected manager command
runner is approved for this demonstration only, not production defaults.
No model invocation, credentials, network, image build/pull or additional host
filesystem authority is granted. Fixture-owned cleanup stays in its existing
bounded harness scope; no unrelated resource cleanup is authorized.

Approval is not provisioning evidence: the group did not exist at inspection.
Record its allocated gid and verify the actual executing process holds it.
Updating account membership does not change the running agent's groups. A
fresh operator group-aware runner can execute the approved fixture without
restarting the entire stack; the agent must not run the proof as root to
substitute for the intended non-owner group-access proof.

## Dedicated group provisioned — 2026-09-07 — baton.prompt for Slawomir

Slawomir completed groupadd and gpasswd; independent getent verification returns
baton-workspace:x:1001:sl. The approved BATON_V12_WORKSPACE_GROUP value is 1001.
This supersedes the pending group-provisioning state above, not the requirement
to verify the actual runner's groups. Existing agent processes do not acquire
supplementary membership automatically. Resume bounded preparation; execute only
from a process holding gid 1001 as approved. If installed managed policy cannot
launch such a runner, supply an exact operator command rather than requesting
managed escalation or silently running as root. All image, fixture and
demonstration-only limitations remain unchanged.

## Operator initial-access failure — 2026-09-07 — baton.prompt

Operator verified the group-aware shell reports groups
1001 4 24 27 30 46 100 113 119 1000. The corrected explicit-module command
then ran exactly one test in 0.143s. In
tests/manager/test_private_line_access_engine.py:139 docker wait returned
container exit status '1', failing the expected '0'. This is a live fixture
failure, not a skipped test or a successful access proof. The underlying
container error is unknown; do not attribute it to permissions or image
compatibility without diagnostic evidence.

Confirmed diagnostic gap: the exit assertion precedes docker logs, and the
registered cleanup removes the exact container even after assertion failure.
A subsequent read-only docker ps -a --filter label=baton.initial-access found
no retained matching container. No container log survived through this harness
path for us to inspect. Capture bounded stdout/stderr and safe exit/state
evidence before assertion/cleanup in the next diagnostic candidate, preserving
all existing success and isolation assertions and fixture-owned cleanup.

An earlier operator paste inserted shell command breaks and accidentally ran
unittest discovery (4535 tests, 11 failures, 1 error, 17 skips), followed by
module-name command-not-found. It is not evidence of this intended live proof.
No broad rerun or unrelated container cleanup is requested. Its catalog,
inventory and cleanup failures are not established as caused by this Work.

## Diagnostic run identifies missing Git executable — 2026-09-07 — baton.prompt

The operator reran the explicit one-test command with diagnostic fixture SHA256
9e3d79c26ac5820040272da55f4e4d050ae30eb92a01b244736050af9460acfc.
One test failed in 0.158s. Container exited 1, Running=false, PID=0,
OOMKilled=false and engine Error empty. Its stderr identifies
FileNotFoundError: [Errno 2] No such file or directory: 'git', at the payload's
first git add invocation. This supersedes the unknown-cause status above for
this diagnostic run. It establishes executable resolution failure in the actual
runtime, not by itself whether Git is absent everywhere or outside its PATH.

The straight-line payload reached this point after appending tracked content,
creating nested/new and executing the fixture script. Those operations did not
raise; this is not evidence of group-write denial there. Later Git metadata,
commit, source read-only and full custody/reviewer/correction checks remain
unproved. Mount diagnostics show /output writable and source/launch/input
mounts read-only. No permission relaxation is justified by this result.

Earlier image approval and inspection were insufficient: exact ID, declared
user and volume metadata did not establish the required Git executable. Prompt's
image recommendation was conditional on compatibility but did not verify Git.
Current v12/worker/Dockerfile.claude includes git in apt-get; that source fact
does not establish contents of the selected older installed digest. Investigate
installed candidate capabilities and runtime PATH, then propose the smallest
image/setup correction with evidence. No automatic image substitution, build,
pull, production change or repeat of the same failing live command is approved.

## Owner selects Git-capable candidate — 2026-09-07 — baton.prompt for Slawomir

Slawomir approved K's M107987 replacement proposal and one focused fixture rerun:
sha256:0697b6595aff0af2a39a81d492223bf33cf69877426ec859fe1abb90abd617e4,
installed tag baton-w71917-provider-gate:20260905. K reports the apt build layer
includes git; prompt independently inspected exact ID, runtime user 65532:65532
and absence of declared volumes. Actual Git execution remains unproved until
the run. Diagnostic fixture hash still matches
9e3d79c26ac5820040272da55f4e4d050ae30eb92a01b244736050af9460acfc.
The older 979f11d5 image selection is superseded for this access fixture only.
The separate detach experiment's immutable package is not changed or authorized
to substitute images by this decision. All other group, permission, command,
no-network/no-credential and demonstration-only boundaries stay unchanged.
No build/pull, relaxed assertion or automatic repeated campaign is authorized.

## Operator initial-access proof PASS — 2026-09-07 — baton.prompt

Slawomir returned full unittest output for the approved explicit-module command:
test_initial_populated_line_is_writable_by_the_fixed_runtime ... ok;
Ran 1 test in 0.236s; OK. Image was
sha256:0697b6595aff0af2a39a81d492223bf33cf69877426ec859fe1abb90abd617e4,
BATON_V12_WORKSPACE_GROUP=1001 and initial-access opt-in enabled. Prompt
rechecked current fixture hash, still
9e3d79c26ac5820040272da55f4e4d050ae30eb92a01b244736050af9460acfc.
This is operator-supplied runtime evidence, not an independent rerun.

The fixture asserts fixed 65532:65532 runtime identity with the dedicated group,
tracked/nested writes and executable access, Git add/commit, read-only source,
created file/directory modes and group, stable line device/inode, changed HEAD,
and stopped/PID0 ending, with fixture-owned cleanup. Initial image/Git execution
uncertainty above is superseded by this successful run. Full custody consumption,
read-only reviewer and later same-line correction remain to be composed/proved;
do not close W105706 or substitute this PASS for those remaining checks.

## Operator custody/re-admission checkpoint PASS — 2026-09-07 — baton.prompt

Owner approved and executed only
InitialPrivateLineEngine.test_the_composed_ending_consumes_reviews_and_corrects_one_line.
Reported result: Ran 1 test in 0.235s; OK. Image0697b659, dedicated group1001
and explicit opt-in are unchanged. Current fixture SHA256 matches the handoff:
d94bf33b42ab347af6ca1d57a4fdd0d06889e8f42bd0970fad40c5664843c3a6.
This is operator-supplied evidence, not an independent duplicate run.

The case starts a real writer, confirms its stop, exercises the actual line
consumption proof and Git checkpoint over foreign-owned bytes, constructs an
ordinary review boundary, and admits a correction writer to the same device/inode
with the earlier commit/reference retained. It does not launch a reviewer or
correction runtime. Thus the test name and broad 'remaining proof' description
must not be read as full live-cycle acceptance. Remaining scoped checks are a
real read-only reviewer denying writes to tracked content and Git metadata while
writing its own output, and a subsequent fixed-user writer editing/committing
in the same line with old checkpoint resolution still valid. Preserve these
passing checkpoints; no unrelated hardening or broad test rerun is needed.

## Independent final fixture review — 2026-09-07 — baton.codex

Claim108160 reviewed M108096 and candidate09d99499ebe811de16320fa930fadf30744c8b372625c7d6e794061187d5cbad.
Exact candidate and comparison are retained in evidence/review-runtime-*.
Reconstructing the predecessor by removing explicit additions and restoring the
saved original cleanup yields the exact operator-reviewed d94bf33b digest; this
is verified reconstruction, not contemporaneous retention. Both previous test
bodies and all assertion semantics are preserved. Eight accepted custody source/
test hashes match; module and payload syntax compile. No live or broad run occurred.

**Confirmed coverage gap, changes requested:** after the second runtime stops,
the correction case reads bytes/stat and resolves commit/reference IDs, but does
not record second completion, prove second consumption, freeze/validate current
checkpoint evidence or audit the old checkpoint through its profile. Thus a PASS
would not yet establish the manager-validation portion of PLAN item5. This is a
test coverage gap, not an observed runtime or production failure. Complete these
already planned checks additively in the same fixture, then return new digest and
delta through independent review. Exact finding and scope assessment are in
review-2026-09-07T06-31-04Z.md; PROGRESS remains the implementer's record.

**Supersedes M108096's pending whole-module run proposal:** preserve the two
completed operator checkpoints and propose only the two remaining exact methods
after correction review. New methods need their own live first-writer setup;
the old standalone passing cases need no duplicate execution. Approved group,
image, non-root cooperative demonstration and cleanup boundaries remain resolved.
No new production, credential, network, group or detach authority is required.

## Independent correction-fixture sign-off — 2026-09-07 — baton.codex

Claim108214 reviewed M108208. Candidate SHA256
20981569e64054222404b4765d3114c4dbb7630c02aa70e81ac7ee0ec06ae2d7
adds the missing post-stop assignment2 consumption, second checkpoint freeze/
current validation and historical revision1 audit. All previous assertions and
other method ASTs remain intact. Eight accepted custody hashes match. One focused
real-Git history/profile test passed independently in0.037s; no OCI or broad run.
Exact candidate/delta/manifest and output are retained under evidence/review-correction-*.

**Supersedes the P2 changes-requested state in review-2026-09-07T06-31-04Z.md:**
the final fixture candidate is signed off in review-2026-09-07T06-37-03Z.md.
Its exact two-method operator command preserves the completed initial and
host-composition checkpoints. Return to baton.ops for execution disposition and
retain actual results for independent evidence review. Candidate sign-off is not
live success, full capability closure, production adoption or repeat authority.
Existing non-root/group/image/cooperative demonstration and confirmed-stop
boundaries remain unchanged. PROGRESS remains the implementer's account.

## Owner approves final two runtime cases — 2026-09-07 — baton.prompt

Slawomir approved one invocation of the two new reviewer/correction methods in
review-2026-09-07T06-37-03Z.md. Immediate fixture SHA256 matches
20981569e64054222404b4765d3114c4dbb7630c02aa70e81ac7ee0ec06ae2d7.
This supersedes pending owner execution disposition, not live-result review.
Group1001, installed image0697b659, fixed identity, cooperative fixture-only mask,
no network/credentials/build/pull and exact fixture-owned cleanup remain.
Do not select the two completed standalone checkpoint methods again. A failure
requires diagnosis, not automatic repeat or changed assertions.

## Operator final reviewer/correction runtime PASS — 2026-09-07 — baton.prompt

Slawomir returned full output from the approved two-selector invocation under
group1001 and image0697b659: test_a_reviewer_runtime_cannot_write_the_checkpoint_it_reads
... ok; test_a_correction_runtime_advances_the_same_line ... ok;
Ran 2 tests in 0.790s; OK. Immediate current fixture SHA256 still matches the
independently reviewed candidate
20981569e64054222404b4765d3114c4dbb7630c02aa70e81ac7ee0ec06ae2d7.
This is owner-supplied live evidence, not an independent duplicate execution.

The reviewed cases cover actual reviewer tracked/metadata/create EROFS denials
with separate writable output and actual fixed-user correction/descendant commit
on the same line. The corrected second case also records completion after stop,
proves generation2 consumption, freezes/validates its new checkpoint and audits
revision1 through the owning API. Fixture cleanup completed without unittest
failure. Earlier initial-access and host-composition PASS results stand.
Return these combined results for final independent evidence disposition; no
further repeated runtime/broad campaign is requested. This is the configured
file/Git access demonstration, not provider/model integration, production umask
rollout or adoption of experimental live detach.

## Independent configured runtime acceptance — 2026-09-07 — baton.codex

Claim110251 reviewed owner approval M110235 and final result M110248 against
the signed-off fixture. Both final selected cases report PASS in0.790s; earlier
initial-access PASS1/0.236s and host-composition PASS1/0.235s remain valid. Current
candidate and retained bytes match20981569e64054222404b4765d3114c4dbb7630c02aa70e81ac7ee0ec06ae2d7;
all ten source/test dependency hashes also match the prior review manifest.
The exact eleven-path audit and operator-result references are retained in
evidence/review-final-runtime-evidence-2026-09-07.json.

**Supersedes pending final evidence acceptance:** review-2026-09-07T12-52-22Z.md
accepts the configured fixed-user/group file/Git runtime demonstration and
recommends owner satisfying closure of W105706. Actual reviewer write denials
and separate output, same-line descendant correction, post-stop consumption,
new checkpoint validation and historical checkpoint audit complete the planned
acceptance. No review finding or additional runtime/broad repetition remains.

Provenance is owner-reported operator execution relayed through Baton and this
record, independently checked against reviewed bytes; no duplicate execution,
original stdout capture or fresh container inspection is claimed. Fixture stop
and cleanup assertions passed according to the reported OK. Synthetic lifecycle
builders and file/Git payloads do not establish standalone Authority or provider/
model integration. Cooperative umask0002 remains demonstration setup, not a
production-default rollout; confirmed stop and separate detach-adoption scope
remain unchanged. PLAN now names owner closure as the sole current action.

## Owner accepts completion — 2026-09-07 — baton.prompt for Slawomir

Slawomir confirmed W105706 is done following final independent acceptance in
review-2026-09-07T12-52-22Z.md. Prompt rechecked current fixture20981569 against
that review. Accept satisfying closure at the configured file/Git runtime-access
demonstration boundary. All recorded provenance and production/provider/detach
limitations remain; no additional test run or Git mutation is needed for closure.
