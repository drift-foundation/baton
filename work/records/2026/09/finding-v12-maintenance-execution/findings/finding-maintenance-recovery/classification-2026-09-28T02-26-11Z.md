# W285465 owner narrowing — hunk disposition against b4b3fc8d

Authority: T285465 messages291205/291218/291235 and OWNER-NO-AUTOMATIC-NORMALIZATION-20260928.md; DESIGN HOST-5. Reviewer claim291240. Baseline b4b3fc8d is comparison ONLY. Full diff preserved in pre-narrowing-2026-09-28T02-26-11Z.patch (not an import/rollback instruction). Ranges below use current snapshot coordinates; exact old/new hunk coordinates appended. Implementer owns selective product/test edits, reviewer records; baton.prompt owns current DESIGN/owner-ruling edits. Recheck drift before editing, never replace whole shared files.

| Path under v12/python | Hunks/symbols | Disposition and rationale |
|---|---|---|
| src/baton_v12/worker_manager/tokens.py | new138-834 recovery constants/RecoveryHold/readers/admission/results/clearance; acquire signature1060 and gate1165 | Repair-only extension: selectively remove its production API/wiring when unused after narrowing. Preserve baseline token exact generation/launch/runtime/activation/cessation/revocation rules. Historical patch/probes remain evidence. Do not turn removal into acceptance of a pre-existing unresolved execution. |
| src/baton_v12/worker_manager/workspaces.py | _task_token_refusal recovering operand3203, recovery hold/exemption3236-3270 | Repair-only wiring paired with tokens extension; remove selectively with that extension. Preserve baseline live-task/preparation exclusion and exact identity safeguards. |
| src/baton_v12/worker_manager/intake.py | _normalized4095/4117/4121 forwarding | Repair-only operands: remove from selected flow. Further bounded edits REQUIRED to completion/recovery callers and proof construction: accessible output must progress without normalization receipt, permission failure preserves bytes/holds and reports exact operation; task/helper cessation still proven. Do not simply return fake custody success or skip evidence. |
| src/baton_v12/worker_manager/oci.py | normalize_directory3477/3519/3539/3548 | Repair-only governing/recovering forwarding and CUSTODY_WORK_VERBS integration may be removed together with governed custody branch. Preserve existing work/cleanup bounds for any retained legacy paths. No new helper launch on selected path. Existing normalization support for other separately selected operations is not blanket removal scope. |
| src/baton_v12/worker_manager/custody.py | _custody_vector1025/1101; _claim_episode1924/2028/2034; normalize_directory2178/2242/2253/2257; CUSTODY_WORK_VERBS2416; _governed_act2464; custody_act2555/2605/2610/2634/2644/2766 | Repair-only governed branch, capability exemptions and hooks: selectively remove with matching callers/tests. Preserve baseline custody implementation/evidence for unrelated separately selected operations, but bypass automatic normalization on this selected path through an honest alternative outcome, not fabricated receipts. |
| src/baton_v12/worker_manager/custody.py | surviving_helpers1385-1436 | Potentially useful READ-ONLY cessation evidence: retain provisionally if used by the narrowed flow. It lists/inspects known custody names and retains uncleared journal episodes; it starts nothing. It is not complete proof for all writer families or a delayed submission. Integrate and prove relevant identity/unknown/outage cases; remove if genuinely unused rather than completing repair machinery. No new helper-container launch. |
| tests/tools/test_single_worker.py | import copy9; EveryHOSTPREPARATIONPHASEIsRecoveredOrHeld2365-2883 | RETAIN useful recovery tests: abrupt phase cuts, completion/restart, identity replacement and concurrent writer. Independently7PASS0.524s/wall0.564s this review. Boundary cuts are not all interior cuts; retain honest coverage notes. Reuse accepted W285464 proofs, add only concrete missing preparation/duplicate-execution cases. |
| tests/job_manager/test_tool.py | fixture reorder1428/1442/1466/1481 | RETAIN allocation-before-governance fixture correctness. It reflects selected host preparation and does not require repair. |
| tests/job_manager/test_tool.py | test_the_WORK_verbs...910-933 | Repair-only new constant assertion: remove with constant. Reassess existing8 failing chain tests against owner outcome; keep budget/isolation/idempotence and error-preservation coverage, replace obsolete mandatory-normalization expectations with zero-helper success/error behavior. |
| tests/manager/test_maintenance.py | new TheRECOVERYHOLDExempts..., TheGOVERNEDCustody..., TheRECOVERYHOLDGates... blocks1783+/2163+ and added token_support import29 | Repair-only coverage may leave active suite with removed APIs, preserved in this patch and append-only reviews. Do not delete baseline maintenance facility tests. Preserve transferable negative cases as job/token safety coverage where relevant; no release gate to run repair containers. |
| tests/manager/test_maintenance.py | new TheSURVIVINGHelpersAreEstablishedAndNotAssumed within1783+ block | Retain with reader if used for narrowed cessation. Author2-case evidence unverified this review; add relevant unknown-journal/writer/outage tests when connected. Not acceptance of full helper absence. |
| tests/manager/test_custody.py | signature expectations/comments554/569 and1092/1107 | Selectively undo additions of recovering/governing if API removed. Preserve exact no-caller-path guard; expectation changes follow removal, not weakening to ignore operands. |
| tests/manager/test_dependencies.py | added repair operand exceptions428-447 | Remove only exceptions whose API operands are removed; inspect remaining use of common names before removal. Preserve unrelated baseline allowlist. |
| tests/manager/test_boundary_inventory.py | RECOVERY_OWNERS1995+, spread2343, WITNESSES9581+, witness helper10258+, four recovery witness methods10308+ | Remove repair-only entries/witnesses with removed APIs. Retain/adjust surviving_helpers ownership if retained. Do not complete obsolete repair witnesses to satisfy a new gate. Report residual receiving debt honestly; newest author573 vs571,2128 total is not accepted. |

Unchanged versus baseline: maintenance.py, single_worker.py product, job_manager.py product, existing task token enforcement. Preserve them except concrete scoped completion/recovery changes supported by new tests. DESIGN.md is outside this patch and owned by prompt: retain current owner text. All canonical dossiers, owner files, reviews, prior candidate manifests/probes stay immutable historical evidence even if their repair-only probes no longer run against narrowed product.

Next accepted scope: interrupted preparation refuses partial launch/overlap; lost create/start does not duplicate jobs; exact task/writer cessation before release; accessible output succeeds with ZERO helper/maintenance starts; inaccessible output reports an error, preserves workspace/bytes and unresolved holds. No automatic host chmod/chown/delete workaround. Runtime removal is distinct from workspace deletion. I/O outside DB locks. No live run, broad refactor, deployment or graph change.

Human WIP message: WIP v12 recovery: preserve host-preparation recovery proofs; classify obsolete automatic repair additions for selective removal. New no-helper completion/recovery path and permission-error preservation are not yet implemented or independently accepted. Git remains human-owned.

## Exact diff hunk index

```diff
+++ b/v12/python/src/baton_v12/worker_manager/custody.py
@@ -1025 +1025 @@ def _custody_vector(engine, *, image_digest, store, assignment_id,
@@ -1101 +1101,12 @@ def _custody_vector(engine, *, image_digest, store, assignment_id,
@@ -1373,0 +1385,52 @@ def _hold_identity(kind, assignment_id, which, episode):
@@ -1861 +1924 @@ def _claim_episode(store, assignment_id, which, operation, image_digest,
@@ -1964,0 +2028,4 @@ def _claim_episode(store, assignment_id, which, operation, image_digest,
@@ -1967 +2034,2 @@ def _claim_episode(store, assignment_id, which, operation, image_digest,
@@ -2110 +2178,2 @@ def normalize_directory(store, custody, *, assignment_id, which,
@@ -2172,0 +2242,9 @@ def normalize_directory(store, custody, *, assignment_id, which,
@@ -2175 +2253 @@ def normalize_directory(store, custody, *, assignment_id, which,
@@ -2179 +2257 @@ def normalize_directory(store, custody, *, assignment_id, which,
@@ -2337,0 +2416,10 @@ def _custody_operation_id(assignment_id, which):
@@ -2375,0 +2464,90 @@ def allowed(seconds, most):
@@ -2377 +2555 @@ def custody_act(engine, run, *, image_digest, store, assignment_id,
@@ -2427 +2605,2 @@ def custody_act(engine, run, *, image_digest, store, assignment_id,
@@ -2431 +2610,2 @@ def custody_act(engine, run, *, image_digest, store, assignment_id,
@@ -2453,0 +2634 @@ def custody_act(engine, run, *, image_digest, store, assignment_id,
@@ -2463 +2644,3 @@ def custody_act(engine, run, *, image_digest, store, assignment_id,
@@ -2582,0 +2766,6 @@ def custody_act(engine, run, *, image_digest, store, assignment_id,
+++ b/v12/python/src/baton_v12/worker_manager/intake.py
@@ -4095 +4095,2 @@ def _custody_capable(adapter):
@@ -4115,0 +4117,2 @@ def _normalized(store, adapter, attempt_id, *, seconds=None, reclaim=None):
@@ -4118 +4121,2 @@ def _normalized(store, adapter, attempt_id, *, seconds=None, reclaim=None):
+++ b/v12/python/src/baton_v12/worker_manager/oci.py
@@ -3477 +3477,2 @@ class OciAdapter:
@@ -3518 +3519,16 @@ class OciAdapter:
@@ -3522,0 +3539,6 @@ class OciAdapter:
@@ -3526 +3548,2 @@ class OciAdapter:
+++ b/v12/python/src/baton_v12/worker_manager/tokens.py
@@ -137,0 +138,697 @@ def domain_of(resource_kind, identity):
@@ -363 +1060 @@ def acquire(control, domain, *, operation, execution, attempt=None,
@@ -467,0 +1165,8 @@ def acquire(control, domain, *, operation, execution, attempt=None,
+++ b/v12/python/src/baton_v12/worker_manager/workspaces.py
@@ -3203 +3203 @@ def _revalidated_roots(storage, assignment_id, what, control=None):
@@ -3235,0 +3236,25 @@ def _task_token_refusal(control, assignment_id, what, mine=None):
@@ -3236,0 +3262,9 @@ def _task_token_refusal(control, assignment_id, what, mine=None):
+++ b/v12/python/tests/job_manager/test_tool.py
@@ -909,0 +910,24 @@ class TheStatusSurfaceMayReadIntegrationAndStillActOnNothing(unittest.TestCase):
@@ -1403,0 +1428,10 @@ def _unsettled_governed_attempt(case):
@@ -1409,4 +1442,0 @@ def _unsettled_governed_attempt(case):
@@ -1437,6 +1466,0 @@ def _running_governed_attempt(case):
@@ -1456,0 +1481,9 @@ def _running_governed_attempt(case):
+++ b/v12/python/tests/manager/test_boundary_inventory.py
@@ -1994,0 +1995,79 @@ _PREPARATION_ROOTS = "the roots THIS manager's own `assignment_workspace` answer
@@ -2263,0 +2343 @@ STATED_OWNERS = {
@@ -9500,0 +9581,64 @@ WITNESSES = {
@@ -10113,0 +10258,15 @@ class DeadlineForwardingInventory(unittest.TestCase):
@@ -10148,0 +10308,161 @@ class StatedRules(BoundaryCase):
+++ b/v12/python/tests/manager/test_custody.py
@@ -553,0 +554,13 @@ class OneMountAndNothingElse(CustodyCase):
@@ -556 +569,2 @@ class OneMountAndNothingElse(CustodyCase):
@@ -1077,0 +1092,13 @@ class OneMountAndNothingElse(CustodyCase):
@@ -1080 +1107,2 @@ class OneMountAndNothingElse(CustodyCase):
+++ b/v12/python/tests/manager/test_dependencies.py
@@ -427,0 +428,20 @@ class NoPublicOperationTakesInternalState(unittest.TestCase):
+++ b/v12/python/tests/manager/test_maintenance.py
@@ -28,0 +29 @@ from . import input_roots
@@ -1781,0 +1783,378 @@ class TheContainersOwnExitDecidesTheOutcome(MaintenanceCase):
@@ -1783,0 +2163,643 @@ if __name__ == "__main__":       # pragma: no cover
+++ b/v12/python/tests/tools/test_single_worker.py
@@ -8,0 +9 @@ import copy
@@ -2363,0 +2365,519 @@ class AnABRUPTDeathLeavesTheWindowStandingAndLaunchesNothing(SingleWorkerCase):
```
