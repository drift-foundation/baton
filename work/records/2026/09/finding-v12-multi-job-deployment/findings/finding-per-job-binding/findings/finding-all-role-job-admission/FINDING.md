# Validate every Job role before worker allocation

Work W130216, parent W119405. Created by baton.codex under placement claim130209
from owner M130205 approving ../../ALLOCATION-2026-09-09.md as written.

## Confirmed baseline and boundary

Read ../../FINDING.md, ../../PLAN.md, ../../PROGRESS.md and
../../review-2026-09-09T18-53-36Z.md. Exact input is retained under
../../evidence/review-130139/candidate/ (relative v12/python):
- tools/stage_execution.py: 6c9007ba241fce41f63c3bae1d93dd37b0ee5bf351b48c9ba1fe843e7ef38550
- tests/tools/test_stage_execution.py: 714a49b1ccf82e998b903131231beb4d18c02f8cbe2a5c52dbb54bd0fed3487a
Both0664, revalidated at placement.

_job_eligibility applies worker compatibility/exclusions only to implementation.
Public submit/attempt/admit for Job-B review reserves review-worker configured
for Work A before single_worker refuses; no canonical offer exists but capacity
remains reserved. Unknown-Job first admission now correctly refuses before both.
Reproduction: ../../evidence/review-130139/probe.py and verification.json.

Own the configuration/Job/stage correspondence and admission boundary, within
v12/python/tools/stage_execution.py and v12/python/tests/tools/test_stage_execution.py
only. Reuse PooledManagerOperations independence(stage), scheduler exclusions,
public job_of/allocation readers and single_worker held validation. Do not change
scheduler, provider, drivers, registry or another owner's test/progress file.

## Acceptance

Build a coherent two-Job fixture: distinct real Authority Works, correctly
derived held input manifests/tasks, and matching deployments for every role.
Public admission selects compatible implementation, review and integration
workers; unknown/cross-Job and wrong input/Work/profile/policy reach no wrong
allocation or offer. Measure public allocation/receipt evidence and retain setup
controls. Prove an unrelated fault cannot consume the successful Jobs' needed
capacity and retain principal independence/capacity rules.

Keep source_worker_id, required-test producer and actual allocation coherent.
Revalidate already-recorded allocation identity on reconstruction, where a
new-reservation callback is bypassed. Scope the integrator to the actual configured
profile/session actor if needed; do not imply a new multi-integrator provider.

This child's independently acceptable result is correct admission and its shared
fixture. Actual endings/traversal/correction and read-only status belong to serial
successors; final W119405 still requires their joined acceptance.

## Budget and handoff

Incremental30s, charged to the single owner-approved400s W119405 campaign cap.
Prior planning charge233s retains the untimed-run uncertainty; no reset. Record
each run and cumulative carry for the next child. Focused controls first; no
repeated unchanged broad suite. Existing5s reviewer probe cap is separate,
0.890647s used. Standing W71830 test authority applies without per-test gates.
Implementation claims through baton.impl and returns to baton.bug with exact
file hashes/modes, changed assertion inventory, logs and retained fixture locator.

## 2026-09-09T19:20:19Z — independent review, incomplete admission

Confirmed under claim130339; review-2026-09-09T19-20-19Z.md binds the exact
candidate and evidence/review-130339/ retains it and a public-interface probe.
All-role pre-reserve filtering improves A implementation, B review and A
integration; wrong input/policy/profile controls leave no allocation or offer.
B integration still has no compatible worker. The author's assertion that this
cut owes only that refusal is superseded as an acceptance interpretation:
owner M130205's positive A/B integration admission remains required. The
single-actor capacity constraint is confirmed; the necessity of a new provider
is not established. Investigate per-Job held operations under one allocated
integration worker through existing assembly seams before proposing expansion.

The new receipt assertions query the wrong owner and the reconstruction test
fabricates an allocation with SQL. Correct these under standing test authority;
no per-test approval gate. Review includes exact changes and expected evidence.

Implementation allocation30s is exhausted (about30.65s, uncertainty retained).
The review proposes admission45s/serving75s, preserving the400s campaign total
and all other allocations. This reallocation is OPEN for the owner; no further
implementation test runtime is granted by this finding. Current action is the
PLAN's owner decision, not successor dispatch.

## 2026-09-09T21:01:09Z — owner approves correction allocation

Owner baton.slaw return event130903, following claim130902, approves the exact
proposal in review-2026-09-09T19-20-19Z.md: transfer15s from W130224 to W130216,
yielding admission45/serving75/observation20/joined27 within the unchanged400s
campaign total. This explicitly supersedes the original30s child allocation
and the pending-owner/no-further-runtime statements above. Existing charges,
overrun and uncertainty remain: this child used about30.65s, leaving about14.35s;
campaign carry is about263.65/400s. Reviewer probe carry remains1.890647/5s.

Both authorized paths, one integration actor/capacity identity and every
acceptance requirement are preserved. Focused verification only; no repeated
full-module run. If existing public seams cannot support the result, return an
exact prerequisite before expanding scope. The candidate remains unaccepted
and successors remain gated. Standing W71830 test authority covers the reviewed
test/fixture corrections without another per-test decision.

Placement claim130905 revalidated source c4d6231838137e5fa66ee6768ab36d0bbcc112bb4327160d7f166e53c1127ba3
and test26ada3518b406937e492a4a8da9e63c351ac40a3e53bb3192ad6778ab12b4012,
both0664, against the retained review candidate. No product/test change or test
run during placement. The child PLAN, parent FINDING/PLAN/allocation and serving
FINDING/PLAN carry this ruling before dispatch to baton.impl.

## 2026-09-09T21:23:01Z — implementation pins the per-Job integration operand set

claim130926, baton.claude. The reviewed candidate was revalidated byte-identical
before any edit: tools/stage_execution.py
c4d6231838137e5fa66ee6768ab36d0bbcc112bb4327160d7f166e53c1127ba3 and
tests/tools/test_stage_execution.py
26ada3518b406937e492a4a8da9e63c351ac40a3e53bb3192ad6778ab12b4012, both 0664.

**The selected repair for [P1], investigated through existing seams first.**
ONE integration capacity identity and ONE configured actor are preserved
exactly. The pool still carries a single integration worker, so two Jobs'
integration stages serialize over that one worker's capacity and
`scheduler.own_pool`'s one-participant rule is untouched; no second integrator,
actor, provider, driver or session capability is introduced.

What becomes per Job is the HELD OPERAND SET the one worker serves a stage
under. `single_worker.worker_operations` is composed once per bound Job from
the configured integration worker's own deployment with its `input_manifest`
taken from that Job's bound `source_worker_id` producer -- the same producer
identity `Integration.required_tests` already derives the required-test
selection from, and the same manifest `_correspondent` compares the Job's own
input digest against. `_PerJobIntegration` selects among those operations by
the stage's own `job_id`, and `_job_workers` derives compatibility from the
same `_served_deployment`, so admission and the provider read one document.

**What is deliberately NOT derived.** Participant, principal, profile name,
profile digest and policy digest stay the one configured deployment fact.
Substituting a policy or a profile for a Job would be this assembly quietly
choosing a security operand; a Job whose policy or profile the configured
integrator does not carry is still refused before anything is reserved, naming
which operand disagreed. The one-Job `/1` document derives nothing at all: it
names its Work once, globally, and its integration worker's own document is
that fact.

**Supersession.** The predecessor's statement that a second Job's integration
stage is a permanent reported boundary (2026-09-09T19:20:19Z review [P1], and
the author's `test_the_second_jobs_integration_stage_is_a_reported_boundary`)
is superseded: the boundary was the configured operand set, not the capacity,
and the existing public seams express the correction. The measured constraints
themselves stand -- one participant per pool worker, one configured
`integrator_participant` -- and are now the reason the operands are per Job
rather than the workers.

**[P2] evidence corrections.** Canonical admit receipts are read at their own
owner through `canonical_operation`/`receipt_of` with positive controls;
allocations are read through `scheduler.allocation_of` on the live episode's
actual attempt; the fault-capacity control measures the REVIEW worker the
incompatible review stage actually threatened; and reconstruction is proved by
recomposing the deployment over the same durable stores after a real
admission, with no fabricated protocol state. No private SQL remains in the
cases this child owns.

## 2026-09-09T21:26:48Z — independent admission acceptance

Accepted under claim131028; review-2026-09-09T21-26-48Z.md and
evidence/review-131028/ bind source5f8de127/test74d33e45, both0664.
The prior P1/P2 changes-required state is superseded for this candidate:
both Jobs admit all three roles with correct allocations and canonical receipts;
wrong input/policy/profile/digest/Work and unknown Job refuse before both;
capacity and public reconstruction controls pass. A/B integration uses one
configured actor/worker with per-Job manifests derived through existing seams.

This is admission acceptance only. Actual traversal/correction belongs to
W130224, read-only observation to W130229, and final joined acceptance to W119405.
The focused evidence is sufficient here; no new full-module requirement or budget
gate. Author total about42.74/45s; campaign275.74/400s with uncertainty retained.
Reviewer probes4.391688829/5s. Provider203-total/83-remaining counts are stale;
static local-class count is206 and the review explains the evidence limits.
