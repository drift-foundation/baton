# Slice2 selection packet — local managed preparation

## Hardening amendment — owner22:32:06Z

Expanded failure/isolation permutations in the historical acceptance matrix
below are v13 hardening, not current W170382/v12 gates. In particular do not
require new exhaustive identity/artifact/custody, causal/timeout/limit and two-Job
combinations before delivery. Preserve existing checks/evidence and actual
correctness-defect coverage; label deferred cases unproved. Recovery child
FINDING/PLAN22:32:06Z is the controlling scope clarification.

## Uncertain-start amendment — owner22:18:02Z

For initially unknown runtime/uncertain failed start, visible actionable manual
recovery and human cleanup are sufficient. Any automatic late-identity recovery/
convergence requirement for this case is superseded. Preserve uncertainty,
original receipt/identity guards, no duplicate launch and unresolved holds;
never silently report absence or successful cleanup. No automatic late-proof API
or abandonment policy. Recovery child FINDING/PLAN22:18:02Z defines exact
reporting/restart acceptance; other selected cases remain required.

## Ordering amendment — owner M172097, 2026-09-14T20:45:53Z

The creation-before-registration relative order in historical composition
steps1–2 and the restart row below is explicitly SUPERSEDED. Register planned
capacity first, then commit immutable intent before child Work creation;
offer/claim/attempt/assignment/admission still precede ordinary runtime start.
Registration grants no execution. Replace the unreachable old cut with before
registration, after registration/before intent, after intent/before creation,
and after creation/before offer. Exact selected sequence, invariants and evidence:
findings/finding-managed-preparation-recovery/REGISTRATION-ORDER-PROPOSAL-170867.md
and that child's FINDING entry20:45:53Z. Preserve all other scope, recovery,
identity, one-root/apply-held and acceptance constraints. This is not slice2
acceptance. Older wording remains below as historical selection evidence.

2026-09-14, baton.codex claim165724. **Proposed implementation scope and allowance,
not implementation authority.** Owner reroute165721 assigned this preparation:
local managed preparation through the ordinary worker lifecycle, mandatory existing
worker input/output reuse, accepted slice1 preserved, derived apply/final failure
settlement deferred to slice3. No product or test file is changed by this packet.

## Decision to select

Select the nine source paths and eight test paths below for slice2 only. Extend
W161230's cumulative author verification cap from600s to1200s; retain the existing
300s cumulative reviewer cap. All prior spending stays charged. Select deterministic
provider/engine-boundary verification; no live model, actual Docker operation,
image build/pull or package installation is requested. The Dockerfile is a reviewable
recipe, not a claim that its image was built or provisioned.

The delivered boundary is a real separately claimed preparation execution composed
through existing Worker Manager owners, with immutable local input, ordinary exchange,
frozen/collected output and portable preparation adoption. The real worker code is
exercised behind the normal simulated engine boundary. It produces verified immutable
candidate/causal material suitable as input to later independent judgment, leaves
the parent apply planned, keeps the one root allocation held and changes no target.
This is not full W161230 completion or permission to release W156162/W161234.

## Observed baseline and implementation decisions

All21 paths in accepted slice1-candidate-165182.json still match, including
DEPLOYMENT.md. Slice1 remains accepted by review-2026-09-14T01-09-21Z.md.
SLICE2-BASELINE-165724.json binds30 edited/new/reused/protected paths and absence
of the five new files; SHA256
be532163850f476643abb48176e12db39c875871019b86206d1e82e149a30a52.
These are current working-tree bytes, not a clean Git checkout or import proposal.
Other owners have existing diffs; no resetting, staging or history mutation follows.

**Observed:** StageExecution.launch sends integration to Integration.run.
Integration.reconciled at stage_execution.py:2642 currently fetches into a coordinator
workspace, calls reconciliation.prepare_result, runs _CausalObserver and invokes
judge_result. _CausalObserver at2111 implements combined/base/isolated ordering and
the combined harness carried into the original base. Preserve that causal meaning;
the managed branch must move its merge/harness execution into the preparation worker.
The legacy/direct branch remains available and explicitly labelled legacy evidence.

**Observed:** PooledManagerOperations.admit at scheduler.py:807 reserves before
calling the worker's admit. That is the usable interception point: wrap the configured
integration operations in integration_worker.py so the real allocation exists before
managed preparation starts, and the parent's offer has not yet been issued.

**Confirmed constraint:** Authority has one claim slot per effective principal,
and the accepted root requires both phases to use the allocated integration actor.
Consequently the parent apply must NOT be claimed while preparation owns its separate
Work. A pool reservation is not an Authority claim. Do not release/recreate a claimed
parent, use another principal, fabricate an extra stage/allocation or weaken Authority
claim rules. Detect an already-claimed legacy parent and refuse managed conversion;
it stays under its recorded legacy recovery path.

**Observed:** manager._delegate treats a nondurable ContractRefusal as deferred
when the parent offer receipt is absent, but a successful return with no receipt is
an integrity failure. The wrapper must therefore drive one bounded preparation poll
and explicitly defer the parent admit while preparation or the later apply gate is
pending. Never mint a fake parent receipt. No generic scheduler/manager change is
needed. Real work/offer/attempt records and the capacity owner's reader expose progress;
do not smuggle a child assignment into the existing parent integration observation,
whose _integration_observation requires the parent's claimed offer/assignment.

**Observed reuse:** single_worker.worker_operations constructs ordinary operations;
_SingleWorker.start records/activates before composing input/start, and its ending
orders positive quiescence, freeze, intake, retention, Authority handoff and cleanup.
PreparationExecution may call the SAME public record_attempt/activate_assignment
operations with the exact same operands after its claim, admit its capacity membership,
then call ordinary operations.launch. The launch's repeats replay those owner acts.
Do not use checkpoint/test hooks as admission authority or copy the lifecycle into
a new runner. Existing mount/end composition seams are available when needed.

**Observed custody gap at this concrete boundary:** integration_capacity._collected_content
currently resolves frozen_output_of only; frozen is not proof of completed intake.
Strengthen successful preparation ending/adoption with intake_receipt_of and the
retained resultManifest/declared artifact identities, bound to the actual fixed
assignment and attempt. Frozen-but-uncollected and quarantined intake must never
become importable preparation. This is now scheduled source/test scope, not a request
to relitigate the accepted slice1 abstract contract.

A discovery search named nonexistent job_manager/serving.py; the serving owner is
job_manager/manager.py and was read instead. This was a search-path error, not a
missing runtime capability or an unavailable required dossier. No unavailable
required file remains.

## Exact source ownership after selection

All paths below are repository-relative. The assigned implementing claimant owns
these nine files and PROGRESS/evidence; reviewer owns FINDING/PLAN/reviews.

| Path | Bounded scheduled change |
| --- | --- |
| v12/python/tools/integration_bundle.py | Add a preparation-specific producer over accepted source/Job/checkpoint/receipts and the pinned target snapshot. Emit semantic request plus measured immutable object/artifact contents inside the ordinary worker source/input model. Reuse descriptor-bound extraction, digest/length checks and atomic local publication. Preserve direct compose_bundle and its lease-bearing envelope unchanged. |
| v12/python/tools/integration_worker.py | Add PreparationExecution and the integration admission wrapper: actual child Work/offer/claim, stable reconstruction, capacity admission before ordinary launch, bounded poll/exchange/ending, public frozen/intake verification and portable adoption. Keep IntegrationRuntimePort direct/apply behavior unchanged. Use worker_operations rather than a second OCI/credential/exchange implementation. |
| v12/python/tools/stage_execution.py | Compose the managed preparation wrapper before the parent offer; resolve the owning Job, configured worker/profile and source/target snapshot; route the selected managed branch away from host preparation/causal execution. Expose collected candidate material as preparation input for later judgment without legacy workspace-path cloning. Preserve existing nonmanaged/direct execution and all per-Job binding checks. |
| v12/python/src/baton_v12/job_manager/integration_capacity.py | Journal exact preparation creation/dispatch intent through existing JobStore operations before external Work creation, with closed owner reader/replay validation. Bind root, real parent episode, both planned phases and child input/profile. Strengthen successful preparation custody proof with the normal intake owner. Preserve serial membership, final-grant admission and every release guard. No new table required. |
| v12/python/src/baton_v12/integration/managed_execution.py | Add closed preparation-specific semantic payload/adoption helpers needed to bind request, causal report and candidate artifacts. Preserve current managed_task/report/result meanings; transport versions and self-digest rules remain unchanged. Do not relax old closed documents to accept extra members; use a separately named semantic artifact when richer fields are needed. |
| v12/python/src/baton_v12/integration/reconciliation.py | Add bounded owner adoption/read of actual collected preparation artifacts, with request/assignment/source/target/content/harness and custody proofs; reuse record_managed_result/attach_managed_phase and shared uniqueness. Return a portable prepared-candidate view suitable for later judgment. No legacy dummy paths, target publication, derived apply execution or final failure-settlement transition. |
| NEW v12/worker/reconciliation_task.py | Standalone preparation workload/semantic reader, using ordinary declared outputs. Materialize immutable input in private worker scratch; perform bounded Git preparation and causal commands; emit measured candidate/path/content/harness and ordered report artifacts. No manager/Authority imports or writable target capability. |
| NEW v12/worker/reconciliation_entry.py | Compose baton_worker.main(agent=preparation_agent) at its existing seam, following dogfood_entry. Reuse the ordinary file exchange, launch/input readers and worker-measured output manifest. No second serve loop or one-shot integration namespace. |
| NEW v12/worker/Dockerfile.reconciliation | Reviewed pinned recipe for the existing worker plus the preparation workload and required Git/runtime tools. Non-root, exec-form entrypoint, no manager/Authority/store package or credentials baked in. Recipe-only verification; do not invent a production image digest or build/pull it under this selection. |

The old v2 table's delegation.py edit is narrowed to reuse: its ordinary operations
already provide the needed behavior. single_worker.py, scheduler.py, manager.py,
JobStore schema/store, generic launch/workspaces/source-boundary/exchange/OCI/output/
intake/Authority modules and GitIntegrationProfile are reuse-only. No hidden source
amendment is granted through a test helper. If concrete implementation proves a
new source boundary necessary, return the exact missing path/API and evidence.

## Required composition sequence and data identity

1. Resolve current parent Job/stage/episode/allocation and accepted source evidence.
   Pin target commit/tree and preparation profile/required harness. Author an immutable
   preparation request; determine child Work/offer/attempt identities from a closed,
   digest-bound orchestration intent. Persist that intent BEFORE public
   Authority.create_work, whose explicit operation_id supplies exact replay. Resolve
   the returned/existing Work and scope; never substitute an in-memory/mock ID in
   the product. Changed intent, route, input, profile, Job or target snapshot refuses.
2. Register the root and both planned members against the existing actual allocation.
   The apply member uses the actual parent Work/offer/attempt and remains planned.
   A created Work with registration unfinished is recoverable intent, not permission
   to issue/start. Keep one participant/principal/worker/pool generation throughout.
3. Issue/accept/claim the preparation's ordinary offer using its actual runtime input
   manifest. Record/activate the attempt through public owners; obtain actual fixed
   assignment; compose/rebuild the slice1 managed task; admit prepare; then ordinary
   launch/dispatch. A failed admission starts nothing. Never weaken the existing
   input/profile/assignment comparisons or compare pool generation to claim generation.
4. Use the existing input.json/assignment.json/source and artifactRef mechanisms.
   Keep the original Job input_digest/policy/limits separate from the preparation's
   actual input manifest/digest, as ordinary judgment executions already do. The
   immutable pre-claim request contains no invented future claim generation and no
   self-referential manifest digest. After claim, managed task identity is reconstructed
   from that request plus the real manifest and assignment owner facts; task_digest
   names the stable request/task material, not a self-containing envelope.
5. The request carries bound source/base/candidate/target object identities, accepted
   path/test authority and harness identity. Logical artifact locators carry measured
   content identity/length through the normal local materializer; they are never
   treated as coordinator paths. Read-only object extraction/export is allowed on
   the coordinator; merge, checkout-for-harness and test execution run only at the
   preparation worker boundary. Its image receives no writable target, lease,
   Authority session, refresh authority or production publisher capability.
6. The worker runs the real configured causal sequence combined/base/isolated using
   immutable snapshots; compare Git behavior to the existing profile's fixed vectors
   and semantics in conformance cases. The container must not import baton_v12 to
   reuse its manager capabilities. Genuine base failure caused by the missing fix
   remains valid evidence; combined failure/conflict is not success. Preserve real
   integer statuses, completed prefix, tagged no-status failure and not-run suffix.
   A worker cannot claim collection, runtime exclusion or manager receipts.
7. Ordinary worker code measures declared candidate/report/log outputs. The manager
   positively quiesces, freezes, collects, verifies accepted intake, retains, hands
   off the child assignment and completes its normal cleanup. Read these owners
   on recovery even after writable roots disappear. Adopt preparation using actual
   manifest/artifact bytes, task/assignment/harness and causal checks; no direct JSON
   report or terminal alone becomes trusted custody. Do not embed a result manifest's
   own final digest in its payload; manager-owned collected references are added after
   freeze/intake. End membership only on its real owner exclusion proof.
8. Successful finish is a portable, measured preparation account plus retained input
   for later judgment, preparation ended, apply still planned and root still held.
   No synthetic reviewer/approver receipt or accepting verdict. Actual derived proposal
   publication/receipt dispatch, derived apply, target effect/receipt producer and
   overall failure/root settlement stay slice3. Failure preserves the measured phase
   evidence and capacity/target holds; required ordinary child cleanup is still driven
   through its existing owners, not waived because root settlement is later.

## Finite acceptance cases

| Group | Required positive, refusal and recovery evidence |
| --- | --- |
| Real coordination and one capacity | Use real disposable Authority/JobStore/ControlStore owners. Create/claim actual separate preparation Work; prove parent has no concurrent claim, exact participant/principal and one root allocation; another Job cannot acquire the occupied integrator. Use no fake stage or second pool slot. |
| Admission/start order | Engine spy refuses any runtime start before committed matching prepare admission; stale/mismatched assignment, Work/offer, input/profile and quarantined root refuse without start. Parent apply cannot claim/start during preparation or at slice2 finish. |
| Ordinary I/O and portable custody | Execute real ordinary launch/input/exchange/output/freeze/intake boundaries using deterministic engine/provider simulation. Tampered digest/length/task/assignment/manifest, missing blobs, symlinks/path escape, missing/quarantined intake and frozen-only evidence refuse. Reopen with original execution roots unavailable and adopt from retained local custody. |
| Real worker behavior | At the normal simulated engine seam invoke actual preparation entry/workload in a separate fixture process. Exercise real disposable Git merge/materialization and real tiny harness commands there; pass protocol/candidate artifacts through actual worker measurement. A fixture result assembled directly by the coordinator is not this evidence. |
| Causal failures and limits | Combined pass/base genuinely missing-fix failure/isolated pass; merge conflict and combined failure; start failure and timeout at each causal position with exact prefix/suffix. Original default former-host verification300 and explicit overrides reach each relocated command via the actual Job owner; preserve provider3600 and unrelated defaults. Two Jobs with distinct overrides cannot cross-wire. No default inferred from child's unrelated input. |
| Coordinator execution trap | Trap legacy prepare_result/_CausalObserver/_ConfiguredExecution or actual merge/harness runner calls in the managed coordinator process. Fail if preparation escapes the worker seam; allow only declared read-only identity/object export. Show the trap catches an intentionally invoked forbidden boundary. |
| Restart and idempotence | Cut after intent/before Work creation, after creation/before registration, after claim/before admission, after admission/before start, after start intent/adapter return, after worker answer/before freeze, after freeze/before intake, after accepted intake/before attachment, and after child cleanup/before membership ending. Rebuild composition; reconcile exact owners; no duplicate Work/claim/runtime/harness turn/attachment. Unknown start remains held, never silently relaunched. |
| No premature success | Missing report is not collected-without-status; no-status is not an exit code. Blocked or incomplete result cannot become successful preparation input. No target bytes/ref/entry settlement, parent release, fabricated judgment or dependent release. Existing direct/legacy tests retain their actual meanings. |

Changing a target snapshot after intent does not retarget the run; preparation is
about that immutable snapshot. Later current-grant/CAS responsibility stays slice3.
A restart test's deliberately incomplete call is charged like any other verification.

## Test path ownership and focused verification

Two new test files:
- v12/python/tests/tools/test_managed_preparation.py — real coordination and ordinary
  lifecycle assembly, independent fake engine seam, cuts/traps/portable adoption.
- v12/python/tests/manager/test_reconciliation_task.py — real worker entry/workload,
  semantic conformance, causal/limits/error cases and recipe/import-graph checks.

Scheduled updates to six existing files:
- tests/tools/test_integration_bundle.py: preparation input artifact producer/refusals.
- tests/tools/test_stage_execution.py: managed wiring, reserved-before-parent-offer
  behavior and real per-Job ownership; preserve direct/legacy branches.
- tests/tools/test_execution_limits.py: add managed equivalents for former-host causal
  defaults/overrides/prefix/suffix, retaining existing cases as legacy evidence.
- tests/job_manager/test_managed_integration_capacity.py: intent/replay and accepted
  intake custody; update frozen-only success fixtures to drive real intake.
- tests/integration/test_managed_execution.py: richer semantic preparation artifacts
  and strict bound contracts; no weakened existing report semantics.
- tests/integration/test_managed_storage.py: real collected phase attachment/read,
  malformed custody refusal and unchanged shared uniqueness.

Those six paths are beneath v12/python. M162289 preapproves necessary test changes;
record actual fixture/assertion changes and evaluate them independently. No extra
per-test approval gate. New files are mode0644, never executable without exact scope.

Run the changed focused modules, then relevant existing ordinary worker/input/output/
intake and manager/delegation neighbors only where integration changes justify it.
Use pinned Python3.13.7/jsonschema4.26.0. No installation or broad suite. Reuse
applicable slice1 evidence at matching hashes. Every launched verification child,
including nested worker/harness simulations and failed cut cases, is included in
the guarded command's measured wall time; no uncharged standalone probe loop.

Current spending: author160 runs401.4989696021221s, reviewer21.403079563991923s.
Selection would yield cumulative caps1200s/300s and available798.5010303978779s/
278.5969204360081s. This is an explicit author-cap extension, not a fresh budget or
a transfer from another Work. Existing cap600 remains until selected. Rationale:
the last15-module focused run cost15.80641844800266s; new worker/cut matrix iterations
need more than the remaining198.5010303978779 author seconds, while reviewer reserve
already fits focused independent work. Plan roughly400–600 author seconds and at
most90 reviewer seconds; unused reserve is not a reason to broaden tests. Persist
actual cap/spent/remainder/expected/margin/timeout before each child, charge failures/
timeouts, and refuse if it cannot fit. No verification ran in this planning claim.

## Shared ownership and handoff

DEPLOYMENT.md remains with W32577 under M165203, currently still SHA256
971fba687461bf4cc0c8899b5f692d086cad3af8cd794573b2004cee1f0a7f94. This selection
does NOT acquire it. Implementer writes DEPLOYMENT-SLICE2-DRAFT.md in this dossier,
describing actual ordinary lifecycle, candidate custody, deterministic qualification
and later apply limitations; hand its digest to the current doc owner for serial
integration. No duplicate user manual is shipped from the dossier. A final main-doc
edit needs the recorded fresh-hash handback first, not an interactive permission gate.

Before implementation, revalidate this packet against later decisions/current bytes,
claim the Work and confirm scoped file ownership; preserve accepted slice1 and
other active diffs. Return an exact candidate/test-path inventory, newest PROGRESS,
logs and cumulative budgets for independent review. If selection changes any product
path, append the exact amendment in FINDING/PLAN. No generic source, Git, engine or
live-provider authority is inferred. Route this packet to baton.decide for selection,
next baton.feat to pin the ruling and hand selected implementation to baton.impl.
