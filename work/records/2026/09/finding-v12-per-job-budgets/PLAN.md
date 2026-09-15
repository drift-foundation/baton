# Plan

**Current: per-Job budgets wait on mandatory managed-integration prerequisite W161230.**

Owner M161222/M161232 created the separate Work at
`baton:work/records/2026/09/finding-v12-managed-integration-execution/`.
This explicitly supersedes routing managed integration design/implementation
through W156162 as the owning Work. Preserve all design/review evidence here;
W161230 adopts exact references and owns independent design review and subsequent
accepted slices. W156162 remains the consumer for final limits/recovery/isolation
acceptance. Record dependency on W161230 and relinquish the current planning claim.
Do not implement managed integration here or create a duplicate prerequisite.

Current reusable design: MANAGED-INTEGRATION-DESIGN-v2-2026-09-13.md,
DESIGN-RESPONSE-161207.md and HANDOFF-DESIGN-161207.md. The bounded first-slice
schema/capacity/custody/no-start-reader proposal needs independent review in
W161230; it is not implemented or self-approved. Owner M161268 additionally
requires final focused verification with project-pinned dependencies and recorded
actual versions, without a separate environment project absent a concrete problem.

### Completed revision, transferred by reference to W161230

Claim161207 responded to DESIGN-REVIEW-161103-2026-09-13.md / M161127.
Current proposal: MANAGED-INTEGRATION-DESIGN-v2-2026-09-13.md; response/handoff:
DESIGN-RESPONSE-161207.md and HANDOFF-DESIGN-161207.md. Route baton.impl for
independent DESIGN review only, then baton.feat. Do not implement or run runtime
verification merely to hand off the design. Owner implementation scope follows
independent acceptance of the concrete proposal; no self-review sign-off.

V2 selects explicit root/all-execution membership rather than hidden child
capacity or duplicate stage allocations. It names admission/parent-start/all-
release enforcement, portable result storage and its additive compatibility
scope, target-owner capability interface, and exact legacy/managed test mapping.
Newly revalidated gate: a failed preparation can leave parent apply never
started; existing quiescent finalization refuses it. V2 proposes a narrow owned
reader for fenced-before-start cancellation proof, preserving uncertainty and
Authority/target gates instead of inventing a runtime. Independently review it.

Current inventory research-161207.json:30 source files and all29 prior candidate
paths unchanged. Author246runs2530.5844189850177s plus4unknown activities;
reviewer147.7342205499972s including0.0027992710020043887s new read-only inventory.
No tests/runtime execution, product/PROGRESS/Git edits, cap/reset or W103525 transfer.
W103525 consolidation161193/161201 retains this prerequisite and later trace
revalidation; it grants no additional source scope.

### Historical first design handoff — superseded by v2 review above

Design: MANAGED-INTEGRATION-DESIGN-2026-09-13.md, author baton.codex under
claim161035. Evidence: research-161035.json and HANDOFF-DESIGN-161035.md.
Planning is complete for this claim; no implementation, runtime verification or
self-review sign-off. Route baton.impl for independent design review only, then
return baton.feat. Review the proposed preparation Work/offer/attempt charged to
parent capacity, parent final-apply identity, portable payload/custody and remote
target-owner publication boundary. Freeze the exact first-slice path and test
scope before requesting implementation authority; no generic lifecycle/schema
extension is presumed. The design's named open gates are not implementation-ready.

The existing29-path candidate is unchanged from review160499 at HEAD f3fc9e12...;
source inventory27files pins the planning basis. Author246 measured runs
2530.5844189850177s plus4unknown activities; reviewer147.73142127899519s including
0.0033738900019670837s inventory. No verification rerun, budget reset or transfer.
The owner architecture ruling below remains the controlling requirement.

**Owner-selected design direction (retained):**
Owner ruling: FINDING.md, 2026-09-13T13:47:40Z. Integration execution, including
reconciliation verification, must use the managed Docker runtime lifecycle with
the same isolation, timeout/termination, positive stop evidence, recovery and
capacity settlement as ordinary Jobs. It must support execution on another farm
machine through explicit input/workspace/result and runtime-state boundaries;
do not assume coordinator-local execution or files. Reuse the existing input/output
protocol designed for relocation, mapping integration inputs/results/evidence to
its contracts before proposing any extension. Prepare a bounded design,
path and authority plan for independent review before added implementation.
Keep W156162 open and preserve positive recovery/isolation acceptance and custody.

This supersedes the proposed separate host-terminality/recovery remedy and its
pending either/or recommendation. Containerizing the coordinator alone is
insufficient. Reuse the managed attempt lifecycle; separately specify legitimate
target repair/new-result actions without implicit retry. No blanket source,
schema or test expansion, live-provider run or exactly-once scope is granted.

### Historical preparation at owner disposition

Authorized explanation/provenance correction accepted.
Latest independent review: review-2026-09-13T12-21-26Z.md, claim160499.
Decision packet: RECOVERY-SCOPE-DISPOSITION-2026-09-13.md. Route baton.decide.

This supersedes the prior current correction action: stale source/test explanation
is corrected and the29-path packet independently matches. Runtime source AST is
unchanged except docstrings and the explanatory constant; reuse accepted tests.
Author logs step244 three tests and step245141tests pass. No further editorial-
only cycle is required before owner disposition.

The superseded proposed owner choice was: preserve positive recovery/isolation acceptance
and schedule a bounded terminality/recovery prerequisite (recommended), or amend
W156162 acceptance to current durable fail-closed/refusal behavior and defer the
positive remainder. The reviewer grants neither new source scope nor a waiver.
Any prerequisite requires an exact independently reviewed design/path/authority
plan before implementation; the packet maps the current seams and required proof.

Do not add crash-before-record exactly-once to this scope: the accepted proposal
excluded it. The new explanatory constant groups two limits, not two required
features. Nor does delivery prose saying a limit is not closed by this Work amend
the accepted plan. Preserve the failure custody, normal-reopen no-repeat and
runtime-owned cleanup already accepted. No fabricated runtime/quiescence/release,
extra integrator remedy, implicit retry or repeated one-capacity verification.

Minor documentation precision for the next substantive edit: recover_on_restart
selects issued/accepted offers; the empty report is an offer-state result, not
proof of runtime absence. This does not block the concrete scope decision.

Author246runs2530.5844189850177s plus4unknown activities;
reviewer147.72804738899322s including all prior failed research. No numeric cap,
reset or W103525 transfer. Packet29hashes stable; HEAD f3fc9e12... and exactW71879
methods preserved. Existing-test authority and immutable proposal/merge preflight
remain. No full-feature/import sign-off. Pin the owner ruling in FINDING and
reflect its chosen current scope here before dependent execution.

## Accepted behavior

Each Job may override `provider_turn_seconds` and
`verification_command_seconds` in `execution_limits`. Values are positive whole
seconds; reject bools, fractions, zero, negatives, unknown fields and unbounded
sentinels. Omission preserves the existing runner default: provider3600,
ordinary verification900, integration-worker verification1800, host composition
verification300. These are per-invocation ceilings, with no universal five-minute
default, cumulative remaining allowance or separate role/stage pools. One explicit
verification setting reaches all three verification boundaries. Timeouts retain
current structured failures and positive cleanup requirements.

## Delivery and identity plan

1. Introduce `baton.v12.job-submission/2`, with an optional closed
   `execution_limits` object on each Job. Preserve submission/1's exact closed
   shape and its normalized operation signatures. Persist requested settings,
   versioned compatibility resolution, effective per-boundary seconds and origins
   under the Job owner. Use the next Job store migration (current version4) without
   rewriting old submission journals. Old Jobs resolve compatibility values.
   Same submission identity with changed settings conflicts; identical replay,
   restart and correction retain them. Defaults changing cannot reinterpret an
   existing Job.
2. Use a new `baton.worker-launch/3` envelope at the existing read-only
   `/run/baton/launch.json` delivery. Preserve /1 and /2 shapes for legacy callers.
   The /3 envelope carries existing session/contract/role, explicit transport
   (existing exchange value or null for one-shot integration), and a closed
   `job_execution` object. Bind Job ID, attempt ID, Job input/policy identities,
   actual runtime input/policy identities, and versioned effective configuration
   plus its canonical digest (excluding its own digest member). Job inputs and
   runtime inputs are distinct: review and derived judgment can consume another
   frozen input. Validate those links rather than requiring equal digests.
3. Resolve through the immutable public Job reader at launch preparation and
   pass the object explicitly to the ordinary Worker and integration port.
   Derived `JudgmentExecution` is not a Job stage: carry its owning result's Job
   explicitly, include settings in its retained dispatch/intent comparison and
   bind its own attempt/input context. Do not mutate shared worker-global state
   or use an environment override as a second authority.

   Placement clarification2026-09-13T01:58:25Z supersedes any reading of this
   item that requires _SingleWorker to hold a Job store: the factory owns the
   handle and injects a narrow context callable using the public reader.
   _prepared/command/ending/serving-observation and observation-only paths use
   the same complete reconstruction; private helpers receive stage as needed.
   Observation uses the already-open read-only owner and gains no write,
   migration, runtime refresh or serving capability. Keep observe(stage) and
   observe_exchange(stage) surfaces unchanged, full launch.adopt comparison,
   actual runtime identity binding and the prior Authority-check behavior.
   Derived judgment receives its owning Job explicitly. Exact seams and focused
   positive/negative/read-only regressions are pinned in the latest review.
4. Extend launch constructors, exact adoption comparison and worker reader
   together. Refuse malformed/mismatched/unsupported delivery before provider or
   test execution. Never recreate missing post-start delivery. A Job requesting
   an override cannot fall back silently to a legacy launch. Establish worker
   image compatibility or fail closed; configured status is not that evidence.
   Task/2, exchange commands and frozen AgentSession/worker-control schemas remain
   unchanged. Integration bundle already binds the whole launch digest; retain
   that binding with the new generation.
5. Consume validated launch data in ordinary agent `seen` and integration
   entry/workload. Reach provider invocations for implementation, independent
   review, integration and derived judgment. Pass the Job-resolved verification
   timeout explicitly to host `_ConfiguredExecution`, separate from `GIT_SECONDS`.
   Replayed results do not start another invocation or renew a timer. Preserve
   existing recovery/cleanup gates; do not introduce a new retry policy.
6. Advance public status to `baton.v12.job-status/5`: requested/effective values,
   seconds, `per-invocation` scope and compatibility/Job origins. Distinguish
   configured/delivered values from observed execution when evidence exists;
   configuration alone does not prove a command ran. Read-only status cannot
   migrate stores or renew a timeout. Diagnostics report the actual applied value.

These mechanics are the reviewer's implementation plan within accepted behavior,
not an owner mandate to ignore contrary source evidence. Record a bounded
correction in FINDING/PLAN if revalidation requires it; cumulative accounting
and scheduler redesign are outside this slice. Implementer must name and test
one supported numeric range shared by both readers, with no silent clamp.

## Finite ownership and edit scope

The implementing claimant owns product edits and PROGRESS. Reviewer owns
FINDING/PLAN/DESIGN and append-only review evidence. Coordinate before simultaneous
edits to a path. Initial product paths are:

- `v12/python/src/baton_v12/job_manager/documents.py`, `submission.py`,
  `schema.py`, `store.py`, `projection.py`, and new `execution_limits.py` in that
  directory: versioned intent, resolution, migration, replay and public reads.
- `v12/python/src/baton_v12/worker_manager/launch.py`: versioned immutable
  delivery construction, validation and adoption.
- `v12/python/tools/single_worker.py`, `stage_execution.py`,
  `integration_worker.py`, `integration_bundle.py`: bind ordinary, integration
  and derived-judgment invocations and retain the whole-launch digest binding.
- `v12/worker/baton_worker.py`, `claude_agent.py`, `integration_entry.py`,
  `integration_workload.py`: closed reader and actual timeout arguments.
- `v12/python/DEPLOYMENT.md`: submission example, scope, units, preserved
  defaults, effective values, compatibility and timeout behavior.

No new worker module is needed; existing recipes copy the affected modules.
Image building, installing dependencies, selecting deployment images, live models
and Git mutations are outside this initial local scope. Record rollout
prerequisites distinctly from deterministic source verification.

Add three new focused modules, reusing helpers without inheriting exhaustive
test classes:

- `v12/python/tests/job_manager/test_execution_limits.py`: validation,
  persistence, migration, replay/conflict and read-only status.
- `v12/python/tests/manager/test_execution_limits.py`: launch conformance,
  adoption, fake provider and verification timeout arguments.
- `v12/python/tests/tools/test_execution_limits.py`: real composition with fake
  boundaries, including direct integration and derived judgments.

Additive fixture clarification2026-09-13T01:36:01Z (R6): add the populated
schema4 golden and concise generation/source/digest provenance under
`v12/python/tests/job_manager/execution_limits_fixtures/`, referenced relative
to the new test. Include these new paths in the immutable candidate inventory.
Keep original dossier evidence intact; do not make the product regression depend
on a `work/records` path. This schedules only new fixture/provenance files and the
new test module, not additional edits to existing regression inputs.

This initial plan schedules additive tests. Existing test files are regression
inputs, not authorized assertion-weakening targets. If a version transition
requires an existing expectation change, identify the exact test and change here
before expanding scope under the repository's test rule. The completed W71830
exception is not invoked.

Prospective bounded fixture update2026-09-13T02:09:22Z: schedule exactly the two
direct launch.adopt calls in v12/python/tests/tools/test_single_worker.py,
AFaultedTerminalSurvivesTheContainerThatWroteIt.faulted and
TheAnsweredEndingRunsThroughTheRealOwners.worked (currently lines2612/3063).
Add job_execution resolved from that helper's existing Job owner, stage Job/
attempt IDs and configured runtime input/policy. Preserve every assertion,
expected outcome and other test body. This supplies the new required setup
operand and does not change expected behavior, so AGENTS.md's case-specific
assertion/expectation approval rule does not require another owner question.
It prospectively extends the initial additive-only file scope for these two
fixture calls only. Reviewer may verify the exact proposed fixture delta in
isolated evidence; implementer owns importing it to the test source. The earlier
five expectation-changing files still need their recorded owner disposition;
this is not retroactive or blanket authority for those or any other tests.

Prospective setup scope clarification2026-09-13 (claim156801): include the three
direct adopt helpers in tests/tools/test_stage_execution.py (ComposedOneJobCase
.turn and both integration_turn helpers, currently2699/3797/7822), and necessary
fixture operand plumbing to obtain the actual Job/attempt/runtime context from
their existing owners. Adapt a fixture when its production delivery actually
carries /3; do not give a still-legacy integration delivery a speculative context.
For the rest of R3, equivalent setup-only propagation of the accepted execution
context/owning Job through existing factory, launch, integration and judgment
fixtures is scheduled in these finite files under v12/python/tests:
tools/test_single_worker.py, test_stage_execution.py, test_integration_worker.py,
test_integration_bundle.py; manager/test_launch.py, test_worker_entry.py,
test_claude_agent.py, test_integration_worker.py. Preserve every assertion,
expected outcome and unrelated fixture behavior; use actual owner identities,
not invented values or data extracted from a launch under test. Record exact
sites/deltas in PROGRESS and the candidate before handoff. This prospective
setup scope supersedes the two-call-only restriction for equivalent R3 operand
plumbing in these files, so each occurrence needs no new scheduling handoff.
It authorizes no existing assertion/expectation edit, no unrelated fixture repair,
and no retroactive disposition of the earlier five files. Other source constraints
or expectation changes remain separate findings.

## Deterministic acceptance and verification bounds

1. Two Jobs, each field alone/both/neither: exact values at every runner and all
   four legacy defaults. Malformed types, unknown fields, unsupported schemas
   and numeric boundaries must refuse before execution.
2. Public Job owners: submit/replay/conflict, legacy-store migration, restart and
   correction preservation. Replay old signed operations after migration without
   resigning them. Repeated read-only status leaves store/journal unchanged.
3. Shared worker A then B and interleaved A/B: reconstruct composition and compare
   retained delivery. Cross-Job/attempt/input/policy/digest substitutions refuse
   before invocation. Missing/changed post-start material cannot reset a turn.
4. Capture `timeout` at the normal subprocess/provider boundary for ordinary
   implementation, review, direct integration, derived judgment, causal tests
   and imported verification. Inject `TimeoutExpired` and start failure, inspect
   real failure/results and preserved cleanup gates. Overrides leave Git and
   engine-client timeouts unchanged.
5. Exercise real configuration, owner operations and affected composition,
   workspace, test and final-result paths with fake providers. Include success,
   timeout and replay with no duplicate invocation. Label model-free integration
   branches accurately; they cannot establish provider coverage.

Run the three new focused modules first. Then only relevant existing cases from
Job documents/submission/store; manager launch/worker-entry/Claude/integration;
and tools single-worker/stage-execution/integration-bundle/integration-worker
suites. Record exact selectors before running, elapsed wall time, exit status,
candidate identities and cumulative W156162 spending in PROGRESS/evidence.
Repeat only affected failures or changed behavior. No blanket suite, real-time
timeout sleep or live model. Injected timeout verifies argument selection and
failure handling, not observed OS descendant termination.

No numeric verification allowance was assigned to W156162; W103525's300-second
ledgers do not transfer. Bounded selectors and deterministic-only policy define
this plan's verification scope. Preserve cumulative spending across handoffs;
record needed scope expansion rather than inventing a five-minute ceiling or
unlimited reruns. Preparation executed no tests/providers (verification
subprocess spending0). Static reads are not a passing runtime baseline.

## Sequence

1. [done] Source revalidation and DESIGN under claim156175.
2. [done] Pin owner first-slice decision event156258 in FINDING.
3. [done] Versioned delivery, finite paths and deterministic plan under claim156264.
   This supersedes DESIGN's old candidate path table and undecided language;
   cumulative design remains deferred history.
4. [in progress] R1/R2/R4/R5/R6/C1 accepted at tested boundaries.
   Finish R3 actual delivery/consumption items3–5, composed deterministic tests
   and final documentation. Ordinary delivery and adapter consumption now have
   runtime callers; derived/direct-integration and host remain pending.
   Keep the
   accepted historical-generation and additive-table mechanics. Continue the
   authorized finite product/additive scope; no separate configuration-only
   approval round or new product decision is needed. Do not borrow W103525's
   verification allowance.
5. [pending] Pass exact candidate paths/digests, PROGRESS and test evidence to
   baton.feat for independent append-only review, then normal integration and
   approval with Git ownership retained by Slawomir.

## Current review and evidence spending

Reviewer0.37727526699927694s; author recorded29.63181132199952s across11 runs.
The baseline rerun described in PROGRESS needs its retained command/log/provenance
and elapsed accounting; no duration is inferred.87 focused review checks pass;
no runner enforcement has been tested because it is not implemented. The four
integration fixture failures remain separately reported, not waived or assigned
for opportunistic repair. Existing test diff reviewed: test_documents.py,
test_tool.py, test_exchange.py, test_store.py and test_scheduling.py under
v12/python/tests/job_manager. Review enumerates exact changes and why their
content fits; owner disposition for their bounded authority remains needed
before integration. PROGRESS identification alone did not amend the initial
additive-only plan.

Latest review spending: reviewer0.8545903619979072s; author measured
30.33542030100034s across13 runs plus one explicitly unmeasured baseline run.
The disclosed count/path/accounting corrections are accepted. Historical baseline
results remain author-reported; the retained reconstruction script supplies no
missing original log or duration. Five existing-test hashes remain unchanged.

Current spending supersedes the preceding totals: reviewer1.2319274499986932s;
author31.34681991099751s across17 measured runs, plus original baseline and golden
generation with unknown durations.80 focused checks pass, independent probe
confirms R5. No full-feature enforcement result is available yet.

Current spending2026-09-13T01:44:11Z supersedes the preceding totals:
reviewer1.6092069799979072s; author32.39793288599867s across21 measured runs plus
the same two unmeasured activities.89 focused tests pass; independent probe
confirms the remaining Boolean acceptance and the corrected attempt/float
refusals. Full-feature enforcement still has no implementation or evidence.

Current spending2026-09-13T01:51:44Z supersedes preceding totals:
reviewer1.9866033189973678s; author33.284753731997625s across24 measured runs plus
the same two unmeasured activities.65 focused tests pass and unchanged independent
probe confirms R5 correction. No production timeout propagation is implemented.

Current spending2026-09-13T01:58:25Z: reviewer unchanged1.9866033189973678s,
no new verification subprocesses for the unchanged candidate; author
37.26906050499747s across25 measured runs plus the same two unmeasured activities.
The latest claim is a static composition decision and not runtime verification.

Current spending2026-09-13T02:10:47Z: reviewer2.9007430729961925s; author
54.22697624999637s over30 measured runs plus two unmeasured activities. Fifteen
tests pass against the exact proposed two-call fixture patch, without changing
their assertions or the repository test source. This is proposed-fixture evidence,
not a green repository-suite or completed enforcement claim.

Current spending2026-09-13T02:19:56Z: reviewer4.529427870997097s; author
76.93585512199752s across33 measured runs plus two unknown-duration activities.
The first reviewer probe had a fixture lookup error and is retained; corrected
v2 passes three selected pooled cases. This does not establish all83 adoption
cases, fix the13 other author errors or prove configured runtime enforcement.

Current spending2026-09-13T02:27:16Z: reviewer5.593950847996894s; author measured
134.89787969399913s over35 ledger runs. In addition to the original baseline and
golden generation, the new isolated-copy attribution attempt and in-place
injection-removal attribution experiment have no supplied command/log/duration
entries. Treat at least these four activities as unknown/unlocated spending until
evidence is recovered. Three focused actual-source tests pass; full R3 remains.

Current spending2026-09-13T02:41:57Z supersedes preceding totals:
reviewer5.921359525997104s; author260.81187214799684s over42 measured runs plus
the same4 unknown-duration activities. Fourteen new tests pass; independent
probe captures18 production adapter calls across two explicit settings, omission
and success/timeout/start failures. It confirms4 malformed /3 deliveries accepted,
including a missing provider boundary falling back3600. See
review-2026-09-13T02-41-57Z.md for current corrections and remaining R3.

Current spending2026-09-13T02:51:29Z supersedes preceding totals:
reviewer6.248712394995891s; author280.02706706999743s over45 measured runs plus
the same4 unknown-duration activities. Twenty focused tests pass and the retained
production probe verifies18 calls and the prior4 reader refusals. Four new nested
metadata observations still accept malformed documents. Current remaining scope
and exact evidence: review-2026-09-13T02-51-29Z.md and review-157001.json.

Current spending2026-09-13T02:59:22Z supersedes preceding totals:
reviewer7.126665509995291s; author316.04785335699853s over51 measured runs plus
the same4 unknown-duration activities.37 focused tests pass, prior nested cases
refuse, six imported-verifier calls select120/default1800 with proper results.
Three resealed association/consistency cases remain accepted. Configured direct
integration is still not delivered; current review-2026-09-13T02-59-22Z.md and
review-157052.json state evidence bounds and remaining R3.

Current spending2026-09-13T03:27:43Z supersedes preceding totals:
reviewer8.404963404997034s; author663.5290292359932s over79 measured runs plus
the same4 unknown-duration activities.50 focused tests exclude3 timed-sleep cases.
Prior metadata associations now refuse. Real-owner/entry probe confirms launch
ceiling-job-a versus bundle job-a, provider timeout3600 despite requested60, and
unknown Job host default300. Full acceptance remains incomplete; current
review-2026-09-13T03-27-43Z.md and review-157207.json name exact next scope.

Current state2026-09-13T03:50:23Z supersedes the preceding direct-carrier defect
state and item4's direct-integration-pending description: ownership correlation,
configured direct provider/verification delivery and host Job-existence reader
are accepted at the boundaries in review-2026-09-13T03-50-23Z.md. All61 focused
tests pass; independent runtime refusal, provider timeout/result, adapter reuse
and unknown-Job checks pass. The no-sleep test correction is complete.

R3 remains in progress. Next implement the derived judgment's explicit owning
Job/retained intent, composed host result/cleanup/no-duplicate behavior, then
configured replay/read-only/A-B acceptance and final docs. Complete these within
the existing finite scope before a full-feature handoff; no separate decision or
configuration-only approval round is needed. Reuse unchanged passing evidence.
Existing five-test owner disposition and both stage_execution paths' other-Work
provenance remain integration gates, not a reason to leave the authorized work
unfinished. Exact next acceptance scope is in review-2026-09-13T03-50-23Z.md.

Current cumulative spending: reviewer11.48461547000079s; author87 measured runs
767.2193527649943s plus the same4 unknown-duration activities. Commands/logs and27
unchanged candidate hashes: run-review-157340.py/review-157340.json. No full-feature
sign-off; cumulative/role pools remain deferred.

Current state2026-09-13T04:03:31Z supersedes the preceding derived-context and
direct-provider outcome pending state. Derived intent/owning Job wiring is
accepted with independent configured real-composition evidence: all three /3
judgment launches name job-b, carry67/43, and preserve actual runtime identities;
both Jobs complete integration through the unchanged scripted consumer lifecycle.
Eight focused cases pass, including direct success/start failure/terminal replay.
Exact bounds and27 stable hashes: review-2026-09-13T04-03-31Z.md and
review-157438.json; reuse repro-157438.py evidence for this successful traversal.

R3 next: composed host timeout/result/cleanup/no-duplicate acceptance and any
necessary bounded failure handling; explicit configured read-only observation
and A/B interleaving at affected paths; final docs and candidate provenance.
Use focused selectors rather than another unchanged575-test or full stage-module
run. Existing integration gates and deferred cumulative/role pools remain.
Reviewer cumulative14.214627461000418s; author99 measured runs963.9498331740033s
plus the same4 unknown-duration activities. No full-feature sign-off.

Current state2026-09-13T04:18:41Z: R3 remains in progress, superseding the latest
author final-provenance-only claim. The host exception catch prevents tick crash
but produces malformed status=None evidence: causal timeouts repeat3 commands
each tick,12 over4 independently observed ticks. Next provide honest durable
failure/diagnostics and no implicit repeat on unchanged poll/reopen; prepare an
exact bounded owner-contract extension for disposition if required rather than
inventing an observed numeric status or changing out-of-scope owners.

Also finish the separate composed post-import failure/retention/cleanup tests
(review probe sees one77-second command, held target, no target advance), actual
read-only owner opening/adoption and no-write/action checks, and configured
composed A/B serving/observation/reopen acceptance. The new helper-only cases
do not discharge those requirements. Literal direct replay bytes are accepted.
Then finalize docs/provenance and the existing integration gates. Exact scope,
evidence and27 hashes: review-2026-09-13T04-18-41Z.md/review-157534.json.

Reviewer cumulative22.149817973002428s; author115 measured runs1064.7652273190033s
plus the same4 unknown-duration activities. Focus new verification on remaining
branches and reuse accepted passing evidence. No full-feature sign-off.

Current state2026-09-13T04:31:29Z supersedes the preceding current-candidate host
failure state: one causal child call over4 ticks with real diagnostics is now
accepted only within one process. Correct the memo's harness/result/phase
collision and repeated scratch materialization. The old post-import blocked
target claim is historical and cannot establish the new raising branch's state.
HOST-FAILURE-PROPOSAL-2026-09-13.md is proposed owner-contract scope awaiting
disposition. Continue the actual composed read-only and A/B acceptance, bounded
post-import failure evidence and candidate provenance in existing scope.
Review-2026-09-13T04-31-29Z.md/review-157602.json give exact findings,7 passing
tests,2 probes and27 stable candidate hashes. Reviewer30.84925778100478s;
author119 runs1106.9795836750018s plus4 unknown-duration activities.

Owner disposition request M157653 is pending on T156162 to baton.decide with
wait=false: the exact two-source host-failure proposal and the bounded five
existing job_manager test expectation changes. It does not block independent
authorized work or grant either requested extension. The next implementing
claim reads that request and any answer before touching dependent paths.

Current state2026-09-13T04:48:28Z supersedes the prior memo correction pending
state. Harness/scope separation and no repeat materialization are accepted with
9 focused tests and the original independent repro. Real configured A/B launch
adoption after serving closes is now measured, through observation_from and a
public read-only ControlStore; reuse repro-157715-readonly-v2.py as the baseline
for author tests. Corrected opener boundary: JobStore has no public read-only
opener, so use its existing public contract and prove observation itself adds
no writes/migration/action. Do not require a new generic opener by inference.
The probe uses a guarded existing Job handle; fresh-process/absent-artifact and
continued serving/reopen remain. Complete these and post-import outcome/cleanup
assertions, then provenance. M157653 still governs only pending owner scope/test
authority. Reviewer37.009955926003386s; author125 runs1160.563274582997s plus4
unknown-duration activities. Review-2026-09-13T04-48-28Z.md/review-157715.json
name exact acceptance bounds and27 stable hashes. No full-feature sign-off.

Current state2026-09-13T04:59:02Z: composed configured observation/adoption and
absent-delivery no-recreation author coverage are accepted. Three cases pass;
independent repro-157811.py proves the public absent answer is None. Retain that
assertion directly in the test rather than discarding answered. Next actual
fresh-process/closed-reopened ownership, continued A/B serving/no-duplicate,
post-import failure/retention/cleanup and final provenance. Existing fixture
READONLY_PROCESS/fresh-process completion and reopen helpers are reusable source
examples; no existing-test edit or broad repeat is scheduled. M157653 remains
pending; prior accepted behavior and source boundaries stand. Evidence:
review-2026-09-13T04-59-02Z.md/review-157811.json,27 stable hashes. Reviewer
38.08808619400406s; author131 runs1180.4354410040032s plus4 unknown activities.

Current state2026-09-13T05:05:13Z: fresh-process observation accepted with actual
new Job/Control handles, A/B/A launch adoption and four store-file comparisons.
The absent-result assertion and guard qualification corrections pass. Continued
configured serving across reopen remains, followed by post-import failure/
retention/cleanup and final provenance. Finish these independent items without
another unchanged broad recount; M157653 is still pending for dependent owner
scope/test authority. Exact review review-2026-09-13T05-05-13Z.md and
review-157850.json bind27 stable hashes. Reviewer38.80232255800547s; current
author137-run ledger1200.2701315720042s includes step137, superseding the stale
handoff1191.335321s total. Four unknown-duration activities remain; no reset.

Current state2026-09-13T05:13:48Z: continued serving remains pending. The new
test passes after its empty reopened fake engine reports both attempts destroyed;
it therefore measures lost-runtime polling rather than healthy continuation.
Preserve the fake daemon state across composition/client reopen, assert healthy
sweep outcomes and actual existing turn progress, and count starts/turns by
attempt. Literal retained delivery bytes/settings are independently accepted;
put that direct assertion in the regression. Exact P1 and evidence are in
review-2026-09-13T05-13-48Z.md/review-157902.json/repro-157902.log. Then finish
post-import failure/retention/cleanup and final27-path provenance. Existing
M157653 owner/test authority and stage_execution overlap gates remain. No broad
recount or full-feature sign-off. Reviewer39.68032088700602s; author140 measured
runs1210.1284220880043s plus4 unknown-duration activities; prior correction carried.

Current state2026-09-13T05:21:14Z supersedes the preceding reopen P1 as corrected.
Author regression positively proves live attempts, unchanged literal deliveries
and no duplicate starts across retained-daemon composition reopen. Independent
repro-157946-v4.py completes both original provider turns/stages with their own
31/67 bounds and exactly one provider call/workload start each after extra polls.
Carry that continuation assertion into the new test while finishing post-import
timeout/start failure/repeated observation, both host boundaries' original scratch
retention/cleanup and final27-path provenance. Reuse accepted evidence; do not
recount unchanged modules. M157653 owner/test authority and stage_execution
overlap gates remain. Exact review review-2026-09-13T05-21-14Z.md and
review-157946.json. Reviewer42.5870492790109s includes three retained failed
probe attempts; author143 runs1220.011155285003s plus4 unknown-duration activities.
No new product defect or full-feature sign-off.

Current state2026-09-13T05:25:38Z: author continuation regression is accepted;
the complete case and independent Job/attempt/bound association probe pass.
Preserve those explicit tuples through replay sweeps on the next edit, without
another isolated handoff for that strengthening. Next complete post-import
timeout/start failure/repeated observation and both host boundaries' original
scratch retention/cleanup assertions, then final27-path provenance and overlap
accounting. M157653 still gates dependent owner semantics/five-test authority.
Reuse accepted evidence; finish independent work before returning solely for
the owner ruling. Exact review review-2026-09-13T05-25-38Z.md/review-157990.json.
Reviewer43.30132153701015s; author147 runs1231.1839466419988s plus4 unknown-duration
activities. No new product defect or full-feature sign-off.

Current state2026-09-13T05:32:04Z: tuple strengthening accepted. Both host phases
are now independently reachable for timeout/start failure: repro-158025.py
asserts one77-second invocation/one scratch across four ticks per scenario, real
owner/Job/result/phase, unchanged target and current post-import authorized result.
Original scratch remains even after composition close; runtime cleanup is not
established by fixture teardown. Turn this exact baseline into regressions and
finish27-path provenance/overlap accounting. Post-import starts from
repro-157534.py's second case or new repro-158025.py, NOT repro-157990.py.
Do not call required_argv/_watching after judgments: they compose a new fixture
serving instance. Read existing deployment/task argv and tick the held composition.
M157653 still gates durable owner/scratch disposition and five-test authority.
Exact review review-2026-09-13T05-32-04Z.md/review-158025.json. Reviewer
50.48564187100965s; author151 runs1262.444742863001s plus4 unknown-duration
activities. No full-feature sign-off; reuse measured evidence without broad recount.

Current state2026-09-13T05:38:06Z: four post-import baseline regressions accepted;
reuse review158025's unchanged-product four-scenario evidence. Next produce the
final27-path provenance packet: base/candidate bytes, owner/scope and existing-test
authority per path, with exact foreign Work/hunk/dependency accounting for BOTH
stage_execution files. Do not alter foreign edits to manufacture provenance;
report any inseparable dependency explicitly. Then return for the pending
M157653 owner decision on durable failure/scratch semantics and five-test
authority. This supplies baseline acceptance, not final failure/cleanup sign-off.
Exact review review-2026-09-13T05-38-06Z.md/review-158071.json. Reviewer
58.256789800010665s; author155 runs1308.9765907300025s plus4 unknown activities.
No unchanged broad recount is needed for provenance documentation.

Current state2026-09-13T05:44:15Z: provenance audited and corrected in
PROVENANCE-REVIEW-158105.md;27 base/candidate inventories validate. Foreign
completion-observation owner is closed W71879 and exact preserved methods match.
Counts/attribution/five-test details and baseline wording corrected without
candidate edits. Independent preparation is complete enough for owner decision;
route baton.decide for pending M157653 two-source durable failure/scratch step5
extension and exact five-test authority. If accepted, pin ruling then implement
the bounded remainder; otherwise record the amended acceptance explicitly.
Integration dependency/preflight gates remain; no full-feature/import sign-off.
Exact review review-2026-09-13T05-44-15Z.md/review-158105.json. Reviewer
58.29267580300984s; author155 runs1308.9765907300025s plus4 unknown activities.

## Owner ruling M157653 — pinned 2026-09-13T09:19:44Z

**Slawomir, on thread T156162 seq 159347:** "Approve HOST-FAILURE-PROPOSAL-2026-09-13.md and the exact five test updates in PROVENANCE-REVIEW-158105.md under W156162's bound dossier. Preserve bounded scope, independent review, W71879 provenance and spending. No acceptance waiver."

Pass comment 159348: "Pin the approved M157653 ruling in FINDING/PLAN. Implement the bounded durable host-failure semantics and scratch disposition with deterministic tests, then return for independent review."

**What it grants.** Exactly two additional product paths enter W156162's finite source scope — `src/baton_v12/integration/reconciliation.py` and `src/baton_v12/integration/execution.py` — for the tagged closed no-status host failure custody, the causal completed-prefix/failed-phase/not-run remainder, blocked causal versus held post-import outcomes, durable no-repeat before materialization, and explicit scratch disposition. And the exact five existing `tests/job_manager` expectation changes listed in `PROVENANCE-REVIEW-158105.md` are approved.

**What it does not grant.** No acceptance waiver, no further source or schema extension, no numeric verification-budget change, and no relaxation of independent review. Successful integer observation contracts stay byte-compatible; no exit status is invented, no implicit retry is added and no generic exception is relabelled.

*Pinned by baton.claude under claim 159350 at the owner's explicit direction; FINDING and PLAN are otherwise reviewer-owned.*

Current state2026-09-13T09:34:47Z: changes requested under approved159347 scope;
no new permission gate. Fix failure content/Job-setting validation at causal and
post-import adoption, and the causal producer recording a commit as input_tree.
Independent repro-159421.py proves false causal custody and post-import claims
accepted after an actual77-second timeout. Then complete the admitted phase/
reason/malformed/signature/reopen/recovery/legacy-success/cleanup matrix, including
real queue-hold replay and disposal failures. Remove stale claims that the owner
extension is unapproved or that the unused causal-only accessor proves post-import
durability. Produce a new29-path provenance packet from PROVENANCE-REVIEW-158105.md
with exact W71879 attribution; preserve historical packets. Review
review-2026-09-13T09-34-47Z.md/review-159421.json. Reviewer62.55998214501051s;
author173 runs1540.163787782978s plus4 unknown activities. No full-feature sign-off.

## 2026-09-13T09:48:11Z — failure custody bindings remain incomplete

**Confirmed:** claim159521 reviews159506/M159505. Fourteen new validator tests
pass. The real combined timeout now records prepared.tree, superseding the prior
observed producer-tree defect at that boundary. Individual base/isolated phases
remain to be exercised. The handoff correctly retracts post-import replay proof.

**Confirmed unresolved P1:** _failure still accepts any positive seconds and
unrelated command/task/harness values. Independent repro-159521.py changes ONLY
seconds from the actual77 to999999; real causal custody and post-import adoption
both accept it. Separate single-member checks accept78 too, plus command, task
and harness substitutions. A maximum-range check alone is insufficient. Compare
to trusted owner-held Job/configuration/content expectations at adoption, not to
incoming self-consistency alone.

**Confirmed unresolved P1:** a base failure's completed combined prefix accepts
an unrelated commit, tree or environment independently. Bind every prefix phase
to its expected content/environment/harness as well as checking its structure.
These are corrections within owner159347's accepted finite extension.

Complete the already admitted failure/reopen/recovery/cleanup/success matrix and
new29-path provenance before another full-feature handoff. Do not count a named
remaining scratch path as established lifecycle cleanup. Keep old27-path packet
and exact W71879 provenance. No new permission/budget gate or acceptance waiver.
Review review-2026-09-13T09-48-11Z.md/review-159521.json and retained probe/logs
bind29 unchanged candidate hashes. Reviewer67.09156740901562s; author180 runs
1640.7954391129751s plus4 unknown activities. No implementation/PROGRESS edits,
full-feature sign-off or integration authorization from this review.

## 2026-09-13T09:56:51Z — configured operands accepted; harness binding remains

**Confirmed:** claim159579 accepts the configured command/task/seconds correction
at real causal and post-import adoption. Actual owner expectations reject78 and
999999 versus applied77, plus unrelated command/task. The specific completed-
combined prefix commit/tree/environment defect is corrected; an unchanged base
prefix is accepted before the three isolated negatives. These observations
supersede the corresponding portions of review09:48:11Z. Twenty focused tests pass.

**Confirmed unresolved P1:** expectations omit test_digest. Independent
repro-159579.py changes ONLY the digest after real77-second timeout; causal
recording durably retains the foreign harness and actual post-import adoption
accepts it. Deployment-time uncertainty does not waive per-result harness binding:
pin actual content before execution and expose its expectation independently of
the returned failure, with result/phase/Job isolation. No global stale digest or
self-comparison. Same approved finite source scope; name an exact missing seam
before expansion if needed.

Finish the already admitted phase/reason/malformed/signature/reopen/isolation/
recovery/cleanup/success matrix and new29-path provenance; no new permission gate.
Preserve historical27 packet and exact W71879 attribution. The incomplete list
alone is not an operational barrier to further authorized implementation.
Review review-2026-09-13T09-56-51Z.md/review-159579.json and probe/logs bind29
unchanged hashes. Reviewer70.42207601200971s; author184 measured runs
1724.648046144961s plus4 unknown activities. No reset, full-feature/import sign-off,
product edit or PROGRESS edit by reviewer.

## 2026-09-13T10:04:29Z — harness correction accepted; inventory prose corrected

**Confirmed:** claim159640 accepts per-execution content pin and actual causal/
post-import digest comparisons. Real77-second timeout adopters reject independent
foreign digest/command/task/78/999999 substitutions; actual answers retain valid
failure custody. Twenty-two focused tests pass. This supersedes the specific
remaining harness P1 from09:56:51Z at the measured boundaries, without claiming
all phase/result/harness/reopen isolation.

**Confirmed provenance:** all29 base/candidate byte/hash records match.
PROVENANCE-REVIEW-159640.md supersedes new author prose counts/independence claims:
6new,16modified product/docs,7existing tests; source18hunks(17ours/1foreign),
test6hunks(5ours/1foreign). Exact W71879 candidate methods and saved bases still
match; textual separation proves no semantic independence. Historical packets
remain. Owner159347 five-test authority stands; no new permission gate.

Next is the already admitted full failure/reopen/recovery/isolation/cleanup/
success acceptance matrix, then final updated provenance. No operational barrier
was reported; proceed with that authorized scope rather than another small-only
handoff. Review review-2026-09-13T10-04-29Z.md/review-159640.json/audit-159640.json
and probes/logs bind unchanged29candidate hashes. Reviewer73.7897591460005s;
author187runs1779.971035676972s plus4unknown activities. No reset, product/PROGRESS
edit, full-feature or import acceptance by reviewer.

## 2026-09-13T10:14:06Z — matrix boundaries and remaining owner execution

**Confirmed:** claim159705 accepts11focused tests at their actual boundaries:
constructed failure-document validation, signature helper distinction, persistent
causal read-only readback and failed-disposal diagnosis. These do not establish
resumed serving, post-import queue-hold no-repeat, Journal replay or cleanup
lifecycle. The author's only-recovery/authorization-left description is explicitly
superseded by review-2026-09-13T10-14-06Z.md's evidence mapping.

**Confirmed independent execution:** repro-159705.py drives actual base and isolated
host timeout/start-failed (four scenarios), correct retained phase/prefix/remainder,
blocked results and77-second commands, two/three calls respectively with no added
calls over four subsequent polls. Add these focused regressions and reuse accepted
combined/post-import evidence; no product defect found in these unchanged sources.

Remaining genuine serving reopen and post-import held queue, operation replay,
Job/result/harness isolation, explicit recovery, authorization and runtime-owned
cleanup still belong to approved scope. No new permission gate. Provenance prose
still contains old contradictory counts and JSON binds prior test bytes; prepare
new final consistent packet after substantive work, retaining correction159640 and
W71879 provenance. No editorial-only round required.

review-159705.json/probe/logs bind29stablehashes;28match previous candidate, only
new tools test changed. Reviewer80.27375380400372s; author196runs1857.653101458971s
plus4unknown activities. No reset, product/PROGRESS edit or full-feature/import
sign-off by reviewer.
