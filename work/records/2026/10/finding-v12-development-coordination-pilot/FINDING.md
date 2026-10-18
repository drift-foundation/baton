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
