# Observe each bound Job through read-only owners

Work W130229, parent W119405. Placement claim130209; owner M130205 approves
../../ALLOCATION-2026-09-09.md as written. Depends on independent W130224
serving acceptance, ../finding-two-job-serving/. Intended tuner implementation,
then independent baton.bug review, with shared-file ownership serialized.

## Confirmed defect

Read ../../FINDING.md, PLAN.md, PROGRESS.md and
../../review-2026-09-09T18-53-36Z.md; reproduction is
../../evidence/review-130139/probe.py and verification.json.
StageObservation.observe_integration creates a production SimpleNamespace with
no binding_for/jobs reader. _bound_id consequently returns None and _bound uses
global Work/target and the first integration worker. This is a real observation
path, not merely an integration test double.

Actual configured status over a held integration succeeds with /2 when both
global and Job target agree. Change only the global target while retaining the
correct bound target: status refuses operation-collision. All owner records and
four database bytes/modes remain unchanged. This demonstrates unavailable correct
per-Job status, not an observed write or cross-Job receipt acceptance.

## Scope and acceptance

Only v12/python/tools/stage_execution.py and
v12/python/tests/tools/test_stage_execution.py. Consume W130224's accepted
shared fixture, candidate and retained attempt identity. Compose pure shared
binding/allocated-worker readers into actual read-only observation; absent
StageDeployment methods must not authorize global fallback. Preserve /1 by its
actual schema and adapt test doubles under standing authority if needed.

Read both Jobs by their actual attempt, including the correct per-Job target
differing from the global field; reject foreign handles without writes. Keep
committed Authority/coordinator/manager provenance and owned completion checks.
Prove owner-record and database-byte/mode equality and that no writable factory,
session mint, serving, launch, finish, prepare or refresh operation is reached.
Use real read-only openers and retain their closure/refusal behavior. Existing
accepted read-only sidecar allowance remains; no new logging or observer feature.

The accepted status-hardening file may be reused read-only as fixture/evidence,
but is not an authorized edit path. No scheduler/provider/driver/registry change.

## Budget and handoff

Incremental20s charged to the one400s campaign cap carrying233s plus actual
predecessor use. Keep the untimed-run uncertainty and all measured carry; no
reset. Focused status controls, reuse unchanged /1 history; no broad repetition.
Standing W71830 test authority applies without a per-test gate.

Claim through baton.tune after W130224 acceptance, revalidate exact accepted
input, and return to baton.bug with full hashes/modes, assertion inventory,
actual read-only evidence and cumulative time. W119405 owns final joined review.

## 2026-09-11T00:40:24Z — owner acceptance applied

Owner M140286/M140288 in T133129 and baton:work/records/2026/09/finding-v12-standalone-multi-job-pipeline/FINDING.md / PLAN.md at 2026-09-11T00:30:54Z govern. This explicitly supersedes older mandatory, essential and no-waiver wording below ONLY where it makes stronger robustness/resilience demonstrations prerequisites. Ordinary correctness, authorization, honest evidence, existing source scopes, cumulative budgets and file ownership remain. Deferred claims are unproved, never passed. No new planning Work or approval round is required.

Narrow the existing W130224 -> observation -> W119405 handoff to the status/evidence the ordinary A/B demonstration actually consumes. First reuse the accepted public Job/stage/completion readers and retained A/B identities. If those suffice, record evidence reconciliation and disposition without inventing an observation implementation campaign. If the actual configured status reader is needed and still falls back to the wrong global binding, correct that real defect within the existing stage_execution.py/test_stage_execution.py scope and20s allocation, then independently verify those actual A/B reads.

Deferred indexed observation claims: general standalone observer redesign; global-target perturbation and foreign-handle permutations not exercised by the chosen A/B deployment; exhaustive capability-reachability, database-byte/mode/sidecar, restart and multi-layout matrices. Revisit after feasibility, when broader observation guarantees or a concrete consumer requires them. These remain unproved beyond retained existing evidence. Do not deliberately select a wrong Job/target, mint writable authority, fabricate completion, or claim a reader is read-only without its actual supported provenance. The known SimpleNamespace/global fallback is not erased; it is an immediate correction only if it prevents or falsifies the actual demo's required observation.


## 2026-09-11T00:59Z — public-reader disposition, baton.tuner claim140438

Revalidated the narrowed owner ruling against the accepted current serving/R
candidate and the actual A/B witness. The required component evidence already
uses public per-Job status and per-attempt StageExecution.observe; no separate
observation implementation is needed for that consumer. This explicitly
supersedes the historical unconditional repair requirement for this handoff,
not the recorded defect. PLAN and OBSERVATION-HANDOFF-2026-09-11.md carry the
current evidence-only disposition for independent baton.bug review.

Confirmed by static inspection: StageObservation's production SimpleNamespace
still lacks per-Job readers. Its early runtime-row/assignment return also
prevents reading the model-free B completion through that detached surface.
These limits are not fixed, passed or concealed. The accepted A/B witness uses
the already running StageExecution, whose account selects the actual attempt
and bound Job through committed owners. It does not instantiate serving as a
status workaround. No new raw-store read or protocol bypass was used here.
If the standalone consumer needs detached rich status, that concrete need
reactivates correction; general detached-reader and robustness claims remain
indexed deferrals under the owner's ruling.

evidence/claim-140438/result.json records the
unchanged43-entry union and hashes retained independent R evidence. No product
source/test/assertion changes, runtime tests, live database opens or new database
byte/mode guarantees. The detailed handoff distinguishes controlled providers,
actual owned receipts/completion and the still-unexecuted standalone W71879 run.
Observation charge0.10242021799931536/20s raises the campaign carry to
383.35242021799934/450s plus historical uncertainty; separate reviewer carry
4.52145815199789/5s is unchanged. No allocation transfer or budget reset.

## 2026-09-11T01:05:51Z — independent disposition accepted

Reviewer claim140487 accepts the narrowed public-reader handoff in
review-2026-09-11T01-05-51Z.md, superseding awaiting-review status. Independent
43-entry continuity and retained R evidence hashes pass with no source/test
delta. No runtime or database tests repeated. Reviewer cumulative is now
4.623840369998892/5s; campaign author carry remains383.35242021799934/450s
plus all uncertainty. Existing allocation boundaries remain.

The detached global-binding and model-free completion limitations stay
unresolved. Their follow-on custody is explicitly indexed as H-7 in
baton:work/records/2026/09/finding-v12-integration-result-hardening/FINDING.md
and PLAN.md, parked W136578. This replaces W130229 as the future hardening
owner, without moving this permanent record or adding a milestone dependency.
Actual required standalone-reader failure is immediate bounded correction;
broader observation guarantees remain deferred and unproved. Close W130229's
selected-reader disposition satisfying; existing W119405 joined review is next.
