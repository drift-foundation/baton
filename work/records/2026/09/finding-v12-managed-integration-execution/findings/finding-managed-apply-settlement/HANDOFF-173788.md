# W170385 complete candidate for independent review

2026-09-15T02:12:35.671127+00:00 — baton.tuner, serial implementing claim173788.

Candidate: baton:work/records/2026/09/finding-v12-managed-integration-execution/findings/finding-managed-apply-settlement/candidate-173788.json
SHA256 `0a1d0a4addc88d83bc9fd580dc216ca47110a0cb8a8ef53da101715ed2ff144d`.
Patch SHA256 `611c2fcd1a64776bb344bf64c3a245eb5e8732a6ef811590ad602681ebf709b3`. This is the complete author proposal,
not independent acceptance. Return baton.feat with set-next=baton.feat. W170387
and parent W161230 remain open and gated for their own acceptance.

## Authority and provenance

SLICE3-SCOPE-172905.md (owner172982), producer amendment172988
(owner173126), and scheduler amendment173130 with review00:40:22Z
(owner173785) bind this implementation. Their exact SHA256 values are in the
candidate. This supersedes incomplete partial172988/173130 as the review target;
those checkpoints and their failed evidence remain historical.

The manifest enumerates all31 selected paths and21 actual changed paths. Each
has fresh current candidate_path and SHA256, target mode, earliest applicable
base_path/base SHA256, and changed flag. Original28 use baseline172988; producer
paths use baseline173130; scheduler uses baseline173788. New test_managed_apply
has no original base. Every baseline snapshot was checked against its original
manifest. Candidate files/patch are immutable custody copies, whose0444 modes
are NOT target checkout modes. Current target bytes/modes match the manifest;
all target files are non-symlink regular files and owner-writable. No Git index,
branch, commit or history mutation occurred. No prior locator fields were copied
into the current manifest. Ten selected paths are unchanged.

## Implemented behavior and finite evidence

1. `AnOrdinaryManagedIntegration.test_preparation_judgments_apply_and_target_settle`
   traverses real ordinary preparation, retained exact Git objects, actual parent
   offer/claim, derived publication, three actual independent JudgmentExecution
   receipts, admitted real worker apply, freeze/intake/retention and destroyed
   runtime. Actual local target/ref and receipt transaction, Authority receipt,
   lease release, fenced parent handoff/gate discharge and root release follow.
   It asserts target harness bytes and the actual projection gate owner over the
   resulting integration state. This gate test does not claim a second full Job
   traversal; the broad two-Job matrix remains deferred.
2. `test_reopen_after_retained_adoption` and
   `test_reopen_after_derived_publication` close ordinary handles and recompose
   against durable stores. One preparation, stable derived result/proposal and
   judgment identities, three judgments and one apply are retained.
3. `test_reopen_after_target_effect_before_coordinator_settlement` loses the
   actual transaction reply, recovers its Git receipt without another CAS,
   completes, then reopens AGAIN and proves the same final Authority receipt.
   `test_reopen_after_authority_receipt_before_final_handoff` covers the later
   committed-receipt cut. Actual target effect count remains one.
4. Missing/nonaccepting actual judgment reports and changed collection mapping
   prevent apply. `test_a_grant_withdrawn_after_admission_prevents_start` and
   `test_target_drift_after_admission_prevents_start` exercise actual withdrawal
   or foreign target movement after admission, before start. Existing placement
   negatives retain stale fence/foreign result/changed target/custody guards.
5. Known failed preparation start ends actual cleanup, cancels planned apply,
   releases capacity and projects exceptional with no parent claim/runtime.
   Its gate is closed. `test_a_failed_apply_is_collected_and_settles_without_a_target_effect`
   runs a real harness returning7; it retains output, destroys its actual runtime,
   refuses its own entry/releases the lease, and settles exceptional without any
   target publication/Authority integration receipt. Repeated sweeps start no
   new apply. `test_reopen_after_failed_outcome_before_root_release` and
   `test_failed_preparation_resumes_after_admission_is_closed` prove continuation
   after the durable outcome or root-close cut.
6. Group2 unknown-start/manual recovery is reused and rerun across reopen in
   step46. The known simulated worker remains alive until fixture cleanup, as
   expected for a product manual hold. The unknown-target test blocks its actual
   queue target, retains live lease/root, carries publication/result/attempt IDs
   and manual next action, and performs no second CAS across reopen.
7. `test_original_job_limit_times_out_the_managed_apply` carries the original
   Job's one-second override into actual worker command execution, retained
   measured signal status and final failure. The report binds command, harness,
   candidate and bound; host merge/harness traps are positively exercised and
   remain unreached during apply. Metadata/object materialization and target
   publication are distinct from candidate execution.
8. Step46 passes295 bounded tests across these cases, retained preparation,
   managed contracts/storage, actual entry, placement negatives, legacy managed
   observation refusals, uniqueness, independent authorization and capacity
   guards. Quarantine works with pending roots including an ended episode;
   ordinary allocations still release. The scheduler atomic release guard and
   direct refusals remain authoritative.

## Verification and limits

Exact supervised argv, output logs and SHA256 values for all48 author runs are
in the manifest and ledger-170385.json. Final step46:295 PASS in
42.54792138101766s.
Step47:3 PASS in 6.58383864001371s
for strengthened completed-reopen/failure-gate assertions.
Step48:2 PASS in 4.805618615995627s
for failed-preparation root-close continuation and ordinary success after that
last narrow source change. No broad repeated discovery was run.

This claim measured143.404962850007s; cumulative author
221.86740775805083s. Prior reviewer1.8941418880131096s stays separate.
All48 supervisor groups are proved gone, with no supervisor timeout or signal.
The worker-command deadline case's own TERM is intentional product evidence.
Python3.13.7/jsonschema4.26.0 are the pinned local interpreter/dependency.
The repository diff check reports only pre-existing stage_execution.py:1923
whitespace; the complete candidate delta adds none.

Every failed run is preserved. Step31 updated-release expectation and fixture
policy mutation; step34 fixture supplied a harness later replaced by its normal
implementation turn; step36 wrong resultManifest field spelling; steps38/39
negative signal status could not be serialized by the existing nonnegative JSON
contract; step41 expected refusal wording; step42 publication-only fixture needed
an explicit dedicated target; step45 foreign-movement fixture needed its commit
objects first. Corrections and subsequent passing evidence are recorded; none of
these failed runs is relabelled as a pass. Earlier step29/reviewer scheduler
failure is resolved by the selected amendment, not omitted from acceptance.

Known-failure logical release does not assert removal of Authority gates or a
successful parent handoff. Unknown status/start/effect remains explicit/manual;
no invented report, automatic uncertain-effect repair, extra CAS, rollback,
live OCI/model, remote backend, image build/install or broad v13 campaign is
claimed. DEPLOYMENT-DRAFT-173788.md is local guidance for group4; main deployment
documentation remains owner-controlled. Independent review/acceptance is owed.

## Changed paths

- baton:v12/python/tools/integration_bundle.py
- baton:v12/python/tools/integration_worker.py
- baton:v12/python/tools/stage_execution.py
- baton:v12/python/tools/integration_placement.py
- baton:v12/python/src/baton_v12/integration/managed_execution.py
- baton:v12/python/src/baton_v12/integration/reconciliation.py
- baton:v12/python/src/baton_v12/integration/execution.py
- baton:v12/python/src/baton_v12/integration/git_profile.py
- baton:v12/python/src/baton_v12/job_manager/integration_capacity.py
- baton:v12/python/src/baton_v12/job_manager/delegation.py
- baton:v12/python/src/baton_v12/job_manager/projection.py
- baton:v12/worker/integration_contract.py
- baton:v12/worker/integration_workload.py
- baton:v12/worker/integration_entry.py
- baton:v12/python/tests/tools/test_managed_apply.py
- baton:v12/python/tests/tools/test_managed_preparation.py
- baton:v12/python/tests/integration/test_managed_storage.py
- baton:v12/python/tests/job_manager/test_managed_integration_capacity.py
- baton:v12/worker/reconciliation_task.py
- baton:v12/worker/reconciliation_entry.py
- baton:v12/python/src/baton_v12/job_manager/scheduler.py

Existing test changes are test_managed_preparation.py (selected continuation and
known-failure final expectations), test_managed_storage.py (managed retained
objects/custody representation), and test_managed_integration_capacity.py
(automatic release precheck while retaining direct refusal/quarantine).
New test_managed_apply.py carries the finite actual composition. Standing test
change authority applies; no unrelated test paths or genuine defect coverage
were removed.
