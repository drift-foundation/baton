# Standard next-run workflow — W339626

## 2026-10-20 — owner selects reusable next-run path

Slawomir confirmed the interactive recommendation: "yes we need that path next
time, don't lose it". Recorded by baton.prompt. This selects the following
workflow direction for subsequent runs:

**Select accepted base + task + limits → generate configuration → validate
changed inputs → launch through the supported enforcement path.**

Routine runs should reuse supported machinery, without writing fresh staging
scripts, copying decision histories or producing another substantial bespoke
preparation dossier. Reuse unchanged accepted evidence; validate the actual delta
and required runtime inputs. Preserve concise exact operator commands and clear
separation of preparation, launch selection, execution outcome and acceptance.

Observed motivating evidence: W333486 claim339421 lasted1547 seconds, approximately
26 minutes. Its handoff339605 reports about132.6 seconds of measured checks;
remaining elapsed time is unattributed, not measured overhead. The fresh packet
had31 members and refreshed15 decision snapshots; four historical packets were
rechecked and verification exclusions assessed. The shutdown helper staging check
was material: omitting the new helper would prevent controller startup. This
finding does not classify every preparation check as unnecessary.

Inferred causes to assess: repeated manual packaging; mixing runtime configuration,
task planning, test selection and historical auditing; fixed30-second verification
gate driving per-run exclusion design; lengthy handoffs. Establish which portions
can be replaced by existing capabilities before adding a new framework.

Confirmed boundary: let the currently prepared diagnostics run/review proceed.
Do not interrupt it, rewrite sealed packets, or add this Work as its prerequisite.
Address this workflow before repeating bespoke preparation for a subsequent run.
The owner selected the outcome, not a specific implementation or specification
change. Native v12 coordination remains the target; do not invest in a durable
v12-to-v11 bridge as a substitute.

Required preservation: exact source/runtime/helper binding, separate private
candidate ownership, enforced original limits, fresh execution identity, no
duplicate submission, drift/refusal and uncertain-effect handling, safe evidence
collection, independent candidate acceptance and human Git control. Reusing a
procedure does not reuse an old run's permission or invent successful validation.
No live run, deployment, direct-execution exception or approval bypass is granted.
Bring any concrete DESIGN change to Slawomir before implementation.

Proposed acceptance for the reviewer to refine within this outcome: a subsequent
bounded run can be prepared from declared inputs through existing or improved
supported commands, with no new per-run helper implementation or copied historical
decision dossier. Changed required inputs are checked and stale/incompatible ones
refused; unchanged evidence is referenced. Output includes exact short launch and
status commands, identities, resolved limits and safe evidence locations. Measure
hands-on preparation and automated validation separately, retaining unknowns.
Product acceptance remains independent from preparation success.

## 2026-10-20T15:16Z — supported-surface assessment, baton.rvpc

**Confirmed:** the previously missing dossier is available. Current assignment
is claim339655, episode339652; read events through339655 and discussion through
T339626/M339626. No pending obligation. Pass339639's missing-input finding is
resolved by the supplied files and reroute339652.

**Observed:** there is already a JSON-driven composer:
`work/records/2026/09/finding-v12-single-implementation-proof/baseline_bindings.py`
`main` accepts selections/base/run-root; `compose` takes task, verification argv,
runtime inputs and bounds. `write` calls the actual
`stage_execution.held_configuration` validator and emits bound documents.
`tools.bootstrap` already installs from declared inputs; `tools.instance`
binds the installed runtime. Another scheduler or generic packaging framework
is unnecessary.

**Confirmed gaps, by source inspection:**

- Diagnostic `execution-339421/prepare.py` repeats pins, committed-source
  staging, bootstrap inputs, authority binding and command construction in a
  task-specific executable. `pins` also requires copied decision snapshots.
  This is the reusable composition boundary.
- `baseline_bindings.write` line721 emits a start through `baseline.py`.
  Its serving call at baseline.py line1214 lacks the enforcement controller.
  The diagnostic preparer compensates with `_authoring_command` and a second
  command document. A standard path must emit the enforced invocation directly.
- `baseline_bindings.compose` lines345/522 hardcodes the fresh verification
  ceiling to30 seconds. Selected new-run limits must be represented consistently,
  or explicitly refused when unsupported; designing exclusions to fit an
  invisible composer constant is not a reusable configuration path.
  Existing run limits remain unchanged.
- `authoring_enforcement.prepare_manager`, `admit_child` and `main` already
  provide manager ownership, consumed-invocation refusal and the controller
  path. Its import of `authoring_shutdown` is a required runtime dependency.
  Reusing evidence cannot skip binding or checking actual loaded bytes.

**Selected bounded implementation within the owner outcome:** expose one reusable
preparation entry accepting declared accepted source/base, task and verification,
runtime/profile/image references, fresh run/destination identities, resolved
limits and reference-only evidence locators. Reuse existing composition,
validation and enforcement owners. Produce bound configuration, a compact input/
delta receipt, and one authoritative launch/status command set; preparation
must not launch or imply execution selection. Keep required runtime source
staging distinct from copying decision narratives. Exact CLI spelling and
internal factoring are implementation choices, not a new product specification.

**Required preservation:** check current required bytes/identities even when
historical tests are reused. Revalidate affected compatibility/import boundaries
when runtime/helper/profile inputs change. Retain accepted evidence by canonical
locator plus digest and applicability explanation; never trust a cached success
solely because a path/name is unchanged. Refuse changed/unsupported inputs and
existing destinations without overwriting prior output. Partial preparation must
remain honestly incomplete. Consumption/replay must not grant a second submission
or turn an uncertain launch into permission to retry. No new token, renewal,
context-reuse, acceptance or permission semantics are selected.

**Decomposition assessment:** keep this first vertical slice on W339626. Source
staging, composition and generated enforced commands jointly establish one
preparation result; separate partial deliveries would still require manual glue.
W333485 renewal and W333486 diagnostics are already independent outcomes and
remain with their current handlers. Do not add a prerequisite to either current
run. W339626 is the joined acceptance consumer for the reusable path. Further
native coordination/cutover and generalized runtime support remain outside this
slice. No new dependency edge or child is needed.

**Ownership:** rvpc changes only this dossier's FINDING/PLAN and new review.
The next implementation claimant owns its new PROGRESS, preparation and isolated
candidate; existing diagnostics/renewal packets and active authors' files remain
theirs. Coordinate actual shared-source integration overlap, particularly
controller/stage-execution changes; source locations above are evidence, not
an exclusive files-to-edit restriction.

**Verification required:** two differently declared tasks/runs use the same
preparer without changing helper code or copying historical dossiers. Check
fresh identities/private roots, exact task/base/runtime/helper binding, resolved
limits and the enforced launch target. Changed required inputs, missing helper,
foreign imports, incompatible schema/limits, destination collision, partial
preparation and consumed-run replay must refuse safely. A deterministic provider
at the normal boundary must exercise generated configuration through the real
affected composition/enforcement and retain honest outcome/unknown evidence.
Preparation success is never candidate acceptance. Record preparation effort
and automated validation time separately; unknown effort remains unknown.

**Execution boundary:** this assessment ran no product tests, providers, engine
operations, bootstrap or staging. Implementation/verification belongs in isolated
v12 Jobs under standing policy. No direct exception or live invocation is granted.
The implementer first prepares the finite Job using existing machinery and returns
its exact execution inputs for independent preparation review and any required
owner execution selection. Do not implement the new preparer on the host to
bootstrap itself. No concrete DESIGN change is needed for the selected outcome;
raise an actual incompatibility before changing the normative contract.

## 2026-10-20 — owner requests independent developer allocation

Slawomir requests another available developer rather than waiting behind Claude.
baton.prompt read canonical snapshot339778: W339626 is ready, unclaimed and
queued at baton.impl after review pass339707; Claude holds W333486.
The roster reports baton.codxpc online, idle and eligible through baton.codx.
Select that existing implementation route for this Work; tuner need not be
repurposed while a dedicated implementer is available. This supersedes the
Claude-route allocation, not the accepted outcome or execution boundary.

The new claimant owns W339626 PROGRESS/preparation/private candidate only;
preserve diagnostics and renewal packets and coordinate actual integration
overlap. Return preparation and candidate results through independent baton.bug
review as already required. This allocation grants no live launch, direct-host
implementation exception or change to the current runs. Install the allocation
with canonical reroute and read back state; this record alone is not routing.

## 2026-10-20T15:34Z — bootstrap preparation seam resolved, baton.rvpc

**Observed:** claim339782 returned finite proposal `JOB-339782.md` and
`JOB-INPUTS-339782.json`, honestly incomplete. No candidate, prepared authority
or actual attempt exists. The diagnostic helper cannot be reused unchanged:
its fixed task/run pins select another Work.

**Confirmed:** this does not require a new product mechanism before preparing
the implementation Job. Existing `prepare_instance.py` `chosen_from` reads
`selections["compose"]`; its CLI takes selections/base/operation-id and calls
the existing public Authority operations. `baseline_bindings.main` consumes
that same compose block and emits configuration through its existing validator.
The bootstrap's authority identity is an output to insert into the selections,
not a value an automatic new-authority-to-selections command must invent.
`Authority.principal_of` is the existing public read for actual principals
(also used by `tools.bootstrap.principals_for`). No raw-store access is needed.

**Clarification within accepted preparation scope:** for this bootstrap Job,
use bounded host preparation: stage exact already-existing committed manager/
supervisor bytes into the fresh private root, write bootstrap-inputs JSON,
invoke existing bootstrap, assemble selections JSON from its actual identity
and public owner reads, then invoke existing prepare_instance and composer
commands. Ordinary file staging and declarative input assembly are preparation,
not host implementation of the new reusable preparer. Small direct invocations
of existing public APIs to read/bind data are permitted preparation; they must
not become a new reusable helper or implement missing product behavior.
Validate exact staged bytes, controller/helper availability and loaded imports.
Preserve the explicit enforced controller invocation rather than using the
composer's known incorrect start. Do not launch during preparation.

This explicitly supersedes any reading of the earlier "no per-run helper code"
wording that requires the not-yet-built standard preparer to prepare itself.
The delivered product's two input-only preparation demonstrations still require
one unchanged reusable implementation and no bespoke helper or copied histories.
This is no host product-execution exception, relaxation of final acceptance,
or new owner decision. The current one-time preparation can use existing
components with data entered by the preparer; it need not automate that seam.

**Required continuation:** baton.codxpc retains its allocation. Complete the
proposed packet, verification argv, runtime availability/provenance checks and
exact command/environment outputs through the supported components. Record
actual preparation effects and refusal/partial state truthfully. Return a
complete bound preparation for independent review, or the exact failing
supported operation and evidence. Missing automatic data assembly alone is
no longer a blocker. Existing execution selection and independent candidate
review remain owed. No current diagnostics/renewal packet or source ownership
changes. Still one cohesive outcome; no decomposition or new dependency needed.

## 2026-10-20T15:35Z — rapid-start ruling incorporated, baton.codxpc

Owner ruling M339832 and `OWNER-RAPID-START-20261020.md` require routine startup
within 60 seconds, using a description and a few selected files with no per-run
script authoring, test writing or bespoke packet engineering. This explicitly
supersedes any reading of the 15:16Z acceptance or JOB-339782 proposal under
which a reusable preparer alone suffices while users still program each run.
The one-time bootstrap clarification at 15:34Z remains preparation authority
for building this product; it is not evidence of the delivered routine path.

Pinned in DESIGN OBS-0 before dependent implementation. Measure wall elapsed
from receipt of the task description and selected files to observed substantive
agent work, including all routine input assembly, checks and launch. Retain both
endpoints, phase timing and environment assumptions. Do not move packet work
outside the interval. Report a missing work-start observation as unknown, not
success. Task thinking/coding/testing after startup is separate and may take
30 minutes. Two input-only runs must meet this outcome; deterministic evidence
must be labelled and cannot assert live provider startup.

No live selection, deployment, host implementation exception or change to
existing run limits follows. Claim339833 coordinates these narrow FINDING/PLAN/
DESIGN edits in M339835; no sibling product-source edits are owned here.

## 2026-10-20T15:40:43Z — bound preparation independently accepted

Review claim339867 accepts preparation339833 only. PREPARATION SHA256
26f81736d4a8d10b942753964cc6b53857f822c5db97246973f2cb0f6de5d0eb,
packet41973dea7204b24bda6095bf8437d6d57d75cb66380f6978217a92197394cb07.
Independent140 digest checks and staged packet/import/controller/configuration
validation pass; installed81-file runtime manifest agrees. Exact evidence and
limitations: review-2026-10-20T15-40-43Z.md and
evidence/review-339867/preflight.json.

This supersedes awaiting-preparation-review state, not launch selection.
Pass to owner for the one concrete proposed authoring run and its exact
ENFORCED-COMMANDS/PREPARED instructions. No actual Job/attempt or product
acceptance exists. Owner rapid-start ruling is correctly reflected in DESIGN
OBS-0; both whole-path input-only demonstrations and independent candidate
acceptance remain owed. No claim of60-second startup from this manual bootstrap.
Original limits, no retry, enforced900 lease, sibling ownership and human Git
control remain. Authoring image availability observation reused; no new live
execution or product verification during review.

## 2026-10-20T15:42:34Z — owner selects one authoring invocation

Canonical owner reroute339891 selects exactly the independently reviewed
PREPARED-339833/review-2026-10-20T15-40-43Z run and packet41973dea7204b24bda6095bf8437d6d57d75cb66380f6978217a92197394cb07.
This supersedes the awaiting-selection state above for ONE invocation only.
Use ENFORCED-COMMANDS.json start, original900s lease and3600/30/4800/60 limits,
one invocation/no retry. Retain partial output and unknown holds; return actual
Job/attempt and candidate evidence for independent review. No other launch,
limit change, direct-host implementation or acceptance is authorized.
Claim339894 revalidated the selected packet, command, receipt and bound source/
configuration digests before invocation; the sealed launch_selected=false field
is historical preparation data, not the canonical owner's later disposition.

## 2026-10-20 — selected invocation startup refused, claim339894

Observed exact selected controller invocation exited1 after0.2174s at
staged tools/authoring_enforcement.py:523 -> baseline.verify_worker_image:606.
The supervisor's _engine_inspect:2892 discards nonzero Docker stderr and returns
None, yielding “engine answered no document”. A bounded read-only reproduction
of that same subprocess inspection returns1 with “permission denied while
trying to connect to the docker API at unix:///var/run/docker.sock”. Earlier
approved direct image inspection succeeded; that does not prove access from the
controller's subprocess execution boundary. Evidence:
`evidence/execution-339894/RESULT.json`.

The selection was invoked once; no automatic retry, alternate wrapper, policy
bypass or host implementation occurred. Failure precedes manager child creation,
submission and provider dispatch. Job/control stores, authoring log and outcome
are absent; the manager lock inode was created and is preserved. Parent exited;
no running child from this invocation is inferred. No actual Job/attempt or
candidate exists. The generic image error loses the actionable permission cause;
this is recorded here before any possible workaround, not called image absence.

Required continuation is an operational correction of the managed controller's
Docker access, followed by explicit disposition of another invocation. The
one-invocation/no-retry selection grants no second start. Product implementation,
verification and rapid-start acceptance remain outstanding; no evidence here
establishes the60-second successful-start requirement.

## 2026-10-20T15:45:40Z — operational failure reviewed

Review339911 confirms unchanged packet and absent pre-submission artifacts,
with source ordering consistent with the author's image-inspect permission
failure before manager creation. See review-2026-10-20T15-45-40Z.md.
Prior preparation review did not prove subprocess Docker access; direct
approved image inspection was not evidence of that boundary. This supersedes
managed-launch readiness, not the accepted byte/configuration checks.

Owner disposition is now concrete: repair the installed authority for the
exact managed controller command, or explicitly select the same reviewed
command for owner-operated execution in an authorized host context. Validate
read-only engine access through the resulting subprocess boundary. No socket
permission workaround, confinement change, alternate controller or stronger
agent command is selected. Another start needs explicit disposition because
the original single invocation was attempted. Preserve lock/root/evidence.
No product-scope change or sibling reassignment; route this authority decision
to owner, then resume baton.codx under the selected boundary.

## 2026-10-20T15:53Z — bounded policy preparation and operational split

Owner reroute339935 selects preparation only, under reviewer claim339937.
Confirmed rendered codxpc dispatcher and infra home, installed policy bytes,
and static rule mismatch: direct Docker image inspection is allowed; enclosing
env/Python controller is unmatched. See POLICY-PREPARATION-339937.md and
`evidence/policy-339937/static-checks.json`. Prepared one inspection-only rule
and exact operator install/restart/probe commands. Candidate checks allow only
the proposed read-only probe among tested cases; changed code/packet and launch
are unmatched. No installed policy or source changed, no actual repaired
managed-boundary success claimed, no additional provider/Job invocation.

A full launch prefix is not exact-arity confinement: the controller accepts
trailing child-entry arguments. Do not silently broaden authority to fix the
socket symptom. Operator must resolve the accepted launch boundary explicitly;
inspection success alone cannot authorize the second start. Existing staged
source bytes remain part of trust, not protected merely by a pathname rule.

Decomposition: ops child W339972 owns installation/lifecycle and managed-boundary
validation plus launch-boundary disposition; dependency339973 blocks W339626 on
it. This supersedes the earlier no-dependencies plan. Parent remains the joined
acceptance consumer for reusable preparation and the owner rapid-start target.
Reviewer owns these evidence/FINDING/PLAN files; operator owns installed policy;
operational executor appends its receipt; parent author retains isolated v12
implementation and PROGRESS. No sibling allocation changes. This split prevents
ordinary product continuation from consuming a missing execution permission.

The optional systemd-user directory could not be read because it does not exist;
the actual infra manifest supplies lifecycle commands. No required policy file
was skipped. Managed validation remains pending in W339972 because reviewer
cannot install operator-owned policy or impersonate codxpc. No product tests
or live models executed; six static policy checks completed, each locally below
the 30-second timeout (individual wall times not measured).

## 2026-10-20T16:00Z — complete managed boundary selected, prerequisite researched

Owner339985 on W339972 supersedes inspection-only delivery and the operator-run
alternative with a complete trusted managed entry validating arguments and source
bytes. Bound child dossier now lives at findings/finding-managed-controller-boundary/.
Reviewer340017 identifies pre-validation imports and mutable-input replacement
as concrete gaps beyond prefix argument matching. Its FINDING/PLAN prepare one
cohesive reusable entry/custody/selection repair and finite deterministic acceptance.
Existing controller semantics are reused, not redesigned. No executable repair or
installed policy exists yet. Concrete remaining decision: select its isolated v12
implementation path or the finite direct implementation exception proposed there;
owner selected preparation only. No second parent authoring invocation selected.
Parent dependency339973 remains; no source/packet/lock/sibling or Git mutation.

## 2026-10-21T01-32-19Z — boundary prerequisite closed; exact continuation ready

Owner343920 closes W339972 satisfying after independent343619 and managed343612 receipts, waking parent343921. This supersedes the prior unresolved boundary/absent-candidate/blocked-parent statements. Review343925 (review-2026-10-21T01-32-19Z.md) verifies accepted custody inputs and three unchanged live fixtures. CONTINUATION-343925.md names exact accepted successor, bounds, operator arm and managed start commands; historical PREPARED-339833 direct /tmp commands are superseded for execution. Closure explicitly grants no arm/start; original339891 attempt grants no retry. Next action is owner selection of that concrete continuation, then baton.codx execution. Product rapid-start acceptance and human checkpoints remain outstanding.

## 2026-10-21 — owner continuation343960 selected

Owner pass343960 selects exactly one invocation per CONTINUATION-343925.md,
reports successful operator arming, and prohibits retry/rearming. This explicitly
supersedes its prepared/not-selected status for this one installed start only.
Claim343964 revalidated installed entry, selection04cc16db... and packet7fa243de...
hashes against accepted values. Original limits/identities/custody remain binding.
Boundary records checkpoint a545df1104951b3d1bef787c7bf9323a88d73a70 observed via
git show; candidate source integration is not claimed. Private evidence access
remains bounded as in CONTINUATION; missing access is not absent execution.

## 2026-10-21 — selected custody start fails before child creation343964

Exact installed start exited1. Receipt evidence/execution-343964.json preserves
stdout/stderr, command and elapsed observations. Primary exception is ENOENT at
installed authoring_enforcement.py:535 opening private
packet/outcome.json.authoring.log in append mode. Its parent directory is missing;
the controller constructs Process only at536, so this invocation never created
the manager child or reached submission/provider dispatch. The runpy warning and
apport exception are secondary diagnostics, not the primary failure.

Confirmed preparation gap: accepted installer prepare_storage creates only
home/tmp; provisioning procedure creates instance/db but no packet directory.
The immutable configuration packet lives under /opt, while outcome_path points
to private storage/packet. Managed check validates existing custody and containment
but does not prove the output parent exists. Successful check/inspect therefore
did not establish this launch prerequisite. No source change is made here.

Entry consumes before executing the controller. Preserve consumption, lock and
private state; no retry/rearm or directory repair is authorized by this claim.
Required next step: bounded operator preparation correction with exact custody
and evidence, plus explicit disposition of any further invocation after review.
Private state was not read; source ordering supports no new Job/attempt for this
invocation, not a claim that private files were independently inventoried.

## 2026-10-21T01-39-01Z — consumed start failed on omitted output parent

Review343979 (review-2026-10-21T01-39-01Z.md) confirms receipt343964 and pinned ordering at authoring_enforcement.py:535 before Process536. Prior provisioning omitted packet output parent; check/inspect acceptance did not cover it. Supersedes startup-readiness implication of prior continuation, not valid historical boundary tests. Selection343960 consumed; preserve receipt/lock/state, no rearm/retry. Reviewer preparation omission acknowledged. Child W343989 (follow-up to closed W339972) now owns bounded corrected provisioning/unconsumed continuation preparation through baton.codx; parent waits for joined acceptance. Human boundary checkpoint observed a545df1104951b3d1bef787c7bf9323a88d73a70, source integration not claimed.

## 2026-10-21T02-52-42Z — install-once ruling pinned before implementation

Owner344511 closes W343989 satisfying and requires OWNER-INSTALL-ONCE-20261021. Review344516 (review-2026-10-21T02-52-42Z.md) pins exact ruling into DESIGN OBS-0a and new TASK-344516.md. Routine starts/recovery must use installation tooling and automatic prerequisite preparation BEFORE selection consumption, not repeated manual provisioning. This explicitly supersedes treating historical v2/v3 procedures or TASK-339833 alone as sufficient product acceptance. Two input-only <=60s demonstrations plus supported failed-start recovery retain isolation/evidence/once-only requirements. Old task/sealed v3 remain preserved; their task/spec binding is stale for expanded target. Next: baton.codx prepares minimal reviewed binding amendment using existing installation or reports exact unsupported seam; no v4 manual reprovisioning campaign, host implementation exception or launch inferred.

## 2026-10-21T02-58-30Z — installed task amendment unsupported; finite development boundary proposed

Review344558 (review-2026-10-21T02-58-30Z.md) confirms author344532 input inventory and installed register/entry refusal seams. No supported mutation binds the new task into provisioned v3; a renamed registration repeats isolated account/storage setup rather than delivering install-once. This supersedes expectation that ordinary input preparation can produce an executable amended v3 through current operations. BOOTSTRAP-DECISION-344558.md proposes exact bounded isolated source-copy development/deterministic verification through baton.codxpc, expiring at independent candidate acceptance. Owner selection required because current v11 preparation scope and expired340055 grant no such execution. No product/spec relaxation, installed change or launch performed.

## 2026-10-21 — owner344614 selects finite implementation boundary

Canonical reroute344614 explicitly approves BOOTSTRAP-DECISION-344558 bound by
INPUT-BINDING-344532 digest90b2fad2102039ace7e77127137a0df9ffc2ddc516ad4dec25f7dd78cf77cb62.
This supersedes the proposed/not-granted status of that decision and the prior
PLAN's no-implementation-selected statement. Claim344617 implements only in
/tmp/baton-next-run-344617, with exact baseline BASELINE-344617.json. All stated
exclusions remain; exception expires at independent acceptance before integration
or deployment. No installed entry/selection mutation or live execution follows
from this selection. Product/specification requirements remain unchanged.

## 2026-10-21T03-15-49Z — owner exception active; partial code reviewed for continuation

Owner344614 selected finite isolated source-copy implementation and deterministic verification, superseding pending-boundary-selection state. Review344684 (review-2026-10-21T03-15-49Z.md) verifies7 candidate/live paths and baseline; partial manifestf3e5b57f1f708e99aede47c49a3b6190016bdfb3c9d4ab5b79de81d43d1bb16e is NOT accepted for integration. Confirmed install still requires preprovisioned slots, execution lacks trusted managed isolation and consumed-run continuation remains held. Continue directly baton.codx under344614, next milestone trusted one-time installation/automatic isolated allocation. Exception remains active; no renewed owner gate or old v3 launch.

## 2026-10-21T03-32-57Z — review344790: dispatch/admission correction

Candidate344698 is not accepted: installed import roots are lost at the fresh controller child, independently reproduced as ModuleNotFoundError before execution; admission also repeats the wildcard mechanism corrected for sudo-rs in operator343603. See review-2026-10-21T03-32-57Z.md and evidence/review-344790.json. This supersedes treating installer/allocation as ready for acceptance; retain progress and continue one bounded dispatch/admission correction directly under344614. Full recovery/timing acceptance remains outstanding; exception has not expired. Ownership and execution restrictions unchanged.

## 2026-10-21T03-41-54Z — review344866: dispatch/admission milestone accepted

review-2026-10-21T03-41-54Z.md supersedes review344790 correction-pending state: candidate344817 supplies fixed installed roots to fresh children and replaces argument wildcards with one literal request plus strict JSON. Independent12-test managed suite passes4.355s; exact twelve-path hashes verified. This is partial milestone acceptance only;344614 remains active through complete independent acceptance. New actual sudo authorization is unproved and author reports a managed setuid refusal; no repair or installation attempted. Next serial outcome is safe consumed-failure recovery, retaining uncertainty/evidence and fresh identity.

## 2026-10-21T03-54-04Z — review344958: interrupted recovery allocation remains incomplete

review-2026-10-21T03-54-04Z.md verifies candidate344881 at fifteen paths and independently passes23 focused tests6.227s. Positive cessation and completed receipt replay are useful progress. Reservation-only interruption and partial allocation permanently refuse supported recovery; this explicitly reported limitation is not accepted as final OBS-0a/install-once behavior. Next bounded correction provides supported attributed continuation without resetting receipts, uncertain reuse, duplicate effects or manual provisioning. Owner344614 remains active; no full acceptance or deployment.

## 2026-10-21T10-03-50Z — interrupted allocation correction accepted

review-2026-10-21T10-03-50Z.md supersedes review344958 correction-pending disposition for candidate345023 digest72f208fa67478f3d9c958915b5169c8104b66e708d1118757f47aa0653183c16. Fifteen snapshot/live bindings verified; independent32 focused tests pass6.157s. Retained partial preparation now reaches an attributed fresh continuation when non-admission/cessation is established; uncertainty still holds. Full two-task substantive-work/timing and failed-start joined proof remain outstanding. Continue directly through baton.codx under344614; no full acceptance, integration or deployment.

## 2026-10-21T10-27-03Z — complete deterministic candidate independently accepted

review-2026-10-21T10-27-03Z.md accepts candidate345109 digest6834513c45e6086fe2739c3591d3d2a592147e8cdd069e3291aa1a00b62f3799:17 snapshot/live and10 worker-input hashes verified; independent80 tests pass32.274s. Joined two-task, consumed failed-start and initial partial-preparation flows reach real owner results with simulated external boundaries, timing3.867/3.870/4.688/3.869s including input assembly. This supersedes joined-proof-pending state, not deployment limitations. Owner344614 exception expires at this full independent acceptance. Human integration/installation selection and product Git checkpoint remain outstanding; pass to owner with no automatic integration or live validation.

## 2026-10-21 — owner selects reviewed-byte integration (M345512)

Owner selects human-plus-agent integration of exact CANDIDATE-345109.json digest6834513c45e6086fe2739c3591d3d2a592147e8cdd069e3291aa1a00b62f3799, after whole-path/base and W341357 overlap checks, stopping on divergence or conflict. This supersedes the integration-selection-pending state only. Installation, deployment and live validation remain unselected; the source-copy development exception remains expired. Prompt performs this selected integration alongside the human, not as a Route Handler or independent reviewer.

Pre-import read at snapshot345514: W339626 unclaimed at baton.decide; W341357 under independent preparation review with isolated retained inputs, no main-tree product edit allocation. All17 candidate members match the reviewed manifest; all3 existing targets match exact reviewed base hashes and are regular non-symlink owner-writable files, while14 new targets are absent. Prompt owns this bounded main-tree import. M345516 on T341357 records shared attempts.py and authoring_enforcement.py inputs; preserve the sibling's pinned candidate/continuation and serialize its later import with a fresh overlap check. No sibling bytes, sealed evidence or accepted bases are rewritten.

Import only reviewed content, preserve existing target modes, create ordinary non-executable new files, and verify complete final hashes/modes. Reuse independent80-test evidence; no host product-test fallback or new live execution selected. Human Git checkpoint remains due after the prepared diff; agents never stage or commit.

Integration complete under M345512: all17 reviewed members imported exactly (3 existing targets,14 new regular0644 files), existing modes preserved, final candidate hashes verified. INTEGRATION-345512.json binds each result to reviewed bases and owner selection. Every other enumerated BASELINE-344617 and BASELINE-EXTENSION-345109 input still matches; git diff --check passes. No product test rerun, installation, live execution or Git mutation. Index observed empty after import. Human product checkpoint remains due; CHECKPOINT-PATHS-345512.txt scopes suggested staging to this delivery and selected decision/evidence records, excluding unrelated working changes. This supersedes the not-integrated state, not deployment limitations or outstanding sibling acceptance.
