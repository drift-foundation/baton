# W71830 correction: ordinary tests, independent review and retained custody

Current allocation clarification, owner112006: the single-implementer allocation
and literal preservation of the disputed whole-verdict comparison below are
superseded by LIFECYCLE-PLAN.md and W112029 FINDING/PLAN. All remaining semantic
requirements stand; the four field mappings and separate recorded_at validation
are explicitly approved. This paragraph preserves the original proposal as history.

Planning: baton.codex, claim111746. Controlling owner clarification: M111752,
superseding M111720's unresolved verification question and owner111686's provider
assignment. The exact ruling is in the W71830 FINDING under “Current verification
is implementer testing plus review”. This is the proposed bounded implementation
assignment for ops disposition; no source/test edits or runtime execution yet.

## Current contract and exact supersession

For W71830, the implementer runs the ordinary required tests and the independent
reviewer assesses the exact checkpoint and may run additional tests. A separate
clean verifier is deferred. CORRECTION-PLAN.md remains historical design support;
its producer, request/read capability, rich clean-verification receipt pair and
reviewer-axis projection are not prerequisites or implementation tasks now.

Explicitly superseded for this milestone: the W71918 requirement that a review
attempt itself have verification=passed before any technical verdict, and the
clean-context requirement insofar as it requires another verification producer.
The reviewer attempt's verification axis may remain none. Do not write passed
into it, reinterpret its failed/unable values, or regress it to another value.
The technical verdict is not certification that required tests passed.

The separate Authority verification receipt remains a protocol prerequisite of
Authority review/integration. Under the owner-approved milestone workflow its
passed observation may describe **actual ordinary required test results**, with
explicit evidence provenance; it must not claim an independent clean run. The
existing unconditional passed in integration.driver is therefore replaced by
evidence-driven publication, not retained unchanged or used to set a manager
axis. No Authority/schema change is proposed. Ops must explicitly include this
receipt interpretation and the test expectations below in the source assignment.

Required tests that failed or did not run cannot produce passed or admission.
An accepted review is not a substitute. Additional/broader red results remain
visible to independent review; changing which failures are required/exempt is
an exact owner decision, never an automatic baseline exception. This plan does
not redefine any current red source gate as green.

## Existing execution and smallest missing data path

Confirmed: v12/worker/claude_agent.py:632 calls _verify with the frozen task's
verification argv in the implementation container. It revalidates candidate
bytes after that command and publishes the private-line commit plus result.json
and verification.txt. The structured record contains the actual status/argv,
task_id, base and head. Its output metadata currently exposes only the four-field
baton.git-proposal/1 claim, so the integration consumer cannot directly resolve
the ordinary test observation through its current frozen-result reader.

Keep this actual execution unchanged. Add one separately namespaced structured
observation to the existing proposal output's result_metadata, proposed name
baton.git-ordinary-tests/1. Closed members: task_id, task_digest, argv, status,
base, head. task_digest is the SHA-256 of the exact bounded task bytes consumed
by the worker; base/head are the existing private-line objects. Populate it only
from the same supervisor-owned task and actual _verify answer used by result.json,
after candidate revalidation and publication. No model-written verification flag,
new suite runner, new output directory, result-schema change or child-stream
capture. Absent/unrun stays absent or explicitly null under the pinned reader
contract; failed status is retained unchanged. Preserve the existing proposal
claim's closed four fields and the review-claim namespace.

integration.driver owns the format-specific reader. Resolve the producer from
the checkpoint and retained proposal, then read the existing frozen result and
retained result manifest; compare assignment/generation, result/manifest/artifact,
proposal base/head, checkpoint head and input/policy identities as the existing
publication reader already does. Compare the observation to a trusted required
test selection supplied by W103083 from the existing implementation deployment's
bounded task_bytes: task_id, task_digest, exact argv and input_manifest_digest.
Add one explicit required_tests keyword to admit_accepted for that closed
selection. It selects requirements, never supplies an observation or passed flag.
W103083 derives it from the same task used for that Job/producer, including
correction attempts; it must not pick a different worker's configuration.

Only actual status0 for the exact required command, bound to the accepted
checkpoint's producer and assessed by its independent review, can yield the
existing Authority raw passed receipt. Validate this before any receipt side
effect. Include the frozen result/observation and requirement digests plus an
ordinary-tests workflow marker in deterministic receipt/operation identity;
retain the full observation in the existing result manifest so the digest is
resolvable. Use an explicitly ordinary-tests identity prefix rather than a
clean-certification label. Existing Authority/session capability checks, current
target checks, review/approval separation and conflict refusal stay intact.
An old differing verification receipt is a conflict, not an overwrite or a
reason to replay a historical fabricated passed value.

No second verifier actor, service, Job stage, queue, worker image, configuration
schema or host execution of candidate code is needed. The current actor/session
records its accountable interpretation of retained ordinary evidence. This is
the precise limitation: it is author-container testing plus independent review,
not clean candidate-merge certification. It follows the owner's milestone ruling.

## The two actual lifecycle defects

First verdict: keep the independent active attachment, current exact checkpoint,
completed disposition, positive runtime quiescence, frozen result and findings/log
bindings. Accept output=sealed only with the matching accepted intake receipt,
result/manifest/artifact identities and required retention decisions. Preserve
the valid legacy frozen branch. Remove only the obsolete reviewer-verification
axis prerequisite; custody alone never proves review completion or a verdict.
No sealed-to-frozen transition and no broad writer-quiescence relaxation.

After ordinary cleanup, exact verdict replay and integration_checkpoint must
read historical evidence. A destroyed runtime is acceptable only for an ended
attachment with its already committed exact verdict, fence, result, accepted
intake, required retained artifacts and successful positive cleanup operation.
Use intake_receipt_of, retentions_of, intake.destroy_operation and the existing
operation journal. Do not ask a destroyed runtime to become quiescent again or
allow destruction to create a first verdict. Missing/uncertain cleanup stays
held. In review_driver, a post-cleanup replay takes this proved historical path
before attempting quiesce/freeze again and returns the existing ending. This
covers immediate cleanup/re-entry, not W110783's separate restart matrix.

integration_checkpoint remains the exact technical-review eligibility reader;
the required-tests gate is enforced by integration admission before Authority
receipts or target access. Do not leave a second reviewer-axis passed check in
that historical reader. Reopening retained bytes after cleanup remains mandatory.

## Proposed bounded assignment and exact expectation changes

Assign the serial implementation to baton.impl under W110772, with these nine
fixed paths and one narrowly bounded inventory path:

1. v12/python/src/baton_v12/worker_manager/review_cycles.py — first-verdict sealed
   custody and historical replay/eligibility; remove reviewer-axis certification.
2. v12/python/src/baton_v12/job_manager/review_driver.py — proved post-cleanup
   ending replay, preserving actual freeze/intake/retention ordering.
3. v12/python/src/baton_v12/integration/driver.py — resolve ordinary test evidence,
   compare required_tests and replace unconditional passed receipt publication.
4. v12/worker/claude_agent.py — expose its existing actual ordinary test result in
   namespaced output metadata; no change to test execution or provider behavior.
5. v12/python/tests/manager/test_review_cycles.py.
6. v12/python/tests/job_manager/test_review_driver.py.
7. v12/python/tests/integration/test_driver.py.
8. v12/python/tests/manager/test_claude_agent.py.
9. v12/python/REVIEW-CYCLES.md — explicit current verification and lifecycle rules.
10. v12/python/tests/manager/test_dependencies.py — only the exact new
    required_tests operand declaration if required; preserve inventory assertions.

Scheduled test edits for owner approval: in
test_verdict_requires_quiescent_frozen_verified_findings_and_logs, replace the
failed reviewer-axis refusal expectation with the current technical-review rule;
keep the unrun/quiescence/findings/logs refusals and no-side-effect assertions.
Add none/failed/unable reviewer-axis cases demonstrating that no axis is forged
or reset. Move required-test failure/unrun refusal coverage to the actual
integration admission boundary, including zero verify/review/approve/admit calls.
Existing raw-axis fixture setup may remain in unrelated legacy cases; it is not
positive evidence for the new workflow. Enumerate each actual assertion change
and bind reviewed candidate bytes before integration.

Keep the two TheWorkerCompletionTraversesPublicCustody assertions intact; their
real first-ending and freeze-reentry must pass with verification none. Extend
them through actual cleanup, retained-byte reopening and eligibility. Add exact
historical replay and negative destroyed-without-cleanup cases. Integration tests
must use an actual trivial required command through the worker's existing _verify
path and real result/manifest/custody/Authority consumers, with deterministic
external transport; no mocked passing observation. Cover a nonzero and unrun
command, wrong task/argv/digest/head/generation, conflicting receipt and replay.
Preserve worker result.json behavior and all existing review/provider refusals.

W103083 owns its existing stage_execution.py assembly and tests: derive and pass
required_tests from the already-held task bytes and wire the reviewed ending.
No verifier factory or new stage is added. Shared assembly paths are not seized
by W110772. W110935 already waits on W110772's shared worker bytes; retain that
edge. Existing schemas, Authority, attempts, intake, OCI, worker recipes and
general verifier code are outside this assignment. Record a concrete missing
interface before widening, not a speculative framework need.

Run focused changed suites and appropriate source/inventory gates once; retain
the exact failures and do not rerun unchanged broad evidence in this planning
turn. Independent review follows the complete candidate. No dependent gate is
released until the bounded correction and its actual custody proof are accepted.

## Coordination and evidence

Canonical open graph snapshot111751 contains no separate clean-verifier provider
Work or new provider dependency for W110772. W61981 remains the older parked
verification-context Work; it is not activated or repurposed. This reviewer had
created no provider under superseded owner111686, so none needs parking or
closing. Keep the deferred service proposal in the existing bound records.

evidence/planning-111746/baseline.json binds15 inspected source/test/doc paths;
the accepted worker/review-driver bytes and both previously failing real-custody
proofs remain unchanged. coordination.json retains the relevant graph projection.
No production/test changes, new Work/dependency, live runtime, image or credential
act occurred. Return this concrete proposal to ops for source/test assignment.
