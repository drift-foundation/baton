# One development workflow coordinated by v12 — W321608

## 2026-10-18 — assignment and assessment

Owner M321608 selects assessment only. Reviewer baton.rvpc claimed E321622;
binding E321624. Read W321608 events through321622 and T321608 through321608,
complete pages. Read canonical W10/W7 and their sole threads, W16830 and W39435
(detail snapshot321632), W2 current adoption checkpoint and decisions, repository
policy, operating guide, mailbox protocol and normative v12/DESIGN.md.

**Recommendation:** select a narrowly scoped new-Work pilot after filling the
operator acceptance/closure and stable-record gaps below. V12 already has real
coordination machinery; replacing it with a copy of v11 commands is unnecessary.
Do not declare the installed v12 surface a complete replacement today. Execution
adoption is accepted; sole-authority development workflow adoption is a distinct
owner decision with missing integration evidence.

This assessment changes only its own record. No product, deployment, configuration,
specification, other dossier, graph edge or active allocation changed. No live
provider/engine or broad certification ran. Existing W61981/W321528 files and pins
were not edited. Source baseline: 3dcf6dc4bcee97e932d17c93ac13c5811b3af188.

## Evidence legend

**Implemented** means inspected code/public API exists, not deployed certification.
**Independently proved** names accepted historical evidence or this assessment's
focused probe, limited to its exact boundary. **Missing** identifies a specific
absent connection/surface in the inspected Python stack. **Unknown** means no
sufficient deployment/pilot evidence was obtained; it does not assert absence.
The older Node PoC and its v11 bridge are not substitutes for the Python host.

## Finite capability/gap map

| Capability | Implemented | Independently proved | Missing / unknown for the pilot |
| --- | --- | --- | --- |
| Create and queue | `authority/api.py:208` public create_work is replayable; trusted `tools/bootstrap.py:_compose` creates v12 Work, routes and scoped receipt grants. `job_manager/submission.py:submit` stores closed versioned submissions; `tools/job_manager.py` exposes submit. | Accepted W247941 creates and serves two independent Jobs. Probe321622 confirms participant binding and durable operation replay, not a complete creation UX. | Bootstrap/configuration and submission are separate operations. No single ordinary create-and-bind workflow command was found. Need a pinned supported operator recipe with exact Work/Job/input identities and refusal/replay behavior; no automatic new general Work CLI is presumed necessary. |
| Assign and actionable pickup | `authority/session.py` exposes bound claim/pass_work/cancel; `scheduler.py:reserve` and `manager.py:serve` handle stage admission, principal capacity and dispatch. | W247941 proves actual overlapping implementation activity and distinct review assignments; nine current focused tests confirm actor binding and restart replay. | Managed workers receive assignments from serve, so a v11 wait/route consumer is not needed inside each worker. Session read inventory has no personal actionable-work listing; pending human decision discovery is not exposed by the installed stack. Need a finite owner-facing pending action, not another hidden background session. |
| Dependencies | `job_manager/documents.py:_dependency/_resolvable/_acyclic` validates stage-scoped dependencies; manager derives eligible acts. Authority also has typed install_gate/satisfy_gate. | Accepted execution proves implementation-to-review sequencing; no fresh general dependency proof claimed. | Cross-submission arbitrary Work graph/containment parity was not found in these APIs. Do not assume it is needed for one Job. A dependent code Job must consume an explicitly accepted integrated base, not a producer's exit. Cross-Job integrated-base behavior is outside this pilot unless selected. |
| Implementation → review → correction | `review_driver`, worker `review_cycles`, and `tools/stage_execution` carry same-line checkpoints and distinct role assignments. Bootstrap names one Work for implementation and review, not separate v11 work items. | W236087 proves a real changes-requested review, restored-context correction and accepted second review; W247941 proves separate independent review lanes. | Current deployment wiring and exact candidate version remain to be pinned. Fresh contexts suffice initially; reuse/parallel reuse is not silently certified or made an extra pilot gate. |
| Review → owner approval | `Session.review` and `Session.approve`; `core.py:2268` requires accepted technical review and records policy generation. Managed integration/result-judgment machinery also exists. | Historical independent reviews establish exact reviewed proposals. This probe confirms receipt actor binding, not actual human approval wiring. | Installed `stack_command.COMMANDS` and manager submit/status/serve expose no human approve/deny command. Automatic integration receipt actors cannot stand in for Slawomir's decision. Need a supported narrowly authorized owner decision path binding exact retained candidate and verdict, with replay/stale refusal. |
| Durable acceptance and closure | Proposal/receipt/decision/operation reads exist; `Session.close`, `core.py:2376` checks close capability and exact live assignment when relevant. | Current focused close test confirms capability separation; restart tests confirm durable results/replay. | Bootstrap GRANTS includes verify/review/approve/integrate, not close. Core close is a general capability act, not proof of review/approval. A completed Job/report-and-hold is not satisfying Work closure. Need a selected owner close grant and wrapper/recipe proving exact approval before satisfying closure, plus denied/non-satisfying dispositions without erasing output. No need for auto-integration. |
| Operator status | Installed manager status, stack status/monitor/logs; current status uses validated readonly openers. Projection fixes W316915/W319114 are integrated. | W319114 independent and integration evidence establish focused status behavior; W247941/W236087 retained evidence also records historical readonly failures rather than hiding them. | No fresh installed-instance availability claim. Read-only view must surface pending owner action and distinguish execution, review and acceptance. W321528 owns failed-run candidate/effective-timeout reporting; revalidate its result for a failure reached by the pilot, do not edit its packet. |
| Intervention and recovery | Public authority cancellation/fencing; Worker Manager deadline/reconciliation machinery; stack start/stop and resource holds. | W247941 exact runtime cessation; W236087 four exact runtimes absent. Current probe proves only authority reopen/replay. | Stack stop stops supervisor processes, explicitly not all Job runtimes (`tools/stack.py:runtime_boundary/_stop_admitted`). No simple installed per-Job cancel/decision surface found. Select and prove one exact cancellation/hold procedure through supported owners; never interpret stopping manager or claim release as writer cessation. General replacement/recovery stays deferred. |
| Dossier, identity, history | Full authority UUID + Work ID and generation; creation, assignments, operations, receipts and label history public reads. Existing repository dossiers remain durable evidence. | Probe confirms histories survive reopen and different Works stay separate; historical reviews bind exact authorities/attempts/candidates. | Python authority API has no canonical dossier binding/history export or general discussion/obligation surface found. W39435 flat dossier locator/materialization remains parked. A single new stable flat locator plus authority-backed binding/readback and evidence references is needed; do not copy the whole v11 mailbox UX. Labels are not a dossier binding. |
| Authority cutover / rollback | Python authority schema is explicitly independent of v11; exact store-kind/UUID and schema refusal boundaries exist. | No retained evidence inspected proves migration or sole-authority workflow cutover. | No supported v11 migration/adoption path found; authority/schema.py still documents clean initialization of disposable proof stores. Production retention/upgrade responsibility must be selected. No backlog copy, old-ID rewriting, database copying or dual writable Work authority is authorized. |

Paths above are under `v12/python/src/baton_v12/` unless prefixed `tools/`, which
means `v12/python/tools/`. These are evidence locations, not a files-to-edit restriction.

## Accepted evidence reused and its limits

- `baton:work/records/2026/09/finding-v12-real-jobs-adoption-gate/review-2026-09-29T16-58-33Z.md`:
  two fresh-context Jobs, four stages, 86.433s actual implementation overlap,
  exact independent candidate verdicts and cessation; no integration or general
  production reuse certification.
- `baton:work/records/2026/09/finding-v12-managed-session-resume/review-2026-09-30T15-26-48Z.md`:
  one real correction/restoration cycle with independent review; no parallel reuse
  claim. W316918 subsequently owns accepted final allocation correction.
- `baton:work/records/2026/10/finding-v12-status-concurrent-submission/review-2026-10-18T07-32-54Z.md`
  and `INTEGRATION-321492.md`: useful code delivery with independent acceptance and
  owner integration, but v11 carried that coordination. Failed execution and absent
  formal adapter verification remain distinct from accepted candidate evidence.
- `PROBE-321622.json`: nine existing deterministic tests passed, 0.017s unittest
  time / 0.179266s subprocess elapsed, timeout60s. Two selected classes exercise
  participant binding, receipt actor, capability closure, durable reopen/replay and
  separate Work histories using disposable stores. No engine/provider or product
  edits. This is not a sole-authority pilot, migration proof or global safety audit.

## Existing ownership and boundaries

W2's current PLAN and ADOPTION-RECONCILIATION-20261018 keep v11 coordination while
moving selected execution to v12. Owner M321608 separately authorizes this assessment,
not a cutover. W10 M6 owns broader mixed-version rollout, observability, documentation,
identity separation and adoption; canonical W10 remains blocked on W9. W7 M3 owns
proposal/verification/review/approval/integration; remains blocked on W3, with W16830
open. Neither edge nor scope is altered here. W10's historical full-retirement TUI
condition is not imposed on this one-workflow experiment or silently waived for
full retirement.

W16830 (`baton:work/records/2026/08/finding-v12-approval-attestations/PLAN.md`) owns
multi-attestation aggregate policy (one-of/all-of/threshold), not proof that every
single-owner approval needs that whole feature first. Recommend one configured
human approver using current receipt semantics for the pilot; owner must select
that scope. W39435 (`baton:work/records/2026/08/finding-v12-flat-dossier-storage/PLAN.md`)
owns stable flat locator grammar and materialization; do not duplicate its product
contract. W71830 and its scheduler/review-cycle children own existing automatic
stages; W247941/W236087 are reusable proof, not Works to reopen.

W61981 owns generic complete verification context; its current reassessment shows
missing declarative context and a schema-version collision. A documentation pilot
can instead pin a fully contained focused check and immutable inputs; it does not
close W61981. W62098 owns proposal completeness, W62535 preparation preflight,
W321528 failed candidate reporting. Apply their selected-path checks rather than
making the entire backlog a prerequisite. Broader resilience, hierarchy, tags,
rich TUI, automated integration and parallel reuse certification are not proposed
pilot prerequisites. Reached loss, duplicate-effect, isolation or false-success
failures still block that path.

## Proposed smallest useful pilot

One NEW v12 Work and one implementation/review Job: produce a concise current
single-Job operator quickstart for the selected installed workflow, with exact
supported commands, explicit execution-versus-acceptance status, failed-output
inspection and safe cancellation/hold procedure. The owner selects its destination
and freezes its source/command evidence before assignment. One documentation
artifact, deterministic structural checks plus independent semantic review; no
manager refactor, broad test suite, integration worker or backlog migration.
This is useful deliverable work rather than a synthetic closure-only exercise.

1. Freeze the pilot contract, base, complete check inputs, one implementation
   principal, separate review principal, human approval principal, exact package/
   image/profile/instance UUID and limits. Allocate the new stable dossier through
   the selected binding mechanism. Existing v11 assessment Work tracks readiness
   only; it must not become the live routing authority for this new deliverable.
2. Use supported bootstrap/submission and serve operations. Implementation/review
   and an in-scope correction if actually needed stay in v12. Do not manufacture
   a review defect merely to force another live invocation; rehearse correction
   deterministically and reuse W236087's real restoration evidence.
3. Owner reads pending action, exact immutable proposal, independent verdict and
   test limitations through the chosen v12 operator surface. Approve/deny with a
   durable idempotent receipt. No passing Job flag substitutes for this act.
4. Human plus assisting agent imports only approved bytes after base/drift checks;
   Slawomir owns Git. Record resulting commit/evidence reference separately from
   approval. Select delivery as an approved reviewed proposal or as integrated
   documentation explicitly; recommended pilot finish is integrated documentation
   so the complete human delivery path is exercised.
5. Close the v12 Work under the selected owner capability and disposition. A
   restart/reopen reproduces identity, dossier, candidate/review/decision/commit,
   closure and outstanding holds without a v11 handoff. Readback is acceptance.

### Exact prerequisite outcomes, before a live pilot

**P1 — owner disposition path:** expose or document a supported, packaged,
participant-bound command/JSON procedure for pending owner action, approve/deny,
recorded integration reference and close. Bind exact evidence; refuse wrong actor,
stale candidate/policy, missing review, duplicate changed operands and satisfying
closure without selected acceptance. Avoid direct SQL/private APIs or ad hoc grants
in worker code. A wrapper over existing public sessions is sufficient in principle;
no new core approval algorithm is presumed. Missing normal operator procedure is
the finding, not permission to bypass it with this reviewer's filesystem access.

**P2 — durable pilot identity/record:** select W39435's minimal stable flat locator,
public binding/readback and evidence retention; freeze authority/schema/store
identity and backup/restore responsibility. Preserve all old dossier locators.
This need not include arbitrary graph navigation or mailbox discussion.

**P3 — joined deterministic rehearsal:** through the selected installed entry points,
exercise create/submit/automatic pickup/review/owner decision/closure, restart at
handoff and lost-reply decision, stale/wrong-principal refusal, missing evidence,
non-satisfying outcome and exact cancellation/held-unknown behavior. Demonstrate
one writable authority and retained history after readback. Use fake/replay
provider/engine at their boundaries, not invented authority receipts. This is the
missing proof; the nine API tests do not discharge it. Pin and independently review
the concrete pilot packet afterwards. Live execution, if selected later, needs its
specific provider question; this assessment authorizes none.

Decomposition recommendation: P1 and P2 are independently reviewable prerequisite
outcomes; P3 consumes both. Existing ownership mappings above should be reused or
narrowly selected before creating duplicate Work. No child/dependency was installed:
this assignment authorizes assessment only, and contract/operational selection
remains with owner. When selected, reviewer coordinates explicit graph gates and
actual file ownership; shared authority/CLI edits serialize unless disjoint ownership
is established. The pilot's independent reviewer is the joined acceptance consumer,
then baton.decide receives the decision. Do not wait for all W9 hardening or change
W10/W7 edges to enact this bounded selection.

## Cutover and rollback proposal

Start with a new deliverable, not migration of an existing open W number. Keep the
v11 instance serving all existing Work. Record the new v12 authority UUID/Work ID
and stable dossier in a read-only cross-reference on the v11 assessment/adoption
record; that reference is not a second assignment or closure authority. No shadow
v11 deliverable with matching mutable status. Do not rewrite historical v11 IDs to
look like native v12 IDs. This limits cutover to choosing where one new Work lives.

Before admission, aborting the pilot leaves v11 untouched and preserves any created
v12 intent. After admission, stop new pickup, fence/cancel the exact v12 assignment
through supported owners, positively account for every runtime/launch and preserve
holds/output. Stopping the supervisor alone is insufficient. If runtime state is
unknown, retain the gate; no conflicting v11 replacement may start. Keep the v12
Work as historical authority even if abandoned/non-satisfying. Only after exclusion
may owner select a distinct v11 follow-up with explicit predecessor/candidate links;
never resume both as writers or replay an uncertain provider effect. This is a
bounded withdrawal, not reverse database migration. General migration remains
W10 scope and requires its own export/import/identity policy and proof.

## Concrete owner decisions

1. Select this new-Work pilot as the sole writable v12 authority for its deliverable,
   while preserving v11 for all existing Work; or retain execution-only adoption.
2. Select single-human approval and integrated-documentation closure, with exact
   actor/capability and evidence requirements; no automatic approval/integration.
3. Select minimal W39435 locator/binding and supported operator disposition work,
   plus retained-store upgrade/backup responsibility. Authorize bounded P1/P2/P3
   preparation under existing mapped ownership without altering W10/W7 gates.
4. After independent packet review, separately select actual deployment/pilot
   execution. No new live run is needed to decide this assessment.

Assessment complete; return baton.decide. If accepted as a major planning milestone,
human Git checkpoint due: suggested message `docs: assess one-workflow v12 coordination pilot`.
No commit is claimed. Findings are a recommendation, not a specification change.


## 2026-10-18 — owner selects preparation, M321677; claim E321681

Owner approves one new operator-quickstart Work coordinated solely by v12, existing
Work remaining v11; single-human approval and integrated-documentation closure.
Prepare supported owner disposition commands and minimal stable dossier binding/
retention, reuse W39435 ownership, then joined deterministic rehearsal. Record exact
backup/restore responsibility and install prerequisites. Return an independently
reviewed concrete packet before deployment/live selection. This supersedes the
previous awaiting-scope-selection checkpoint and assessment-only restriction for
bounded preparation. It does not authorize this reviewer to implement product code.

Finite decomposition: W321688 is the minimal binding/retention provider under
existing W39435; W321689 owns owner disposition commands under this umbrella;
W321690 owns joined rehearsal/packet under this umbrella. W321689 waits for
W321688 to serialize potential shared authority/CLI edits. W321690 waits for both;
W321608 waits for W321690. Canonical edges installed E321691–E321694, not prose
substitutes. Existing W10/W7 edges remain unchanged. P2 precedes P1 because owner
receipts need stable evidence references; this changes preparation order, not
accepted outcome. Broad W39435 obligations are not silently closed by its child.

File ownership: reviewer owns this umbrella and child FINDING/PLAN/reviews; assigned
implementer owns each child PROGRESS and its isolated candidate. W321688 alone is
the first executable source owner; W321689 cannot edit overlapping product paths
until its provider has independently accepted delivery and owner checkpoint.
Implementer records actual paths before edits and coordinates any overlap with
W61981/W321528; their packets and pins remain untouched. No exclusive edit list is
imposed. Child results bind exact candidate/base/test changes for independent review.

Backup responsibility: Slawomir is the production backup/restore authority and
sole canonical Git owner. The assigned preparation implementer writes the bounded
procedure and demonstrates it only on disposable deterministic fixtures; reviewer
independently checks restored identities, evidence and refusal boundaries. Neither
reviewer nor worker may copy/restore a live authority or clear runtime holds. The
concrete packet must name retained authority, Job/control stores, immutable inputs,
outputs/context, configuration and version provenance as one consistent recovery
set, with access boundaries and verified manifest. Stop admissions and positively
account for writers before selecting a backup cut; no guessed SQLite file-copy
recipe or automatic migration. Restore never enables a second writable instance;
old runtime/launch uncertainty remains held until accounted for. A source Git commit
alone is not this backup. No production backup operation is selected here.

Read E321681 and T321608 through M321677, complete pages. Prior probe remains nine
passing tests, 0.179266s; no new test/live execution needed for decomposition.

## 2026-10-18 — owner clarifies v11 preparation / v12 execution boundary

Owner: "we prepare work packets/dossiers here in v11 (for now) but we should always run via v12". V11 remains the current preparation and coordination authority: dossiers, scope, acceptance, packet preparation and handoffs stay here. Executable work runs through isolated v12 Jobs, with actual Job/attempt identities and retained evidence returned to the owning v11 dossier. A v11 claim, external model session or isolated directory does not substitute for v12 execution. This supersedes the earlier AGENTS.md concrete-blocker fallback wording: a blocked v12 operation is recorded and resolved, not authority to execute directly outside v12. No standing direct-execution exception remains. Human Git ownership, independent acceptance, reviewed-byte integration and specific live-provider/deployment selection requirements remain unchanged. This operating boundary does not migrate the existing v11 backlog or select a production deployment.

## 2026-10-18 — owner prioritizes useful v12 parallelism

Owner: "the key is that v12 allows parallel work, we should maximize". Prepare independent bounded packets in v11 and maximize useful concurrent v12 Job execution rather than carrying the serial v11 implementation queue into v12. Establish actual file/output ownership, input readiness, isolated execution and independent review; preserve real dependency gates and serialize overlapping integration. Current coordination read: W321528 is ready after W321688 and W322125 closed; it is the immediate candidate for preparation alongside active W321689. Revalidate its packet against committed 433b09d6/current accepted source and coordinate shared collector/CLI paths before execution. W321690 still genuinely depends on W321689; W321776 still depends on W321528 and W321780. No graph edges or active assignments changed by this assessment, and no unverified Job launch is claimed. W321689 alone retains its owner completion exception; successor work follows v12.

## 2026-10-18 — native coordination takes priority over v11 bridge investment

Owner prioritizes leaving v11 for all coordination, not only execution. This supersedes treating durable v12-to-v11 terminal-result bridging as the next delivery investment. W324316 proposal is not selected for implementation; manual collection is temporary. Use the existing W321608/W321689/W321690 path to establish the smallest independently accepted native coordination workflow and concrete cutover packet. Include terminal result pickup, failure/held diagnosis and independent review ownership in readiness assessment; classify any concrete missing outcome before adding scope or graph edges. Preserve existing authority/evidence until explicit supported cutover; this priority is not permission to copy the backlog, deploy, waive review or claim migration complete.

## 2026-10-18 — owner expedites native coordination critical path

Owner directs prompt to ensure the v12 path gets us off v11 as soon as possible. Current canonical path: active W321689 bounded corrections and independent acceptance -> W321690 joined native workflow proof/packet -> W321608 owner-selected pilot/cutover decision. Reviewer acknowledgement324396 confirms native candidate-to-review ownership, unable/no-candidate/held diagnosis ownership, restart/lost-reply and stale-principal/episode behavior, and durable owner disposition are required joined evidence, not presumed missing product mechanisms. Prioritize these three Work high using owning-team priority authority. W324316 bridge remains parked; W324214 telemetry and broader hardening are not added as cutover gates. Use independent capacity for disjoint preparation where inputs exist; do not bypass W321689 acceptance or silently execute blocked W321690. A new gate requires a concrete defect in this selected workflow and an actual recorded dependency. Keep existing Work identities and one coordination authority; delivery priority alone does not select deployment or bulk migration.

## 2026-10-18T17:44:45Z — interrupted-session recovery deferred, successful reuse retained

Owner poke324905 pinned at baton:work/records/2026/10/finding-v12-development-coordination-pilot/OWNER-INTERRUPTED-SESSION-RECOVERY-324905.md. Interrupted-provider-session recovery is deferred and does not gate current3600s continuations or native coordination cutover. Successful-turn context reuse remains required for v12. Preserve all findings/evidence and candidate checkpoints; revisit if longer runs show material interruption loss. This supersedes any broader gating interpretation of earlier reuse investigation, not its facts. No launch authorized; existing claims/dependencies unchanged.

## 2026-10-18T19-50-44Z — preparation accepted; native pilot deployment selection next

Owner E325893 closes W321690 satisfying and wakes this umbrella E325894. Claim325909 reconciles all prerequisite delivery; review-2026-10-18T19-50-44Z.md and SELECTION-325909.md govern continuation. P1 owner disposition, P2 stable dossier/recovery and P3 bounded deterministic joined proof are delivered, superseding initial missing-selected-path statements only. Two-stage implementation/review Job enforces owner approval boundary. No deployed pilot/cutover/backlog migration claimed. Next owner pins concrete deployment operands, then instance-specific packet preparation/review and separate admission selection. Existing v11 Work remains v11; new pilot deliverable must have only native v12 authority.

## 2026-10-18 — owner M325952 selects instance-specific preparation

Claim325956 pins M325952/E325954: retained destination /home/sl/baton-instances/native-coordination-pilot-w321608-1, accepted source14e52d80679de5e844f72324df632da5e01cf393, Slawomir retention/backup/Git ownership, two-stage native quickstart Work, separate judgment actors, human owner and dedicated diagnosis. Owner delegates resolution of concrete participants/grants/profiles/build-images/credential-network references and proposed3600s provider bounds with reserves. This supersedes waiting for routine operand selection in SELECTION-325909, not independent packet review or separate launch/cutover selection.

Create W325959, baton:work/records/2026/10/finding-v12-native-pilot-instance-packet/, as bounded preparation-only child routed baton.impl. One independently reviewable packet keeps umbrella available for joined acceptance and prevents confusing v11 preparation with the future native deliverable. Reviewer owns child FINDING/PLAN; implementer owns new packet/PROGRESS only. Parent dependency installed separately and read back; no backlog or existing assignment changes. Umbrella remains open through native delivery.

## 2026-10-21 — owner prioritizes fast code–try–identify cycles

Owner: "the critical path does not seem complicated, yet we are constantly burried in new tiny issues. I want the cycle of code-try-identify to go fast". Recorded by baton.prompt. This confirms rapid feedback and useful integrated delivery as the working priority within the accepted v12 scope; preparation milestones alone are not evidence of usable Jobs.

Apply existing focused-verification and continuity authority concretely: run the smallest relevant reproduction/gate early in each selected isolated execution, correct demonstrated ordinary defects and repeat there while the existing invocation/lease permits. Preserve the complete acceptance gate for the candidate handoff. Reuse unchanged reviewed setup and evidence; identity-only continuation changes do not justify rebuilding or re-reviewing unaffected machinery. Record a new issue, but make it a delivery blocker only when it demonstrably prevents the selected outcome or violates a required correctness/isolation/recovery invariant. Do not split a routine tightly coupled correction into a new approval campaign. Existing graph gates change only through explicit supported coordination.

Handoffs name the observed failure, useful result, next executable action and concrete reason execution stopped. Distinguish time spent on useful execution from setup/review/queueing when evidence permits; unknown durations remain unknown. Reviewer corrections return directly to implementation within accepted scope. Installation preparation must produce concrete executable operands and a bounded validation path, reusing the committed accepted implementation rather than reopening it speculatively.

This supersedes any operational interpretation that every small discovery or partial turn requires a new scope decision. It does not extend consumed invocation selections, leases, live-provider/deployment authority, host-execution exceptions or permit bypassing independent acceptance. Prompt coordinates existing assignments without claiming them or altering their active allocations. Current renewal claim345627 and diagnostics/installation work retain their selected boundaries.

## 2026-10-22T03:15:30.728068+00:00 — shutdown evidence persistence requirement

Owner states /tmp is wiped on shutdown: required receipts and restart inputs must not remain solely there. Preserve current-run reports, candidates, verification evidence and continuation checkpoints in canonical dossiers or durable instance storage before releasing for shutdown; verify copied hashes. baton.prompt verified all21 W339626 Stage B receipt files against their durable dossier copies and preserved the temporary helper and once-only marker under operator-b-helper-347232. Active W341357 handler notified to preserve remaining current-run evidence before drain release. This does not authorize another run or imply all temporary evidence has been audited.

## 2026-10-22 — suspend mandatory v12 development orchestration

Owner selects: "change the policy to not use v12 orchestration for now" and confirms that adoption was premature without proper orchestration and is slowing delivery. Until explicitly superseded, routine v12 implementation, correction and independent verification use direct agent/host execution under the existing v11 claim workflow. Do not require a v12 Job, bespoke execution packet, live-provider launch or per-correction host exception merely to develop v12. This explicitly supersedes the October 18 mandatory v12 execution/no-direct-fallback rule and the requirement that parallel development use v12 Jobs; it is not a product-specification relaxation.

Preserve accepted scope, actual file ownership, isolated candidates where overlap/provenance requires them, independent exact-byte review, deterministic verification defaults, required acceptance and human Git control. Reuse retained candidates and focused evidence; measure useful work and overhead honestly. Actual v12 orchestration tests remain appropriate when the product behavior itself requires them, within the owning scope and existing live-provider/engine/deployment selection boundaries. No speculative reruns, new live execution, install or deployment is selected by this policy. Active claims and in-flight executions are preserved; participants adopt the simpler workflow at a safe boundary without duplicate executors.

V11 remains the current coordination authority. No switch to a file-based journal, bulk backlog migration, deletion of records or abandonment of dependencies is selected here. Native v12 coordination and execution remain the delivery target; resume using them for routine development only after an explicit owner decision supported by a practical orchestration path. Prompt records this policy and notifies existing implementers/reviewer; no new implementation Work or claim is needed solely to apply it.

## 2026-10-24T00:36:47Z — template-based Job creation follows accepted retry

Owner confirms the discussed template contract and priority: "I agree, once this immediate retry-job is done and passes, we focus on this". Recorded by baton.prompt from the interactive conversation. Finish the current manager-owned retry outcome and its required acceptance first; then focus on simple ordinary Job creation with an explicit template selection. This makes the previously selected general-creation/template follow-on the next priority, without adding it to W358969/W359719 acceptance or interrupting their active allocation. This supersedes leaving the follow-on priority unspecified, not the retry-first ruling or existing acceptance and operational boundaries.

Confirmed request: template, task, source, scope, acceptance criteria and optional explicit overrides. Resolve and record the exact template version and show the resolved selection; a configured default may save typing without hiding that selection. The reusable template covers stages/roles, stage dependencies and consumed results, input/output contracts (including candidate, verification evidence and review findings), completion/correction/failure rules, and default execution/verification limits with permitted overrides. Deployment supplies actual workers, credentials and capacity. Start with the ordinary implementation-to-independent-review workflow, not a general framework.

The Job manager owns validation of the instantiated workflow and admission through the existing owning APIs; the CLI requests the operation and reports the result. No operator-authored manifests or bespoke launch packets should be required for this ordinary path. Preserve explicit task scope, acceptance and limit overrides, independent review, source/result provenance and prior retry evidence. Template composition must not duplicate admission/uniqueness/recovery logic in a helper.

Coordination checkpoint: W321608 owns this queued follow-on until the managed reviewer allocates bounded implementation Work and installs/readbacks the actual scheduling relationships at the retry handoff. This entry does not install a graph dependency. Align normative DESIGN with this confirmed contract before dependent implementation; SCH-1 currently pins normalized submissions but does not yet state this template contract. No new live run, deployment, cutover or Git mutation selected.

## 2026-10-26 — accepted pilot consumed; template delivery allocated

**Confirmed:** under claim361899, read W321608 detail/events through361899 and
T321608 through358996 (complete pages). Owner E361852 closes W325959 satisfying:
instance4 quickstart-d completed implementation and independent review with retained
results/released resources; stale documentation was separately corrected and
committed as182c8f943cdfc12134ae2d082d9afe98189efe90. Read its full final handoff
E361815, closure and exact review-2026-10-24T03-33-50Z.md. This consumes accepted
evidence, not a new live run or certification of the old document. Current graph
also reports W358969 and other prerequisite children closed satisfying.

**Confirmed scope:** the October24 template-first ruling now becomes actionable.
DESIGN SCH-1a transcribes that already-approved contract before implementation;
it extends SCH-1 without weakening admission, recovery or startup requirements.
No new product choice or deployment selection is inferred. Temporary direct
development remains current; v11 remains the coordination authority.

**Observed code:** job_manager/submission.py:submit accepts a normalized document
and owns atomic submission/Job uniqueness, including fresh-attempt reservations.
job_manager/documents.py owns closed versioned submission shapes. tools/job_manager.py
main exposes document-based submit and fresh-attempt; fresh_attempt.py:admit owns
the connected retry and existing ownership ports. tools/bootstrap.py:_compose owns
Work/grant composition. The inspected ordinary path has no template request or
resolution surface. This is a bounded source finding, not a deployment probe.
Operational read correction: src/baton_v12/stack_command.py does not exist; located
and read tools/stack_command.py instead. No required policy/dossier is unreadable.
CLI `help` was rejected as an unknown verb; supported `--help` supplied workflow
operands. These were caller locator/syntax corrections, not product defects.

**Decomposition:** W361910 resolves and pins the versioned implementation-review
template contract; W361912 consumes that exact accepted result and delivers the
manager creation operation, thin CLI and joined deterministic rehearsal. The two
outcomes are independently reviewable; serial delivery avoids overlapping shared
submission/admission edits and speculative interfaces. W361912 waits on W361910
(E361914). W321608 retains joined acceptance and stays open through delivery.
Both use flat top-level canonical dossiers because they are separately scheduled
product capabilities. No broad framework, migration or extra retry gate is added.

**Ownership:** reviewer owns this FINDING/PLAN, new child FINDING/PLAN/reviews and
the SCH-1a specification transcription. No concurrent DESIGN/product edit was
observed in scoped git status. Implementer owns each isolated child candidate,
tests and its PROGRESS once claimed; canonical product import remains a separately
reviewed human-plus-agent operation. Actual needed files are the implementer's
choice; coordinate any real overlap. No protocol/application implementation or
existing test mutation performed in this review turn.

Historical pilot-preparation and retry-pending checkpoints in the previous PLAN
are superseded as current status by this entry and retained verbatim in
PLAN-HISTORY-361899.md. No tests rerun: this is planning and accepted-evidence
consumption. Required human Git checkpoint remains pending for the new specification
and planning milestone: `docs(v12): specify template-based Job creation`.

Canonical completion of allocation: E361927 installed parent -> W361912 and
released claim361899; E361941 passed W361910 to baton.impl, next baton.bug.
Detail readback snapshot361942 confirms the complete serial graph and released
claims. A pass using unsupported `next=` refused without effect; corrected to
the advertised `set-next=` and succeeded. No policy bypass or operational blocker.

## 2026-10-27T01:52:12Z — owner selects useful Jobs and lightweight monitor after integration

Owner confirms the prompt recommendation: after the current creation/retry chain
passes joined acceptance and is integrated, the next milestone is to run useful
v12 Jobs and observe them in the lightweight Job monitor. Use that bounded real
work to guide monitor improvements; do not substitute a broad infrastructure or
v13 hardening campaign for this milestone. Recorded by baton.prompt from the
interactive owner's "I agree". This makes the post-integration priority explicit;
it does not supersede the current creation/retry acceptance requirements.

At this decision the remaining chain is W365075 writer recovery, W364834 retry
task preservation, and W361912 joined creation/workflow acceptance. W321608 is
unclaimed and blocked on W361912. Minimum worker visibility W324214 is already
closed satisfying; reuse its accepted evidence. Monitor work can proceed in
parallel where actual files and inputs are independent, with explicit ownership.
No new scheduling edge, allocation or claim is installed by this record.

After accepted integration and the human Git checkpoint, the managed reviewer
prepares the bounded useful-Job/monitor continuation and concrete operator
commands, allocating any necessary Work through the canonical graph. A particular
build, deployment and live execution still require explicit supported selection.
This ruling does not launch a Job, migrate backlog, change the coordination
authority, relax isolation/recovery/independent acceptance, or restore mandatory
v12 orchestration for routine development. Current direct-development policy
remains until explicitly changed. Broad monitor/TUI enrichment remains v13 scope;
the selected outcome is the lightweight read-only monitor used with useful Jobs.

## 2026-10-27T16-54-56Z — joined template delivery accepted; integration remains due

**Confirmed:** W361912 closed satisfying at E366766 with exact candidate-366616
manifest `177147f6557aa6882f7fd6fee74068817a0fc078a0191ead5c09b7aa80931b03`.
All32 candidate members verified again; canonical targets all remain base bytes
(or absent for additions), at HEAD18e771f034d22fed40ae4c597aa606f50c169daa.
Human integration and Git checkpoint remain explicitly due under owner closure.
Review: review-2026-10-27T16-54-56Z.md; evidence/review-366770/INTEGRATION-STATUS.json.

**Current state supersession:** the prior PLAN statement that W321608 is blocked
on W361912 is historical: E366767 woke the umbrella after satisfying closure.
The creation/retry chain is complete; useful Job/monitor continuation remains
post-integration under the October27 owner ruling. Keep this umbrella open.
Source/package/simulated timing acceptance does not certify live startup, a
completed correction plus second review, or native cutover. Preserve all original
evidence and its limits. No further coding decomposition justified at this
checkpoint; next bounded milestone is human integration/checkpoint, then reviewer
preparation of concrete useful-Job/monitor selection. No product changes or tests
rerun this turn. Reviewer owns only this dossier records and new review evidence.

## 2026-10-27 — owner selects candidate-366616 integration

Slawomir explicitly instructed baton.prompt to integrate candidate-366616 while
holding W321608 (claim E366860). This selects human-plus-copilot exact-byte
import under review-2026-10-27T16-46-15Z.md and umbrella assessment
review-2026-10-27T16-54-56Z.md; manifest
`177147f6557aa6882f7fd6fee74068817a0fc078a0191ead5c09b7aa80931b03`.
Whole-path preflight confirms 20 existing writable regular base files and 12
absent additions; no symlink parents. Canonical v12 status is clean and no Baton
background participant holds Work. baton.prompt owns only this exact import and
integration evidence during the human claim. Preserve existing modes; additions
use ordinary non-executable modes. Standing test authority covers the reviewed
test paths; their exact enumeration remains in the manifest/review.

Perform bounded connected-startup/joined-workflow verification with deterministic
seams and explicit writable disk roots. Reuse unchanged accepted package and
other focused evidence. No live provider/engine, deployment or Git mutation.
Human product commit remains pending, followed by return to baton.bug for
useful-Job/monitor planning. This supersedes integration-unselected wording only;
all source acceptance and adoption limitations remain.

## 2026-10-27 — candidate-366616 imported; local verification pending

**Confirmed:** baton.prompt imported all 32 reviewed candidate members under
Slawomir's instruction and claim E366860. Receipt and exact product path list:
`evidence/integration-366616/receipt.json` and `product-paths.txt`. All candidate
hashes and modes rechecked after the attempted verification; existing modes
preserved and new regular files use 0644. No Git index/history mutation.

**Verification limitation:** the initial focused 18-test run failed seven tests
because the explicitly configured scratch root was inside the checkout
(31.393867s). The second failed all 18 at the disk-root guard because /tmp is
tmpfs (0.313861s). These are environment failures, not passing integration
evidence; logs and measured results are preserved in the integration directory.
Two requests to run with disk-backed /var/tmp failed at permission acquisition
(`approval request failed`), before command execution. No successful local
integration check is claimed. The accepted independent review remains unchanged.
`evidence/integration-366616/verify.py` supplies the exact human-run check with
a 180-second timeout, disk-backed scratch, before/after hash and mode checks,
and uniquely named durable output. Human Git checkpoint remains pending.

`git diff --check -- v12` reports candidate-provided trailing whitespace at
`v12/python/tools/single_worker.py:1482`. Preserve the reviewed bytes; no
unreviewed whitespace correction was applied. This entry supersedes all
prior descriptions of the candidate as not yet imported. No deployment, live
provider/engine execution or Work handoff was performed.

## 2026-10-27 — human-run integration verification passed

Slawomir ran the prepared verification helper with disk-backed /var/tmp scratch.
The durable result in
`evidence/integration-366616/verification-20261027T171340Z/verification.json`
records exit 0, 35.390864908s wall time and all 32 candidate hashes/modes matching
after verification. `focused.log` records all 18 connected-startup/joined-workflow
tests passing (35.067s unittest duration). baton.prompt read the saved result
and independently rechecked all 32 imported hashes/modes. This supersedes the
pending-verification state above; failed environment attempts remain historical
evidence. Exact-byte integration and bounded verification are complete. Human
Git checkpoint remains due, then the umbrella returns for useful-Job/monitor
preparation. Candidate-provided trailing whitespace remains unchanged. No broader
suite, deployment, live-provider or cutover claim is made.

## 2026-10-27 — human Git checkpoint confirmed

Slawomir committed `42bed8bb04a53380e565b1a63fb2bc702677f0d0`
(`feat(v12): create template Jobs with verified delivery and startup`).
baton.prompt verified all 32 committed product blobs against the reviewed
candidate hashes. The passing 18-test integration evidence is preserved.
This supersedes the pending-Git checkpoint. W321608 still belongs to Slawomir
at readback sequence 366947; return to baton.bug for useful-Job/lightweight-monitor
preparation remains the next action. No deployment or live run selected.

## 2026-10-27 — integrated checkpoint consumed; useful-Job preparation split

**Confirmed:** E366949 returns after human commit42bed8bb04a53380e565b1a63fb2bc702677f0d0
and18 passing integration tests. This supersedes pending-integration/checkpoint
status. Under claimE366958, reviewer read updated owner entries and exact handoff,
current source command/parser/template/monitor contracts and W324214 acceptance.

**Proposed bounded useful outcome:** a reusable current-source template Job guide,
produced through one ordinary implementation/review Job and observed through the
existing monitor. Historical instance4 QUICKSTART remains truthful. New dossier
../finding-v12-useful-template-job-monitor (W366962) records concrete task inputs,
acceptance, proposed limits and preparation ownership. No build, deployment or
live execution is selected; exact operations return for owner selection after
independent preparation review.

**Decomposition:** W366962 is one independently reviewable preparation result,
separating one-time supported deployment prerequisites from ordinary input-only
creation. It must not recreate per-Job packet engineering. Parent retains joined
acceptance and stays open. Reviewer owns parent/child FINDING/PLAN and reviews;
implementer owns child preparation evidence/PROGRESS, with product/deployments
read-only. No separate monitor implementation justified by existing evidence.
Accepted W324214 projection is reused, not confused with the installed monitor.
A later actual monitor defect can be independently allocated with explicit
ownership; broad W39649 hardening is not a gate.

Read positions E366958/M361944 and W324214 closure325838. No product tests repeated
in this planning turn; no live process/store/credential inspected. Search guesses
v12/docs and v12/python/QUICKSTART.md were absent; actual guide v12/QUICKSTART.md
was found and read. No required policy or dossier remains unreadable.

Canonical allocation readback snapshot366986: W321608 is blocked on W366962,
handler null; E366986 released parent claimE366958. Child is actively claimed
by baton.claude through baton.impl (E366970). Handoff M366985 names current
records and independent-review return condition. Existing six closed children
remain unchanged. CLI help guesses send/post were unsupported; supported say
used successfully after replacing participant include with endpoint baton.impl.
No rejected operation changed state.

## 2026-10-28 — owner selects incremental useful-Job adoption sequence

Slawomir explicitly agreed to the interactive proposal: documentation Job, then
two bounded independent coding Jobs, then repeatable parallel development toward
production work and v13. Finish W366962's independently reviewed operator packet
first, establish selected-installation readiness (actual image, credentials,
finite execution/correction limits), and select the concrete operations before
running the documentation Job. Assess real task delivery, independent review,
monitor visibility, retained result and human acceptance, fixing concrete failures
without turning this into broad certification.

Following that evidence, prepare two coding outcomes with independent ownership
and focused verification. W44342 reassessment may supply one; it is not yet a
selected coding payload. Preserve human-plus-agent integration and human Git
ownership. Production work can start when its relevant execution path has been
demonstrated; broader v13 execution follows useful parallel development. Required
context reuse retains its separate acceptance obligation; supported fresh-context
adoption does not wait on it, consistent with the September 23 ruling.

Keep v11 as coordination authority and preserve Work identities, canonical
records and evidence. Execute selected Jobs in v12 and link their results to
the owning Work; do not copy the backlog or introduce a second authority.
W33755 and broad W103525 certification remain parked and off this adoption path
unless a concrete correctness defect requires a bounded part. No unfinished
requirement is declared passed.

This confirms the documentation payload previously proposed and extends the
selected adoption sequence beyond that first Job; it does not supersede required
review, readiness or explicit execution selection. No specific build, deployment,
live run, two coding payloads, graph change or authority cutover is authorized
by this sequence alone. Current W321608-on-W366962 gate remains unchanged.


## 2026-10-28T01-07-28Z — preparation gate complete; bounded readiness selection next

OwnerE370152 closed W366962 satisfying on exact binding29375db1f141bb4b64b3be38a9429264590d3a3d2a41dd196461d7c977eaf34f, without deployment/live authority. UnderE370157, review `review-2026-10-28T01-07-28Z.md` consumes the completed graph and rechecks binding, source HEAD and fresh path absence. This supersedes the prior waiting-for-W366962/current-child-active checkpoint.

READINESS-SELECTION-370157.md proposes concrete bounded read-only image metadata and source checks plus non-disclosing local credential resolution; commands validated syntactically but not executed. Recommend owner select that readiness scope, then decide actual execution with automatic correction exposure explicit. No finite round ceiling exists in the prepared native start; observation does not cap work. Selected documentation payload remains first; no two coding Jobs or authority cutover allocated. Umbrella stays open, existing v11/direct-development policy remains.


## 2026-10-28 — owner selects bounded readiness checks, E370206

OwnerE370206 selects READINESS-SELECTION-370157.md exact local image metadata, local credential resolution without disclosure, source revision and fresh-path checks, with redacted durable results. This supersedes the prior unselected readiness-check status only. No installation, pull, build, clone, container/model start or automatic repair. Reviewer claimE370208 executes only these checks and returns findings plus concrete execution choice.


## 2026-10-28T01-12-57Z — selected local readiness passed; execution choice returned

ReviewerE370208 executed ownerE370206 exact checks. Selected immutable image exists with expected metadata; production local credential resolution succeeds without disclosure; source42bed8bb/clean v12/commit object and all5 fresh paths checked. Packet binding unchanged. Redacted evidence/readiness-370208/READINESS.json and review `review-2026-10-28T01-12-57Z.md` retain results/limits. Initial Docker socket sandbox denial was resolved by approved read-only escalation, not a product readiness failure.

This supersedes unknown local readiness only. No install/build/pull/clone/container/model/repair/Git operation occurred. Concrete owner choice is the prepared native one-Job installation/serving path with explicit acceptance of automatic corrections under per-invocation3600/900 limits and NO fixed round/cumulative ceiling, or selected bounded cancellation preparation before serving. Review supplies exact grant boundary; no execution implicitly follows.


## 2026-10-28 — owner selects live execution; W370268 allocated

OwnerE370247 explicitly selects retained-archive materialization, mint/composition, ONE fresh installation at /home/sl/baton-instances/useful-template-job-w366962, selected clone/credential delivery and ONE template-job-guide-42bed8bb Job under default policies. Independent implementation/review and report-and-hold; automatic corrections explicitly accepted with NO total-time or round-count ceiling, provider3600/verification900 per invocation. Observe while work remains, preserve artifacts/logs, require actual runtime cessation before supervisor stop. No automatic integration/deletion/discretionary fresh retry/unrelated Job/cutover. This supersedes pending execution/correction-exposure selection, not acceptance or operational limits.

ReviewerE370258 allocated W370268 at baton:work/records/2026/10/finding-v12-useful-documentation-execution after publishing FINDING/PLAN/initial PROGRESS. This is a finite installation/observation evidence outcome with implementation handler sole operator and independent reviewer, not a second authority for the documentation worker assignment. Roster confirmed baton.claude idle with no claim; no active Work interrupted. Child owns new instance/execution evidence/PROGRESS; reviewer owns records/reviews; closed preparation immutable. W321608 remains joined adoption consumer and will be gated on W370268. No operation was executed by this allocation turn.

## 2026-10-28 — owner reports Claude authentication renewed

Slawomir reports one failure was caused by expired Claude authentication and
that he renewed it. The affected Work/attempt and credential context were not
specified in the interactive report. Record as owner-reported operational
information, not independently verified remote authentication or attribution
of the retained documentation review fault. No credential material was read.
The confirmed shared-output declaration incompatibility remains valid evidence;
auth renewal does not supersede that finding or authorize a new live retry.

## 2026-10-28 — owner direction: frequent useful execution feedback

Slawomir clarified that he is not insisting on an immediate run, but wants frequent real test runs because these have been the most useful issue-discovery mechanism so far. Plan repeated bounded execution checkpoints after meaningful fixes, rather than postponing all real execution until the whole improvement backlog is complete. Each checkpoint should identify the question to learn from, the smallest required readiness subset, exact candidate and execution limits, and failure/settlement handling. Preserve failed-run evidence and feed discovered issues into existing Work or bounded follow-ups.

Deterministic verification remains the ordinary development default and prepares these checkpoints; it does not replace real execution evidence for questions requiring the actual installed/provider path. This cadence direction supersedes any interpretation that every workflow improvement must finish before another useful run. It does not itself select an immediate run, grant an unspecified retry/build/deployment, weaken acceptance, or change canonical dependency edges. The reviewer should prepare the next concrete checkpoint within existing scope and bring only its actual execution selection or substantive decision to the owner.

## 2026-10-28 — failed useful-run assessment and next readiness allocation E376779

Owner E376711 closes W370268 non-satisfying, explicitly accepting review-2026-10-28T19-34-00Z.md and its readback limitations. Native close is owner-receipt evidence; candidate retained, acceptance receipts absent, historical cleanup stays with owner. This supersedes the active W370268 execution checkpoint, not the preserved historical grant/evidence. Native useful delivery, adoption, live review success, routine startup timing and parallel readiness remain unproved. All eight direct preparation/execution children now terminal is not a successful umbrella outcome.

M376659 selects frequent meaningful bounded feedback preparation. Allocate W376804 for the next concrete documentation readiness inventory, not another product implementation or live run. Exact learning question: does one useful task with corrected shared role-output declarations and trustworthy observation reach independent review and retained proposal through a qualified installed pair? Keep report-and-hold and human acceptance. Reassess the guide task against current source before proposing unchanged payload; do not claim an old task label fixes its base.

Candidate references observed: human commit8876bf950ff1f8ab8767ce9786df268cc9d767c6 follows verifier checkpointef703336 and observation fixf36bcd75; existing image47e733834bb690fd4601e102f81e527a08b6ffe55da8b8cb345f45edfcb1517e has accepted build binding under W325695, not yet accepted kernel behavior. Source checkpoint and image equivalence are distinct. W375445 is closed satisfying atE376744 on command/preview/status source and fixture package proof; W375446 is still executing joined deterministic settlement proof. No installed host artifact containing these fixes has been established by this review. W370688 inventory00add5d1 remains accepted source preparation with simulated Git/provider and invalid-bundle limitations; never relabel inherited package1da85eed as fixed source.

Minimal readiness is task-specific corrected outputs, actual role compatibility/transport evidence, qualified fixed-observation host and matching worker, relevant selected verifier topology, isolated fresh resources and actionable failure/settlement/retention. Existing W371296 qualification and W325695/W375446 proofs retain ownership; reuse exact applicable evidence rather than starting competing implementations. Queue/startup redesign, the whole W370747 campaign, richer diagnostics, broad hardening, reuse completion and authority migration are not automatic gates for a bounded fresh-context learning run. A concrete safety or false-success defect on the selected path still blocks it.

Only W376804 preparation becomes a new parent dependency. W370302 remains independently ready for its already-selected preparation after failed-run assessment, not authorized live execution. No retry/build/deployment/cutover or change to another Work's gates. Existing failed instance is not repaired or reused; any later historical settlement remains separately selected. One preparer owns only its new dossier/evidence; parent reviewer owns adoption assessment and independent review. Return any required artifact-build and actual-run choice as concrete commands after readiness review, with no reusable historical grant assumption.

## 2026-10-28T22-24-51Z — readiness preparation consumed; two bounded next outcomes

review-2026-10-28T22-24-51Z.md preserves not-ready adoption status after W376804 closure. Reuse its exact source/image/task evidence; no build/run granted. Existing W376246 owns connected safe install; new research-only W378034 resolves supported finite native cancellation/deadline/correction/cessation controls, without duplicate product implementation or launcher. Install both actual parent dependency edges. This supersedes waiting-for-W376804 as current scheduling; full startup/backlog is not added as a gate. W321608 integrates and returns only concrete operational or substantive decisions to owner.

## 2026-10-29 — preparation joined; concrete finite-control decision E383131

review-2026-10-29T11-58-58Z.md consumes closed W376246/W378034 without claiming runnable readiness. Safe failure retention is accepted, automatic cleanup is not. The installed cancel/finite Job contract remains missing; owner E383126 accepts research only. CONTROL-SELECTION-383131.md proposes exact per-Job cancellation/correction/deadline semantics and a smaller different-exposure alternative. This is proposed, not a specification ruling. Pass owner for this actual product choice; no product or live operations authorized. W371295 import correction and exact artifact qualification remain concrete readiness obligations, not a blanket campaign dependency. Prior waiting-for-two-prerequisites checkpoint is superseded.

## 2026-10-29 — owner selects finite native Job control, E383183

Owner baton.slaw E383183 approves CONTROL-SELECTION-383131.md (SHA256 4af2b7d214bad390f6501d87ae3cd5b3e335f9fc49b25afcf456de72d5e6b25c), including clock origins, first-profile limits and unresolved-shutdown semantics. The proposal's pending/unselected wording and prior PLAN owner-decision checkpoint are explicitly superseded by this ruling. The smaller different-exposure alternative is not selected. Preserve the original proposal as decision history.

Selected: versioned persisted per-Job controls; first profile one implementation and independent review with zero corrections, stage4800s from execution admission before preparation, Job9960s from durable accepted creation including queue time, provider3600s/verification900s per invocation,120s bounded shutdown attempt after trigger. Expiry/cancel fences successor admission and orders exact active cessation; unresolved shutdown retains holds and reconciliation. Preserve elapsed time across restart/correction; uncertainty fails closed. Installed cancellation composes existing owners with durable replay and exact-generation protection. No success/acceptance from cessation, no deletion/reset authority.

Owner explicitly requires FINDING/DESIGN pinning before dependent implementation and two serial cancellation/fence then persisted-policy outcomes with actual graph edges and coordinated ownership. W321608 retains joined acceptance. No build, installation, live execution or cutover is selected. This is a bounded exception to LIM-3's previously unselected aggregate-control status, not selection of general cumulative cost accounting or shared-capacity scheduling.

Allocation reason: cancellation/fencing is independently testable and supplies the ending mechanism consumed by policy; common scheduler/CLI/composition files require serial editing. Reviewer owns this dossier, the new child FINDING/PLAN/reviews and this exact DESIGN addition. Implementing claimant owns attributable PROGRESS, candidate and tests after claim; child2 waits for accepted child1. Existing W375517/W375518 queued-admission owners retain their outcomes; coordinate actual shared files and schema via their owners, without duplicating their ledger. No active executor is interrupted.
