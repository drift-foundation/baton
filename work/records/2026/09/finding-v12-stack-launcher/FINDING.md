# Persistent v12 stack launcher

## 2026-09-16T11:40Z — owner bootstrap passes; retain a named test recipe

Owner reports `just setup` completed at /home/sl/.local/state/baton-v12-venv,
with locked dependencies hash-verified, then reports the requested bootstrap
test finished OK. Retained /tmp/w183883-bootstrap.log confirms 67 tests in
0.938s, OK. Verbatim output and attribution are OWNER-BOOTSTRAP-20260916.log
and OWNER-BOOTSTRAP-20260916.json. All ten current candidate hashes match
review-2026-09-16T11-35-36Z.md. This supplies the outstanding owner-independent
bootstrap run; no test was run by baton.prompt and no separate supervisor exit
or resource inventory is inferred from the log. Final evidence review remains.

Owner asks: "test finished ok, should this be a just cmd so we don't forget".
Selected small addition: `just test-bootstrap` under v12/, using the prepared
venv, the same focused unittest module and a bounded timeout. Expose the external
disk-backed test root explicitly with /var/tmp as this deployment's default and
preserve BATON_V12_STACK_TEST_ROOT override. Preserve failing exit status; do
not hide failures behind output capture or install dependencies implicitly.
Document this command next to setup/bootstrap. It tests fixture configuration,
not the actual installed deployment, and neither starts a live Job nor expands
the test campaign. Existing passing owner evidence need not be repeated solely
to turn its command into a recipe.

This supersedes the missing-independent-bootstrap-run action. The small recipe
addition and evidence review precede remaining concrete production setup.

## 2026-09-16 — separate setup recipe

Slawomir clarifies the venv requirement: "it should be a separate just cmd".
Expose `just setup` under v12/ to create/validate the dedicated Python 3 venv
and install locked dependencies. This is separate from start/stop/status/monitor:
those commands use the prepared interpreter and perform no installation. If
setup is missing, report the exact setup command. Keep the existing Node proof's
`just install` recipe distinct. Repeat setup must preserve persistent stack
state and refuse an incompatible existing environment rather than delete it.

## 2026-09-16 — owner requires a Python 3 virtual environment

Slawomir: "we should use a venv with python3". Confirmed for the remaining
operator setup: create a dedicated virtual environment with a Python 3
interpreter satisfying v12/python/pyproject.toml, install the locked
dependencies with hash verification, and use that environment's interpreter
for start/stop/status/monitor and all their Python children. Do not rely on
global site packages or an operator remembering to activate the environment.
Document its explicit location and repeatable one-time setup command. This
supersedes the bare ambient python3 invocation as the final operator recipe;
earlier launcher evidence remains evidence for its reviewed bytes.

## 2026-09-16T10:20Z — owner composition run passes; finish operator setup

Slawomir ran the exact two-case ValidIdleComposition command from the latest
review, using BATON_V12_STACK_TEST_ROOT=/var/tmp and timeout 180s with 10s kill
grace. Both cases report OK, 2 tests in 10.535s. The supplied terminal output
matches /tmp/w183883-composition.log, retained verbatim here as
OWNER-COMPOSITION-20260916.log. This is owner-executed independent evidence,
not another author run or a test run by baton.prompt. The reported duration is
unittest elapsed time, not a separately measured supervisor/cleanup total.

All six current candidate hashes were re-read and match the exact candidate
table in review-2026-09-16T06-57-11Z.md. That review's missing independent
composition-run evidence is now supplied. The successful test includes the
normal stop and cleared-record assertions; no separate historical process
inventory was captured by the owner log. Preserve those attribution limits.
No repeat of these tests on unchanged bytes is needed merely for handoff.

The original requested usable startup still needs concrete operator deployment
setup. STACK.md currently lists required Authority/profile/worker/Work operands
and placeholder exports; it does not create a persistent deployment for this
machine. This is the remainder of original PLAN step 3, not a new readiness
campaign. Route impl to finish bounded bootstrap/configuration preparation and
copy-paste setup/start commands, then review only that new boundary while
retaining the accepted launcher evidence. Do not report a fixture deployment
as a usable production worker pool. Separate v12 state and v11 coordination,
fresh context-free attempts and Git ownership remain as previously selected.

This entry supersedes the preceding current demand to obtain the two-case
independent run; final Work completion remains pending operator setup and its
focused review. Historical reviews and author PROGRESS remain unchanged.

Work: W183883. Canonical binding: baton:work/records/2026/09/finding-v12-stack-launcher.

## 2026-09-16 — owner selects side-by-side startup

Slawomir: "next, I need to be able to fire up our v12 montior and launch the
\"stack/scheduler\" so we can run parallel to v11". Further concrete requirement:
"under v12/ we need a jsutfile that lets us start/stop/status the stack".

Confirmed outcome: an operator can run the persistent v12 scheduler and its
read-only monitor alongside v11, using v12/justfile. Provide start, stop and
status recipes; monitor is the companion entry point for the requested viewer.
Reuse accepted v12 execution and observation surfaces. This is the selected
next work, not the previously proposed v13 hardening job.

## Observed starting point

- v12/justfile currently drives the historical Node proof and its disposable
  state; it has no persistent stack lifecycle recipes. Its default is test.
- v12/python/tools/job_manager.py has submit/status/serve. The multiworker
  serving factory is tools.stage_execution:factory; configuration is selected
  by BATON_V12_STAGE_EXECUTION_CONFIG. State and deployment operands are explicit.
- v12/python/tools/job_viewer.py consumes a status document and defaults to one
  tick. JOB-VIEWER.md requires atomic snapshot publication for refresh and the
  read-only observing_factory for exchange observation. The serving loop owns
  runtime reconciliation; a viewer must preserve stale/disconnected semantics.
- v12/testing/live_ab/deployment.py supplies useful composition examples but
  is tied to a particular two-Job proof, temporary settings and fixture tasks.
  It is not a ready persistent operator installation.
- The root justfile has no v12 stack recipes. Initial git status was clean.

## Selected boundary

Small operator lifecycle/deployment composition, with explicit separate v12
state, process ownership and configuration. Start must be repeatable without
duplicate managers. Stop targets only the owned v12 processes, retains stores
and evidence, and truthfully reports unresolved live execution. Status must
distinguish process health, store/Job observations, absence and stale data.
Monitor continuously refreshes until the operator exits; stopping the monitor
does not stop scheduling. An empty configured stack is a valid idle state.

Keep v11 services, configuration, stores and existing readiness consumers
untouched. v11 remains the project Work coordination authority; any v12 local
execution authority is separate and explicitly identified, not a copied
backlog or a competing owner of existing v11 Work. Preserve context-free fresh
attempt defaults and parked optional reuse W177936. No automatic Job submission,
live provider call, Git mutation or disposable proof run as a side effect of
start/status/monitor. Existing accepted code/evidence is reused.

The launcher must clearly document prerequisites and the one-time setup needed
for a real deployment. Do not conceal missing worker/profile/authority binding
behind a fake idle success. If existing factories cannot support empty idle
startup, identify the exact narrow gap and solve it within this scope or return
that concrete blocker; do not turn this into a general scheduler redesign.

## References

- v12/python/DEPLOYMENT.md and JOB-VIEWER.md.
- v12/python/tools/job_manager.py, stage_execution.py, job_viewer.py.
- W2 readiness review: work/records/2026/08/finding-v12-isolated-agent-workers/review-2026-09-16T04-14-53Z.md.
- W2 documentation acceptance: work/records/2026/08/finding-v12-isolated-agent-workers/review-2026-09-16T04-43-55Z.md.
- Existing multi-Job composition: work/records/2026/09/finding-v12-multi-job-deployment/DEPLOYMENT-HANDOFF-2026-09-11.md.

## 2026-09-16T05:15:54Z — independent review requests bounded corrections

Confirmed under claim183958: all five candidate hashes match the author handoff
and all32 supplied tests pass. Controlled deterministic checks nevertheless show
two concurrent starts spawning four processes with only two ownership records,
and unreadable ownership permitting a replacement while the original lives.
The real documented child command fails to import baton_v12 in this checkout;
start still returns0 and prints started. This is an import failure before config
validation, not proof of an invalid-document refusal. Static review additionally
finds stop returns0 for unresolved supervisor ownership/liveness and does not
report the requested unresolved worker execution boundary.

review-2026-09-16T05-15-54Z.md specifies R1–R4, exact code locations, correction
scope and focused regression expectations. REVIEW-EVIDENCE-183958.json preserves
the candidate hashes and observations; reproduce-review-183958.py reproduces
the checks. Reviewer total verification1.5529989219503477s includes the test
subprocess1.2311618709936738s. Author test duration1.195s remains separate;
earlier recipe duration is unknown. All reviewer children were reaped. No live
provider, engine, Job submission, v11 operation or Git mutation occurred.

This supersedes pending independent acceptance with changes requested, without
altering the selected product outcome or granting release acceptance. Return
for ordinary implementation correction and re-review. The author-reported five
unregistered test modules remain an operational finding outside this correction
scope; no broad gate or unrelated cleanup is requested. W177936 stays parked.

## 2026-09-16T06:00:07Z — correction review, claim184197

Confirmed: all five candidate digests match author EVIDENCE-183998.json and61
focused tests independently pass. Shared lifecycle admission, initial unknown
refusal and Python environment setup improve the prior candidate. Remaining
controlled counterexamples show stop/unwind deleting ownership after visibility
becomes unknown, ordinary publisher spawn failure leaving the admitted manager
live, and malformed nested snapshots crashing runtime_boundary. Static review
and a labelled stand-in readiness check show a changed observer snapshot does
not establish serving initialization. Review review-2026-09-16T06-00-07Z.md
specifies C1–C4 and supersedes full R1–R4 resolution with bounded corrections.

REVIEW-EVIDENCE-184197.json and READINESS-REVIEW-EVIDENCE-184197.json bind the
candidate, results and retained reproduction scripts. Reviewer verification
12.840890395978931s includes61 tests12.836152499017771s; separate readiness
check0.002758326008915901s. All owned children reaped. No live provider/engine,
Job submission, v11 operation, Git mutation or product/existing-test edit.

Operational finding: reviewer cannot independently execute the two disk-backed
outside-checkout composition cases under current writable roots. /tmp is tmpfs;
/var/tmp is disk-backed but outside authority. No bypass or escalation attempted.
Author63-test/19-probe evidence remains separate and preserved; an authorized
independent composition run is still needed before acceptance. Prior measured
spending and historical unknown recipe duration remain intact. Return ordinary
corrections to impl and re-review; keep W177936 parked and v11 authoritative.

## 2026-09-16T06:35:51Z — correction review narrows remaining recovery scope

Confirmed under claim184403: six author candidate hashes match,84 stack checks
and168 adjacent checks pass. C1 positive-GONE cleanup and C4 malformed/source-time
handling satisfy the reviewed cases. The scoped job_manager serving acknowledgement
was pinned before editing and preserves machine-readable stdout.

Remaining confirmed counterexamples: failure of the second manager record write
(incarnation update) occurs before rollback registration and leaves the admitted
manager live; both-live and publisher-replacement start paths report success
with an existing manager that never acknowledged initialization. These are owned
process-boundary stand-ins, not a claimed deployed-manager failure. Review
review-2026-09-16T06-35-51Z.md specifies D1/D2 and supersedes full C1–C4 completion
with verified C1/C4 and bounded remaining C2/C3 corrections.

REVIEW-EVIDENCE-184403.json and reproduce-review-184403.py bind digests, checks,
counterexamples and cleanup. Reviewer total20.8455910270568s includes84 stack
tests14.4608839469729s and168 adjacent tests6.37693740503164s. All owned children
were stopped/reaped; no live provider, engine, deployment, Job submission, v11
operation, Git mutation or product/existing-test edit. Prior costs and unknown
recipe timing are retained. The two external disk-root composition cases remain
outside this reviewer's installed write authority; author evidence stays separate
and authorized independent composition verification remains needed. Return
ordinary D1/D2 corrections to impl and re-review. W177936 stays parked.

## 2026-09-16T06:57:11Z — D1/D2 verified; concrete composition gate remains

Confirmed under claim184537: all six candidate digests match EVIDENCE-184442.json
and94 focused stack checks pass. Complete identity publication is now one owned
write, no post-spawn acknowledgement cache write remains, unwind contains failures
per process, and both inherited-manager paths require matching acknowledgement.
No further selected implementation correction is identified. Prior C1/C4 review
and168 adjacent checks against unchanged adapter bytes remain applicable.

review-2026-09-16T06-57-11Z.md supersedes the D1/D2 correction queue with verified
corrections and a concrete operational gate. REVIEW-EVIDENCE-184537.json and
verify-review-184537.py retain hashes, individual results and handle collection;
reviewer total15.599983819993213s includes testing/cleanup, no admitted handles
remain. Earlier author/reviewer costs and unknown recipe duration are preserved.

Final acceptance still needs the two independent ValidIdleComposition cases.
/tmp remains tmpfs, /var/tmp is disk-backed but outside reviewer write authority,
and the deployment excludes checkout-local mutable roots. No workaround or
managed-turn escalation attempted. Return to ops for an authorized external
disk root or independent verifier with that authority; exact command and bounded
scope are in the review. Author results are preserved separately. No live model,
engine run, Job submission, v11 operation, Git mutation or product/test edit by
reviewer. W183883 remains open; W177936 parked; v11 remains authoritative.

## 2026-09-16T10:39:48Z — setup correction review and bootstrap triage

Confirmed under reviewer claim185739: all eight candidate hashes match and29
focused environment tests pass. Offline counterexamples show the documented
`just setup PY=/path` forwards PY= as part of the executable, and a failed first
install leaves an unmarked environment that repeat setup refuses as foreign.
Review review-2026-09-16T10-39-48Z.md specifies E1/E2 and focused regressions.
REVIEW-EVIDENCE-185739.json and reproduce-review-185739.py retain exact evidence;
verification including cleanup0.12554923997959122s. No real install/provider/
engine/Job/deployment was run; owned temporary stand-in cleaned, children exited.

Triage B1: actual production choices remain unselected, but explicit required
inputs permit the already authorized bootstrap helper and deterministic tests
to proceed. This supersedes claim185653's blanket owner-input blocker on all
bootstrap implementation, not the requirement for valid inputs before activation.
Revalidate accepted /2 job_bindings, same-Work review binding, derived actors
and real stage capacity; the discovery's fixed nine-endpoint count and pool-only
characterization are not accepted specifications. Return ordinary corrections
and original step3 completion to impl, then focused review and exact ops choices.

Owner two-case composition evidence10.535s resolves the prior independent-run
gap for reviewed launcher bytes. Preserve its attribution/cleanup limits and
prior author/reviewer durations and unknowns; no repeated unchanged checks.
PROGRESS stays author-owned, W183883 open, W177936 parked, v11 authoritative.

## 2026-09-16T10:58:20Z — E1/E2 verified; bootstrap F1–F3 remain

Confirmed under reviewer claim185857: all ten candidate hashes match and67
setup/bootstrap tests pass. The selected positional-override and failed-first-
install retry corrections satisfy E1/E2. Bootstrap now exists, but its successful
tests do not validate the emitted deployment against its consumer.

Controlled offline checks using disposable v12 Authorities confirm successful
bootstrap of incomplete worker documents later refused by held_configuration;
corrupt existing configuration overwritten on repeat; a /2-to-/1 repeat dropping
a Job and changing another Job's base/target; and integration_preparation=true
accepted but omitted from output. These are local configuration-boundary results,
not production execution claims. review-2026-09-16T10-58-20Z.md specifies F1–F3
and supersedes claim185774's assertion that production selections are the only
remaining gap. Correct in the owning bootstrap/test/runbook boundary, then review.

REVIEW-EVIDENCE-185857.json and reproduce-review-185857.py retain hashes/results;
verification including cleanup0.22083405102603137s. Both temporary roots cleaned,
subprocesses completed; no actual provider/engine/Job/install/v11/Git operation.
Retain unchanged launcher evidence, owner composition10.535s, prior per-actor
spending and unknowns. PROGRESS author-owned; W183883 remains open, W177936
parked and v11 authoritative. No broader redesign or qualification is selected.

## 2026-09-16T11:14:19Z — bootstrap validation improves; G1/G2 remain

Confirmed under reviewer claim185945: ten candidate hashes match and21
negative/closed-input tests pass. The real deployment validator now refuses
incomplete workers before creation, and true integration_preparation is retained.
Controlled helper-boundary checks still show an incomplete but recognizable
binding record permits changed base/target, emitted configuration corruption is
ignored by repeat preflight, and explicit integration_preparation=null is omitted
so the consumer defaults false rather than rejecting it. No live rebind or
end-to-end valid bootstrap is claimed from these helper checks.

review-2026-09-16T11-14-19Z.md specifies G1/G2 as remaining F2/F3 scope and
supersedes the complete-resolution claim. REVIEW-EVIDENCE-185945.json and
reproduce-review-185945.py retain results and candidate; measured verification
including cleanup0.0037346489843912423s, imports excluded. Owned scratch cleaned;
no deployment/Authority mutation/provider/engine/Job/install/Git execution.

New25 ValidFixture success/repeat cases need an independent authorized external
disk-root run; reviewer /tmp is tmpfs and /var/tmp is outside write authority.
No prohibited write or escalation attempted. Author evidence remains separate.
The owner two-case launcher result stays applicable to unchanged launcher bytes
but does not verify this new bootstrap. Preserve all prior costs/unknowns and
PROGRESS ownership. Return corrections to impl then review; Work stays open,
W177936 parked, v11 authoritative.

## 2026-09-16T11:25:49Z — G2 resolved; existing configuration validation remains

Confirmed reviewer claim186022: ten hashes match;21 negative/closed-input tests
pass. Incomplete record and corrupt emitted JSON now refuse; explicit null is
preserved and refused by the accepted preparation validator, resolving G2.
Controlled helper-boundary checks still show review Work drift, unsupported
schema and /1 producer identity drift produce no conflicts. Existing document
projection omits those facts. No live rebind or complete valid bootstrap is
claimed from these stand-ins.

review-2026-09-16T11-25-49Z.md specifies H1 as the remaining G1 correction:
validate existing configuration through accepted rules and compare normalized
bindings instead of a permissive partial projection. Supersedes the full G1/G2
resolution claim, preserving improvements. REVIEW-EVIDENCE-186022.json and
reproduce-review-186022.py bind results; verification including cleanup
0.004474725050386041s, imports excluded. Owned scratch cleaned; no Authority
mutation/provider/engine/Job/install/Git or production deployment operation.

Forty new ValidFixture cases remain independently unrun because reviewer /tmp
is tmpfs and external disk roots are outside write authority. Author evidence
and prior owner launcher result remain separately attributed. Return correction
to impl then review/authorized independent verification; preserve costs/unknowns
and author PROGRESS. W183883 open, W177936 parked, v11 authoritative.

## 2026-09-16T11:35:36Z — H1 reviewed; independent bootstrap verification remains

Confirmed under reviewer claim186081: ten candidate hashes match;21 independent
negative/closed-input tests pass, real schema/review-Work refusal controls hold,
and11 isolated normalized-result comparison checks pass. H1 now reuses accepted
held_configuration and compares its normalized bindings. No further selected
implementation correction identified. Isolated comparison stand-ins are not
claimed as full valid-deployment acceptance.

review-2026-09-16T11-35-36Z.md supersedes the H1 correction queue with an explicit
ops verification action: the46 ValidFixture cases still need authorized external
disk-backed independent execution. Exact command/candidate/evidence requirements
are pinned there. Reviewer /tmp is tmpfs, external disk roots outside authority;
no prohibited write/escalation. Owner earlier launcher result remains applicable
to unchanged launcher only; author evidence stays separate. Pass ops, then feat
with independent results, not another unchanged implementation cycle.

REVIEW-EVIDENCE-186081.json and verify-review-186081.py preserve evidence;
verification including cleanup0.005015750008169562s, imports excluded. Owned
scratch cleaned; no processes/Authority mutation/provider/engine/Job/install/
production deployment/Git operation. Retain all costs/unknowns and PROGRESS
ownership. Actual production inputs and usable operator deployment remain ops
work after bootstrap acceptance. W183883 stays open, W177936 parked, v11
coordination authoritative.

## 2026-09-16T11:45Z — owner selects external installed instances

Owner agrees lifecycle commands take the same JSON and requires bootstrap to
place the instance at a destination outside source/repo. The exact current
ruling and command contract are OWNER-INSTANCE-DESTINATION-20260916.md in this
dossier. Bootstrap inputs plus explicit external destination produce instance.json;
start/status/monitor/stop all consume that emitted instance file. Include fixed
installed runtime code, databases, process records and logs, so checkout code
edits do not alter an existing instance. This explicitly supersedes earlier
manual-export/default-global-root UX and checkout-bound runtime execution.
Retain reviewed evidence for unchanged behavior, the separate setup/test-bootstrap
recipes, v11 authority and independent review. Current implementer owns folding
this newly confirmed ruling into PLAN before further affected implementation.

## 2026-09-16 — owner selects PyInstaller and an independent deployed repository

Owner confirms PyInstaller one-folder to include Python itself, and explicitly
requires self-contained distro/db/repo outside the source checkout so normal
development continues beside running Jobs. OWNER-PYINSTALLER-20260916.md is the
current precise outcome and supersession: zipapp and build/shared-venv runtime
dependence are superseded; explicit external destination and one instance.json
for all lifecycle commands remain. The distro must include actual bundled
child commands, native dependencies and assets; the repository must not depend
on development worktrees/alternates. Active reviewer folds this into PLAN and
passes the remaining implementation slice after finishing the current small
recipe/evidence review. W183883 is not complete at recipe acceptance alone.

## 2026-09-16T11:53:00Z — owner bootstrap evidence accepted; recipe I1 and bundled deployment remain

Confirmed under reviewer claim 186175: owner log supplies 67 passing bootstrap
tests in 0.938s on unchanged bootstrap bytes. Separate supervisor exit status
and resource inventory were not captured; attribution and limits retained in
OWNER-BOOTSTRAP-20260916.json. The earlier independent bootstrap-run gap is
superseded by this evidence, without claiming packaged deployment acceptance.

Thirteen focused recipe tests pass; real just dry-run confirms I1: inherited
BATON_V12_STACK_TEST_ROOT is overwritten with /var/tmp when no positional ROOT
is provided. Preserve positional > environment > default precedence and add
focused coverage. REVIEW-EVIDENCE-186175.json records outputs/hashes and
0.04717645701020956s measured reviewer verification; all subprocesses completed.
No deployment/install/provider/engine/Job/product edit occurred. Author costs
remain separate; preserve prior unknowns and evidence.

review-2026-09-16T11-53-00Z.md and current PLAN return this bounded correction
plus the confirmed remaining deployment slice to impl, then feat. Latest owner
PyInstaller one-folder ruling supersedes shared/build-venv runtime options and
requires independent distro/db/repo plus common instance.json outside checkout.
The previous recipe-only next-action plan is explicitly superseded. No extra
planning gate; actual bundled child/resource/isolation behavior needs focused
verification and independent review. Keep Work open, PROGRESS author-owned,
W177936 parked and v11 authoritative.

## 2026-09-16T12:04:20Z — I1 accepted; J1 evidence correction and packaging remain

Reviewer claim186262 matches all ten candidate hashes and verifies 22 focused
tests, four real helper CLI combinations and six isolated resolver controls.
I1 precedence and refusal behavior is accepted, superseding the correction
queue. One initial real-storage fallback case failed because this managed
boundary has no writable disk root outside checkout; it is not an independent
real-storage success claim. Exact timings and limits: REVIEW-EVIDENCE-186262.json.

J1: probes-186214.py names a recipe test under TheRecipesUseIt although it is
under TheInterpreterOverrideIsExecutable. The same selector fails with
AttributeError on pristine candidate. The claim that this probe demonstrated a
regression kill is explicitly superseded; original evidence/costs preserved.
Append an author correction alongside packaging, without another recipe-only
approval gate. review-2026-09-16T12-04-20Z.md contains details and hashes.

Packaging is still unstarted. Continue the already authorized PyInstaller
one-folder independent distro/db/repo and common instance.json implementation
using claim186214 path ownership. Dependency availability is not a completed
build. Actual bundle composition/isolation needs focused verification and
independent review. No product edits or external writes by reviewer; PROGRESS
remains author-owned. W183883 open, W177936 parked, v11 authoritative.

## 2026-09-16T12:20:20Z — J1 resolved; source dispatch verified, instance deployment incomplete

Reviewer claim186356 independently verifies the corrected J1 probe on a
pristine temporary recipe, intended reversal assertion and restored pass.
Seventeen focused dispatch/lifecycle/publication tests and seven entry-point
forwarding checks pass; all thirteen candidate hashes match. Measurement
1.6185368220321834s. review-2026-09-16T12-20-20Z.md and
REVIEW-EVIDENCE-186356.json bind the outputs and scope. This supersedes J1 as an
outstanding correction; I1 remains accepted.

Packaging is now partially implemented, superseding the earlier unstarted
status. The author reports a real build/resource imports/invalid-config manager
refusal, but no bundle artifact or raw logs remain. Independent valid packaged
instance acceptance is not supplied by this partial report. Finish the already
authorized instance/deployment slice and retain final bundle provenance/evidence.
Instance identity must cover the whole one-folder runtime, not only executable
bytes, and check resource integrity before admission.

Author timing representations disagree (handoff J1 1.291s/total28.428s versus
JSON0.125s/total27.262s); preserve and clarify rather than silently replacing.
Unmeasured frozen smoke checks are verification with unknown duration, not
excluded cost. No historical reconstruction or replenishment gate follows.
Reviewer made no product/test edits or external writes; all subprocesses ended,
retained recipe scratch is /tmp/w183883-review186356-8it19brl. Return impl then feat;
W183883 remains open, W177936 parked, v11 authoritative.

## 2026-09-16T12:35:10Z — K1–K4: instance isolation and admission are not yet established

Reviewer claim186439 matched fifteen hashes and reproduced: K1 a selector
retained at A dispatches stop into B/state after foreign path edits; K2 B runtime
verification still generates A executable argv when builds differ, and external
symlink target byte changes leave manifest/verify unchanged; K3 prepare precedes
missing-distro refusal, existing corrupt selectors can be overwritten, and
identity JSON reporting absent resources is accepted; K4 _MEIPASS covers only
distro/_internal so distro/mutable-state passes the outside-code guard.

These supersede claims that the current selector fully derives/binds its paths,
that the whole reachable runtime is protected by the manifest, and that frozen
_checkout protects every path inside distro. Direct regular byte tampering is
correctly refused; partial progress retained. review-2026-09-16T12-35-10Z.md specifies
bounded corrections and scheduled regression cases alongside remaining lifecycle,
repository, UX and bundled-evidence scope. No extra planning approval gate.

reproduce-review-186439.py and REVIEW-EVIDENCE-186439.json preserve exact controls,
substitutions, fifteen hashes and measured 0.0028278949903324246s excluding
imports/hash preflight. No real control signal/Authority/provider/engine/Job,
bundle build or product/test source edit. Scratch retained:
/tmp/w183883-review186439-2y6cthz3. Prior evidence and measured intervals/unknowns remain
separately attributed; no cumulative budget gate. Return impl then feat;
W183883 open, W177936 parked, v11 authoritative, PROGRESS author-owned.

## 2026-09-16T12:43:53Z — K4 verified; K1–K3 corrections incomplete

Claim186499 matches fifteen hashes and confirms direct-path/frozen-command/
child-link and missing-distro/existing-selector improvements. K4 protects the
whole selected onedir distro and permits instance mutable siblings. This
supersedes the claim that all K1–K4 corrections are complete with K4 verified
and three bounded remainders: K1 same-layout symlink escape still dispatches
A selector stop into B/state and wrong types escape; K2 distro root symlink is
accepted; K3 executable/resource identity is checked after prepare and copy,
and empty/arbitrary schema/native identity fields still pass.

review-2026-09-16T12-43-53Z.md, reproduce-review-186499.py and
REVIEW-EVIDENCE-186499.json preserve controls, substitutions and hashes.
Measurement 0.003370393009390682s excludes imports/hash preflight;
scratch /tmp/w183883-review186499-1ev8mcjt retained. No real control signal/Authority/
provider/engine/Job, build, external-root write or product/test source edit.
Return corrections WITH planned registered regressions and finish the existing
lifecycle/repository/UX/provenance slice; no further planning approval. Costs and
unknowns preserved; W183883 open, W177936 parked, v11 authoritative.

## 2026-09-16T12:53:30Z — selector regressions verified; bootstrap admission/custody still incomplete

Claim186560 matches sixteen hashes and independently passes all24 instance tests.
K1 read-time containment/types and K2 root-link refusal are verified; K4 remains
accepted. Bad frozen identity now refuses before prepare with no destination.
This supersedes the full K1–K3 resolution/coverage claim with narrower acceptance.

Confirmed remaining bootstrap defects: install succeeds with foreign state link
and publishes a selector read rejects; dangling selector links are overwritten;
resource identity trusts an unbound resources root and accepts unlisted native
paths; main discards the first admitted candidate and install accepts changed
bytes after prepare. Exact controls, substitutions and regression scope are in
review-2026-09-16T12-53-30Z.md, reproduce-review-186560.py and
REVIEW-EVIDENCE-186560.json. Add deterministic bootstrap regressions alongside
corrections and finish the already selected lifecycle/repo/UX/packaging evidence.
No new planning gate or partial-build-only handoff required.

Independent measurement 0.05098099901806563s excludes imports/hash checks.
Scratch retained /tmp/w183883-review186560-2bfwkv20. No actual Authority/lifecycle/build/
provider/engine/Job, external-root write or product/test edit. Author costs and
prior unknowns separately preserved. Return impl then feat; W183883 open,
W177936 parked, v11 authoritative, PROGRESS author-owned.

## 2026-09-16T13:09:22Z — original bootstrap corrections verified; destination custody can change after admission

Claim186639 matches sixteen candidate hashes and independently passes all forty
instance tests. The four static examples from review-2026-09-16T12-53-30Z.md are
addressed, superseding their outstanding status. The new sixteen tests preserve
prior assertions and add bounded admission/resource/source-drift checks.

Confirmed remaining K3: after actual admission, a newly created instance.json
is overwritten by install(admitted=...), and a newly created foreign state link
is accepted, producing a selector its reader rejects. The identity subprocess
alone is substituted; actual scratch file operations establish these interleavings,
not live concurrent execution. Source-drift refusal remains verified. Preserve
pinned source identity while revalidating destination custody, preventing selector
clobber at publication and coordinating cooperating attempts. Add deterministic
regressions and finish the existing deployment scope; no new planning gate.

review-2026-09-16T13-09-22Z.md, reproduce-review-186639.py and
REVIEW-EVIDENCE-186639.json hold exact findings, hashes, controls and acceptance.
Reviewer measurement 0.0579148480319418s excludes imports/hash preflight;
scratch /tmp/w183883-review186639-uab9ke5b retained. Author's 27.154s focused
suite and 0.589s probes remain separately attributed. No real Authority, process
control, build, provider, engine, Job, external-root write or product/test edit.
Prior costs/unknowns preserved. Return impl then feat; Work remains open,
W177936 parked, v11 authoritative, PROGRESS author-owned.

## 2026-09-16T13:20:49Z — destination-change refusals verified; publication temporary file is not owned

Claim186721 matches sixteen candidate hashes and independently passes all fifty
instance tests. Late selector and late state link examples from the prior review
now refuse while preserving foreign state, superseding their outstanding status.
Ordinary installation still reads back. Prior accepted controls remain intact.

Confirmed new K3 remainder in instance.create: a fixed instance.json.new is
written before exclusive final-name publication. A symlink at that temporary
name, present before actual admission, redirects install into overwriting a
foreign document; install reports success and publishes a symlink. A hardlinked
temporary can damage an existing selector even as create refuses and claims its
bytes were preserved. These use actual scratch filesystem operations, with only
runtime identity substituted for admit/install; no concurrency or hostile
mutation claim. The correction must own a fresh exclusive regular temporary
before writing, preserve foreign entries, and retain final-name no-clobber.
Add bounded temporary regular/symlink/hardlink regressions and finish existing
deployment scope without a new planning gate.

review-2026-09-16T13-20-49Z.md, REVIEW-EVIDENCE-186721.json and
reproduce-review-186721.py preserve exact results and hashes. Reviewer measured
0.1260618109954521s excluding imports/hash preflight; scratch retained
/tmp/w183883-review186721-a2s8q432. Author27.202s focused,0.625s probes,
0.003s scenarios stay separately attributed; all prior costs/unknowns preserved.
No product/test edit, Authority, process control, build, provider, engine, Job,
external-root write or Git mutation. Return impl then feat; Work remains open,
W177936 parked, v11 authoritative, PROGRESS author-owned.

## 2026-09-16T13:36:58Z — temporary custody resolved; installed recipe dispatch omits manifest preflight

Claim186809 matches sixteen hashes and independently passes121 focused tests
(instance58, environment56, installed-monitor7). Both prior temporary symlink/
hardlink reproductions preserve foreign bytes/entries; ordinary publication
reads back, superseding the prior defect as outstanding. Recipes and installed
monitor are now implemented, superseding their wholly unimplemented status.
Actual four-recipe forwarding passes using harmless printing executable fixtures;
this does not establish a real bundled manager/publisher/viewer lifecycle.

Confirmed K2 remainder: instance.main calls read but not verify before returning
the executable to the recipe. After changing the fixture launcher, direct verify
refuses the manifest mismatch, but actual just status runs changed bytes with
exit0. A changed resource also passes the helper. Verify before command dispatch
and retain the installed frozen identity check; add actual recipe negative tests.
Finish already-selected real bundled lifecycle, repo/base, preservation and
artifact/provenance acceptance, with docs matching installed normal UX. No new
planning gate or broader live-provider scope.

review-2026-09-16T13-36-58Z.md, REVIEW-EVIDENCE-186809.json and
reproduce-review-186809.py preserve results and hashes. Successful reviewer
harness measured 0.5808480150299147s excluding imports/hash preflight;
scratch /tmp/w183883-review186809-3rtr7lgv retained. Initial harness passed tests
but just refused recipe script creation under read-only /run/user/1000/just;
no recipe ran. Its stopwatch was not persisted (unknown duration), scratch
/tmp/w183883-review186809-gfw_1tmm retained. Corrected fixture selects owned /tmp
XDG_RUNTIME_DIR within managed authority, without escalation/external writes.
Author27.256s focused,0.541s/2.197s probes,0.003s scenarios remain separately
attributed; all prior costs/unknowns preserved. No real stack/Authority/build/
provider/engine/Job, product/test edit or Git mutation. Return impl then feat;
W183883 open, W177936 parked, v11 authoritative, PROGRESS author-owned.

## 2026-09-16T13:45:15Z — K2 dispatch correction accepted; finish real bundled deployment

Claim186872 matches sixteen hashes and independently passes123 focused tests
(instance62/environment61). Original actual just status reproduction now
refuses the changed launcher before execution (exit2, no marker), while the
unchanged runtime executes successfully and non-executing state discovery stays
available. This supersedes the outstanding K2 dispatch finding from the prior
review. No new blocking defect found in this correction. Nine added tests hold
whole-bundle helper/recipe refusals without weakening selected expectations.

review-2026-09-16T13-45-15Z.md accepts this bounded slice and directs continuation of
the existing unfinished delivery: registered real packaging smoke, valid external
credential-reference fixture and bundled manager/publisher/viewer lifecycle,
independent repo/base, two-instance/preservation/source-build independence and
retained artifact/provenance evidence. Printing fixtures are not real bundle
acceptance. No new approval campaign. Clarify residual documentation scope;
external installation/Git-owned setup beyond managed authority becomes exact
operator commands, not an escalation request or a fixture production choice.

REVIEW-EVIDENCE-186872.json and reproduce-review-186872.py retain exact hashes,
full output and controls. Reviewer measured 0.5477617380092852s excluding
imports/hash preflight; scratch /tmp/w183883-review186872-qez07pt1 retained.
Author27.547s focused and1.247s probes separately attributed; prior costs and
unknowns retained. No real stack/Authority/build/provider/engine/Job, external
write, product/test edit or Git mutation by reviewer. Return impl then feat;
W183883 open, W177936 parked, v11 authoritative, PROGRESS author-owned.

## 2026-09-16T14:06:35Z — real bundle verified; recipe omissions and repository packet remain

Claim186978 matches17 candidate hashes plus artifact-source hashes and passes133
focused tests, including9 real retained-bundle checks without skips. Build and
both installed copies match80-file digest50cc5a1bf071ce978ef6fb9d84d73312851351151c9ecf7e2a00358774c33db5.
Author two-instance idle lifecycle evidence reviewed; four reported pids are
absent. This supersedes packaging/lifecycle as wholly unimplemented, without
claiming independent restart or production/repository qualification.

Confirmed R1: bootstrap recipe unconditionally realpaths empty optional DISTRO,
failing before Python for the retained no-destination form. R2: an inherited
missing BATON_V12_STACK_DISTRO yields exit0/skipped9 at the required packaging
recipe's test boundary; the recipe does not bind the output it builds. Correct
both with actual bounded controls. No new product or planning scope required.

Both retained repo/ directories are empty; deployment inputs still carry the
fixture base and separate outside nominated_source/workspace roots. The promised
exact owner commands/input mapping are absent. Complete the concrete repository
packet and any input-binding implementation before owner routing. Retain exact
lifecycle harness/argv/environment/fixture-digest mapping with existing outputs;
do not fabricate historical evidence. review-2026-09-16T14-06-35Z.md gives next scope.

REVIEW-EVIDENCE-186978.json and reproduce-review-186978.py preserve results.
Reviewer successful 2.6237212599953637s, source-hash preflight excluded;
scratch /tmp/w183883-review186978-dihqyrkt retained. First harness133 tests passed
but expected the wrong realpath wording; tool wall2.511310005s, internal duration
unknown, scratch /tmp/w183883-review186978-26wovo8p retained. Author29.559s focused,
7.194s lifecycle,3.683s source probes,17.09s build probes remain separate; final
standalone build duration and prior unknowns preserved, no cumulative gate.
No reviewer rebuild/actual stack control/credential or store read/Authority/
provider/engine/Job/external-root write/product edit/Git mutation. Return impl
then feat; W183883 open, W177936 parked, v11 authoritative, PROGRESS author-owned.

## 2026-09-16T14:26:38Z — recipe corrections accepted; repository, provenance and cleanup remain

Claim187086 independently passes157 tests (instance70/environment68/packaging9/
repository-report10), no skips. All17 candidate hashes match. Build and both
installed copies match retained80-file digest
e142ba6d15e23726932114e5b49075ee326aaa47fe74c879c7fe9cbe45877ea3.
This explicitly supersedes prior R1/R2 as outstanding: omitted DISTRO reaches
the helper, and the required packaging gate binds its built output and fails
rather than skips when missing. Prior accepted corrections remain accepted.

Confirmed remaining packet defect: only external target clone is prepared;
destination/repo remains empty although now integration_workspace. Reconciliation
requires a real workspace Git common directory before its first fetch. Worker
source/mutable-storage bindings and owner-selected independent deployed Job
repository still need the complete role/path mapping. The author's assertion
that target must be outside and outlive the instance does not supersede the
owner's selected repo layout. Prepare the required owner-only commands and
fail-closed base/independence verification before owner routing.

Confirmed provenance discrepancy: ARTIFACT-MANIFEST-187015.json records different
bootstrap.py and STACK.md source hashes from the current candidate. Bundle hashes
match, but that does not establish which source produced them. Preserve and
explain the manifest with evidence; changed executable behavior requires its
final built acceptance, documentation/comment-only drift needs an explicit
disposition. Do not silently rewrite historical artifact provenance.

Confirmed harness defect with mocked commands: timeout at first status after
two starts escapes without either stop. Selector/library restoration also lacks
finally protection by inspection. This is not an observed live leak. Preserve
the original successful run and supply exception-safe restoration/exact owned
cleanup, checked outcomes and failure evidence, verified by injected failures.
Author's four reported pids are currently absent; bundled library bytes match.

review-2026-09-16T14-26-38Z.md gives bounded next scope, backed by
REVIEW-EVIDENCE-187086.json and reproduce-review-187086.py. Reviewer measured
3.261850885988679s including hashes; unittest3.033s. Scratch
/tmp/w183883-review187086-h3qh2yv_ retained. Author30.191s focused,7.219s lifecycle,
28.886s reversal and unknown separate build durations remain separately
attributed; all prior costs preserved without cumulative gate. No reviewer
rebuild/actual stack control/credential or store read/Authority/provider/engine/
Job/external-root write/product or test edit/Git mutation. Return impl then
feat; W183883 open, W177936 parked, v11 authoritative, PROGRESS author-owned.

## 2026-09-16T14:40:22Z — current artifact accepted; packet and cleanup still incomplete

Claim187184 matches all17 candidate hashes and all new manifest source hashes.
Three80-file copies match8f4a59ea380263b3d82ec156c666b6c7c393850a401fbe75ef92321fd9bfcfd8.
21 focused tests pass (repository12/packaging9), no skips. This supersedes the
prior current-artifact mismatch as outstanding. Historical explanation still
needs accuracy: prior stack.py hash matched and repository already ran then;
the prior mismatches were bootstrap.py/STACK.md, not this claim's new warning.

The workspace clone is now documented. The packet still explicitly places
target/source/mutable worker storage outside destination, contrary to the
selected contained Job repo and mutable state. Finish a compliant separate-role
layout, exact preparation order and emitted-input mapping before owner routing.
Confirmed shell defects with Git read results simulated: workspace stat failure
prints errors but returns0; workspace alternates also pass. Explicitly check
each read and each required repository, and stop claiming remote listing proves
absence of push capability. No actual Git operation in these reproductions.

Confirmed harness progress: injected after-starts exception now stops both
instances and exits2. Confirmed remaining H1 via subprocess mocks and scratch
files: status timeout returns0/failure null; nonzero stops plus reported survivor
still permit library tampering and return0; FileNotFoundError during cleanup
aborts before second-instance stop and emits no JSON. No real stack/library
was affected. Require checked outcomes, stopped proof before mutation,
per-action cleanup error isolation and preserved failure evidence. Old successful
lifecycle results remain valid bounded author observations, not proof of these
uncovered failure paths. Twelve reported pids are currently absent.

review-2026-09-16T14-40-22Z.md and REVIEW-EVIDENCE-187184.json plus
reproduce-review-187184.py give exact scope/results. Reviewer measured
2.1951854529906996s including audit; unittest1.916s. Scratch
/tmp/w183883-review187184-w8735sfp retained. Author30.153s focused,7.37s lifecycle,
28.295s reversals, approximately7s/injected-run estimates and unknown standalone
build duration preserved separately; all prior costs/unknowns retained. No
rebuild/actual stack control/Git operation/credential or store read/provider/
engine/Job/external-root write/product or test edit by reviewer. Return impl
then feat; W183883 open, W177936 parked, v11 authoritative, PROGRESS author-owned.

## 2026-09-16T14:54:21Z — placement accepted; incomplete pid knowledge is not stopped proof

Claim187271 matches all17 unchanged candidate hashes and current manifest source
hashes; three80-file bundle copies retain8f4a59ea380263b3d82ec156c666b6c7c393850a401fbe75ef92321fd9bfcfd8.
Prior product acceptance reused. Nine packet scenarios independently pass their
intended results. This supersedes the mandatory external-placement contradiction
and previously reproduced workspace-alternates/unchecked-comparison findings as
outstanding. Source/target/workspace and worker storage now map inside destination.
Remote reporting and historical source-drift chronology are corrected.

Seven independent lifecycle boundary cases confirm status timeout and stop
OSError now produce JSON/exit2 with both cleanup attempts. H1 narrows: already-
running output or timed-out start leaves no captured pids; PermissionError in
alive is treated as absent. Each control with simulated live workers and failed
stops still mutates runtime bytes before its final failure. Treat uncertainty
as a reason to skip; distinguish this run's ownership from pre-existing state.
No real runtime was affected. Another control sets selector_unchanged=false
after a simulated bootstrap refusal yet exits0/ok=true; preservation must be an
asserted result. These are the existing cleanup/preservation obligations.

The packet's before-bootstrap order is concrete; its after-bootstrap advice is
not valid with an absent nominated source. bootstrap validation reaches
single_worker._held and nominate_source, which independently refuses that absent
directory. Correct the order without weakening product preflight. Keep owner
source/base choices explicit and repository mutation owner-only.

review-2026-09-16T14-54-21Z.md, REVIEW-EVIDENCE-187271.json and
reproduce-review-187271.py retain exact evidence. Reviewer0.4329486200003885s
including audit; scratch /tmp/w183883-review187271-og6yiv0d retained. Author
30.309s focused,7.398s normal lifecycle and approximate boundary/packet timings
remain separately attributed; build-true metadata contradicts the no-build
handoff and needs factual correction. All prior costs/unknowns preserved.
Four reported normal-run pids are absent. No reviewer build/actual stack control/
Git/provider/engine/Job/credential or store read/external-root write/product or
test edit. Return impl then feat for narrowed corrections; W183883 open,
W177936 parked, v11 authoritative, PROGRESS author-owned.

## 2026-09-16T15:04:03Z — one owned instance must not admit a two-instance lifecycle

Claim187334 matches all17 unchanged candidate hashes; prior product/artifact
acceptance reused. H1b preservation assertion independently fails a changed
selector; O3 packet now orders sources before bootstrap; build metadata correction
is explicit. These are accepted and supersede their outstanding prior status.
Runtime library corruption removed, prior mismatch evidence retained.

Confirmed remaining H1a with seven mocked-boundary scenarios: lifecycle only
checks `if not owned`, allowing one complete instance to admit operations on
the other. A fresh/B running or unknown corrupts B selector and stops B though
only A is claimed. Reverse order stops unclaimed A. One timed-out start also
continues selector mutation. Both-refused safely stops nothing and the positive
case passes; global injections applying to both sides miss the mixed boundary.
Require complete accepted identity for both before any shared lifecycle work,
otherwise exit the demonstration into filtered bounded cleanup. No real process
or runtime was touched in reproduction; ordinary scratch files only.

review-2026-09-16T15-04-03Z.md, REVIEW-EVIDENCE-187334.json and
reproduce-review-187334.py retain exact scope/results. Reviewer
0.018344615993555635s including hashes; scratch
/tmp/w183883-review187334-gi4oyjdf retained. Author7.557s normal lifecycle remains
separate; boundary and packet estimates remain estimates. Four reported pids
absent. No reviewer product/test edit, real stack/build/Git/provider/engine/Job,
credential/store read or external write. Return impl then feat for this one
correction, then concrete owner packet routing after acceptance. All prior costs
preserved; W183883 open, W177936 parked, v11 authoritative, PROGRESS author-owned.

## 2026-09-16T15:11:36Z — final harness correction accepted; concrete owner packet ready

Claim187385 independently accepts the remaining H1a correction, superseding its
outstanding status in review-2026-09-16T15-04-03Z.md. Nine deterministic scenarios
exercise the retained harness with mocked subprocess/status results: positive,
both-running, destructive refusal, both mixed running orders, unknown on either
side, and start timeout on either side. Both complete identities are now required
before shared lifecycle work; cleanup stops only claimed instances/attempts.
All17 candidate hashes match; unchanged product/artifact acceptance is reused.

Clarification superseding claim187356 single-gate/no-stop prose: `touched` tracks
normal-path operations, while cleanup directly issues stops over `claimed`.
Empty `touched` is not absence of cleanup; full independent call traces verify
no stop of the refused instance. No further code correction is needed for that
wording. Review and evidence: review-2026-09-16T15-11-36Z.md,
REVIEW-EVIDENCE-187385.json, reproduce-review-187385.py.

The next action is owner operations using OPERATOR-INDEPENDENT-REPOSITORY.md:
actual source/base/destination/reference/observer/input selections, independent
owner-created target/workspace/worker-source repositories before bootstrap,
then selected input mapping, read-only verification output and runtime identity
back to review. Retained empty repository fixtures are idle runtime evidence,
not production integration qualification. W183883 stays open; W177936 parked;
v11 authoritative. No live Job/provider/engine execution selected.

Reviewer0.02227956900605932s includes nine scenarios/hash audit; author7.569s
normal lifecycle and eleven boundary-control estimates remain separately
attributed. All prior costs/unknowns preserved. Reported four normal-run PIDs
absent; scratch /tmp/w183883-review187385-zpjv4hb5 retained. No reviewer product/
test edit, actual stack/build/Git/provider/engine/Job, credential/store read or
external write; PROGRESS author-owned.

## 2026-09-16 — owner directs complete bootstrap and standalone destination justfile

Owner explicitly selects finishing the two-argument bootstrap, including bundled
distro, databases and independent repositories. Owner then requires deployed
lifecycle to need at most the destination and selects a justfile inside that
destination. OWNER-STANDALONE-INTERFACE-20260916.md pins the exact interface:
bootstrap INPUTS DESTINATION; then cd DESTINATION and just start/status/monitor/
stop. Internal instance.json is resolved automatically. This supersedes public
JSON operands, mandatory third DISTRO argument and manual clone prerequisites
as the delivered owner workflow. Agent Git ownership restrictions remain;
implement owner-run repository preparation without performing agent Git mutations.
Current PLAN returns bounded completion to impl then independent review; Work
remains open. No live Job/provider or new planning campaign selected.

## 2026-09-16T18:45:20Z — repository-enabled bootstrap not yet usable

Independent claim188542 reviews the owner-selected standalone interface, not
the superseded manual-clone packet. The public two-argument install and deployed
justfile shape are present. Changes requested in review-2026-09-16T18-45-20Z.md:

- R1 Confirmed: repository_source is copied from bootstrap OPTIONAL into the
  closed stage configuration. Otherwise accepted input issues five simulated
  clones, then schema validation refuses; no selector is published.
- R2 Confirmed: cloning precedes held structural validation. Source-only input
  issues two clones before missing-input refusal. Worker ID x/../../../escape
  yields a clone target outside the selected destination, reproduced entirely
  with ordinary /tmp fixtures and a substituted runner.
- R3 Confirmed: custody only rejects a symlink at justfile; an existing regular
  file is overwritten by successful install. Preserve it and publish exclusively.
- R4 Confirmed mapping mismatch: fixed prepared repository paths can differ
  from preserved explicit target/workspace/nominated_source selections; the
  checks prove the unused paths. Operational failure after R1 is inferred.
  Align preparation/proof with the emitted in-destination path set or refuse
  incompatible explicit selections before effects. Keep mutable storage local.

These supersede any claim188434 interpretation that the source-enabled command
is ready for owner execution. Reviewer evidence and six-case reproducer are
REVIEW-EVIDENCE-188542.json and reproduce-review-188542.py. All17 candidate hashes
match. REVIEW-ARTIFACT-188542.json records matching build/installed80-file bundles,
f9be5d2c03599d3cb912b5c7fc9c8bfdfefd00846190f105fa10da18f2a77e86;
selector agrees, and author PIDs3930002/3930003 are absent.

Operational finding: REVIEW-TESTS-188542.json records236 focused cases,188 pass
and48 failures in fixture setup, all because no writable disk-backed external
root is available in this managed context (/tmp tmpfs, /var/tmp and cache not
writable). No resource-policy workaround, actual Git or real stack run. This
limits independent suite coverage; it is not evidence of48 product defects.
Author handoff349 versus evidence358 includes a9-packaging-count discrepancy;
correct the reporting without another run solely for that purpose.

Measured reviewer focused3.0584828489809297s, reproduction/candidate audit
0.011346058046910912s, artifact/PID audit0.03480301599483937s. Author30.169s focused,
2.588s probes,5.66s lifecycle and two builds with unknown elapsed durations stay
separate; all older costs/unknowns preserved. Scratch
/tmp/w183883-review188542-xtkbx548 retained. No reviewer product/test edits,
Authority/store open, credential read, Git mutation, live provider/engine/Job or
external destination write. Return bounded corrections impl then feat; owner
production selections remain explicit, W183883 open, W177936 parked and v11
unchanged. PROGRESS author-owned.

## 2026-09-16T19:00:59Z — direct corrections accepted; three remaining boundaries

Claim188639 accepts R1 installer-only schema correction, R2 missing-input and
traversal refusal before effects, R3 preservation of existing/racing foreign
justfiles, and R4 repository-path mismatch refusal. Those subcases supersede
outstanding status in review-2026-09-16T18-45-20Z.md. Prior R1 failed validation
before Authority composition, correcting the author's composed-Authority prose.

Remaining confirmed cases, same review scope: R2 custody is checked before
waiting for the clone lock, not after acquiring it. Deterministic lock-boundary
injection of a completed foreign install still permits five clone calls. R3 a
transient selector publication OSError leaves the attempt's justfile, removes
runtime, and blocks retry with no selector; contain/report partial state and
safely unwind owned material or supply an explicit supported retry outcome.
R4 repositories_agree ignores workspace_storage, so external shared storage is
accepted by repository preparation and emitted unchanged. Enforce destination
isolation while preserving any intentional accepted intra-instance sharing.
No credential relocation, new installer framework or approval gate is requested.

Exact evidence: review-2026-09-16T19-00-59Z.md, REVIEW-EVIDENCE-188639.json and
reproduce-review-188639.py. Ten observations use ordinary scratch, inert runtime
identity, fake repository runner and real validators where stated. Scratch
/tmp/w183883-review188639-z1wf43bi retained. No actual Git, Authority/store open,
credential read, live stack/provider/engine/Job or external write.107 tests pass
(98 instance,9 required real packaging); previously unavailable disk-backed
bootstrap fixtures not rerun. All17 candidate hashes match. Current80-file build
0c0765fe070f9ff00cbe8afdcff3175959056d9ccb7b8ee4f88f8f25c75ebd11;
new author live claim lacks an exact destination/transcript in supplied evidence,
so not independently reverified. Retain its existing locator/transcript next time.

Reviewer seconds: reproduction/audit0.13164438703097403, tests2.23406296398025,
manifest0.01697837800020352. Author30.199s focused,3.239s probes, one build/current
live elapsed unknown remain separate; prior costs/unknowns preserved. Current
370-test count consistent; old349/358 discrepancy corrected by author. Return
impl then feat with R2/R3/R4 narrowed above. W183883 open, W177936 parked, v11
unchanged, PROGRESS author-owned.

## 2026-09-16T19:12:39Z — custody/storage accepted; R3 ownership interval remains

Claim188711 accepts R2 under-lock custody (zero clones after destination taken)
and R4 destination-local storage derivation, external/resolved-escape refusal
and valid local sharing. Their prior outstanding status is superseded. R3 normal
selector failure now unwinds own completed justfile and retry succeeds.

Confirmed remaining R3: wrote_justfile is set after write/close, so an injected
partial-write failure leaves24 bytes, no runtime/selector, and blocks retry.
A separate replacement-after-create injection causes cleanup to delete the
foreign replacement because a boolean/lexists is mistaken for current identity.
Track ownership at exclusive creation and through cleanup, preserve/report
foreign or uncertain paths, and contain/report bounded failure/retry honestly.
These are the same partial-failure and replacement-preservation obligations,
not a new adversarial filesystem-protection requirement.

review-2026-09-16T19-12-39Z.md, REVIEW-EVIDENCE-188711.json and
reproduce-review-188711.py retain eight observations.116 tests pass (107 instance,
9 required real packaging); inaccessible disk-backed bootstrap fixtures not
rerun. All17 hashes match. Build/installed80-file bundle and selector match
 e850fe8cb9d7b36b21598ac326e9aed9ff6b3d581092f8c60f26366bf72c55c6.
Exact author destination /var/tmp/w183883-standalone-188671/deployment and
INSTALL-188671.log supplied; repository-free idle evidence, not real Git
preparation. Lifecycle remains author-reported, no reviewer live run.

Reviewer measured0.125907837995328s reproduction/hash audit,2.3469101429800503s
focused tests,0.031989169016014785s artifacts. Author30.233s focused,3.524s probes,
one build/live duration unreported remain separate; all older costs/unknowns
preserved. Scratch /tmp/w183883-review188711-ix50myxq retained. No reviewer
product/test edit, actual Git, Authority/store or credential read, provider/
engine/Job/live stack or external-destination write. Return one R3 correction
impl then feat; W183883 open, W177936 parked, v11 unchanged, PROGRESS author-owned.

## 2026-09-16T19:20:14Z — ownership accepted; public refusal still missing

Claim188763 independently accepts partial-write cleanup/retry and preservation
of a replacement after exclusive create. Identity-based cleanup and all112
instance tests pass; earlier R1/R2/R4 remain accepted. These supersede previous
outstanding ownership defects. Nine independent observations retained in
REVIEW-EVIDENCE-188763.json and reproduce-review-188763.py.

One previously requested R3 portion remains: actual main catches only
BootstrapRefusal, so expected OSError from installation escapes as traceback
after successful cleanup. Injected selector I/O failure leaves neither runtime
nor justfile, preserves cleanup diagnostics, but returns no bounded refusal.
This is a medium-severity public error-boundary issue, not false success or
residual-data loss. Keep helper exception contract if useful; handle expected
installation OSError at public main with useful refusal/return2 and one focused
regression. No other implementation correction requested.

Review review-2026-09-16T19-20-14Z.md documents limits: prepare is substituted to
avoid Authority composition; real main/install/cleanup run against inert runtime,
no actual Git/provider/engine/Job/live stack, store/credential read or external
write. No product/test edits. Scratch /tmp/w183883-review188763-dfbmo0oq retained.
All17 hashes match. Reviewer0.12674616603180766s reproduction/audit and
0.4377329840208404s tests; author30.271s focused/4.205s probes separate; all history
preserved. No new build claimed: prior188671 runtime remains prior-version
interface evidence, and owner two-operand bootstrap will build final source.
Return tiny main-boundary fix impl then feat, no unchanged rebuild/live rerun
needed solely for handoff. W183883 open, W177936 parked, v11 unchanged.

## 2026-09-16T19:25:41Z — public error boundary accepted; false cleanup summary remains

Claim188803 accepts OSError refusal/return2 and TypeError propagation, superseding
the previous uncontained-public-error finding. Two new focused tests pass. Earlier
R1/R2/R4 and R3 ownership/retry acceptance remain. All17 hashes match.

Confirmed one narrow reporting defect: main unconditionally says "Anything this
attempt made was unwound and reported above". Actual main/install/cleanup with
selector OSError plus unlink PermissionError reports the justfile still present,
then appends that false blanket summary; the file indeed remains. Replace the
assertion with a pointer to actual removed/retained-path diagnostics and add one
public cleanup-failure regression. No new cleanup algorithm or other product
change requested. Exact review: review-2026-09-16T19-25-41Z.md.

Ten observations in REVIEW-EVIDENCE-188803.json/reproduce-review-188803.py;
prepare alone substituted to avoid Authority composition. Reviewer0.1327388189965859s
reproduction/audit and0.1678872579941526s tests. Author30.305s focused/2.955s probes
separate; no build, prior188671 bundle remains prior-source interface evidence.
All history/unknowns preserved. Scratch /tmp/w183883-review188803-_2lfll03 retained.
No reviewer product/test edit, actual Git, Authority/store/credential read,
provider/engine/Job/live stack or external write. Return message plus one regression
impl then feat; no unchanged suite/build/live repeat needed. W183883 open,
W177936 parked, v11 unchanged, PROGRESS author-owned.

## 2026-09-16T19:31:51Z — implementation accepted; stale operator-guide sections remain

Claim188837 accepts the final truthful cleanup pointer. Three focused public
checks and ten independent scenarios pass, all17 hashes match. All outstanding
R1–R4 implementation defects are superseded as resolved. No further code edit
requested. Evidence REVIEW-EVIDENCE-188837.json, REVIEW-TESTS-188837.json,
reproduce-review-188837.py; exact review review-2026-09-16T19-31-51Z.md.

While preparing concrete owner handoff, confirmed v12/STACK.md still has stale
later sections: mandatory-looking third-distro workflow at178–190, JSON lifecycle
operands at212–224/240 (current wrappers append /justfile to a DIRECTORY), and
manual-target-preparation/no-derived-target claims at226–240. No repository_source
mention exists anywhere in the guide. Top-level interface is correct, so the
product guide contradicts itself. Finish this bounded documentation-only part
of the selected interface; no new code/test/build/live run. OWNER-READY-188837.md
supplies the reviewed concrete owner command/input/evidence packet and explicitly
supersedes manual pre-clone execution instructions. Product docs must stand alone.

Reviewer0.1291853139991872s reproduction/hash,0.1697127310326323s tests; author
30.241s focused/2.332s probe separate, all history/unknowns preserved. Scratch
/tmp/w183883-review188837-sj0q6wll retained. No reviewer product/test edits,
actual Git, Authority/store/credential read, live stack/provider/engine/Job or
external write. No build;188671 retained runtime predates final failure changes;
owner two-operand bootstrap builds final source. Return guide correction impl
then feat, then ops for remaining actual production choices and owner execution.
W183883 open, W177936 parked, v11 unchanged; PROGRESS author-owned.

## 2026-09-16T19:39:47Z — guide accepted; owner execution ready

Claim188889 accepts the documentation-only correction in review-2026-09-16T19-39-47Z.md.
This explicitly supersedes the outstanding guide task from19:31:51Z; earlier
implementation acceptance stands. Commands now use two bootstrap operands and
the destination-local lifecycle; repository_source preparation, derived paths,
local storage, explicit owner choices and no-source limits are documented.
All17 hashes match EVIDENCE-188860; only STACK.md changed since accepted188818.
No code/test edit or reviewer test/build/live run. Independent hash audit
0.0009302190155722201s in REVIEW-EVIDENCE-188889.json. Author69 environment tests,
0.839s, are reported evidence despite the stale generic no-suite sentence; the
review records that clarification and inherited provenance prose explicitly.

Route ops then feat with OWNER-READY-188837.md: owner selects actual source/full
base/reference/observer/complete inputs/destination and runs the two-operand
bootstrap, returning nonsecret configuration and execution evidence. No pre-clone
or new planning gate. Packet opening guide-pending status superseded here.
Prior188671 bundle remains historical and finalsource is built by owner command;
external disk-fixture and simulated-repository verification limits preserved.
W183883 open, W177936 parked, v11 unchanged; PROGRESS author-owned.

## 2026-09-16 — confirmed version module and packaged commit/dirty stamp

Owner confirms version.py as application version authority and --version output
with packaging-time commit/dirty state. Dirty deployments are allowed; deployed
commands do not consult the original checkout. OWNER-VERSION-STAMP-20260916.md
pins exact scope and supersedes arbitrary label/commit-as-version. Build source
is inferred from the repository containing v12/justfile; the source path is not
required in deployed configuration. Keep per-Job immutable bases distinct from
application build version. PLAN routes this bounded delta to impl then review,
retaining prior acceptance and pending actual owner deployment. No Git mutation
or new clean-tree/release approval gate.

## 2026-09-16T21:21:54Z — version verified; stamping and recipe gaps

Claim189445 review review-2026-09-16T21-21-54Z.md: version authority and installed --version
work with no Git on PATH; recorded/built/installed stamps agree,81-file manifest
32b81cd3b46149bbc90ca6116f56b2e9540d789b1a5b989600098f12be63a38a matches,
all21 candidate hashes match.149 focused tests pass. Unchanged prior acceptance
stands; owner VERSION ruling supersedes old repository_source JSON packet.

Confirmed V1: status --porcelain honors status.showUntrackedFiles=no, omitting
ordinary untracked source; isolated actual status read plus capture returns clean.
Force the selected ordinary-untracked boundary independently of this setting.
Confirmed V2: build/out, build/work and packaging/build-stamp.json are untracked,
not ignored as code/tests assume; generated artifacts can dirty later captures.
Use a narrow generated-artifact boundary preserving actual untracked source.
Confirmed V3: guide option examples put --no-repositories/--repository-source in
DISTRO and fail to forward the intended option. Actual just dry runs retain exact
expansions. Correct recipe/docs agreement and test the wrapper, no clones needed.
Return bounded corrections impl then feat; detailed paths/acceptance in review.

REVIEW-EVIDENCE-189445.json/reproduce-review-189445.py retain observations;
REVIEW-TESTS-189445.json retains149 passes. Reviewer tests2.6618858630536124s,
audit0.12422490800963715s; author31.876s focused/1.13s probes, unknown build time
and all prior costs preserved. No reviewer rebuild/live lifecycle/Job/provider/
engine/Git mutation, store/credential read or product/test edit. Existing external
disk-fixture limitation stands. Owner production bootstrap still pending;
W183883 open, W177936 parked, v11 unchanged; PROGRESS author-owned.

## 2026-09-16T21:31:10Z — stamp corrections accepted; hidden test rebuild

Claim189507 review review-2026-09-16T21-31-10Z.md accepts V1/V2 and original V3 fixes,
superseding their outstanding status; all21 hashes match and29 focused checks pass.
Confirmed new test_environment documented-form test invokes just build before
missing-input refusal, including pip/PyInstaller. Do not rerun unchanged; substitute
the nested build boundary while proving actual argv. Prior no-build claim needs an
append-only correction: current build81d45b33e6009ff623737e1c330c4c4d3e662fa6811f781a13d5558fabdc6270
has new stamp field; retained install32b81cd3... remains previous logic. Actual
build count/separate durations unknown. Reviewer did not rebuild anything.

New optional direct-helper example also resolves distro one directory too deep
and uses ambient Python. Correct/remove it, retaining prepared interpreter and
build/out/distro from v12/python. Return only test/docs/evidence corrections impl
then feat; no stamp/runtime redesign or real rebuild/live campaign needed.
REVIEW-EVIDENCE-189507.json and REVIEW-TESTS-189507.json retain evidence;
audit0.03199005004717037s, tests0.044590805016923696s. Author38.504s focused/8.068s
probes and prior unknowns preserved;421 per-module total versus420 narrative noted.
W183883 open for owner delivery after acceptance, W177936 parked, v11 unchanged.

## 2026-09-16T21:42:31Z — final corrections accepted; owner packet current

Claim189577 accepts both corrections in review-2026-09-16T21-42-31Z.md, superseding their
outstanding status. Nested builds are substituted in recipe coverage; the guide
uses the prepared interpreter and correct build/out/distro path. Historical
no-build/count claims are explicitly corrected. All21 candidate hashes match;
9 recipe tests pass and independent complete before/after manifests confirm both
current81d45b33... and retained32b81cd3... bundles unchanged. Directory mtime
alone is not byte proof; manifest evidence supplies it for this review run.

OWNER-READY-189577.md supersedes prior execution packets with inferred-source
bootstrap, actual owner inputs and evidence return. Route ops then feat. No further
implementation/test/docs edit, manual clone prerequisite, new planning gate or
live campaign. Reviewer measured0.8180373870418407s total including
0.7567476470139809s tests; author31.634s focused/1.212s probes separate and all
history/unknowns preserved. No reviewer real build/clone/lifecycle/Job/provider/
engine/store/credential operation. Disk-backed fixture availability limit stands.
W183883 open pending owner execution/resolution, W177936 parked, v11 unchanged.

## 2026-09-16 — owner correction: a fresh install has zero Jobs

Observed in bootstrap.REQUIRED/_JOB and STACK.md: installation demands a jobs
list with Work, immutable base, target and source-worker bindings. After inspecting
the input contract, Slawomir explicitly rejected requiring any Job for a fresh
installation and confirmed the empty-instance correction.

OWNER-FRESH-INSTALL-20260916.md is now authoritative. Bootstrap generates and
persists identity, initializes empty databases and instance settings, installs
the standalone bundle/justfile, and starts a real idle scheduler/monitor with
zero Jobs. Job-specific bindings belong at Job creation, with no fabricated seed
Work/Jobs. This explicitly supersedes OWNER-READY-189577.md's preselected-Job gate
and the preceding no-further-implementation/owner-execution-only conclusion.
Earlier component acceptance/evidence is retained. PLAN now selects bounded
bootstrap/runtime correction, focused deterministic checks and accurate minimal
instance inputs, routed impl then feat. No product edits or tests by prompt.

## 2026-09-16T22:27:59Z — fresh-install review: incomplete lifecycle and unsafe identity reuse

Claim189832 review review-2026-09-16T22-27-59Z.md withholds fresh-install sign-off. Author
correctly reports no fresh install/real idle lifecycle. Confirmed current nonempty
worker/pool requirements and Work-sealed manifests. The owner already selected
minimal real empty lifecycle; treating all necessary empty-capacity handling as
excluded generic scheduling is superseded as scope interpretation by this review.
A broad manifest/assignment relocation is not established as necessary for idle
initialization. Research direction: no-capacity instance composition using actual
manager/observer/store behavior, failing closed on any unconfigured existing work.
Preserve configured execution contracts and report later-Job limits accurately.

Confirmed new guide minimal block is invalid JSON (bare ellipsis), only tested by
key names; later example still supplies refused authority_uuid. Require runnable
no-Job inputs and actual idle acceptance. Also confirmed authority-identity.json
is missing from custody and read through symlinks, including exclusive-create
collision fallback. Two destinations accept one externally linked identity.
Refuse unsafe records before effects and preserve foreign links/bytes.

Five existing identity unit tests pass; changed hashes match. Independent evidence
REVIEW-EVIDENCE-189832.json/reproduce-review-189832.py. Scratch
/tmp/w183883-review189832-94czecyn retained; no Authority/Job/control store opened.
Audit0.0010764109902083874s, tests0.181396814994514s; author31.431s focused/9.878s
probes and all unknowns preserved. No reviewer build/clone/provider/engine/Job or
product/test edit. Return bounded completion impl then feat, no owner production
run or superseded Job-input gate. W183883 open, W177936 parked, v11 unchanged.

## 2026-09-16T22:36:58Z — original link defect resolved; lifecycle still outstanding

Claim189893 review review-2026-09-16T22-36-58Z.md accepts original F3 symlink/reuse/collision
correction;9 tests pass and changed hashes match. F2 overclaim corrected but no
runnable JSON/F1 lifecycle yet. Planning clarification within owner scope: mint
no stage sessions with no Work/capacity; do not introduce new deployment-scoped
receipt capabilities. Minimal empty/deferred pool attachment is an implementation
choice subject to real recovery/observation and fail-closed unexpected-work checks,
not a new product-approval gate. Prioritize actual empty lifecycle and guide now.

Confirmed new reader details: FIFO passes custody and blocks at O_RDONLY before
fstat (2s subprocess killed/reaped); reading only65536 bytes accepts invalid
trailing content beyond that boundary. Bound/reject special files and oversize
records without following or modifying foreign state. Exact evidence in
REVIEW-EVIDENCE-189893.json/reproduce-review-189893.py; scratch
/tmp/w183883-review189893-p732quah retained, no live helper remains.
Audit2.0038832249701954s includes FIFO2.0026056300266646s;tests0.17559671198250726s.
Author31.311s focused/13.173s probes and all prior unknowns preserved. No reviewer
build/clone/Authority/Job/control/credential operation or product/test edit.
Return bounded completion impl then feat; no owner production run. W183883 open,
W177936 parked, v11 unchanged; PROGRESS implementer-owned.

## 2026-09-16T22:58:33Z — source idle works; empty recovery misses control work

Claim190015 review review-2026-09-16T22-58-33Z.md accepts F3 FIFO/oversize fixes
and real source-run empty lifecycle, superseding those outstanding statuses.
16 focused checks pass and five candidate hashes match. The lifecycle tests call
prepare and source tools.stack; they do not install a runtime/selector/justfile.
Correct the standalone-install overclaim and supply focused installed acceptance.

Confirmed through real v12 fixture APIs: an accepted control offer present before
or introduced after empty composition remains recoverable, but manager.reconcile
reports an empty recovery result. Pooled recovery loops over zero workers and
never asks the control store. A pool activated after attachment likewise leaves
the manager reporting ordinary empty reconciliation. Constructor-only Job-store
comparison is not ongoing proof of absence. Require visible refusal for relevant
unexpected Job/control work, preserving it, at startup and during serving.

Confirmed guide contradictions: later section still says no pool cannot serve,
repetition still requires nonempty bindings, and old deployment table presents
Job/worker members as universal. Repeated two-operand install refuses an existing
runtime, so the claimed later-Job repeat/restart path needs exact supported
configuration operands or an honest missing-capability statement. No dynamic
onboarding expansion required by this review.

Evidence REVIEW-TESTS-190015.json and REVIEW-EVIDENCE-190015.json, reproducible with
reproduce-review-190015.py. Reviewer10.60917818499729s tests and0.01748515199869871s
audit; author42.259s focused/62.593s probes separate. All historical unknowns
retained. Scratch /tmp/w183883-review190015-7c17nj88 preserved; owned handles/helpers
released. Deterministic control offers use strict fake Authority sessions, no live
Work/provider/engine, production store, build or actual Git mutation. Return impl
then feat; W183883 open, W177936 parked, v11 unchanged, PROGRESS author-owned.

## 2026-09-16T23:16:06Z — resume guard misses steady serving; reconfiguration loses workspace

Claim190122 review review-2026-09-16T23-16-06Z.md accepts the new read-only offer
reader and startup/explicit-reconcile refusal. Nine focused checks pass and five
candidate hashes match. Source-run labels/evidence are corrected, simulated-runtime
installation tests add component coverage, and earlier guide contradictions are
superseded. These accepted portions replace their outstanding review status.

Confirmed via actual manager.serve with state injected during its sleep callback:
accepted control offers and an active pool arriving after initial recovery are
ignored by ordinary ticks. The loop reconciles once then sweeps; recover-only
validation is not ongoing. Both runs return normal empty reports while the public
unconfigured_work reader names the state. Require read-only guard on every actual
tick and preserve foreign state, not repeated full restart recovery.

Confirmed documented one-operand reconfiguration removes integration_workspace
from deployment.json after destination install. Immutable selector/runtime bytes
stay unchanged, which the current test checks, but effective path binding does not.
Require exact supported inputs preserving installed selections or honest statement
of missing installed-update capability; no generic migration expansion needed.

Current frozen installed lifecycle remains unverified: simulated launcher cannot
execute and test_packaging examines old retained bundle identity/manifest, not the
new empty runtime. After the tick fix, use one focused current build/install and
destination-local lifecycle with manifests/logs/costs, no Git/model/engine effects.

Evidence REVIEW-TESTS-190122.json, REVIEW-EVIDENCE-190122.json and
reproduce-review-190122.py. Reviewer5.444025699980557s tests and0.0218375229742378s
reproduction; earlier wrong layout key caused reviewer KeyError, tool wall
0.060025017s, corrected with fixture cleanup. Author47.462s focused/24.689s probes/
55.163s current stage suite, prior unknown costs retained. No reviewer product/test
edits, build, actual Git mutation, provider/engine or production store operation.
Return impl then feat; W183883 open, W177936 parked, v11 unchanged.

## 2026-09-17T00:17:18Z — fresh-instance corrections independently accepted

Claim190454 review review-2026-09-17T00-17-18Z.md accepts the ordinary-tick guard
through drain, path-selection preservation/refusal and current frozen installed
lifecycle evidence. This supersedes all outstanding corrections from the previous
review.13 focused checks pass; all24 delivery-path hashes match their handoff chain.
REVIEW-CANDIDATE-190454.json consolidates the accepted bytes and originating records.

Independently verified current81-file bundle digest
f675e883ad0e752c1d2881702d9d6b40189e2f565bc21242268cd05abfe99911 and version
baton12.0.0 (fb5d39d6, dirty). It matches the author's actual no-repository installed
lifecycle manifest. Frozen start/status/bounded monitor/stop/status all returned0;
canonical empty snapshot/logs and stopped status are retained. This is source-cwd/
environment independence, not a claim the checkout was inaccessible on the host.

Accounting clarification: successful frozen13.242s excludes finally-stop duration
and separate removal0.002s. Warm build7.146s is not cold cost. At least one600s
monitor timeout and unknown cold-build time, plus prior claim189471 unknowns,
remain history; "one build/install" PLAN shorthand is superseded as accounting.
Author reports two earlier destinations manually stopped/removed without identities.
No matching /var/tmp/w183883-frozen-190149-* paths remain visible; reviewer cannot
prove host-wide process absence through its local PID namespace. Successful run's
own stop/absent evidence stands. If reusing the harness, verify finally-stop success
before removing evidence; no rerun required for this acceptance.

Reviewer tests5.465995617967565s, bundle audit0.0938894179998897s, full candidate
audit0.0011403600219637156s. No reviewer product/test edits, build, actual Git,
provider/engine/credential or production-store operation. Evidence
REVIEW-TESTS-190454.json and REVIEW-EVIDENCE-190454.json.

OWNER-READY-190454.md replaces the superseded Job-preconfigured owner packet;
pass ops for owner review/Git ownership and execution or explicit resolution.
No workload inputs needed for empty installation. Actual default clones are owner
operations; no live Job/provider qualification or cutover. W183883 remains open,
W177936 parked, v11 authoritative, PROGRESS implementer-owned.


## 2026-09-17 — owner requests concrete instance-inputs.json

Slawomir requested creation of the instance input file after accepting the empty
installation boundary. Prompt prepares v12/instance-inputs.json with zero Jobs,
workers or credentials and no supplied Authority UUID. Routine initial selections:
Git profiles; baton.merge integrator; baton.codex verification/review receipts;
baton.slaw approval receipts; generation 1; retain all artifacts under the exact
bytes of v12/instance-retention.md. Integration instructions digest binds current
AGENTS.md bytes, not a synthetic digest. Default state_root is
/home/sl/baton-v12-instance; the two-argument installer overrides it with its
chosen destination. This is input preparation only, not installation, worker
assignment or Job execution. Recheck instruction bytes when configuring real
Jobs; later changes to AGENTS.md do not silently change the captured digest.


## 2026-09-17 — ignore generated Python build outputs

Owner requested ignoring the build subdirectory to avoid adding artifacts.
Observed: v12/python/build and packaging/build-stamp.json are already tracked.
Add narrow v12/.gitignore rules for python/build/ and the generated
python/packaging/build-stamp.json, preserving visibility of runtime state paths.
The owner must remove these generated paths from the Git index; prompt only
edits ignore rules and does not delete artifacts or mutate Git state.


## 2026-09-17 — prompt-authored first-Job provisioning failure

Owner ran /tmp/baton-codex-adapter-job/KICKOFF.sh. Work a2b0d14b-W1 and
Job codex-adapter-first were recorded in the v12 instance, but manager startup
failed in check_workspace_storage because the prompt-authored packet did not
create its configured storage directory. This is a preparation error, not
evidence that the Job executed or failed its task. The same packet incorrectly
selected distinct storage roots for workers sharing one control store;
configure_workspace_storage binds one common root per control store.

Short-term correction: retain the first configured implementation storage path
as the common root, create only missing manager-owned directories, keep
participant/credential/launch identities distinct, and recompose through the
bundled bootstrap before starting. Preserve the immutable submitted document
and all existing state; no resubmission, database edits, root deletion or
credential changes. This correction does not close the human-facing Job
preparation gap or reopen the completed installer Work. Structural document
validation alone did not prove host provisioning and should not have been
presented as sufficient kickoff readiness.


## 2026-09-17 — installed status omits retained preparation failure

The first v12-owned Job is exceptional before runtime start, but status exposes
no preparation refusal and the serving loop prints only its final sweep. The
public attempt_preparation_failure_of reader exists. The CLI exposure gap is
recorded before a diagnostic workaround: a small read-only CLI wrapper will use
ControlStore.open_readonly and the public failure readers, with no SQL or
workflow mutation. This wrapper is a stopgap, not the product fix or a claim that
the installed CLI already exposes failure detail. Owner explicitly requested
continued diagnosis. Preserve the existing Job and exact attempt identity.


## 2026-09-17 — first Job failure localized to initial line access

Public read-only failure reader reports attempt-7a06eb4497395f38e6d45044ec437f9c40e93ba47fd12fc10655958432c6b072 as preparation-failed, runtime not-started,
message: initial development-line access failed: OSError; no permissions were
changed; keep the line materializing and ungranted. No start-failure record exists.
Source initial line access retains descriptors for every visited regular file
and directory until the entire proof/application finishes. The private checkout
has 18078 files/directories. Descriptor exhaustion is a hypothesis; the retained
refusal drops errno. The manager PID is not visible in the diagnostic namespace;
owner was asked for its Max open files limit. Do not assert EMFILE or change
permissions/retry based on this hypothesis alone. No live state was modified.
