# W130229 — existing public readers satisfy the component handoff

baton.tuner, claim140438. Under the owner's 2026-09-11T00:30:54Z ruling,
return an evidence-only disposition for independent review. The accepted
ordinary A/B fixture already obtains both terminal states and both actual
completion records through supported public readers. No source/test change,
new serving instance or repeated A/B execution is needed to reconcile it.
W119405 still owns joined acceptance; W71879 still owes real standalone execution.

## Exact input and retained execution

All43 entries in the accepted serving/R union match current bytes and modes.
The two allocated paths under v12/python remain:

| Path | SHA-256 | Bytes | Mode |
| --- | --- | ---: | --- |
| tools/stage_execution.py | 9cf2927f4057a68beec61cfd56abeca709509d7770cd577412f750bce4ae1223 | 213805 | 0664 |
| tests/tools/test_stage_execution.py | 2b234a605028d08952a11e2610753ab116a0ea969957399fecac8d55dbd1bffd | 404014 | 0664 |

Full manifest and retained-evidence hashes: evidence/claim-140438/result.json.
Source copies remain in ../finding-two-job-serving/evidence/review-140405/candidate/.
The accepted predecessor is ../finding-two-job-serving/review-2026-09-11T00-52-04Z.md.
R's independent acceptance is
baton:work/records/2026/09/finding-v12-line-rebase-after-target-advance/findings/finding-integration-result-composition/review-2026-09-11T00-40-24Z.md.
Its evidence/review-140320/independent-ab-and-binding.log records27 passing tests;
ancestry.json records the separate successful ancestry command. These are
retained independent executions, not executions by this claim.

## Consumer reads and their limits

The concrete witness is
TwoBoundJobsTraverseServingAndCorrection.test_BOTH_JOBS_REACH_TERMINAL_ON_ONE_TARGET
in the allocated test file. It uses these existing readers:

1. states_for calls baton_v12.job_manager.status on the already running
   composition, selects the exact job_id, then reads each stage's kind/state.
   It asserts integration completed for both job-a and job-b.
2. attempted reads stage_rows, selects job-a/integration or job-b/integration,
   reads live_of for that stage and combines them with attempting. The actual
   returned episode/attempt is retained for the completion lookup; no guessed
   attempt id, global Work or test-manufactured completion is supplied.
3. completion_of calls the existing composition's StageExecution.observe(attempt)
   and reads ['integration']['completion']. A reports its direct branch with
   result_id null and execution_runtime quiescent. B reports its own result_id,
   immutable source_proposal_id, separate derived proposal_id and entry_id,
   execution_runtime absent and runtime_id null. The witness checks released
   lease/fence and scheduler allocation against their public owners.

StageExecution.observe delegates to pooled observation and Integration.observe;
the latter reads Integration.account. The account correlates the immutable
attempt, bound worker/Work/target, fixed assignment, claimed offer, Authority
receipt/pass result and coordinator entry/lease. The reconciled account checks
configured post-import execution and absence of a competing runtime. These
reads reuse existing deployment handles. They are not a factory with only
read-only capabilities, and this handoff does not recommend constructing a
serving factory just to obtain them.

For separately invoked persisted status, the existing job_manager status
command with the actual Job store, authority UUID, incarnation and control
store uses _ReadOnly and no serving factory. It reports stored/canonical
state; without --observe it does not claim exchange or rich integration
completion evidence. Its state may lag the serving loop. This is a supporting
public surface established by current source inspection, not a new execution
or a substitute for the accepted detailed completion reads above.

No live fixture database or globally reusable attempt identifier is promised.
The retained fixture reconstructs its own identities per execution. Do not
reuse historical temporary paths as current deployment configuration.

## Explicitly unproved and deferred

StageObservation/observing_factory is a different, detached reader. Its
SimpleNamespace still lacks per-Job readers, allowing _bound's global fallback.
Its runtime-row/assignment early return also means model-free B, which has no
activated runtime, does not reach the result account. The current A/B witness
does not consume that detached path; it must not be advertised as equivalent
to StageExecution.observe or as a complete rich A/B observer.

These limitations remain indexed here under the owner's observation deferral.
If the actual standalone run requires that detached rich reader, return that
specific ordinary-consumer defect for correction under existing ownership;
do not select a wrong Job/target or invent missing completion. Broad observer,
foreign-handle, sidecar, database-byte/mode and restart matrices remain unproved.
This claim opened no database and makes no new owner/DB preservation assertion.
Historical preservation evidence remains ../../evidence/review-130139/verification.json
for its exact earlier fixture/candidate only.

Runtime/engine providers in the accepted witness are controlled. Authority
sessions, manager/coordinator ownership, content and configured causal/post-import
execution are real within that fixture. Actual standalone runtime/model judgment
must be demonstrated by W71879; none is inferred from component acceptance.

## Cost and next action

No changed tests/assertions, no runtime tests, no source delta. The continuity
check measured0.002420217999315355s; including0.1s outer reserve, observation
uses0.10242021799931536/20s. Campaign total383.35242021799934/450s retains
historical uncertainty and overruns. Reviewer carry4.52145815199789/5s remains
separate; serving4.63s, joined40s and margin2.12s are not transferred.
Static inspection and dossier work remain disclosed unmeasured activity.

Last independently demonstrated ordinary transition: B terminal integration
and capacity release, with both changes landed. No component observation
blocker remains for the selected public reads. Next action is independent
baton.bug assessment of this disposition, then W119405's existing joined
acceptance. The next real execution is the already planned W71879 freeze/run,
whose concrete deployment operands are still its owner's responsibility.
