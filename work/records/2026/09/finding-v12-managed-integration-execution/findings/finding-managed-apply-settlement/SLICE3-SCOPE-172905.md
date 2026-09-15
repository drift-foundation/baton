# Managed apply and settlement: concrete selection proposal

2026-09-14T23:08:35Z — baton.codex, reviewer claim172905, W170385.
**Proposed for owner selection; no implementation or independent acceptance.**

## Baseline and decision

W170382 closed satisfying at172901. Its candidate-172672.json has SHA256
b3248a8da92f2b39339144ba07ba810be41d72627a39250f707f191478e63ba7;
review-2026-09-14T22-42-50Z.md independently accepted the reduced preparation
scope. Those files are in the sibling finding-managed-preparation-recovery
record. research-172905.json pins the current source/test baseline and checks
all17 accepted preparation paths against that manifest. This is an inventory,
not another runtime acceptance result.

Select the fifteen source paths and thirteen test paths below for one serial
implementation of the existing group3 outcome. Recommend baton.tuner for
continuity, only if explicitly assigned; otherwise the selected implementer is
baton.claude. Return the complete immutable candidate to baton.feat for independent
baton.codex review. The reviewer does not implement or self-accept this proposal.
The owner may amend this packet before selection. No additional child or generic
recovery project is proposed.

This packet follows parent SPLIT-SETUP-2026-09-14.md and
DESIGN-RECONSIDERATION-166444.md. It supersedes the original v2 design's tentative
slice3 path list **only if selected**, not its invariants. The original design is
baton:work/records/2026/09/finding-v12-per-job-budgets/MANAGED-INTEGRATION-DESIGN-v2-2026-09-13.md.
The accepted first-slice contract review is parent review-2026-09-14T01-09-21Z.md.

## Observed seams and proposed composition

1. **Observed:** integration_worker.ManagedPreparation.admit always defers the
   parent, even after PreparationRuntime.poll adopts the candidate. The child
   must release its actual Authority claim before the same actor can claim the
   parent. **Proposed:** resume the existing parent offer/claim after proved child
   ending and retained custody; keep the existing root allocation throughout.
   Do not create another stage, worker, principal or execution attempt. Reopened
   composition resolves the retained preparation rather than its process cache.

2. **Observed:** reconciliation.adopt_prepared_candidate returns the real
   candidate artifact, report artifact, request/harness digests, collected
   result/manifest/custody, source and combined/base/isolated states. It creates
   a portable result and attaches preparation, but publishes no derived proposal.
   Its _ended_preparation currently requires apply still planned. Later resume
   therefore needs a retained-result reader appropriate after apply admission,
   rather than repeatedly invoking initial adoption. managed_result_of proves
   creation and attachments and currently refuses unjournalled state changes.
   **Proposed:** journal managed prepared/causal/publication/authorization/import
   transitions in the existing IntegrationStore and prove them in its reader.
   Use the existing schema6 columns and one-result key across both representations;
   create neither a parallel legacy result nor fake workspace/path/inode fields.
   Retain failed causal evidence as blocked; never turn it into an approved result.

3. **Observed:** StageDeployment.judgment_subject and judge_result call the
   legacy result_of and clone workspace.path. publish_result and
   record_result_evidence also consume that representation. **Proposed:** add
   explicitly managed variants using the collected candidate and measured causal
   report. Publish once through the integration actor's actual parent assignment;
   freeze the whole derived custody basis, accepted Job input/policy, source and
   target identities. Materialize a verified immutable judgment snapshot from
   declared retained content. Reuse JudgmentExecution and real scoped Authority
   publication/verification/review/approval owners, with deterministic providers
   in focused tests. Successful causal execution is evidence, never a verdict.
   Three independent current-policy receipts must name the exact derived proposal
   and result. Restart reuses the same dispatch/proposal/receipt identities.

4. **Observed:** capacity.admit_integration_execution already requires the
   ended successful preparation, fixed parent assignment, live grant and trusted
   authorization. Its approved content operand is the preparation collection
   manifest digest. placement._authorized later receives the apply collection
   manifest digest. Those are different collections, not necessarily equal.
   **Proposed:** retain an explicit provenance mapping from preparation collection
   to its candidate artifact/commit/tree, derived result and approved receipts,
   then from the apply collection to the very same approved candidate. Keep
   artifact, collection, candidate-content and result digests distinct. An apply
   reporting success must not authorize different bytes by giving a digest the
   same field name. Bind parent preparation attempt/collection in managed_task.

5. **Observed:** IntegrationRuntimePort.run currently composes the direct source
   bundle and writable /target mount. integration_entry reads that direct
   assignment and invokes integration_workload.integrate. **Proposed:** a
   separately admitted managed apply purpose through the normal immutable input,
   launch, runtime, frozen output, collection and cleanup owners. It executes the
   already approved candidate and pinned harness in private storage; it does not
   grant the worker Authority sessions or canonical target write access. Use the
   original parent attempt and planned workload identity, and admit capacity
   before request_runtime_start. Do not reuse a preparation task/input digest as
   an apply workload digest. Preserve direct source admission unchanged.
   The relocated former-host post-import verification retains its host_verification
   default300 and the original Job's explicit override; direct verification1800
   and ordinary verification900 retain their existing meanings. No coordinator
   merge or harness execution is permitted on this managed branch.

6. **Observed:** LocalTargetPlacement/publish_collected_integration already
   compose materializer.materialize, execution_owner.exclusion_of,
   authorization.authorized and target_owner.apply/recover. They prove collected
   success, exact runtime/start/assignment exclusion, actual entry ownership,
   current grant immediately before the effect, admitted-old-revision CAS, and
   settlement. The target owner in test_managed_integration is explicitly fake:
   its in-memory receipt map is not a production receipt producer.
   **Proposed:** wire actual node-local owners to that interface. The materializer
   verifies frozen artifact bytes and maps the approved revision into the locally
   configured target object store. The execution owner uses the adapter that
   executed this attempt plus ControlStore's durable fixed runtime/start records;
   a stopped worker report, elapsed timeout or foreign adapter is insufficient.
   The authorization owner proves current independent receipts and the mapping
   in item4. Worker content carries none of these capabilities.

7. **Proposed concrete target effect:** implement the local Git owner in
   integration_placement.py with a narrow profile operation in git_profile.py.
   Prepare an immutable Git receipt object containing the exact publication
   identity and operands, configured target/ref, derived result and collection
   mapping, entry/lease/fence and fixed execution binding. Atomically compare and
   advance the configured target ref AND create its publication receipt ref in
   one Git reference transaction. The receipt namespace is owner-local, derived
   from the publication identity, and unavailable to the worker. A receipt is
   not a sidecar written after an ordinary advance. The owner revalidates the
   bound grant at its actual mutation boundary after preparatory object work;
   CAS always uses the admitted old revision. Existing profile.advance behavior
   for direct/legacy callers stays intact.

   Recovery validates the exact receipt object and its operand binding; it never
   infers ownership from HEAD or a reference now equal to the desired revision.
   A retained receipt proves an applied effect even after coordinator process
   loss. The placement still checks current target content before settlement.
   Receipt absence alone is **unknown**, not proof that a delayed operation cannot
   commit; retain a visible hold without another CAS. A fresh transaction that
   positively failed can report not-applied only with the owner's own complete
   no-effect account. No automatic unknown-effect repair, ref rollback, receipt
   deletion, second target lock service or remote backend is selected. This
   mechanism must be tested using real disposable Git repositories; atomicity
   and receipt recovery are proposed behavior, not yet measured here.

8. **Observed:** Integration.account selects only legacy results; its finish
   requires the owned committed integration and lease release. Delegation's
   _integration_completion explicitly rejects a result_id paired with an actual
   runtime, because its reconciled variant means legacy model-free execution.
   **Proposed:** add a closed, explicitly identified managed completion variant
   carrying managed result, actual parent runtime and existing receipt/grant/
   handoff identities. Re-prove through owners; do not relax the legacy variant
   into accepting arbitrary result/runtime combinations. Projection must wait
   for managed target settlement and terminal handoff rather than treating a
   worker's completed verification output as completed integration.

9. **Proposed ending order:** preserve a durable obligation before effects that
   could otherwise make further work appear unnecessary. Success must account for
   collected apply, actual exclusion/cleanup, target effect, queue settlement,
   Authority integration receipt, lease release and terminal parent routing.
   Re-enter incomplete owner acts by their stable identities. Close root admission
   through begin_integration_ending, end actual admitted members with their own
   proof, and release through scheduler's existing guarded owner only after the
   applicable outcome is retained. A receipt or cleanup axis alone is not final
   success. No cross-store atomicity is claimed.

   A known preparation failure must also settle the parent/root outcome: cancel
   planned apply, preserve child failure and exclusion, and report exceptional
   integration without inventing a parent runtime/claim or a successful result.
   Use a narrow integration-owned journalled outcome in integration_capacity
   and its bound projection if the pre-offer parent has no ordinary runtime
   observation. Its reader must prove the actual stage/episode/root/member facts;
   a caller-supplied failed flag is not release evidence. A known apply failure
   follows its actual attempt's ordinary cleanup/ending and keeps dependent gates
   closed. Target uncertainty or unresolved runtime/delivery exclusion retains
   the necessary hold and names identifiers, unknowns and manual next action.
   Releasing logical capacity never asserts that a target hold or Authority gate
   disappeared. Do not fabricate a frozen parent result to satisfy a generic
   ending API whose preconditions are absent.

## Exact proposed file ownership

All paths below are prefixed baton:. This is an upper bound for the selected
change, not a requirement to modify every file. No concurrent author on these
shared files. The actual author's PROGRESS and candidate enumerate changed paths
and explain test expectations. Standing test authority supplies permission for
necessary test changes; it is not another per-test approval gate.

| Source path | Bounded change |
| --- | --- |
| v12/python/tools/integration_bundle.py | Compose/adopt managed apply inputs and immutable derived evidence. |
| v12/python/tools/integration_worker.py | Parent continuation, admitted managed apply runtime and restart/ending composition. |
| v12/python/tools/stage_execution.py | Wire managed proposal/judgment/apply/placement, owned observation and final routing. |
| v12/python/tools/integration_placement.py | Concrete local materializer, authorization/exclusion/target effect owners; preserve existing publication gates. |
| v12/python/src/baton_v12/integration/managed_execution.py | Closed managed apply request/report/provenance variants, preserving preparation readers. |
| v12/python/src/baton_v12/integration/reconciliation.py | Retained managed transitions/readers and custody-to-approved-result mapping. |
| v12/python/src/baton_v12/integration/execution.py | Managed eligibility/grant and completion composition through existing owners. |
| v12/python/src/baton_v12/integration/queue.py | Recognition/proof of the added managed custody acts; existing queue/lease rules unchanged. |
| v12/python/src/baton_v12/integration/git_profile.py | Narrow atomic target-ref plus receipt-ref operation and receipt read; existing direct advance unchanged. |
| v12/python/src/baton_v12/job_manager/integration_capacity.py | Integration-specific durable final outcome/reader and composition with existing member/root ending. |
| v12/python/src/baton_v12/job_manager/delegation.py | Closed managed observation/completion admission alongside existing variants. |
| v12/python/src/baton_v12/job_manager/projection.py | Honest managed pending/failure/final projection and owed continuation, without early completion. |
| v12/worker/integration_contract.py | Separate managed apply purpose and closed artifact bindings. |
| v12/worker/integration_workload.py | Execute exact derived content/harness privately and retain measured apply output. |
| v12/worker/integration_entry.py | Dispatch the explicit managed purpose through ordinary launch/output boundaries. |

| Test path | Why it may change |
| --- | --- |
| v12/python/tests/tools/test_managed_apply.py (new) | Actual composed preparation-to-apply-to-final-outcome fixtures and bounded restart/failure cases. |
| v12/python/tests/tools/test_managed_preparation.py | Reuse the accepted ordinary preparation fixture; replace deferred-parent assertions only where selected continuation changes behavior. |
| v12/python/tests/tools/test_stage_execution.py | Managed composition/judgment/projection and legacy preservation. |
| v12/python/tests/tools/test_integration_worker.py | Parent apply port admission and actual lifecycle wiring. |
| v12/python/tests/tools/test_integration_bundle.py | Derived request/content/receipt correlation at delivery. |
| v12/python/tests/tools/test_managed_integration.py | Real receipt producer and restart alongside labelled abstract-owner tests. |
| v12/python/tests/tools/test_execution_limits.py | Original Job ceiling reaches managed apply; no host harness escape. |
| v12/python/tests/integration/test_managed_execution.py | Closed managed apply task/report variants. |
| v12/python/tests/integration/test_managed_storage.py | Journalled lifecycle and retained custody after apply admission. |
| v12/python/tests/integration/test_execution.py | Derived eligibility and final receipt/grant settlement. |
| v12/python/tests/job_manager/test_managed_integration_capacity.py | Final success/failure root disposition, planned cancellation and unresolved hold. |
| v12/python/tests/job_manager/test_delegation.py | Explicit managed completion with runtime; old variant refusals remain. |
| v12/python/tests/manager/test_integration_worker.py | Actual entry/workload and unchanged direct behavior. |

Reuse-only: generic Worker Manager/OCI transport/attempt lifecycle, scheduler
uniqueness/release guard, schema/migrations, source profiles, judgment execution
engine, existing preparation workload, image recipes and Authority protocol.
The new managed entry stays in the already copied integration worker files.
Do not perform schema changes, generic cancellation/start rewrites, source-boundary
relaxations or image builds under this packet. A concrete inability to compose
through these owners returns an exact scoped finding for selection; it does not
authorize a hidden fallback. The target Git profile operation and managed
completion/outcome representation are explicit new selections requested here.

## Finite acceptance and verification

The implementer records exact test methods/commands and supervised results in
PROGRESS. Start with the new tests.tools.test_managed_apply module, then impacted
named classes/methods in the table. Use the repository .venv interpreter from
v12/python with PYTHONPATH=src:tools:.; record actual pinned dependency versions.
Use sensible per-run timeout and TERM/KILL cleanup grace, preserving output and
measured duration. No tests ran in this research claim: new test spending0s.

Required bounded evidence, not a Cartesian matrix:

1. One ordinary actual accepted preparation, real derived proposal and scoped
   independent receipts, admitted parent apply, real worker entry and retained
   output, positive owner exclusion, actual disposable-target transaction/receipt,
   final integration receipt/lease release/handoff and released root. Assert
   target bytes and final dependency behavior, not merely start/helper counts.
2. Reopen ordinary stores/composition after candidate adoption and after derived
   publication: same result/proposal/judgment subjects, no repeated preparation.
3. Reopen after target transaction/receipt but before coordinator settlement;
   settle once without a second target effect. Reopen again after final receipt
   or handoff: the final account replays without duplicate result or receipt.
4. Missing/nonaccepting judgment prevents apply; a changed candidate mapping and
   a stale grant/changed target each refuse the affected boundary before an
   unauthorized target effect. Preserve existing placement negative tests rather
   than reproducing their full matrix in the composed fixture.
5. One known preparation failure safely cancels planned apply and records final
   failure; one known apply harness failure records its actual outcome, performs
   no target publication and ends only after ordinary cleanup/exclusion. Neither
   opens a success-dependent gate or becomes an automatic new attempt.
6. One uncertain start and one uncertain target-effect answer remain visibly held
   across reopen, with actionable IDs/unknowns and no duplicate start/CAS. Reuse
   group2 manual-start evidence where applicable; automatic convergence is not
   required. Do not fabricate a not-applied receipt from current target state.
7. One original-Job override reaches managed apply; inspect measured command,
   harness, candidate and actual bound. Coordinator execution traps cover merge
   and harness callbacks. Real Git metadata/custody materialization and the
   selected target-owner transaction are distinguished from candidate execution.
8. Bounded regression selection preserves preparation, direct integration,
   global result uniqueness, independent receipt requirements and root guards.
   Tests using fake providers/engine still exercise real orchestration, custody,
   worker and target owners. Report simulation honestly; no live OCI/model or
   remote-placement certification is claimed.

Owner rulings M172655/M172691/M172730/M172741 remain effective: visible manual
recovery for unknown starts; deferred partial-delivery protocol, broad adversarial
identity/custody/causal/limit/two-Job matrix and expanded cancellation/cleanup
matrix stay v13/unproved. Do not delete existing defect coverage or reintroduce
those campaigns as group3 prerequisites. Concrete work-loss, duplicate-effect,
isolation or false-success defects encountered in selected behavior still matter.

Main v12/python/DEPLOYMENT.md remains owner-controlled and outside this change.
The author may add a group3-local deployment/acceptance draft describing actual
outcomes and limitations. W170387 owns final independent feature acceptance and
documentation routing; W161230 and its dependents remain open/gated.

## Operational notes and handoff

Required policies/dossiers were readable. Guessed source names
integration/coordinator.py and job_manager/lifecycle.py and jobs.py do not exist;
file enumeration located queue.py and ending.py/episodes.py instead. These were
research lookup errors, not missing required evidence or a product defect.
No product files, tests, Git state, engines, images or models were changed/run.
The shared-tree inventory is a time-stamped baseline; author must revalidate it
at claim start and report drift, not overwrite another owner's work.

Owner selection requested: accept/amend this concrete scope and target receipt /
managed completion design, and name the serial implementing route. Do not close
W170385 on this design handoff; implementation and independent review remain.
