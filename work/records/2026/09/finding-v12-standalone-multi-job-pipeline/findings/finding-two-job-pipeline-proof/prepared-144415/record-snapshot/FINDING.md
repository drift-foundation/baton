# Prove the standalone two-Job v12 pipeline

Ledger Work: W71879

Parent: `work/records/2026/09/finding-v12-standalone-multi-job-pipeline/`

## Confirmed scope

Run one integrated, evidence-producing acceptance demonstration after the
bounded control-plane, source/workspace, concurrent-stage, review-correction,
and integration leaves are available. This leaf owns fixtures, one submission,
measurement, retained evidence, and the independent assessment of the whole
vertical slice. It does not repair a component defect inline; a defect returns
to its owning Work and this proof is rerun from a clean submission.

## Review-ahead scheduling ruling — 2026-09-04

The open component dependencies constrain FREEZING AND RUNNING the integrated
proof, not independent review of its demonstration contract. The scenario
shape, required evidence, operator-intervention budget, test-change authority,
resource measurements, and pass/fail boundary can be reviewed before those
components finish. That review may require a targeted delta review if a
component's accepted interface later differs materially from the assumptions
recorded here; it cannot claim that the demonstration itself passed.

Protocol 11 cannot represent those stage-scoped edges. For review-ahead, the
eligible reviewer temporarily removes the open component edges, claims and
reviews this plan, restores every still-open component edge before leaving
review, and reroutes the Work to implementation. Restoring the first edge
atomically releases the review claim, so this is deliberately a
`block`-then-`reroute` ceremony rather than a `pass`. The live proof therefore
stays blocked until all providers are accepted, then becomes runnable without
an operator watching the queue.

## Demonstration shape

- Submit at least two independent Git-backed Jobs from the same immutable base
  commit in one documented CLI/JSON operation.
- Run both implementation containers concurrently in separate disk-backed
  manager-custodied workspaces with immutable read-only source mounts,
  separate durable output/log locations, and bounded scratch.
- Send each immutable candidate checkpoint to an independent containerized
  reviewer. Force one bounded changes-requested result, return that Work to the
  same private development line, and accept a later checkpoint without another
  source clone or candidate-tree copy.
- Include one explicitly planned existing-test modification within its Work
  scope. Also inject one distinct out-of-scope test mutation and prove the
  integration preflight refuses it before any canonical path changes.
- Queue accepted proposals to the one-target integrator and import them
  serially. Slawomir retains final Git ownership.
- Inject one worker/runtime failure and prove the other Job and available
  slots continue without a full manager or v11 restart.

## Acceptance evidence

- The submitted document, immutable source/base identity, Job/offer/claim/
  attempt/session identities, workspace/source mounts, checkpoints, review
  verdicts, integration queue/lease records, and final handoffs are retained.
- The status projection is sampled at queued, offered, claimed, running,
  reviewing, changes-requested, integrating, completed, and exceptional states
  and includes runtime identities plus safe relative log/activity locators.
- Process/container timing proves at least two implementation runtimes overlap.
  Review and integration timing proves reviews may overlap unrelated coding
  while one target's integrations do not overlap.
- Filesystem evidence proves source mounts stay unchanged, writable workspaces
  are distinct and disk-backed, the correction reuses one private line, and
  canonical paths are untouched by the refused candidate.
- Operator intervention is enumerated. Ordinary transition count is zero;
  allowed human acts are initial submission, the deliberately forced review
  verdict or policy decision, exceptional observation, and final Git action.
- Record wall latency, per-stage latency, CPU utilization, peak workspace and
  scratch use, retained artifact sizes, failures/refusals, and every operator
  intervention.
- Independent review either calls this narrow design promising or records the
  exact false-success/blocking defect and links the owning follow-up Work.

## Test-change authority

This Work authorizes creating demonstration fixtures and adding or editing
tests within the exact paths named by the final frozen run plan. It explicitly
requires one planned existing-test modification and one out-of-scope mutation
fixture. The accepted candidate/review must enumerate those paths; any deletion
or weakened production expectation must be separately explicit. No other test
mutation is authorized.

## Entry-gate revalidation — 2026-09-06 — baton.claude

PLAN item 2 is the gate that has to pass before the run can be frozen, and it
does not pass. What it finds is not interface DRIFT. Every component provider
is closed and its recorded interface is the one this contract assumes. What is
missing is the DEPLOYMENT HALF that would make one submission drive the
vertical slice, and it is missing for everything except a single implementation
worker.

**The rule this record already holds is why that matters.** The control plane
knows WHEN an act is owed and deliberately does not know HOW a deployment opens
an Authority, delivers credentials or starts a runtime; `job_manager/
delegation.py` states it in its own words -- "Starting a runtime needs a
delivered workspace and a runtime adapter (W71917); freezing an output,
deciding a verdict and importing a proposal need review and integration policy
(W71918, W71878). Those operations exist and are not called from here." Every
component leaf is a library plus that stated omission. W76207 supplied the
omitted half for ONE implementation worker, as its own independently reviewed
Work with its own configuration schema.

**What exists, checked against the tree rather than against the records.**

- `tools/single_worker.py` is the only production composition, and it refuses
  to be anything else: `given["launch_role"] != "implementation"` is a policy
  refusal, and its own header says "This is deliberately not a pool ... worker
  choice and capacity belong to W71877."
- It hands a frozen result to a configured **v11 review Route**. That is a
  human/agent review through the ledger, not the containerized independent
  reviewer this contract requires.
- `integrate_next` has NO caller outside `baton_v12.integration` and its tests.
  Nothing outside the package even imports the integration package.
- `record_verdict` and `integration_checkpoint` have no caller outside the
  Worker Manager's own `__init__` re-export and tests. No program turns an
  accepted checkpoint into a published proposal, and no program admits one.

**What the control plane does supply**, so the gap is named accurately: the
scheduler carries both lanes, and a review stage already excludes the worker,
participant and principal of its Job's implementation stage. Reviewer
independence is implemented. Nothing runs it.

**The consequence for this leaf's own acceptance boundary.** The contract
requires zero ordinary operator transitions after one submission. Today the
transitions that would have to be manual are: starting every review runtime,
freezing each checkpoint, recording each verdict, returning the corrected line,
publishing each proposal, and every integration. A run performed that way does
not fail the demonstration -- it CANNOT BE the demonstration, because the thing
being demonstrated is that nobody does those by hand.

**Disposition, and why it is not "build it here".** Plan item 3 cannot be
frozen: it must name verification commands and artifact roots that do not
exist, and the approved test-change authority is bounded to "the exact paths
named by the final frozen run plan". Building the missing compositions would
also put credential, image-digest and network authority into a leaf whose
independent review is about EVIDENCE rather than about deployment safety --
and W76207 is this record's own precedent that one such composition is a Work
with its own review. This leaf therefore reports the gap and asks the owner to
place it, rather than growing to fill it.

## Owner placement ruling — 2026-09-06

The missing deployment composition is a separate provider under the
standalone-pipeline milestone. This proof remains unchanged and blocked until
that provider is independently accepted. The provider separates the
review/correction driver from the proposal/integration driver so they may be
implemented concurrently without overlapping files, then gives their shared
process and configuration boundary to a final assembly leaf. This proof does
not manually substitute for any missing ordinary transition and does not
repair the provider inline.

## 2026-09-08 — owner-approved preparation before final freeze

Slawomir approved preparing contracts and measurement requirements ahead of
provider completion. PREPARATION-2026-09-08.md collects the freeze inputs and
their suppliers, Job roles and evidence checklist. The original contract already
has independent plan approval in review-2026-09-04T14-10-08Z.md; final concrete
freeze and material-delta review remain required. No live gate was removed.

Open scenario clarification: accepted W71877 policy leaves injected failures
exceptional without an operator retry, while this run forbids ordinary retries.
The proposed third fault Job would preserve two successful integrations and
failure containment in one submission. Owner guidance is pending; this proposal
does not supersede the current two-Job reviewed plan or authorize extra execution.

## 2026-09-08 — demonstration plan approved

Slawomir approved PREPARATION-2026-09-08.md in the W71879 record, including
two Jobs intended to complete and a third small Job carrying the deliberate
failure, all in one submission. This supersedes the earlier pending scenario
question and exact-two-document wording of the demonstration plan. Both successful
integrations, required runtime overlaps, independent review/correction, scoped
test modification, companion refusal and failure containment remain mandatory.
No automatic retry, ordinary operator transition or stack restart repairs the run.
The final base, exact paths/documents, deployment identities, commands, metrics
and budgets still require the existing concrete freeze and material-delta review;
this approval is not a claim that the demonstration ran or passed.

## 2026-09-08 — parallel tuner preparation authorized

Slawomir requested useful parallel work for tuner while Claude executes W110774.
Assign one lightweight preparation Work to baton.tuner, role tuner, with no new
dependency or duplicate dossier binding. Its exclusive write path is
TUNER-PREFLIGHT-2026-09-08.md in this existing record; it may read accepted
component contracts and current source to prepare the approved demonstration.
The output names concrete Job scenarios, failure/refusal injection seams,
measurement/resource proposals and the exact assembly-supplied freeze inputs.
Separate confirmed APIs from pending interfaces; retain provider gates. No
source/test/shared-plan edits, tests, runtime launches, live submission, fixture
execution or Git mutation. This prepares the existing proof rather than creating
a new hardening or acceptance prerequisite.

Created as lightweight W115572, thread T115572. Initial canonical create was
denied by the sandbox's read-only external ledger access; approved execution of
the same standalone command succeeded at115572. No raw-store workaround or
duplicate consumer was used. The existing managed tuner readiness path owns
pickup; this prompt neither launches a second context nor claims its Work.

## 2026-09-08 — integrator model decides permitted change scope

Confirmed owner decision, recorded by baton.prompt: Slawomir does not want to
spend substantial time on mechanical change-scope enforcement at this stage.
For W71830/W71879, rely on the integrator model to decide whether the whole
candidate falls within the permitted scope, using the accepted task/scope and
frozen independent review evidence already supplied to it.

This explicitly declines and supersedes the prompt's preceding proposal to
require a new deterministic file-and-operation allowlist before target writes.
No such mechanism, generalized semantic checker or additional enforcement
framework becomes a prerequisite of this demonstration. This also supersedes
any interpretation of W115604's placement research that such a mechanism must
be developed to close the milestone. Existing candidate identity, independent
review, target preflight and observed-result checks remain in force.

W115604 now only records this selected boundary and the smallest feasible
model-based refusal scenario using existing capabilities. The model receives
the whole candidate and permitted scope and is instructed to refuse before
importing a change it judges unauthorized. Retain the model decision and actual
target observations as evidence; do not claim mechanical prevention or a
universal guarantee from the model instruction. The already agreed successful
imports, independent review/correction and failure-containment objectives
remain. Do not fabricate acceptance or approved bytes for a negative fixture.
If the exact existing companion-refusal scenario cannot fit those objectives,
return that concrete acceptance conflict to the owner rather than designing a
new enforcement subsystem or silently expanding the proof.

## 2026-09-08 — multi-Job placement recommendation, W115599

Reviewer claim118998 confirms the current factory still has one worker per role
and one configured line while W103083 actively owns its one-Job assembly work.
review-2026-09-08T12-29-16Z.md recommends a separate successor provider under
W103068 after assembly acceptance, split into multi-worker configuration and
per-Job line/binding results. This is Proposed, awaiting owner placement; no
claim scope, live gate, runtime authority or proof requirement changed. The
companion-refusal decision remains separately tracked by W115604.

## 2026-09-08 — minimal companion evidence conflict, W115604

Reviewer claim119026 follows the selected integrator-model boundary in M119018;
no mechanical enforcement prerequisite is proposed. Current admission requires
genuine accepted evidence, while the known negative component fixture is
synthetic and deterministically refuses to held/import-incomplete. It cannot
silently stand for an automatically admitted independently approved live
companion. review-2026-09-08T12-33-00Z.md states that exact conflict and asks
whether the owner accepts the existing component refusal as separately labelled
evidence alongside the actual A/B/C demonstration. This is Proposed, not a
waiver or changed proof assertion. No live model/no-write guarantee is claimed;
successful imports and all other agreed objectives remain required.

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

## 2026-09-08 — approved companion evidence adjustment, M119128

**Confirmed owner ruling:** Slawomir approved the adjustment in the proof's
review-2026-09-08T12-33-00Z.md. The existing component refusal may serve as
separately labelled negative boundary evidence. This explicitly supersedes the
requirement for an automatically admitted, independently approved live negative
companion and any implication in earlier demonstration/acceptance paragraphs
that this fixture proves refusal before all canonical mutations. It also
supersedes the pending companion-placement/conflict status in the earlier
reviews, preflight and plan. Preserve those documents as historical evidence;
this is the current freeze interpretation.

Use the existing `test_an_unscheduled_existing_test_change_is_the_providers_to_refuse`
in `v12/python/tests/manager/test_integration_worker.py`, with the
`test_a_clean_provider_refusal_after_writable_work_is_still_held` control.
The derived bundle and deterministic refusing provider are labelled component
fixtures. They show the whole-candidate instruction, the measured selected
ending bytes and conservative held/import-incomplete outcome. They do not
show an automatically admitted independently approved live negative proposal,
live-model refusal, absence of intermediate writes or universal prevention.
Retain applicable accepted evidence and exact source/fixture identities at
freeze; rerun only if a named evidence gap or changed bytes require it.

The integrator model still judges permitted scope from the whole candidate,
accepted task/scope and frozen independent review. Actual candidate identity,
review correlation and target preflight remain required. Actual A/B successful
imports, independent review and same-line correction, fault-C containment,
required overlaps, one A/B/C submission and zero ordinary operator transitions
remain unchanged. C remains the deliberately exceptional Job, not a third
successful import. No fabricated approval, fourth Job, live negative companion,
new mechanical enforcement subsystem or new runtime grant is required by this
adjustment. Component evidence is reported separately from the live result.

## 2026-09-08 — placement gate verified, claim119493

**Confirmed:** owner M119490 installed the M119126 proof dependency.
Canonical details at snapshots119493/119495/119497 verify the final gate,
retained prerequisites and serial successor ownership. This explicitly
supersedes the unresolved route-authority status in
review-2026-09-08T13-22-47Z.md. Final placement review:
review-2026-09-08T13-31-47Z.md; exact observations are retained in
evidence/placement-119493-ledger.json. Lightweight W115599 placement is complete;
actual successor implementation and independent joined acceptance are still
required before freeze. No product acceptance or prerequisite was waived.

## 2026-09-11T00:40:24Z — owner acceptance applied

Owner M140286/M140288 in T133129 and baton:work/records/2026/09/finding-v12-standalone-multi-job-pipeline/FINDING.md / PLAN.md at 2026-09-11T00:30:54Z govern. This explicitly supersedes older mandatory, essential and no-waiver wording below ONLY where it makes stronger robustness/resilience demonstrations prerequisites. Ordinary correctness, authorization, honest evidence, existing source scopes, cumulative budgets and file ownership remain. Deferred claims are unproved, never passed. No new planning Work or approval round is required.

Freeze and execute the ordinary standalone A/B feasibility run through the existing handoff after accepted provider composition. Name exact candidate/base, A/B task contracts, actual runtime/provider profiles, commands, target/artifact roots and existing resource/time limits. Submit A and B through normal coordination and collect actual review/test authorization for the original submissions and separately merged result, both landed changes, original private bases and honest terminal evidence. Use required public status readers. No demo-only bypass, manual lifecycle/target repair, synthetic receipt/runtime/completion, or fixture-provider substitution.

Explicitly superseded: the older three-Job freeze, submit-all-three, deliberate fault-C containment, injected failure, companion-refusal and crash/restart/adversarial/race prerequisites. Do not add fault Job C to the immediate run or wait for its acceptance. Deliberate correction/failure exercises whose sole purpose is robustness are likewise deferred; normal review-requested correction, if it occurs, must still execute legitimately.

Indexed deferral C-1: real fault-Job containment and fault-capacity behavior, plus companion negative/refusal scenarios, remain unproved as standalone guarantees. Revisit after successful A/B feasibility when the owner schedules robustness/resilience; use retained component evidence only for its stated boundary. No new planning Work or approval round solely to narrow to A/B. A concrete defect blocking/falsifying ordinary A/B is returned to its owner and fixed, never patched around in the demo. Existing source scope and run budgets remain; actual standalone evidence has not yet been produced by R.

## 2026-09-11T04:02:49Z — tuner141510 preparation and deployment findings

**Confirmed:** owner pass141506 assigns actual proof preparation/execution to
baton.tuner and retains the targeted material-delta review through baton.feat
before execution, returning to baton.tune. The accepted provider handoff is
`../finding-standalone-stage-composition/CONSUMER-HANDOFF-2026-09-11T03-42-24Z.md`.
This supersedes the old missing-composition finding as an execution gate;
provider component acceptance is not actual proof acceptance.

**Observed operational inputs still missing:** the current managed process
does not hold dedicated workspace gid1001 (`baton-workspace`), although the
host group names user sl. DEPLOYMENT.md requires membership in the manager
process; login gid1000 is expressly not a substitute. No operator-prepared
W71879 Git baseline/target was located in the inspected v12 state roots or
fixture directory. The earlier preflight reserves preparation/commit to
Slawomir, consistent with AGENTS.md Git ownership. The selected older provider
image sha256:0697b6595aff0af2a39a81d492223bf33cf69877426ec859fe1abb90abd617e4
exists, but that observation does not bind current worker/integration source
bytes or supply an accepted current integration image. No image was built.
The credential registry and its referenced source are present with owner-only
modes; no credential payload was opened. These are deployment observations,
not a newly discovered composition defect.

**Observed policy boundary:** `docker ps` and exact `docker image inspect`
succeed; `docker image ls --format ...` was denied access to the Docker socket.
No escalation or broader-command retry was attempted. The deployment must
provide the intended execution boundary and outside-checkout writable roots;
this managed context currently has repository and /tmp write roots only.

**Open allocation locator:** pass141506 preserves W71879's existing allocation.
The proof records read here do not identify its numerical execution allowance
or a prior spending ledger. The old20-minute suggestion is explicitly a
proposal. W103068's numerical author/reviewer/reserve accounts belong to that
provider and cannot fund this run. Obtain the existing allowance's exact
locator/value and accumulated spend before freezing execution limits; this
does not request a new allocation or reset an old one.

**Preparation boundary:** create exact baseline payload and A/B task-contract
files in this dossier, without creating a Git repository or implementing either
requested feature. A replaces the specifically scheduled greeting expectation;
B adds its hours feature/test and one self-contained required-test script.
The latter is deliberate: the configured causal owner carries the named script
alone into the original base, so it must not depend on a newly added test module.
Use the existing supported stage dependency graph to propose both original
reviews before A integration, then B integration after A. This makes direct A
and derived B deterministic while allowing independent coding. These concrete
run choices await the already required material-delta review. They grant no
source changes, Git mutation, fake judgment, manual lifecycle repair, fault C,
or new hardening prerequisite.

## 2026-09-11T04:10:45Z — reviewer141577 confirms operational return

review-2026-09-11T04-10-45Z.md retains all13 prepared files without drift and confirms missing effective workspace gid1001 and absent nominated run root. Operator Git baseline/target and numerical preserved allocation remain unresolved. These are concrete deployment inputs, not a new provider defect or another planning Work. OPERATIONAL-HANDOFF-2026-09-11T04-10-45Z.md names the exact repair/output and returns execution to tuner after ops. The next tuner packaging embeds full task scope and limits model evidence claims to what the accepted judgment input actually delivers; original/derived authorization still must be retained and verified by their real owners. No final material-delta approval or actual run claim. Read-only validation0.00040272800106322393s plus prior tuner0.004338626000389922s and historical uncertainty retained; no tests or provider-budget transfer.

## 2026-09-11T04:20:37Z — prompt separates sandbox observation from host execution policy

Owner M141636 supplies the source/target under /home/sl/.local/state/baton/v12/w71879-run1,
baseline commit 2fbb2d456638e5706218020aebfa47f0a82c8920 and tree
3492ba64448ab9d39bde53ee6456ce24e74ece2c, and explicitly approves A/B wall20min,
implementation4min, original review/derived judge3min and integration2min limits.
This supersedes the missing baseline and unidentified numerical allocation above;
all preparation costs/uncertainty remain and provider reserves do not transfer.

Read-only inspection finds host app-server PID4666 and dispatcher PID7011 already
hold supplementary1001. The sandboxed shell's1000/65534 observation remains true,
but does not establish that a host-group repair or restart is necessary.
Installed default.rules:164 already allows the exact prefix
`/usr/bin/env PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src:. /usr/bin/python3 -m tools.job_manager`.
`codex execpolicy check` against installed default.rules and baton.rules returns
allow; that exact command with --help succeeds from v12/python. The policy check
warned that PATH aliases could not be created; its rule evaluation still succeeded.
No store, model, container or actual run was started; diagnostic elapsed cost is
not comprehensively measured and is not claimed zero.

This supersedes treating all manager commands as restricted to the sandbox.
It does not prove the final configured serve command or provisioning commands
are authorized: adding BATON_V12_STAGE_EXECUTION_CONFIG changes the matched prefix.
Current images, public Authority/config provisioning and their exact commands are
still needed. Proposed next owner disposition is to return existing packaging to
tuner, who identifies the exact missing command grants with reviewable artifacts;
do not request a blanket sandbox override, guess a host restart or infer approval
of a different command. M141636's execution hold remains until owner disposition.

## 2026-09-11T04:26:29Z — tuner141676 executable packaging boundary

**Confirmed:** return141673 authorizes completing deployment/provisioning
artifacts within current access and identifying exact missing grants before
execution. Source/target HEAD and baseline tree match M141636; target status
is clean. Installed default.rules164 grants the exact unconfigured Job Manager
prefix. It does not grant the stage-configuration environment prefix or an
arbitrary provisioning/build helper. Host-group repair is not inferred.

**Packaging choices for the existing delta review:** freeze local build contexts
over the selected historical provider base, recopy current worker/profile bytes,
and build one provider candidate plus the accepted integration recipe candidate.
No package reinstall, floating base, credential payload or fixture provider is
included. Candidate image IDs remain build outputs until independently reviewed
for selection. Generate full tasks, seven policy documents, manifests, five
stage deployments and three result-judge deployments, and provision fresh
Authority Works/grants through public APIs only. Embed complete A/B scope in
judge instructions and limit their evidence claims to the delivered candidate,
causal observations and policy; concurrent peer/original report bodies are not
assumed present. Preserve prepared141510 as history.

**Observed capacity:** Docker reports32 CPUs and32718819328 memory bytes;
the run-root filesystem has723990093824 available bytes at this observation.
Accepted OCI limits are2 CPUs,2GiB and512 pids per runtime. All eight configured
execution owners plus two helper slots conservatively fit20 CPUs/20GiB.
Propose512MiB declared workspace capacity per assignment and16GiB retained-run
storage stop threshold; capacity declaration is a free-space preflight, not a
filesystem quota. Scratch limits remain the accepted owner's constants.
The approved20/4/3/2-minute limits require an external run deadline observer:
provider code has longer fixed deadlines and these are not configurable in
single-worker/4. An exceeded proof limit stops the run exceptionally and retains
evidence; it never authorizes another attempt or a manual success transition.

**Additional operator Git operand:** the configured integration workspace must
be an existing private Git repository for the accepted prepare/fetch/merge
operations. The run root currently contains source and target only. Nominate
`/home/sl/.local/state/baton/v12/w71879-run1/integration-workspace` as a fresh
bare repository, prepared by Slawomir under existing Git ownership. Packaging
will refuse absence, not initialize or repair it. This supplies a concrete
existing provider operand, not a new protocol or planning prerequisite.

### Packaging result under claim141676

`PACKAGING-141676.md` and `prepared-141676/` now supply the concrete command
handoff. Public-schema/bootstrap validation passes for five Works, five stage
workers and three independent judge deployments. Temporary validation uses
explicit historical image values only and is not the run configuration.
Actual image build/selection and the final render remain behind the named
engine grant, with the existing material-delta acceptance before submission.
The exact build/provision/run helper commands and configured serve prefix have
no matching installed rule; the unconfigured Job Manager prefix matches allow.
This is a measured command-grant distinction, not a blanket host-access claim.
No host group repair, escalation, rule edit or alternate launcher was attempted.

The actual selected credential mapping is present in the registry metadata.
The shared provider installation/default-model behavior is explicit; the
factory's fixed provider-diverse label is not evidence of actual provider/model
diversity in this run. The external guard uses public assignment owners and
basic status, includes active derived judgments within the integration limit,
and retains exceptional stops rather than repairing outcomes. Its scripts and
all retained inputs receive independent review before any execution grant is
used. Exact preparation costs, corrected packaging errors and retained
temporary validation paths are in prepared-141676/spending.json. Prior
preparation costs and all provider reserves remain unchanged.

## 2026-09-11T04:51:36Z — independent command/scope acceptance, reviewer141816

review-2026-09-11T04-51-36Z.md accepts the exact prepared141676 package for operator command-grant disposition. Independent33-file hash/size/mode check,45-provider-entry continuity, earlier payload continuity and clean operator source/target identities pass; three helper ASTs parse. COMMAND-REVIEW-2026-09-11T04-51-36Z.md names the three exact helper invocations and effects. This supersedes pending command/scope review, not final material-delta/image selection or actual execution acceptance. Ops supplies exact grants and operator bare workspace; tuner builds/checks/renders, then existing independent review binds real images/configs before provisioning/run. No blanket grant, new planning Work or host restart. Review validation0.009054458001628518s and all prior measured/unmeasured spending preserved; no actual models/builds/containers/submission here.


## 2026-09-11T11:49Z — operator build complete; final freeze, claim144072

**Confirmed decision:** owner return144067 (2026-09-11T11:43:30Z) supplies the
bare integration workspace and successful execution of the reviewed
prepared141676 build helper. It explicitly directs reuse and validation of the
actual candidates, no rebuild, then final immutable configuration rendering and
the existing independent material-delta review. Supply exact remaining
provision/run commands or grants after that preparation. Actual submission stays
held until access and review are complete. This supersedes the current
build-grant/build-action premise in PLAN, not any execution limit or review gate.

**Revalidated:** evidence/freeze-144072/pre-render-validation.json records all33
reviewed package files, all45 accepted provider entries (43 present,2 absent),
and prior13 payload files unchanged. Both source and target are clean at the
owner baseline commit/tree, target main; integration workspace is bare. Actual
image IDs match retained IID/inspect/build outputs and live immutable image
metadata; all14 retained container-file checks match the reviewed context.
Operator build evidence records23 successful commands, two never-started
inspection containers removed by the reviewed helper, and0.3397777770005632s.
No model execution is inferred. Production Authority/Job/control stores and
selection/review markers are absent. The reviewed generator can now render
frozen-config inside the repository. Historical snapshots stay unchanged;
rendering is a candidate freeze pending independent image/config acceptance.

All numerical owner limits, cumulative costs/uncertainty, original/derived
authorization and both-landed/terminal proof obligations remain. Shared Claude
installation/default model makes no vendor/model-diversity claim. No product
source change, new Work, rebuild, provisioning or submission is authorized by
this freeze step alone.


## 2026-09-11T11:53Z — final candidate rendered; review/access remain

**Observed:** unchanged reviewed deployment.py render succeeds. The33 frozen
files bind actual candidate images; stage configuration SHA-256 is
747ae861826fa7993a847f610e98b83859b1b25db0b15f83ca2fb42cc2660976 and submission
SHA-256 is154cdee4547dd3e0fbde6021fecf1abdf91db4643ec71e84e18e577bee199287.
Cross-document pure validation passes. FREEZE-144072.md names the immutable79-file
candidate manifest, original review/provider chain, exact remaining commands,
real review-marker contract, limits, costs/uncertainty and remaining proof.
Installed rules still have no match for either exact provisioning/run command;
neither operation was attempted. Production roots/stores and selection/review
markers remain absent. The next action is the existing independent final
material-delta and image-selection review, followed by exact access disposition
and tuner execution. This is preparation evidence, not two-Job runtime proof.

## 2026-09-11T11:58:12Z — final image/configuration accepted, reviewer144132

review-2026-09-11T11-58-12Z.md selects actual providersha256:26cdfe7df693d3cfad0190e879e93ba9f3fea2086ecb5c7f1f4c2fe598aced99 and integrationsha256:8e84757c898b15b98fce42ca2d5a3a4ba07e44c0c744978870bdf36a4aa2cdb2, accepting the79-file candidatesha256:c10f798f017fd9b174bcb08cc555379e2afda52b40bcc486ef156664a56491fa. Independent hashes/schemas/bindings, live image metadata, retained14-byte checks and clean baseline/bare workspace pass. This supersedes pending final material-delta/image selection below; actual execution/result acceptance is still outstanding. Genuine review/selection marker documents live in evidence/review-144132/ for tuner materialization, with no additional approval required for unchanged bytes. EXECUTION-HANDOFF-2026-09-11T11-58-12Z.md sends existing Work to ops for the two remaining exact grants, then tuner public provisioning/run and independent result review. No rebuild/new planning Work. Measured review0.028188105003209785s, listed cumulative0.80724953001253s plus all historical uncertainty; provider reserves and1200/240/180/120 limits unchanged.


## 2026-09-11T12:07:44Z — prompt observation of operator run1 failure

Operator executed accepted provisioning and run.py under claim144179. The
operator output reports the accepted configuration/submission digests. Retained
/home/sl/.local/state/baton/v12/w71879-run1/evidence/run-result.json records
submitted=true, terminal_both=false, start12:02:28.168723Z and223.9077433210041s
wall including termination. This supersedes the unexecuted status above; it is
an unsuccessful actual run, not a passed proof or independent result review.

Observed in the174 retained samples: B implementation reaches completed around
42.45s and its runtime is destroyed; A implementation remains answering/quiescent,
B review remains answering/quiescent, both integrations stay blocked and derived
judges remain unclaimed. B review claimed at12:03:11.758Z; its180s deadline is
12:06:11.758Z, matching the timeout at about223.6s from submission start. The
1200s global limit was not exhausted. No increase in wall time follows this result.

A retained proposal/result.json reports provider-failed, api-error, status1,
no changed paths and no verification. B retained logs/review.json reports
api-error/status1, zero report bytes and no verdict. These are the supported
published provider classifications, not evidence identifying a specific upstream
HTTP/auth/rate-limit cause. B implementation's completion does not establish a
successful original review. serve.log records deferred conclude for A implementation
and B review: output is sealed while custody requires FROZEN. This is a separately
observed finalization refusal; root cause and relationship to failed-provider
output remain for independent diagnosis, not an inferred success-path redesign.

The run result records zero ordinary operator transitions and no exceptional
container stops. A read-only Docker query for this exact Authority label at
inspection found no running containers. All external state and failed-run evidence
remain intact; no retry, store repair, claim release or test execution was performed
by prompt. Diagnostic reads/parsing are unmeasured and retained as uncertainty.
Next proposed handoff is independent failed-run assessment and smallest concrete
provider/finalization diagnosis, preserving the happy-path goal and deferred
hardening. Any retry needs its own explicit disposition; no run1 overwrite.

## 2026-09-11T12:28:12Z — independent failed-run assessment — baton.codex

Review claim144288 completes assignment144282 in
`review-2026-09-11T12-28-12Z.md`, with hashed retained evidence,174-sample
transitions and a fresh supported status in `evidence/review-144288/`.
Actual A/B acceptance remains unsuccessful: A provider failed without a candidate,
B implementation completed, B provider review failed without a verdict, and
neither integration or derived judgment started. Both failures were already
quiescent in seconds; supported Docker State reads show no OOM kill and clean
adapter-container exits. Their provider status1 is a separate fact.

**Confirmed diagnostic limit:** the adapter intentionally discards provider
stdout after closed classification and discards stderr entirely. Retained
api-error does not establish an HTTP/auth/account/rate-limit/network cause.
No specific provider remedy can honestly be selected from this evidence.
Operator next action: obtain a provider-owned diagnostic through an existing
authorized account/service channel for12:02:29–12:02:36Z and12:03:11–12:03:17Z,
or report that channel's exact absence and supply a bounded supported diagnostic
action before further provider execution. This is a limit in the current
operational surface, not authority to invent a logging mode or run a model probe.

**Confirmed separate defect:** live ending re-entry calls intake again after
custody made output sealed; request_intake checks frozen before replay, masking
the original unable/held reason. W144335 is recorded at
`baton:work/records/2026/09/finding-v12-sealed-intake-reentry` and parked as
independent failure/re-entry hardening, without a W71830/W71879 gate or child.
Its bounded proposed receipt validation/re-entry fix does not make an unable
provider result a completed candidate or review. First-pass successful execution
remains the critical scope; all prior observation/fault-C/resilience deferrals
remain. The inferred first-pass refusal is labelled as inference in the review,
because only the last serve sweep survives.

This supersedes pending independent diagnostic assessment above, not the failed
run outcome, accepted image/config provenance or need for causal provider evidence.
Pass this existing Work to ops, Next tuner. Preserve run1 and its223.9077433210041s
cost, original1200/240/180/120s limits and all billing/elapsed uncertainty.
Review hashing/parsing0.015611637994879857s makes listed preparation/validation
0.8228611680074099s, separately from run wall time; untimed diagnostic/source/
document work is additional. No new tests, model calls, source/test edits,
runtime actions, store repair, retry, rebuild or budget transfer occurred.


## 2026-09-11T12:44Z — one fresh run2 authorized, tuner claim144415

**Confirmed owner disposition:** return144411 (2026-09-11T12:41:57Z)
incorporates M144306: host Claude OAuth had expired, the operator completed
login, and the same host check returned pong. The configured
operator-file/w64268-run1 source points to /home/sl/.claude/.credentials.json.
This establishes restored host authentication, not the causal explanation of
run1 api-error or refreshed credentials in existing attempts. The owner accepts
that remaining uncertainty and explicitly authorizes one fresh A/B run2 with
1200/240/180/120-second limits and no automatic further retry.

This supersedes the prior requirement to establish the exact run1 provider
cause before any further execution and the prior no-retry disposition only to
the extent of this one fresh run2. Run1 remains failed and immutable evidence;
it must not be rerun, repaired or overwritten. Its 223.9077433210041 seconds and
all preparation costs, unknown provider billing and diagnostic uncertainty stay
spent. W144335 and other hardening remain parked, with no new prerequisite.

**Current authorized implementation:** prepare a separate prepared-144415
package and /home/sl/.local/state/baton/v12/w71879-run2 namespace, fresh Authority
UUID c71879ac000000000000000000000001, principals/scope/profile/incarnation and
credential delivery homes. Reuse unchanged independently accepted provider and
integration images and task behavior, keeping original commit
2fbb2d456638e5706218020aebfa47f0a82c8920 and private original bases. Use the same
configured source for fresh ordinary credential delivery; never copy failed
attempt credentials or inspect their payloads. Existing material-delta review
must bind changed executable inputs before this new run. Supply exact operator
shell commands for fresh Git roots and required host execution access; agents
still do not mutate Git. Public provisioning and the normal one-submit/serve
path must drive original reviews, both integrations and actual derived judgments,
followed by independent retained-evidence assessment. No rebuild, model probe,
timeout increase, success repair or product source correction is assigned.

**Revalidated preparation inputs:** run2 root is absent; registry metadata still
maps the named configured source to the operator's refreshed host path. Source
payload contents are not read as part of that metadata observation. Existing
image/config acceptance is review-2026-09-11T11-58-12Z.md; independent failed-run
assessment is review-2026-09-11T12-28-12Z.md. Neither is represented as run2
configuration acceptance or proof of future provider success.
