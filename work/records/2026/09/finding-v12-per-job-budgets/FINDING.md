# Finding: configure execution and verification budgets per Job

Ledger Work: W156162

## Owner requirement — 2026-09-13T00:34:12Z

Slawomir observed that Claude/Codex routinely spend more than ten minutes working
on code and questioned the five-minute limit discussed for W103525. He confirmed
that these limits should be configured per Job. This record owns that product
requirement; it does not expand W103525's two-test-file implementation scope.

**Confirmed existing meaning:** W103525's five-minute allowances in
`baton:work/records/2026/09/finding-v12-deterministic-scheduler-stress/FINDING.md`,
2026-09-12T23:50:14Z, are cumulative test subprocess wall time for author and
reviewer separately. They are manually recorded verification allowances, not a
five-minute worker/model turn timeout. Reasoning, reads and edits were explicitly
outside that measured ledger. Agent working time exceeding ten minutes therefore
does not by itself exceed that allowance. The earlier prompt explanation did not
make the measurement distinction clear enough.

**Confirmed product direction:** configure budgets per Job rather than treating
one conversational number as a universal limit. Name the measured resource and
its scope clearly so an operator can distinguish total agent execution from test
runtime. The five-minute W103525 decision is not a global default for future Jobs.
No replacement numerical value or per-attempt versus cumulative semantics was
selected in this turn. Do not infer that five minutes of test runtime should
kill a worker after five minutes of elapsed agent work.

**Observed preliminary source inspection:**
`v12/python/src/baton_v12/job_manager/submission.py:_job` persists input/policy
digests, test scope and terminal policy, and `_stage` binds a profile. There is
no direct budget field in these insertion paths. This does not establish that
all profile or policy configuration lacks useful limits; that requires a bounded
review of the actual configuration owners. Existing offer/settlement deadlines
and engine command timeouts serve different boundaries and must not be relabelled
as Job execution budgets without examining their contracts.

**Proposed design questions for the managed reviewer:** identify the canonical
Job configuration owner; distinguish execution elapsed time, verification runtime
and any provider token/cost limits already supported; propose defaults and Job
overrides, role/stage scope, accumulation across corrections/retries/restart,
usage visibility and exhaustion behavior. These are design questions, not
already approved schema fields or a mandate for a general budget framework.

Use deterministic providers and focused tests for subsequent implementation.
Retain legitimate lifecycle/cleanup behavior on exhaustion; budget expiry must
not be reported as successful completion or as proof a worker has stopped.

Discovery context: W103525 budget discussion, interactive baton.prompt.

## Reviewer preparation — 2026-09-13T00:39:13Z

**Confirmed assignment:** claim156175, following complete W156162 events and
T156162 discussion. This is design preparation only: no product change, test
execution or live model is assigned. W103525 remains independently scheduled and
its remaining verification allowance is not available to this Work.

**Confirmed by current source inspection:** the Job submission schema's closed
member set has no limits; normalized Job intent is journaled atomically and
replayed by submission identity/signature. Stage profile and Job policy are
digest-bound identities, not existing per-Job execution accounting. The source
baseline is the explicit `JOB_MEMBERS`/`_job` whitelist: a proposed limit cannot
be added to submission/1 and silently consumed. This is static evidence, not an
executed rejection test.

The deployed Python worker paths already have several different ceilings:
`v12/worker/claude_agent.py` gives one provider invocation3600 seconds and one
ordinary verification command900 seconds. Imported-target verification in
`v12/worker/integration_workload.py` uses1800 seconds. Reconciliation/verification
in `v12/python/tools/stage_execution.py:_ConfiguredExecution._run` uses the
300-second `GIT_SECONDS` constant, which also bounds distinct Git commands.
These are per-invocation limits, not cumulative usage. Provider reasoning and
tool activity occur within the provider invocation, while manager idle/queue
time and the present managed v11 thread are different intervals.

AgentSession profiles already declare setup/turn/cancel-drain deadlines in
milliseconds and event/queue limits. This declaration does not establish that
the direct CLI runner consumes those values; its provider path uses the constant
above, and `worker_manager/sessions.py` explicitly excludes turn/deadline
execution from its implemented scope. Worker-control size limits, OCI resource
limits, engine-client timeouts and offer/settlement/interrogation deadlines
remain separate boundaries. No mapped Job/direct-provider token/cost ledger was
found. Do not generalize that bounded inspection to every external provider.

**Proposed, not ruled:** `DESIGN.md` recommends a first delivery of explicit
per-Job provider-turn and verification-command ceilings, with immutable intent,
versioned resolution/delivery, visible scope/provenance, compatibility defaults
and deterministic acceptance. It specifies how existing different runner
defaults would be preserved rather than inventing one universal number. No
cumulative remaining value may be displayed for this per-invocation slice.

The design separately describes cumulative execution/verification accounting:
physical invocation measurements, role attribution, reservations before
concurrent dispatch, exactly-once settlement, correction/retry/restart retention,
uncertain usage and explicit exhaustion behavior. That requires an owner choice
and a larger accepted implementation boundary. Seconds cannot stand in for
tokens/cost. Expiry cannot stand in for positive cleanup or a completed test.

**Open owner decisions, concrete and ready for disposition:**

1. Deliver configurable per-invocation limits first (reviewer recommendation),
   or require cumulative Job allowances in the initial delivery as well?
2. Preserve existing per-runner defaults for omitted settings (recommendation),
   or select new explicit defaults? No new number is inferred.
3. Use Job-wide overrides across its relevant runners initially (recommendation),
   or require independently bounded role/stage pools now? The latter needs a
   named allocation policy and defaults rather than copying W103525's manual
   author/reviewer ledger.

After the decision, pin the exact versioned delivery carrier and finite
implementation/test path set in PLAN before product assignment. Proposed fields
and test cases are not current edit authority. The accepted per-Job direction is
unchanged; the recommended sequencing does not waive cumulative requirements
should the owner select them.

**Operational/source-read note:** initial searches guessed provider modules
under `v12/python/tools` and a `worker_manager/profiles.py` file. Those locators
do not exist. Actual provider/workload code under `v12/worker` and profile
certification in `worker_manager/handshake.py` were located and read; no required
source remains unavailable. No raw coordination store was opened. Preparation
changed only FINDING/PLAN and added DESIGN, leaving PROGRESS to its future
implementer. No tests or providers were run; no verification spending is claimed
as a passing baseline.

## Owner decision — 2026-09-13T00:49:46Z

**Confirmed:** baton.slaw returned W156162 through event156258 after claim156254:
approve per-Job provider-turn and verification-command timeouts first, preserving
existing runner defaults when omitted and using Job-wide overrides initially.
Cumulative accounting and separate role/stage budgets are deferred. Expose exact
units, scope and effective values. Pin the decision and prepare a bounded
implementation/test plan using fake providers. There is no universal five-minute
default.

This explicitly supersedes the three open owner choices in the preceding
preparation entry and DESIGN's original claim that first-delivery semantics are
undecided. The cumulative section remains historical design support for deferred
work, not an initial-delivery requirement. Existing per-runner defaults remain
3600 seconds for provider turns, 900 for ordinary worker verification, 1800 for
integration-worker verification and 300 for host composition verification.
The latter does not authorize changing unrelated Git-operation timeouts.

Reviewer claim156264 owns the bounded plan and source revalidation. Implementation
remains unstarted; this preparation does not run tests or providers. PLAN names
the current handoff scope and DESIGN records the proposed delivery mechanics
within these accepted semantics.

## Bounded implementation preparation — 2026-09-13T00:57:48Z

**Confirmed by source, not executed:** ordinary Worker materializes/adopts through
`worker_manager/launch.py`; the worker forwards validated launch data to
`ClaudeAgent.work` as `seen`. Integration entry already reads that same launch
contract and forwards it to its workload. `tools/integration_bundle.py` binds
the whole launch digest. `tools/single_worker.py:JudgmentExecution` is a separate
execution whose input is not the Job's original input; its owning result's Job
must explicitly supply the timeout settings. These seams support a versioned
launch carrier without changing task/2 or frozen control/session schemas.

**Proposed mechanics within accepted scope:** PLAN selects submission/2,
launch/3 and status/5, preserves legacy signatures/defaults, names a finite
product path list and three new additive test modules, and specifies negative,
replay, migration, shared-worker and timeout cases. The implementing handler
revalidates the mechanics before edits. The owner-selected first-slice semantics
are fixed; this plan does not reopen the deferred cumulative/role-pool choices.

**Operational source-read finding:** searches initially guessed
`worker_manager/integration_worker.py` and `worker_manager/integration_bundle.py`;
those files do not exist. The actual owners are `v12/python/tools/` modules of
those names and were read. No required source remains unavailable. A draft
documentation patch was rejected because it tried to delete and add PLAN in one
patch; it made no partial change and was replaced by an ordinary whole-file
write. Neither observation is a Baton protocol defect.

Preparation changed only FINDING/PLAN/DESIGN, leaving PROGRESS to implementation.
No tests, providers, installations or Git mutations occurred. W156162 has no
assigned numerical test allowance; PLAN records bounded deterministic selectors
and cumulative spending requirements rather than transferring W103525's ledger.

## Independent configuration review — 2026-09-13T01:13:49Z

**Confirmed:** claim156392 reviewed partial implementation handoff156390 and
M156388.87 focused tests pass; candidate identities and unchanged hashes for all
12 files are in review-156392.json. Additive limits-table migration and generalized
schema-3 subtraction are accepted mechanics. Delivery and enforcement remain
unimplemented and are required before completion.

**Observed R1:** an unchanged Job with omitted provider setting reports3600
seconds, then7200 after a simulated compatibility-default change, while identical
submission replay still succeeds. Read-time resolution contradicts PLAN's pinned
Job configuration identity. PROGRESS's request-only rationale does not supersede
that requirement. Pin immutable versioned compatibility resolution or equivalent
resolved values/digest; preserve old signed submission operands.

**Observed R2:** public submission/2 accepts a present execution_limits:null.
The optional closed-object contract permits omission or an object, including
empty, not a present null. Keep internal absence separate from public validation.
`repro-156392.py` uses disposable public Job owners for these probes.

**Authority finding:** five existing test files, not six, were changed for version
transitions; newest review enumerates paths/content and finds the expectations
consistent with accepted behavior. Initial PLAN scheduled additive tests, however,
and post-edit PROGRESS enumeration is not the case-specific accepted test-edit
scope AGENTS.md requires. Preserve the diff for exact owner disposition before
integration; continue already authorized source/additive implementation. No
retroactive approval or assertion weakening is claimed by this review.

**Evidence finding:** the four integration-fixture failures are retained in author
run logs. The separately claimed baseline rerun has no located command/log/
provenance or ledger entry; retain and account that evidence rather than claim
independent baseline verification. Current test_exchange.py is changed elsewhere;
the failing functions, rather than all their paths, appear untouched.

Current next: correct R1/R2, finish the authorized carrier/adoption/runner/tests/docs
scope and return complete evidence for independent review. Reviewer spending
0.37727526699927694s; author recorded29.63181132199952s, baseline accounting to
resolve. No numerical allowance assigned; W103525 ledger remains separate.

## Independent generation review — 2026-09-13T01:23:33Z

**Confirmed:** claim156469 accepts R1 historical-generation resolution and R2
public null rejection at tested boundaries.94 focused tests pass. The independent
public-owner probe preserves the old Job at provider3600 while a new Job receives
generation2/provider7200; identical old submission replay remains stable. A
present null is refused. Full candidate hashes/evidence are in review-156469.json.

**Observed R4:** the new claimed populated legacy migration test opens and
upgrades an empty schema4 store first, asserts current schema5, submits through
the current owner, then deletes limits rows and reopens. It does not admit a
submission while schema4 or migrate an already-recorded old-owner signature.
That claim in PROGRESS/handoff is superseded by this source-based finding.
Replace the evidence with a genuine populated legacy baseline and preserve the
old signed outcome across migration/replay; correct the author's record by append.

**Current next:** R3 carrier/adoption/runner/tests/docs is still unstarted and
already authorized. Complete it along with R4 without another configuration-only
approval round; no new budget or authority blocker has been identified for the
product/additive scope. Pin confirmed mechanics in FINDING/PLAN before implementing.

The five-file/path/accounting corrections are accepted disclosure. The baseline
reconstruction script was read, not executed, and cannot recreate its original
missing log/duration/provenance. Reviewer cumulative0.8545903619979072s; author
measured30.33542030100034s plus one unknown-duration baseline run. Existing-test
owner disposition still precedes integration; hashes unchanged, no retroactive
approval. No full-feature certification, live provider or Git mutation.

## Independent carrier review — 2026-09-13T01:36:01Z

**Confirmed:** claim156531 reviewed handoff156529/M156521.80 focused tests pass;
fourteen candidate path hashes were stable. R4 is now accepted at the tested
boundary: the test starts with a genuinely populated schema4 golden and already
signed /1 operation, then migrates/replays under generation0. This supersedes the
prior R4 current-owner/row-deletion evidence objection. Old-owner generation is
author-produced, not independently regenerated; metadata prose says six source
files but lists five. Preserve history and clarify provenance separately.

**Observed R5:** launch authoring accepts a sealed empty configuration and one
stating minutes/cumulative/generation999/provider=-1. It also materializes and
adopts delivery attempt-1 with a context naming attempt-other. Digest equality and
exact replay do not validate semantics or owner links. `repro-156531.py` and its
retained log demonstrate these acceptances. Validate the closed supported
configuration and bind actual attempt on both materialization and adoption,
without conflating Job input with runtime input identities.

**Observed R6:** the permanent regression reads its only golden from the dossier,
outside the declared product candidate. PLAN now schedules an additive normal
fixture/provenance copy in tests/job_manager/execution_limits_fixtures; retain
original evidence and enumerate new candidate bytes. This follows AGENTS.md's
stand-alone artifact placement rule and does not authorize existing-test edits.

**Current next:** R3 remains incomplete: launch/3 is only a carrier and configured
provider60 still executes with3600. Complete actual Job-bound delivery, readers,
all provider/verification boundaries, composed tests and docs, with R5/R6. No new
product authority or numerical-budget blocker was identified. Prior R1/R2 and
additive-table/generation mechanics remain accepted. Reviewer owns this record
and PLAN; implementer owns source/new tests/PROGRESS.

Reviewer cumulative1.2319274499986932s; author measured31.34681991099751s across17
runs plus two unknown-duration activities (baseline and golden generation).
Unmeasured costs are disclosed, not estimated. Existing five test diffs/hashes
remain unchanged and still require owner disposition before integration. See
`review-2026-09-13T01-36-01Z.md` and `review-156531.json`; no feature sign-off.

## Independent carrier correction review — 2026-09-13T01:44:11Z

**Confirmed:** claim156592 reviewed handoff156590/M156583.89 focused tests pass;
sixteen candidate hashes stayed stable. R5 now rejects the previously reported
empty/invalid configurations and contradicting attempts. R6 test fixture placement
is corrected and the fixture digest matches the original. These specific defects
are superseded by the corrected state; R1/R2/R4 remain accepted at tested bounds.

**Observed remaining R5:** a correctly resealed configuration with requested
provider integer1 and effective provider Boolean true is accepted by launch
authoring. Python dictionary equality conflates True and1. Compare canonical
typed content or explicitly enforce exact types, keeping valid integer1 accepted.
Float mutations are refused by boundaries.own and are not part of this remaining
finding. Independent repro-156592.py records positive refusal controls and the
Boolean acceptance, including attempt refusal before storage creation.

**Observed C1:** new fixture PROVENANCE.md says six committed files including
__init__.py; corrected metadata says five replacements over a working-tree copy.
Correct the new provenance description without overstating reconstruction
completeness; old-owner generation remains author evidence, not independently
regenerated. Preserve historical evidence and attributable corrections.

**Current next:** begin and finish R3 runtime propagation, tests and documentation
with remaining R5/C1 in the accepted implementation episode. Three partial
carrier/correctness claims have not started propagation; no authority or budget
blocker was reported. A configured provider60 still executes3600. A carrier-only
correction is not the complete candidate requested for review.

Reviewer cumulative1.6092069799979072s; author32.39793288599867s across21 measured
runs plus two unknown-duration activities. Existing five test diffs/hashes and
their required owner disposition before integration remain unchanged. See
review-2026-09-13T01-44-11Z.md and review-156592.json. No feature sign-off.

## Independent correction and context-helper review — 2026-09-13T01:51:44Z

**Confirmed:** claim156643 reviewed handoff156636/M156634.65 focused tests pass;
sixteen candidate hashes remain stable. Canonical comparison refuses the exact
previously accepted resealed Boolean from unchanged repro-156592.py. Valid
integer1 remains accepted. R5 remaining Boolean finding is superseded by this
corrected state. C1 provenance now accurately discloses the five-file replacement
over unpinned working-tree inputs. R1/R2/R4/R6 remain accepted at tested bounds.

**Confirmed partial mechanism:** submission.job_execution_context reads admitted
Job configuration/generation and identities, carries distinct runtime identities
and seals a context accepted by launch_document. The helper's legacy case tests
missing-row generation0 fallback; the separate golden case supplies populated
schema4 migration evidence. Actual runtime ownership links still need validation
at composition/consumption.

**Observed R3:** no production caller of the helper or job_execution= exists in
v12/python/tools or v12/worker. API preparation has not propagated the context to
a launch or provider; configured provider60 still executes3600. All other prior
corrections are accepted at their boundaries, so full authorized R3 propagation,
worker validation, runner arguments, composed tests and docs are the substantive
next work. No authority or numeric-budget blocker has been reported.

Reviewer cumulative1.9866033189973678s; author33.284753731997625s over24 measured
runs plus two unknown-duration activities. Existing five test hashes and bounded
owner disposition before integration remain unchanged. See
review-2026-09-13T01-51-44Z.md and review-156643.json. No feature sign-off.

## R3 composition placement clarification — 2026-09-13T01:58:25Z

**Observed:** handoff156676/M156675 identifies a real missing dependency:
_SingleWorker has no Job store, _adopted currently receives only attempt_id and
_Observation discards job_store, while all /3 adopters need the same complete
Job context. Static review confirms all outer serving/observation sites already
have stage, hence job_id/attempt_id can reach private helpers without changing
ManagerOperations.observe or observe_exchange public signatures.

**Confirmed clarification of earlier policy interpretation:** the quoted
_Observation.__init__ comment reserves an additional configuration/Authority
mismatch refusal for a ruling; it does not prohibit every public Job-owner read.
tools/job_manager._Observed forbids mutations/refresh/serving capabilities.
StageObservation already reads allocations through self.jobs. Reading pinned Job
configuration can preserve that boundary and need not add the old extra refusal.

**Pinned reviewer implementation-plan decision within accepted owner scope:**
factories retain their already-open Job owner and inject a narrow, read-only
execution-context callable into worker and observation compositions. It uses
submission.job_execution_context/public owner reads, has no mutation capability,
and reconstructs complete expected launch data from the Job and actual retained
runtime identities. Private helpers receive stage as needed. _SingleWorker gets
no general Job-store handle; _Observation gets the same narrow read over its
read-only owner, no serving factory/session/engine/credentials/migration/refresh.
Preserve full canonical launch.adopt comparison and missing-post-start refusal;
never derive expected Job settings from the untrusted launch or fall back to
legacy when a Job context is missing. Keep earlier Authority-check behavior.

This explicitly supersedes the ambiguous placement reading of PLAN item3 and
the handoff's proposed binary choice between a general store handle and weakened
adoption. It refines authorized implementation mechanics, not owner timeout
behavior. No frozen protocol or public observation callback change is required.
Derived JudgmentExecution still gets its owning result Job explicitly and binds
configuration to retained intent, rather than pretending to be a Job stage.

Exact factory/helper sites, identity checks and fresh-process, shared-worker,
read-only, substitution and absent-allocation tests are in
review-2026-09-13T01-58-25Z.md. Existing finite source/new-test scope suffices.
Proceed with full R3 propagation/consumption/runner tests/docs; no further owner
question is needed for this seam. All sixteen prior candidate hashes are unchanged
in review-156679.json, so no repeat verification was run. Reviewer remains
1.9866033189973678s; author37.26906050499747s over25 measured runs plus two
unknown-duration activities. Prior accepted findings and existing-test authority
disposition remain unchanged. No runtime enforcement or feature sign-off yet.

## Ordinary carrier review and bounded fixture scope — 2026-09-13T02:10:47Z

**Confirmed:** claim156751 reviewed handoff156747/M156746. The single-worker
factory and observation composition now inject the narrow reader and reconstruct
full expected /3 contexts. Exchange namespaces now depend on selected transport
rather than schema/2, correcting the author-observed missing namespaces. The
seventeen-path candidate remained unchanged during independent verification.

**Observed and independently reproduced correction:** all15 author-reported
fixture errors disappear when the two direct test-side launch.adopt calls receive
their expected job_execution operand. repro-156751.py compiles the exact
fixture-156751.patch into an isolated module, runs the two affected classes and
retains all original assertions. Fresh/read-only observation and real ending
cases pass. Repository test source is unchanged, so its current failures are not
claimed resolved in-tree. These omitted-setting/direct-serve_exchange cases do
not establish configured provider deadlines or the worker launch reader.

**Prospective plan scope decision:** the two setup calls in
tests/tools/test_single_worker.py, faulted and worked helpers, are explicitly
scheduled to gain the accepted context operand. This supersedes initial
additive-only file scope for those two calls only. No assertions or expected
behavior change, so the AGENTS.md case-specific assertion/expectation approval
rule does not require another owner question. Implementer applies the retained
patch and includes the eighteenth path/digest in the next candidate. The five
earlier expectation-changing files remain separately pending owner disposition;
no retroactive or blanket authority is supplied.

**Current next:** complete remaining R3 pooled/per-Job integration and derived
judgment propagation, four worker consumers, actual provider/verification timeout
arguments, configured fake-provider acceptance matrix and docs. The ordinary
factory's new reader does not cover other worker_operations callers; their
default None cannot silently stand for a Job's missing context. Existing scoped
implementation continues without waiting for the earlier five-file disposition.

Reviewer cumulative2.9007430729961925s; author54.22697624999637s over30 measured
runs plus two unknown-duration activities. Exact hashes, retained proposed patch,
log and source identities are in review-156751.json and associated evidence.
See review-2026-09-13T02-10-47Z.md. No full-feature sign-off or live provider.

## Pooled factory review and prospective fixture scope — 2026-09-13T02:19:56Z

**Confirmed:** claim156801 reviewed handoff156799/M156796. The two scheduled
single-worker fixture operands are imported without assertion/expectation
changes. Pooled and per-Job integration worker_operations now receive the narrow
Job reader. Nineteen candidate hashes are stable. Other-Work changes in
stage_execution.py remain separately owned and are not signed off here.

**Observed attribution correction:** retained author run32 has83 adoption
refusals through the main turn helper and13 distinct errors:4 missing reconciles,
8 missing proposal,1 missing relative Git source. This supersedes handoff/
PROGRESS's all96-adoption claim. Record those separately with actual evidence;
do not infer baseline provenance. The two integration_turn sites are forward
setup scope, not established causes of the current96 errors.

**Prospective implementation-plan clarification:** the three stage-execution
adoption helpers and necessary owner/attempt/runtime fixture plumbing are
scheduled. Equivalent R3 setup propagation is also scheduled in the eight
explicitly enumerated existing fixture files in PLAN. Preserve every assertion,
expected outcome and unrelated fixture behavior; record exact deltas instead of
returning for another scheduling pass at each equivalent occurrence. This
supersedes the prior two-call-only setup scope, supplies no retroactive
expectation authority, and excludes unrelated fixture repairs. Five earlier
expectation-changing files retain their separate owner-disposition gate.

**Independent proposed-fixture evidence:** selecting the actual prepared worker
and resolving its attempt through allocation/static stage to the Job makes three
representative pooled implementation/review/Job-B-verdict cases pass, preserving
original assertions. Scripts repro-156801.py and repro-156801-v2.py retain the
fixture delta/helper. First probe erroneously expected attempt_id on static
stage rows; its failure is reviewer misuse, retained and accounted, not a product
defect. V2 uses public allocation lookup. Repository test source remains unchanged
and no green whole-suite or configured-timeout result is claimed.

Continue full R3 derived/direct-integration context, worker consumers, actual
timeout arguments, configured acceptance matrix and docs under the pinned narrow
reader/full-adoption decision. Reviewer4.529427870997097s; author
76.93585512199752s over33 measured runs plus2 unknown-duration activities.
See review-2026-09-13T02-19-56Z.md and review-156801.json. No feature sign-off.

## Imported fixture review and attribution limits — 2026-09-13T02:27:16Z

**Confirmed:** claim156862 reviewed handoff156860/M156853. The imported turn
helper uses the scheduled context operand and public owning-Job reconstruction.
Three representative implementation/review/Job-B-verdict tests pass against the
actual repository module;20 candidate hashes stayed stable. Positive fixture
import is accepted at that tested bound, not as configured timeout enforcement.
For missing/ambiguous prepared workers or allocation, do not infer legacy from
None: require known Job-bound evidence, with explicit legacy exceptions only.
This is a tightening within the already-scheduled new helper/setup scope.

**Attribution clarification superseding handoff's broader conclusion:** the
reported experiment removes two reader injections, not all W156162 changes.
Persistence of13 errors under that experiment would only show independence from
those injections in that tree, not that no W156162 change contributes. Current
hashes match the restored prior candidate; temporary candidate/run provenance
was not independently established. The13 errors remain observed and their
historical cause unresolved. Accept the83-versus13 breakdown correction.

**Accounting finding:** the new isolated-copy attribution attempt and in-place
injection-removal experiment have no supplied retained command/log locators or
ledger durations. Steps34/35 account only for full changed-suite and restored
passing-subset runs. These add at least two unknown/unlocated activities to the
previous original baseline and golden generation. Locate evidence if available;
otherwise retain unknown duration explicitly. Do not reconstruct timings or
claim the prior two-activity list complete. No repeated baseline run is required
before continuing accepted R3; keep experiments isolated from shared candidate
source with provenance and resource paths retained.

Current next remains actual derived/direct-integration context, worker readers,
provider/verification arguments, configured acceptance matrix and docs. This
claim changed only test setup; configured provider60 still executes3600. No new
authority or numeric-budget blocker was reported. Reviewer5.593950847996894s;
author134.89787969399913s over35 measured runs plus at least4 disclosed activities
with unknown spending. See review-2026-09-13T02-27-16Z.md and review-156862.json.
Existing authority/overlap requirements remain; no feature sign-off.

## Ordinary runtime consumption and reader gaps — 2026-09-13T02:41:57Z

**Confirmed:** claim156931 reviewed handoff156929/M156921. Independent production
_provider/_ran_provider and _verify/_ran calls through the injected run boundary
select60/45,17/23 and omitted3600/900, with correct success, timeout and start-error
results. This explicitly supersedes the preceding statement that ordinary
configured provider60 still executes3600. It does not establish full composition,
live providers, credentials or observed OS descendant termination. Fourteen new
author tests pass, but their claimed subprocess case calls its local runner
directly; require actual adapter-call coverage in that new module.

**Observed defects:** the worker reader accepts a resealed configuration missing
provider_turn and _bound silently returns3600 despite requested60. It also accepts
unknown transport, nontext Job ID and resealed wrong units. The manager's stronger
producer/adoption validation does not make this reader closed. Require complete
supported config/boundary metadata, identity/digest shapes, and exchange-or-null
transport. Missing/malformed Job-bound values must refuse, not select legacy
defaults. No Job-store access in the worker is needed. Actual outcomes are in
repro-156931.py/review-156931-probe.log.

**Current next:** correct these reader/test gaps and finish derived judgment's
explicit owning Job/retained intent, direct integration/bundle/entry/workload,
imported/host timeout application, configured composed acceptance and final docs.
The fixture's explicit legacy judgment branch describes unfinished scope, not a
new exception to Job-wide behavior. Existing finite product/setup authority
covers this work. See review-2026-09-13T02-41-57Z.md; no feature sign-off.

**Accounting:** accept4 explicitly unmeasured activities and narrowed attribution;
the13 other errors' historical cause remains unestablished despite a surviving
pre-existing qualifier in verification bullets. Reviewer5.921359525997104s;
author260.81187214799684s over42 measured runs plus4 unknown-duration activities.
Twenty-four hashes stable in review-156931.json. Existing owner-disposition and
other-Work overlap gates remain before integration. No further broad baseline
rerun or unrelated fixture repair is required to continue accepted R3.

## Reader corrections verified; nested schema and R3 remain — 2026-09-13T02:51:29Z

**Confirmed:** claim157001 reviews handoff156999/M156998. The four preceding
acceptance observations (missing provider boundary, unknown transport, nontext
Job ID, wrong units) are explicitly superseded: the retained probe now confirms
refusal. The adapter's direct missing-boundary case refuses too. Twenty focused
tests pass and the revised test reaches production through its run injection.
The retained independent18-call probe still verifies configured/default arguments
and success/timeout/start-error results. Accept the author's evidence correction.

**Observed remaining P2:** resealed requested Boolean/unknown-setting maps and
boundary missing-origin/unknown-member maps remain accepted by the worker reader.
Close both nested maps and validate their types/vocabulary/setting association;
do not replace the owner's immutable resolution with current defaults or require
a Job store in the worker. This completes the already-requested schema check.
Repro/log and24 stable hashes: repro-157001.py and review-157001.json. The new
repository test matrix also needs success/start-error result assertions; the
independent retained probe currently supplies those checks.

**Current next unchanged:** finish derived Job/retained intent, direct integration
carrier/bundle/entry/workload/provider context, imported/host verification limits,
configured composed acceptance and final docs alongside these corrections. The
handoff reports no actual external blocker. Accepted scope already authorizes
this work; no new permission or numeric-budget gate. No feature sign-off.

Reviewer6.248712394995891s; author45 measured runs280.02706706999743s plus the same4
unknown-duration activities. Accept the corrected historical-cause qualification
for13 other stage errors. Existing owner-disposition and overlap requirements
remain. Current review: review-2026-09-13T02-51-29Z.md.

## Nested refusals and imported verifier boundary — 2026-09-13T02:59:22Z

**Confirmed:** claim157052 reviews handoff157050/M157043. The four preceding
nested acceptance observations are explicitly superseded: retained probes now
refuse them. Ordinary success/start-error assertions were added to the new
focused module.37 focused tests pass, including two legacy integration regressions.
Six independent imported-verifier calls select120/default1800 and check success,
timeout and start-error results. This is real run_verification with an injected
subprocess, not configured producer/bundle/full integration evidence.

**Observed remaining P2:** resealed provider metadata may name the verification
setting, select effective30 despite requested60, or claim compatibility origin
despite an explicit provider request. Correct boundary-to-setting association
and internal request/origin/seconds consistency as already requested. Explicit
request implies job origin and matching seconds; omission implies compatibility
origin and seconds equal to the carried default. No current-default re-resolution
or worker Job store is required. Evidence: repro-157052.py/review-157052-probe.log.

**Delivery limitation:** the author reports direct integration still produces /1.
The new verifier reader therefore cannot yet apply configured Job limits on that
normal path. DEPLOYMENT.md must retain this limitation until delivery is wired
and verified. Finish direct carrier/bundle/provider context, derived owning Job
and retained intent, host verification, composed acceptance and final docs under
the existing scope. No external blocker was reported; no feature sign-off.

Reviewer7.126665509995291s; author51 measured runs316.04785335699853s plus4
unknown-duration activities.25 candidate hashes stable in review-157052.json.
Existing authority/provenance gates and historical uncertainty for13 other stage
errors remain. Current review: review-2026-09-13T02-59-22Z.md.

## Direct carrier ownership and provider gaps — 2026-09-13T03:27:43Z

**Confirmed:** claim157207 reviews handoff157205/M157202. The previous three
metadata-association acceptances are explicitly superseded: retained probes now
refuse them. Direct IntegrationRuntimePort authors /3 and bundles its full digest;
this supersedes the previous /1-only producer limitation.50 focused tests pass
without repeating the3 new timed-sleep tests, which conflict with PLAN's bound.

**Observed P1:** the new positive fixture admits the original job-a proposal but
supplies ceiling-job-a to prepare. Actual public admission answers running, the
launch names ceiling-job-a, the bundle authority scope names job-a, and the real
entry invokes the provider. Bind carrier Job to the actual accepted owning Job
before runtime start and check it against bundle scope before provider execution.
Configure the actual owning Job at original public submission for positive
evidence, preserving the foreign case as a refusal regression.

**Observed P1:** integration_entry/workload never passes launch context to
ClaudeAgent.invoke_provider; _seen is populated only by ordinary work(). The
real-entry injected run observes3600 despite requested60 and produces a genuine
held/provider-failed timeout result. Provider propagation remains required R3.
The new fake-provider runner's hard-coded300 currently hides its supplied timeout.

**Observed P2:** new submission.boundary_seconds returns300 for an unadmitted
Job. Prove Job existence before interpreting a missing limits row as migrated
compatibility; retain defaults for existing legacy Jobs and explicit unbound
callers. No new authority or behavior decision is needed for these corrections.

Evidence: repro-157207.py/review-157207-probe.log,27 stable hashes in
review-157207.json. Derived owning Job/retained intent, composed host failure and
cleanup behavior, replay/no-duplicate/read-only/A-B acceptance and final docs
remain. Replace the three timed sleeps with normal-boundary injection, preserving
real composition and result checks. Reviewer8.404963404997034s; author79 measured
runs663.5290292359932s plus4 unknown-duration activities. Existing authority and
other-Work provenance gates remain; no feature sign-off. Current review:
review-2026-09-13T03-27-43Z.md.

## Direct ownership and provider corrections verified — 2026-09-13T03:50:23Z

**Confirmed:** claim157340 reviews handoff157333/M157331. This entry explicitly
supersedes the preceding three open defect observations: the foreign carrier is
now refused before runtime start, the actual integration provider run receives60
and publishes held/provider-failed on injected timeout, and the host reader
refuses an unknown Job while existing legacy Jobs retain their defaults. The
worker also compares carrier Job with proved bundle scope. Positive fixtures
configure the real owning Job at original public submission. All61 focused tests
pass; timed sleeps have been replaced by normal-boundary injections.

Independent adapter reuse observes60/17/3600/60/3600 and restores the preceding
context. This is bounded adapter isolation evidence, not completed composed
two-Job/replay acceptance. Evidence: repro-157340.py, review-157340-probe.log and
27 stable candidate hashes in review-157340.json. Full remaining scope is derived
JudgmentExecution owning Job/retained intent, composed host result/cleanup and
no-duplicate behavior, configured replay/read-only/A-B acceptance and final docs.
No new decision or external blocker is needed to continue that accepted scope.

Reviewer cumulative11.48461547000079s; author87 measured runs767.2193527649943s
plus the same4 unknown-duration activities. Existing test-authority and other-Work
provenance gates remain before integration. Current review:
review-2026-09-13T03-50-23Z.md. No full-feature sign-off.

## Configured derived judgments verified — 2026-09-13T04:03:31Z

**Confirmed:** claim157438 reviews handoff157436/M157434. This explicitly
supersedes the previous derived-context and direct-provider success/start-failure
pending state. The actual result subject supplies JudgmentExecution's owning Job,
the intent carries it, and the narrow reader composes the judge's own runtime
manifest/policy identities. Independent configured public-submission evidence
uses A31/29 and B67/43 provider/verification seconds. All three derived launches
adopt as /3 for job-b with67/43 and distinct runtime versus submitted input
digests. The existing real consumer lifecycle completes both integrations and
passes its terminal replay/cleanup assertions under deterministic providers.

Eight focused tests pass, including direct success/import, start failure with
no imported path, and no second provider on terminal replay. The replay assertion
compares parsed results, not raw bytes. Evidence is bounded configured delivery
and successful lifecycle coverage, not new host failure or live-model evidence.
Composed host result/cleanup/no-duplicate timeout behavior and explicit read-only/
A-B interleaving acceptance remain next, followed by final docs/provenance.

Review review-2026-09-13T04-03-31Z.md and review-157438.json bind27 stable candidate
hashes. Independent evidence: repro-157438.py/probe log; commands and accounting:
run-review-157438.py. Reviewer cumulative14.214627461000418s; author99 measured
runs963.9498331740033s plus the same4 unknown-duration activities. Existing
integration authority/provenance gates remain; no full-feature sign-off.

## Causal timeout retry and remaining composed acceptance — 2026-09-13T04:18:41Z

**Observed P1:** claim157534 reviews handoff157532/M157531. The host timeout
catch prevents the tick crash, but status=None is rejected by the causal owner's
integer-status contract before retaining observations or settling failure.
Independent probe observes3 repeated host timeout calls per ordinary tick,
12 over4 ticks, with only an integrity/schema exit-status message exposed.
The successful-observation no-duplicate case does not cover this failure loop.
This explicitly supersedes the handoff's completed-host/final-provenance-only
state. Honest durable failure, actual timeout/start-error diagnostics and bounded
retry behavior remain R3; never fabricate a child exit status. If existing APIs
cannot represent it within finite scope, prepare the exact owner-contract/path
extension for disposition, while continuing other authorized acceptance work.

**Confirmed separate post-import branch:** after real judgments, an independent
host timeout injection receives77 and runs once over4 ticks. Target remains
unchanged and becomes blocked at fence2; result remains authorized, integration
stage claimed. The post-import owner also rejects None as malformed status.
This bounded hold evidence differs from the causal loop and was not covered by
the new author tests. Runtime cleanup/retention still needs an explicit assertion;
a temporary materialization remains before fixture cleanup, without establishing
a new regression against prior behavior.

**Confirmed bounds:**12 focused cases pass; literal direct replay bytes now
match. Read-only helper/table equality and separate-adapter A/B selection pass,
but actual read-only owner opening/adoption, absence of all writes/actions, and
configured composed serving/observation/interleaving remain untested. Prior
accepted boundaries stand; no full-feature sign-off. Current exact findings:
review-2026-09-13T04-18-41Z.md. Evidence: run-review-157534.py/review-157534.json,
repro-157534.py/probe log,27 stable hashes. Reviewer22.149817973002428s;
author115 measured runs1064.7652273190033s plus4 unknown-duration activities.

## 2026-09-13T04:31:29Z — retained timeout identity and owner-contract proposal

**Confirmed, superseding the preceding current-candidate failure state:**
claim157602 independently observes one causal host command at77 seconds across
four ticks, with the real timeout diagnostic and no judges. The process memo
fixes repeated child execution within that deployment only. The prior candidate's
post-import blocked-target evidence does not transfer: the current raised owner
refusal bypasses the adopted-answer hold branch, and four post-import ticks now
defer with the same timeout reason. Target reference remains unchanged, result
authorized and stage claimed. Current durable queue state was not queried.

**Confirmed defects in the new memo:** its argv/revision/seconds key conflates
different added harnesses on the same base; repro-157602.py observes the second
harness refused using the first harness's timeout without executing it. Its
lookup also follows materialization: three owner calls produce three scratch
directories for one child timeout. The probe cleans its own fixture only after
measuring; runtime cleanup is unproved. Job/result/phase identity is absent.

**Proposed, not accepted scope:**
HOST-FAILURE-PROPOSAL-2026-09-13.md records the reviewed bounded extension for
durable no-status failure answers. Add reconciliation.py and execution.py under
the integration owner, preserving successful integer evidence, closed failure
identity, completed/not-run phases, blocked/held state, replay, cleanup and
existing generic-refusal/double-block behavior. No global nullable-status
relaxation, fabricated return codes or implicit retry policy. Submit for owner
disposition; continue already-authorized acceptance work in parallel with that
decision. This records the previously source/PROGRESS-only proposal durably.

Seven focused tests pass; both independent probes succeed and27 candidate hashes
are stable. Exact evidence and outstanding scope:
review-2026-09-13T04-31-29Z.md, run-review-157602.py/review-157602.json and logs.
Reviewer cumulative30.84925778100478s; author119 measured runs
1106.9795836750018s plus the same4 unknown-duration activities. No full-feature
sign-off; composed read-only/A-B coverage, failure lifecycle and integration
provenance/test-authority gates remain.

Coordination: asynchronous owner request M157653 on T156162 names the above
proposal and separately requests bounded authority for the five existing
job_manager test expectation changes (legacy/unsupported submission versions,
status/5 and migration fixture generation). Both are pending, not assumed
accepted; authorized independent implementation continues while awaiting reply.

## 2026-09-13T04:48:28Z — memo accepted and configured observation baseline

**Confirmed:** claim157715 reviews handoff157681/M157679 and supersedes the
preceding memo P1/P2 as corrected. Nine focused tests pass; the independent
original harness probe now observes1,0,1 child/archive increments for first,
repeat and different harness. Scope includes Job/result/causal-or-post-import,
and lookup precedes materialization. Durable outcome and original scratch
cleanup remain unproved; M157653 is still pending, not scope authority.

**Confirmed independent observation:** repro-157715-readonly-v2.py configures
real submitted A31/29 and B67/43, materializes both producer launches, closes
serving, publicly reopens ControlStore read-only, and constructs two fresh
observation_from readers. Six alternating A/B/A actual launch.adopt calls
preserve the configured Job contexts and equal the serving exchange answers.
Job writes are rejected during that read window; four store files remain
byte-identical, and guarded serving/session/pool/line/preflight acts are unused.

**Clarification of prior read-only shorthand:** current JobStore has no public
read-only opener. Its existing open initializes/adopts/migrates and requests WAL;
status uses that same opener. Observation must add no write/migration/action,
but this Work does not implicitly require a new generic Job-store opener.
The independent probe uses an existing current-schema Job handle with write
guard plus the real read-only ControlStore. It does not claim fresh-process,
absent-artifact or complete serving-reopen coverage. Keep that boundary explicit
and use the actual public opener contract in the next focused acceptance tests.

The first probe used a nonexistent composed.observe_exchange method; v2 uses
composed.observe(stage)[exchange]. This reviewer fixture error and its cost/log
remain. Current exact review review-2026-09-13T04-48-28Z.md;
run-review-157715.py/run-review-157715-followup.py/review-157715.json bind27 stable
hashes and all verification. Reviewer37.009955926003386s; author125 measured
runs1160.563274582997s plus the same4 unknown-duration activities. Remaining
author regression integration, absent-artifact/reopen/continued A-B, post-import
failure/cleanup and final provenance are actionable within existing scope.
No full-feature sign-off or new owner-contract authority.

## 2026-09-13T04:59:02Z — composed observation and absent delivery accepted

**Confirmed:** claim157811 reviews handoff157788/M157787. Three composed tests
pass over real distinct A/B submissions, materialized launches, closed serving,
public read-only ControlStore and fresh observation_from readers. Six alternating
adoptions preserve each Job's context and serving exchange answer. The helper
class is labelled accurately. The absent-delivery test uses launch.discard and
does not recreate the root; independent repro-157811.py asserts the actual public
answer is None. Add that direct assertion to the repository regression on its
next authorized edit; the test currently discards the answer.

This supersedes composed author observation/absence pending state, not the
remaining fresh-process or continued-serving reopen requirement. Listed SQL
mutation guards and four database-file comparisons have their stated boundary;
they are not a universal arbitrary-write proof. The existing Job handle is
retained, and only ControlStore is actually reopened read-only. No generic new
Job opener is required. Continue fresh ownership/serving/no-duplicate and
post-import failure/retention/cleanup assertions, then final provenance.
M157653 remains pending with no dependent scope authority.

Exact review review-2026-09-13T04-59-02Z.md and
run-review-157811.py/review-157811.json/repro-157811.py/logs bind27 stable hashes.
Reviewer38.08808619400406s; author131 measured runs1180.4354410040032s plus4
unknown-duration activities. No product change this claim, no full-feature
sign-off, no broad repeat or budget reset.

## 2026-09-13T05:05:13Z — fresh-process observation accepted

**Confirmed:** claim157850 reviews handoff157847/M157846. Two focused tests
pass. The new real child opens its own JobStore and read-only ControlStore after
serving and both parent handles close, then reconstructs and adopts A/B/A with
31/29 and67/43 Job settings. Exchange answers match serving; four store files
remain byte-identical. This supersedes fresh-process observation pending state,
not continued serving across reopen. Direct None assertion and narrower guard
description are accepted. No product change or new bounded-review defect.

**Confirmed accounting correction:**137 ledger runs total1200.2701315720042s.
The handoff/PROGRESS1191.335321s omits step137's8.934810776001541s count run;
carry the current ledger total and all four unknown-duration activities. Reviewer
cumulative38.80232255800547s. Exact review review-2026-09-13T05-05-13Z.md and
run-review-157850.py/review-157850.json/focused log bind27 stable hashes.

Next continued configured A/B serving/reopen/no-duplicate, post-import failure/
retention/cleanup and final provenance in existing scope. M157653 remains pending;
no dependent owner-contract/test authority or full-feature sign-off is supplied.
Accepted earlier evidence stays; no unchanged broad recount or spending reset.

## 2026-09-13T05:13:48Z — reopened fixture loses runtimes

**Confirmed:** claim157902 reviews handoff157890/M157888. The new reopen test
passes, but independent repro-157902.py records BOTH implementation runtimes
refreshed to destroyed on the first reopened sweep, then not-asked on the next
two. serving_two creates an empty _ConcurrentEngine, losing the simulated daemon
state. Empty start lists in this lost-runtime scenario do not establish healthy
continued serving. This rejects the latest author claim that continued serving
is discharged; the earlier pending requirement remains. Reuse external runtime
state across client/composition reopen, assert healthy sweep outcomes and actual
existing turn progress, with actual per-attempt start/turn counts. The class
docstring claims a provider count that the test never takes.

**Confirmed separately:**19 A and18 B real adoptions preserve literal launch
paths/bytes and Job31/29 versus67/43 settings. Carry that direct byte comparison
into the author regression, which currently compares semantic context/exchange
answers. This is a test-fixture acceptance gap, not an established new product
defect. Prior accepted observation/fresh-process evidence stands.

Exact review review-2026-09-13T05-13-48Z.md and review-157902.json/logs retain
the one passing focused case and independent probe. Reviewer39.68032088700602s;
author140 measured runs1210.1284220880043s plus4 unknown-duration activities.
Next healthy configured serving/reopen, post-import failure/retention/cleanup
and final provenance. M157653 remains pending; no new owner authority or full
sign-off is supplied.

## 2026-09-13T05:21:14Z — healthy reopen and actual continuation accepted

**Confirmed:** claim157946 reviews handoff157944/M157943. The empty-daemon P1
from review-2026-09-13T05-13-48Z.md is superseded as corrected: one fake daemon
survives client/composition reopen, and all three sweeps positively report both
original attempts running. Literal launch bytes/settings remain unchanged.
Independent repro-157946-v4.py also completes both existing provider turns after
the author's full regression. Both implementation stages complete, with one real
adapter _provider call per attempt carrying31 or67 and one workload engine start
each, including three further replay sweeps. Two custody helpers per attempt are
retained in the log and are not duplicate workload starts.

Carry this bounded continuation into the new regression while completing the
remaining host failure/retention/cleanup and provenance work. The probe saves the
original container's mounts and owner-derived context before close, then uses
each Job's actual fixture output. It changes no production owner. Three earlier
probe errors (new owner's empty preparation map, wrong Job B output, counting
custody helpers as workloads) remain retained/charged; they establish no new
product defect. Exact review review-2026-09-13T05-21-14Z.md and review-157946.json
bind27 stable candidate hashes. Reviewer42.5870492790109s; author143 measured
runs1220.011155285003s plus4 unknown-duration activities. M157653 and existing
integration gates remain pending. No full-feature sign-off.

## 2026-09-13T05:25:38Z — continuation integrated into the regression

**Confirmed:** claim157990 reviews handoff157988/M157987. The new test now
completes both original worker turns after reopen, with original mounts, adopted
Job contexts and each Job's own fixture output. Both implementation stages
complete and each original attempt has one workload start. The independent
repro-157990.py covers the whole author test including sweeps and observes
exactly one real adapter _provider call for each distinct original attempt,
Job A31 and Job B67. This supersedes author-continuation-integration pending
state. Preserve explicit Job/attempt/bound association in the regression during
the remaining edits; its current sorted bounds do not independently detect a
swap, although current behavior is verified by the probe. No separate return
solely for that strengthening is requested.

Next host failure/retention/cleanup at both boundaries and final27-path
provenance. M157653 and stage_execution overlap remain pending gates. Exact
review review-2026-09-13T05-25-38Z.md and review-157990.json/probe/log bind27
stable candidate hashes. Reviewer43.30132153701015s; author147 measured runs
1231.1839466419988s plus4 unknown-duration activities. No new product defect,
scope extension or full-feature sign-off.

## 2026-09-13T05:32:04Z — both host failure boundaries and scratch measured

**Confirmed:** claim158025 reviews handoff158023/M158022. Tuple association/count
assertions through replay now pass. Post-import is reachable on current bytes:
the correct earlier locator is repro-157534.py's second case, not repro-157990.py.
New repro-158025.py drives both host phases with timeout and start failure, four
ticks each. All four scenarios reach the expected real owner, make one77-second
host invocation and one materialization, then defer without new work. Actual
Job/result/phase scope is retained; target reference is unchanged and B integration
stays claimed. Both post-import result rows stay authorized.

**Confirmed cleanup boundary:** the original scratch in every scenario remains
after polls and composed.close(); fixture teardown runs afterwards and proves no
runtime cleanup. The current _run has no disposal branch and its failure memo
does not own a scratch locator. This supersedes the prior unmeasured original
scratch state, not the pending owner disposition or baseline attribution. The
HOST-FAILURE-PROPOSAL already requires explicit scratch ownership/lifecycle.
Do not claim the current state is an accepted retention policy or a newly
introduced leak without the appropriate owner/baseline evidence.

**Confirmed fixture caveat:** required_argv() composes another serving instance,
resetting _composed/engine, and _watching() calls it. After pending_judgments and
actual judgment turns, derive argv from the held deployment/task, then inject and
tick; do not recompose merely to read argv. The removed tests cannot establish
their exact cause from source now; retained failed step149/150 logs remain.

Use this reachable baseline for bounded author regressions, then finish27-path
provenance and overlap accounting. M157653 remains pending for durable owner
semantics/five-test authority. Exact review review-2026-09-13T05-32-04Z.md and
review-158025.json/logs bind27 stable hashes. Reviewer50.48564187100965s;
author151 measured runs1262.444742863001s plus4 unknown-duration activities.
No full-feature sign-off or dependent scope extension.

## 2026-09-13T05:38:06Z — post-import baseline regressions accepted

**Confirmed:** claim158071 reviews handoff158069/M158067. Four focused new cases
pass: configured post-import ceiling, timeout/start-failure one-call and phase
retention across four ticks, and scratch-count persistence through polls/close.
The corrected watcher uses the held task/deployment and no pre-arm tick.
These are accepted current-state baseline regressions; durable no-status failure
and scratch cleanup remain pending owner semantics, not completed acceptance.
All26 other candidate hashes match review158025, whose independent four-scenario
owner/result/reference/scratch evidence remains applicable without rerunning it.

Next final27-path provenance and explicit ownership/hunk accounting for both
stage_execution files. Identify foreign Work dependencies without modifying or
absorbing its edits. Five existing Job test changes still await M157653 along
with the two-source durable failure extension. Scratch step5 was already in that
proposal; new evidence does not expand or approve scope. Then return a concrete
packet for owner disposition. Exact review review-2026-09-13T05-38-06Z.md and
review-158071.json/log bind27 stable hashes. Reviewer58.256789800010665s;
author155 measured runs1308.9765907300025s plus4 unknown-duration activities.
No new product defect or full-feature sign-off.

## 2026-09-13T05:44:15Z — provenance audited; ready for owner disposition

**Confirmed:** claim158105 reviews handoff158103/M158102. All27 candidate and
recorded base byte/hash inventories validate against the current candidate and
named HEAD. PROVENANCE-REVIEW-158105.md supersedes the submitted packet's counts
and attribution:6 new paths,14 modified product/docs,7 existing tests. Foreign
completion-observation hunks belong to closed W71879, match its exact preserved
candidate methods, and have saved bases identical to current HEAD. Exact hunk
snapshots/identities are retained. Textual separation is proved; semantic
independence or a pass after excision is not. The13 earlier stage errors still
are not an unchanged-HEAD baseline. Five exact pending test changes are listed.

The packet is now concrete enough for the pending M157653 owner decision. Route
to baton.decide for the two-source durable failure extension, original step5
scratch disposition and five-test authority. No current process-local failure
baseline is promoted to final acceptance. On acceptance pin the ruling and
return to implementation; on amendment record the new boundary explicitly.
Integration still requires candidate/base/path/authority checks with W71879
dependencies accounted for. No full-feature or import sign-off.

Exact review review-2026-09-13T05-44-15Z.md, PROVENANCE-REVIEW-158105.md and
audit-158105.py/review-158105.json. Reviewer58.29267580300984s including read-only
audit; author155 runs1308.9765907300025s plus4 unknown activities. No new runtime
test execution or candidate changes.

## Owner ruling M157653 — pinned 2026-09-13T09:19:44Z

**Slawomir, on thread T156162 seq 159347:** "Approve HOST-FAILURE-PROPOSAL-2026-09-13.md and the exact five test updates in PROVENANCE-REVIEW-158105.md under W156162's bound dossier. Preserve bounded scope, independent review, W71879 provenance and spending. No acceptance waiver."

Pass comment 159348: "Pin the approved M157653 ruling in FINDING/PLAN. Implement the bounded durable host-failure semantics and scratch disposition with deterministic tests, then return for independent review."

**What it grants.** Exactly two additional product paths enter W156162's finite source scope — `src/baton_v12/integration/reconciliation.py` and `src/baton_v12/integration/execution.py` — for the tagged closed no-status host failure custody, the causal completed-prefix/failed-phase/not-run remainder, blocked causal versus held post-import outcomes, durable no-repeat before materialization, and explicit scratch disposition. And the exact five existing `tests/job_manager` expectation changes listed in `PROVENANCE-REVIEW-158105.md` are approved.

**What it does not grant.** No acceptance waiver, no further source or schema extension, no numeric verification-budget change, and no relaxation of independent review. Successful integer observation contracts stay byte-compatible; no exit status is invented, no implicit retry is added and no generic exception is relabelled.

*Pinned by baton.claude under claim 159350 at the owner's explicit direction; FINDING and PLAN are otherwise reviewer-owned.*

## 2026-09-13T09:34:47Z — approved failure extension has binding defects

**Confirmed:** claim159421 reviews owner159347/pass159348 and handoff159419/
M159416. The recorded approval supersedes the pending-authority state for the
two integration sources and exact five test changes; no acceptance waiver.

**P1:** reconciliation._failure discards the owning result and lacks failed/
completed-phase content and owner-held command/task/harness/environment/budget
checks. The post-import branch checks commit/tree but not the other expectations.
Independent repro-159421.py makes a real77-second injected host timeout, then
shows unrelated causal commit/tree/command/task/digest/environment and999999
seconds accepted into durable blocked custody. Post-import accepts the altered
non-content fields too. This falsely attributes failed work even though the
result stays fail-closed for publication. Validate against actual owners and
cover each mismatched member independently.

**P1:** an unmodified causal timeout records input_tree equal to input_commit,
different from prepared.tree. _no_status uses revision for both and the causal
failure bypasses the real tree lookup. Correct the producer at each phase as
well as the adopter, so proper validation does not merely cause repeated refusal.

Full matrix/provenance remain: all causal phases/reasons, malformed inputs,
signature/readback/replay through actual reopened owners, recovery, legacy
success and authorization, scratch disposal including failure. The accessor
failed_host_verification is not called by production and only reads causal
custody; its existence proves no post-import replay. Preserve actual queue-hold
behavior and verify it. Correct stale unapproved/process-local-only prose.
Prepare a new29-path packet retaining corrected W71879 attribution and the
old27-path packet as historical evidence. Exact review
review-2026-09-13T09-34-47Z.md/review-159421.json/probe/log bind29 unchanged hashes.
Reviewer62.55998214501051s; author173 runs1540.163787782978s plus4 unknown activities.
No full-feature/import acceptance or product edits by reviewer.

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

## 2026-09-13T10-27-22Z — causal resumed-serving and public blocked-result gates

**Confirmed:** claim159795 independently executes the fresh-serving reopen test
and six resumed sweeps: one host command at77 seconds, blocked custody preserved,
no judges. Additional actual _materialize counter remains1 before/after. This
supersedes the getter-only limitation for combined-timeout causal restart; it does
not cover post-import held queues, all phases or isolation. Candidate directory
census is not itself an actual materialization counter.

**Confirmed:** actual reopened blocked-result public publish_result and
record_result_evidence refuse policy/denied; record_imported refuses precondition;
each names blocked and leaves public result readback unchanged. This new reviewer
evidence supersedes missing public result-owner refusal evidence at those exact
boundaries. The author's new test still calls only shape/private helpers, so its
claim to execute these owners is superseded by review-2026-09-13T10-27-22Z.md's mapping. Carry real
calls/counters into focused regressions, preserving direct-judgment limits.

Remaining post-import restart/one hold, actual Journal replay/conflict, isolation,
recovery/new-result, runtime cleanup and final provenance stay authorized and open.
No new permission gate. Finish substantive matrix before another complete handoff;
record exact owner blockers if found.29 hashes stable, only new tools test changed
from review159705. Author199runs1918.1892541639681s plus4unknown activities;
reviewer81.83902408500035s. No full-feature/import sign-off or product/PROGRESS edit.

## 2026-09-13T10-38-32Z — post-import held restart independently accepted

**Confirmed:** claim159866 accepts two focused candidate tests. Actual public
publish_result and record_result_evidence refusal calls are present. Materialization
counter is installed but never asserted/read in candidate tests, superseding the
handoff claim that resumed serving asserts one; add that bounded assertion.
record_imported carryover remains omitted although reviewer159795 proved it.

**Confirmed:** repro-159866.py closes/reopens real serving and owners after actual
post-import timeout, then runs six sweeps. Host/materialize/block_target counts
remain1/1/1. Full target blocked account, queue entries and authorized result readback
are unchanged; one held B entry, unchanged target reference, no derived integration
receipt. This supersedes missing post-import timeout restart evidence at those
boundaries. Post-import result stays authorized while queue/target are held/blocked;
causal failure result is blocked. No Journal-conflict, isolation, recovery or
cleanup-lifecycle acceptance is implied.

Carry focused reviewer cases into new tests together; finish actual Journal replay/
conflict, isolation, explicit recovery and runtime-owned cleanup, then final29-path
provenance preserving correction159640/W71879. No new permission gate. Full scope
and sign-off remain pending. review-2026-09-13T10-38-32Z.md and review-159866.json/probe/logs bind29
stable hashes;28 other paths unchanged. Author205runs2030.067345054973s plus4unknown
activities; reviewer87.32187861899911s. No reset/transfer/product/PROGRESS/Git edits.

## 2026-09-13T10-48-56Z — three carryover tests and actual observation Journal replay

**Confirmed:** claim159935 accepts3focused tests. Causal materialization assertion
and record_imported call are now present, superseding specific omissions. New
post-import restart checks1/1/1 actual counts and unchanged entry rows, but still
omits exact authorized result/full target account/reference/absent receipt assertions
from accepted repro-159866. Carry those public assertions; existing independent
product evidence remains valid and is not reset.

**Confirmed:** repro-159935 drives record_causal_observations against actual retained
failure custody. Identical replay reaches real IntegrationStore.replay once;
changed valid diagnostic refuses operation-collision; no transact call/new command/
materialization and unchanged result readback. This supersedes exclusively-dict-level
Journal evidence for this one causal operation. It is not all-operand/fresh-process
replay, isolation or recovery evidence.

Remaining test carryover, Job/result/harness/phase isolation, explicit recovery/
new-result, direct judgment boundary, runtime-owned cleanup and final29-path
provenance remain authorized/open. Exact review review-2026-09-13T10-48-56Z.md and159935 JSON/scripts/
logs bind29stable hashes;28 other paths unchanged. Author212runs2134.517830444973s
plus4unknown activities; reviewer93.90548035699794s. No new permission gate,
reset/transfer, product/PROGRESS/Git mutation or full-feature/integration sign-off.

## 2026-09-13T11:08:02Z — carryovers and direct judgment refusal accepted

**Confirmed:** claim160060 independently passes all six changed regressions:
post-import restart's full public state/reference/receipt assertions, actual
Journal replay/conflict, and four composed base/isolated no-status cases. This
supersedes the10:48:56Z candidate carryover omissions; previously accepted owner
evidence remains valid. All29 hashes stable, only new tools test changed.

**Confirmed:** repro-160060 calls actual deployment judgment_subject/judge_result
on a composed blocked result. Both refuse precondition before any judgment
construction/engine call/dispatch change; result unchanged and host/materialization
counts1/1. This supersedes missing direct composed judgment refusal evidence at
that exact boundary. Carry the small test with the remaining substantive work.

**Revalidated limits:** existing abandon_held_lease/abandon_lease deliberately
leave target blocked and entry held; activation replay is not unblocking. Do not
invent automatic retry or host runtime interruption. Demonstrate supported
recovery/refusal and separate new-result isolation; name any missing capability.
_no_status retains failed-disposal path only in diagnostic text; deployment
closers have no scratch lifecycle. Runtime-owned cleanup remains required under
accepted step5, beyond fixture teardown. Actual Job/result/harness/phase isolation
and final consistent29-path provenance preserving159640/W71879 remain open.

review-2026-09-13T11-08-02Z.md and review-160060.json/scripts/logs bind evidence.
Author215runs2170.774839522972s plus4unknown activities; reviewer103.89273440600118s.
No numeric gate, reset, transfer, scope expansion or full-feature/import sign-off.
Exploratory absent judgments.py locator was a reviewer assumption; actual methods
were found/read/tested in stage_execution.py, not a missing required record.

### Routing correction after review160060

Canonical detail160086 confirms baton.bug resolves to rview/codex, so the
reviewer's initial use of that endpoint returned this completed review to itself.
This is a reviewer route-selection mistake, not a Baton defect. Claim160087
reacquires only to forward the completed review to baton.impl, next baton.feat;
no new implementation or verification is performed and spending is unchanged.
This supersedes the final review sentence naming baton.bug as the implementing
handoff. The review verdict, immutable evidence and all remaining scope stand.

## 2026-09-13T11:22:32Z — runtime cleanup accepted; suite attribution narrowed

**Confirmed:** claim160149 passes the three changed regressions. Independent
repro-160149 additionally proves second PUBLIC close succeeds after a refused
causal cleanup, and actual post-import timeout/start-failed scratch is removed
by ordinary close while fresh read-only result/target custody remains identical.
All cases keep command/materialization counts1/1. This supersedes missing cleanup
lifecycle at these tested boundaries. Registry belongs to deployment and surviving
paths stay reported until disposal; no crash-before-record guarantee is inferred.

**Corrected author attribution:** step218/219 thirteen errors are4missing
reconciles,8missing proposal,1missing fixture repository. Step95 already contains
those groups. Step220 proves only the four-error negative control against the
prior-reviewed source, not all13 or an unchanged-HEAD baseline. The dossier's
revert-160092-stage-execution.py is a transformation script; actual generated
source now retained as review-160149-prior-stage_execution.py, matching prior
3ee83301... hash. audit-160149.json preserves exact groups/log hashes. No new
cleanup-induced failure group observed; historical baseline limits remain.

Actual isolation and supported explicit recovery/refusal/new-result evidence,
then final29-path provenance preserving159640/W71879, remain authorized/open.
Carry the new public-lifecycle cases with substantive work; no new approval gate
or repeated broad suite is needed. review-2026-09-13T11-22-32Z.md/160149 ledger,
probes/logs/diff bind29stable hashes, only source+newtools test changed.
Author220runs2313.675153564982s plus4unknown activities; reviewer112.57892026800437s.
No reset/transfer, source/PROGRESS/Git edit by reviewer, or full-feature/import sign-off.

## 2026-09-13T11:36:15Z — isolation boundary corrected; recovery seam recorded

**Confirmed:** five focused candidate tests pass; public-close/post-import cleanup
carryovers accepted. The new isolation matrix really invokes _run six times and
refuses identical memo operands. This is useful low-level execution evidence.

**Confirmed limitation, superseding full-isolation handoff claim:** independent
repro-160230 reads job-a paired with job-b's IntegrationResult; another result id
belongs to a direct entry and result_of refuses it; phase variant yields raw
`causal`; bound variant manually overrides B77 with300. All raw answers retain
commit-as-tree before normal owner completion. No second coherent result adopts
these answers. Real base-added/changed-harness Job/result isolation remains.
Use real entrypoints and admitted related identities; do not insist that only
one string change when ownership requires several identities to agree.

**Observed recovery seam:** actual post-import timeout has no matching composed
runtime assignment. Runtime-oriented held_status/abandon_held_lease reject the
old assignment; composing from the blocked account rejects closed target access.
Public hold/result state and counts stay unchanged. Accepted as that negative
boundary, not successful recovery/new-result behavior or universal API absence.
The existing integer-failure branch likewise has no runtime assignment; queue
readers and lower trusted abandon_lease exist but were not exercised by this case.
Any host-aware extension needs defined quiescence authority and exact scope; do
not forge runtime evidence or relabel the account. No workaround is performed.

Independent authorized isolation/new-result/provenance work can continue; the
potential recovery extension is not a blanket owner gate. Preserve the exact
refusal for later concrete disposition without claiming resumption or waiving
acceptance. review-2026-09-13T11-36-15Z.md/160230 ledger/probes/logs bind29stable
hashes, only newtools test changed. Author229runs2372.2906757449964s plus4unknown
activities; reviewer122.06616825600395s. No reset/transfer/scope expansion/sign-off.

## 2026-09-13T11:49:41Z — additional-result setup proved; no fixture approval gate

**Confirmed:** relabelled unit and two-Job/one-derived-result tests pass. Independent
repro-160302 then uses existing public fixture setup to obtain TWO coherent derived
results for B(imported) and C(published), each with its own actual base-added/failing
and isolated/combined passing causal evidence. No test/product file edited; borrowed
fixture hash and readouts recorded. This supersedes a claimed authorization blocker
from the borrowed two-Job helper's limitations, not the still-missing failure matrix.

**Plan clarification within existing authority:** own additional-Job setup helpers
in the approved NEW test_execution_limits.py. Use actual Work/routes/capabilities,
post-setup policy, per-Job task/manifests/submission digests and judges; existing
four_works/four_jobs/four_submission helpers and repro-160302 map the concrete seam.
No borrowed fixture edit or additional existing-assertion approval is needed.
Failure adoption/isolation, repeat/reopen and configured bounds remain required.

**Confirmed packet:** all29 base/candidate hashes match; actual HEAD f3fc9e12...;
6new/16modifiedproductdocs/7existingtests, source19/test6 context hunks, exact
W71879 methods preserved. +2548/-132/156 totals exclude6new files and need that
label. Equal path hashes are not a HEAD-identity proof; audit-160302 pins HEAD.

**Documentation finding:** DEPLOYMENT705 newly says a fresh process reruns because
no durable outcome exists, contradicting642/669 and accepted runtime tests.
Distinguish local memo from durable result/queue failure custody; normal reopen
does not execute again. Preserve crash-before-record limits. Correct matching
stale source/test/packet prose with completion, then bind a new packet.

Runtime recovery refusal remains accurately limited; no new recovery source
expansion or acceptance waiver. Independent work can proceed without an owner
question. review-2026-09-13T11-49-41Z.md/160302 ledger/probes/log/audit bind stable
29candidate hashes. Author234runs2416.1856840719993s plus4unknown activities;
reviewer129.05033405900213s. No reset/transfer or full-feature/import sign-off.

## 2026-09-13T12:12:03Z — three-Job setup accepted; capacity and recovery remain

**Confirmed:** three focused tests pass. Actual B77/C61 use their own admitted
Jobs/tasks/manifests. B's causal timeout is durably blocked; C stays queued with
an explicit capacity deferral, and public composition recover finds no offers
to abandon/recover. Additional-Job setup is delivered, superseding the previous
missing-helper obstruction. The negative case is not two-failure isolation.

**Confirmed:** all29 provenance records match, pinned HEAD f3fc9e12... and exact
W71879 methods remain stable. Tracked-only totals are labelled correctly.
The new source AST equals the prior reviewed source; runtime evidence carries.

**Still incorrect:** source1741-1780 and HOST_OBSERVATION_CONTRACT/_host_retention
still describe the now-implemented durable failure contract as missing and the
approved reconciliation/execution paths as outside scope. The newly inserted
correct paragraph does not supersede that surrounding text. Correct the whole
live explanation and the corresponding stale new-test commentary, then bind a
new packet. Main DEPLOYMENT durability correction is accepted.

**Confirmed source map:** the held causal branch has no runtime completion;
scheduler reconciliation has no corresponding host terminal settlement. Public
recover reaches offer-restart recovery. Integration eligibility permits the one
configured actor, so another participant is not a simple capacity remedy.
Separate-deployment setup is authorized but not proof of shared-retention
isolation. Runtime-oriented post-import abandonment and trusted queue abandonment
have the distinct limits recorded in review12:12:03Z; neither supplies successful
host recovery/new-result scheduling. No forged assignment/quiescence or release.

**Open for scoped disposition after authorized corrections:** owner proof of host
terminality, exact assignment/offer/allocation ending without retry or erased
custody, and a legitimate new-result path after a post-import hold. No added
scheduler/delegation/recovery/schema authority or acceptance waiver here.

Reviewer integer-comparison probes failed at their blocked/held-state assumption;
v2 public read shows prepared/no causal observations. Preserve both failures;
no preexisting integer behavior or new product defect is inferred from them.
review-2026-09-13T12-12-03Z.md/review-160401.json/audit and logs bind29stable hashes.
Author243runs2481.982865931008s plus4unknown activities; reviewer147.39409734499532s.
No reset/transfer, product/PROGRESS/Git edit or full-feature/import sign-off.

## 2026-09-13T12:21:26Z — correction accepted; recovery scope ready for disposition

**Confirmed:** the complete live source/test explanation now describes the
implemented durable owner outcomes and additional cache correctly. This
supersedes the previous P2 correction requirement. All29 base/candidate hashes
and diff figures match the fresh packet; exact W71879 methods preserved. Source
AST changes only docstrings/explanatory constant; no execution branch change.
Author retained logs confirm3focused and141module tests pass; no repeated suite.

**Scope clarification:** crash-before-record exactly-once was expressly excluded
by the approved proposal. The new constant grouping that limit with stage
terminality adds no requirement. Delivery prose about what is not closed by this
Work is not an acceptance amendment. Positive recovery/isolation remains open.

**Proposed:** RECOVERY-SCOPE-DISPOSITION-2026-09-13.md recommends preserving
acceptance and scheduling a bounded host-terminality/recovery prerequisite, with
an exact independently reviewed design/path plan before implementation. It maps
the single-integrator allocation, claimed-offer, runtime-required abandonment and
held-target boundaries and their separate proof obligations. The alternative of
accepting current fail-closed/refusal behavior requires an explicit owner amendment;
none is made here. No source/schema expansion, retry or fabricated quiescence.

Minor current prose clarification: recover_on_restart reads issued/accepted offers,
so its empty report is an offer-state answer, not itself a runtime absence proof.
Carry that wording correction with the next substantive edit; no editorial-only
loop is needed before owner disposition.

review-2026-09-13T12-21-26Z.md/review-160499.json/audit bind29stable hashes atHEAD
f3fc9e12.... Author246runs2530.5844189850177s plus4unknown activities;
reviewer147.72804738899322s. Historical failed probes/spending retained. No reset,
transfer, product/PROGRESS/Git edit or full-feature/import sign-off. Route decide
for explicit scope disposition and pin the ruling before dependent execution.

## 2026-09-13T13:47:40Z — owner decision: integration uses the managed Docker lifecycle

**Confirmed owner decision, recorded by baton.prompt:** after discussing the
coordinator-local verification subprocess and its missing runtime recovery,
Slawomir ruled that integration must have the same isolation and treatment as
ordinary Jobs: "I think that's the only option since we want the same level of
isolation and treatment". Integration execution, including reconciliation and
its verification commands, must run within the managed Docker runtime lifecycle.
Containerizing only the coordinator does not satisfy this requirement: the actual
integration attempt must have the managed execution identity and lifecycle used
for timeout, termination, positive stop evidence, recovery and capacity settlement.

The owner additionally explained that Jobs may execute on a distributed farm,
with integration running on a different machine. The design must support that
placement: delivery of inputs/workspaces and collection of results, evidence and
runtime state must use explicit managed boundaries, not assume the coordinator's
local subprocess, filesystem or machine is the integration executor. This is a
design requirement, not an instruction to deploy a farm during this Work.

The owner identifies the existing input/output protocol as the deliberate basis
for relocating execution. Reuse that protocol's delivery, identity and result
contracts; do not introduce a coordinator-local shortcut or a second ad hoc
transport. The design must map integration's operands and evidence onto those
existing boundaries and identify any concrete gap before proposing an extension.

This **supersedes the proposed standalone host-terminality/recovery direction**
in RECOVERY-SCOPE-DISPOSITION-2026-09-13.md and the 12:21:26Z proposal above.
The current coordinator-local subprocess is evidence of the gap, not the required
architecture. Prepare a bounded prerequisite design that reuses the ordinary
managed runtime lifecycle instead of adding a parallel host-only recovery path.
Map exact interfaces, paths, compatibility and test authority for independent
review before added implementation. This ruling selects architecture; it does
not supply an unreviewed blanket implementation path set.

Preserve per-Job limits, failure custody, integration authorization and target
holds. Ending a failed attempt and releasing capacity must not imply success,
automatic retry, target repair or permission for a new result. Keep positive
recovery/isolation acceptance and W156162 open. Preserve applicable deterministic
evidence and all spending; fake/replay provider verification remains the default.
No crash-before-record exactly-once expansion is added. The prior 29-path review
remains historical partial evidence, not completion or import approval.

## 2026-09-13T13:58:24Z — managed integration prerequisite design prepared

**Confirmed:** claim161035 consumed reroute161030 and M161029. The confirmed
owner architecture selects managed Docker integration and relocation through the
existing input/output protocol. Formal obligation160528 remains pending; this
reviewer neither impersonates its responder nor treats it as blocking the already
confirmed planning direction. The standalone host-only recovery remedy is superseded.

**Observed source contracts:** ordinary launch/3, input/assignment manifests,
exchange, frozen output/collection and managed stop/cleanup supply reusable
boundaries. Existing integration assignment/1 instead requires a live writable
target lease, unavailable before derived preparation/judgments. Bundle/2 is a
direct-source evidence bundle, not complete reconciliation snapshots. Local
path/inode target and workspace proofs cannot be copied between machines.
GitIntegrationProfile is already standalone and intended for worker packaging.
Activate_assignment requires a real committed claim for the execution attempt;
JudgmentExecution provides a derived-execution example but has no pool allocation.
These are concrete gaps, not proof that a remote backend already exists.

**Proposed for independent review:** MANAGED-INTEGRATION-DESIGN-2026-09-13.md
uses ordinary managed input/output and lifecycle for a separately claimed
preparation execution charged to parent integration capacity, then authorized
managed apply under the parent's real stage attempt/lease. It specifies the
collected candidate/causal evidence boundary, actual positive-stop proof,
versioned derived apply semantics, remote target-owner validation and explicit
failed-phase ending. It does not turn a worker report or successful private
replica into canonical integration completion.

The design maps a finite proposed source path set, initial new tests and bounded
existing-test authority, compatibility, deterministic placement/lifecycle/race/
replay verification and exact open design-review gates. Generic launch/exchange/
manifest/lifecycle APIs are reuse-only; new schema/store/protocol changes require
concrete additional scope. No implementation authority, target repair, implicit
retry, live provider, farm deployment or exactly-once expansion is granted.
Independent design review must check phase claim/capacity ownership and the
target-owner publication boundary before those choices become accepted behavior.

research-161035.json pins27sourcefiles and an unchanged29-path W156162 candidate
atHEAD f3fc9e12cc89bebf9524cd173103df7af67d5212. No runtime tests executed for this
planning turn. Author246runs2530.5844189850177s plus4unknown activities;
reviewer147.73142127899519s includes the0.0033738900019670837s inventory. No reset/
transfer, product/PROGRESS/Git edits, self-review or full-feature/import sign-off.
Completed planning to baton.impl for independent review only, next baton.feat.

## 2026-09-13T14:00:22Z — formal owner response confirmed after handoff

Canonical detail after pass161101 shows obligation160528 responded at161051.
The full owner response, read through T156162, confirms the same managed Docker,
existing input/output and relocatable execution architecture already pinned at
13:47:40Z, preserving recovery/isolation acceptance and independently reviewed
bounded scope. This supersedes statements in the planning packet/handoff that
160528 remained pending; no architecture or implementation authority changed.
Baton.claude holds claim161103 for independent design review only. Coordination
message161104 records the same clarification. No owner-response wait remains.

## 2026-09-13T14:21:37Z — design review objections accepted; concrete v2 proposed

**Observed, baton.codex claim161207:** complete return161137 and M161127 read.
Independent DESIGN-REVIEW-161103-2026-09-13.md affirms the managed boundary,
ordinary identity/limits reuse and trusted target-owner publication, but rejects
the undefined subordinate capacity relation and requires portable custody in
slice one. This review is accepted as an objection to v1, not as implementation
sign-off. Current source confirms actual stage allocation FK/unique live indexes;
filtering a second child allocation out of an occupancy query would not overcome
those indexes. Every root release reaches `_move`, including cleanup and episode
ending. Existing integration result workspace/source fields are path-bearing and
consumed; integration schema5 has no migration today.

**Proposed:** MANAGED-INTEGRATION-DESIGN-v2-2026-09-13.md explicitly supersedes
v1's unspecified capacity representation, deferred portable scope and unresolved
target-owner boundary. It selects additive root/member relations, one actual
root allocation with all execution members visible, unique serial admission,
parent apply admission and all-release guarding. No child stage, second effective
principal, relaxed allocation index or hidden JudgmentExecution capacity.
Real Work/offer/claim identities precede admission; no future claim is fabricated.

V2 moves a closed portable task/report and separate managed result representation
into slice one. It proposes explicit bounded integration5→6 additive/read-only
compatibility and cross-legacy/managed one-result enforcement in the target-global
transaction. Local paths/inodes never become remote content identity. The trusted
target-owner entrypoint resolves actual local capabilities, rechecks the live
grant/admitted old revision and settles after collected verification/positive stop.
Existing input/output is reused; no ad hoc network protocol or deployed farm claim.

**Newly revalidated design gate:** preparation may fail before parent apply ever
starts. `finalize_quiescent_assignment` requires an attached runtime and therefore
cannot end this shape. Existing cancellation fences the assignment and reports
no stop ordered when none is attached, which is not absence evidence. V2 proposes
a narrow owned fenced-before-start reader proving cancellation/fence, no committed
start intent, no runtime and a cancelling axis; races require ordinary reconciliation
instead. This is NOT a new quiescence receipt or authority-gate discharge. Independent
review must affirm the exact proof before the added reader scope can be approved.

DESIGN-RESPONSE-161207.md maps every review finding; HANDOFF-DESIGN-161207.md
requests independent design review only. Exact first-slice schema/store/scheduler,
portable owner and narrow reader paths, later runtime/delivery slices, new tests
and exact legacy/managed method mapping are proposed. No implementation authority,
self-review approval, positive recovery waiver, target repair, implicit retry,
crash-before-record exactly-once or live-provider expansion follows.

research-161207.json fingerprints30sourcefiles; all29prior candidate paths and
27previously inventoried source paths unchanged. Read-only inventory
0.0027992710020043887s brings reviewer cumulative147.7342205499972s. Author246runs
2530.5844189850177s plus4unknown activities unchanged. No runtime test, product/test,
PROGRESS or Git mutation; no numeric cap/reset/transfer. W103525 consolidation
161193/161201 retains this prerequisite and later trace revalidation separately.
Return v2 for independent review before owner implementation scope selection.

## 2026-09-13T14:29:43Z — owner separates mandatory managed integration as W161230

**Confirmed:** full later thread messages M161222/M161232 read before handoff.
Slawomir requires managed Docker integration as a SEPARATE mandatory Work/job.
Baton.prompt created W161230 at
`baton:work/records/2026/09/finding-v12-managed-integration-execution/`.
Its current detail, complete thread and FINDING/PLAN were read. Do not create a
duplicate or move this historical dossier. This explicitly supersedes design
handoff wording that routed managed integration as implementation within W156162.

W156162 owns per-Job budget behavior and final recovery/isolation acceptance;
W161230 owns the isolated relocatable integration prerequisite and independent
review of its exact design/path plan. Existing v1/review161103 and v2/response161207
remain here; the new Work receives canonical references, not copied histories.
The present planning claim will record W156162's dependency and relinquish it.
No managed integration implementation starts in this consumer Work.

W161230 M161268 adds the owner-approved final criterion: project-pinned dependencies
and recorded actual versions for focused final verification. Existing jsonschema
mismatch is qualified historical evidence, to resolve/revalidate for selected
final checks; no separate environment project absent a concrete setup problem.
No live provider/farm run or new verification allowance is implied. This criterion
is reflected in the transferred v2 design. Spending and all candidate bytes remain
as recorded by research161207; separation resets or transfers neither budget.

## 2026-09-15T03:45:58Z — prerequisite complete; one focused test correction

**Confirmed:** W161230 closed satisfying174613 and W156162 was claimed174632.
The prior waiting/prerequisite-not-implemented status is superseded. Complete
current handoffs/discussion and bound record were read before review execution.
Review `review-2026-09-15T03-45-58Z.md` records the current evidence mapping and
exact next correction; `review-evidence-174632.json` binds the observed bytes.

**Observed:** pinned Python3.13.7/jsonschema4.26.0 run of the three execution_limits
modules plus Job-store tests produced253 tests:252 pass, one failure in
tests.tools.test_execution_limits.TheJobOwnerAnswersOneBoundaryWithoutADelivery.
test_a_migrated_job_with_no_limits_row_still_answers. Its preserved generation0
host-boundary assertion passes; its following schema5 assertion fails against6.
This matches previously classified W170387 row56. Return through baton.bug for
that sole test-path correction and affected-case rerun, then baton.feat review.
Preserve genuine migration/default coverage. Standing test authority suffices;
no product change or separate owner test approval is requested.

**Scope clarification:** accepted W161230 preparation/recovery/apply evidence is
reused; current33-path accepted chain and final deployment document match.
Owner rulings in managed-preparation-recovery FINDING2026-09-14T22:18:02Z,
22:25:29Z,22:32:06Z and22:33:45Z explicitly classify expanded managed failure,
limit/two-Job, partial-delivery and shutdown coverage as v13/unproved and retain
visible manual recovery for uncertain starts. Those later v12 rulings supersede
reading the old consumer recovery/isolation requirement as a mandate to rebuild
that deferred matrix. They do not erase earlier evidence or known concrete
defects. This review demonstrated no new budget implementation defect and grants
no live-provider/OCI certification or full-feature/import sign-off.

New measured execution44.307999097014545s, normal subprocess exit1, process group
gone. Reviewer measured total192.04221964701173s. Historical author246runs
2530.5844189850177s plus4unknown activities preserved; ordinary read time remains
unmeasured. Standing no-cumulative-gate policy applies. No implementation,
PROGRESS or Git mutation by reviewer; PLAN now names the bounded next action.

### 2026-09-15T03:48:18Z — correction routing

Pass174731 returned the incomplete item through baton.bug as policy requires;
canonical detail confirms that endpoint is reviewer-owned. Claim174733 completed
that triage without further implementation or verification. The review's sole
test correction now routes to baton.impl, with return to baton.feat. This is
normal endpoint routing, not a CLI defect or additional acceptance requirement;
all evidence and spending above remain unchanged.

## 2026-09-15T03:54:40Z — independent retained-scope acceptance

Reviewer174782 accepts candidate174738, manifest SHA256
1181863ca52453709dd0bbe354b45edee41187cec5d8e76bbdca37149a0f4502, and the retained
W156162 v12 outcome. Review `review-2026-09-15T03-54-40Z.md` and evidence
review-evidence-174782.json bind the result. The sole correction uses schema>=5
while preserving the actual legacy-generation/default assertion; exact prior
bytes reconstruct to66b1954e... and current candidate matches ea7257f4...,
225429 bytes/0664. Other observed paths are unchanged. This supersedes the
pending correction and withheld retained-scope acceptance in review174632.

Independent6-test class passes in pinned Python3.13.7/jsonschema4.26.0,
0.21377338099409826s, normal exit/group gone. Reuse prior252 passes and accepted
W161230 managed evidence, retaining the historical253-test failed run honestly.
The author numeric mutation tests an expected current-default-plus1 (300!=301),
not legacy-versus-current generation selection by itself; dedicated generation
coverage supplies the latter. The comment plus assertion diff and this narrower
mutation meaning are recorded without requiring an editorial-only cycle.

Reviewer measured total192.25599302800583s; author250 measured runs
2531.283201341037s plus historical unknowns. Reported author pre-edit reproduction
has no separate measured ledger row; no duration is fabricated. Standing ordinary
verification policy applies. No product/test/PROGRESS/Git edits by reviewer.

Return baton.ops for owner completion disposition. Manual recovery for uncertain
starts and explicitly deferred v13/unproved expanded causal/limit/two-Job,
partial-delivery and shutdown coverage remain as recorded in review174632 and
the prerequisite; no actual OCI/live-provider certification or broad-suite pass.
This is the retained technical outcome, not acceptance of deferred coverage.
