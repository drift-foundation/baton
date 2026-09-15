# Relevant regression classification — reviewer claim174271

This is a bounded feature assessment, not a passing full-suite claim. Parent
review-2026-09-14T15-23-18Z.md and review-audit-170280.json preserve the original
7094-test run:40 failures,18 errors,20 skips,455.6685428629862s. Its earlier
wrong-root invocation was invalid. No broad discovery or engine rerun was made
here. baseline-classification-174271.json retains all58 reported outcomes with
zero-based historical indices, exact names/signatures and current rerun status.

## Observed again in this claim

The17 exact methods in historical-selectors-174271.json ran under the reviewed
180s process-group supervisor:2 failures,17 errors including subtests;
1.1234030229970813s. Every group ended, no timeout or signal. Exact argv and log
are bound by review-ledger-174271.json and after-174271.json. These remain red.
This is signature confirmation, not an old-base/current-candidate causal test.

| Historical indices | Classification and disposition |
| --- | --- |
| 0–3 | Completion fixtures in tests/job_manager/test_exchange.py and test_status.py omit required source_proposal_id/result_id. Current completion validation refuses them. Fixture producers need bounded maintenance preserving the original completion/held expectations; do not remove the production provenance checks. Actual managed completion and restart are independently exercised by the accepted group3 run. These fixture errors do not establish a broken ordinary completion producer. |
| 5–8 | AFreshPortReentersANeverStartedDelivery constructs an obsolete SimpleNamespace without reconciles; it errors before its intended behavior assertion. Update the fixture capabilities in a separately selected repair. |
| 9–16 | TheIntegrationStageConsumesTheAcceptedPort supplies object() as Authority and related owners; the current boundary reads proposal. Eight subtest errors from six methods are fixture-contract failures, not eight demonstrated runtime failures. Preserve the original start/reentry assertions when repairing. |
| 17 | TheServingPathReachesTheAcceptedDrivers runtime-port refusal case reaches Git materialization with no fixture source repository. The observed failure precedes the intended runtime-capability refusal. The fixture/setup-order question remains for a bounded repair; do not classify the intended assertion as passed. |
| 56 | The migrated-Job case reaches and passes its 300s compatibility-value assertion, then fails SCHEMA_VERSION==5 because the accepted additive schema is6. Preserve the migration/value proof and update the stale schema expectation in a selected repair. |
| 57 | Concrete construction unwind is a real known defect, W129838, discussed below. It is not a stale test and has not been fixed. |

## Preserved historical categories, not rerun or certified green

Indices18–45 cover Authority exports/diagnostic rules and manager receiving-owner,
probe and writer inventories. Indices47–55 cover operand/dependency allowlists,
durable-writer/security/public-callable and text-sweep inventories. Missing or
doubled entries and probes that do not reach their stated boundary are coverage
and maintenance debt. The two persisted-attempt probes also show a diagnostic
mismatch and a None.keys escape. The retained audit does not establish whether
every such observation is solely an outdated fixture; no blanket production
exoneration or unrelated-baseline claim is made. No security/whole-inventory
acceptance is inferred from the focused managed-flow run. Preserve these exact
rows for separately scoped inventory/boundary review; parent W161230's audit
remains their owning unresolved evidence. This claim selects no blanket repair.

Index4 is the deadline engine test's deliberate refusal of execution without its
reviewed engine-gate.py supervisor. It is not evidence that the supervised
runtime deadline gate failed. W32577 is independently closed satisfying168561;
its own bounded engine evidence retains its original meaning. This turn makes
no new OCI or combined managed-integration OCI certification.

Index46 is the credentials-engine global-prefix container inventory assertion.
The owner's15-exited-container list and original failure remain evidence; they
do not show those containers were made by this selected run. No new container
inspection, cleanup, engine run or claim of deployment-wide quiescence was made.
The supervisor proves only the process groups this reviewer launched are gone.

## W129838: confirmed, already parked; concrete effect assessed

Canonical detail snapshot174307: W129838 remains a confirmed defect, parked,
route baton.impl, no handler, last-change140586. Owning record:
baton:work/records/2026/09/finding-v12-stage-composition-hardening/findings/finding-concrete-worker-close/FINDING.md
and PLAN.md. Owner M140286/M140288 deferred it on2026-09-11; the parent's later
v13 classification does not magically cure it or defer an actual v12 loss.

Current source corroborates the same close/release mismatch: StageExecution's
_closers in tools/stage_execution.py selects release; worker_manager/single_worker.py
_Operations exposes close. On later construction failure, the test observes
only coordinator/authority closing, omitting implementation. The construction
path in operations_from gives the concrete ordinary worker dispose=lambda:None;
Authority is owned by the enclosing composition. Inspecting worker_operations
shows no additional independently owned persistent/runtime handle acquired by
that callback in this path. Thus the mocked missing close is real; an additional
current resource leak or corruption of the selected managed flow is not proven.
The independently exercised runtime cleanup/endings are separate owners.

Disposition: retain W129838 and its failing coverage under its existing explicit
owner deferral, without resolving/reopening/rerouting it here. Reassess if the
concrete worker acquires an owned resource or a current v12 loss is demonstrated.
This qualified assessment supplies the selected feature relevance decision; it
is not a global waiver of construction unwind correctness.
