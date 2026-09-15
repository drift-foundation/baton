# Managed integration: explicit capacity and portable custody

**Owning prerequisite is now W161230**, per owner M161222/M161232, bound at
`baton:work/records/2026/09/finding-v12-managed-integration-execution/`.
This design was prepared under the active W156162 claim and remains here as
durable history; W161230 owns its independent review and accepted implementation.
W156162 consumes the result. This supersedes any prior implication that managed
integration implementation belongs inside W156162.

Owner completion criterion M161268: final focused verification uses project-pinned
dependencies and records actual versions. Existing jsonschema mismatch remains
qualified historical evidence; resolve it for final selected checks. No separate
environment project without a concrete setup problem; no live/farm run implied.

2026-09-13T14:21:37Z — baton.codex, claim161207. **Revised proposal for
independent design review only. No implementation authority or self-approval.**
Responds to DESIGN-REVIEW-161103-2026-09-13.md / M161127. Owner architecture
remains FINDING2026-09-13T13:47:40Z and formal response161051.

This version supersedes v1's unspecified subordinate-capacity representation,
optional-later portable storage scope and unresolved target-owner boundary.
V1's other isolation, ordinary input/output, per-Job limits, source authorization,
positive-stop, target-hold and no-implicit-retry requirements remain. The old file
and independent review remain historical evidence. The path plan below replaces
v1's proposed path plan; it is an explicit proposal, not permission to edit it.

## Decisions proposed in response to independent review

1. Choose the explicit scheduler relationship, retaining the parent integration
   stage attempt for final apply. Use a NEW membership relation keyed by execution
   attempt and referencing the existing root allocation. Do not put a second
   stage allocation into the current unique worker/principal indexes, invent a
   child stage, weaken those indexes, or give an unaccounted child a runtime.
2. Add portable result storage and its version-aware adoption/readers in the first
   slice. Existing `workspace(path,device,inode)` is still consumed by
   `StageDeployment.judge_result`; it is not already a portable reference.
3. Accept the independent review's target-owner boundary: trusted publication of
   authorized bytes and reference CAS after runtime exclusion are owner acts.
   Add the explicit node-local target capability entrypoint to the first contract
   slice. An actual remote transport/backend is not presumed to exist.
4. Keep former host-boundary tests as labelled legacy coverage and add managed
   equivalents preserving every meaningful assertion. A coordinator execution
   trap must fail if managed-path tests/merge execution escape onto the host.

## A. One capacity reservation, with an enforced serial execution membership

**Observed current constraints:** Job schema5 `stage_allocations` has foreign keys
to actual `(stage_id,episode)` and the configured worker tuple, plus unique live
worker/principal/stage-episode indexes. `_lane` has only implementation/review;
integration is already an eligible kind in the implementation lane. `_move` is
the common release boundary, including episode-ending and cleanup shortcuts.
Adding a child row and filtering it in `reserve` would still fail the unique
indexes and cannot be the implementation.

**Proposed representation:** two additive JobStore relations, created in its
next reviewed schema migration (5→6 if the baseline is unchanged). Additive tables
fit `JobStore._schema_three_shape`'s current derivation; ALTERing old allocations
does not. Names below define the intended public concepts, not preexisting APIs.

| Relation | Fixed identity and mutable state | Required constraints |
| --- | --- | --- |
| `integration_capacity_roots` | FK `root_assignment_id` to actual stage allocation; orchestration ID and immutable Job/stage/episode/Authority/worker/pool-generation binding; lifecycle `open`, `ending`, `ended` and journal references | One root per allocation; only an integration-kind episode; no new pool lane or extra principal; released allocation cannot register |
| `integration_capacity_members` | PK execution attempt; FK root; fixed role `prepare` or `apply`, execution Work/offer/fixed assignment, task/input/profile digest, participant; state `planned`, `admitted`, `recovery-required`, `ended`; start/ending evidence locators | Unique root+phase for this two-phase plan; at most ONE `admitted` or `recovery-required` member per root; child cannot attach to multiple roots; no recursion; apply member names the parent's actual attempt |

Canonical principal, selected worker and pool generation come from the root's
owned allocation, not the child payload. The actual phase claim participant must
match the configured integration actor. Pool generation and Authority assignment
generation are different axes and never compared numerically. Preparation uses
that actor's real separate Work/offer/attempt and phase profile, bound by the root
orchestration's declared preparation task. It is NOT a new schedulable stage kind
fed through `_lane`, nor a way to select a different integration principal.

Planned membership binds the real Work and intended offer/participant but does
not invent the future claim generation. The claimed assignment is fixed once,
from the actual successful claim, before admission; its absence is legal only in
the planned state. The separate preparation-Work creation intent is persisted in
the orchestration journal first; create/replay yields its real ID before membership
registration. An incomplete registration cannot admit either runtime. A phase's
profile is the plan's explicitly certified preparation/apply profile, not an
assumption that the two runtime profile digests are identical.

Proposed public owner operations, all journalled and identity-collision checked:

- `register_integration_capacity`: validate the root and fixed plan; create both
  planned memberships before any child offer/setup/start. The prepare Work is
  actually created/claimed through Authority owners. Persist its creation intent
  before that separate act; a crash retains pending custody, not another Work.
- `admit_integration_execution`: inside one JobStore transaction require root
  open+reserved, matching current plan/claim/input/participant, and no active
  member. Preparation may enter first; apply requires collected successful
  preparation, its closed execution membership, and the actual authorized
  derived candidate/grant. Commit `admitted` before any runtime start.
- `end_integration_execution`: consume owner-validated fixed-attempt ending
  evidence; exact repeat replays, changed evidence collides. Success/failure is
  retained separately from exclusion. Stop uncertainty sets recovery-required;
  it never frees the member. Frozen output alone cannot end membership.
- `begin_integration_ending`: atomically close admission (`open→ending`) and
  cancel remaining planned phases by the explicit failure-ending decision.
  It cannot cancel an admitted member on the strength of a missing runtime ID.
- `integration_capacity_of`: read root plus EVERY membership and provenance so
  capacity is visible in ordinary owner observation, including between phases.

**Enforcement points, not just reporting:**

1. The root allocation remains live in existing `reserve` occupancy throughout
   preparation, judgment waiting and apply. Thus other Jobs see one occupied
   configured integrator without any change to worker/principal exclusion.
2. New preparation orchestration and managed `IntegrationRuntimePort` apply both
   require their exact admitted membership BEFORE reaching the ordinary runtime
   start API. Parent apply is registered too; it cannot bypass the check because
   it already owns the original allocation. Worker-reported parent IDs confer
   nothing. No independent integration child launch path is exposed.
3. Guard **every** root release in `_move`, including calls from ended episode,
   cleanup-complete/retained, validated integration-completed and pre-runtime
   failure branches. For registered roots, require root ending/ended and all
   memberships ended under the validated completion/failure account. A direct
   `release(root, reason)` cannot bypass this. Old unregistered allocations keep
   existing behavior. A success path closes admission before committing its final
   root ending; a late prepare claim cannot appear after release.
4. Membership state is held across the separate JobStore, ControlStore, Authority
   and adapter transactions. There is NO claimed cross-store atomic commit.
   Intent is durable before each external act; failed/unknown adoption leaves
   capacity held. Exact resume reads the recorded operation and reconciles the
   ordinary attempt; it never mints another execution identity automatically.
5. Never end an admitted member because polling sees no attached runtime. A start
   intent might precede the delayed adapter act. Quiescence/destruction and frozen
   collection must refer to the actual lifecycle, and no-start ending needs the
   stronger cancellation proof below. A timeout does not expire membership.

**Newly revalidated no-start ending:** a preparation failure can leave the parent
apply attempt activated but never launched. `finalize_quiescent_assignment`
explicitly refuses that shape; it requires attached runtime and terminal worker
disposition. Do not invent either. Existing `request_cancellation` journals the
decision and fences the actual assignment; `_order_quiescence` reports
`ordered=false` when no runtime is attached. That return is not stop proof.

Propose one narrow public reader in `worker_manager/attempts.py`,
`unstarted_cancellation_of(store, port, attempt_id)`, with a closed document in
`worker_manager/documents.py`. It derives and validates the exact fixed assignment,
committed cancellation intent and Authority fence through existing `assignment_of`
port/operation readers; requires no attached runtime, no committed runtime-start
intent and a cancelled execution axis that prohibits a subsequent start. The
start transaction's axis transition and cancellation must be tested in BOTH
orders. It returns **fenced-before-start**, with `runtime_id` absent, never
`quiescent` or `destroyed`. A raced/pending start refuses this reader and uses
normal adapter reconciliation/destruction instead. This adds a reader, not a
generic cancellation rewrite or a new permission to discharge Authority gates.

The integration owner may consume that proof ONLY for the matching unstarted
member after admission is closed. Its counterpart for an execution that started
is existing explicit finalization/abandonment plus actual exclusion evidence.
Any Authority gate remaining after fencing stays visible; scheduler capacity
release is not a claim that a gate, target hold or failed Work became successful.
If the independent review cannot affirm the exact never-started proof from these
owners, this gate remains refused; no new finalization semantics are implied.

## B. Portable task, result and target-owner contracts in slice one

Use ordinary immutable manifest/blob inputs, assignment/launch identity and
declared frozen output. The generic transport versions are unchanged. Introduce
two closed, versioned SEMANTIC artifacts inside them, with explicit purpose
variants rather than nullable preparation leases:

| Artifact | Required bound contents |
| --- | --- |
| `baton.integration.task/1`, preparation variant | Authority/Job/stage/episode/root allocation; member/Work/offer/actual attempt/fixed assignment; source proposal/checkpoint/result; base/candidate/target commit+tree and measured object artifact locators; expected target revision; exact task/harness/accepted path and test authority; original Job limits digest, selected default slot, effective positive seconds; profile/input digests |
| Same task, apply variant | Common execution binding plus derived result/content, independent receipt identities, canonical target, actual entry/lease/fence and admitted old revision. No direct-source validator relaxation; this is a separately admitted case |
| `baton.integration.phase-report/1` | Exact task/input/execution binding; measured output candidate/content/path-set identifiers; execution environment; command/harness/commit/tree and applied bound per actual observation; explicit outcome variant and original causal phase order |

Phase reports distinguish (a) real integer exit observations, (b) collected tagged
no-status start/timeout failure with completed prefix and not-run suffix, and
(c) **NO COLLECTED REPORT**, which is a manager collection/lifecycle state and
cannot be represented as worker observations. No synthetic exit code, worker
stop attestation or unmeasured suffix. Keep combined/base/isolated order and
the combined harness carried into the original base as current `_CausalObserver`
does. A base failing for the genuine missing fix remains positive causal evidence;
do not replace it with an arbitrary failure to obtain a result.

Per-invocation limits retain provider3600, ordinary verification900, direct
integration verification1800 and relocated former-host verification300 when
omitted. One explicit Job verification override reaches every applicable boundary.
The report's bound is compared to the original Job's configured expectation;
the child's own manifest is compared to its actual execution, not the original
producer manifest. Transport/output ceilings retain their existing bounds.

**Storage choice:** add `managed_integration_results` to the target-global
IntegrationStore, with common immutable source/target/result identities and
closed portable task, collected-custody and phase-report references. Do not put
dummy paths/inodes into old `integration_results.workspace`/`target_source`, or
reinterpret those closed legacy objects as portable JSON. Managed fields hold
content-addressed artifacts (digest, length, declared logical locator), never
coordinator absolute paths, inodes or Docker IDs. Runtime/collection evidence has
its own owner reference and is validated separately from the worker report.

The portable row uses the existing result state semantics and preserves rejected/
blocked history and publication-before-independent-authorization. The managed
reader is a distinct admitted representation; old result readers still expose
their old shape. Every new and legacy result creation in the upgraded writer
checks `(canonical_target_id, source_proposal_id, target_revision)` against BOTH
tables inside the same target-global write transaction, and refuses conflicting
IDs/content. Per-table uniqueness alone would allow two results for one key.
Reads also refuse a double representation. No new target lock or per-Authority
integration store is introduced.

**Explicit storage compatibility scope:** integration store currently has no
migration (`MIGRATIONS={}`), unlike JobStore. Propose a narrowly bounded explicit
5→6 additive migration for this table, preserving all existing target/lease/entry/
result/operation bytes. Read-only open must recognize old5 and new6 without
upgrading; unknown versions/shapes still refuse. Writable upgrade is an explicit
owner operation after schema5 validation, not an automatic replay or fresh empty
store that discards a live target lock. Do not copy a still-active target into a
second writable store. Independent review must accept the shape/version and
unchanged-history tests before this additional store scope reaches implementation.

`StageDeployment.judge_result` must obtain the immutable candidate from the
collected portable artifact through a trusted materializer at the execution node;
it cannot clone `held['workspace']['path']` from machine A in the managed case.
Likewise post-import verification gets its content and harness from its admitted
apply task. A worker does not choose arbitrary host source or target paths.

**Target-owner entrypoint:** propose
`publish_collected_integration(canonical_target, entry, lease, fence,
admitted_old_revision, authorized_candidate, collected_phase_reference)` on the
trusted placement owner. It resolves the configured target/ref and collected
source locally on B, validates current Authority/queue grant through trusted
owner capabilities immediately before mutation, proves exact stopped execution,
then invokes existing publication/CAS and settlement rules. Worker output carries
no Authority session, target capability or grant refresh authority. A stale grant,
changed target, unavailable reader or missing local artifact refuses before write.
Do not substitute the current ref for admitted_old_revision.

The semantic request and ordinary artifacts travel through existing input/output
delivery; trusted runtime/target capabilities are composed at B. The first slice
defines/tests this local interface; subsequent disjoint-root replay composes it
with actual delivery and collection. A real remote backend still needs its existing
trusted authority/runtime access; inability to supply that access is an explicit
deployment gap, not permission for a new RPC, copied credentials, cached live-grant
fiction or reported farm success. Target CAS remains after positive stop and
collected verification. Target repair/new result is a separate authorized action.

## C. Finite proposed source and test scope

All paths here are beneath `v12/python/` unless beginning `v12/worker/`.
Each slice has a reviewable finish condition; none starts during this design turn.

| Slice | Exact proposed paths | Finish condition |
| --- | --- | --- |
| 1 — capacity and portable owner contracts | `src/baton_v12/job_manager/schema.py`, `src/baton_v12/job_manager/store.py`, `src/baton_v12/job_manager/scheduler.py`; NEW `src/baton_v12/job_manager/integration_capacity.py`; `src/baton_v12/worker_manager/attempts.py`, `src/baton_v12/worker_manager/documents.py`; `src/baton_v12/integration/schema.py`, `src/baton_v12/integration/store.py`, `src/baton_v12/integration/reconciliation.py`; NEW `src/baton_v12/integration/managed_execution.py`; NEW `tools/integration_placement.py` | Real root/membership transactions and all-release guard; bounded no-start reader; closed semantic task/report/custody; versioned portable rows with cross-representation uniqueness and explicit/read-only compatibility; target-owner interface. Focused owner tests; no claim of deployed managed execution |
| 2 — preparation delivery and ordinary lifecycle | `tools/integration_bundle.py`, `tools/integration_worker.py`, `tools/stage_execution.py`; `src/baton_v12/job_manager/delegation.py`; NEW `v12/worker/reconciliation_task.py`, `v12/worker/reconciliation_entry.py`, `v12/worker/Dockerfile.reconciliation`; slice1 managed_execution/integration_capacity modules | Actual separate Work/offer/claim, admitted membership and Docker attempt at normal engine seam; ordinary output freeze/collect; portable adoption and derived judgment input; coordinator execution trap; actual fixed Job limits |
| 3 — derived apply and explicit failure settlement | `src/baton_v12/integration/execution.py`, `src/baton_v12/integration/runtime.py`, `src/baton_v12/integration/oci_delivery.py`; `v12/worker/integration_contract.py`, `v12/worker/integration_workload.py`, `v12/worker/integration_entry.py`; slice1 placement/managed_execution and slice2 composition/delegation | Separately admitted derived apply under parent membership; positive stop, exact live grant and target CAS; all-member release after explicit failure ending; real B failure/C isolation, preserved target holds; bounded disjoint-root placement replay |
| Documentation alongside affected slice | `DEPLOYMENT.md` | Actual defaults, lifecycle, compatibility and placement limits; legacy evidence never advertised as managed execution |

These additions are justified by concrete source gaps: Job allocation foreign
keys/unique indexes, strict path-bearing integration result columns, absent
integration migration, missing target capability signature and attached-runtime
finalization precondition. Generic launch/exchange/manifests/OCI lifecycle,
source-boundary algorithms, GitIntegrationProfile and target-repair policy remain
reuse-only. No generic attempt start/cancel transition rewrite is proposed; return
the exact new scope if the no-start proof requires one. No extra image build/pull
authority is presumed from a Dockerfile path.

Initial new test files: `tests/job_manager/test_managed_integration_capacity.py`,
`tests/integration/test_managed_execution.py`, `tests/tools/test_managed_integration.py`,
`tests/manager/test_reconciliation_worker.py`. New helpers live there.
Existing neighbor tests get additive cases only within the exact owner boundary;
no change to old assertions is needed for slice1 by this proposal.

For slice2/3, bounded updates in this Work's new `tests/tools/test_execution_limits.py`
retain the following as explicit legacy tests, adding managed equivalents:

- `_watching`, `test_the_composed_causal_owner_runs_under_the_jobs_ceiling`,
  `test_a_causal_overrun_is_retained_and_blocks_the_result`,
  `test_the_post_import_verification_uses_the_jobs_ceiling`,
  `test_a_post_import_overrun_runs_once_and_defers`,
  `test_a_post_import_start_failure_is_the_same_shape`;
- `test_a_base_observation_that_never_finishes`,
  `test_a_base_observation_that_never_starts`,
  `test_an_isolated_observation_that_never_finishes`,
  `test_an_isolated_observation_that_never_starts`;
- `test_the_retention_key_distinguishes_its_operands_at_the_unit`,
  `test_the_retained_failure_is_keyed_by_the_work_it_is_about`;
- `test_a_scratch_that_survives_disposal_is_the_deployments_to_release`,
  `test_a_scratch_that_survives_the_release_too_is_reported`,
  `test_a_post_import_scratch_is_released_by_the_same_close`,
  `test_a_post_import_start_failures_scratch_is_released_too`,
  `test_the_failed_scratch_is_disposed_of`.

Preserve exact old recovery-refusal/capacity cases as historical owner behavior;
managed replacements must separately show positive recovery/isolation without
erasing the old refusal. Each replacement compares command, effective seconds,
Job/result/content, actual harness digest, prefix/suffix, custody and explicit
ending. Failed managed execution cannot pass merely because no host command ran.
The existing `_watching` seam can supply the negative host trap, but the trap's
reach must include relocation/materialization/verification callbacks too.
No existing-test authority is inferred from the expired W71830 exception.

## D. Focused proof obligations before implementation approval

Independent reviewer checks this revision, especially:

1. Root/member FK and uniqueness, real child claim/profile identity, one admitted
   member, parent apply guard, all `_move` release paths, and direct/legacy behavior.
   Race two admissions; race ending against admission; reject wrong root/episode/
   worker/principal/generation/task/claim; exact replay vs changed operands.
2. No-start cancellation proof against the actual Authority fence and ControlStore
   start-intent/axis rules. Both race orders: if start committed, hold/reconcile;
   if cancellation committed first, no adapter call. Do not generalize no runtime
   attached into proof no runtime exists. Release no other root/member.
3. Portable schema5/6 compatibility and one-result key across legacy/new tables;
   reject path/inode substitution, conflicting artifact, foreign phase/Job/limits,
   false report, unavailable report and changed fixed prefix. Existing history,
   live lease exclusion and target-global authority survive upgrade unchanged.
4. Explicit target-owner signature and grant/old-revision/collected-result checks,
   with no coordinator candidate execution, worker Authority capability or ad hoc
   transport. Later placement replay uses disjoint roots and only declared input/
   output; it is simulated placement, not a deployed farm.
5. Preservation of positive timeout/termination/recovery/isolation acceptance and
   every enumerated legacy/managed expectation. Exact first-slice paths above are
   proposed for approval after independent design acceptance, not blanket authority
   to edit all later slices or resolve unrelated failures.

No runtime experiment was needed for this revision. research-161207.json pins
30 source files and all29 unchanged candidate paths; it records0.0027992710020043887s
inventory and reviewer cumulative147.7342205499972s. Author246runs
2530.5844189850177s plus four disclosed unknown activities unchanged. No numeric
cap, reset, W103525 transfer, live provider or full-feature/import sign-off.
W103525's completed consolidation161193/161201 recommends this architecture work
and names later trace revalidation; it grants no source authority here. Return
the revised design to an independent participant before owner implementation scope.
