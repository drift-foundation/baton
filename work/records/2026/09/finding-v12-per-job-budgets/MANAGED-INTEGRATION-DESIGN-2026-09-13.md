# Managed, relocatable integration — prerequisite design for independent review

**Historical v1.** Independent DESIGN-REVIEW-161103-2026-09-13.md rejected the
unspecified capacity relationship. The revised proposal is
MANAGED-INTEGRATION-DESIGN-v2-2026-09-13.md (claim161207). Its explicit
supersessions and finite path plan are current for independent design review;
neither version grants implementation authority. This original text is preserved.

Prepared by baton.codex under claim161035. **Planning proposal, not implementation
authority or self-review approval.** Owner decision: FINDING2026-09-13T13:47:40Z,
discussion M161029, reroute161030. This replaces the host-only remedy proposed in
RECOVERY-SCOPE-DISPOSITION-2026-09-13.md; historical evidence stays in place.

## Required outcome and boundary

Integration preparation, reconciliation, causal verification and final imported
content verification execute in managed Docker attempts. Each has a real claimed
execution identity, immutable input, private workspace, declared output, configured
Job limits, observed runtime state and the ordinary stop/freeze/collection/cleanup
or explicit abandonment path. Running the coordinator in a container does not
satisfy this requirement. No control store, Authority session or unrestricted
coordinator filesystem is delivered to a candidate-executing workload.

The coordinator may run on machine A while the integration execution and target
owner run on B. The relocation unit is the existing input/assignment/launch
delivery plus declared outputs and managed runtime observations. Host paths,
device/inode pairs and Docker IDs are local capabilities of their execution node,
not portable content identity. No new socket/RPC protocol, farm scheduler or farm
deployment is proposed. A transport adapter can move existing deliveries; merely
changing Docker's host address while keeping A's bind paths is not relocation.

The architecture preserves the distinction between untrusted worker evidence,
trusted runtime exclusion evidence, and the integration/Authority owners' adoption
and settlement. A process exit, provider report, frozen artifact or successfully
prepared tree alone never grants publication, canonical reference advance or an
integrated receipt.

## Confirmed reusable contracts and concrete gaps

| Existing owner/interface | Reuse | Gap that must not be hidden |
| --- | --- | --- |
| workspaces.compose_input_root, assignment_workspace; contracts manifests | `/input/input.json`, assignment identity, bounded declared input/output, per-attempt roots | Node-local source nomination is not a portable reference; materialize and validate on the receiving node |
| launch.launch_document/materialize/adopt `/3` | Job execution context, immutable requested/effective limits, actual runtime input/policy identities | Reconciliation execution needs its own manifest/attempt linked to the original Job; do not equate its manifest with the submitted producer manifest |
| baton_worker + worker_manager.exchange | Existing command/event/terminal correlation and declared `/output/output.json` | It is one work execution, not an unspecified bidirectional stream for granting a lease halfway through a run |
| attempts.record_attempt/activate_assignment/request_runtime_start/reconcile_runtime | Actual claim, labels, adapter, start intent and positive stop observation | Activation requires this attempt's own committed offer; copying the parent assignment onto a new ID refuses |
| output.request_freeze/record_frozen_result/frozen_output_of; OciAdapter.seal/collect; intake | Owner-frozen and collected result bytes, exact attempt identity, retained cleanup | A worker-written integration result namespace is not automatically an ordinary frozen/collected result |
| attempts.finalize_quiescent_assignment; intake.abandon_attempt; integration.recovery | Existing explicit lifecycle ending after actual attached runtime and positive exclusion | Do not invent a runtime for old host failures. Existing holds remain operator evidence; conversion is not permitted |
| integration.git_profile.GitIntegrationProfile | Standalone standard-library profile with injected argv runner, explicitly designed to be packaged in a worker image | Current prepare_result calls its effects synchronously from the coordinator and pins local storage paths/inodes |
| tools.integration_bundle / worker.integration_contract input `/2` | Measured immutable content/evidence, bounded blobs, accepted test/path authority | Bundle describes direct accepted source import; it does not deliver a complete original-base/candidate/current-target reconciliation input or a phase result |
| integration.runtime assignment/result `/1` | Exact target/entry/lease/fence binding for authorized apply | Assignment requires a live writable lease. Preparation precedes derived publication/judgments/lease, so it cannot honestly use this assignment unchanged |
| integration.oci_delivery | Node-local no-overlap, no-follow, source identity and writable-target checks | Its closed three mounts include local `/target`; coordinator-local device/inode checks cannot attest a mount on another machine |
| execution.settle_observed / import_authorized_result | Live grant recheck, actual stop proof, target holds, verified settlement and receipt ordering | Derived import currently performs Git/profile effects and verifier calls locally; `_current` deliberately distinguishes direct from reconciled entries |
| scheduler.reconcile_allocations | Release from accepted ending/cleanup/completion facts | Parent integration allocation currently has no validated relation to a separate preparation runtime's ending |

These are observed code contracts, not claims that a remote backend or the proposed
phase orchestration already exists. In particular, `JudgmentExecution` demonstrates
an ordinary derived execution with its own Work/offer/attempt and inherited Job
context, but it explicitly has **no pool allocation**. Copying it without parent
capacity accounting would create hidden integration capacity.

## Proposed execution sequence

### 1. Pin the logical integration and prepare immutable input

Keep the submitted Job and its integration stage. Resolve source eligibility,
accepted review/test authority, original base/candidate and current target snapshot
through their public owners. Commit a preparation intent before dispatch, binding
the parent Job/stage/episode/attempt/allocation and fixed integration assignment,
target ID/revision, source proposal/checkpoint, policy, purpose and input digest.
No candidate code, merge or verification runs during this control-plane act.

Deliver complete bounded Git object/content inputs sufficient to reconstruct the
three pinned snapshots, the configured required-test task/harness, and the accepted
path/test authority as ordinary immutable inputs. Reuse the existing manifest/blob
measurement and Git profile; do not introduce another pack decoder or fetch an
ambient branch from the network. Workload roots are fixed container paths. Its
scratch contains its private reconstructed repositories and prepared candidate.

**Proposed semantic payload:** a versioned `integration preparation` task artifact
declared in the existing input manifest, with purpose, parent references, source
and target content identities, required tests, selected effective limit slot and
payload digests. It is not an extension of the generic transport envelope. The
exact JSON spelling and bounds must be frozen by the contract slice below before
runtime implementation. Do not add nullable lease fields to assignment/1.

### 2. Run a real preparation attempt and collect its result

Use a separate, durably named execution Work/offer/attempt for preparation, with
its own real claim and ordinary managed lifecycle. It is a subordinate execution
charged to the parent's already-reserved integration capacity, never an additional
unaccounted worker. The parent integration Work remains the owner of orchestration
and publication. The child input/assignment identifies the parent; its launch uses
the original Job's resolved limits with the child's actual runtime identities.

This Work/offer mapping is a **new orchestration contract**, proposed for review.
The implementation must prove it through real claim/activation APIs before any
start. It cannot fabricate a stage row or copy a parent's claim. Serial phases
share one principal-capacity reservation; no simultaneous parent and child runtime
may use it. The parent does not activate its final-apply runtime before preparation
has positively ended. Separate physical attempt identities describe distinct
planned work, not an automatic retry of a failed attempt.

Inside Docker, reuse GitIntegrationProfile for preparation and run combined/base/
isolated checks against the pinned inputs and added harness. A deterministic
workload needs no model call or provider credential. Each command gets the owning
Job's configured seconds. Preserve the original per-boundary defaults: relocated
former host verification remains the accepted300s default; existing direct worker
verification remains1800s; one explicit Job override still reaches both. Location
does not silently change an omitted setting's meaning.

The ordinary declared output contains the prepared candidate artifact and a closed
phase report: parent/task/input/attempt identity, source/target/candidate commits
and trees, changed-path/content digests, actual execution environment, command,
harness identity/digest, applied bound and actual observations or tagged no-status
failure with completed prefix/not-run suffix. Failure output contains diagnostics,
not publishable successful evidence. Existing output ceilings apply before any
publication; oversize or partial output is a refusal, not a partial acceptance.

Require correlated terminal output, trusted adapter positive stop evidence and
frozen/collected output before adoption. TimeoutExpired in a child subprocess is
not proof that its container or descendants stopped. If no phase report survives,
retain the manager's runtime interruption/uncertainty; do not fabricate a causal
failure document with command observations that were never collected.

### 3. Adopt prepared content, then obtain real judgments

Split `reconciliation.prepare_result` into durable intent/dispatch and adoption of
the collected prepared artifact. Public owner validation rechecks source authority,
the recorded target snapshot, content/path bindings and each observation against
the configured expectations. Git/content validation may read bytes and compare
identities; it must not re-execute merge, tests or candidate code on the coordinator.
The local-path fields in existing records remain historical; a versioned portable
record must distinguish content locators from node-local storage capabilities.

A failed preparation settles the actual result blocked and retains its phase
execution account. A successful preparation creates the derived proposal and uses
the existing independent judgment pipeline. No preparation result counts as those
receipts. Keep the parent's integration allocation during this serial workflow;
release on failure only through the explicit, validated ending described below.

### 4. Apply authorized content through a managed target execution

After the derived result is authorized, re-resolve its eligibility and acquire the
real target lease for the final-apply attempt. The parent stage's existing manager
attempt is the proposed final-apply identity, so its allocation/offer/assignment
remain real; preparation used a distinct subordinate attempt.

Deliver the immutable authorized candidate, receipts/authority bindings, expected
target revision and exact lease/fence using the existing input/output mechanism.
The receiving target-owner node materializes a fresh delivery and proves its own
canonical target mapping and mount identity. It may be on B while the coordinator
is on A. Never transport a writable target capability by accepting a worker-supplied
absolute pathname or by trusting A's inode values on B.

All candidate application and post-import verification occur in the managed
runtime on the target-owner node. Reuse the existing direct integration mount and
runtime lifecycle where their contracts apply. The existing direct input bundle
and `_current` source-account checks must gain an explicitly versioned derived
candidate case; do not feed a derived proposal through the direct-source validator
and bypass its refusal. Return declared, collected artifact/evidence and the exact
target/entry/lease/attempt/fence account. A verified private replica is not proof
that the canonical target was changed.

**Proposed control-plane boundary for review:** reference compare-and-swap and
Authority/queue receipt settlement remain trusted target/integration-owner acts
after the candidate-executing runtime is positively stopped and the live grant,
old revision, authorized candidate and collected verification are rechecked. They
must be reachable through the target-owner capability on B, not a hidden local
path on A. This is bookkeeping/authorized publication, not coordinator execution
of candidate code. Independent design review must affirm this boundary against
the owner's “integration execution” ruling before implementation. If the target
owner cannot provide this existing semantic operation across the node boundary,
record the exact adapter gap; do not invent transport or remote success receipts.

### 5. End failures and settle capacity through real lifecycle evidence

A preparation failure and an apply failure have different target effects. The
former has no fabricated entry/lease; the latter retains the existing blocked
target/held-entry account before reference advance or integrated receipt.

Expose the ordinary explicit finalization/abandonment actions for the actual
managed attempt. Preserve exact claimed Work, offer, phase, parent, allocation,
runtime and generation bindings. Only the trusted runtime adapter supplies stop/
destruction evidence. The phase owner records the ending idempotently; the parent
adapter presents a validated failed-phase ending, **not successful completion**, to
the scheduler. A narrow scheduler extension releases only the matching parent's
logical capacity after every execution using it is proved excluded and the
explicit ending is committed. Cleanup retains its separate owner/status.

Ending an old execution does not retry it, clear a failure record, reopen a target,
approve a new result or resolve a merge conflict. In particular, existing
abandon_held_lease leaves target blocked and entry held. Subsequent C execution can
prove shared Job/result/harness isolation after B's causal failure is explicitly
ended while the target remains usable. For a post-import target hold, demonstrate
safe refusal until a separately authorized repair/new-result action exists; the
prerequisite does not manufacture that authority. Positive runtime recovery and
new-result authorization remain separately assessed acceptance questions.

## Bounded proposed path and authority plan

All paths below are relative to the repository. They are a **requested candidate
boundary for independent review**, not edits authorized by the architecture ruling.
The first implementation slice must settle the open contracts listed below; no
implementation is handed off by this planning turn.

| Slice | Proposed product paths | Bounded purpose |
| --- | --- | --- |
| Contract and phase custody | new `v12/python/src/baton_v12/integration/managed_execution.py`; `v12/python/src/baton_v12/integration/reconciliation.py` | Typed parent/phase/execution relationship; intent and collected artifact adoption using existing operation journal where possible; portable content identity |
| Delivery and worker | `v12/python/tools/integration_bundle.py`, `v12/python/tools/integration_worker.py`; new `v12/worker/reconciliation_task.py`, new `v12/worker/reconciliation_entry.py`, new `v12/worker/Dockerfile.reconciliation` | Reuse ordinary input/output framing and launch readers; bounded semantic task/report; deterministic Git/profile workload and image packaging |
| Derived final apply | `v12/python/src/baton_v12/integration/execution.py`, `v12/python/src/baton_v12/integration/runtime.py`, `v12/python/src/baton_v12/integration/oci_delivery.py`, `v12/worker/integration_contract.py`, `v12/worker/integration_workload.py`, `v12/worker/integration_entry.py` | Versioned derived candidate support, collected evidence, live grant and positive-stop settlement; node-local target capability validation |
| Composition and capacity | `v12/python/tools/stage_execution.py`, `v12/python/src/baton_v12/job_manager/delegation.py`, `v12/python/src/baton_v12/job_manager/scheduler.py` | Replace managed-path local execution; real subordinate preparation claim/lifecycle charged to parent; validated failed-phase ending and exact capacity release |
| Placement capability | new `v12/python/tools/integration_placement.py` | Compose existing input/output delivery and runtime/target-owner capabilities on the executor node; no network protocol or direct store access from worker |
| Documentation | `v12/python/DEPLOYMENT.md` | Managed lifecycle, defaults, relocation boundaries, phase endings, retained holds and historical host-path limitations |

Reuse without planned mutation: generic launch/3, exchange/1, manifests, workspaces,
ordinary baton_worker, source boundary, OCI lifecycle, attempts/output/intake,
GitIntegrationProfile and queue target-repair policy. Packaging the standalone
Git profile must bind its actual bytes in the image; do not fork its algorithm.

**Potential additional paths are NOT silently included:** integration schema.py /
store.py if portable phase custody cannot fit existing signed operations/result
columns without confusing old path/inode identity; worker_manager APIs if existing
public lifecycle cannot own the subordinate execution; generic input/output schema
or OCI engine transport if the relocation proof exposes a real gap. Identify the
failing public contract, propose the exact extension and return for reviewed scope
before changing one of these. No module-wide “whatever is needed” permission.

### Test ownership and compatibility

Propose new tests only initially: `v12/python/tests/integration/test_managed_execution.py`,
`v12/python/tests/tools/test_managed_integration.py`,
`v12/python/tests/manager/test_reconciliation_worker.py`, and
`v12/python/tests/job_manager/test_managed_integration_capacity.py`. Own all new
fixture helpers there; no borrowed fixture edits merely for convenience.

Schedule bounded updates to this Work's new
`v12/python/tests/tools/test_execution_limits.py`: retain old host-boundary cases as
accurately labelled historical/legacy coverage, add managed replacement cases and
replace current managed-path expectations only when that path is implemented.
Do not delete failure/reopen/cleanup acceptance to obtain passing tests.

Existing `tests/tools/test_integration_bundle.py`, `tests/tools/test_integration_worker.py`,
`tests/manager/test_integration_worker.py`, `tests/manager/test_oci_integration.py`,
`tests/integration/test_runtime.py` and `tests/integration/test_execution.py` need
additive version/conformance cases if their affected owners change. Preserve their
legacy assertions. Any necessary existing expectation changes must be enumerated
by method with before/after accepted behavior in the implementation plan and the
independent review. W71830 standing test authority has ended; do not reuse it.

Keep old wire versions readable and fail closed on unsupported new task/report
versions. No in-flight host record is reclassified as a managed execution, no
automatic replay onto Docker, and no old timeout acquires invented stop evidence.
The first rollout policy should require new execution identity for the selected
managed mode while retaining read-only historical observations. Do not introduce
a permanent host fallback that bypasses the selected architecture.

## Focused verification and completion gates

1. Contract/relocation proof: construct a real ordinary input/assignment/launch,
   copy only declared immutable bytes to disjoint B roots, make A's roots
   unavailable to the worker, execute the actual deterministic workload entry,
   then seal/collect/adopt through normal owners. Check host paths/inodes never
   become content identity. Label a disjoint-root replay as simulated placement,
   not a deployed farm or certified Docker run.
2. Real owner lifecycle with fake/replay provider and engine: preparation, source
   eligibility, three causal phases, distinct B77/C61 Jobs/results/harnesses,
   independent judgments, authorized apply, post-import evidence and target CAS.
   Instrument the coordinator and fail the test if it runs candidate verification
   or performs the reconciliation execution locally. A hosted Docker coordinator
   with local host commands must fail this check.
3. Timeout/start failure at each phase, unavailable output, malformed/foreign
   manifest, wrong Job/attempt/phase/limit/harness, stale lease, changed target,
   interrupted transfer, conflicting duplicate output and false stop evidence.
   Preserve completed prefix/not-run suffix without fabricated exit status.
4. Ordinary polls and genuine reopen adopt recorded state with zero duplicate
   starts/execution/materialization. Explicit finalization/abandonment uses actual
   runtime identity and positive stop evidence; uncertainty retains the hold.
   Wrong-parent/old-episode ending cannot release another allocation. After B's
   explicit causal-failure ending, C runs its own task/bound without reusing B's
   outcome, while B's full custody stays unchanged.
5. Focused managed Docker lifecycle check when authorized: deterministic workload,
   no live model, actual timeout/stop/descendant exclusion and output collection.
   Fake engine evidence cannot certify real process termination. This tests the
   runtime boundary specifically, not provider behavior. Use an available approved
   image; no installation/build/pull or new execution authority is presumed.
6. Compatibility: old direct and reconciled records remain readable; legacy wire
   versions/signatures unchanged, W156162 limits retain defaults/overrides, target
   hold and explicit repair separation retained. Final exact base/path/candidate
   hashes, all changed existing tests, W71879 overlap and independent proposal
   provenance precede any baton.merge import.

No live-provider question, cumulative budget feature, role pool, target repair,
implicit retry, exactly-once guarantee or farm deployment is part of this plan.
Preserve author246 runs2530.5844189850177s plus four disclosed unknown activities and
reviewer147.72804738899322s; charge any new measured work cumulatively. No numeric
cap or budget reset is proposed. Reuse accepted evidence and run focused slices;
do not repeat the old single-integrator failure loop expecting new behavior.

## Questions the independent design review must resolve

The proposal is concrete enough for **design review**, not implementation start:

- Confirm separate preparation Work/offer/attempt charged to the parent allocation,
  with parent stage attempt reserved for apply, against real activation and
  principal-capacity rules. Do not approve reuse based only on JudgmentExecution.
- Freeze the versioned semantic payload/report and portable custody representation;
  decide whether the current journal/result schema suffices. Recheck declared
  object transport bounds and complete snapshot reconstruction.
- Confirm the target-owner publication boundary on B and the collected-result /
  live-grant / positive-stop ordering. Identify any missing target-owner capability
  without substituting a worker report or designing a second transport.
- Confirm exact source path set and existing-test mutations for the first slice.
  Any added schema, generic protocol or lifecycle API needs its own explicit
  justification and reviewed authority before implementation.

An independent participant should review this design and return findings to
baton.codex. After revision, the owner approves the bounded implementation scope.
The pending formal owner obligation160528 is not impersonated or self-resolved;
M161029/FINDING carry the confirmed architecture direction in the meantime.

## 2026-09-13T14:00:22Z — formal owner response confirmed after handoff

Canonical detail after pass161101 shows obligation160528 responded at161051.
The full owner response, read through T156162, confirms the same managed Docker,
existing input/output and relocatable execution architecture already pinned at
13:47:40Z, preserving recovery/isolation acceptance and independently reviewed
bounded scope. This supersedes statements in the planning packet/handoff that
160528 remained pending; no architecture or implementation authority changed.
Baton.claude holds claim161103 for independent design review only. Coordination
message161104 records the same clarification. No owner-response wait remains.
