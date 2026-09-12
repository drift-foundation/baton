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


## 2026-09-11T15:12:39Z — stats correction candidate complete, tuner145261

STATS-CORRECTION-CANDIDATE-145261.md and prepared-145261/candidate-manifest.json
bind25 files, manifestsha256:7a3987abd1703a0de20db1c46f7d995d65c3d8182fafd53295c49f13e8f18b5c. The runner isolates one
bounded stats call, records unavailable/available/not-requested with partial
text/timing/IDs/errors/truncation, flushes surrounding evidence and indexes gaps
in final output. Only subprocess.TimeoutExpired is caught; the actual watchdog
handler remains fatal. All strict required-observation/resource/storage/deadline
and terminal/final-check gates remain. No retry or fabricated measurement.

All17 focused offline tests pass, including flushed EOF continuation, actual
watchdog containment and required failure/final-verification refusal. The new
test is additive under accepted scope; no existing test changes. Fresh run4
identity operands and exact operator/host commands are separately enumerated;
no future roots/configuration/markers or model run exist. All229 old candidate
files/230 execution bindings and45 provider entries match. No product source,
Git, image, failed-run or live-state mutation occurred.

Pass completed correction to independent baton.feat review, Next baton.ops.
Owner145258 does not authorize another attempt; final actual inputs/review and
explicit owner run disposition remain. Preserve all three failed wall
560.1007706070232s, listed preparation2.3595462350280596s plus uncertainty, all existing
limits and hardening deferrals. Actual original/derived/landed/terminal proof
remains outstanding; no new planning prerequisite or reserve transfer.


## 2026-09-11T15:16:13Z — bounded stats correction independently accepted — baton.codex

review-2026-09-11T15-16-13Z.md accepts prepared-145261, manifest
7a3987abd1703a0de20db1c46f7d995d65c3d8182fafd53295c49f13e8f18b5c,
superseding pending correction review. All25 files and prior229/230 bindings plus
45 provider entries match;17 offline tests pass independently. Stats gaps persist
and flush while watchdog/required-observation/resource/terminal guards remain.
The additive test's changed behavior matches owner145258; no existing test edit.
Mechanical run4 packaging and unchanged posture/operator logic are accepted for
concrete operator disposition, not actual model-run permission or final inputs.

Pass same Work to ops, Next tuner, with exact commands in
STATS-CORRECTION-CANDIDATE-145261.md. No root/config/acceptance marker exists;
operator fresh preparation and host validate/render then existing final review
remain. Another model attempt requires explicit owner authorization. Preserve all
three failed runs, all limits/deferrals and runtime560.1007706070232s. Listed
preparation now2.521937728037696s plus untimed/operator/billing uncertainty; no reserve
transfer. Evidence: evidence/review-145312/. Actual A/B terminal proof remains.


## 2026-09-11T15:25:58Z — run4 timestamp packaging defect confirmed — baton.codex

Owner145370 reports failed host validation and dependent render. review-2026-09-11T15-25-58Z.md
confirms actual frozen schema rejects CREATED2026-09-11T15:06:04Z and accepts
2026-09-11T15:06:04.000Z. Actual constructor with test-local correction emits33
valid documents/six manifests; these offline fixtures are not final run inputs.
Earlier review145312 missed schema validation of this mechanical timestamp
change; its packaging readiness conclusion is superseded, stats acceptance and
candidate provenance retained. No fourth model attempt happened.

Owner already authorizes smallest reviewed correction and real-schema tests.
TIMESTAMP-CORRECTION-145373.md sends existing Work directly to tuner, Next feat, for a new immutable
candidate with only timestamp correction plus bounded regression/provenance.
Reuse prepared unsubmitted run4 identities/roots. Preserve old package and
/tmp/w71879-145261-validation-00nb1okq; no Git preparation, root repair, namespace
replacement, schema relaxation or model run. Exact corrected validate/render
commands are part of that concrete candidate handoff. All deferrals/limits hold.
Evidence: evidence/review-145373/. Failed runtime wall560.1007706070232s remains;
listed preparation2.670276407029118s plus untimed/failed host/operator/billing uncertainty.


## 2026-09-11T15:28:01.372Z — exact timestamp correction pinned, tuner145397

Owner145370 and review145373 authorize the new immutable prepared-145397
candidate: change only deployment.CREATED from2026-09-11T15:06:04Z to
2026-09-11T15:06:04.000Z, preserving the instant and all run4 operands.
The missing fractional digits were introduced by tuner145261; syntax and stats
tests did not exercise the actual manifest schema. This implementation adds
prepared-145397/test_manifest_timestamp.py through the real documents/input
manifest/check_manifest_structure paths, with six emitted manifests and the
old invalid value as a negative case. No validator stubbing or regex substitute.
The additive test and copied unchanged stats test are tuner-owned within this
claim; no prior test assertion is changed. Existing candidate history remains
untouched. All25 prepared-145261 files revalidate.

Copy required unchanged helper/input dependencies and bind their provenance.
Do not execute copied operator-prepare.sh: run4 Git/ownership preparation is
already complete. No new namespace, root repair/deletion, model attempt, schema
relaxation or broader change. Offline fixture outputs remain test evidence, not
real host validation/rendering. The exact new-candidate host validate/render
commands follow independent correction review; managed ID projection still
cannot establish host posture. Preserve failed temporary validation, all three
failed runs/costs, numerical limits and hardening deferrals.


## 2026-09-11T15:31:10.186Z — timestamp candidate and real-schema tests complete, tuner145397

TIMESTAMP-CANDIDATE-145397.md and prepared-145397/candidate-manifest.json
bind27 files, manifestsha256:46ac9d39fdb0e49728835696f04efd2d784f606b13982789b4406443aba4ad78. The only helper delta
is CREATED2026-09-11T15:06:04.000Z;20 copied dependencies are byte-identical.
All old25 candidate files and45 provider entries match. No run4 identity/root/
base/task/image/stats/posture/budget change or prior package mutation.

All20 offline tests pass: three actual documents/frozen-manifest regressions
including six valid emitted manifests and rejection of the original value, plus
17 unchanged stats tests. Fixture outputs are labelled synthetic constructor
evidence, never actual host validation or production Authority observations.
Exact corrected host validate/render commands and preserved failed temporary
path are in the handoff. Independent correction review through baton.feat is
next, then ops host outputs and existing final-input review. No repeated Git/
ownership preparation, new namespace, schema relaxation or model attempt.

Preserve all three failed runtime560.1007706070232s and listed preparation
2.872410018033801s plus untimed/failed-host/operator/billing uncertainty, all limits
and deferrals. Actual A/B terminal acceptance remains outstanding.


## 2026-09-11T15:33:58Z — timestamp correction independently accepted — baton.codex

review-2026-09-11T15-33-58Z.md accepts prepared-145397 manifest
46ac9d39fdb0e49728835696f04efd2d784f606b13982789b4406443aba4ad78,
superseding pending correction review. All27 candidate files/25 prior files and
45 provider entries match;20 offline tests pass. Twenty dependencies identical;
only deployment.CREATED gains required .000. Real schema tests cover33 documents,
six valid manifests and old-value rejection; no assertion/schema weakening.
Evidence: evidence/review-145429/. These fixtures are not host validation outputs.

Pass existing Work to ops, Next tuner, with exact corrected host validate then
render commands in this review and TIMESTAMP-CANDIDATE-145397.md. Reuse prepared
unsubmitted run4 roots; no Git preparation, namespace replacement, live repair
or model attempt. Preserve failed temporary validation and prior packages.
Actual host outputs/final-input review/explicit owner run authorization remain.
Three failed walls560.1007706070232s and listed preparation3.0692377850286303s plus all
untimed/failed-host/operator/billing uncertainty remain; all limits/deferrals hold.


## 2026-09-11T15:37:07.843Z — actual corrected host run4 inputs supplied, tuner145461

Owner145458 reports prepared-145397 host validate/render both succeeded and
assigns actual-input binding and existing final material-delta review, with exact
execution commands. This supersedes pending host output actions above, not the
hold on another model run. Preserve successful outputs as host evidence and the
failed /tmp/w71879-145261-validation-00nb1okq separately. No helper, test or source
change is scheduled; no repeated Git preparation/validation/rendering is needed.

Owner145458 reiterates parent FINDING ruling2026-09-11T15:26:31Z: clear bounded
corrections within accepted scope go directly to tuner then independent review;
uncertain causes/scopes warrant diagnosis. This supersedes treating diagnosis
and another operator disposition as mandatory preliminary steps for every clear
correction. Required host/Git operations, unresolved decisions and explicit model
run authorization remain operator responsibilities. Apply this at safe handoffs
without duplicate work or interrupting active claims. All numerical budgets,
immutable provenance, independent review and hardening deferrals remain.


## 2026-09-11T15:40:45.825Z — actual run4 inputs bound for final review, tuner145461

RUN4-FREEZE-145461.md and evidence/run4-freeze-145461/candidate-manifest.json
bind327 files, manifestsha256:8dd26ff86cbef12103b9184d4f06fd8d011494dd3f4c967bd533f9f032378f0a. All33 host-rendered
files match deterministic reconstruction after only temporary path substitution;
ordinary schemas pass. Accepted27/25/prior229 package files,45 provider entries
and source requirements match; live immutable images and supplemental clean
original Git baseline/payload/bare checks pass. Host posture remains explicitly
operator evidence, not managed projected-ID proof. No helper/test/source change.

Pass completed final-input binding directly to baton.feat review, Next baton.ops
with exact host provision/run commands. Genuine review/markers and explicit owner
run authorization remain; both exact commands currently have no installed rule
match. No production state, model run, repeated preparation/render, root repair,
Git or prior-evidence mutation. Keep campaign direct-routing ruling, all original/
derived/landed/terminal proof obligations and hardening deferrals. Failed runtime
560.1007706070232s and listed preparation3.2739890010347463s plus uncertainty remain spent.


## 2026-09-11T15:44:36Z — final run4 package independently accepted — baton.codex

review-2026-09-11T15-44-36Z.md accepts327 files plus manifest,33 reconstructed actual host documents,
45 provider entries/four source requirements, live images and clean original
baseline. This supersedes pending final material-delta review, not owner145458's
run hold. Genuine markers now bind this review and328 paths/all three helpers at
prepared-145397 with retained copies/digests in evidence/review-145494. Managed
ID projection remains distinct from host posture evidence. No new test changes.

Pass same Work to ops, Next tuner, with exact provision/run commands in review
and RUN4-FREEZE-145461.md. No repeat preparation/render/build. Remaining owner
involvement is explicit run/host access disposition; routine clear corrections
follow parent direct-routing ruling. Actual original/derived/landed/terminal
proof remains outstanding. All three failures560.1007706070232s and listed
preparation3.4397910760384858s plus untimed/operator/billing uncertainty stay spent.
All limits/deferrals persist; no model/runtime/production/Git mutation or reserve
transfer. Package acceptance alone authorizes no additional model attempt.

## 2026-09-11T15:59:06Z — run4 incomplete; report instruction omission — baton.codex

Owner M145524 authorized exactly one run4, superseding the145458 hold for that
attempt only. Return145562 reports its120s integration watchdog failure and
authorizes diagnosis and direct routing of clear bounded corrections. No further
model retry, deadline increase or live repair is authorized.

review-2026-09-11T15-59-06Z.md and evidence/review-145574 independently establish
both implementations/original reviews completed, A integration launched, and its
two target files match accepted candidate58c20e7e1ed8a2875b3f04d97471b59fe850bf90
at0644. Source stays clean; target HEAD remains original with those two changes.
No integration result exists, no B integration or derived/terminal completion.
Container stopped137/OOMKilled=false; canonical running field is stale after
exceptional containment. Run4 wall272.6205856000015s;110 samples106 available,
4 not-requested,0 unavailable. Stats correction did not cause this failure.

Confirmed separately: actual integration instructions plus hash-matched composed
prompt name the report schema but omit its eight keys and allowed values. The
provider's exact timeout phase/cause remains unknown; target mtimes do not prove
an internal execution trace. Do not equate the instruction omission with a proven
cause or its correction with terminal acceptance.

REPORT-INSTRUCTIONS-CORRECTION-145574.md pins a bounded new immutable preparation
instruction/test correction through existing integration_instructions, directly
to tuner then independent review. It supplies the existing report contract and
actual-value rules without changing product/parser/image/runtime/import guards.
This is a recorded deployment stopgap for the default workload prompt omission;
generic prompt improvement is deferred here for revisit after feasibility or use
by another deployment. Preserve all current source ownership. This supersedes
pending run4 execution disposition above: run4 was consumed and failed; its dirty
target is retained, never repaired or reused for another attempt.

Optional docker diff access was denied; supported inspect/logs/ps and ordinary
retained files supplied evidence. No container-private report is claimed observed.
Four failed walls832.7213562070247s and listed preparation/diagnosis3.458741714035963s
plus all untimed/failed-command/host/billing uncertainty stay spent. All limits,
hardening deferrals, immutable evidence and honest terminal acceptance remain.


## 2026-09-11T16:06:56.370393+00:00 — bounded report instruction implementation pinned, tuner145615

Revalidated review145574 and REPORT-INSTRUCTIONS-CORRECTION-145574.md against
integration_contract.check_report and integration_workload.integrate/compose_prompt.
New prepared-145615 changes only documents() integration instructions, supplies
the eight closed report keys and actual-value semantics, and adds focused offline
test_report_instructions.py. Copied test_manifest_timestamp.py and
test_stats_observation.py remain byte-identical. Tuner owns these new package
paths and its handoff/progress; product/parser/image/runtime paths remain untouched.
This is the already recorded deployment stopgap, not a proven timeout remedy.

Revalidation correction to reviewer evidence: inspect_retained.py passes the
whole measure_bundle() mapping to compose_prompt, whereas actual integrate()
passes correlated['bundle_digest'], the measured digest string. Thus the retained
reconstructed prompt's mapping-valued identity is a diagnostic reconstruction
error, not actual runtime behavior. The missing eight-key contract remains
confirmed. New offline tests use the actual string operand and real report
correlation; no speculative dict-handling workaround is added. Earlier evidence
is preserved and this explicit clarification supersedes its operand-identity
claim only.

The package retains historical, submitted run4 operands solely for comparison.
It is not executable/final input preparation and must not be provisioned/rendered
over dirty run4. No host roots, Git actions, state repair, model attempt, deadline
increase or new hardening gate. Four failed walls832.7213562070247s and listed
preparation/diagnosis3.458741714035963s plus uncertainty remain spent.


## 2026-09-11T16:12:39.599670+00:00 — report instruction candidate complete, tuner145615

REPORT-INSTRUCTIONS-CANDIDATE-145615.md and prepared-145615/candidate-manifest.json
bind33 files, manifestsha256:601f57182dd6b19922b5ce5e0f7b58abde24f74533a3720af07d75f3bd13bbdd.
Only deployment.documents() instructions change;21 dependencies match unchanged.
All26 offline tests pass, six new actual prompt/report-contract cases and20
unchanged cases. All327 prior freeze files,45 provider entries and four source
requirements match. No product/live/host/Git/model or prior-package mutation.

This supersedes pending tuner implementation, with direct independent correction
review next. Historical run4 operands are not executable; any later fresh inputs
and execution remain owner-reserved. The default prompt omission stopgap does
not establish timeout cause or A/B terminal completion. New report tests and
verification harness are the only additive verification paths; no old test edited.

Initial test loader import-path mistake and overbroad provenance comparison are
disclosed in handoff/evidence; no product failure inferred. Preserve all four
failed walls832.7213562070247s and listed preparation/diagnosis3.8131969440223057s
plus untimed/failed-command/host/billing uncertainty, all limits and deferrals.

## 2026-09-11T16:14:49Z — instruction correction independently accepted — baton.codex

review-2026-09-11T16-14-49Z.md accepts prepared-145615 manifest
601f57182dd6b19922b5ce5e0f7b58abde24f74533a3720af07d75f3bd13bbdd,
superseding pending correction review. All33 candidate files,27 prior candidate
files,327 prior frozen files,45 provider entries and four source requirements
match. Twenty-one dependencies are identical; only one instructions literal is
added to documents(). All26 offline tests pass, including six new actual prompt/
contract/correlation cases and20 unchanged cases. Evidence: evidence/review-145681.
No test expectations weakened or product/runtime/parser/import guard changed.

Reviewer confirms the tuner correction to claim145574: the reconstruction used
the measure_bundle mapping; the actual workload passes its digest string. The
earlier operand-identity reconstruction is superseded as inaccurate, not a product
defect. The missing report-contract finding and run4 observations remain intact.

Pass existing Work to ops, Next tuner, for later owner host/run disposition.
Historical submitted dirty run4 operands are not executable. Correction acceptance
does not authorize a retry or establish timeout cause/A/B terminal completion.
Fresh isolated input/host preparation and actual final-input review remain for
any owner-authorized next attempt; no new routine planning gate. Preserve all
four failed walls832.7213562070247s, listed preparation/diagnosis4.045642237012029s
plus all uncertainty, limits, deferrals, evidence and active source ownership.


## 2026-09-11T18:51:56.074Z — owner146531 fresh run5 preparation pinned, tuner146538

Owner146531 authorizes concrete fresh run5 inputs incorporating the report
instructions accepted by review-2026-09-11T16-14-49Z.md. This supersedes the
pending owner fresh-input disposition above for preparation only; model execution
remains unauthorized. No preliminary diagnosis or routine operator permission
gate is added. Prepare the package and combined exact host preparation plus
validate/render commands, then direct independent material-delta review.

New prepared-146538 uses /home/sl/.local/state/baton/v12/w71879-run5, observed
absent before preparation, UUID c71879af000000000000000000000001 and consistent
run5 principal/scope/profile/incarnation/task/manifest/submission identities.
Use CREATED 2026-09-11T18:51:56.074Z with required fractional milliseconds. Preserve accepted
images, original base/tree, complete task behavior, report contract, import/
verification guards and1200/240/180/120 limits. All four run roots and run4
target changes remain retained. Timeout cause remains explicitly unresolved.

Tuner owns only new package helpers, tasks/policies/record snapshots, additive
preparation tests and dossier handoff/progress. In copied test_manifest_timestamp.py
update expected timestamp and fixture principal/prefix; in copied
test_report_instructions.py update fixture principal/prefix only. Preserve all
assertions and contract expectations. Copied stats test stays byte-identical.
Add test_run5_preparation.py for the fresh namespace/public-bootstrap constructor
and unchanged behavior. W71830 standing test authority applies; these changes
are recorded for independent review, not another approval gate.

Host-only Git clone/target ownership operations are supplied as exact reviewed
commands for Slawomir, never executed by this managed turn. No live repair, model
run, deadline increase, source/parser/image/runtime change or broader hardening.
Four failed walls832.7213562070247s and listed preparation/diagnosis
4.045642237012029s plus all untimed/failed-command/host/billing uncertainty remain.


## 2026-09-11T18:54:07.810654+00:00 — offline fresh-root fixture correction, tuner146538

The first run5 offline suite reached17 passing stats cases but three constructor
setups refused: real held_configuration nominates RUN/source, and run5/source
correctly does not exist before operator preparation. Earlier copied tests
implicitly depended on already prepared run4/source. This is a test-fixture
deficiency, not a product defect or permission blocker. Retain failed output
at /tmp/w71879-146538-offline-verification-09igeue0;0.20350630499888211s stays spent.

Within the scheduled new-package test scope, add offline_fixture.py supplying a
labelled temporary empty nominated-source directory and overriding only RUN
for documents() construction. Use it in copied timestamp/report tests and the
new preparation tests. Real nomination, schema validation, report parser and
bootstrap stay unchanged; no validator stubs, production root creation or fake
host posture. Assert production RUN restores to run5 and distinguish temporary
output roots from actual future host configuration. This supersedes only the
earlier fixture-edit enumeration; existing behavior/assertions stay required.


## 2026-09-11T18:58:09.536Z — concrete run5 preparation complete, tuner146538

RUN5-PREPARATION-146538.md and prepared-146538/README.md provide combined exact
host preparation/validate/render commands and held eventual provision/run.
The37-file manifestsha256:bbb5761e087ed5bd61c8371de09346da35f9632f7cbbb203ce16b657cdc5483b
binds mechanical run5 identities with accepted byte-identical report instructions,
images and safeguards. Thirty offline checks pass; test-fixture source nomination
correction and failed spending are retained, not a product defect or host bypass.
All33 correction/327 freeze files,45 provider entries and four source requirements
match. Source baseline clean and both images available; run5 host root absent.

This supersedes pending tuner preparation. Pass directly to independent feat
review, Next ops, carrying all host commands together. Owner146531 preparation
authority does not authorize model execution. Real host outputs and final-input
review precede the eventual run decision; no new preliminary permission gate.
All four runs/dirty run4 remain; timeout cause and terminal proof stay unresolved.
Preserve832.7213562070247s failed wall and4.5073859860062235s listed preparation
plus untimed/failed-command/host/billing uncertainty, all limits and deferrals.

## 2026-09-11T19:00:11Z — run5 preparation independently accepted — baton.codex

review-2026-09-11T19-00-11Z.md accepts prepared-146538 manifest
bbb5761e087ed5bd61c8371de09346da35f9632f7cbbb203ce16b657cdc5483b,
superseding pending preparation review. All37 files, prior33/327 files,45 provider
entries/four source requirements match;30 offline tests pass. Test changes only
update timestamp/identity and real temporary source fixtures; no assertion or
validator weakening. Mechanical namespace changes preserve accepted report
instructions, tasks, images and safeguards. Source baseline is clean, run5 absent.
Independent evidence: evidence/review-146582/.

Pass to ops, Next tuner, with exact operator-prepare, validate and render commands
together in the review and bound README. Owner146531 already supplies preparation
authority; no extra preliminary diagnosis/routine permission gate. Actual host
outputs then undergo existing final-input binding/review; model execution remains
held. Preserve four runs and dirty run4; timeout cause and terminal proof unresolved.
Failed wall832.7213562070247s and listed preparation/diagnosis4.765032461997574s plus
all untimed/failed-command/host/billing uncertainty, limits and deferrals remain.


## 2026-09-11T19:06:09.596Z — actual run5 host outputs supplied, tuner146623

Owner146620 confirms operator preparation and host validate/render succeeded
and assigns actual-input binding/final independent review with exact execution
commands. This supersedes pending host preparation above, not the hold on a
model run. Consume accepted prepared-146538/review-2026-09-11T19-00-11Z.md and
retain successful validation output /tmp/w71879-146538-validation-lr__6q30.
No repeated Git/preparation/validate/render/image build is needed.

Tuner owns only new evidence/run5-freeze-146623, handoff and current dossier
entries; no helper/test/product/source or prior-evidence change is scheduled.
Reconstruct documents offline from the actual public bootstrap facts and accepted
images, compare exact host outputs after only temporary destination substitution,
and revalidate inherited bindings. Host UID/GID posture remains owner evidence;
managed projection is not proof of real host ownership. Preserve all four runs,
dirty run4,832.7213562070247s failed wall,4.765032461997574s prior listed preparation
plus host validation0.025035662998561747s and untimed/host/billing uncertainty.
Original timeout cause and actual A/B terminal proof remain unresolved; all
limits/deferrals and explicit owner model-run disposition remain.


## 2026-09-11T19:09:56.494Z — actual run5 inputs bound, tuner146623

RUN5-FREEZE-146623.md and evidence/run5-freeze-146623/candidate-manifest.json
bind444 files, manifestsha256:a9ff1b8e38de58a862319c13de4bf1badccc15c28d8b88b74eb7f955d0a9f531.
All33 actual host outputs match unchanged real constructors with actual public
bootstrap facts after only temporary destination substitution. Schemas pass;
accepted report instructions exact. Prior37/33/327 files,45 provider entries/four
source requirements match. Images retain accepted metadata; supplemental
source/target baseline checks are clean. Real host posture is owner146620's
success evidence, explicitly separate from managed projected IDs.

This supersedes pending tuner actual-input binding. Direct independent final
review through feat, Next ops, with exact held provision/run commands in handoff.
No helper/test/source change, repeated host preparation/render, new marker,
model attempt, runtime, live repair or prior-evidence mutation. Run5 remains
unprovisioned. Owner model authorization still required. Preserve all four runs,
dirty run4, unresolved timeout cause and genuine A/B terminal obligations.
Failed wall832.7213562070247s and listed preparation4.831007444991368s plus
untimed/failed-command/host/billing uncertainty remain; all limits/deferrals hold.

## 2026-09-11T19:11:49Z — final run5 package independently accepted — baton.codex

review-2026-09-11T19-11-49Z.md accepts444 files plus manifest,33 actual host
documents reconstructed with real schemas/public facts,45 provider entries/four
source requirements, unchanged image metadata and clean original baselines.
This supersedes pending final material-delta review, not owner146620's run hold.
Genuine selected-images/execution-review markers at prepared-146538 bind445
paths/all three helpers and this review, with copies/digests in evidence/review-146656.
The execution marker explicitly records no model authorization. Real host posture
remains owner success evidence, distinct from managed ID projection.

Pass to ops, Next tuner, with exact provision/run commands together in review
and RUN5-FREEZE-146623.md. No repeat preparation/validate/render/build or planning
gate. Owner model-run decision remains; no further attempt, live repair, deadline
increase or Git change occurred here. Actual A settlement/B derived integration/
causal/terminal acceptance and original timeout cause remain unresolved. Preserve
four failed runs/dirty run4,832.7213562070247s failed wall and4.881056235994432s listed
preparation/diagnosis plus untimed/failed-command/host/billing uncertainty, all
limits/resource/custody/authorization checks and hardening deferrals.

## 2026-09-11T19:30:01Z — run5 index refresh evidence and missing status observer — baton.codex

Owner M146694 authorized the single run5, superseding146620's run hold only
for that attempt. Owner return146728 and claim146732 now supersede the pending
execution action: run5 failed in292.0414934099972s. A returned held/repository-mutated
after about61s, exit0, not a provider timeout. Both original implementations and
reviews completed; B integration remained blocked. Five runs remain retained.

review-2026-09-11T19-30-01Z.md and evidence/review-146732/result.json distinguish
observed target index refresh (mtime19:19:10.200016Z, same staged entries with
changed cached stats) from inferred provider-side Git read. Exact PID/command is
unobserved. Disposable real-witness comparison confirms ordinary git status can
rewrite the index without staging anything; --no-optional-locks prevents that
fixture refresh. It does not prove the actual writer. Target candidate bytes
match A, but independent runtime verification was not reached.

A correlated held result conservatively blocks the target; it cannot conclude
as successful integration. The runner's STATUS omits the accepted read-only
integration observer, so starting/quiescent is not an account of coordinator
settlement. Exact observed-status CLI failed at JobStore.open with unable to open
database file; this is an operational finding, cause unestablished. No bypass or
repair. Review gives the public owner read command and preserves uncertainty.

Under the campaign15:26:31Z direct-correction ruling, route directly to tuner,
Next independent review, for two bounded deployment changes in a new immutable
prepared-<claim> package: instruct every integration Git read to use
--no-optional-locks, and wire STATUS to the existing observing_factory with its
exact config. Scope is deployment.py/run.py, focused offline tests, manifest and
handoff plus tuner PROGRESS. Preserve historical packages/roots, product sources,
images, guards, report contract, deadlines and all terminal acceptance. This
explicitly supersedes the prior no-observation-factory harness choice, because
integration status requires its existing owner observation for honest acceptance.
No new provider/product implementation or fresh run identity preparation.

Tests exercise real witness/prompt/observer selection and completed versus held
projection, using existing fixtures within budgets. Record affected paths/reasons;
standing W71830 test authority supplies permission. New model attempt, host/Git
repair, deadline increase and manual lifecycle transitions remain unauthorized.
The review specifies exact ownership and next handoff; no new planning prerequisite.

Indexed W71879 deferrals: precise provider-command tracing and generic Git-read
enforcement; richer held diagnostics/fail-fast/recovery in the runner. Revisit
after ordinary A/B acceptance or owner decision. Existing W144335/W144813/
W136578/W129838 and fault-C/resilience deferrals remain. Actual A settlement,
B derived integration/judgments, merged causal evidence and both terminal Jobs
are still owed. Five failed walls1124.7628496170219s; listed preparation/diagnosis
4.908113534991966s plus prior uncertainty. All resource/authorization limits hold.


## 2026-09-11T19:36:01.614547+00:00 — two bounded deployment corrections pinned, tuner146797

Revalidated review146732 against current integration_workload witness/prompt,
job_manager._status/_observation_from, stage_execution.observing_factory and
projection._integrating. New prepared-146797 adds explicit no-optional-locks
integration Git-read instructions and supplies exact config plus observing_factory
to runner STATUS. Startup control-store guard, command failure, deadlines and
all-stages-completed success criterion remain unchanged. Historical run5 operands
are retained; no run6 preparation or execution is authorized.

Tuner owns only the new immutable package and focused tests/handoff/progress.
Copy existing timestamp/report/stats tests; update copied test_run5_preparation.py
only for the two scheduled deltas while preserving identity/task/policy checks.
Add test_observed_status.py for real prompt/witness-safe reads, actual observer
factory selection, real projection completed/held distinction and main-loop
held refusal. Temporary fixtures only; no real-run repair or Git mutation.
Existing full owner fixtures require constructing private Git histories; bounded
local checks will disclose synthetic observation inputs rather than run those
Git-mutating fixtures or claim an actual successful owner settlement. Product
source, images, guards and report contract remain unchanged. Missing guessed
tests/job_manager/test_projection.py was a locator error; projection.py is the
actual owner and is readable. No unreadable bound policy/dossier file.

All five runs and exact-writer/coordinator-entry uncertainty remain. Public
observed-status access failure is already recorded and is not retried/bypassed.
Failed wall1124.7628496170219s and listed preparation4.908113534991966s plus
untimed/failed-command/host/billing uncertainty stay spent; all limits/deferrals.


## 2026-09-11T19:42:02.051Z — Git-read/status correction complete, tuner146797

GIT-READ-STATUS-CORRECTION-146797.md and prepared-146797/candidate-manifest.json
bind39 files, manifestsha256:156cb7f53d1eab4e41d1602742ddda778376250b6d1af5e7eee9e12a3c775588.
Only integration Git-read instructions and STATUS observer/config change;23
dependencies unchanged. Copied test_run5_preparation.py retains preservation
assertions accounting exactly for assigned deltas via new correction_expectations.py.
New test_observed_status.py adds six cases;36 offline tests pass. First observer
fixture lacked its required control group; fixed with public temporary ControlStore
configuration, with failure/cost retained. No validator stub or host posture claim.

Real witness-safe reads, prompt, CLI/factory selection and projection are covered;
held cannot satisfy actual runner success. Completed/held account inputs remain
explicitly synthetic, not proof of a real settled owner. All37/444 prior files,
45 provider entries/four sources match. No source/image/guard/deadline/terminal
relaxation, new run identity, model retry, live repair or historical package change.
This supersedes pending tuner implementation; direct independent feat review next,
then existing owner path. Five failed walls1124.7628496170219s and listed
preparation5.511844064989813s plus uncertainty remain; all deferrals and actual
A/B terminal obligations persist, exact run5 writer/coordinator entry unresolved.

## 2026-09-11T19:47:17Z — bounded Git-read/status correction accepted — baton.codex

review-2026-09-11T19-47-17Z.md independently accepts39-file prepared-146797,
manifestsha256:156cb7f53d1eab4e41d1602742ddda778376250b6d1af5e7eee9e12a3c775588.
Thirty-six offline tests pass; exact candidate/prior37/prior444 file bindings,
45 provider entries/four requirements/three observation source hashes match.
Twenty-three dependencies unchanged; only scheduled instruction/STATUS changes
and the copied preservation-test expectations differ. Test expectation changes
retain accepted behavior and standing authority; synthetic owner inputs remain
explicitly separate from actual settlement. Evidence in evidence/review-146872.

This supersedes pending independent review. Direct ops, Next tuner, for existing
owner disposition. No extra diagnosis/planning gate, fresh host preparation,
model retry, source/image change, repair or execution marker. Historical run5
operands remain nonexecutable; all five runs and exact-writer/coordinator-entry
uncertainty remain. Actual A settlement/B derived integration/causal/terminal
proof is still owed. Preserve1124.7628496170219s failed wall and now
5.820637809978901s listed preparation/diagnosis plus uncertainty, all limits
and indexed hardening/fault-C deferrals. Exact handoff/review scopes are unchanged.


## 2026-09-11T19:51:48.071Z — fresh run6 preparation authorized, tuner146897

Owner return146894 authorizes fresh run6 inputs incorporating the corrections
accepted by review-2026-09-11T19-47-17Z.md. This explicitly supersedes the prior
no-fresh-preparation restriction only; model execution remains unauthorized.
Revalidated the accepted39-file package and current handoff. New prepared-146897
uses /home/sl/.local/state/baton/v12/w71879-run6 and fresh Authority
c71879b0000000000000000000000001, with run6 principals/scope/profile/incarnation/
tasks/submission and millisecond timestamp 2026-09-11T19:51:48.071Z. All five old runs remain.

Tuner owns the new package, snapshots, evidence and preparation handoff. Copy
accepted deployment/runner with identity metadata only; preserve exact Git-read
and report instructions, observer config, images, tasks, safeguards and limits.
Provide host operator-prepare plus validate/render commands together for review.
No host Git/ownership operations, prepare/validate/render/provision/serve, model
execution, live repair, guard relaxation or deadline increase in this managed turn.

Standing W71830 test authority applies to copied test_run6_preparation.py
(renamed from test_run5_preparation.py, checks fresh bindings/preservation),
test_manifest_timestamp.py/test_report_instructions.py (fresh fixture identity),
and test_observed_status.py (fresh identity and explicitly copied original
run1/source fixture, because run6 source does not exist yet). Existing assertions
and six observer cases remain. Retain stats tests unchanged and actual validators.
These are offline fixtures, never actual host posture/owner settlement evidence.

Run5 index refresh is observed; exact writer/command and coordinator entry remain
unresolved. Actual A settlement, B derived integration/judgments, merged causal
observations and both terminal Jobs are owed. Keep1124.7628496170219s failed wall
and5.820637809978901s listed preparation/diagnosis plus uncertainty, all limits
and indexed deferrals. Guessed operator-prepare-run5.sh was absent; actual bound
operator-prepare.sh was read successfully. This was a locator error, no unreadable
bound file or deployment defect. No extra diagnosis/planning gate is introduced.


## 2026-09-11T19:56:44.743Z — run6 preparation complete, tuner146897

RUN6-PREPARATION-146897.md and prepared-146897/README.md supply concrete host
preparation plus validate/render commands together and separately held execution
commands. Manifest binds 37 files, SHA256 d24b5349ed6a6e35b37fbc933eaa2550fea7233d2483123ba5ad985f3d1f7c37.
Fresh run6 root remains absent. Only scheduled namespace/time/ruling metadata
changes in deployment/runner; accepted instructions and observer wiring remain.
Current snapshots pin owner146894; prior packages and all five runs are preserved.

All36 offline tests pass in0.29618631600169465s, with public bootstrap/real
schemas and whole-file preservation checks. Copied test_run6_preparation.py
replaces local run5 test name and adds STATUS incarnation check; timestamp/report
fixtures use run6 metadata; observer test uses an explicit filesystem copy of
original run1/source because fresh run6 is absent. Assertions/validators remain.
Stats tests unchanged. Synthetic owner accounts still do not prove settlement.
Exact affected paths/delta and retained /tmp paths are in README/evidence.

All39/37/444 prior files,45 provider entries/four source requirements/three
observer source bindings match. Nine copied dependencies unchanged; images
available, original source clean, bash -n and git diff --check pass. No source/
image change, external root, actual final inputs, marker, model run, repair or
Git mutation. Direct independent feat review, Next ops, supersedes pending tuner
preparation. Actual final-input freeze follows existing reviewed host sequence.

Failed wall1124.7628496170219s, listed preparation6.126776408979307s (prior
5.820637809978901 + suite0.29618631600169465 + provenance0.00995228299871087)
plus untimed/failed-command/host/billing uncertainty remain spent. All limits/
deferrals and exact-writer/coordinator-entry/actual A/B proof uncertainty remain.

## 2026-09-11T19:58:47Z — run6 preparation independently accepted — baton.codex

review-2026-09-11T19-58-47Z.md accepts37-file prepared-146897, manifestsha256:
d24b5349ed6a6e35b37fbc933eaa2550fea7233d2483123ba5ad985f3d1f7c37. Independent36-test
offline suite passes; candidate/prior39/37/444 file bindings,45 provider entries,
four requirements/three observer bindings match. Nine dependencies unchanged.
Fresh namespace/time/ruling changes preserve accepted task/policy/helper behavior;
copied test expectations remain genuine under standing test authority. Instruction
bytes and read-only STATUS correction remain exact. Run6 root/final inputs/markers
are absent. Accepted images available, original source clean; static checks pass.

This supersedes pending preparation review. Direct ops, Next tuner, for the
owner146894-authorized operator-prepare then validate/render; all exact commands
are together in the review and bound README. No extra diagnosis/planning gate,
deployment prepare/rebuild, live repair or model run. Actual host outputs return
for existing final-input binding/review and later explicit owner run decision.
Preserve all five runs, exact run5 writer/coordinator-entry uncertainty and genuine
A/B terminal obligations. Failed wall1124.7628496170219s; listed preparation/
diagnosis6.433112515973729s plus uncertainty; all limits/guards/deferrals remain.


## 2026-09-11T20:05:45.152Z — actual run6 input binding assigned, tuner146988

Owner return146985 reports successful operator preparation and host validate/
render after independent preparation acceptance review19:58:47Z. This explicitly
supersedes pending host preparation; another model run remains unauthorized.
Bind actual prepared-146897 outputs in new evidence/run6-freeze-146988 and pass
directly for final independent review, Next ops with exact held execution commands.
No repeat prepare/validate/render/provision, image build, model run, live repair,
Git mutation, source/helper/test change, fabricated marker or deadline increase.

Verify actual33 documents through accepted constructor and actual retained public
bootstrap facts, only output destination temporary; no RUN/validator substitution
or store reads. Revalidate accepted manifests/provider/source bindings, clean
source/target payload/base/tree/main and bare workspace with read-only Git.
Host UID/GID posture remains owner-success evidence, not projected managed IDs.
Preserve five runs, exact run5 writer/coordinator-entry uncertainty, prior failed
wall1124.7628496170219s and listed preparation6.433112515973729s plus new host
validation and bounded verification spending/uncertainty. All limits/deferrals
and actual A/B terminal proof obligations remain. Tuner owns only new freeze
evidence/check script and attributable records/handoff; no existing tests change.


## 2026-09-11T20:06:52.049Z — image inspection process invocation failed, tuner146988

Observed: docker image inspect launched inside the evidence-building Python
subprocess returned status1 before any evidence writes. CalledProcessError
retained argv/status but the wrapper failed to print captured stderr; exact cause
is unknown. This is an operational invocation finding, not evidence of a Baton
product defect or changed image. Prior actual-input/baseline verification passed.
Use the existing directly authorized read-only docker image inspect boundary to
obtain actual metadata/output; no escalation, alternate engine/socket, image build
or runtime start. Preserve the failed command/cost uncertainty in handoff.


## 2026-09-11T20:09:40.125Z — actual run6 inputs bound, tuner146988

RUN6-FREEZE-146988.md and evidence/run6-freeze-146988/candidate-manifest.json
bind568 files, SHA25687a320bdee36cfdca8e7d18372e65ff26eeb314eeda948db3402692b328dd0a9.
All33 actual documents reconstruct exactly from accepted constructor/real retained
public bootstrap facts after output-path substitution only. Source/target clean
main/original base/tree and10 payloads match; workspace bare; execution stores/
roots and markers absent. Host posture remains owner-success evidence.
Entire report/Git instructions and owner-based STATUS are unchanged.

Verified37/39/37/444 prior file sets and45 provider entries/four requirements/
three observer source bindings. Accepted image metadata matches through direct
inspection; failed Python subprocess invocation/status1 remains documented,
exact cause unknown. No escalation/alternate engine or image/runtime mutation.
No existing test/helper/product/source/image change or repeated host preparation.
Independent preparation36-test evidence retained; this claim only checks actual
inputs. Existing final independent feat review is next, then ops for explicit
run decision; exact held provision/run commands are in the handoff. This
supersedes pending tuner binding, not the no-model-run restriction.

Listed preparation6.501497828962268s includes host validation0.023940075989230536
and current check0.04444523699930869 on prior6.433112515973729; failed wall
1124.7628496170219s plus untimed/failed-command/host/billing uncertainty remain.
All five runs/dirty targets, limits/deferrals, exact-writer/coordinator-entry
uncertainty and actual A/B terminal proof obligations remain.

## 2026-09-11T20:11:32Z — final run6 inputs independently accepted — baton.codex

review-2026-09-11T20-11-32Z.md accepts568-file actual package plus manifest,
SHA25687a320bdee36cfdca8e7d18372e65ff26eeb314eeda948db3402692b328dd0a9.
All33 actual documents reconstruct exactly with real retained public facts and
output-destination substitution only. Independent custody/image checks pass;
prior37/39/37/444 files,45 provider entries/four requirements/three observer
bindings remain exact. Accepted36-test preparation evidence retained; no helper/
test/source/image change or repeated suite. Clean source/target baseline/main/
payload and bare workspace verified. Real host posture remains owner evidence.

Genuine selected-images/execution-review markers now exist at prepared-146897,
with copies/digests in evidence/review-147020. Marker binds569 paths/all three
helpers and actual config/submission, this review locator, and explicitly records
execution_authorized:false. This supersedes pending final review and marker
absence, not owner146985's no-model-run restriction. Direct ops, Next tuner,
with exact provision/run commands together in the review and RUN6-FREEZE-146988.md.
No repeat preparation/validate/render/build or new planning gate. Five prior runs,
run5 writer/coordinator-entry uncertainty and genuine A/B terminal obligations
remain. Failed wall1124.7628496170219s; listed preparation/diagnosis now
6.558265653970405s plus uncertainty; all limits/guards/deferrals preserved.


## 2026-09-11T20:28:10.480Z — run6 failure and bounded correction pinned, tuner147109

Owner147106 applies campaign FINDING/PLAN20:23:14Z and assigns prompt definitive
failed-required-attempt handling and a nonsecret diagnostic boundary. M147067
authorized exactly run6; it failed in216.34791136499553s with a later TimeoutError.
Retained samples show A answered unable at sample5/8.731681402990944s and B review
answered unable at sample21/41.547954526991816s; B implementation completed at
sample17/34.741726855994784s. Correlated custody result/review reports publish
provider status1/api-error, A provider-failed/no candidate and B no verdict.
Six failed walls now1341.1107609820174s. Prior listed preparation6.558265653970405s
plus current verification spending/uncertainty remains; no fresh run authorized.

New prepared-147109 preserves historical run6 operands (not executable). Tuner
owns copied runner plus a bounded failure-observation helper and focused tests.
Use existing canonical STATUS exchange terminal evidence, correlated to current
attempt/episode/allocation/assignment. Stop on definitive unable/cancelled or
closed fault/lost terminal; pending collection, quiescence, missing telemetry,
completed and review plan-rejected are not this failure. Preserve first failure
before diagnostics/telemetry and supported containment; later watchdog/cleanup
errors remain secondary. Success/deadline/host/custody guards stay.

Diagnostics use only existing correlated published adapter result.json/review.json
and fixed allowlisted reason/status values; no provider stdout/stderr, credential
file, arbitrary report prose or new classifier. Bounded no-follow regular-file
reads stay under the configured storage custody path; missing/unreadable/untrusted
report means unavailable/unknown, never a substitute lifecycle failure.
claude_agent.py currently maps only api_error to api-error, plus timeout/start-error/
unclassified; it cannot establish an authentication cause. Exact provider causes
remain unknown. Supporting auth-specific diagnosis would require an independently
assigned adapter/image change with observed structured vocabulary under W55360;
that product source is outside tuner scope. No guessing, credential disclosure
or another model attempt to acquire evidence here.

Standing W71830 authority covers new failure tests and copied preservation-test
expectations only for the runner/helper delta; retain all stats/report/timestamp/
observer assertions. No prior package/test/source/image change. Direct independent
review next. This narrow requirement supersedes earlier blanket fail-fast/diagnostic
deferral; generic tracing/recovery/resilience and existing indexed Work remain
deferred. Six runs and run5 writer/coordinator-entry uncertainty are preserved.
Locator guesses for plural output/artifact modules were absent; actual output.py/
exchange.py/claude_agent.py are readable. A read-only evidence summary initially
failed on null terminal; corrected null handling without changing any evidence.
No unreadable bound file, raw store access, host repair or escalation.


### Claim147109 implementation scope clarification

New failure_observation.py is a fourth required execution helper; the runner
review marker must bind it as well as the existing three. Copied stats fixture
marker adds only this helper, and its exercise gains optional containment-error
injection for focused tests without changing prior assertions. The copied run6
preservation test retains accepted deployment/task/policy/operator equality,
compares the former runner against its accepted source, and schedules the exact
new runner delta for focused failure/guard tests and independent diff review.
Its stats-byte equality accounts only for the explicit fixture binding/injection.
No old tests are edited. Do not copy execution markers into this correction.


### Claim147109 focused verification correction

First49-case suite retained48 passes/one failed B-review replay. The new helper
incorrectly compared allocation generation1 (configuration) to Authority claim
generation2. These are distinct owners/axes. Corrected correlation uses the
current stage/episode performed claim receipt and runtime assignment equality;
foreign-generation refusal remains tested. Real retained STATUS receipts are
kept in replay facts. No source/product or acceptance expectation was weakened.
Failure logs/cost0.3226501370081678s retained. Symlink test was strengthened to
reach no-follow file opening at a valid custody path, not only reject its locator.


## 2026-09-11T20:39:21.128Z — early failure correction ready for review, tuner147109

EARLY-FAILURE-CORRECTION-147109.md and prepared-147109/README.md bind43-file
candidate manifest94d8b8e83b5d11a25edc8b91ae54e9bef98bc7a718cd8d17616784a00ea22cb2.
Runner records and raises the first correlated required failure promptly through
existing containment, with secondary deadline/cleanup errors and safe adapter
diagnostics. Helper is a fourth required review input. All49 offline tests pass;
retained A/B-review failures replay at8.731681402990944/41.547954526991816s.
Current published adapter reports both return api-error/status1, auth cause unknown.

Boundary is established: current adapter has no auth-specific discriminator;
exact causes cannot be recovered from retained coarse reports. A separately scoped
adapter/image contract change needs observed structured vocabulary and independent
closed-map review. No provider stream/credential access, new classifier, product
patch or model retry here. Precise unresolved scope is in handoff/README.
This supersedes pending tuner correction, not the diagnostic requirement before
another run. Direct independent feat review, Next ops for unresolved scope.

Only runner and two copied fixture/preservation tests differ;25 dependencies
unchanged, two new code/test files. All test paths/reasons and first failed49-case
suite are recorded. Final49 tests and git diff --check pass; prior37/568/provider
bindings verified. Six runs preserved, no new host inputs/marker/repair/source/image
changes. Failed wall1341.1107609820174s and listed preparation7.531655556995641s
plus uncertainty remain. All limits/deferrals and actual A/B proof obligations persist.

## 2026-09-11T20:42:32Z — runner correction accepted, provider diagnosis still open — baton.codex

review-2026-09-11T20-42-32Z.md accepts43-file prepared-147109, manifestsha256:
94d8b8e83b5d11a25edc8b91ae54e9bef98bc7a718cd8d17616784a00ea22cb2. Independent49-test
suite passes. Candidate/prior37/568 and source bindings match;25 dependencies
unchanged, exact runner/test delta reviewed under standing authority. New helper
must be the fourth review-bound executable input. No new marker or source change.

Independent replay verifies all168 retained sample projections and detects A at
sample5/8.731681402990944s and B review independently at sample21/41.547954526991816s.
Safe published-report reads return api-error/status1/authentication unknown for
both. This is retained replay, not a new run or proof the provider cause is fixed.
First failure remains primary through later deadline/containment errors; pending
collection/success/review correction and all success/limit guards remain intact.

This supersedes pending independent runner review only. Campaign20:23:14Z's
actionable diagnostic requirement remains immediate and unresolved. The reviewer
read W55360's full record and current adapter: no supported authentication-specific
discriminator survives in the retained reports; api-error cannot name its cause.
Owner must assign the supported nonsecret diagnostic observation/adapter scope
and evidence acquisition boundary before another run. No new category, raw-output
capture, product/image change or model retry is authorized here. Exact options
and required closed-map evidence are in the review; direct ops, Next tuner,
under owner147106's explicit unresolved-scope return instruction.

Six runs remain retained, failed wall1341.1107609820174s and listed preparation/
diagnosis8.020424597991617s plus uncertainty. No fresh packaging/repair/limit
increase; all guards and remaining deferrals hold. Actual A/B settlement/derived
integration/causal/terminal proof and run5/run6 uncertainties remain unresolved.


## 2026-09-12T01:19:47.948307+00:00 — diagnostic scope revalidated; exact installed source inaccessible, tuner148686

Owner return148665 explicitly assigns bounded Claude-adapter diagnostics beyond
the runner: inspect the exact installed provider code/documented vocabulary offline,
implement only supported closed classifications, preserve unknown and pass directly
for independent review. If evidence cannot establish a discriminator, return the
minimal diagnostic acquisition proposal and required authority. The later campaign
FINDING/PLAN01:12:52Z clarifies that another coarse label alone is insufficient: useful
nonsecret explanation/code/request detail, omissions and attempt correlation matter.
This supersedes the prior pending scope-disposition action and the statement that
all adapter source work is outside this tuner's assignment. It does not supersede
credential exclusion, independent review or the no-execution boundary.

**Observed operational finding.** Direct read-only docker inspect confirms run6 A's
exact retained exited container and accepted provider image, read-only root, and no
mount at the installed package path. A direct docker cp of only the installed
package.json failed with Docker socket permission denied; no provider package
bytes were read. This is an execution-policy/deployment limitation, not an observed
Baton product defect. No escalation, socket/overlay bypass, container start or
alternative privileged invocation followed. evidence/diagnostic-148686/operational-finding.json
pins the command, error and safe metadata.

The host launcher resolves to2.1.263; readable version directories are2.1.241,
2.1.250 and2.1.263. The image recipe pins2.1.247 and historical evidence reports
that version; it does not attest the installed binary bytes. W55361 history already
shows pinned npm metadata plus postinstall is not sufficient reproducibility.
No different-version host behavior is substituted. Filename-only local source
search found no candidate; unreadable private /tmp directories and guessed absent
locators are recorded, not bypassed or mistaken for proof of global absence.

**Confirmed unchanged contract.** Current adapter reads bounded structured stdout
then discards it; stderr/verification streams remain DEVNULL. Only api_error has
evidence in W55360. Published proposal1/proposal2 and review-log1 provider records
carry status/failure_reason/seconds_bound, not preserved causal detail. Historical
run6 api-error/status1 cannot establish authentication or recover discarded prose.
No exact-version discriminator or safe free-text publication rule is established
by these reads. No new category/source/test/image change is justified yet.

DIAGNOSTIC-ACQUISITION-148686.md supplies the exact minimal operator static-copy
step and read-only follow-up boundary, detail/exclusion acceptance, compatibility
and image implications. This is the explicitly requested fallback, pending direct
independent feat review, Next ops for the unavailable static acquisition boundary.
The actionable diagnostic requirement remains open; no model probe is requested.
All43 accepted prepared-147109 files match hashes/sizes/modes. Prior49-test acceptance
stands; no redundant runtime suite or new synthetic assertions were run against an
invented classifier. Tuner owns this new proposal/evidence and dossier entries only.
Preserve six failed walls1341.1107609820174s and listed preparation/diagnosis now
8.02408010199036s plus untimed/failed-command/host/operator/billing uncertainty.
All1200/240/180/120s and resource/target/custody guards, deferrals, actual A/B proof
obligations and run5 writer/coordinator/run6 provider-cause uncertainty remain.

## 2026-09-12T01:23:14Z — exact static acquisition fallback accepted — baton.codex

review-2026-09-12T01-23-14Z.md accepts the three-file proposal manifest
9a829c5d43c6c4f8fbe0a614ad2fc082d5056a38ea83c585a7d40596ba24e602. Independent
hash/size/mode/type checks and all43 accepted runner files/12 source bindings pass.
Direct inspection confirms the retained exited, read-only run6 A container and
accepted image, without a package-path mount. Destination remains absent; installed
package bytes remain unread after the recorded copy permission failure.

This supersedes pending proposal review only. Direct ops, Next tuner, for the
exact package.json copy in DIAGNOSTIC-ACQUISITION-148686.md and the new review.
Owner148665 already grants bounded offline source scope; access to exact installed
bytes is the concrete missing input, not another generic planning/scope gate.
No -L, overwrite, engine/socket/overlay bypass, code execution or credential/
provider-stream copying. Return regular bounded metadata/hash, then tuner traces
actual installation code paths under that assignment. Image execution, network/
model probes, new packaging and retry remain unauthorized.

Proposal correctly requires useful detailed errors with exclusions/omissions and
correlation, not only a new label, plus exact-version output evidence, compatible
adapter/reader contracts and both-image provenance if code changes. No classifier,
diagnostic cause or A/B completion is accepted. Prior49-test runner acceptance
stands without redundant tests. Six failed walls1341.1107609820174s; listed
preparation/diagnosis8.027892207996441s plus uncertainty. All limits/deferrals,
historical runs and actual A/B/run5/run6 proof uncertainties remain preserved.


## 2026-09-12T01:31:03.893141+00:00 — installed2.1.247 metadata verified; declared code paths established, tuner148768

Owner148760 completed the exact package.json copy accepted by review148728.
Verified non-symlink regular mode0644,1476 bytes,64KiB ceiling, no-follow opened
inode and SHA256204e690591b935992fff95f6d2af6aeac86be074719da7900f1c4e4056f37efe
before strict JSON interpretation. Evidence/diagnostic-148768 preserves exact bytes
and checks. Current direct inspection still confirms the retained exited/read-only
run6 A container and accepted image with no package-directory mount. Source identity
is owner copy attestation plus this posture, not a repeated tuner extraction.

This explicitly supersedes metadata-unread/pending metadata-copy statements above.
Installed package metadata says @anthropic-ai/claude-code2.1.247, bin/claude.exe,
postinstall node install.cjs; file list names cli-wrapper.cjs. These establish the
next exact static code paths. They do not resolve link/native target, installed
optional dependency or structured error contract. No classifier, auth cause or
safe prose publication follows from version metadata alone.

STATIC-PROVIDER-PATHS-148768.md gives three concrete static copies, bounded file
checks and the next source trace. Owner148760 supplied only the metadata; the
recorded Docker-copy restriction for this participant remains, and no repeated
denied invocation, bypass or code execution was attempted. This is the next
already-authorized acquisition step, not a new generic scope gate. Direct feat
review, Next ops for exact copies. Original useful-detail/exclusion/compatibility/
test/image boundary remains accepted; diagnostic requirement remains unresolved.
Tuner owns new path proposal/evidence and current dossier entries only. No product,
test, image, old package or marker change. All43 accepted runner files match;
prior49-test acceptance remains. Verification0.0032709279912523925s; cumulative
listed8.031163135987693s plus uncertainty, six failed walls1341.1107609820174s.
All limits/guards/deferrals and actual A/B/run5/run6 obligations preserved.


## 2026-09-12T01:36:09Z — independent metadata/path review accepted, reviewer148792

Review review-2026-09-12T01-36-09Z.md accepts STATIC-PROVIDER-PATHS-148768.md
for already-authorized operator static acquisition only. Independently verified
three-file manifest a223215b85a844aa6c94e28a6cb18bc840894fd7c769d24b0ef81a24a53cdb78,
owner-supplied metadata with bounded no-follow opened-inode/hash checks, all43
accepted runner files and retained exited/read-only container/image posture.
Metadata establishes declared install.cjs, cli-wrapper.cjs and bin/claude.exe;
all proposed destinations absent. No native/output contract or classifier proven.

Pass ops Next tune for exact copies and existing access boundary. No new planning
prerequisite; acquisition within owner148665/148760 scope. Useful nonsecret detailed
errors, exclusions/omissions/correlation and eventual tests/reader/both-image
provenance remain essential. No code/test/image change, provider execution,
credential/stream read, model/network probe, new package, repair or retry.
Prior49-test acceptance stands; metadata acquisition is complete, static source
trace and detailed diagnostics remain open. Actual A/B terminal integration remains
owed. Verification0.003350547020090744s; listed cumulative8.034513683007784s plus
uncertainty; six failed walls1341.1107609820174s and all limits/deferrals preserved.


## 2026-09-12T01:48:41.284743+00:00 — exact installed static trace and bounded diagnostic implementation, tuner148870

Owner148865 supplied all three accepted copies. Verified their no-follow regular
types, ceilings and hashes; exact provenance and offset-bound source slices are
in evidence/diagnostic-148870/static-provenance.json. Native file is ELF64 x86-64,
250162696 bytes, SHA2565fb321bf417ffc5cd4e3f36e7c9c7e029bf47aaa36d5621db979fcc5e6eabe15.
The installation script places the platform native binary at metadata bin/claude.exe;
its regular ELF bytes were acquired without executing any copied code. This
supersedes pending source-copy/unreadable native-code statements for these files.

**Confirmed static source:** bBe attaches API status to the synthetic assistant
error; LWo has an E8 branch whose noninteractive content is exactly Failed to
authenticate: OAuth session expired and could not be refreshed, with internal
error authentication_failed. The headless result constructor copies assistant
apiErrorStatus to api_error_status, isApiErrorMessage to is_error and its text
to result. The nonverbose JSON path serializes the final result and exits nonzero
on is_error. The result schema explicitly exposes nullable integer api_error_status.
Other LWo branches interpolate arbitrary error messages; those cannot pass through
merely because they are JSON. Internal requestId is not in the supported result
schema/constructor. No discarded run6 detail is recovered or cause inferred.

Under owner148665 and campaign01:12:52Z, implement only evidence-backed detail:
preserve the whole exact fixed OAuth explanation by equality to a source-owned
constant, internal authentication_failed classification for that match, and integer
HTTP error status400..599 where the complete supported result carries it. Every
other explanation is withheld/unavailable explicitly; request identifiers remain
unavailable. No substring/regex/prose redaction or secret reads. Authentication
remains unknown for HTTP status alone, including401/403. Current failure_reason
map and all lifecycle outcomes remain unchanged. This explicitly and narrowly
supersedes W55360's category-only publication restriction for these reviewed typed
status and fixed-constant detail fields; its raw text/stream/credential exclusions,
strict total parser and drain/overflow/partial bounds remain. Useful detail is
preserved where supported; arbitrary provider explanation is not claimed safe.

Tuner owns v12/worker/claude_agent.py and additive focused cases in
v12/python/tests/manager/test_claude_agent.py for this claim. Preserve existing
assertions. New prepared-148870 copies accepted prepared-147109 as historical
operands, updates only its reader and adds focused compatibility/sentinel cases;
old package remains immutable. Add optional provider.diagnostic to proposal1/2
and review-log1 failures, absent on success/start/timeout when no record exists.
A successor reader validates its closed schema and reconstructs safe values.
No new image, deployment marker, fresh-run package or run execution. Both image
provenance must be renewed before using changed adapter bytes. Independent review
follows; exact full error causes and A/B proof remain open.


### Claim148870 focused verification correction

First adapter run:180/181 pass, one new test incorrectly assumed2000 nested arrays
would exceed the configured decoder recursion limit. The valid record correctly
retained the fixed explanation. Corrected only that fixture to30000 arrays, matching
the existing accepted recursion-exhaustion regression within the64KiB byte bound.
No parser/expectation weakening. Failed log and9.614955884986557s remain recorded.
First reader suite59 cases passed in0.3315211730077863s; five were accidental
rediscovery of an imported TestCase. Changed its import to a module reference so
final count is49 inherited plus five new cases, with no changed assertions.


## 2026-09-12T02:00:59.239201+00:00 — supported diagnostic detail ready for independent review, tuner148870

PROVIDER-DETAIL-148870.md and prepared-148870/README.md describe the source-backed
boundary. Candidate manifest evidence/diagnostic-148870/candidate-manifest.json
SHA2560c13a9034aef59636214749876bb83960c18a457dc79a992cf1c6b2c15d0028f binds76 files, including
v12/worker/claude_agent.py, additive test_claude_agent.py and the successor reader.
Adapter SHA256489399897c3f0ae94f06be9da47adde3f05210fa0ecfd7faad295daf6accfe2a;
reader SHA2569f653396dd4e05a9419448de198aba9c03b5d021f7f00357e1cc54999cef11c9.

181 adapter tests,54 offline package tests and106 offline worker-entry tests pass.
The first new recursion fixture failure and duplicate discovery are retained.
Every preexisting test class/function is AST-identical; all43 prior package files
match,41 successor inherited files unchanged. Exact static source slices/offsets,
file custody, test logs, patch and spending are retained in that evidence folder.
After passing tests only explanatory source comments changed, not executable AST.

The adapter preserves the exact OAuth expiry/refresh-failure explanation and
typed HTTP400..599 where supported, with unknown cause for status alone and
explicit unavailable/withheld detail. No arbitrary prose/request-ID publication.
Old failure_reason/lifecycle/first-failure guards remain. Optional diagnostic
publication is covered for proposal1/proposal2/review-log1; successor reader
validates/reconstructs it through existing correlated no-follow custody reads.

This supersedes pending bounded implementation, not independent acceptance,
deployment or actual A/B proof. Both images still hold old source and need new
review-bound immutable provenance before future use. Direct feat review, Next ops
for exact remaining deployment/run authority and supported-detail coverage. No
image build/execution, copied-provider execution, credential/stream read, network/
model probe, fresh-run packaging, repair, retry or marker. Other explanatory text
and IDs remain unavailable; run6 discarded detail/cause cannot be reconstructed.
Cumulative listed28.337977460971555s plus uncertainty; all six failed walls
1341.1107609820174s and all limits/guards/deferrals/run5/run6 obligations remain.


## 2026-09-12T02:08:32Z — independent supported-detail acceptance, reviewer148964

Accepted candidate76-file manifest0c13a9034aef59636214749876bb83960c18a457dc79a992cf1c6b2c15d0028f
in review-2026-09-12T02-08-32Z.md. Independent181 adapter/54 package/106 worker-entry
tests pass; git diff --check passes. All43 prior package files,41 inherited successor
files and27 existing test class/function ASTs preserve accepted bytes/expectations.
Test change authority covers the nine additive adapter cases and five new reader
cases. Static native/script custody and ten source slices verified; additional
same-module error construction and text-filter evidence supports the output path.
No raw provider execution or real credential/stream/network/model access occurred.

This supersedes pending independent implementation review. The fixed OAuth
explanation, bounded typed HTTP status and explicit omissions satisfy the bounded
supported-detail collection/exclusion/retention/presentation scope; arbitrary
prose/IDs remain unavailable, status alone does not prove authentication, and
run6 discarded cause remains unknown. Lifecycle, custody and success are unchanged.
The source/helper correction is accepted, not deployed and not actual A/B proof.

Pass ops Next tune for remaining image/fresh-preparation/run authorization boundary,
not another generic planning gate. Both images still contain old adapter bytes;
authorized future builds must bind reviewed source, exact provider installation
and new provider/integration image digests; future runner binds new reader hash.
No build, image selection, fresh package, execution marker, retry or repair here.
Actual A settlement, B judges/import, causal merged observation and both terminal
Jobs remain owed. Existing budgets/guards/deferrals/run5/run6 uncertainties stand.
Independent evidence/review-148964/spending.json: current10.772683072922518s,
cumulative39.11066053389408s plus untimed/search/host/operator/billing uncertainty;
six failed walls1341.1107609820174s preserved. No double-count or reserve transfer.


## 2026-09-12T02:23:07.032Z — owner149049 preparation scope revalidated, tuner claim149053

Owner149049 accepts review-2026-09-12T02-08-32Z.md and the76-file supported-detail
candidate. Updated provider/integration image preparation and fresh run7 packaging
are authorized; model execution, retries, historical root changes and agent Git
mutations remain unauthorized. This explicitly supersedes prior pending image/
fresh-preparation authority, not the final image/input review or owner run boundary.

Tuner owns new prepared-149053, RUN7-PREPARATION-149053.md and evidence/image-preparation-149053
plus this record's current action/progress. Reuse accepted image recipes/context
from prepared-141676, replacing only the adapter with the accepted48939989 bytes.
Both images inherit the same immutable provider base; verify installed package,
installer, wrapper and native hashes against the owner copies accepted by148964.
Bind both actual immutable candidates after build, all four runner helpers, fresh
run7 identities and exact operator host preparation/validate/render commands.
No package reinstall or provider/model execution. Preserve current four-helper
fail-fast/detail boundary, A/B tasks and all1200/240/180/120s limits/resources/
custody/target/success guards and six historical runs.

Fresh root /home/sl/.local/state/baton/v12/w71879-run7; Authority
c71879b1000000000000000000000001. Test changes are confined to copied packaging
fixtures: rebase run6 identities/time/ruling to run7, preserve historical run6 replay
using its explicit original identifiers, and add bounded image provenance checks.
Record exact paths/deltas for independent review under W71830 test-change authority.
The existing accepted adapter and product tests remain unchanged.

Operational read finding: the guessed prepared-148870/operator_prepare.py path
does not exist; the actual retained operator helper is operator-prepare.sh and has
been read. No required policy, review or actual helper is unreadable. Installed
Docker copy restrictions from148686 remain an operational boundary; do not bypass
them. If building or static inspection needs operator execution, supply the exact
complete reviewable commands and retain partial outputs.
