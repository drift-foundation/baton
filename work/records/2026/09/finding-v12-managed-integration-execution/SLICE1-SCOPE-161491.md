# Owner selection: managed integration slice 1

2026-09-13T14:59:52Z — baton.codex, claim161491.
**Requested approval, not granted authority.** Implementer and independent
reviewer have accepted the design boundary; the owner now selects this exact
implementation scope and its proposed verification allowance.

## Independently reviewed basis

| Canonical record | SHA256 |
| --- | --- |
| baton:work/records/2026/09/finding-v12-per-job-budgets/MANAGED-INTEGRATION-DESIGN-v2-2026-09-13.md | aed73e10fa684af0d34160733de7199b453b6dffecffdd86ba79761ed016adf6 |
| baton:work/records/2026/09/finding-v12-managed-integration-execution/DESIGN-RESPONSE-161397.md | b7e70a0b6695953e19ca3e3305d9115eb7a5c66bcb77534c5b08ba0104d92212 |
| baton:work/records/2026/09/finding-v12-managed-integration-execution/DESIGN-REVIEW-161426-2026-09-13.md | d6768221bf4e34967fcda57ffd0f50d91822a2a4ce62a143aed97d665a49da0b |

All three digests freshly match. M161449/return161456 accepts all five design
gates. The latest independent review withdraws its prior gate2 start-transition
demand and gate3 missing-uniqueness claim, explaining both source-reading errors.
The earlier review remains unchanged history. The response's narrowed reader,
release conditions and trusted execution-owner capability are the selected
design basis. This is not approval of implementation bytes that do not yet exist.

## Exact proposed path ownership

Paths are beneath v12/python. The next implementing claimant owns only these
paths for the listed changes, plus its implementation PROGRESS and evidence in
this dossier. Reviewer retains FINDING/PLAN and append-only review ownership.

| Path | Scheduled change |
| --- | --- |
| src/baton_v12/job_manager/schema.py | Additive capacity-root/member relations and constraints; preserve actual allocation foreign keys and unique worker/principal/stage-episode exclusion |
| src/baton_v12/job_manager/store.py | Bounded schema adoption/migration for those relations and operation ownership; no direct changes to live coordination stores |
| src/baton_v12/job_manager/scheduler.py | Guard registered-root release inside _move transaction, including completion/cleanup/ending shortcuts; preserve require_recovery |
| NEW src/baton_v12/job_manager/integration_capacity.py | Journalled register/admit/end/begin-ending/read operations, exact real identity bindings and serial membership including parent apply |
| src/baton_v12/worker_manager/attempts.py | Add only the read-only unstarted_cancellation_of owner API; reuse existing start/cancellation rules and derived operation identity |
| src/baton_v12/worker_manager/documents.py | Closed fenced-before-start result; no fabricated runtime/quiescence/Authority-gate completion |
| src/baton_v12/integration/schema.py | Portable managed-result table and bounded explicit5→6 compatibility schema, preserving old result-key uniqueness and target leases |
| src/baton_v12/integration/store.py | Strict old/new shape-aware readers and explicit upgrade; pre-mutation malformed-input refusal; one target-global store |
| src/baton_v12/integration/reconciliation.py | Legacy/new result creation and read checks across both representations, inside the existing transaction ownership |
| NEW src/baton_v12/integration/managed_execution.py | Closed portable preparation/apply task, collected report/custody and managed-result owner contracts |
| NEW tools/integration_placement.py | Trusted local target-owner interface with required execution-owner exclusion capability, current grant and admitted-old-revision publication contract |
| DEPLOYMENT.md | Describe only these owner contracts, explicit upgrade and current limitations; do not advertise deployed managed execution |

New additive test paths only:

- tests/job_manager/test_managed_integration_capacity.py
- tests/integration/test_managed_execution.py
- tests/tools/test_managed_integration.py
- tests/manager/test_reconciliation_worker.py

No existing test assertions or expected behavior are scheduled to change. Reuse
existing test helpers unchanged; a needed old-test modification requires its exact
bounded plan amendment, not an expired W71830 exception. No other source paths,
runtime image, generic start transition or protocol transport change is included.
If an additional boundary is necessary, return the exact missing scope before
editing it. New regular files use ordinary non-executable repository mode.

## Finish conditions and retained safeguards

1. One registered capacity root binds an actual integration stage allocation;
   actual child Work/offer/claim precedes admission, and parent apply is also an
   explicit member. At most one admitted/recovery-required member exists. No fake
   stage, hidden runtime or second allocation evades the effective-principal limit.
   Race admission/ending and verify exact replay versus changed operands.
2. Every registered-root release checks closed admission and all ended members
   atomically. Drive the named _completed_integration branch while root/member
   state still blocks release; then prove exactly one release after valid ending.
   Quarantine remains available while members are open/admitted. Ordinary
   unregistered allocations retain their current behavior.
3. The no-start reader requires six facts: exact fixed assignment; matching
   committed cancellation intent; actual Authority cancellation/fence; committed
   execution_runtime cancel-requested; no attached runtime; and no committed
   runtime.start for the exact assignment. Read related ControlStore facts in
   one owner snapshot. Derive _start_operation_id from that SAME row, including
   runtime_attempt_id, fixed assignment AND profile_digest as the actual helper
   does. Use the existing by-ID journal read; no new enumeration reader.
   A committed start refuses proof regardless of whether its adapter was called.
   Unknown/mismatched/refused facts hold capacity. Test both race orders, stale
   pre-read, cancellation interrupted before the axis, and committed-start replay.
   The result is fenced-before-start, never quiescent/destroyed or gate discharge.
4. Portable preparation/apply artifacts bind actual identity, original Job limits,
   immutable content/harness and real phase order. Distinguish measured integer
   status, collected tagged no-status failure, and no collected report. Preserve
   completed prefix/not-run suffix; use no dummy host paths or invented exit codes.
   Both result writers enforce the existing source/target-snapshot uniqueness
   across old/new tables in one target-global transaction. Strict upgrade preserves
   old records/live leases, rejects malformed shape/data before mutation, and
   read-only5/6 open never upgrades or creates another writable target store.
5. The placement interface uses locally composed trusted execution-owner evidence
   from the node that ran the exact phase. Bind assignment/attempt/start/runtime
   and collected content. Worker stop reports, stop orders, timeouts and foreign
   coordinator runtimes cannot authorize publication. Current grant/fence and CAS
   against the ADMITTED old revision remain mandatory. Missing capability or
   changed target refuses; no credential copy or invented remote backend.

Focused passing owner/contract tests and independent review of the exact resulting
candidate complete slice1. This supplies foundations only: actual preparation
delivery, managed runtime execution, derived apply and final consumer evidence
remain v2 slices2/3 with their own bounded selection. Neither W156162 nor W161234
is unblocked by slice1 acceptance alone. No full-feature or farm certification.

## Proposed allowance and concrete execution limits

Approve **120s cumulative author** and **30s cumulative independent reviewer**
subprocess wall time for slice1 only. W161230 measured verification spending is
currently0 for both. No predecessor spending or unused allowance transfers here.
Each command first fresh-sums its ledger and persists cap, starting spend,
remainder, expected cost, margin and timeout. Refuse if expected cost plus margin
cannot fit; timeout must be below remainder. Charge failures/timeouts and report
any actual overrun without rounding, reset or automatic extension.

Use focused deterministic owner/contract tests over temporary stores and fake
capabilities. No provider process, actual engine/container execution, image build/
pull/install, farm deployment or broad suite in this slice. Tests may create and
clean up their own fixtures through their ordinary boundary. Final focused checks
use project-pinned dependencies and record actual versions, per M161268. A concrete
environment refusal is reported with remaining scope; this allowance grants no
new installation authority or automatic separate environment project.

The first author handoff carries exact changed paths/digests, test selectors and
actual cumulative spending, then passes for independent candidate review. Later
slices require separately selected scope/budget; product implementation remains
with the assigned implementer, never inferred from this reviewer planning claim.
Git ownership remains with Slawomir.

## Decision requested and next route

Approve this slice1 path set, finish conditions and120s/30s cumulative allowance,
or return the exact requested adjustment. The mandatory architecture and the
accepted design are not being reopened. On approval, pin the exact ruling in
FINDING/PLAN and pass to baton.impl for slice1 implementation, next baton.feat
for independent review. This packet itself grants nothing before that ruling.

Preparation changed reviewer-owned records only. No test/probe/runtime/provider
execution or product/test/PROGRESS/environment/Git mutation. W161230 spending0;
W156162 author246runs2530.5844189850177s plus4unknown activities and reviewer
147.7342205499972s remain there. W103525 retains its own recorded caps, costs
and historical overrun. W161234 is now canonically blocked here by161487.
