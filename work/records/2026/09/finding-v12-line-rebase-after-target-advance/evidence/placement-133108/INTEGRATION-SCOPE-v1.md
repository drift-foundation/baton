# Proposed replacement scopes, disposition and verification

W131409 reviewer133017; owner direction M132985. Read INTEGRATION-CONTRACT-v1.md.
This is a NEW proposal, not execution authority. All paths below are repository
relative. Evidence/replacement-133017/base.json pins current bytes/modes or
planned absence. A later author must revalidate them and all accepted predecessor
bytes before edits. One serial writer, independent review between slices.

## Observed boundary and smallest proposed change

Current integration/admission.resolved_account requires original proposal.target
equal current Authority target (around246). driver.admit_accepted and
continue_accepted propagate that original proposal into queue, receipts and
completion. tools/integration_bundle._accepted_evidence independently resolves
the same original line/proposal, and worker/integration_workload.integrate checks
the target revision and exact original base/candidate path bytes before import.
Authority.core.integrate around2255 finally compares proposal.target to its
cursor and advances to proposal.candidate_digest. A one-line guard removal
would therefore both miss later refusals and conflate two different candidates.

Propose separate result custody and an ordinary derived Authority proposal,
keeping Authority/core/schema/API and producer/Job-round mechanics unchanged.
An integration-specific Git profile owns private reconciliation and the explicit
dedicated target revision reference. The final importer still imports only
independently approved bytes. This avoids teaching a generic manager Git or
making workers chase target revisions. Authority publication reuse is an
implementation-start revalidation gate; if its scoped API cannot express the
new publication, return an exact amendment before extending Authority.

Operational read notes: guessed paths v12/python/src/baton_v12/worker_manager/
integration_worker.py, v12/AGENTS.md and v12/python/AGENTS.md do not exist. They
were not silently treated as read; rg resolved the runtime port to
v12/python/tools/integration_worker.py and the workload to v12/worker/. Root
AGENTS.md is the supplied policy. No required assigned dossier is unreadable.

## D — exact disposition of superseded bytes

W132712 is parked at133013. Its eight rejected changed paths are fully retained
in review132898, with the later test edb9d44c retained in review132973. No cleanup
has happened. Propose explicit approval to restore these SIX existing paths
to their exact pre-A bytes/modes from evidence/contract-131466/base/:

- v12/python/src/baton_v12/checkpoint_profiles.py
- v12/python/src/baton_v12/worker_manager/attempts.py
- v12/python/src/baton_v12/worker_manager/review_cycles.py
- v12/python/src/baton_v12/worker_manager/schema.py
- v12/python/tests/manager/test_attempts.py
- v12/python/tests/manager/test_store.py

And remove only the TWO unaccepted new working-tree files after exact current
hash verification and retained-evidence verification:

- v12/python/src/baton_v12/worker_manager/target_rework.py
- v12/python/tests/manager/test_target_rework.py

This is filesystem candidate disposition only, never Git restore/reset/staging
or deletion of a dossier. It restores the pre-A ControlStore schema18 boundary;
no live schema19 store is opened, downgraded or migrated. Drift at any one path
refuses the whole disposition. Existing history, reviews, probes and all costs
remain permanent. Profile transplant algorithms may inform the new profile,
but rejected code is not inherited as certified functionality. The four review
defects become required negative/replay controls at their applicable new owners.

After independent disposition review, close A as superseded, not fixed. Old
B W132720 and C W132724 have no implementation and0s runtime; propose explicit
superseded closure of those contracts, preserving their permanent paths and
forwarding to the replacement children. Their old base-advance/triple-replacement
behavior is not part of the new design. Consumer two-terminal acceptance stays.

## P — original eligibility, separate result and causal evidence

Product source allowlist:

- v12/python/src/baton_v12/integration/reconciliation.py (new)
- v12/python/src/baton_v12/integration/git_profile.py (new; standalone profile
  primitives, no manager/Authority store capability in worker copy)
- v12/python/src/baton_v12/integration/schema.py
- v12/python/src/baton_v12/integration/store.py
- v12/python/src/baton_v12/integration/admission.py
- v12/python/src/baton_v12/integration/driver.py
- v12/python/src/baton_v12/integration/__init__.py

Tests:

- v12/python/tests/integration/test_reconciliation.py (new)
- v12/python/tests/integration/test_admission.py
- v12/python/tests/integration/test_driver.py
- v12/python/tests/integration/test_coordinator.py

Own schema5 typed custody/journal, source eligibility distinct from result
freshness, real private Git reconciliation, immutable causal observations,
independent combined-result evidence and scoped derived Authority publication.
Prove readers/cutpoints and result preparation with real repositories and a real
Authority/session in at least one focused path. The profile's target revision
mechanics are explicit typed capabilities, not ambient human-repository Git.

Required new named test groups in test_reconciliation: OriginalSubmissionIsImmutable,
CausalEvidenceSurvivesComposition, PreparedResultReplaysItsIntent,
ResultReadersRejectTampering, DerivedPublicationUsesItsOwnAssignment,
and ConflictsAndForeignSourcesHold. Include actual base-fail/isolated-pass/
combined-pass and combined-fail outputs, not canned owner answers. Existing
test_admission AcceptedAccount/RefusalBeforeMutation and test_driver
TheOrdinaryCommandTraversesPublicAdmission supply focused compatibility controls.
The implementation handoff lists exact selected test methods and measured logs.

## Q — authorized result through queue, importer and target settlement

Source allowlist:

- v12/python/src/baton_v12/integration/queue.py
- v12/python/src/baton_v12/integration/execution.py
- v12/python/src/baton_v12/integration/runtime.py
- v12/python/src/baton_v12/integration/recovery.py
- v12/python/src/baton_v12/integration/driver.py (serial extension of accepted P)
- v12/python/tools/integration_bundle.py
- v12/python/tools/integration_worker.py
- v12/worker/integration_contract.py
- v12/worker/integration_workload.py
- v12/worker/integration_entry.py
- v12/worker/Dockerfile.integration
- AGENTS.md (only a paragraph distinguishing the proposed v12 configured
  preparation capability from unchanged current v11 agent/Git/import permissions)

Tests:

- v12/python/tests/integration/test_execution.py
- v12/python/tests/integration/test_runtime.py
- v12/python/tests/integration/test_recovery.py
- v12/python/tests/integration/test_coordinator.py
- v12/python/tests/integration/test_driver.py
- v12/python/tests/tools/test_integration_bundle.py
- v12/python/tests/tools/test_integration_worker.py
- v12/python/tests/manager/test_integration_worker.py
- v12/python/tests/manager/test_integration_image.py

Own the new explicit result-account branch and bundle version, separate source/
result evidence, scoped profile publication into the dedicated target reference,
post-import tests/readback, unchanged exact lease/fence exclusion, and derived
Authority receipt before final release. Package only standalone profile code
needed by the worker; do not copy manager, store or Authority packages into it.
No image build, rollout or live provider call belongs to this verification.

Controls cover current result importing both changes, stale derived-result
refusal at enqueue and immediately before writes, missing/foreign source or
result review, independent reviewer enforcement, target path/object/mode drift,
reference CAS, post-import failure, and crash/replay between content/reference/
Authority/settlement. Reuse focused tests from TheGrantIsProvedAgainRIGHTBeforeTheModelWrites,
OnlyANOTSTARTEDAttemptIsAskedToRun, TheWholePathSetIsProvedBeforeAnyImport,
TheEndingIsConservative and existing recovery witnesses. Preserve direct import
and the literal v11 Git/agent restrictions. Exact new method names and selected
old controls belong in the author plan before running, not a module sweep.

## R — configured two-Job composition and completion provenance

Source:

- v12/python/tools/stage_execution.py
- v12/python/src/baton_v12/job_manager/delegation.py
- v12/README.md

Tests:

- v12/python/tests/tools/test_stage_execution.py
- v12/python/tests/job_manager/test_delegation.py
- v12/python/tests/job_manager/test_scheduling.py

Own pure factory preflight for named per-target profile/content and scoped
publisher/evidence sessions, ordinary integration-stage preparation and pending
evidence, result-specific runtime ports, and completion documents binding both
derived receipt and original submission. Read historical publication through
driver.publication_for_attempt, not retain_proposal against a later target.
Extend only the closed completion vocabulary in delegation; preserve its fixed
attempt/episode/runtime checks and accepted scheduler capacity release semantics.
No scheduler implementation edit or new producer/reviewer episodes is proposed.

Reuse TwoBoundJobsTraverseServingAndCorrection for actual A then B terminal
on one target, unchanged B original line/producer/review, all three causal
observations and separate combined-fail/conflict/target-race paths. Check /1 and
no-drift /2 plus pure preflight and read-only observation with bounded methods.
Retain candidate, full records and exact commands for W130224/W119405 independent
acceptance; do not rerun their whole campaign or close them by implication.

## New allocation request — no old remainder transferred

Old direction is stopped. Retained spend: author64.56s measured plus provisional
about8s unmeasured, reviewer0.286152s; total about72.846152s with uncertainty.
Old unused A/B/C/review allowances and10s reserve are not replacement authority.
The unapproved old68+8 correction request is superseded entirely.

Propose a NEW replacement tranche of260s, cumulative and serial:

| Slice | Implementation ceiling | Independent review ceiling | Total |
| --- | ---: | ---: | ---: |
| D exact disposition |8s|2s|10s|
| P custody/profile/evidence/publication |77s|8s|85s|
| Q queue/import/target settlement |95s|10s|105s|
| R ordinary composition/causal witness |40s|5s|45s|
| Owner-held contingency |15s|0s|15s|
| Replacement total |235s including contingency|25s|260s|

This adds260s authority for the NEW work; it neither resets historical spend
nor adds unused old allocations. Lifetime W131409 spending would be bounded by
the retained about72.846152s PLUS260s, about332.846152s with the old uncertainty
still explicit. W119405 and its carry/serving/observation/joined allocations are
separate, unchanged. Contingency requires an explicit owner reallocation.

Cost basis is a reviewer estimate, not a measured promise: D allows one focused
fresh-store/writer control; P allocates30s to custody/readers/cutpoints,20s to
real profile/causal evidence,17s to real publication/independence,10s to relevant
old guards; Q30s to account/bundle/runtime boundaries,35s to real import/revision/
verification,20s to failure/recovery,10s to old exclusions; R25s to ordinary
two-Job and causal controls,15s to preflight/no-drift/read-only/capacity controls.
All setup, failing attempts and necessary reruns count inside those ceilings.
No whole module/package/broad suite, live model, OCI build/run or benchmark.
Stop before a cap if acceptance is incomplete and return a concrete measured gap.
Unused slice/review time is not automatically reusable elsewhere.

## Decision and placement

Approve or amend BOTH versioned files, including exact rejected-byte disposition,
dedicated target reference authority, IntegrationStore schema5 fresh-store
boundary, derived ordinary Authority publication with independent evidence,
source/test/policy allowlists and new260s tranche. Standing W71830 grants test
change authority within accepted scope; it does not waive defect coverage.

After approval reviewer pins the ruling and creates separately bound P/Q/R
children with serial dependencies. D runs through the safely returned old A,
then independently reviewed disposition closes the superseded A/B/C contracts.
Replacement children keep new canonical paths; old dossiers are never renamed.
Dispatch D only, then each next slice only after exact candidate acceptance.
Parent remains open until all replacement children and consumer prerequisites
are satisfied. No implementation/cleanup/runtime is authorized by this proposal.
