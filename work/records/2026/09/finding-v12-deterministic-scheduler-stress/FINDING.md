# Finding: certify v12 parallel scheduling with deterministic traces

Ledger Work: W103525

## Placement — confirmed 2026-09-06

This certification stage starts immediately after the standalone multi-Job
v12 pipeline milestone represented by W71830 is accepted. It does not block or
broaden that milestone.

The purpose is to validate the scheduler before model latency, provider
availability, and non-deterministic completion times obscure its behavior.
Scheduler correctness must be provable without invoking an AI model.

## Confirmed test contract — 2026-09-06

Use Python-scripted actors, controlled completions, and a logical clock to
exercise multiple teams with pools of implementation and independent-review
workers. The durable event trace is the evidence and a validator asserts
causal partial orders and final state invariants.

The certification covers:

- dependencies preventing premature stages without serializing unrelated
  Jobs;
- role, capability, team, and repository eligibility;
- implementation/review session separation;
- same-line correction affinity to the original healthy implementation
  worker and session;
- explicit fallback as the only intentional affinity break, with a fresh
  session;
- one live offer/claim per worker slot and no duplicate execution;
- work-conserving dispatch: no compatible slot remains idle while eligible
  Work exists;
- priority governing between explicit priority pools, affinity selecting
  within a pool before creation chronology, and creation order breaking the
  remaining ties;
- restart, replay, and repeated observation producing the same canonical
  result without duplicating effects; and
- a trace shape that a later read-only v12 TUI can render as stable Job rows
  plus chronological offers, claims, handoffs, corrections, fallbacks, and
  integration transitions.

Independent Jobs may complete in any order and workers may take arbitrary
amounts of time. Tests assert only required `this-before-that` relationships;
they do not invent a total completion order.

A later live Claude/Codex exercise validates adapters, credentials, latency,
and observability. It is not the oracle for scheduler correctness.

## Deferred details

Exact pool sizes, workload counts, timing thresholds, randomized interleaving
strategy, and TUI presentation remain open until the parallel scheduler is
available. This record fixes the certification boundary, not those mechanics.

## Reviewer revalidation — 2026-09-12T15:54:16Z

**Confirmed:** W71830 is closed satisfying. Canonical W103525 event153657
released its dependency; claim153660 belongs to baton.codex. The initial
handoff and T103525 contain no later scope amendment. The placement hold is
therefore superseded: research may proceed now. This does not certify the
scheduler or close W103525.

The repository's 2026-09-12 v12 verification default applies: scripted/replay
providers at their normal boundary, focused local tests, real owners for the
behavior being proved. The earlier paragraph promising a later live exercise
is superseded as a mandatory sequence; live calls require a specific
provider-dependent question. W71830's temporary test-change exception expired
with its completion. This Work proposes additive tests and no edits to existing
assertions or product files.

**Observed baseline:** `baseline-153660-system.json` and its `.log` retain 26
passing existing scheduler/sweep tests, exact selectors, source fingerprints,
and 0.2537531379784923 seconds of subprocess wall time. These exercise real Job
and control stores with fake Authority sessions/runtime callbacks. They are
not evidence of full composed multi-team execution or provider-session reuse.
The initial `.venv` invocation failed before test execution because jsonschema
was absent; `baseline-153660.json`/`.log` preserve that failure and its
0.034172585990745574 seconds. Total measured baseline spending is
0.2879257239692379 seconds, with no live model calls. The successful interpreter
has jsonschema4.19.2, whereas `v12/python/pyproject.toml` pins4.26.0; this is
exploratory evidence, not dependency-conformant certification. No dependencies
were installed or changed. `baseline-153660.py` reproduces the selection with a
fresh output label and refuses to overwrite either earlier result.

**Confirmed contract mismatches, not permission to weaken acceptance:**

1. `job_manager/scheduler.py:reserve` implements soft affinity: when the
   preferred worker is occupied, it automatically chooses another compatible
   available worker and records `selection_outcome=fallback`. Existing
   `SelectionAndSettlement.test_affinity_is_soft_and_fallback_does_not_rewrite_it`
   passes. W71877's finding, “Proposed selection and settlement order” and
   “Operator acceptance of decision 1 — 2026-09-03”, describes this behavior
   and separates worker identity from session identity. W103525's later
   explicit-fallback-only wording is stronger. A busy healthy worker also
   exposes tension between waiting for affinity and work-conserving dispatch.
   Neither text is silently superseded by this reviewer.
2. The current Job submission and worker-pool closed schemas have no priority
   field. `projection.owed_acts` visits sorted stage IDs, and `reserve` orders
   available workers by worker ID. This is not the promised priority-pool,
   affinity-before-creation, creation-order tie-breaking contract. Reversing
   stage-ID order relative to submission chronology is the minimal
   distinguishing scenario; it must not be labelled a passing priority test.
3. `v12/python/tools/stage_execution.py:_job_workers` restricts implementation
   eligibility to the Job binding's `source_worker_id` before reservation.
   `_job_eligibility` feeds those exclusions to the existing scheduler. A unit
   test's replacement worker therefore cannot establish that a composed
   correction can continue on another worker. Emergency named pool-generation
   activation, automatic worker selection fallback, and fresh provider-session
   creation are three separate facts and require separate observations.

**Open:** the complete multi-team/repository eligibility and session-continuity
matrix has not yet been executed. Team membership alone is not a substitute
for Authority scope/capability decisions; a configured source root alone is
not proof that a wrong repository was refused. Existing composed fixtures are
the starting point, not an assumed passing result.

**Proposed direction:** implement the additive trace/oracle foundation in PLAN
without claiming the three mismatches certified. The owner should explicitly
choose whether to amend W103525 to current soft-affinity/stable-order behavior
or retain the stronger contract and schedule the missing product behavior.
Recommended: retain the stronger requirements as open, deliver the bounded
foundation first, then scope the missing behavior from its distinguishing
traces. This advances execution without redesigning product code in a reviewer
claim or manufacturing a passing certification.

Prior decision locator:
`baton:work/records/2026/09/finding-v12-standalone-multi-job-pipeline/findings/finding-concurrent-stage-scheduling/FINDING.md`.
Full current source map, scenario boundary and proposed verification caps are
in this record's PLAN. No product/test path or author-owned PROGRESS was edited.

## Owner decision and independent review — 2026-09-12T16:18:34Z

**Confirmed owner decision:** canonical return153764 at2026-09-12T16:06:36Z
approved the additive foundation in the current PLAN: two new test files,
deterministic providers, real coordination owners and independent validation.
It retained fallback, priority/chronology and composed-continuation requirements
as open, accepted120s author/30s reviewer and100 ticks per trace, and required
explicit environment gaps with no live models/full certification claim. This
supersedes the prior pending-owner-decision status. It does not waive the
foundation's real owner transitions or authorize product edits.

**Observed review outcome: changes requested.** Candidate153769 matches its
two declared SHA256s and all25 focused tests pass. Independent reproduction
shows the oracle accepts a claim/completion without reserve/offer, aliased
principal over-occupancy, custody freed by reopen, and regressing logical time.
A fresh driver's bookkeeping also misreports an idempotent reserve as a new
effect. Exported schedules stop at reservation, so they do not satisfy the
approved composed foundation. The candidate's allocation-release helper does
not complete a Job: its stage remains queued with dependents blocked.

Exact findings R1–R5 and correction boundary:
`review-2026-09-12T16-18-34Z.md`; reproduction `repro-153824.py` and retained
`review-153824-repro.log`; selectors, hashes and measured spending in
`review-153824.json`. No integration approval or certification is issued.
Author1.4638874580268748/120s; reviewer0.40351907099829987/30s; earlier research
0.2879257239692379s remains separate. No budget reset, model calls, product edits
or author-owned PROGRESS edits by the reviewer. Corrections return to the same
implementer boundary without a new approval gate.

## Independent correction review — 2026-09-12T16:35:09Z

**Confirmed:** candidate153855 matches its two hashes and38 focused tests pass.
Actual composed accepted-review and correction cases now execute. R3's principal
capacity/reopen correction and R4's durable reserve/observe classification are
accepted for this boundary. These supersede those two earlier open review items;
the historical review remains unchanged.

**Observed:** R1/R2/R5 remain partial. Independent probes show completion without
start, standalone review and standalone integration still validate without
prerequisites. The new snapshot extractor translates a refused admission receipt
into a performed offer. Composed artifacts contain no Job graph, all events at
tick1, and only current episode2 for correction; their sorted post-run output
does not establish actual causal order. Team/repository labels are now honestly
described as unproved, but no exact failing composed setup has been supplied.

Newest review `review-2026-09-12T16-35-09Z.md` records remaining C1–C3 and directs
correction inside the same two-file boundary. Evidence: `repro-153920.py`,
`review-153920-repro.log`, `review-153920-suite.log`, `review-153920.json`.
No integration approval/full certification is issued. Cumulative author
36.81703629397089/120s, reviewer2.047547444992233/30s; research baseline
0.2879257239692379s separate; no resets or live model calls. Reviewer did not
edit either candidate or author-owned PROGRESS.

## Independent recording review — 2026-09-12T16:51:07Z

**Confirmed:** candidate153951 matches both hashes;43 focused tests pass.
The missing-start probe now refuses, unsupported review/integration acts are
explicitly unvalidated, and the actual extractor preserves a refused receipt.
These bounded C1/C2 fixes supersede their earlier demonstrated defects. Other
unimplemented acceptance checks remain open; this is not full certification.

**Observed remaining C3 defect:** the extractor sorts episode/stage ordinal/act
rank before timestamps. A synthetic claim timestamped before its offer is
reordered to offer-before-claim and validates clean. The evidence generator
therefore imposes the very order its oracle claims to verify.

**Confirmed available observation seam:** the actual composed fixture exposes
implementation=completed immediately after `produced()` and before correction.
That state becomes waiting after correction. The superseded completion can be
preserved by observing while executing; a new product-history API is not shown
necessary. `review-2026-09-12T16-51-07Z.md` gives a bounded test-only capture
direction at the existing `sweep` and driver boundaries. D1 remains changes
requested; no new scope/approval gate or integration sign-off.

Evidence: `repro-154010.py`, `review-154010-repro.log`,
`review-154010-suite.log`, `review-154010.json`. Cumulative author
58.525035111029865/120s; reviewer4.148816700995667/30s; prior research
0.2879257239692379s separate. No reset, model call or reviewer candidate edit.

## Live-observer review — 2026-09-12T17:01:19Z

Candidate154041 matches its two hashes and46 focused tests pass. Live tick
observation now retains the earlier implementation completion through correction;
that portion of D1 is corrected, and the final-state act-rank sorter is removed.
The original unequal-timestamp counterexample remains: the current observer
emits claim00:00:01 before offer00:00:02, both observed at tick1, and the validator
accepts it because its prerequisite check ignores owner instants when ticks tie.

`review-2026-09-12T17-01-19Z.md` narrows the next correction to that comparison,
with actual-observer synthetic negative/positive inputs in `repro-154077.py`.
Prior accepted corrections stay accepted; no new acceptance requirement or
approval gate is introduced. No integration/full-certification sign-off.
Cumulative author67.41587816199171/120s, reviewer5.464061403967207/30s;
research0.2879257239692379s separate. Logs and bindings: `review-154077.json`,
`review-154077-suite.log`, `review-154077-repro.log`; no reviewer candidate edits.

## Prerequisite timestamp acceptance — 2026-09-12T17:08:44Z

**Confirmed:** D1 is corrected in candidate154100. All50 focused tests pass;
the unchanged actual-observer counterexample now returns `out-of-order` and its
legal companion passes. This supersedes the remaining D1 changes-requested
status in the17:01:19Z entry; earlier accepted corrections remain accepted.

Review `review-2026-09-12T17-08-44Z.md` binds both candidate hashes and records the remaining original
foundation scope. Next is the real Authority team/repository positive and refusal
case, or an exact failed public setup/missing seam before any scope expansion.
Acceptance/session and review/test/import authorization evidence remains open;
the three retained product mismatches are unchanged. No full certification or
immutable import approval. Cumulative author72.77131704305066/120s, reviewer
7.242810859985184/30s; research0.2879257239692379s separate.
Evidence `review-154120.json` and its suite/repro logs; no reset or live models.

## Team authorization clarification — 2026-09-12T17:15:58Z

**Confirmed:** candidate154142 passes52 focused tests. The actual missing-base
line refusal and ungranted receipt-actor refusal are accepted at their observed
boundaries. Prior fixes remain accepted.

**Correction to inference:** a missing grant does not establish a missing
team-membership API. Independent `repro-154165.py` composes `other.reviewer`
successfully using the existing scoped `Authority.grant_capability`; no grant
and wrong-scope grant both refuse. This supersedes the new missing-membership-
seam claim as a reason the accepted two-team configuration cannot be driven.
Earlier reviewer wording about a team membership fact is clarified: use actual
team.member endpoints and actual scoped authorization, not an invented new
membership relation or team-policy requirement. No product expansion authorized.

Review `review-2026-09-12T17-15-58Z.md` requests the exact negative/positive matrix and honest gap
labels, then the already queued acceptance/session/authorization evidence within
remaining scope and cap. This is configuration proof, not execution of a whole
multi-team schedule. Full certification and the three retained product gaps
remain open. Cumulative author77.30077425704803/120s, reviewer9.322020830004476/30s,
research0.2879257239692379s separate; evidence review-154165.json/logs.

## Team matrix and offer acceptance review — 2026-09-12T17:24:24Z

**Confirmed:** candidate154186 passes52 tests; real second-team scoped-grant
matrix and separate owner-recorded offer acceptance are accepted. This resolves
the17:15:58Z changes request and supersedes prior claims that offer acceptance
has no separate owner evidence. Independent deletion/late-acceptance mutations
refuse while the original retained artifact passes. Prior accepted fixes stand.

Review `review-2026-09-12T17-24-24Z.md` carries the next existing item: actual review/test/import
authorization via normal executions and public owner evidence. Session identity
remains unexercised on this path, not an absent API. The three retained product
requirements and certification remain open. No new approval prerequisite or
source expansion. Author87.5610530859849/120s, reviewer11.152919651009142/30s;
research0.2879257239692379s separate. Evidence review-154217.json/logs and
repro-154217.py; no reset or reviewer candidate edits.

## Authorization export correction — 2026-09-12T17:30:56Z

**Confirmed:** real composed integration supplies public verification/approval/
review/integration receipts; all56 candidate tests pass. The owner documents
already carry exact candidate, target and authorization decisions.

**Observed:** current authorized() drops disposition and context: synthetic
changes-requested review still becomes performed and validates. A review at
00:00:02 after integration at00:00:01 also passes when observed in one tick.
Verification/approval and candidate/scope/policy fields are absent from exported
authorization, so the queued item is incomplete despite having real input.
This supersedes the author claim that the addition discharges the queued scope;
it does not reopen earlier accepted fixes or assert a product defect.

Review `review-2026-09-12T17-30-56Z.md` supplies exact correction and existing acceptance boundary;
raw public receipts and synthetic mutations retained in review-154259-repro.log
and repro-154259.py. No new scope/approval gate or certification. Author
92.44196586098406/120s, reviewer15.13365985697601/30s; research0.2879257239692379s separate.
Session independence and the three product requirements remain open.

## Authorization decision/context review — 2026-09-12T17:37:27Z

**Confirmed:**62 tests pass; rejected/late reviews now refuse, all required
judgment kinds and candidate/target checks are present. Those corrections
supersede the corresponding open items at17:30:56Z; prior fixes stand.

**Observed remaining context gap:** replay through current authorized() accepts
a review with foreign effective_scope, missing decision.policy_generation, or
wrong decision.role. Review `review-2026-09-12T17-37-27Z.md` gives the exact bounded check and
clarifies nullable receipt.policy_generation versus required positive
authorization-decision generation. No new product rule/API or approval gate.
Evidence repro-154303.py and review-154303.json/logs. Author100.38120128700393/120s,
reviewer18.313524367986247/30s; research0.2879257239692379s separate. Session independence,
correct validation and the three product requirements remain open.

## Scope-reference refusal review — 2026-09-12T17:42:54Z

**Confirmed:**21 affected tests pass; with the owner reference present, all
three retained context mutations now refuse. Those parts of the17:37:27Z
correction are accepted. Earlier fixes remain accepted.

**Observed sole remaining gap:** deleting authorization_references disables the
scope check; both missing-reference and foreign-scope-plus-missing-reference
artifacts validate. Require the subject owner scope before accepting a
performed authorization. Review `review-2026-09-12T17-42-54Z.md` and repro-154343.py retain the exact
negative/positive boundary; no product scope or approval change. Author
108.39710617496166/120s, reviewer21.29538442796911/30s, research0.2879257239692379s separate.
Session/correct/three product gaps and full certification remain open.

## Foundation correction acceptance and remaining work — 2026-09-12T17:48:52Z

**Confirmed:**70 focused tests pass independently. The missing-reference and
foreign-scope-without-reference probes now refuse; original passes. This
supersedes the17:42:54Z changes request and resolves the demonstrated correction
queue. Earlier bounded acceptance remains in force. Exact final candidate hashes
and tested limits are in `review-2026-09-12T17-48-52Z.md`.

**Not certified:** the complete composed four-Job/two-team alternate/reopen
scenario, actual agent-session independence, explicit correct validation, the
three retained product requirements and pinned dependency environment remain
open. Passing isolated pieces does not prove their full composition. W103525
stays open. No product expansion, Git mutation or immutable import approval.

**Proposed, not authorized:** owner disposition of next same-two-file test-only
continuation with additional45s author/10s reviewer, cumulative165s/40s, no reset.
The costed session/composition attempt and exact failure-return boundary are in
the review and PLAN. Current author116.65264648597804/120s and reviewer24.47790529599297/30s; research
0.2879257239692379s separate. No further spending increase has been applied.

## Continuation authority and independent review — 2026-09-12T23:32:26Z

**Confirmed owner decision:** return155646 at2026-09-12T23:07:36Z accepted
the tested foundation and authorized its same-two-file continuation with
cumulative165s author/40s reviewer caps, prior spending preserved. Nonempty
sessions and independent roles come first, then composed alternate order,
reopen and correction evidence; no product expansion, live providers or repeated
unchanged suites. This explicitly supersedes the17:48:52Z pending-approval
status and original120s/30s caps. The ruling is recorded here after discovering
that the current PLAN still showed it pending. No additional permission is needed.

**Confirmed:** candidate155666 passes93 tests independently. Real owner-created
sessions, the crossed-port refusal, both composed implementation completion
orders and per-trace observation bookkeeping are demonstrated at the limits in
`review-2026-09-12T23-32-26Z.md`. Previous bounded acceptances remain in force.

**Observed changes requested:** a correction artifact with only a review
reservation and no later review acts validates clean. A real session reference
with a foreign provider component, or a review session naming an unassigned
participant, also validates clean. These new validator rules do not yet prove
their claimed causal/assignment relationships. Exact positive controls and
labelled negative inputs are retained in `repro-155774.py` and its review log.

**Confirmed public correction evidence:** `ending.settlement_of` on the original
review episode returns `evidence.verdict_id`, correction outcome and routed next
attempt; `review_cycles.verdict_of` answers the matching committed judgment.
`review_driver.review_verdict_from_result` also answers the frozen review claim
from the attachment. The independent composed probe successfully read all three.
This explicitly supersedes claim155666's inference that this scenario requires
a new attachment-to-verdict API. Correct within the accepted test-only boundary.

The latest handoff's team-membership wording does not supersede the17:15:58Z
clarification or17:24:24Z scoped-team-matrix acceptance. That setup is proved;
the full multi-team execution remains unproved. Composed reopen was not attempted.
Full composition/session continuity, the three retained product requirements
and the pinned dependency environment remain open, with no certification waiver.

Current author153.47350225197812/165s, reviewer29.259979616993178/40s;
research0.2879257239692379s separate. Evidence `review-155774.json` and suite/repro
logs bind the exact unchanged candidate; every recorded source hash in the
two155666 export sets matches current files. Reviewer edited no candidate,
PROGRESS or Git state and made no live model call. Return the two bounded
corrections through baton.bug, with full remaining scope and budgets preserved.

## Session acceptance and remaining correction context — 2026-09-12T23:45:06Z

**Confirmed:**61 affected tests pass independently; the author's105-test final
module result is retained. The original foreign-provider and foreign-session-
participant probes now refuse, as does the review-reservation-only correction.
R2 and the demonstrated R1 disposition/routed-attempt improvements are accepted,
superseding those portions of the23:32:26Z changes request. The public verdict
reader correction remains confirmed; all earlier bounded acceptances stand.

**Observed remaining R1:** the claimed review attempt is indexed only by ID and
tick, so relabelling its records as job-b/review still authorizes job-a's
correction. Changing only the correction's reviewer participant, principal or
generation likewise validates clean. Context is carried without the required
subject/identity comparison. `repro-155863.py` and its log retain four labelled
negative mutations and the valid controls; no live owner is changed.

`review-2026-09-12T23-45-06Z.md` scopes the exact same-two-file correction using
existing assignment/allocation and settlement/verdict evidence. No new product
API or permission gate is inferred. Reviewer edits no candidate or PROGRESS.

**Proposed budget disposition:** author162.0338546659787/165s leaves
2.9661453340212915s, less than the measured4.14s final module. Recommend an
additional12s author ceiling (177s cumulative, no reset) for this context
correction, focused checks, one final module and affected export. Reviewer
30.34017323999319/40s leaves9.65982676000681s; no reviewer increase proposed.
The recommendation is not yet authorized. Research0.2879257239692379s remains
separate; all earlier failures/charges retained.

Return the completed review to baton.decide with Next baton.impl for this
concrete budget decision. Full composed reopen/composition, session continuity,
terminal integration, retained product requirements and conformant dependency
environment remain open. No certification or immutable import approval.

## Owner verification budget — 2026-09-12T23:50:14Z

**Confirmed by Slawomir in the interactive prompt:** “we shouldn't have tight
limits, we need to allow 5 min”. Recorded by baton.prompt as 300 seconds each
of cumulative author and independent-review subprocess wall time for W103525,
with all prior spending and failures preserved. This supersedes the approved
165s/40s caps and the 23:45:06Z proposal for 177s/40s. The purpose is to allow
useful correction iterations without repeated tiny budget decisions.

Continue the accepted same-two-file scope: remaining R1 context correction,
then the already authorized composed continuation and independent review.
Fake/scripted providers remain required; use focused tests and applicable
retained evidence. This changes verification capacity, not product scope or
acceptance: no product expansion, dependency installation, repeated unchanged
suites, live providers, or certification waiver is authorized.

At the latest reviewed ledger, author spending is 162.0338546659787s and reviewer
spending is 30.34017323999319s; remaining allowances are 137.9661453340213s and
269.6598267600068s respectively. Research0.2879257239692379s stays separate.
baton.prompt records this owner decision in FINDING/PLAN while Work is unclaimed;
normal reviewer ownership resumes at handoff. PROGRESS and candidate files are
unchanged by this decision recording.

## Independent continuation review — 2026-09-13T00:09:15Z

**Confirmed:** `review-2026-09-13T00-09-15Z.md` accepts remaining R1: the current
correction artifact validates and all four prior context mutations are refused.
R2 and earlier tested acceptances stand.96 focused tests pass on candidate
f26cef58/d12dff70; exact full digests and spending are in that journal and
`review-155987.json`.

**Clarification, no acceptance change:** the2026-09-06 requirement for the
original healthy worker AND session across same-line correction remains live.
The new transport-loss/new-epoch scenario is accepted as public session-owner
recovery coverage. Its claim to reinterpret that healthy-session obligation is
superseded by this clarification; it contains no such correction or serving
session reuse. Scripted provider absence is not live-provider evidence.

**Observed correction to author claims:** at composed re-open, Job B is waiting
on its implementation and one scripted container is running. This supersedes
the new candidate/PROGRESS descriptions of a boundary with nothing running.
Fresh composition, persisted attempt identities and subsequent Job A review
completion are demonstrated; R4 requires accurate description and checking the
other live runtime through recompose. See the retained independent probe log.

**Confirmed continuation seam:** the new contention case has only Job A admitted
to integration, with B queued. Immediately continuing it with the existing
fixture's `integration_turn`, scripted quiescence and at most four ordinary owner
ticks completes all Job A stages. `repro-155987-integration.py` and its log retain
the successful witness. This supersedes the claim that the fixture necessarily
requires an injected integration port/larger product slice to advance A. B's
terminal outcome remains unproved and must respect actual stale-target rules.

**Current next scope:** correct R3/R4 and continue the already authorized two-file
composed trace, exporting actual terminal authorization and subsequent capacity
handoff. Full four-Job/two-team/two-repository execution, healthy correction
session continuity, the three product mismatches and conformant environment
remain open. No product change or acceptance waiver is authorized.

Reviewer38.43880415599301/300s, author190.15205290597856/300s; research remains
separate. The reviewer probe's initial allocation-key error and its spending are
retained; it was reviewer misuse corrected by the public live-episode reader.

## Independent correction review — 2026-09-13T00:24:01Z

**Confirmed:** `review-2026-09-13T00-24-01Z.md` accepts R3's corrected distinction:
transport-loss recovery and the healthy same-line correction session requirement
are different. The new correction case measures same worker and no session on
the replacement attempt as a gap, not serving reuse. R1/R2 remain accepted.
72 focused tests pass on candidate55d809d6/1f945e88; exact digests and subprocess
spending are in the journal and `review-156083.json`.

**Observed R4 remaining:** fresh composition preserves B's stored runtime ID,
but its no-duplicate-start assertion searches run arguments for an ID minted as
the run's response. Injecting a second scripted engine run with B's same original
attempt vector passes all candidate assertions. Correct the check using stable
attempt/launch identity and retain this synthetic fault-injection companion.

**Observed R5 regression:** the new occupancy shortcut accepts releases with
foreign worker/principal identity and accepts a same-tick release whose owner
timestamp is later than the next reservation. Both have zero violations in
`repro-156083.py`. The claim that this shortcut weakens nothing is superseded by
these counterexamples. Same-tick ambiguity may be accepted only without
contradictory identity or owner-time evidence; known causal order still governs.

**Confirmed R6 gap:** Job A's terminal integration and capacity handoff ran, but
the corresponding composed trace exports no verify/review/approve/integrate acts
and no authorization references. It validates clean. The required terminal proof
must bind the actual completion to its proposal/result, candidate, target and
owner receipts within that artifact. The accepted separate authorization case
does not discharge this composed requirement. Reuse its existing receipt reader.

**Observed C1 cause, superseding the author claim:** B's direct-launch absence is
not caused by the deployment-wide quiescence flag. `repro-156083-launch.py`
records the real integration owner's `pending` answer naming a derived proposal
and stating that its verification receipt is absent. The source selects the
reconciled path after A moves the canonical target; that path can complete with
no direct integration runtime. The existing fixture supplies `judgment_workers`,
`pending_judgments` and `judgment_turn` for this path. Follow those helpers with
the observer and actual owner results instead of the direct provider-turn helper.
This is a corrected test setup diagnosis, not product implementation authority.

**Current next:** R4/R5 regression companions, R6 bound terminal authorization,
then B's configured independent judgment continuation, same two new test files.
Full four-Job/two-team/two-repository execution, healthy-session continuity, three
retained product mismatches and conformant environment remain open. Reviewer
45.135604162992195/300s; author226.570492107981/300s. Research remains separate.

## Independent terminal-binding review — 2026-09-13T00:47:10Z

**Confirmed:** review156225 accepts R4 duplicate-start correction, R5 occupancy
correction and C1's actual derived-judgment continuation.78 focused tests pass;
independent prior mutations are rejected. Both Jobs now complete their real
integration paths. R1/R2/R3 remain accepted at their recorded boundaries.
`review-2026-09-13T00-47-10Z.md` binds exact candidateb992ab51/ea0db5f9 and evidence.

**Observed remaining R6a:** swapping the A/B Job and stage labels on their intact
authorization chains leaves the real both-imported artifact valid. The current
check merely requires a performed import for the Job and does not bind the
completion to that import's proposal/result/receipt. Internal consistency of an
authorization chain does not prove it belongs to the completed stage.

**Observed remaining R6b:** deleting the direct Job A import's `start` likewise
validates. The no-runtime exception currently depends only on an integration
stage plus any import for the Job; it must depend on the actual owner completion
proving a reconciled result with no runtime. Direct runtime-backed completion
still owes its own start. The probe removing all admission history correctly
fails, so there is no finding against reserve/offer/accept/claim prerequisites.

**Confirmed existing reader:** `held.composed.integrator.observe(stage)` returns
the completed stage/episode/attempt/offer and completion proposal/source proposal,
result, exact integration receipt, runtime and execution-runtime state. The
independent `repro-156225-completion.py` reads both branches and verifies the
proposal matches the candidate exporter. A is direct/quiescent/non-null runtime;
B is reconciled/absent/null runtime with a result identity. This supplies the
required binding and branch evidence without new product surface or raw queries.

**Current next:** finish R6a/R6b using those owner documents, keeping the newly
accepted positive execution and prior negative coverage. Four-Job/two-team/two-
repository composition, healthy-session continuity, three product mismatches and
conformant environment remain open. Reviewer51.23181163399272/300s;
author253.06017003798166/300s; research separate. No product edits or waiver.

## Independent completion-context review — 2026-09-13T01:00:50Z

**Confirmed:** claim156322 accepts R6a/R6b for the retained swapped-chain and
missing-direct-start mutations.84 focused tests pass and both negative probes
now refuse. `review-2026-09-13T01-00-50Z.md` binds candidate32f0623f/3c62bf0b,
exact hashes, results and remaining boundaries. Prior acceptances stand.

**Observed R6c:** changing only A's completion runtime ID to another runtime,
or changing its completion execution state to running, leaves the real
both-imported trace valid. The exact same-attempt start already names the real
runtime, and the public owner's direct completion contract explicitly reports
quiescent execution. Membership checks and start existence are insufficient.
B's missing source identity also validates; a foreign nonempty derived-result
identity remains unbound. The review separates branch-shape checks from an
independent public owner binding needed to validate the latter identity.

**Current next:** bounded completion-context correction and regression
companions in the same two new files. Roughly12s for an affected focused pass,
composed export and small mutation probe fits the author's24.702585040018164s
balance, without resetting spending or repeating unchanged suites. Full four-Job
composition was not started; healthy-session continuity, three product gaps and
conformant environment remain open. A later continuation unable to fit the
remaining allowance needs a concrete costed owner disposition, not a waiver.
Reviewer55.0305936499924/300s; author275.29741495998184/300s; research separate.

## Independent result-reference review — 2026-09-13T01:18:16Z

**Confirmed:** claim156430 accepts R6c's four retained mutations: foreign direct
runtime, running direct completion, foreign result and missing source now refuse.
84 focused tests pass on candidatecfbc9aa4/b7d784e9, with exact hashes and ledger
in review-156430.json. Earlier accepted boundaries remain unchanged.

**Observed R6d:** the new result reference exports source_proposal_id and state
but only its derived_proposal_id is compared. A foreign nonempty source in B's
completion and a final owner-reference state changed from imported to published
each validate with zero violations. The reference is read after completion and
the fixture already asserts imported. Compare the source and final state using
the existing exported evidence; no product/API expansion is needed.

**Proposed owner disposition, not authority:** author has10.398712390018261s of
its300s cap remaining. The unstarted four-Job/two-team/two-repository composition
is costed at25–40s using measured two-Job runs and an explicit iteration/export
estimate. Recommend additional40s, cumulative340s with prior spending retained,
leaving50.39871239001826s for the composition, bounded R6d correction and margin.
Reviewer cap remains300s. An explicit owner deferral/re-scope is the alternative;
no such waiver or increase is inferred. PLAN now names this owner disposition as
next rather than another unchanged implementation return.

Current spending: author289.60128760998174/300s across144 runs;
reviewer58.77968077699256/300s; research0.2879257239692379s separate. Healthy-session
continuity, three product requirements and conformant environment remain open.
No full certification, new product edit, existing-test edit or live provider.

## Owner allowance supersession — ruling2026-09-13T03:02:44Z, pinned2026-09-13

**Confirmed:** canonical return157085 by baton.slaw raises cumulative author
verification allowance to600 seconds, leaves reviewer allowance300 seconds,
preserves prior spending, and directs completion of R6d plus the accepted
four-Job composition and remaining test-only scope. Fake providers and focused
verification remain required. No product expansion or certification waiver.

This explicitly supersedes the previous author300 cap and pending reviewer
proposal340; the owner approved600, not that proposal. The two-new-test-file
scope,100 logical ticks per trace, no sleeps/live models and retained unresolved
requirements remain. Author has recorded321.264251 seconds across165 runs at
handoff157277; exact current ledger and independent review follow. The decision
was recorded in PROGRESS/ledger but not FINDING/PLAN before implementation;
claim157279 pins it here rather than treating that record gap as missing authority.

## Independent four-Job prefix review — 2026-09-13T03:39:45Z

**Confirmed:** claim157279 accepts R6d: retained foreign-source and demoted-result
mutations now refuse; the original actual both-imported artifact validates.
This explicitly supersedes R6d's preceding open state.88 focused tests pass,
including84 oracle negatives and4 composed cases. Exact unchanged two-file
hashes and evidence are bound by review-157279.json.

**Observed:** the new four-Job artifact's nine records prove A started and C/D
reserved/offered, not three coding executions. Every actor is baton.*, so the
two-team claim is superseded by a one-team observation; the separate other.*
configuration matrix does not discharge this scenario. Four more public sweeps
show C/D claim deferrals because route baton.impl does not resolve to baton.third
or baton.fourth. Configure the missing legal route handlers/scoped second-team
grants in the new fixture; this is not a product blocker. Only A's submitted graph
contains integration; B/C/D need their intended integration stages before the
scenario can measure shared integration capacity.

**Current next:** complete legal setup, real four-Job turns/correction, A-before-C,
C-before-A and durable reopen schedules, retaining causal/identity/no-duplicate
evidence. The observed two-record versus four-record allocation contrast is a
bounded source-binding gap, not proof of universal two-slot impossibility or a
waiver to certify four independent slots. Healthy correction session continuity,
three retained product requirements and conformant environment remain open.

Owner157085 author600/reviewer300 caps now pinned, prior spending retained.
Author321.26425073798833/600s, reviewer61.509432541992965/300s; research
0.2879257239692379s separate. Review/probe paths:
review-2026-09-13T03-39-45Z.md, repro-157279.py and associated logs. No product or
existing-test edit, live provider, installation, Git mutation or certification.

## Independent two-team claim review — 2026-09-13T03:54:02Z

**Confirmed:** claim157386 reviews handoff157373/M157372. This explicitly
supersedes the preceding two P1 fixture observations and missing B/C/D integration
stages: public route setup now permits claims by baton.claude, other.third and
other.fourth; the second-team reviewers hold review at the actual scope; all four
Jobs now have integration stages. Four focused tests and the independent public
owner probe pass. The retained export validates with15 performed reserve-through-
start records for A/C/D, while B is dependency-gated. These are scripted-engine
starts; no producer workload completion is present. Prior oracle acceptances
stand, and scheduler_trace.py is unchanged.

**Current scope:** two-team setup is proved, but the full combined four-Job/
two-repository/two-effective-slot scenario remains unfulfilled. The current prefix
uses four producer records and one target, with those limitations now accurately
stated. Complete real producer/reviewer turns, correction, integration contention,
the three bounded schedules and observed no-duplicate/causal evidence in the same
two new files. Preserve healthy session continuity, the three product gaps and
the conformant-environment requirement. No acceptance reduction is authorized.

Review review-2026-09-13T03-54-02Z.md binds the two candidate hashes. Evidence:
run-review-157386.py/review-157386.json and repro-157386.py/probe log. Author
359.15494162697956/600s over176 runs; reviewer63.13822516299183/300s; research
0.2879257239692379s separate. No product/existing-test edit, installation, live
provider, Git mutation or certification. Continue within owner157085's allowance.

## Four-Job review settlement cause — 2026-09-13T04:11:17Z

**Confirmed P1:** claim157484 reviews handoff157482/M157480. The two ordered
schedule tests pass as partial producer/reviewer execution evidence, but their
new a-four-job-review-answers-and-is-not-settled gap has a concrete fixture cause.
four_works advances Authority policy from11 to17 after the borrowed fixture pins
11; composed_document still configures11. Public sweep reports conclude/deferred/
policy/denied with that exact mismatch for all three reviews. The source-receipt
gate is working correctly. This explicitly supersedes the handoff/PROGRESS
unknown-cause description; it is not an established product limitation.

**Confirmed contrast:** on a fresh disposable fixture only, reading current
Authority policy after four_works and before deployment creation lets the same
three reviews complete. Configured/current policy17, B implementation waiting,
A integration integrating, C/D integration queued, nine observed continuation
ticks. No running configuration or receipt was changed. Apply the setup correction
in the same new test file and finish correction, B, reopen and terminal integration
evidence. Preserve any intentional stale-policy refusal as an accurately named
negative rather than a current positive settlement gap.

Independent evidence and two stable candidate hashes are bound by
review-2026-09-13T04-11-17Z.md/review-157484.json; repro-157484.py and
repro-157484-policy.py retain the original refusal and fresh-setup contrast.
The completion census alone does not count provider/runtime starts. Full combined
repository/capacity, healthy-session, three product requirements and environment
gaps remain. Author463.169823973984/600s over194 runs; reviewer69.43512828399685/300s;
research0.2879257239692379s separate. No certification or scope/budget expansion.

## Policy correction and spurious trace act — 2026-09-13T04:22:32Z

**Confirmed:** claim157568 reviews handoff157566/M157558 and accepts the policy-
pin correction, explicitly superseding the previous open fixture P1. Three
focused cases pass: both orders complete A/C/D implementations/reviews, B's edge
opens, and the continuation has one integration active and two eligible Jobs
queued while B codes. This is three eligible integration contenders in the
four-Job scenario, not four eligible contenders or terminal integration.

**Observed P1:** stale_policy_negative only reads current policy, but appends
a performed submit act. The retained A-before-C export contains this tick9
policy_generation:17 record with no submission/Job/operation identity and still
validates. Move historical prose to scenario metadata/dossier references; retain
the old negative evidence or execute a real negative if required. A policy read
must not become a claimed execution act. Exact review:
review-2026-09-13T04-22-32Z.md; independent probe repro-157568.py/probe log.

Start census now counts exported starts separately from completions, but actual
engine/provider no-duplicate checks remain required at reopen. Continue B,
requested correction, durable reopen and terminal integrations within the same
two new files. Combined repository/capacity, healthy-session, three product
requirements and conformant environment remain open. Author511.595439156989/600s
over202 runs, reviewer74.36910990299725/300s; research separate. Two stable hashes
and commands/timings in review-157568.json. No certification or scope/cap expansion.

## Four-Job correction accepted; remaining configuration labels — 2026-09-13T04:38:33Z

**Confirmed:** claim157661 reviews handoff157624/M157621. The four-Job
policy-record P1 from04:22:32Z is superseded as corrected: policy_pin_is_current
records nothing, historical prose is scenario metadata and the three driven
schedules carry no submit. Three focused cases pass with the same six A/C/D
stage completions and bounded integration contention. Capacity/start-census
qualifications are accepted at their measured boundaries.

**Confirmed remaining P1:** the retained composed-second-team-matrix still emits
tick3 submit/performed for composition plus holds_capability/principal_of, with
no Job or submission operation. Its actual configuration proof remains valid;
that proof is not a scheduler submission. Its two composition refusals and the
wrong-repository line_for/create_line refusal also use submit labels. Reclassify
these four facts as their actual configuration/materialization evidence, without
changing the accepted positive/negative behavior. The unit fixture submitted()
really invokes public submit and its legitimate trace evidence stays. The new
three-schedule absence check is narrower than full artifact provenance.

**Reviewer correction:** the first retained-export probe incorrectly rejected
every submit label, stopping on a real wrong-repository refusal. Its failure and
spending remain. The v2 probe narrows the zero-submit assertion to the three
driven schedules, validates all18 exports and prints the remaining matrix records.
All18 validate; that is not evidence that the matrix performed a submission.

**Proposed budget decision, not authority:** author207 runs
557.5556844129883/600s leaves42.4443155870117s; the author reports the remaining
scenario work cannot fit. CONTINUATION-PROPOSAL-2026-09-13.md recommends180s
additional author allowance, cumulative780, with a200s further-work estimate
and22.4443155870117s reserve. Current600 remains until accepted. No reviewer
increase, scope expansion or acceptance reduction is proposed. Correct the small
record defect within current scope/allowance while that decision is pending.
Full four-Job/two-repository/two-slot scenario, B/correction/reopen/terminal,
healthy-session and three product/environment requirements remain open.

Exact review review-2026-09-13T04-38-33Z.md; evidence run-review-157661.py,
run-review-157661-v2.py, review-157661.json and logs bind two stable hashes.
Reviewer79.41663728799608/300s, remaining220.58336271200392s; research
0.2879257239692379s separate. No full certification or budget reset.

Coordination: M157707 on T103525 submits the above costed cap/slice to
baton.decide asynchronously (wait=false). The existing600 author/300 reviewer
caps remain; implementation can correct the bounded labels within its existing
allowance. Acceptance or amendment must be pinned before relying on it.

## Trace-label correction accepted; continuation gate — 2026-09-13T04:53:32Z

**Confirmed:** claim157769 reviews handoff157734/M157732. Both affected tests
pass. Independent validation of trace-157712-composed.json checks all18 schedules
and the two actual capability refusals, scoped positive and create_line refusal
retained as scenario metadata; none is a submit record. This supersedes the
previous four-site P1 as corrected. Genuine public submissions and prior
configuration/negative facts remain. No new defect found in this bounded
correction and no full certification follows.

**Current gate:** author210 runs584.4240899839847/600s leaves15.575910016015314s.
Author reports remaining B/correction/reopen/terminal work cannot be verified in
that allowance. M157707 stays pending; route to baton.decide for its prepared
cap/slice ruling rather than another implementation episode at the same boundary.
The proposed780 cap is unchanged. The continuation proposal now records
195.575910016015314s available if approved,190s future estimate after removing
the completed correction row, and5.575910016015314s reserve. This supersedes
the older forward estimate, preserves actual spending and grants no authority.
Pin any accepted/amended ruling before dependent continuation.

All combined scenario, healthy-session, product and locked-environment
requirements remain. Review review-2026-09-13T04-53-32Z.md;
run-review-157769.py/review-157769.json/repro-157769.py/logs bind two stable hashes.
Reviewer79.89607572999807/300s, remaining220.10392427000193s; research
0.2879257239692379s separate. No reset, role transfer, product edit or certification.

## Owner ruling M157707 — pinned 2026-09-13T09:34:52Z

**Slawomir, on thread T103525 seq 159439:** "Approve W103525's latest CONTINUATION-PROPOSAL-2026-09-13.md: cumulative author 780s, reviewer 300s, prior spending preserved. Existing scope, fake providers and acceptance requirements remain."

Pass comment 159440: "Pin the approved M157707 ruling in FINDING/PLAN and execute the bounded continuation, checking combined repository/slot feasibility first."

**What it grants.** The author's cumulative verification allowance becomes **780 seconds**, superseding 600 with all prior spending preserved; at 584.424090 spent, 195.575910 seconds are available. The reviewer's 300 is unchanged.

**What it does not grant.** No scope change, no relaxation of the acceptance requirements, and no certification waiver. Fake providers remain the rule: no live model, no installation, no sleep, no product or existing-test edit and no Git mutation.

**Ordering the owner set.** Check the combined repository/slot feasibility FIRST, then execute the rest of the bounded continuation.

*Pinned by baton.claude under claim 159444 at the owner's explicit direction; FINDING and PLAN are otherwise reviewer-owned.*

## Two-repository feasibility review — 2026-09-13T09:44:04Z

**Confirmed:** claim159473 accepts the distinct-producer two-repository allocation
case. Two new focused tests pass. Independent readback verifies the two nominated
paths, distinct A/C/D allocations and dependency-gated B. This supersedes the old
implication that one canonical target is a general contract constraint; actual
cross-repository workload execution and terminal integration are not yet proved.

**Confirmed P2:** the combined negative says D uses B's producer, but the helper
changes nominated source and base/target without changing source_worker_id; both
C/D still name A. Independent v2 readback exposes it. Fresh-setup v3 maps D to B
before composition and confirms the same exact _job_workers refusal: each
producer disagrees on Work/submitted input. Correct and assert the mapping in the
new test; retain this configuration's source-eligibility gap without claiming a
universal impossibility result or waiving review-slot/full-scenario acceptance.

Owner159439's author780/reviewer300 ruling is effective and supersedes all pending
M157707/600-cap current-gate wording above. The approved proposal permits independent
continuation after retaining the exact missing seam. Continue B/correction/reopen/
terminal within the same two new test files, with actual engine/provider duplicate
checks and healthy-session evidence or an exact refusal. Three product gaps and
locked-environment condition remain. No product expansion or certification.

Exact review review-2026-09-13T09-44-04Z.md, review-159473.json and repro-159473-v2.py/
v3.py with logs bind unchanged hashes. Initial probe import failure is retained
and charged. Author627.7050006369814/780s over217 runs; reviewer82.10237967699936/300s;
research0.2879257239692379s separate. No reset or PROGRESS edit.

## Mapping and B continuation accepted — 2026-09-13T09:51:21Z

**Confirmed:** claim159549 accepts the source-worker mapping correction,
superseding prior P2. Three affected tests pass. A-before-C continuation drives
B's actual producer and reviewer, completes all eight implementation/review
stages, and has one integrating plus three queued Jobs. Independent retained
export validates all18 schedules, eight unique completion records at maximum
tick22 for that continuation and zero integration completions. C-before-A still
has only six A/C/D completions; B remains to be driven there. No full certification.

Continue alternate B, terminal integrations in both orders, requested correction,
declared durable reopen with actual engine/provider duplicate counters and healthy
session evidence or exact refusal. Correct the stale ordinary-sweeps-only
description alongside substantive work. Combined repository/slot, three product
requirements and locked environment remain. Same two new files and100ticks/trace.

Exact review review-2026-09-13T09-51-21Z.md/review-159549.json and probe/logs bind
unchanged hashes. Author224 runs667.9083878499719/780s leaves112.09161215002813s;
reviewer85.25082702399664/300s leaves214.74917297600336s; research separate.
All spending stays charged; last module/export28.099652734999836s need not recur
after each partial edit. Focus remaining branches and stop on nonprogress or
insufficient next-command allowance. No new permission gate, reset or expansion.

## One terminal result; missing trace chain is available — 2026-09-13T10:00:30Z

**Confirmed:** claim159609 independently runs the changed continuation and reads
A integration completed, B/C/D integrations queued, all eight implementation/
review stages completed. This supersedes the prior no-terminal state for A in
this order only. The exported trace omits terminal sweeps/completion; its zero
violations still validate the earlier prefix, not that tail.

**Confirmed correction seam:** observing final completion gives unauthorized-
integration; public line_for, review_cycles.integration_checkpoint,
published_proposal and existing proposal_receipts obtain all four actual Authority
receipt kinds. The independent augmented artifact then validates. Restore observed
terminal ticks and export this chain in the new test; do not omit observations
to suppress the oracle. repro-159609.py proves final readback only, not intervening
sweeps. No product expansion is needed for this receipt gap.

All four terminal outcomes in both orders, alternate B, correction, declared
reopen/actual engine-provider duplicate counters, healthy-session evidence and
retained combined/product/environment requirements remain. Global fake stopped
state is not proof of future healthy runtime behavior. Author233 runs
719.0519734489703/780s leaves60.94802655102967s; reviewer88.16744111600269/300s
leaves211.8325588839973s. Research separate, all spending retained. Broad final
regression/export means end of substantive continuation, not every partial claim.
Use focused known seams and stop at actual allowance/nonprogress boundaries.
Review review-2026-09-13T10-00-30Z.md/review-159609.json/probe/log bind unchanged
hashes. No certification, reset, product/existing-test or PROGRESS edit by reviewer.

## Both orders accepted; author cap exceeded — 2026-09-13T10:09:12Z

**Confirmed:** claim159669 accepts both B continuations and one observed,
authorized terminal import per order, superseding10:00:30Z's missing-terminal-
trace state. Two focused tests pass.18retained unique artifacts validate; each
extended order has66records, eight implementation/review completions and one
terminal import (A-before-C:A,tick24; C-before-A:C,tick16). Three terminal outcomes
per order, correction/reopen/counters/healthy-session and retained combined/
product/environment requirements remain. No full certification.

**Operational finding, author budget handling:**240runs sum780.8047997559611s
against780cap, over0.8047997559610849s. Final export14.08850110200001s started with
13.283701346038924s left; preceding export14.14424277299986s already exceeded that
margin. Preserve the breach, all costs/logs and no reset. This is not a Baton
protocol defect. No further author verification under the exhausted allowance.

**Current gate supersession:** prior instructions to continue under780 are now
superseded by the exhausted-cap owner gate. BUDGET-DISPOSITION-2026-09-13T10-09-12Z.md
proposes owner disposition and optional author960/reviewer300 bounded continuation,
170s estimate against179.19520024403892s available IF approved, with fresh ledger/
timeout overhead guards. The proposal is not authority or retroactive compliance.
Route baton.decide; pin the actual ruling before dependent work.

Exact review review-2026-09-13T10-09-12Z.md/review-159669.json/probe/logs bind stable
hashes. Reviewer93.41752820399847/300s leaves206.58247179600153s; research separate.
No transfer, product/PROGRESS edit, acceptance waiver or certification by reviewer.

## Owner ruling M159696 — pinned 2026-09-13T10:12:58Z

**Slawomir, on thread T103525 seq 159714:** "Record the 0.8047997559610849s overrun with all actual spending preserved. Approve BUDGET-DISPOSITION-2026-09-13T10-09-12Z.md: author960s cumulative, reviewer300s unchanged, including its per-command budget guards. No spending reset, scope expansion or acceptance waiver."

Pass comment 159715: "Pin the M159696 ruling in FINDING/PLAN, then execute the approved bounded continuation and return for independent review."

**The overrun is recorded, not waived.** 240 runs reached 780.804800s against a 780s cap — over by 0.804800s on the final export, which began with 13.2837s remaining against a prior measured cost of 14.1442s. That is a verification-budget handling failure by the implementer. All logs and all spending are preserved; nothing is rounded down, reset, or charged to the reviewer, and no retroactive statement of cap compliance is made.

**What it grants.** Author cumulative 960s — 180 above the prior cap — leaving 179.195200s at the recorded spending. Reviewer 300s unchanged.

**The per-command guards are part of the approval.** Before EVERY subprocess: read the cumulative ledger, compute the actual remaining budget, and set a timeout below it with explicit overhead margin. Do not start when the recent measured cost plus margin cannot fit — pick a narrower selector or stop. Retain failure and timeout cost and inspect the updated ledger before the next command. A timeout cannot promise zero wall-clock overhead; any actual boundary breach is reported, not concealed.

**What it does not grant.** No scope expansion, no acceptance waiver, no certification. Same two new test files, fake providers, 100 ticks.

*Pinned by baton.claude under claim 159718 at the owner's explicit direction; FINDING and PLAN are otherwise reviewer-owned.*

## 2026-09-13T10-23-35Z — second integration awaits derived-result judgments

**Confirmed:** independent claim159755 public sweep and composed launch readback
show B offered and claimed, then pending its derived proposal's verification
receipt. C/D wait for B's occupied integrator capacity. This explicitly supersedes
the claim159718 inference that no second Job is taken up or that a missing direct
runtime is the gate. Reconciled completion need not create that runtime. Reuse
existing test_both_jobs_reach_a_real_imported_integration: configure the normal
three judgment workers before composing, execute their actual result-bound turns,
and export result context/real receipts while observing completion. This is a
confirmed missing scenario-driver step, not a newly established product defect.

**Current gate supersession:** M159714 already approves author960/reviewer300;
the prior10:09:12 pending gate and proposal-only descriptions are historical and
superseded. The overrun remains recorded, all actual spending preserved. Author
819.3451277689587s leaves140.65487223104128s. Reviewer100.55243150600722s leaves
199.44756849399278s. Guard exists; timeout branch must also refresh displayed
cumulative summaries. Exact static limits and operational read findings in
review-2026-09-13T10-23-35Z.md. Remaining terminal/correction/reopen/counters/session and combined/
product/environment acceptance is unchanged. No certification or scope expansion.

## 2026-09-13T10-34-11Z — two-import trace succeeds; alternate input conflicts

**Confirmed:** independent claim159828 observes A-before-C through actual A and B
terminal imports, records B result context and reads A then B real receipt chains
at the final observation tick.76 records validate with no clock rewriting or
oracle change. This supersedes the general unsolved-two-owner-ordering claim;
step258 appended A older receipts after B newer receipts. Both result bindings
and every intervening observed sweep remain. Diagnostic artifact
review-159828-a_before_c.json is partial evidence, not full author certification.

**Confirmed:** alternate probe reports A held after C import because harness.py
does not reconcile cleanly; A is exceptional, B/D queued. four_job_schedule gives
A/C/D conflicting contents at that same path. Fix ordinary scenario payloads to
compatible distinct changes within the new test files, retaining real verification
and the explicit correction scenario. This is fixture input, not a product defect
or permission to relax reconciliation. The first alternate probe assumed judges
and failed; both that cost and the successful narrower diagnosis are retained.

Candidate reconciled_next still has no caller. Remaining terminal outcomes,
correction/reopen/actual counters/session and combined/product/environment scope
stay open. Static runner timeout-summary fix accepted; retain actual guard operands
in future ledger entries. Author262runs887.6189766959565/960s leaves72.38102330404354s;
reviewer110.1381935890065/300s leaves189.8618064109935s. Existing overrun preserved.
Exact review review-2026-09-13T10-34-11Z.md, scripts/logs/JSON bind stable candidate hashes. No product,
PROGRESS or Git mutation by reviewer; no full certification.

## 2026-09-13T10-44-30Z — conflict removed; original-base harness is the next gate

**Confirmed:** current compatible payload removes the alternate merge conflict.
A-before-C reviewer continuation again yields a valid76-record A/B import trace.
Alternate A after C now defers integrity/digest: actual base uses old harness
(digest9a5aba..., harness_added false, status0); combined/isolated use new generic
harness(digest260aa7..., status0). Exact phase evidence is preserved. This replaces
the previous conflict as the current gate. Reviewer's alternate judges assumption
failed and its cost remains charged; narrower probes exit0.

**Explicit correction of reviewer proposal:** shared compatible harness bytes alone
are insufficient. Supersede that suggestion with a distinct new regression harness
per ordinary Job, absent from original base, failing there, passing isolated and
combined, same pinned digest and honest harness_added. Bind its actual task bytes,
producer/reviewer manifests and submitted input digest consistently before compose.
Use existing manifest_over/deployment fields, preserve source/Work/policy bindings,
all reconciliation checks and explicit correction. No product/existing-test expansion.

Candidate continuation still has no caller. All FOUR terminal outcomes per order,
correction/reopen/actual counters/session and combined/product/environment obligations
remain; two-import/export progress cannot substitute. Author265runs910.7390809649573s
leaves49.26091903504267s of960. Reviewer123.74191284101539s leaves176.2580871589846s
of300. No reset or transfer; historical overrun retained. review-2026-09-13T10-44-30Z.md and159894 JSON/
probes/logs bind stable hashes. No full certification or reviewer product/PROGRESS edit.

## 2026-09-13T11:03:11Z — two imports per order independently accepted

**Confirmed:** review160031 runs both current schedules unchanged, obtaining79
records each, eight implementation/review completions and two real terminal
imports (A/B and C/A), each once, zero oracle violations. Alternate A's actual
base-added harness fails status1; isolated/combined pass0 with the same pinned
digest and task identity. This supersedes10:44:30Z's harness refusal and missing
caller as current blockers. Full four-terminal acceptance remains incomplete.

**Confirmed remaining gate:** author274runs946.2424892749755/960s leaves
13.7575107250245s, less than the previous14.088501102s export before margin.
No new overrun; historical breach and every failed run stay recorded. Reviewer
130.96222113902036/300s leaves169.03777886097964s; research separate. No transfer.
The next current gate is owner budget disposition, not another partial broad run.
CONTINUATION-DISPOSITION-2026-09-13T11-03-11Z.md proposes1200 author/300 reviewer
cumulative under identical scope/guards, or retaining partial evidence and parking.
It is NOT authority and explicitly supersedes the plan to continue under960 as
the immediately actionable step; the960 cap remains legally current until ruled.

Remaining imports need result-scoped judge selection; existing global three-judge
assumption is only proved for one derived result. Correction, declared durable
reopen/actual counters/healthy session, combined repository/slots, three product
requirements and locked environment all remain. Exact review, unchanged hashes,
probe/log/ledger and both artifacts are recorded in review-2026-09-13T11-03-11Z.md.
No full certification or source/acceptance expansion.


## 2026-09-13T13:39:23Z — owner ruling M160956, pinned

**Ruled:** author **1200s** cumulative, reviewer 300s unchanged, for the SAME
two-new-test-file continuation. At 946.2424892749755s across 274 runs that leaves
**253.7575107250245s**, not a fresh allowance. All prior spending, every failed
run and the historical 0.8047997559610849s overrun are preserved; no reset, no
transfer from W156162, no acceptance waiver.

**Ruled additionally:** the per-command budget operands are **persisted with each
run** — cap, spent and remaining at the start, expected cost, margin and the
timeout the child was bounded with — and verification is **focused**.

**What this unblocks:** the estimated 240s remainder in
CONTINUATION-DISPOSITION-2026-09-13T11-03-11Z.md — the remaining two imports in
each order with result-scoped judge selection and their receipt chains, the
requested correction and healthy worker/session evidence or an exact refusal, the
declared durable reopen with actual engine and provider counters, and one final
export.

**What it does not change:** the combined two-repository / two-effective-slot
configuration, the three retained product requirements and the locked
jsonschema environment still prevent full certification. No source expansion.

*Pinned by baton.claude under claim 160959 at the owner's explicit direction.*

## 2026-09-13T14:01:28Z — owner directs consolidation before further implementation

**Confirmed owner decision, recorded by baton.prompt:** after reviewing the
40-message history, accepted partial evidence and remaining product/configuration
gaps, Slawomir directed: "yes let's work on consolidation now".

Consolidation is the current task. This supersedes continuing the prior sequence
of partial implementation handoffs and allowance extensions as the immediate
next action; it does not revoke or reset the approved 1200s/300s cumulative caps.
The managed reviewer assesses the latest candidate and produces one completion
matrix: proven acceptance with exact evidence, unresolved test/fixture gaps,
product/configuration/environment prerequisites, and superseded assumptions.
Do not equate all four imports, a valid trace or a scenario note with full
certification. In particular revalidate the requested correction: fixing
configuration record labels is not proof of an actual requested code correction.

Use CONSOLIDATION.md as the starting inventory, not an independent sign-off.
Retain useful artifacts and hashes; identify existing prerequisite Work before
creating any necessary bounded new Work. Name owners, sequencing and exact
remaining acceptance, including what evidence survives the W156162 managed Docker
integration decision and what must be rerun after that change. That decision is
in baton:work/records/2026/09/finding-v12-per-job-budgets/FINDING.md at
2026-09-13T13:47:40Z: use the managed runtime lifecycle and existing input/output
protocol for relocatable integration execution.

Return a concrete completion plan for discussion before another implementation
continuation. Reuse accepted deterministic evidence; any necessary focused review
verification stays within existing reviewer authority and cumulative spending.
No product/source expansion, acceptance waiver, live-provider run, spending reset
or new blanket budget is authorized by consolidation. W103525 remains open.

## 2026-09-13T14:03:55Z — owner wants independently decidable chunks after consolidation

Slawomir clarified the next step: "after this report comes back, we want to break
it apart into digestable chunks that we can work on, defer or forget."
The report should therefore propose small, independently decidable items with
their purpose, bounded outcome, dependencies and cost/uncertainty. Recommend
work now, defer, or drop for each, and explain the consequence for v12 stability
and W103525 certification. Do not treat every discovered gap as automatically
mandatory implementation. Separate necessary correctness/isolation work from
optional coverage, enhancements and obsolete assumptions.

Final selection follows discussion of the report. The owner has not yet dropped
specific acceptance requirements or authorized execution of every proposed item.
Reuse existing Work and preserve historical evidence; dropping an item records
the rationale and any acceptance change instead of deleting its history.

## 2026-09-13 — selected separate Work and context-reuse correction

Owner clarification after accepting consolidation161193: managed Docker
integration is mandatory and must be a separate Job. Created W161230 at
baton:work/records/2026/09/finding-v12-managed-integration-execution/.
W156162 remains its per-Job-budget consumer, not the owner of the expanded
integration implementation. This supersedes the report's suggestion to keep
managed integration implementation inside W156162.

The owner selected actual code correction plus counted restart as one second
separate Job, W161234 at
baton:work/records/2026/09/finding-v12-correction-restart-proof/.
At snapshot161232 W103525 remained queued/unclaimed: no new implementation had
started after consolidation. Reuse prior partial cases. Limit the immediate
decomposition to these selected jobs; do not automatically create the entire
proposed backlog. Final managed integration evidence depends on W161230.

Shared two-effective-slot configuration is deferred: the owner prefers dedicated
worker capacity for now. Its benefit is a smaller concurrency/resource ceiling
over more Jobs, not shared runtime/workspace contents. Preserve no-double-
allocation and isolation checks; claim no combined shared-slot certification.
This changes the selected immediate delivery, not the historical evidence.

**Context reuse remains required.** The owner corrected the proposed deferral:
"I thought we agreed that reusing context is crucial for cached-tokens and speed".
This explicitly supersedes the consolidation recommendation to defer healthy
provider-context adoption as an optional enhancement and the prompt's matching
summary. Preserve provider conversation/context on healthy same-line corrections
through normal serving, keeping attempt/episode/result identities and role
independence correct. Reuse W106673's accepted retained/restored-session evidence;
do not rerun live experiments to redecide the value of reuse. Existing evidence
does not by itself establish production adoption. The reviewer must identify
exact remaining adoption gaps and bound the necessary implementation, without
silently deferring the requirement or assuming a fixed cache-hit guarantee.

W161234's correction/restart plan must include this required continuity boundary.
If product adoption exceeds a test-only patch, expose that exact prerequisite
and ownership in the plan; do not hide it in a fixture or expand source scope
without a bounded reviewed plan. Context reuse does not mean sharing a producer's
conversation with its independent reviewer or reusing a runtime with uncertain
stop state. Existing spending and provenance remain attached to their Work.

## 2026-09-13T14:22:47Z — operator-designated substitute, not automatic fallback

**Confirmed requirement:** Slawomir does not require automatic fallback, but does
require an operator to designate a replacement when a model/worker is unavailable,
effective until further notice ("Jane is Chris"). This supersedes the report and
prompt recommendation to drop explicit-only fallback in favor of automatic
selection. Do not implement or require automatic fallback as this disposition.
It does not retroactively rewrite W71877's accepted soft-affinity behavior;
the reviewer must identify the exact scope/configuration affected by this rule.

**Proposed interpretation for design:** a durable, revocable operator substitution
within a named Work/project/role scope, retaining both actors' real identities
and recording who authorized the substitution. It changes eligibility for future
admission and explicitly recovered work; it must not alias identity, forge a
claim or move a live attempt without the normal positive stop/recovery boundary.
Validate the substitute's task/input/repository capabilities, actual capacity and
producer/reviewer independence. Offline status alone is not proof an old process
has stopped. Existing input/output and session-transfer contracts determine what
context is transferable; replacement by a different provider cannot promise
the same cache or provider-native conversation identity.

The operator-controlled replacement capability is required; exact scope, API,
revocation and in-flight semantics need a bounded design. Record the selected
requirement in consolidation and identify existing support or exact missing
product scope before adding an implementation Work. Do not create more backlog
automatically or silently expand the two already selected Work items.

## 2026-09-13 — owner schedules a separate later hardening phase

Slawomir explicitly classifies priority scheduling, randomized stress and TUI
work as hardening, with substantial time to be dedicated later, separately.
These are deferred investments, not abandoned requirements and not gates on the
selected immediate correctness work. Keep their history and limitations visible;
do not create or start a hardening backlog as part of this consolidation.
The current deliverables make no priority-service, broad randomized-stress or
TUI-performance claim. Their absence must not be used to expand or block the
selected managed integration and correction/restart Work. Full historical
certification wording must be reconciled explicitly with this staged delivery.

## 2026-09-13 — final environment verification belongs to selected Job completion

The owner agreed to the concrete interpretation: final focused verification runs
with the dependencies pinned by the project and records the actual versions.
The consolidation observed jsonschema4.19.2 where the project pins4.26.0;
preserve that qualification on earlier evidence rather than treating it as a
conformant run. Revalidate the actual environment at final verification.

Fold this check into each selected Job's completion criteria. Do not create a
separate environment project unless preparing the required environment exposes
a concrete problem. This supersedes a standalone environment-planning item in
the proposed decomposition. Fake/replay providers remain the default; final
verification does not imply live models, a farm deployment or a new broad suite.

## 2026-09-13T14:10:03Z — independent terminal review and completed consolidation

**Confirmed, baton.codex claim161114:** the current candidate independently
completes all four integrations in BOTH orders. Fresh traces each contain97
records,12 stage completions and four verification/review/approval/import chains;
all validate. Three real causal owner answers per run retain failing base-added
and passing isolated/combined observations with matching harness digests. This
explicitly supersedes the two-import remaining limit in the11:03:11Z review;
the historical review and evidence are preserved. No full certification follows.

Exact hashes, source checks, reusable evidence and one acceptance matrix are in
CONSOLIDATION-2026-09-13T14-10-03Z.md; append-only independent review is
review-2026-09-13T14-10-03Z.md. The exact author18-schedule export was independently
audited with zero violations and unique names; only the two terminal-order methods
were freshly executed. Both new fresh traces have zero correction acts, no reopen
and no session references. Fixing configuration trace labels did not discharge
the actual requested revised-code correction. The separate correction artifact
ends at revised attempt preparation; provider invocation counts cannot be derived
from empty session rows. These remain explicit acceptance gaps.

**Confirmed reusable predecessor:** closed W106673's accepted retained/restored
session/workspace useful-correction proof is existing evidence, not a reason to
repeat live providers. Its explicit exclusion of production manager adoption
remains. Current attempt-keyed session rows alone do not establish universal
impossibility of continuing the provider conversation. Existing W71877/W119403/
W119405 scheduling/pool/per-Job evidence remains reusable at its accepted scope.
Current specific manifest/Work eligibility refusal does not prove every legal
two-effective-slot configuration impossible.

**Proposed only:** the report offers independently decidable now/defer/drop
chunks, exact finish conditions, owners, effort/uncertainty and consequences.
Prioritize actual correction/reopen counters and W156162 managed isolation;
decide shared slots and session lifecycle before more fixture loops; consider
aligning explicit-only fallback with accepted soft affinity; defer priority and
random/TUI extensions. The owner has selected none of these dispositions yet.
All retained acceptance remains live until an explicit amendment. No new backlog,
product scope, live experiment or generic budget increase is authorized here.

W156162 M161127's independent design review identifies a real missing representation
for child-to-parent capacity charging and requires portable custody in the first
slice. Its managed Docker work owns that prerequisite; do not duplicate it or call
current host reconciliation evidence proof of the new lifecycle. The report names
the exact capacity, stop/release, phase-content, judgment, target-owner and restart
checks that must be revalidated after relocation through existing input/output.

Two new passing subprocesses cost10.87323230200127s and0.03151493900077185s.
`review-161114.json` preserves pre-command cap/spend/remainder/expected/margin/
timeout operands. Reviewer141.8669683800224/300s; author289runs
1063.5077970099796/1200s unchanged; all historical failures and0.8047997559610849s
old-cap overrun preserved. Initial research0.2879257239692379s separate. Only
reviewer-owned dossier records/evidence changed; no product/test or PROGRESS edits.
Return the completed report to baton.decide for discussion before implementation.

## 2026-09-13T14:40:58Z — selected small-Job plan and substitution boundary

**Confirmed, baton.codex claim161345:** read owner response161211, return161212
and complete later clarification messages161244/161254/161258/161267. The
currently actionable disposition is SELECTED-PLAN-161345.md. This explicitly
supersedes the earlier report's B–H recommendations and its statement that no
chunks have been selected, including that wording in the physically later
14:10:03Z entry above. Historical observations/reviews/hashes are unchanged.

Two separate Jobs are selected: W161230 managed integration; W161234 useful code
correction, counted reopen and REQUIRED healthy provider-context continuity.
Context reuse is no longer an unresolved preference. Reuse W106673 live evidence
and bound missing normal-serving adoption before implementing it. Dedicated
capacity is selected now. Shared slots and priority/random/TUI are deferred;
hardening is not an immediate correctness gate. Final pinned-dependency checks
belong to both selected completions; W161234 PLAN now reflects M161269 just as
W161230 PLAN reflects M161268. No separate environment project is selected.

**Confirmed source support, not fresh runtime evidence:** scheduler.activate_pool
records immutable configuration generations and leaves old allocations intact;
reserve enforces actual-principal occupancy and independence with existing soft
affinity. Serving _job_workers/_job_eligibility requires real per-Job Work/input
and implementation source_worker_id compatibility before reservation. Existing
pool activation is a useful building block, not proof of scoped operator
substitution. SELECTED-PLAN-161345.md names the exact functions and bounded
missing designation/revocation/admission/recovery design. The owner's required
replacement capability remains here without creating an unsolicited third Job,
forging an identity or expanding W161230/W161234. Automatic fallback is not the
selected requirement; W71877's historical acceptance remains intact.

The selected plan gives finish conditions, dependencies, planning effort and
uncertainty for the two Jobs; it distinguishes still-open substitution design
from deferred hardening and keeps full historical certification unclaimed.
W156162 is canonically blocked on W161230; W161234's dependency is documentary
only at detail161363 and must be arranged by its executing reviewer without
hiding unfinished adoption planning. No new Work, implementation or test run
was started here. Return the concrete breakdown before implementation as161212
requested; do not repeat the W103525 partial implementation loop.

W103525 spending unchanged: author289runs1063.5077970099796/1200s, reviewer
141.8669683800224/300s, research0.2879257239692379s separate; historical
0.8047997559610849s old-cap overrun preserved/unwaived. No reset or transfer.
Only reviewer-owned planning records changed; prior reviews, PROGRESS and
product/test files are untouched by this claim. A broad read-only diff check
reported pre-existing/concurrent trailing whitespace at
v12/python/tools/stage_execution.py:1909, outside this claim's edits; it is not
repaired or represented as this plan's verification failure. Check the exact
planning path set separately before handoff.
