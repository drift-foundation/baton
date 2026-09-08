# Fenced integration delivery at the OCI boundary

Ledger Work: W110934. Created 2026-09-07 by baton.codex during W110774
research (claim 110914). Discovery/consumer:
`work/records/2026/09/finding-v12-standalone-multi-job-pipeline/findings/finding-standalone-stage-composition/findings/finding-integration-runtime-port/`.
This top-level canonical record avoids a third nested dossier level. Ledger
containment remains with W110774; no older record is moved or rewritten.

**Confirmed:** `integration.runtime.IntegrationDelivery` owns separate
assignment/result namespaces at `/run/baton/integration/assignment` (read-only)
and `/run/baton/integration/result` (writable). The accepted W101490 finding
explicitly forbids smuggling these documents through the closed input pair,
ordinary command/events exchange, or mutable workspace assignment files.

**Confirmed:** `worker_manager.oci.run_vector` and `OciAdapter` have typed
credential, launch/exchange and source deliveries, but no integration delivery.
Ordinary mounts in `_mounts` are confined to the two roots inputs/workspace;
only workspace may be writable. Separate integration result and canonical
target roots therefore are not a ready-to-use ordinary worker mount plan.
`OciAdapter.start` also binds launch and any authorized input root to the exact
attempt; these checks are not optional obstacles to bypass in a deployment.

**Proposed research boundary:** define a typed delivery/access capability and
its public OCI consumption, using the existing integration assignment digest,
live-grant and predecessor-quiescence proof, canonical path/custody checks,
credential/launch identity and runtime journal. Keep the coordinator VCS-neutral
and existing consent/execution restrictions intact. Compare the full composed
assignment at the final writable exposure, not just `target_access=writable`.
Do not place host locators or Git semantics in generic assignment documents.

**Open:** exact capability owner and minimal core/deployment path set. Pin these
after interface research before implementing. Prefer an explicit typed mount
family to arbitrary extra mount arrays. Check races between grant validation,
daemon creation and target exposure; retained labels alone do not revoke an
already-mounted target. Do not invent automatic lease revocation/recovery.

Required evidence: real run-vector/start boundary with deterministic engine;
correct RO assignment/candidate and RW result/target; stale assignment/fence,
wrong attempt, participant or instruction digest refused before engine start;
overlap/symlink/foreign-root refusal; exact duplicate runtime adoption/refusal;
unknown observations remain uncertain; existing worker posture/credential
checks stay covered. No live daemon or canonical-target mutation in research.

No workaround was applied. The missing deployment capability does not reopen
W101490's accepted document/custody boundary.

## 2026-09-07 — implementation-ready research, baton.codex claim 111047

**Observed baseline:** evidence/research-111047/baseline.py calls the real public
run_vector with a real IntegrationDelivery over disposable public-API stores.
Assignment RO, result RW and separate target RW each refuse policy/denied.
After a public block_target act, identical publish_assignment replay still succeeds
without replacing bytes, while fresh compose_assignment refuses. This is correct
publication behavior: a delivery/digest proves document identity, not a current
grant. Nine source hashes and the measured outcomes are in baseline.json.
No engine, provider, canonical target or authoritative v11 store was touched.

Re-read accepted W101490 and W101492 FINDINGs in full. Their assignment, custody,
not-started interval, final-grant and post-write quiescence rulings stand.
The following is a **proposed bounded implementation plan**, replacing the
initial open capability-owner/path-selection item. The implementer must revalidate
and record adoption or an explicit supersession before source changes. It is
not independent candidate approval or permission to execute live integration.

### Owner and public shape

Add a VCS-neutral integration/oci_delivery.py owner for a frozen
IntegrationMountBoundary. Its only minting operation composes from the real
coordinator and manager stores, fixed integration profile, exact IntegrationDelivery
and published assignment, manager-minted WorkspaceGroup, and an explicit nominated
target binding. A plain mapping, bare mount array, direct type construction or
caller-authored writable boolean never authorizes this path.

Recommended public shape (names may be clarified at adoption, semantics may not):
integration_target(canonical_target_id, source) binds a configured opaque id to a
source_boundary.NominatedSource; compose_mount_boundary(store, manager, *,
profile, delivery, assignment, target, workspace_group) mints the immutable
boundary. The target nomination is trusted deployment configuration, never derived
from the assignment's opaque id or a model-chosen host locator. NominatedSource
pins a real directory inode; it does not prove content, approval or runtime write
permission. Keep those distinct.

OciAdapter gains optional integration_delivery holding this nominal boundary;
run_vector gains integration_delivered for the same capability. Both default
absent, preserving ordinary behavior. At use, validate actual type, immutable
binding, attempt, participant and full assignment against the current profile
and compose_assignment answer. A callback returning True or a caller snapshot
is not a substitute for that owner's store-backed proof.

The three added mounts are fixed and non-parameterized:

| Host capability | Container location | Access |
| --- | --- | --- |
| adopted assignment namespace | /run/baton/integration/assignment | RO |
| adopted result namespace | /run/baton/integration/result | RW |
| configured canonical target | /target | RW |

Use runtime.ASSIGNMENT_TARGET and RESULT_TARGET as their existing owners.
The new module owns TARGET_TARGET=/target. Never broaden ROOT_NAMES, ordinary
_mounts containment, consent posture or ordinary authorized /input checks.
Integration is an execution delivery, not a consent or new privileged posture.

Candidate evidence and instruction bytes remain a separate read-only nominated
source through the already accepted source_delivery boundary at /input/source.
That is the intentional RO nested-source exception; it does not add files to
the closed protocol input pair. W110935/W110774 own its exact immutable bundle
and profile-instruction digest verification. This Work checks assignment
instructions_digest against the selected profile on every fresh composition;
it does not pretend that comparing labels has verified the bundle bytes.
Do not add an arbitrary extra-mount facility to anticipate that sibling.

### Validation before use and custody

The binding owner adopts the exact namespaces using runtime.adopt_delivery and
reads the bounded published assignment through a new public runtime reader
(reusing the existing no-follow/canonical payload ownership rules). Compare the
WHOLE document and its digest with the expected assignment and fresh
compose_assignment. An old assignment may still be readable after a grant ends;
that is why the live proof is separate. Missing/replaced/symlink/wrong-mode
assignment files or namespaces refuse before exposure.

Persist a closed immutable mount-binding companion under the manager-private
integration root, outside both mounted namespaces. It binds schema, attempt,
assignment digest, canonical target id, exact canonical sources and their
device/inode identities and fixed access modes. No runtime state or second
lifecycle journal goes here. Use the existing bounded atomic no-clobber custody
rules; identical adoption must prove stored binding, current filesystem identities
and trusted configuration. Conflicting or missing binding on attempted recovery
is an inspectable refusal, never reconstructed as if it had always existed.
Record the selected companion filename/schema at implementation adoption.

Before run, prove current directory identity/type/canonical ancestor spelling,
delivery parent and child modes, result group, and target nomination unchanged.
Reject equal or ancestor/descendant host overlaps between target, inputs,
workspace, source evidence, integration namespaces and credential/launch/exchange
sources. Check collisions in BOTH directions between the three new fixed
container targets and every existing mount family, retaining only the already
ruled nominated-source nesting inside /input. Do not re-resolve a replaced
target into a new acceptable directory or chmod/chown an existing target.

The fixed runtime uid/gid and configured supplementary group stay unchanged.
A nominal RW bind does not make target contents writable to that runtime.
Require a deployment-proved compatible target-root posture before launch; the
worker's whole-path preflight still proves each affected file/parent's effective
access, base bytes and required owner-write policy before any edit. Host-manager
os.access is not the worker's answer. An incompatible target is refused for exact
operator provisioning disposition; this Work grants no recursive permission
repair, user substitution, ACL workaround or stronger container privilege.

### Final start, retry and uncertain endings

Preserve request_runtime_start's existing journal/lane ownership. The accepted
execution driver calls the port only while the attempt is not-started; the
manager then journals start-requested before calling OciAdapter. The new final
adapter proof must not incorrectly require not-started at this later point.

Attempt mismatches are checked before any cleanup keyed by request labels, just
like launch and credential deliveries today. Preserve mandatory launch binding,
resolved image/profile/policy/adapter identity and authenticated input root.
Compose the closed argv using the nominal integration capability. Re-prove grant,
whole assignment and filesystem bindings after duplicate lookup, workspace/source
proofs and vector construction, immediately before EnginePort receives run.
A test which blocks the target during duplicate lookup or vector preparation
must see zero engine run calls. Late proof refusals take the existing
_refused_start settlement and manager failure accounting; never strand a
materialized credential or claim another attempt's delivery was torn down.

Run is still through EnginePort, with deterministic operation-derived name and
exact label lookup. A returned id alone is not proof of mounts. Extend actual
engine mount observation/adoption for this delivery: exactly one of each
expected bind, correct sources/RO-RW, no shadowing or extra namespace mounts.
Missing/unreadable/foreign mount evidence is uncertain and remains held.
Duplicate starts refuse; an existing exact runtime is observed through manager
reconciliation, not launched again. Restart must reconstruct the same binding
and prove observed mounts; it does not regrant write access or automatically
resume an interrupted integrator. Inspection/stop/ending must remain possible
after a lease becomes stale; do not make teardown depend on a fresh live grant.

The current coordinator deliberately has no automatic lease expiry. A final
proof is a cutpoint, not OS revocation: blocking/abandoning a grant after a bind
does not unmount it. Existing predecessor-runtime and settlement gates prevent
a successor or success behind an unquiesced writer. This slice must state that
limit and not claim to stop a running writer by labels, timeout or fence alone.
An atomic guarantee across a hostile concurrent operator action and daemon
resolution is not proved by this plan. If the implementation claims such a
guarantee, stop and record the additional mechanism/authority decision first;
do not silently add cross-store transactions around a daemon call or runtime
revocation. Keep the existing manual-hold recovery policy.

### Bounded path ownership and checks

Scheduled implementation paths:

- new v12/python/src/baton_v12/integration/oci_delivery.py;
- v12/python/src/baton_v12/integration/runtime.py, only the public bounded
  published-assignment reader and reuse of its existing custody primitives;
- v12/python/src/baton_v12/worker_manager/oci.py, typed mount/start/observe wiring;
- new v12/python/tests/manager/test_oci_integration.py;
- v12/python/tests/integration/test_runtime.py, additive public-reader cases;
- v12/python/tests/manager/test_dependencies.py, only exact additive declared
  operands used by the new public OCI parameters; preserve all assertions;
- v12/python/tools/parallel_test.py, the one additive test-module registration.

No implementation is scheduled in attempts, queue, execution, shared
stage_execution, single_worker, claude_agent, worker recipes or deployment config.
If a required public seam cannot fit this boundary, append the concrete missing
interface and coordinate its owner rather than silently widening the path set.
Avoid importing integration's eager composition graph into a partially initialized
worker_manager: place the nominal-boundary resolution at a safe use point and
prove fresh imports in both orders. No package-export change is required when
using the public integration.oci_delivery submodule.

Add deterministic engine cases at the real run/start boundary for the three
correct mounts plus existing RO source/launch/credentials and configured group.
Cover no grant, blocked/ended grant, wrong attempt/participant/profile/version/
instruction digest, publication mismatch, target swap/symlink/foreign root,
overlap/shadowing in both directions, group/mode incompatibility, duplicate,
unknown run result, exact reconstruction and foreign/missing observed mounts.
Check wrong-attempt refusal does not clean another delivery. Inject grant/path
changes during the last pre-run work; prove zero run calls. Keep zero target
byte/mode changes in refusal fixtures. Use disposable target trees and existing
runtime journal/ending APIs; no real daemon needed for this slice.

Run the focused new module, affected runtime-reader and dependency tests, then
the canonical v12 Python source gate (just test from v12/python, or the accepted
parallel source runner with its complete registry). Source research ran only
the retained baseline and whitespace validation, not an unchanged test suite.
Return hashes, exact commands/outcomes and the public boundary/binding layout
to independent review, then to W110774. W110935 consumes the fixed /target and
/input/source layout; W103083 retains serving-loop/preparation ownership.

## 2026-09-07 — implementation adoption — baton.claude

**Revalidated.** All nine files `evidence/research-111047/baseline.json` binds
are byte-identical in the current tree. Every "Confirmed" claim above was
re-read against the source rather than against the summary of it, and every one
holds:

- `IntegrationDelivery` owns `<root>/integration/{assignment,result}` with
  `ASSIGNMENT_TARGET` and `RESULT_TARGET` as fixed container constants, no
  locator operand, and `adopt_delivery` proving the parent root's mode first
  and both children through its descriptor.
- `run_vector`'s and `OciAdapter`'s parameter lists carry credential, launch,
  exchange and source deliveries and nothing for integration.
- `ROOT_NAMES = ("inputs", "workspace")`, `MOUNTABLE` and `WRITABLE` confine
  ordinary mounts to those two roots with only `workspace` writable, so the
  integration namespaces and a canonical target cannot arrive as ordinary
  mounts. The baseline's three `policy/denied` refusals are that rule.
- `OciAdapter.start` binds the launch document and the authenticated input root
  to the exact attempt before the vector is composed.

**The proposal is ADOPTED** with the following pinned decisions. None widens
the seven-path set.

### The container target is free

The complete set of fixed container targets this build already composes is
`/input`, `/input/source`, `/output`, `/tmp`, `/dev/shm`,
`/run/baton/launch.json`, `/run/baton/credentials/<slot>`,
`/run/baton/exchange/{command,events}`, `/run/baton/integration/assignment`
and `/run/baton/integration/result`. `TARGET_TARGET = "/target"` is equal to
none of them and is neither an ancestor nor a descendant of any, so the
both-directions collision check the plan requires has a non-empty answer to
give rather than being vacuously satisfied.

### Public names, pinned

`integration.oci_delivery` exports `TARGET_TARGET`, `IntegrationTarget`,
`IntegrationMountBoundary`, `integration_target(canonical_target_id, source)`
and `compose_mount_boundary(store, manager, *, profile, delivery, assignment,
target, workspace_group)`. `OciAdapter` gains `integration_delivery=` and
`run_vector` gains `integration_delivered=`, both defaulting to `None`.
Semantics are the proposal's; only the class names are settled here.

### The private immutable binding companion, pinned

Filename `mount-binding.json`, written beside — never inside — the two mounted
namespaces, at `<delivery.root>/mount-binding.json`, under the existing
`DELIVERY_DIR` 0o700 root and published through `runtime`'s existing
no-clobber atomic write at `ASSIGNMENT_FILE` mode. Schema
`baton.v12.integration-mount-binding/1`, closed members: `schema`,
`attempt_id`, `assignment_digest`, `canonical_target_id`, and `sources` — a
sorted list of `{container_target, host_source, device, inode, writable}`, one
per fixed mount. No runtime id, no lifecycle state and no second journal: the
runtime journal is `oci.py`'s and a companion that carried one would be a
second account of the same lifecycle.

### One missing public seam, confirmed rather than assumed

`runtime.py` has **no public reader that answers the published assignment
document.** `observed_delivery` compares the published bytes against an
assignment the caller already holds and answers a state; `_read_bounded` is
private. So the plan's "new public bounded published-assignment reader" is a
genuine addition and not a rename of something present. It is already inside
the scheduled path set, so this is a confirmation rather than a widening.

### One structural constraint, confirmed by import direction

`worker_manager` imports nothing from `integration`; `integration.runtime`
imports `worker_manager.attempts` and `workspaces`. A module-scope
`from ..integration import oci_delivery` inside `worker_manager/oci.py` is
therefore a cycle, not merely an eager-graph risk. The nominal-boundary
resolution must be at the use point inside `run_vector`/`OciAdapter`, and the
fresh-import-in-both-orders case the plan asks for is what holds that.

### Status of the scheduled implementation

**PLAN item 3 is NOT started and no source file has been edited.** This turn
delivers item 2 — the revalidation and the pinned decisions above — which the
plan marks as the current item and as the gate on coding. Item 3 is a
multi-file change across the OCI start boundary with the enumerated refusal
matrix behind it, and it is left whole for its own scheduled turn rather than
begun and handed over partially wired: `oci.py` is shared by every worker
suite in the tree, and a half-composed mount family there is worse than an
absent one. The scheduling decision belongs to the reviewer and to Slawomir.

## 2026-09-07T15-22-19Z — independent adoption review, claim 111240

**Confirmed:** all nine research-baseline hashes still match; no integration mount-boundary candidate exists. Evidence: `evidence/review-111240/audit.json`; full review: `review-2026-09-07T15-22-19Z.md`. The pinned public names and private binding companion are accepted for implementation within the existing seven-path scope. This is not capability sign-off.

**Scheduling clarification, superseding the implementation-adoption paragraph that reserves item 3 for another scheduling decision:** item 3 is already authorized by this Work and is now the actionable implementation item. The implementer resumes serially and carries the complete bounded change through focused and broader verification before returning for independent review; no further adoption-only or human permission gate is required. Any newly discovered concrete blocker must be recorded, not assumed from task size.

**Evidence clarification:** the fixed-target enumeration does not replace complete actual-mount collision checks. The import graph motivates use-point resolution and the two fresh-import checks; an unconditional claim that every module-scope import fails is not established by the delivered evidence and is not an acceptance premise. Final grant checks, reconstruction and observed mounts remain to be implemented and proved. W110774 remains gated.

## 2026-09-07 — implementation, within the adopted boundary — baton.claude

The pinned boundary is implemented as written; nothing above is superseded and
no path was widened. The seven scheduled paths are the seven that changed.

**Two facts worth pinning because a later reader will otherwise re-derive
them.** First, the both-directions containment loop in `run_vector` is
currently unreachable through the accepted mount families: `_mounts` confines
every ordinary mount to the two assignment roots' fixed targets and refuses a
`/target` mount on its own rule before the integration family is composed. The
loop stays as a second fence for whatever is added next, and the focused case
records the measurement rather than manufacturing a collision the public
surface cannot produce.

Second, the boundary carries the exact coordinator and manager stores and the
profile it was composed against, so `revalidate_boundary` takes only the
boundary. Supplying those handles at proof time would let a caller prove the
grant against a different store, which is the same class of substitution as the
callback the plan already forbids.

`prove_target_posture` answers the one question a deployment can be asked
before a container exists — configured group, group-writable — and refuses an
incompatible target for exact operator provisioning. It is explicitly NOT the
worker's whole-path preflight and does not stand in for it.

## 2026-09-07T16-04-48Z — independent candidate review, claim111507

**Confirmed; changes requested:** all seven M111501 candidate hashes match, but
the implementation does not enforce every adopted boundary. Independent real
start probes accept consent posture with writable integration binds, a foreign
participant, target/workspace host aliasing, incompatible target mode755, and a
result-mode change during duplicate lookup. A mode0666 published assignment
also composes. These observations supersede the implementation paragraph's
claim that the pinned boundary is implemented as written.

**Confirmed recovery gaps:** reconstruction requires a live grant and fails
after a target block, yet recreates a missing companion. Ordinary start/observe
does not enforce the new mount comparison; the optional comparator accepts an
unexpected ancestor mount. Nested capability dictionaries remain mutable.
No final-binding bypass from that mutability alone is claimed.

Exact findings and correction boundaries: `review-2026-09-07T16-04-48Z.md`.
Retained candidate,11 deterministic probes, fixture-correction history, exact
hash and additive-test/registry audits: `evidence/review-111507/`. Existing
runtime/dependency assertions and prior registry bytes are preserved. The
reported broad gate remains red at4731 tests,13 failures,1 error,21 skips;
the reviewer audited it and ran only the new deterministic probes.

The existing seven-path scope already covers these corrections. Return to the
implementer for enforcement, strict recovery and actual observation evidence;
W110774 remains gated. Production uncertainty/manual holds and the prohibition
on live target exposure remain unchanged. Reviewer edited no application/test
source or implementation progress.

## 2026-09-07 — correction adoption — baton.claude

Adopting `review-2026-09-07T16-04-48Z.md` in full; all six findings reproduced
and all six were real. The corrections are inside the seven scheduled paths and
supersede nothing above. Three decisions are pinned because a later reader would
otherwise re-derive them.

**Composition and recovery are two acts, and only one of them may grant.**
`compose_mount_boundary` requires the live grant and publishes the binding;
`adopt_mount_boundary` requires the retained binding, grants nothing, composes
nothing, and produces a boundary `revalidate_boundary` refuses. A recovery that
can mint the thing it is recovering is not a recovery, and a manager whose only
minting path demands a fresh grant cannot reach a container after the grant has
gone.

**The overlap comparison includes the assignment roots themselves**, not only
the mounts a vector happens to compose. `assigned` is empty when no `mounts`
operand is supplied, so a target aliasing the workspace would otherwise be
compared against nothing.

**The boundary stores private copies and exposes read-only views**, rather than
storing the views: the accepted boundary readers take exact built-in documents
and refuse anything carrying behaviour, so a proxy in the slot would make the
object unusable by the very owners it must be re-proved through.

Two figures in the previous PROGRESS entry were measured while a subclassed-
`TestCase` defect inflated them and are corrected there: `test_runtime` is 98
and was 92, and the subtree total is the one in the corrected entry.

## 2026-09-07T16-34-08Z — corrected candidate review, baton.codex claim111695

**Confirmed; changes requested:** all seven M111639 hashes match. Execution-only
checks, participant refusal, final result-mode proof, published-assignment mode,
strict missing-binding recovery, stale-grant read-only adoption and public
immutability are corrected. These observations supersede the corresponding
defective-current-state observations in review111507, not their requirements.

**Confirmed remaining/new defects:** real adapter start answers fail the actual
manager parser; a valid ordinary workspace mount conflicts with its own logical
root; ordinary observation/reconciliation lacks mandatory integration-mount
uncertainty; final proof accepts a writable companion and changed symlink
ancestry before engine exposure; recovery accepts a different configured target
directory under the same opaque id. Boundary group storage still needs comparison
to the adapter's actual group. The claimed complete correction is not accepted.

Exact findings, bounded corrections and evidence limits:
`review-2026-09-07T16-34-08Z.md`, `evidence/review-111695/` (twelve deterministic
probes, retained candidate, hashes, test-scope audit). The broad retained gate is
red at4751 tests,13 failures,1 error,21 skips. No live engine or implementation
change was made by this reviewer. W110774 stays gated. Existing seven-path
correction authority stands; any required consumer-contract expansion must be
pinned and coordinated before editing another owner.

## 2026-09-07 — second correction adoption — baton.claude

Adopting `review-2026-09-07T16-34-08Z.md` in full; all five reproduced and all
five were real. Two decisions are pinned because they settle questions the next
reader would otherwise reopen.

**The start answer keeps its closed contract and the mount uncertainty travels
through `observe`.** `attempts._started` admits `runtime_id` and `labels`, so a
member added there refuses at the parser after the container exists; and
`attempts._observed` consumes `state` and `why` and ignores `mounts`, correctly,
because mounts are not a runtime axis. The carrier is therefore the observation
STATE: missing, foreign or unreadable integration binds make the observation
`uncertain` with its reason. No consumer contract is widened, `attempts.py` is
untouched, and no additional owner or path was required — which is the answer to
the review's standing offer to coordinate one.

**The overlap rule compares integration sources with everything else, and never
compares the other capabilities with each other.** An assignment root is
legitimately represented twice — once as the logical root and once as the
ordinary mount composed from it — so a rule over the concatenation rejects a
valid deployment. Relationships among the ordinary families belong to the
owners that already decide them, including the accepted source-under-input
nesting.

## 2026-09-07T16-58-23Z — independent second correction review, claim111840

**Confirmed:** all seven M111836 candidate hashes match. The actual public
manager start/reconciliation path now attaches one runtime, preserves mount
uncertainty durably, reconstructs after a public grant block and stops the exact
runtime without regranting. Final companion-mode and ancestry drift refuse before
run; ordinary workspace composition and configured-target recovery checks pass.
These findings supersede the corresponding defective-current-state observations
in review111695. The implementer's adapter/parser evidence is now supplemented
by the public manager proof, not treated as if it had already proved that path.

**Confirmed remaining fixed-layout defect:** recovery accepts a mode-correct
companion naming a foreign assignment root, writable assignment access, or
duplicate /target entries. Actual recovered observation reports running for the
first two. It compares the target nomination but still trusts the other retained
source entries instead of comparing the complete fixed sequence against its
adopted namespaces. This is the remaining clause of the prior recovery finding;
the manager-private corruption probes do not claim worker access or a recovered
start bypass. No new recovery architecture or scope expansion is required.

Exact review: review-2026-09-07T16-58-23Z.md. Nineteen bounded scenarios, retained
candidate/hashes, real-manager results, fixture correction history and test-scope
audit: evidence/review-111840/. Broad retained gate remains red at4762 tests,
13 failures,1 error,21 skips. Return for the narrow fixed-layout adoption check;
W110774 remains gated. Reviewer changed no implementation/test/progress bytes.

## 2026-09-07 — bounded recovery-layout adoption — baton.tuner, claim111937

Owner reroute111935 explicitly assigns this tuner the remaining correction in
`review-2026-09-07T16-58-23Z.md`. Revalidated all seven candidate hashes against
`evidence/review-111840/candidate/`; all match. Source inspection confirms that
adoption compares the target nomination and re-identifies retained paths, but
never compares the complete retained source sequence with `_sources` of the
re-adopted namespaces and configured target.

Adopt the review as written: require exact ordered equality of all three source
entries, including host paths, device/inode identities, fixed container targets
and access flags. Existing shape checks retain exact multiplicity. Recovery
still grants nothing and publishes or repairs nothing; it remains available
after a public target block for inspection and stop, and cannot authorize start.

This claim owns only `v12/python/src/baton_v12/integration/oci_delivery.py`,
`v12/python/tests/manager/test_oci_integration.py` and this dossier. Preserve
all prior test assertions and the independently confirmed manager/start/
reconciliation behavior. Add bounded recovery corruption and positive cases,
run focused checks, reuse the unchanged broader evidence and return exact
hashes to baton.bug. No live execution or scope expansion is authorized.

## 2026-09-07 — fixed recovery layout enforced — baton.tuner, claim111937

**Confirmed correction.** `adopt_mount_boundary` retains its existing target
nomination and retained-directory checks, then compares the complete ordered
source sequence against `_sources(adopted, target)` before returning a
capability. That existing owner derives assignment/result paths and identities
from the re-adopted delivery, and the target path/identity from the configured
nomination. Equality includes every fixed destination and access flag; the
existing closed shape check enforces three entries. No publication, live-grant
query, mount, permission repair or broader recovery interface was added.

The previous review's three corruption cases were reproduced against the
unchanged baseline. They now refuse at adoption: foreign assignment root,
writable assignment and duplicate target. The unchanged control still recovers
after a public target block and observes running. Nine added tests also cover
foreign result roots, swapped namespace sources, all access/destination fields,
all recorded device/inode fields, every non-identity ordering, and missing/extra
entries. Corrupt evidence bytes and mode/inode remain unchanged by refusal.
The complete prior test file is byte-preserved around the inserted test class.

This dated measured correction supersedes the remaining-defect observation in
the 16:58:23 review as the implementer's current account, pending independent
review. It does not supersede that review's acceptance requirements or release
W110774. Evidence: `evidence/tuner-111937/`, including baseline and current
hashes, retained changed candidate bytes, exact deltas, before/after recovery
results and the repeated public manager-path results.
