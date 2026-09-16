# Operator-designated replacement: concrete v12 design

Author: baton.tuner, W174357 claim174470, 2026-09-15.
Status: **proposed for owner selection; no implementation or independent acceptance**.

## Recommended decision

Add a small, journalled **replacement designation in the Job store**, composed
with existing configured workers and ordinary admission. Keep the source binding
as the source binding; record separately which real worker is authorized to
execute a Job role. A designation remains active until an explicit revocation.
It selects exactly one worker, with no automatic fallback when that worker is
busy or unavailable. Existing allocations keep their original owner and operands.

Use explicit, enumerated Job/Work/role scope for v12. An operator can designate
the same replacement for several listed Jobs in one atomic request. Do not add
wildcard project inheritance, replacement chains, expiry timers, availability
scoring, priority or shared-slot scheduling. A Job submitted later is covered
only after it is explicitly included. This is a concrete proposed scope for the
already-required capability, not a claim that the owner selected these APIs.

Configuration-only replacement is useful in a narrow case but does not meet the
whole requirement. A fresh deployment can nominate another source worker with
matching Work, input, policy and profile, and the pool records real identities.
That proves a possible legal composition, not durable authorization for an
existing Job, designated-only admission, safe revocation or changed-provider
manifest provenance. The smallest missing relation is between those existing
owners; a second worker identity system or new coordination authority is not
needed. Implement it locally in v12; v11 remains the Work coordination authority.

## Authority and evidence read

The selected requirement is W103525 FINDING's 2026-09-13T14:22:47Z ruling and
SELECTED-PLAN-161345.md, accepted by owner M161420. Automatic fallback is not the
requested replacement behavior; W71877's accepted soft affinity remains valid
for ordinary undesignated work. Required healthy context reuse remains W161234's
separate outcome. Dedicated capacity is selected; priority/shared-slot/random/
stress/TUI expansion remains deferred.

Read the original FINDING and PLAN, complete SELECTED-PLAN, the current
consolidation/selection-to-design event and discussion window through M174368,
and this Work's complete events/thread through M174369. W103525 detail174473
is parked, no handler, with closed W71830 and an open W2 dependent. Neither its
state nor the release graph changes here. Historical bulk event output exceeded
the display bound; the complete current handoff/selection window was reread
explicitly after161193. No claim of rereading every historical run handoff is made.

Accepted advisory W174052 PREWORK.md is decision support. Its evidence is not a
fresh scheduling certification. Its inference from reserve's absent operand
alone is insufficient; the source composition below supplies the stronger,
bounded reason for recommending an extension. W174289 DESIGN.md is also a
proposal: compare its context boundaries without assuming adoption or blocking
this design on its disposition.

### Observed source and read test bodies

Paths in this table are under baton:v12/python/ unless stated otherwise.
These are static observations, not new executed behavior.

| Owner / exact symbol | Observed support and limit |
| --- | --- |
| src/baton_v12/job_manager/scheduler.py:own_pool, activate_pool | Closed pool/1 document; immutable generations, resolved principals, journalled activation. Returning to an old variant creates a new generation. No authorizer, per-Job designation or revocation field. The variant label is not authorization. |
| scheduler.py:reserve, _exclusions | Exact stage profile/kind match; actual worker/principal occupancy; review excludes every recorded implementation worker/participant/principal for that Job. Soft affinity selects another available eligible worker. Existing allocation is returned before fresh selection. |
| scheduler.py:_required_workers, PooledManagerOperations | Active and live prior-generation operations are required and their principals revalidated. _worker selects by allocation generation/worker. Changing configuration does not transfer a live assignment. |
| tools/stage_execution.py:held_configuration, _held_bindings, _resolved, _pool_generation | Validates configured workers, one source worker per Job, same implementation/review Work, actual Authority principals and prospective pool generation. Generation validation is construction-time; it is not a per-reservation designation fence. |
| StageDeployment.binding_for, source_for, line_for | Binding is read from the held configuration. Source comes from source_worker_id; create_line binds the persistent line to Authority/Work, nominated source and declared base. Source worker identity must not be globally aliased. |
| StageDeployment.worker_for, publication_for | Execution follows the actual allocation; publication follows the actual producer's assignment participant. Replacement must retain both facts through final output. |
| _job_workers, _job_eligibility, _served_deployment, _disagreements | Work/input/policy/profile checks apply before allocation; implementation additionally requires source_worker_id. Only integration currently derives per-Job input/task operands. Editing the source-worker filter alone is inadequate. |
| tools/stage_execution.py:operations_from | Composes operations keyed only by the newly active generation, whereas pooled attachment requires live old generations too. Do not describe arbitrary live pool replacement as already supported by this assembly. |
| tools/single_worker.py:_held | Input manifest binds runtime profile, worker image, policy, Authority and assignment contract. Switching provider/image may change the manifest digest even with identical task/source bytes. |
| src/baton_v12/job_manager/submission.py:submit, job_execution_context | Submission is immutable/idempotent; changed intent collides. Existing job_execution_context already distinguishes original Job input/policy from runtime input/policy and preserves original limits. Reuse that distinction, not a new budget owner. |
| src/baton_v12/job_manager/delegation.py:stage_intent, check_binding, ManagerOperations | Current delegated intent binds original Job input/policy and stage profile. The new effective execution binding must enter this owner and its replay comparison explicitly; passing an altered dictionary around the check is not an implementation. |
| src/baton_v12/job_manager/episodes.py:restart_abandoned_correction, open_next | Reads cross-bound abandonment/fence/positive runtime absence/restoration/exclusion proofs, ends only the old episode, and leaves one ordinary successor to sweep. A declaration or offline label alone is insufficient. |
| src/baton_v12/worker_manager/review_cycles.py:restore_abandoned_correction | Existing line restoration/excluded-writer evidence is the recovery prerequisite, not permission to move a running checkout. |
| tools/job_manager.py:main | Existing submit/status/serve tool consumes trusted operations factories; it does not mint operator authority. Do not claim a replacement command exists today. |

Read test bodies, not just names:

- tests/job_manager/test_scheduling.py:SelectionAndSettlement.test_affinity_is_soft_and_fallback_does_not_rewrite_it
  reserves/releases, occupies the preferred worker, then observes fallback and
  unchanged stored preference. Preserve that ordinary behavior.
- PoolDocuments.test_reattachment_revalidates_principals_and_does_not_rewrite
  rejects changed resolved principal; activation-generation tests preserve rows.
- test_returning_to_a_historical_variant_is_a_new_generation and
  test_the_active_generation_survives_a_reopen prove generation3, not reactivation
  of generation1. They use the scheduler owner, not full serving replacement.
- test_live_allocation_keeps_its_generation_after_pool_change attaches both
  generations explicitly and claims old/new through distinct stubs. This proves
  the pooled API can retain old owners; it does not prove operations_from builds
  those two sets or executes the replacement workload.
- tests/tools/test_stage_execution.py:test_reconstruction_reattaches_the_same_pool
  reconstructs unchanged configuration and remains generation1. It is not a
  changed-provider replacement test.
- test_a_source_worker_this_deployment_does_not_configure_is_refused and the
  adjacent duplicate-binding, different-review-Work and legacy one-Job cases
  enforce the source/Work boundaries that the design must preserve.

W103525 review-2026-09-13T14-10-03Z.md independently accepts four terminal imports
in each of two orders and the exact18-schedule audit at its stated boundaries.
It explicitly does not freshly execute every exported method. Its later owner
supersessions make context reuse/replacement required, not optional. Nothing in
this design reruns or enlarges that evidence.

## Why a configuration revision alone is insufficient

1. **Restricted success case:** with no existing allocation, same input/profile,
   valid actual routes and grants, a new configuration can name Jane as the
   source_worker_id. This is a valid candidate composition, not a universal
   impossibility claim. It must preserve the exact nominated repository/base.
2. **Missing durable scope:** pool activation records workers and principals,
   not that operator O authorized Jane to cover Chris for Job A implementation.
   Two configurations with different Job bindings may yield the same pool
   digest. A free-text variant cannot bind the source/input decision to admission.
3. **Changed provider:** _held pins image/profile into the input manifest, while
   _disagreements and stage_intent bind submitted digests. Merely changing the
   configured worker cannot authorize a different runtime manifest for an
   already-submitted Job; resubmitting changed bytes under its ID collides.
4. **Revocation and races:** a long-lived composer holds old configuration.
   Checking its generation only at construction does not make a later operator
   revocation authoritative at reservation. A live relation must be read under
   the same lock that chooses the worker.
5. **Old execution:** reserve replays an existing allocation, and full serving
   does not construct old-generation providers on arbitrary pool changes. A
   config edit cannot mean that old runtime has ended or that its credentials,
   session, source and publication identity now belong to Jane.

Extending only pool_generations.document with designation text still needs a
Job-bound admission reader, authorizer and allocation binding. Keeping that
relation in its own small owner avoids treating every designation/revocation
as a pool-generation change requiring all live providers to be recomposed.

## Proposed durable record and APIs

All names below are proposals, not existing callable APIs. Add
src/baton_v12/job_manager/replacements.py and two additive Job-store relations:

- replacement_revisions: immutable document plus digest, operation identity,
  predecessor revision, action designate/revoke, recorded time, operator audit
  and the exact enumerated scope. No expiry. One current revision per scoped
  Job/role is derived from the journalled chain; overlap/chains/cycles refuse.
- allocation_replacements: one optional immutable record per assignment_id,
  referencing the selected revision and validated execution-binding digest.
  Written in the allocation transaction. Legacy allocations have no record.

No copy of offer/runtime/session/cleanup state is stored here. The ordinary
owners continue to answer those questions. Job schema is currently6; use the
next schema revision and its normal additive migration machinery. Routine
numbering and migration implementation are engineering work, not another owner
permission question. Historical operations/allocations remain unchanged.

Proposed public owner entry points:

```python
designate_replacement(job_store, authorization, document, *, expected_revision)
revoke_replacement(job_store, authorization, designation_id, *, expected_revision, reason)
replacement_of(job_store, job_id, role)
replacement_for_allocation(job_store, assignment_id)
```

The designation document carries: stable designation ID; exact Authority,
Job-store and deployment identity; finite Job IDs with Work and role; original
source worker and actual participant/principal; designated worker and actual
participant/principal/profile; expected pool generation and worker configuration
digests; original Job input/policy and source/base/target bindings; replacement
runtime manifest/profile/image/adapter and derived binding digest; reason and
expected predecessor. Only implementation/review stage roles are proposed for
this first release. Integration and derived judgment actor replacement require
their result-specific authority/session composition and are explicitly outside
this patch, not silently covered by an implementation designation.

Authorizer: the deployment operator, **not the worker or an arbitrary participant
string**. Add a trusted deployment-side authorization factory to a narrow new
tools/operator_replacement.py entry point, following tools/job_manager.py's
injected-capability approach. The factory authenticates the local operator using
the deployment's protected OS-user-to-Authority-participant enrollment, resolves
the actual principal through Authority, checks the enrolled exact scope, and
returns a non-worker-facing capability to the owner. Record actual OS identity,
participant/principal, enrollment digest, reason and operation. Request payload
fields never supply or override the authenticated actor. Invalid/unavailable
enrollment refuses before Job mutation. This is a proposed local administrative
trust boundary, not cryptographic remote attestation or a defense against the
OS account that controls the deployment itself.

Authority's current receipt capabilities do not include replacement management;
do not reuse approve/close/manage-work-labels or mint a forged receipt. This
local operator capability grants scheduling configuration only. Actual worker
route eligibility, claim and scoped publication/review permissions still come
from ordinary Authority owners. An operator designation supplies none of them.

Designate/revoke use expected-revision compare-and-swap and exact journal replay.
Changed operands under the same operation refuse. Replaying an earlier successful
designation after revocation returns that historical receipt without activating
it again. Deliberate reactivation is a new revision. Deleting the config file,
reopening the manager, worker health or elapsed time cannot revoke a designation.
Revocation restores the original bound role eligibility for future reservations;
it does not erase evidence or move a current assignment.

## Admission and execution composition

The original source_worker_id continues to name source/task/harness provenance.
It is never rewritten to impersonate Jane. A separate effective execution binding
is derived by replacements.py from the current designation, original Job and
validated configured worker facts. It records both original and runtime input
identities. The replacement runtime manifest may change only execution metadata
explicitly selected in that binding; Work, task bytes/instructions, declared
source objects/repository, base/target, policy, test scope, artifact contracts and
Job limits must remain identical. A changed image/profile is not permission to
change source or tasks. Reject a manifest whose differences exceed the enumerated
execution metadata. Use normal manifest ownership/digest validation.

For the current manifest, the proposed difference allowlist is exactly
runtime_profile_digest and worker_image_digest, plus the manifest_digest
recomputed by its normal owner. All other manifest members remain byte-equivalent
after canonicalization, including assignment_contract, Work, payload references,
policy and task contract. Profile name, adapter identity and image configuration
are separately pinned in the designation's worker binding. If a selected provider
requires a different task or assignment contract, refuse it under this design;
that is a different product change, not an additional allowed metadata field.

Same-profile replacements still require this designation binding, even if the
runtime input digest happens to stay equal. Different-provider replacements need
a separately valid and configured profile/image/adapter; designation cannot
certify it. Preserve the original Job profile/input as immutable intent and
expose the explicitly authorized runtime profile/input as a separate execution
revision. Reviewers must see both, not a rewritten submission.

At a new reservation, the serving compatibility reader supplies its held
configuration digest and pool generation. Under the Job-store transaction,
reserve resolves the current designation and exact effective binding, compares
those operands, and intersects designated-only eligibility with ordinary hard
profile/kind/Work/input/repository checks, review independence and actual-principal
occupancy. A missing or busy designated worker waits/refuses honestly; it does
not try Chris, a third worker or an alias. Record selection_outcome=designated
and the revision in allocation_replacements. Keep affinity unchanged.

Resolve designation under the lock, not only in _job_eligibility. A stale caller
cannot submit a permissive exclusion list to bypass revocation. The same owner
must validate the original stage/Job identity before producing an effective
runtime intent. PooledManagerOperations.binding_intent/admit/check_binding and
subsequent launch/dispatch/observe/recovery read the allocation's pinned binding,
never today's designation. Extend delegation's owned intent/replay contract to
carry that provenance. Do not pass a fabricated copy of stage/job to unchanged
validators and call it owner authority. An unbound or forged override refuses.

Use existing job_execution_context to keep original Job limits and original
input/policy alongside actual runtime input/policy. This reader already supports
that distinction; no new limits resolver or change to its defaults is needed.
The single-worker launch remains fully checked against its actual manifest and
assignment. Worker outputs, checkpoints and publications attribute Jane's real
participant/principal and fresh attempt, never Chris's identity.

Configure dedicated primary/replacement workers before normal serving so a
designation can change within one pool generation. For the first delivery,
adding/removing pool workers or changing their configuration requires a drained
pool with no reserved/recovery-required allocations before recompose; retain all
old evidence. This avoids claiming unimplemented full-serving old-generation
provider construction. It does not require stopping unrelated Jobs just to
activate/revoke a designation among already-configured workers. Pool drift makes
the designation incompatible and held until explicitly revised; it cannot make
the replacement silently ordinary or reactivate Chris.

### Linearization and existing attempts

The allocation transaction is the admission selection cut. A reservation
committed before designate/revoke retains its worker, even if its offer is not
yet issued. That is observable and avoids ambiguous half-revocation. A revocation
that commits first governs the next unreserved attempt. Race tests must prove
both legal orders, not assume wall-clock order.

| Existing state | Treatment |
| --- | --- |
| No allocation / fresh successor | Read current designation atomically, then ordinary reserve/offer/claim/start |
| Reserved, including not-yet-offered | Preserve pinned binding and owner. If the operator wants it stopped, use ordinary cancellation/recovery first; designation alone does not release it |
| Claimed/running/answered | Continue or recover through the original owner. No retagging, session handover or second writer |
| Unknown start or runtime stop | Retain hold, exact identities and original owner; offline/model outage is not positive stop |
| Completed producer awaiting independent review | Preserve that checkpoint and attribution; a reviewer designation affects only a new review allocation, with exclusions against all producers |
| Positively recovered abandoned correction | Existing restore_abandoned_correction and restart_abandoned_correction prove excluded writer/restored line, end the old episode, then ordinary sweep opens one successor that can use the designation |

Do not broaden the accepted abandoned-correction recovery into a general
takeover protocol. Other unsupported in-flight cases stay held with their exact
owner evidence and manual recovery boundary. Designation may be recorded while
such a hold exists, but no replacement execution is admitted for that episode.
No timeout-based absence, lease theft, automatic abandonment or duplicate launch.

## Independence and context transfer

Use actual-principal capacity globally across live allocations/generations.
Different worker IDs or participant aliases resolving to one principal provide
one capacity, not extra slots. Review exclusions must include Chris and Jane if
both produced any attempt for that Job, including superseded attempts. Validate
the declared separation class and independently authorized reviewer configuration
before admission; a designation cannot make the producer its own reviewer.

A replacement starts with a fresh provider conversation by default. Useful
state is the positively retained/restored development line, accepted artifacts
and explicit task/correction evidence, not a borrowed live process or credential
home. Do not transfer private producer context to an independent reviewer.

W174289's proposed context record is bound to real participant/principal,
Job/line/provider/profile and protected generations. It does not authorize a
different actor or provider to resume Chris's conversation. For the same healthy
actor, W161234's required continuity remains; this design does not reset that
requirement. For a designated different actor/provider, choose fresh context
and preserve available portable work. Any future compatible same-provider private
context transfer needs its own explicit custody/access proof; no fixed cache
savings or provider-native identity preservation is claimed here. Revoking Jane
also cannot resume a stale Chris context as though Jane's intervening work were
already in it.

## Operator example — proposed surface, not runnable today

An unavailable implementation worker for Job `compile-parser` is `impl-chris`,
participant `team.chris`, principal resolved by Authority. The operator designates
already-configured `impl-jane` / `team.jane` for this Job's implementation until
revoked. The resolved principal, profile and image are Jane's. `source_worker_id`
remains `impl-chris` for the unchanged nominated source/input contract.

1. Inspect the proposed read-only replacement status: original worker, current
   designation/revision, exact Job/Work, actual principals/profiles, and whether
   an allocation already pins an owner. Inspect actual runtime uncertainty
   through its owner; replacement status must not infer absence.
2. Use the new deployment-authorized entry point to designate Jane with expected
   revision0 and the reviewed execution-binding digest. Its receipt identifies
   the operator and revision1. If Chris still owns an allocation, the response
   says it remains pinned; no second execution starts.
3. After any necessary positive original-owner recovery, ordinary serving
   reserves a fresh successor for Jane. If Jane is occupied, it remains pending.
   Reopening preserves revision1 and the same committed allocation.
4. Revoke revision1 explicitly. The receipt records revision2; already-reserved
   Jane work continues under revision1, and the next unreserved eligible attempt
   returns to Chris's original binding. If Chris remains unavailable, it waits.

A display should say “Jane designated for this Job's implementation; current
attempt still owned by Chris; recovery required” when those are the facts. It
must not say “Jane is Chris” or “replacement complete” upon configuration alone.
The request is an exact finite mapping; covering another Job is another explicit
scope entry, not an inferred project-wide alias.

## Exact proposed ownership and verification

This table is a finite implementation proposal for later selection/review, not
permission to edit now. Coordinate overlap with W161234/context work at
stage_execution.py and single_worker.py before implementation. Keep the original
W103525 evidence unchanged; use new focused tests. An unexpected extra production
owner requires an explicit scope correction, not an opportunistic edit.

| Proposed paths under v12/python/ | Responsibility |
| --- | --- |
| NEW src/baton_v12/job_manager/replacements.py | Designation/revocation, validated effective binding, historical/current readers, journal replay and transaction-local admission checks |
| src/baton_v12/job_manager/schema.py, store.py | Two additive relations, owned schema/migration; no submission or existing-allocation rewrite |
| src/baton_v12/job_manager/scheduler.py | Atomic designation selection, allocation binding, designated outcome, original effective-principal capacity/independence and pinned replay |
| src/baton_v12/job_manager/delegation.py | Explicit owned execution-binding provenance in intent/adoption and exact replay; original Job identity retained |
| tools/stage_execution.py | Validated standby worker binding, separate source/executor selection, consistent compatibility/operations/publication/read-only status; drain refusal before incompatible pool activation |
| tools/single_worker.py | Accept only owner-bound runtime execution revision at the existing stage/manifest comparison and launch boundary; preserve actual assignment and limits |
| NEW tools/operator_replacement.py | Protected local operator capability factory, designate/revoke/status; no Authority impersonation or arbitrary worker-provided authorizer |
| NEW tests/job_manager/test_replacements.py | Journal/schema/replay/race/exclusion/immutability matrix |
| NEW tests/tools/test_operator_replacement.py | Authenticated operator/enrollment/scope refusal, read-only status, no mutation on denied/invalid request |
| NEW tests/tools/test_replacement_serving.py | Real normal owners and fake provider boundary, actual replacement output/checkpoint/review, fixed source/limits, recovery/reopen and no duplicate effects |
| Existing tests/job_manager/test_scheduling.py, test_store.py, test_delegation.py; tests/tools/test_single_worker.py | Focused schema/closed-intent fixture updates only where necessary; preserve legacy fallback, principal and replay expectations |
| DEPLOYMENT.md through its current owner after accepted implementation | Actual command recipe and qualification limits; no manual change under this design |

Source/test estimate: medium-to-large, principally the owned effective-runtime
binding through delegation and full serving; larger than a config-only recipe.
Implement in two serial reviewable parts: durable designation/admission first,
then serving/operator composition and complete proof. Both parts are needed for
the stated outcome; a passing table-level selector is not feature completion.
No new Work or gate is created by this proposal.

Proposed focused deterministic acceptance, with sensible per-run timeouts and
process cleanup; no test or probe is executed in this design:

| Case | Required actual witness / negative |
| --- | --- |
| Designate, replay, revoke, reopen | One revision per exact act; historical replay does not reactivate; stale expected revision and changed operands refuse; fresh read-only owner reports exact actor/scope/history |
| Designated-only and scope | Jane alone eligible for named Job/role; busy Jane waits despite free Chris/third worker; another Job retains ordinary policy; no wildcard spill |
| Reservation races | Two JobStore connections interleave designation/revocation with reserve; allocation binds exactly the winning revision; later replay preserves it |
| Real identity | Aliased principal occupancy refuses; wrong Authority principal, route, Work, profile, policy or repository/base refuses before offer/setup |
| Changed provider binding | Distinct valid runtime image/profile/manifest, identical semantic task/source/policy/limits; actual fixed assignment and launch carry Jane and new runtime digest while Job input remains original. Forged/unrecorded digest or changed task/harness/output contract refuses |
| Full replacement | Normal reserve/offer/claim/start, real local worker process at deterministic provider seam, meaningful code change, ordinary freeze/intake/retention/checkpoint attributed to Jane, independent review and actual authorized terminal result. No authored success receipts |
| Existing attempt | Record designation while Chris is running or unknown: no Jane launch and no rewritten allocation. Accepted abandoned-correction recovery proves positive exclusion/restoration; exactly one ordinary successor then uses Jane |
| Review independence | Jane cannot review a Job she or Chris produced, including through a principal alias; a distinct authorized reviewer can. Producer context is not exposed |
| Revocation/reopen | Reserved Jane attempt survives revocation under pinned operands; new attempt uses original binding; actual provider/engine invocation counters reject duplicate launch after durable reopen |
| Pool change boundary | A changed generation with live allocations refuses before activation in this composition; same-generation designation works while unrelated Job remains active |
| Legacy | Existing soft fallback, no-designation source/input refusal, direct/managed owner guards and original Job limit resolution remain true |

Use project-pinned dependencies and record actual versions. A proposed focused
command is `python -m unittest tests.job_manager.test_replacements
tests.tools.test_operator_replacement tests.tools.test_replacement_serving` after
those tests exist, plus the affected existing selectors above. A 180s supervised
per-run ceiling with bounded termination/cleanup is a planning starting point,
not a cumulative budget or authorization to run a live engine/model. Preserve
failed evidence and measured time. No broad random/stress/two-slot certification.

## Return and limitations

Select the bounded durable-designation plus explicit execution-binding direction,
then independently review its concrete implementation packet. Exact finite scope,
local operator trust boundary, admission-time revocation and fresh replacement
context are the product choices proposed here. They are not already accepted
behavior. No open question about whether replacement is required remains.

Post this report nonblockingly to T103525 and T2, then pass this design Work to
baton.ops. W103525 stays the original requirement/evidence owner. Do not close it,
W2, W161230 or W161234 from this advisory report. No tests, probes, provider/model/
engine calls, builds, Git mutations or additional workers ran; new measured
runtime verification0s. Reading/editing elapsed time was not measured as a run.

Operational read findings: guessed job_manager/configuration.py, pool-adjacent
CLI/recovery paths and an advisory review glob were absent. File discovery
located the actual tools/job_manager.py and recovery owners in attempts.py,
review_cycles.py and episodes.py. The advisory has PREWORK evidence, not a
separate review file at that guessed glob. These were corrected search mistakes;
no mandatory policy or bound dossier was unavailable. Display-truncated source
reads were narrowed for the cited owner bodies. No coordination store was opened
directly and no workaround was used.

## Exact reference fingerprints at design completion
These are read-only current-byte fingerprints, not an immutable import proposal
or a claim that historical tests ran on every current source. Original canonical
records and their accepted snapshots remain authoritative for historical evidence.
| Canonical locator | SHA256 |
| --- | --- |
| baton:work/records/2026/09/finding-v12-deterministic-scheduler-stress/SELECTED-PLAN-161345.md | f1fdbd5c15f22d10ca6da157b590d305ed755a0202a969694adf4b7bc3cc0569 |
| baton:work/records/2026/09/finding-v12-deterministic-scheduler-stress/review-2026-09-13T14-10-03Z.md | f162479f5d3711cbbee76bfef073b8b12fff816b697bd14a2a209e99c3efe4ff |
| baton:work/records/2026/09/finding-v12-scheduling-evidence-prework/PREWORK.md | 62216cf955ce4292fc183c6fd820bfcb06a0a3165434804fb3a8e26a8fc98d90 |
| baton:work/records/2026/09/finding-v12-context-reuse-design/DESIGN.md | 5da337d20d0bd62ba3e2d65128ce046b0ef318bf1f1512cb47ee8ca44bcbf3c7 |
| baton:v12/python/src/baton_v12/job_manager/scheduler.py | 4a315a23dc368e8b39fdb07c63868c29578f32be409912ffc762078f17bda0e1 |
| baton:v12/python/src/baton_v12/job_manager/delegation.py | f8ae5cf8525024a6d329d90bc0669b35a356411caa2b2b83f31f57920b8024d8 |
| baton:v12/python/src/baton_v12/job_manager/submission.py | 204e6eb50d955ae359cf833f5e8426bc3c2b13c63687eda3b8bf2508d440c2c1 |
| baton:v12/python/src/baton_v12/job_manager/episodes.py | 32e46805540fb7aa4558a735d6d8a714e03c4b7c0e85c8695f929ca596077865 |
| baton:v12/python/src/baton_v12/job_manager/schema.py | 137617b87020e4b4b5309c3396ce94f86243822604d67392bfbd44dafd9cc0f0 |
| baton:v12/python/tools/stage_execution.py | abf0bb2d89aee0398f8428221a0282b52c69cdb5074736150a0259f2281dd8b2 |
| baton:v12/python/tools/single_worker.py | 3b78842c59a46b30a2a542cac6e7ed860e32c5e5645baed643c478a4eddd3c49 |
| baton:v12/python/tools/job_manager.py | 1060e26a4196bafbc55db7955271853b1a2dde45e316d39cba7681939aeb6bb7 |
| baton:v12/python/tests/job_manager/test_scheduling.py | d61e968e11dd6bd8904631b577f25ceafc9e231b811294ea7f81ae681e88b03e |
| baton:v12/python/tests/tools/test_stage_execution.py | fcdbb74e51a8f9bf1a66b414f22f4acf9180cb70ece39fa3bdf778387e9d4b86 |
| baton:v12/python/tests/tools/scheduler_trace.py | fa9e69f2df32b11cd2a830dc962900796e5aeb89398c50c5175d8e8e87ccf0d5 |
| baton:v12/python/tests/tools/test_scheduler_trace.py | a57c0a71e52629ee6008f054dccb1ef2d563bb886453b6bd8317daefe2437e17 |
