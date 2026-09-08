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
