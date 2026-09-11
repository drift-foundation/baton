# Accepted per-Job composition for W119400

W119405 reviewer140519; review-2026-09-11T01-10-44Z.md is the joined acceptance.
evidence/review-140519/result.json binds the unchanged43-entry R140229 union.
Shared candidate copies remain in findings/finding-two-job-serving/evidence/
review-140405/candidate/. Source9cf2927f/test2b234a60, both0664; full hashes in
the review and manifest. No source/test edits or runtime execution in this handoff.

## Configuration and consumer contract

Use the accepted baton.v12.stage-execution-deployment/2 document: workers are
{worker_id, role, deployment}, with explicit identity and independent principals.
Each job_bindings entry carries job_id, job_work_id, review_work_id,
line_declared_base, canonical_target_id and source_worker_id. Implementation and
review share that Job's Work; different Works select different persistent lines.
The held producer task, manifest digest and declared base agree. The scheduler
owns allocation/independence/capacity; no list-position selection or manual line
choice. One configured integration actor serves per-Job operands serially.

The accepted integration-result consumer additionally configures integration_target
(dedicated repository), integration_workspace (distinct preparation storage),
integration_observer (actual execution participant, separate from integrator and
judges), and integration_target_reference. Preserve the actual required-test argv
from each producer task and distinct original/derived authorization. The exact
configured fixture is TwoBoundJobsTraverseServingAndCorrection in
v12/python/tests/tools/test_stage_execution.py; its
test_BOTH_JOBS_REACH_TERMINAL_ON_ONE_TARGET selector identifies retained execution,
not an instruction to rerun it at every parent. Context was v12/python with
PYTHONPATH=src:tools. Fresh standalone identities/paths must come from that run's
owners; historical temporary fixtures are not deployable operands.

Read status by exact job_id, then stage_rows/live_of/attempting for its real
attempt. The running StageExecution.observe yields integration.completion.
Direct A has result_id null and quiescent runtime; reconciled B has its own
source/derived/result/entry identities and absent runtime. Do not fabricate a
runtime, borrow A completion or construct serving solely to obtain status.
Detached StageObservation is not equivalent; its two known gaps remain W136578 H-7.

## Evidence map

- Pool: ../finding-multi-worker-pool/review-2026-09-09T18-17-21Z.md.
- Admission/reconstruction: findings/finding-all-role-job-admission/review-2026-09-09T21-26-48Z.md;
  retained allocation/receipt identity, not successful duplicate bearer issuance.
- Serving/correction/overlap: findings/finding-two-job-serving/review-2026-09-11T00-52-04Z.md.
- Required public observation: findings/finding-per-job-readonly-observation/review-2026-09-11T01-05-51Z.md
  and OBSERVATION-HANDOFF-2026-09-11.md there.
- Integration custody/import/causal/terminal evidence:
  baton:work/records/2026/09/finding-v12-line-rebase-after-target-advance/CONSUMER-HANDOFF-2026-09-11.md;
  R review-2026-09-11T00-40-24Z.md and evidence/review-140320/ retain the final
  independent27-test result and separate ancestry exit0 witness.

These are actual owned component operations with controlled runtime/engine
providers. W71879 still owes legitimate standalone runtime/model judgments and
completion. Fault-C and stronger resilience demonstrations are deferred, never
passed. No new planning prerequisite, manual repair or demo-only bypass.

## Cost and action

Reviewer cumulative4.750571445997288/5s; campaign author383.35242021799934/450s
plus all historical uncertainty. Joined40s unused; observation used0.10242021799931536/20s.
Unused serving4.63s and margin2.12s remain untransferred. Predecessor/prerequisite
budgets, failed runs and overruns stay separately attributed. No budget reset.

W119400 now consumes this joined result and the accepted pool evidence, then
supplies the concrete configuration/evidence to W103068 and the existing W71879
freeze/run. No repeated component campaign solely to restate this acceptance.
Last successful ordinary transition is B terminal integration/capacity release;
no W119405 blocker remains. The actual standalone run is still outstanding.
