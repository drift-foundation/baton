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


## 2026-09-11T12:51Z — run2 source nomination requires operator Git roots

**Observed:** prepared-144415 adapts only run identities/declaration provenance
from the accepted helpers. Original 79-file package and 45-entry provider chain
match; five task behaviors and all limits are unchanged. Static helper/task/policy
checks pass. The ordinary validator refuses absent run2/source before writing
successful validation/configuration evidence. Its temporary public Authority and
partial documents remain at /tmp/w71879-144415-validation-yywyz7p8. No product
failure, model call or production state is inferred from this preparation refusal.

RUN2-PREPARATION-144415.md and the new 25-file preparation manifest provide exact
operator-only Git preparation plus the subsequent validate/render/provision/run
commands. Final rendering/material-delta review remains pending actual nominated
Git roots; no validator bypass or source substitution was made. Under AGENTS Git
ownership, Slawomir must execute the provided fresh clone/bare-workspace script.
After that same-Work handoff tuner resumes the already authorized run2 preparation.
The exact later provision/run commands have no installed rule match. Keep run1,
all spending/uncertainty and the one-run2 limit; W144335 and all hardening remain
parked. No new causal-diagnosis gate or repeat run authorization is requested.


### Concurrent UX decision acknowledged

Before releasing claim144415, read
UX-DECISION-2026-09-11T12-44-51Z.md from baton.prompt. The confirmed actionable
authentication-failure UX requirement is deferred, separately from W144335,
and explicitly leaves authorized run2 preparation unchanged. No additional
source/test change, model probe or retry is performed or made a prerequisite.

## 2026-09-11T12:52:46Z — run2 operator command independently reviewed

baton.codex claim144468 accepts the concrete operator preparation handoff in
review-2026-09-11T12-52-46Z.md. Independent25-file hash/size/mode checks, exact
helper substitutions, five task/seven policy continuity, shell syntax and clean
original source identity pass; evidence/review-144468/result.json records them.
Run2 is still absent, matching the retained source-nomination refusal. No
validator bypass or execution-success inference. This supersedes pending
independent review of the incomplete-preparation return, not final run2 rendering
or material-delta acceptance.

Pass the existing Work to ops, Next tuner: Slawomir executes the exact reviewed
operator-prepare.sh in RUN2-PREPARATION-144415.md, then tuner resumes actual-root
validate/render and existing final review. This creates the missing real Git
operands for ordinary A/B execution and both terminal integrations; it is not
another run authorization or causal-diagnosis gate. Owner return144411 persists.
W144335, authentication UX and all other hardening remain deferred.
Review checks0.006661940002231859s make listed preparation1.0196849790054526s,
plus all prior/current untimed uncertainty; run1 wall223.9077433210041s remains
spent separately. No run2 model/submission, source/test/Git change or budget
transfer. Preserve all existing limits and no automatic further retry.


## 2026-09-11T13:05:29Z — operator run2 roots supplied; freeze resumes, tuner144546

**Confirmed:** owner return144544 reports the reviewed operator-prepare.sh
completed successfully and directs validation/rendering, existing final
material-delta review and the already authorized single run2. Read current
review-2026-09-11T12-52-46Z.md and complete canonical handoffs/thread.
This supersedes the absent-run2-source prerequisite and pending operator Git
action above; it does not waive final configuration review or host execution
access. No operator Git action is to be repeated.

**Revalidated:** evidence/run2-freeze-144546/pre-render.json records both actual
run2 clones clean on main at the unchanged original commit/tree with all ten
baseline payload files matching, and a bare integration workspace. The reviewed
25-file preparation, prior accepted 79-file package and 45-entry provider chain
match. Production run2 roots/stores, validation/final configuration and actual
review markers are absent. Proceed with the unchanged reviewed validate/render
helpers, keeping immutable record snapshots, images, tasks and numerical limits.
Run1 evidence/costs and all diagnostic uncertainty remain; one-run2 permission
persists and W144335/authentication UX/other hardening remain deferred.


## 2026-09-11T13:09:37Z — final run2 candidate ready for material-delta review

The unchanged reviewed helpers now validate and render successfully against
actual run2 roots. RUN2-FREEZE-144546.md binds the 159-file candidate manifest
SHA-256 e681e9501b8221fbc791de7b2f8ef12ad6ba11f12b045717c7e186ce8e362330,
including 33 final documents, unchanged preparation/old provenance and required
baseline/task payload. Final configuration SHA-256 is
7081a6fe3e54563393ecb149f4b398a9cb1c918f2871f400fde3dbf267c1522f; submission is
4b010820657b031ec222dd5825ff698b688da6266bc811c6f7b6143919a26694.
Cross-document schemas, identities, task/policy bindings, limits and live image
metadata pass. No helper, image or product source change was needed this claim.

This supersedes pending validate/render status above. The next action is the
existing final run2 material-delta review, then exact host access and normal
public provisioning/one run. Both exact provision/run commands remain unmatched
by installed grants; production run2 state and genuine review markers are absent.
The successful temporary validation path and earlier failed path are retained.
Run1 wall cost stays 223.9077433210041 seconds; listed preparation including this
claim is 1.1195892509876832 seconds plus all untimed/billing uncertainty. Limits,
no automatic further retry and all hardening deferrals remain unchanged.

## 2026-09-11T13:14:10Z — final run2 material-delta accepted — baton.codex

Review claim144585 accepts the159-file candidate in
review-2026-09-11T13-14-10Z.md, manifest
sha256:e681e9501b8221fbc791de7b2f8ef12ad6ba11f12b045717c7e186ce8e362330.
Independent candidate/provider continuity, all33 final documents, ordinary
schemas, fresh identity/principal bindings, clean baseline payloads/bare workspace
and live immutable image metadata pass; evidence/review-144585/ retains results.
This supersedes pending final run2 material-delta review above, not the unexecuted
state or actual result acceptance. No further image/design/run permission gate.

Genuine selected-images/execution-review markers are retained in that evidence
folder and materialized unchanged at prepared-144415/. The review binds both
helpers, both exact final document hashes and all159 files plus their manifest.
RUN2-EXECUTION-HANDOFF-2026-09-11T13-14-10Z.md gives the two remaining exact host
commands. Pass existing Work to ops, Next tuner, for exact access or operator
execution of public provisioning then one run2. Operator Git preparation is
complete and must not repeat. This advances ordinary fresh A/B execution through
both integrations and actual derived judgments, followed by independent terminal
evidence assessment. Owner144411/144544 persists; preserve failed run1 and all
hardening deferrals, including W144335/authentication UX/observation/fault-C.

Checks0.03381236300629098s plus two reviewer comparison errors0.062595478s
make listed preparation1.215997091993974s. Those errors were digest-domain/
normalization mistakes in the reviewer harness, corrected without candidate
changes. Run1 wall223.9077433210041s remains separate and spent; all imports,
reads, marker/document work and historical/operator/billing uncertainty remain
additional. No model, suite, production state/runtime, product/test/PROGRESS/Git
change or provider-budget transfer. Preserve1200/240/180/120s and all bounds;
no automatic further retry, manual repair or invented success evidence.

## 2026-09-11T13:51:50Z — run2 launch failure assessed — baton.codex

Owner144774 and review-2026-09-11T13-51-50Z.md supersede the unexecuted run2
status: submitted run2 stopped after300.8523036100087s, both implementations and
original reviews completed, but A integration stayed claimed/not-started until
its120s deadline. B integration remained blocked, no derived judge ran, and the
clean target still has the original baseline. No landed/terminal proof.
Hashed evidence,170 sample transitions, current public status and target metadata
are retained in evidence/review-144777/; no running labelled containers observed.

**Confirmed provisioning defect:** target and Git metadata have gid1000 while
the unchanged integration mount owner requires1001. The reviewed operator clone
script and deployment preflight omitted that target requirement; prior reviewer
readiness acceptance missed it. Source orders launch materialization/bundle before
target-posture validation, explaining the retained partial launch. The first
specific target-posture refusal is strongly inferred, not a preserved original
trace; the final repeated existing-root refusal is observed. The review records
the supplemental managed public-owner probe failure and successful supported
Job Manager status separately, without claiming direct live-boundary reproduction.

Smallest proposed correction: a fresh immutable preparation candidate with
operator-created target gid1001, setgid/group access and explicit umask, plus
read-only target/Git/affected-file posture checks before submission. Preserve
production authorization checks, original bases and both failed runs. No live
permission repair, root deletion, timeout increase or further model retry.
Pass same Work to ops, Next tuner, for bounded preparation correction and exact
continuation disposition. No new planning prerequisite. W144813 records and
parks secondary integration-launch refusal/re-entry hardening outside this proof;
W144335 and other deferrals remain. This is not a provider/authentication defect.

Run1+run2 wall524.7600469310128s stays spent separately. Added diagnosis checks
0.026215132005745545s and failed public probe0.021988386s make listed preparation/
diagnosis1.2642006099997195s plus all historical/current untimed and billing
uncertainty. No source/test/PROGRESS/Git/runtime/store change or budget transfer.


## 2026-09-11T14:02:26Z — bounded target preparation correction, tuner144859

**Accepted scope:** owner return144855 accepts review-2026-09-11T13-51-50Z.md
and assigns a new immutable helper/command candidate for a future fresh target:
gid1001, group write/traversal, setgid inheritance and explicit umask0002;
read-only target/Git/affected-file checks before submission, with focused
wrong-group refusal and compatible-target validation. Preserve both failed runs
and prior packages, images/task behavior and limits. No live-root repair,
deletion, protocol relaxation or another model run. Independent correction
review precedes operator disposition; W144813/W144335/authentication UX and
other hardening remain deferred. This supersedes proposed correction status,
not either failed proof outcome or the further-run authorization hold.

**Confirmed by current source:** integration/oci_delivery.py:prove_target_posture
requires target gid and group write/traversal. Additionally, the unchanged
v12/worker/integration_workload.py:_owner_writable requires uid equal to the
runtime effective uid and owner write on affected existing files and parents.
Its preflight compares Git100644 to exact0644. Dockerfile.integration fixes
uid65532. A group1001 clone with operator-owned mode0664 affected files would
therefore still be incompatible. These are existing product checks, not new
policy or claims about the unretained first run2 error.

**Candidate preparation decision:** bind a future, absent w71879-run3 root in
prepared-144859, with the same baseline and images/task behavior. The operator
script creates only this new root, creates target gid1001/setgid before cloning
under umask0002, initializes affected existing file modes to0644, then assigns
this newly cloned target to65532:1001. This is initial provisioning of a fresh
candidate, never a permission change to run1/run2 or an existing run root.
The host remains its existing uid and uses an exact-target safe.directory Git
setting scoped to the helper process, because target ownership belongs to the
fixed container uid; no global Git trust or runtime identity substitution.
These extra ownership/mode/trust operands are explicitly part of the proposed
correction candidate for independent review and operator disposition.

A read-only preparation helper will check target root, traversed directories,
Git metadata, and all five permitted task paths, requiring actual owner/mode
semantics above and rejecting links/special files. It runs at baseline preflight,
before provisioning or submission, and remains additional to the production
integration/worker checks. Its compatible filesystem regression may use the
managed test uid/gid as explicit fixture parameters; production CLI defaults
stay65532/1001. No managed process can claim a real65532/1001 host fixture or
new model result before the operator supplies it. All test fixture creation
stays inside a new retained temporary directory, with no Git mutation.


## 2026-09-11T14:13:25Z — correction candidate and focused validation complete

TARGET-PREPARATION-CORRECTION-144859.md binds the new 25-file candidate manifest
SHA-256 6b4121c4f36c3b881e4fd2d8edcc09ac358c6c28b5b98b787c1a7f1185aa9b33.
The operator script prepares only a fresh target with gid1001/setgid/umask0002,
initial uid65532 ownership and affected-file0644 modes required by unchanged
worker code. Host Git trust is process-local to that exact target; no global
config or protocol relaxation. Target/Git/affected-path preflight runs before
preparation/provision/submission writes, and the new helper is included in the
runner's mandatory review bindings. Existing source checks remain authoritative.

Ten focused tests pass, including wrong-group refusal before Git/Authority/submit
and compatible real-file fixtures with explicit managed uid/gid parameters.
This is not actual fixed-uid host target/kernel/Git validation; the operator's
future preparation ends with the production65532/1001 check. A read-only call
also confirms run2/target's current gid1000 refusal without changing metadata;
it does not retroactively recover the first runtime refusal. All159 accepted
run2 candidate files/provider45 entries, images and task behavior remain intact.

No future model run is authorized or executed; no production/root/credential/Git
mutation occurred. All new tests are additive helper tests within owner144855
scope. Preserve both failed runs, 524.7600469310128s spent runtime wall and listed
preparation/diagnosis1.4785027580024397s plus all untimed/billing uncertainty.
Pass the completed correction candidate for independent review, then operator
disposition; do not turn correction acceptance into another run authorization.


## 2026-09-11T14:18:17Z — preparation correction independently accepted — baton.codex

Review review-2026-09-11T14-18-17Z.md accepts the exact25-file prepared-144859 candidate for operator
disposition, superseding pending correction review. Manifest
6b4121c4f36c3b881e4fd2d8edcc09ac358c6c28b5b98b787c1a7f1185aa9b33
and prior159-file package checks pass; ten focused helper tests pass independently
without changing candidate evidence. New test expectations retain genuine access
refusals. Fresh initial65532:1001 ownership, affected0644 modes, gid1001/setgid/
umask0002 and process-local exact-target Git trust agree with current source.
Actual fixed-uid target/kernel/Git behavior remains for operator preparation;
the future root is absent and neither failed run was changed.

Pass existing Work to ops, Next tuner, using the exact script/continuation in
TARGET-PREPARATION-CORRECTION-144859.md. Operator creates/checks fresh operands,
tuner validates/renders, existing final review binds concrete execution inputs,
and owner must explicitly authorize any further model run. No new planning
gate, live repair, deletion, deadline increase or execution marker. Genuine A/B
integration/derived judgments/terminal results remain outstanding; all hardening
deferrals persist. Evidence: evidence/review-144952/. Runtime wall remains
524.7600469310128s; listed preparation now1.6266462880108228s plus untimed/billing
uncertainty. No provider reserve transfer or product/test/PROGRESS/Git changes.


## 2026-09-11T14:25:11Z — actual fresh operands supplied, tuner145012

Owner return144993 accepts review144952, including fresh uid65532/gid1001,
required modes and process-local exact-target Git trust, and reports that the
reviewed operator-prepare.sh completed with its final production posture check.
This explicitly supersedes the absent-future-root/operator-preparation step above.
Current authorized work is actual-root validation and final rendering using the
unchanged prepared-144859 helpers, then the existing independent material-delta
review and corrected execution package with exact host commands. Another model
run remains unauthorized; neither correction review nor successful preparation
removes that owner hold. Preserve run1/run2, all immutable packages, limits,
failed runtime524.7600469310128s, listed preparation1.6266462880108228s plus
uncertainty and all recorded hardening deferrals. No source or test change is
scheduled in this rendering claim; no repeated Git preparation or live repair.


## 2026-09-11T14:28:38Z — managed ID projection blocks actual-root validation, tuner145012

The read-only preflight and exact target_posture.py command refuse observed
target gid65534 instead of1001. /proc/self uid_map/gid_map represent only1000;
target uid/gid both appear65534, with reviewed2775/0644 modes visible. This is
a managed identity-visibility limitation, not proof of host misconfiguration;
owner144993 reports the actual host check passed. That preparation remains
accepted. The expectation that this managed boundary could immediately validate
and render is explicitly superseded by this observed operational finding.

RUN3-HOST-VALIDATION-145012.md supplies exact reviewed validate/render host
commands, both with no matching installed rule. No helper relaxation, ownership
repair, Git action or alternative runtime is proposed. All25 correction candidate
files,159 prior package files and four source requirements still match. No final
configuration/review marker, production state or model run exists. Return
incomplete freeze through baton.bug, Next baton.ops, for exact host preparation
execution or access; then tuner completes final binding and existing independent
material-delta review. Another model run remains unauthorized. Evidence and
costs: evidence/run3-freeze-145012/. Listed preparation1.663012100016991s plus uncertainty;
failed runtime524.7600469310128s and all limits/deferrals remain unchanged.


## 2026-09-11T14:31:00Z — host validation handoff independently confirmed — baton.codex

review-2026-09-11T14-31-00Z.md confirms the managed projection/refusal with unchanged metadata and
unchanged25-file correction/159-file prior candidates. This supersedes pending
baton.bug triage, not owner144993 successful host preparation or correction
acceptance. Actual host ownership cannot be inferred from projected65534 IDs.
No final config or acceptance markers exist. evidence/review-145044/ retains
independent checks. Pass same Work to ops, Next tuner, for the exact host
validate/render commands in RUN3-HOST-VALIDATION-145012.md, then actual final
binding/material-delta review. No target repair, repeated Git preparation,
helper weakening, new candidate/planning gate or model-run authorization.
Both A/B terminal results remain outstanding; all hardening deferrals persist.
Failed wall524.7600469310128s remains spent; listed preparation now1.6680928130198172s
plus untimed/operator/billing uncertainty, without reserve transfer.


## 2026-09-11T14:33:59Z — host validation and rendering supplied, tuner145070

Owner return145067 reports both reviewed host deployment.py validate and render
succeeded. Retain prepared-144859/validation.json and frozen-config as host
outputs; bind concrete run3 inputs and complete the existing final material-delta
review. This explicitly supersedes the missing host validate/render action in
review145044 and the prior operational return. The managed ID projection remains
a disclosed execution-boundary limitation, not a reason to repeat or weaken the
host check. No helper changes, repeat Git preparation or model run are scheduled.
Another model run remains unauthorized pending the reviewed package; accepted
preparation, both failed runs, all limits/costs and hardening deferrals persist.


## 2026-09-11T14:37:43Z — actual run3 configuration bound for final review, tuner145070

RUN3-FREEZE-145070.md and evidence/run3-freeze-145070/candidate-manifest.json
bind229 files, manifestsha256:9c2a40cd84df9bad831c4056f46237d94cb69021bb441f80987c6acbf68711cd. All33 host-rendered
files match deterministic reviewed-helper reconstruction after destination-path
substitution; ordinary schemas pass. All25 correction files,159 prior files,
45 provider entries and four source requirements match. Live immutable image
metadata and supplemental clean original source/target baseline checks pass.
Host65532:1001 posture remains operator evidence, distinguished from managed
projected IDs; no gate was bypassed or helper changed.

The material delta is host validation and exact final rendered inputs. Existing
final independent review through baton.feat is next, then baton.ops receives the
concrete provision/run commands. Both exact commands have no installed rule
match. Genuine final review/markers, real host access and explicit owner model-run
authorization remain; owner145067 does not authorize a run. No production state,
model, source/test/helper/Git mutation or failed-run repair occurred. Preserve
524.7600469310128s failed wall and listed preparation1.8694361010246812s plus uncertainty,
all numerical/resource/storage limits and all hardening deferrals.


## 2026-09-11T14:42:01Z — final run3 package independently accepted — baton.codex

review-2026-09-11T14-42-01Z.md accepts all229 candidate files plus manifest, all33 reconstructed host
documents,45 provider entries/four source requirements, live image metadata and
supplemental clean baseline. This supersedes pending final material-delta review;
host ID-visibility limits remain disclosed. Genuine selected-images/execution-review
markers now bind this review and230 paths including all three helpers, retained in
evidence/review-145102/. No future model run is authorized by package acceptance.
Owner145067 hold persists until explicit disposition on this concrete package.

Pass same Work to ops, Next tuner, with exact provision/run commands in this
review and RUN3-FREEZE-145070.md. No repeated preparation/render/rebuild or new
planning gate. Appropriate host access and owner authorization precede ordinary
A/B execution, actual original/derived judgments, both integrations and terminal
proof. Preserve both failures, all limits/deferrals and failed wall524.7600469310128s.
Listed preparation now2.0333831210272058s plus all untimed/billing uncertainty; no provider
reserve transfer, model/runtime, source/test/PROGRESS/Git or production mutation.


## 2026-09-11T14:52:15Z — run3 failed on unavailable stats; runner defect — baton.codex

M145141 authorized exactly one run3 and superseded145067 hold for that attempt
only. Owner145162 reports its failure; review-2026-09-11T14-52-15Z.md independently confirms both
implementations completed, A review offered/B review queued, both integrations
blocked and no reviews/judges/terminal proof. Source/target remain clean original
base;230 execution bindings unchanged. Run3 spent35.340723676010384s.

**Confirmed:** strict command() promotes Docker stats nonzero EOF into fatal
runner containment before persisting that iteration. A deterministic offline
reproduction verifies classification; the completion/destruction race causing
EOF is merely plausible, not established. Twelve surviving samples and current
public status remain distinct. Producer provider0/verification0 are not review
acceptance. The earlier readiness conclusion is superseded; input provenance
stands. Missing metrics must not mean zero usage or terminal success.

**Proposed smallest correction:** STATS-OBSERVATION-CORRECTION-145165.md isolates one bounded stats call,
records unavailable outcomes and surrounding sample data, preserves Docker caps,
strict required observations, storage/absolute deadlines and honest gap reporting.
Do not catch built-in alarm TimeoutError through OSError/Exception. New immutable
helper/test candidate only after owner disposition, same existing handoff through
ops Next tuner; no product/protocol change, run3 repair, broader monitoring gate
or new model retry. No Work prerequisite added; this dossier owns the defect.
All three failed runs stay intact. Runtime wall560.1007706070232s; listed preparation
2.1643190810253747s plus untimed/operator/billing uncertainty. All limits/deferrals persist.


## 2026-09-11T15:06:04Z — bounded stats correction accepted, tuner145261

Owner145258 accepts STATS-OBSERVATION-CORRECTION-145165.md: new immutable
runner candidate and focused offline tests. Stats nonzero/empty output and
subprocess.TimeoutExpired become explicit unavailable observations, retaining
bounded raw/partial output, timing, requested IDs, errors and gaps; surrounding
samples are flushed. Built-in watchdog TimeoutError must remain fatal. Required
status/inspect/label/storage checks, enforced caps, deadlines and all terminal/
final verification gates remain unchanged. No retries, fabricated measurements,
new model attempt, live repair, deadline increase or broader monitoring scope.
This supersedes proposed correction status, not any failed run or proof outcome.

Revalidated current runner: strict stats command precedes sample persistence;
it does not enforce resource thresholds. All229 prior package files still match.
Candidate prepared-145261 will contain the bounded runner change and new
test_stats_observation.py. Fresh packaging operands are separately mechanical:
w71879-run4 root (currently absent), UUID c71879ae000000000000000000000001,
matching Works/principals/scope/profile/incarnation and record snapshots/ruling.
Reuse reviewed deployment/posture/operator preparation logic, images and task
behavior; no fresh root is created by this claim. The exact operator preparation,
host validate/render and held provision/run commands accompany the candidate.
These operands do not authorize another run or reuse submitted run3 state.
Offline tests use mocked process/clock/Authority responses and retained temporary
files only, never live evidence, review markers, Docker or lifecycle mutations.
The additive test path above is owned by tuner under this claim and accepted
W71830 scope; existing tests and prior packages remain unchanged.
