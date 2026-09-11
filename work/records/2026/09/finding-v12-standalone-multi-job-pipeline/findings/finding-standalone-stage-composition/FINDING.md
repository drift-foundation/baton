# Compose standalone v12 stage execution

Ledger Work: W103068

Parent: `work/records/2026/09/finding-v12-standalone-multi-job-pipeline/`

## Observed — 2026-09-06

The persistent Job Manager schedules implementation and review stages, the
Worker Manager owns durable workspaces and checkpoints, and the integration
package owns accepted-candidate admission, fenced execution, and manual
recovery. Those accepted components remain libraries. The only production
composition launches one implementation worker and returns its frozen result
to a v11 review Route.

Consequently one v12 submission cannot yet launch an independent reviewer,
record and act on its verdict, publish an accepted proposal, or drive the
serialized integrator. Performing those acts manually would violate the
two-Job proof's zero-ordinary-transition acceptance boundary.

## Confirmed boundary — 2026-09-06

Build the missing production composition as its own reviewed provider. It
composes accepted public interfaces and deployment profiles; it does not
redesign scheduling, workspace custody, checkpoint semantics, proposal
policy, integration ordering, or recovery.

The provider has three bounded leaves:

1. A review/correction stage driver launches the independently configured
   reviewer, freezes and attaches the checkpoint, records the verdict, and
   returns `changes-requested` Work to the same private development line.
2. A proposal/integration stage driver publishes the accepted candidate,
   admits its fully cross-bound account, obtains the target-global lease,
   invokes fenced integration, and records the completion or held recovery
   state.
3. A shared composition assembly binds both drivers to the persistent manager,
   profiles, credentials, status, and restart loop. It owns the common process
   and configuration boundary and follows the two disjoint drivers.

The first two leaves may advance concurrently only after they name disjoint
production and test paths. The shared assembly is not parallelized across
those paths. Reviewer and implementer use separate logical workers and agent
sessions even when an emergency profile maps both roles to one vendor.

## Acceptance

- One submitted Job advances from implementation through independent review,
  one same-line correction, accepted proposal publication, serialized
  integration, and terminal handoff without ordinary operator transitions.
- Every transition is driven from durable manager state and is safe to replay
  after process restart; container stdin/stdout lifetime is not the authority.
- Runtime launch uses explicit profiles and preserves role/session separation.
- Existing live-grant, custody, target-global lease, final-cutpoint, and
  operator-held recovery guarantees remain intact.
- Safe status and log locators remain observable throughout the composed path.
- The accepted provider supplies the exact commands, profiles, artifact roots,
  and verification surface required to freeze the two-Job proof plan.

## Non-goals

- Reopening accepted component contracts without a measured incompatibility.
- General remote adapters, a command-capable v12 TUI, or exhaustive hardening.
- Automatic policy decisions for uncertain or interrupted output.
- Running the two-Job acceptance proof inside this implementation Work.

## Independent plan revalidation — 2026-09-06

**Observed:** `job_manager.documents` admits implementation, review, and
integration stage kinds, and `scheduler.PooledManagerOperations` already
reserves a review worker after excluding the implementation worker,
participant, and principal. The persistent sweep nevertheless delegates the
same generic launch/exchange surface for every kind. The only concrete
deployment factory, `tools.single_worker`, rejects every kind and launch role
except one configured implementation Work and passes its result to a v11
review Route.

**Observed:** `worker_manager.review_cycles` is the accepted custody owner.
It creates one `(authority_uuid, work_id)` development line, grants a single
generation-fenced writer, freezes a checkpoint only after finalizing that
writer's Authority assignment, attaches a reviewer assignment for that SAME
Authority and Work, records an independently fenced verdict, and makes only
an accepted checkpoint integration-eligible. Consequently a Job's
implementation and review stages must name the same v12 Work. A submission
that gives those stages unrelated Work identities can be scheduled by the
generic parser but cannot be attached by the accepted review-cycle provider.
The production provider must refuse that shape before issuing an offer.

**Observed:** proposal publication is necessarily earlier than the initial
wording above implied. `Authority.publish` requires the exact LIVE producer
assignment. `review_cycles.freeze_checkpoint` calls
`finalize_quiescent_assignment`, which cancels and fences that assignment
before the checkpoint profile freezes the line. The retained reproduction
`repro-publish-after-fence.py` confirms that a publish attempted afterwards
refuses with `assignment generation was fenced and ended`.

**Confirmed ordering correction:** the integration driver owns proposal
publication, but its publication function is called during the implementation
ending after the generic output and proposal manifest are frozen and proved,
while the producer assignment is still live. Only then may the review driver
fence the writer and freeze the immutable checkpoint. Acceptance of that
checkpoint later authorizes the separately attributable verification,
technical-review, and configured approval receipts and admission; it does not
create the proposal retroactively. This supersedes item 2 of “Confirmed
boundary” only where that item can be read as publication after acceptance.

**Observed missing transition:** a `plan-rejected` review output projects as
`changes-requested`, but that state is terminal to the current Job Manager.
Only an abandoned offer opens a replacement episode. There is no public,
journalled operation that atomically closes the completed implementation and
changes-requested review episodes and opens their correction successors. The
accepted line provider can grant a correction writer, but no durable
scheduler act can produce the new assignment it requires. This is a measured
composition incompatibility, so the review/correction leaf may extend the Job
Manager's episode/document/schema/projection contract narrowly; it may not
create a parallel scheduler or a second account of Worker Manager state.

**Confirmed receipt policy:** the driver does not infer approval from a model
answer. A closed deployment configuration supplies separately attributable
Authority sessions and the pinned approval policy generation. Verification,
review, and approval remain three immutable Authority receipts even if one
deployment deliberately grants several capabilities to one principal.

### Reviewed Work and path split

- W103076 owns review/correction orchestration and the narrow Job Store
  correction-cycle extension: `baton_v12/job_manager/review_driver.py`,
  `job_manager/{__init__,documents,episodes,projection,schema}.py`, and focused
  tests under `tests/job_manager/`. It does not edit runtime deployment tools,
  Authority, integration modules, or the shared test registry.
- W103077 owns the provider-neutral proposal/receipt/admission/execution
  driver: `baton_v12/integration/driver.py`, `integration/__init__.py`, and
  `tests/integration/test_driver.py`. It does not edit Job Manager correction
  state, runtime deployment tools, or the shared test registry.
- W103083 owns the concrete process and configuration assembly after both
  drivers are accepted: `tools/stage_execution.py`, the required extraction or
  parameterization in `tools/single_worker.py`,
  `tests/tools/{test_stage_execution,test_single_worker}.py`, and
  `tools/parallel_test.py`. It does not redesign either accepted driver.

The two driver leaves therefore have disjoint paths. The shared assembly is
blocked on both and owns every inevitable common production/test path.

## Approved bounded composition and ownership — 2026-09-06

Slawomir approved keeping W103874 as the five-path proposal-manifest producer
owned by K and W103083 as K's bounded shared assembly. The absent producer
must be accepted before assembly; its dossier corrects the earlier proposed
worker-side `proposal.publish` remedy. Publication stays manager-to-Authority.

This supersedes an exhaustive reading of Acceptance's restart requirement as
a first-delivery test matrix. Preserve restart-safe behavior, role/session
separation and held uncertainty, prove the composed correction lifecycle and
one representative restart cutpoint, and reuse independently accepted leaf
evidence. The production composition must actually use the retained-manifest
producer. A new missing capability gets its own Work rather than growing this
assembly's path set.

Expanded coverage is recorded as independent W103950, bound to
`work/records/2026/09/finding-v12-stage-composition-hardening/`, intended for
baton.tuner. It is deferred until assembly is stable and explicitly scheduled,
outside this provider's containment and critical dependency graph. Its new
test file is disjoint from K's production, existing tests and registry paths.

Scheduling correction later on 2026-09-06: Slawomir superseded the deferred,
explicit-scheduling wording above. W103950 is approved work waiting on the
assembly, represented by a dependency on W103083 rather than a park. The
reverse dependency is not introduced; initial delivery does not wait on it.

## 2026-09-07T15-51-57Z — mandatory custody proof in assembly acceptance

**Confirmed decision:** owner reroute111426 on W105982 accepts its independent
review-2026-09-07T15-46-38Z.md. Accepted configured runtime evidence establishes
positive-stop line access, read-only review, same-line correction and checkpoint
use; actual sealed-result retention and survival after ordinary cleanup remain
unproved. This ruling supersedes waiting for full W105982 closure as a
composition prerequisite, once this residual proof is recorded here and in
`baton:work/records/2026/09/finding-v12-standalone-multi-job-pipeline/findings/finding-standalone-stage-composition/findings/finding-shared-stage-assembly/`.

**Mandatory first-delivery acceptance:** the assembled lifecycle must bind the
launched attempt and durable line/object pin to its actual completion and frozen
sealed result, record real public intake/retention receipts, and run ordinary
manager-authorized cleanup. Afterwards reopen the retained manifest and artifact
bytes at recorded locators, verify their digests, and reopen the same persistent
line with its durable pin validated. Show retained sibling custody stayed outside
every writable worker mount. Path inequality, Git checkpoint references, fixture
teardown and canned receipts do not prove this boundary. Cross-link the actual
proof and independent acceptance into
`baton:work/records/2026/09/finding-v12-private-line-custody-locators/`.

This requirement is part of W103083/W103068 lifecycle acceptance, not the deferred
hardening matrix. Preserve the existing assembly five-path focused-test/fixture
authority, custody additive-only scope and serial ownership; identify any extra
path, assertion change or execution scope before execution for scoped disposition.
Claim111429 performs documentation and only the approved W103068-on-W105982 edge
correction. No runtime or implementation is authorized by this administrative act.
W105982 and experimental child W106673 stay open; their closure/adoption gates
and production confirmed shutdown remain unchanged.

## 2026-09-07 — W112039 bounded review-ahead, owner M112547, claim112565

Owner M112547 authorizes temporary removal of the W112029 dependency solely to
claim and map accepted evidence while preserving final acceptance and downstream
gates. This supersedes waiting to perform any mapping until both provider
closures; it does not supersede the two-provider acceptance prerequisite.
The 13 current candidate hashes agree with both independent reviews. Existing
proof covers the ordinary path and lifecycle boundaries separately; the two
smallest final joins are actual admission after real freeze re-entry and public
admission refusal after missing cleanup history. Exact evidence map and limits:
evidence/joined-review-112565/REVIEW-AHEAD.md. No source/test edit or broad run.
Before relinquishing, re-read W112029 and restore its dependency if open; if
closed, continue the already authorized exact-candidate joined acceptance.

## 2026-09-07T18:45:07Z — W112039 joined acceptance, claim112565

**Confirmed:** W112029 closed satisfying112567 against its accepted manifest
before final execution; W110772 was already closed satisfying112501. Owner
M112547 therefore authorizes continuing the joined review without restoring an
open-provider gate. The two mapped gaps now pass: actual ordinary evidence and
real review-freeze re-entry reach durable Authority admission and exact replay;
missing cleanup history refuses before all receipt/admission effects. All13
candidate hashes match both accepted providers before/after, with no source/test
edit or broad rerun. This supersedes the preceding review-ahead pending-final-
checks status. Joined acceptance is recorded in review-2026-09-07T18-45-07Z.md
and evidence/joined-review-112565/. Close W112039 satisfying only; downstream
ownership, other dependencies and live restrictions remain unchanged.

## 2026-09-08 — approved multi-Job successor placement, M119126

**Confirmed owner ruling:** Slawomir approved the separate successor provider
under the stage-composition owner after independent shared-assembly acceptance,
as proposed in review-2026-09-08T12-29-16Z.md in the two-Job proof record.
This explicitly supersedes the pending-placement status of that recommendation.
Preserve the current one-Job assembly/custody/restart scope. Split multi-worker
configuration/pool composition from per-Job deployment/line binding, and require
joined acceptance before the demonstration freeze. The reviewer creates bounded
plans and dependencies before implementation. Shared source/test files are
owned serially, not by concurrent claims.

The successor's canonical record is
`baton:work/records/2026/09/finding-v12-multi-job-deployment/`. Its dossier is
promoted to a top-level path to retain readable paths and bounded dossier depth;
Baton containment still places it under the stage-composition owner. The two
implementation children each own only `v12/python/tools/stage_execution.py`
and additive controls in `v12/python/tests/tools/test_stage_execution.py`.
An explicit new multi-Job configuration variant preserves the old one-Job
schema/refusals; enumerate its exact document/interface before editing. No
external schema, scheduler/driver redesign, extra source path, unrelated test
assertion change, live runtime grant or manual-transition workaround follows.

## 2026-09-09T17:57:08.562564+00:00 — assembly retained-custody acceptance cross-link

baton:work/records/2026/09/finding-v12-standalone-multi-job-pipeline/findings/finding-standalone-stage-composition/findings/finding-shared-stage-assembly/review-2026-09-09T17-57-08Z.md
accepts the joined one-Job assembly, including the mandatory transferred
sealed-result intake/retention, ordinary cleanup, reopened manifest/artifact
digests and persistent line/checkpoint pin proof. Exact final consumer evidence:
baton:work/records/2026/09/finding-v12-standalone-multi-job-pipeline/findings/finding-standalone-stage-composition/findings/finding-composed-one-job-proof/review-2026-09-09T17-53-28Z.md.
The same recovered Job also reaches committed terminal integration. This
supersedes pending assembly-proof wording, not W105982 experimental-child
disposition or production confirmed-shutdown requirements. Commands/profiles/
locators and evidence limits are in the assembly CONSUMER-HANDOFF-2026-09-09.md.
31 parallel scan failures remain with W115981/W48697. Standing W71830
test-change authority supersedes historical per-test/additive-only gates.

## 2026-09-09T17:59:04.128785+00:00 — remaining composition acceptance

Claim129807 confirms one-Job assembly accepted but W119400, the multi-Job
successor placed under this parent by M119126, remains an open child. Parent
closure must wait for its joined acceptance. review-2026-09-09T17-59-04Z.md records the
missing dependency and accepted consumer handoff. This supersedes any inference
that W103083 closure alone now completes this parent. No new implementation,
planning Job, test gate or scheduler feature is authorized or needed.

## 2026-09-11T00:40:24Z — owner acceptance applied

Owner M140286/M140288 in T133129 and baton:work/records/2026/09/finding-v12-standalone-multi-job-pipeline/FINDING.md / PLAN.md at 2026-09-11T00:30:54Z govern. This explicitly supersedes older mandatory, essential and no-waiver wording below ONLY where it makes stronger robustness/resilience demonstrations prerequisites. Ordinary correctness, authorization, honest evidence, existing source scopes, cumulative budgets and file ownership remain. Deferred claims are unproved, never passed. No new planning Work or approval round is required.

Reuse accepted one-Job assembly and the W119400/W119405/R candidate/evidence chain at the existing parent handoff. Reconcile the actual ordinary deployment and prepare its concrete configured invocation/input handoff for W71879; do not introduce a fresh assembly implementation, planning prerequisite or test campaign. Retain existing custody/restart evidence without reexecution.

Any older mandatory restart/fault-C/adversarial/race demonstration wording is superseded for this feasibility milestone. Those stronger claims are deferred and unproved beyond retained evidence. Actual submission isolation, review/test authority, correct integration/completion and suitable public observation remain necessary. W71879 must execute real configured standalone providers; the controlled component fixture is not that execution. Existing scopes, budgets and child completion rules remain.

## 2026-09-11T01:22:35Z — actual production handoff remains incomplete

Confirmed under reviewer140591: tools.stage_execution:factory calls operations_from
without integration_port; _integration_ports returns None for each Job and the
direct Integration._run branch refuses before prepare/admission. The production
tree contains the port class but no constructor call. The A/B fixture constructs
ports and explicitly reconnects operations_from after acceptance. The complete
static trace and exact current source/fixture locators are in
review-2026-09-11T01-22-35Z.md. No execution was invented or performed here.

This explicitly supersedes the inference in the preceding handoff that all
contained provider closures permit final W103068 acceptance. Their bounded
component/custody results remain valid; the production constructor is still
missing from the original assembly handoff obligation. A manual test connect()
or guessed future proposal is not a legitimate standalone fix.

Confirmed additional consumer boundary: the derived B path publishes and waits
for independently owned receipts; the fixture creates them with real sessions.
The concrete autonomous production judgment consumer is not supplied by the
inspected path and must be identified or wired, without fabricated approval.
Direct A port construction is the first deterministic blocker. These concern
ordinary successful execution and are not parked resilience demonstrations.

Return W103068 through baton.ops for the bounded production correction and
verification assignment described in the review, keeping W71879 gated. No new
planning Work, implicit source expansion or budget transfer; existing same-scope
component evidence is reused. Static review adds no runtime verification charge.

## 2026-09-11T01:30:06Z — owner approves production correction and ceilings

Owner baton.slaw return140663 approves review-2026-09-11T01-22-35Z.md and
directs pinning and serial baton.claude ownership of exactly
v12/python/tools/stage_execution.py and v12/python/tests/tools/test_stage_execution.py.
Whitespace introduced inside the returned path spellings is interpreted as
the exact existing pair named by that review; no new path or broader authority.

Wire production integration-port construction and establish the actual
independent derived-result judgment consumer. Verify the public configured
factory without injected ports or reconnect steps. No fabricated judgments or
manual repair. Additional required source scope must return with concrete
evidence. Independently review the correction, then prepare actual W71879
standalone execution. Existing component evidence is reused; hardening remains
deferred. This supersedes pending source-owner/allocation status above.

The cumulative per-Job author ceiling increases450s to570s and reviewer5s to25s,
retaining all spending and uncertainty. Author carry383.35242021799934s and
reviewer4.750571445997288s precede this placement check; joined40s is unchanged.
The120s author increase funds this correction; old reserved balances are not
transferred. The20s reviewer increase is cumulative, not a fresh25s allowance.
Earlier untimed runs, mistaken probes and overruns stay recorded without
retroactive authorization. No reset or use of separate prerequisite budgets.

Placement claim140665 pins the ruling before author dispatch. This existing
Work carries the authorized correction and returns to baton.feat for independent
review; no new planning Work or additional approval round. W71879 remains gated
until the actual missing production path is independently accepted.

Placement evidence: evidence/placement-140665/result.json confirms all43 accepted
R140229 entries unchanged with zero drift; the two author paths are retained in
its candidate/ directory. No product/test changes or runtime tests. Continuity
elapsed0.0023577829997520894s plus0.05s outer reserve charges0.05235778299975209s,
giving reviewer cumulative4.80292922899704/25s. Author carry remains
383.35242021799934/570s plus all uncertainty; added120s correction and unchanged
joined40s remain distinct. Static reading/dossier work is disclosed unmeasured
activity on the inherited basis. Dispatch the approved two-path correction now.

## 2026-09-11T02:06:10Z — correction review: factory defaults still refuse

Confirmed reviewer140835, review-2026-09-11T02-06-10Z.md: author140686's
new dynamic construction works with injected capabilities, but literal factory
retains engine_run=None and credential_provider=None and its new constructor
refuses. This explicitly supersedes the P1-resolved claim in PROGRESS/M140813;
partial two-file construction work remains retained. Independent evidence:
evidence/review-140835/ (actual factory-default refusal plus passing injected
control, exact candidate copies/diffs,43-entry continuity, no unexpected drift).
B's authentic derived-result judgment consumer is still missing. Literal-call
search is not exhaustive: driver._receipt invokes session verbs dynamically.
Do not infer that holding sessions alone grants judgment or that a new worker
role is necessarily required. The actual consumer must bind genuine independent
judgments to the derived candidate under the existing public acceptance contract.

Audit corrects the author handoff:15 nonzero runs,160.93217554400326s this claim,
cumulative544.2845957620026/570s plus uncertainty. The120s correction allocation
was exceeded by40.93217554400326s; nominal25.715404237997404s remaining cannot
also preserve unchanged joined40s. No reserve transfer or retroactive approval.
Reviewer cumulative6.64732907199965/25s includes all three probe attempts and
outer reserves; two setup refusals are preserved, not reported as product proof.
Return the existing Work through baton.bug for owner allocation/scope disposition,
then serial correction and independent review. No new planning Work or robustness
gate; W71879 still requires the actual runnable provider before ordinary A/B proof.

## 2026-09-11T02:11:47Z — owner140905 approves four-file correction

Owner accepts review-2026-09-11T02-06-10Z.md and the prior correction overrun
40.93217554400326s, retaining cumulative author544.2845957620026s plus
uncertainty and every failed run. Author ceiling becomes800s with a new180s
correction allocation; joined40s and other reserves remain. Reviewer25s carries
6.64732907199965s before this placement. This explicitly supersedes the pending
owner-disposition status and prior570s ceiling; it does not erase the overrun.

Serial baton.claude owns exactly tools/stage_execution.py, tools/single_worker.py,
tests/tools/test_stage_execution.py and tests/tools/test_single_worker.py under
v12/python. Retain the partial candidate. Concrete design is pinned in
DESIGN-2026-09-11T02-11-47Z.md: share the effective production engine/provider
capabilities; dispatch the exact published derived subject to authentic independent
judgment through supported worker/review/custody interfaces; adopt correlated
real reports as scoped receipts; preserve distinct owners and current policy.
Session possession alone neither proves judgment nor forbids evidence-backed
receipt recording. Additional required source paths return with exact evidence.
First literal factory defaults reach A prepare/start/continuation, then B genuine
judgment and authorized terminal completion. Correct inaccurate test claims,
reuse baseline evidence, no broad reruns, no fabricated judgment/manual repair.
Independent review precedes W71879 actual A/B; hardening remains deferred.

Placement140907 retains all four candidate inputs and checks43 R entries plus
the newly owned single_worker pair without unexpected drift. Exact hashes/modes
and copies: evidence/placement-140907/result.json and candidate/. Its initial
script wrongly indexed the single_worker path in R's43-entry union; that reviewer
mistake and a conservative1s charge remain recorded. Total placement charge
1.0555699340009597s; reviewer cumulative7.702899006000609/25s. Author spending
unchanged; no product/test changes or runtime tests. Dispatch the authorized
correction on this Work now; no new planning prerequisite or approval round.

## 2026-09-11T02:27:46Z — P1 accepted; authorized P2 configuration clarified

Reviewer140987 accepts the default-capability correction in author140937:
literal factory now supplies effective engine and the actual resolved integration
credential provider. Independent factory-to-direct-A-completion join passes;
evidence/review-140987/ retains the exact four inputs/diffs and45-entry continuity
with no unexpected drift. review-2026-09-11T02-27-46Z.md explicitly supersedes
P1-factory-default-blocked status, while W103068 still requires P2.

Author says P2's execution configuration and read-only derived-subject boundary
fit the approved four files and has150.46587770600308s remaining. Owner140905's
instruction to implement that authentic consumer already authorizes its necessary
bounded configuration; there is no separate approval rule for that implementation
detail. The earlier design only required return for an actual additional-path
or unsupported-interface gap. This explicitly supersedes the pending-new-owner-
configuration-approval inference in M140983/PROGRESS. No approval is fabricated
and no new product source scope is granted by this clarification.

DESIGN-2026-09-11T02-27-46Z.md pins a separate optional result_judgment_workers
configuration per bound Job, with verification/review/approval each naming a
complete supported worker deployment and worker identity. Match configured
receipt actors and scopes; preserve the original three-stage pool. Compose
actual authorized worker dispatch over exact retained derived custody and consume
correlated frozen reports before evidence-backed scoped receipts. No original
review substitution, fake assignments/runtime or manual demo repair. Additional
required paths/interfaces return concrete evidence; configuring this already
approved consumer alone is not another owner gate. Pass existing Work serially
to baton.impl, next baton.feat, with P1 retained and no new planning Work.

Audit: author573.8187180559995/800s plus uncertainty,29.534122293996916s consumed
of existing180s correction,150.46587770600308s left. Nonzero steps are1 and5;
step2 diagnostic exited0.13 focused errors match retained baseline identities.
No full-suite success or waiver is inferred. Reviewer8.952968286004273/25s after
1.2500692800036632s charged retention/audit/independent join. No product/test edits
by reviewer; static reads/dossier work disclosed unmeasured. Joined40s and other
reserves remain. W71879 actual A/B follows P2 independent acceptance; hardening
remains deferred.

## 2026-09-11T02:41:03Z — configuration retained; execution still required

Reviewer141074 retains author141024 configuration/derived-subject additions.
review-2026-09-11T02-41-03Z.md and evidence/review-141074/ bind the partial
candidate:45 entries without unexpected drift, eight added tests, no changed
existing test AST. No runtime rerun. This does not accept a judgment consumer:
dispatch, frozen-report correlation and scoped receipts remain unimplemented.
P1 remains independently accepted; W71879 remains gated on complete P2.

Continue under owner140905 in the same four files. Resolve judgment deployment
principals/Works/scopes through Authority before effectful use; _resolved still
only visits stage workers. New judgment_execution fixture copies the original
Work reference, so its claimed own-Work execution is not established. Configure
legitimate judge Works/manifests and obtain actual assignments normally, then
mount exact derived custody read-only, dispatch and adopt authentic frozen
reports before authorization/import/terminal completion. No fabricated assignment,
receipt/runtime, original-review substitution or manual repair. No new approval,
planning Work or additional path is currently reported or required.

Author652.9370181620048/800s plus uncertainty; correction108.65242240000225/180s,
71.34757759999775s remains. Nonzero correction runs1/5/7/8/10 retained; step2 is
an exit-zero diagnostic and13 baseline errors belong to regression5/10. Prior
accepted overrun and joined40s/other reserves remain. Reviewer9.083004062006024/25s
after0.13003577600175048s static retention/AST/audit; static reads unmeasured.
Pass serially to baton.impl next baton.feat. Continue through context compaction;
working context alone is not an additional approval gate or completion milestone.
Use focused execution verification, not repeated47/152-case baseline runs solely
because a new claim began. Hardening stays deferred.

## 2026-09-11T02:53:00Z — repeated execution-delivery limit; owner disposition

Reviewer141138 retains author141103 principal/Work preflight and distinct judge
Work/task/manifest fixes. Exact review-2026-09-11T02-53-00Z.md and
 evidence/review-141138/ bind all four inputs and45-entry continuity without drift.
No judge execution, dispatch or authentic report return exists yet. P1 remains
accepted; W71879 remains gated. Two new controls and strengthened own-Work
assertions match scope; retained201-test/13-error result is not aggregate green.

Observed operational issue: M141132 reports a third context-limited author return;
prior review141074 already directed continuation across compaction. This explicitly
supersedes automatic unchanged redispatch as the current action. The core task
is fully specified within the four files, not an additional design prerequisite.
Return through baton.bug then route to baton.ops for explicit execution reassignment
or concrete repair of the existing author continuation. Recommend another existing
implementer, e.g. baton.tuner, with baton.codex retained as independent reviewer;
this recommendation grants no source ownership by itself. One live context per
participant, serial four-file custody, no hidden second context or new planning Work.

Concrete remainder is bounded real judge assignment/runtime/read-only derived
input/separate frozen report custody plus composed dispatch/poll/correlation and
scoped receipts, followed by existing authorized B import/terminal completion.
Do not repeat broad baseline runs before that code exists. No fabricated evidence,
manual claims/repair or original-review substitution. Hardened failure proof stays
deferred, not a reason for this return.

Author700.5897750580131/800s plus uncertainty, correction156.30517929601046/180s,
remaining23.694820703989535s. All failures and accepted prior overrun preserved;
joined40s/other reserves unchanged. No new budget inferred. Reviewer
9.146181310000488/25s after0.06317724799446296s static retention/audit. No runtime
rerun or product/test edits; source/dossier reads disclosed unmeasured.

## 2026-09-11T03:09:21Z — owner141241 reassigns completion to baton.tuner

Owner pass141241 explicitly reassigns remaining implementation to baton.tuner
serially in the existing four files; baton.codex retains independent review.
This supersedes the pending execution-disposition and baton.claude ownership
statements above. Successful tuner claim141250 owns this episode. The exact
review141138 four-file input has been revalidated byte-identical, all0664, and
remains retained in evidence/review-141138/candidate/.

Complete actual judge assignments/runtime over read-only derived input with
separate frozen report output, dispatch/poll/correlation and evidence-backed
current-policy receipts, then normal B import/terminal completion. Reuse accepted
A and baseline evidence; first focused witness exercises B's actual consumer.
No preliminary broad rerun, fabricated receipts, manual repair, new planning
Work or hidden context. Continue across compaction from these records.

Owner adds120s: correction ceiling300s and cumulative author ceiling920s. Carry
author700.5897750580131s plus uncertainty, correction156.30517929601046s, all
failures and accepted prior40.93217554400326s overrun. Remaining correction
143.69482070398954s. Joined40s and all other reserves remain untransferred.
Reviewer9.146181310000488/25s unchanged. Completed candidate returns through
baton.feat for independent review, then W71879 actual A/B execution.

### 2026-09-11 — claim141250 execution design and preflight correction

Confirmed against current owners: one control store owns one workspace storage root; the earlier configuration fixture gave each judge a different root, which cannot launch. Judges use the configured manager storage with independent assignment directories, launch homes and credential homes. This supersedes the fixture-specific separate-storage assumption; no manager ownership rule changes.

Implementation within the four assigned paths reuses ordinary single-worker admission, claim, runtime, command exchange and full freeze/intake/retention/pass/cleanup. Each judge gets a deterministic execution identity over the coordinator-derived subject, judgment kind, actor, input and current policy generation. An auxiliary read-only judgment.json carries that subject and causal observations beside the existing task; its exact bytes are proved on recovery. The configured review workload already emits a frozen findings report with observed base/head/tree; that accepted contract is reused and cross-bound to the exact assignment, completed result, accepted intake and derived candidate before issuing an evidence-derived receipt. No worker protocol extension or fabricated positive report is introduced.

A private copy-safe Git snapshot is materialized from integration-owned storage and detached at the prepared derived candidate before read-only delivery. Judges have separate writable report output. Only all three completed accepted judgments authorize receipts; policy drift refuses reuse. Absence of configured consumers keeps the accepted pending behavior. Additive consumer tests exercise the real B branch first, genuine worker exchange/freeze/custody and negative correlation/replay; no preliminary broad runtime test.

### 2026-09-11T03:33:40Z — claim141250 observed consumer completion, awaiting independent review

Observed: final focused witness executes all three configured judges under their own real assignments and review runtimes, collects separate frozen reports and completes ordinary A/B integration. It explicitly proves read-only source/input and writable independent report output. Correlated report evidence and receipt decisions are retained in evidence/tuner-141250/consumer-witness.json. The source snapshot uses a copy-safe clone followed by explicit prepared-candidate fetch before detach; a bare integration store does not advertise that candidate as an ordinary branch. The ordinary review report has a text findings member; the consumer now reads that accepted contract directly from frozen custody. These observations supersede earlier statements that the executor is absent; they do not claim independent acceptance or real standalone/model proof. Exact final candidate and limitations are in HANDOFF-141250.md.

## 2026-09-11T03:42:24Z — independent final composition acceptance, reviewer141384

review-2026-09-11T03-42-24Z.md accepts tuner141250 exact four-file candidate. Independent literal-factory B success and rejected-report refusal both pass;45-entry continuity has no unexpected drift. This explicitly supersedes earlier missing-executor/factory blockers and awaiting-independent-review status, preserving their evidence. Author731.3390351440088/920s plus uncertainty, correction187.05443938200625/300s; reviewer13.312307043996647/25s including conservative1s failed-audit charge. No baseline waiver, budget transfer or live-model claim. W103068 can close; CONSUMER-HANDOFF-2026-09-11T03-42-24Z.md advances existing W71879 to the actual ordinary A/B run. Stronger resilience/fault-C/detached-observer/cleanup guarantees stay deferred.
