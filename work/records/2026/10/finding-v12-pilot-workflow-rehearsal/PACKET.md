# The concrete pilot packet — W321690

What an operator would need to stand the selected pilot up, with every value
either PINNED here or named as an explicit owner selection. Nothing in this
file is a plausible default standing in for a bound value: the FINDING's rule
is that "packet cannot be called executable until required values are pinned",
so the open selections are listed as open rather than filled in with something
reasonable.

**Status: reconciled and reviewable; NOT executable.** The control that keeps
automatic integration admission away from the owner's decision is pinned in
§3b and driven in
`baton:work/records/2026/10/finding-v12-pilot-workflow-rehearsal/composition-325757/`
(32 checks, 3 scenarios, self-check failed for its own named reason). Every behavioural proof
the joined rehearsal owed is now covered by accepted child evidence — the map
is `baton:work/records/2026/10/finding-v12-pilot-workflow-rehearsal/reconciliation-325675/COVERAGE.md`, and §8 summarises it. What keeps the
packet non-executable is §6: nine owner selections that nobody but the owner
can make. A proposed value in §3 is a reviewable proposal, not a selection.

Every pin below was revalidated against the current tree in claim 325675.
Product base `372281f4a473300efb474d5a6573954c15ade367`;
`git diff --stat 372281f4 HEAD -- v12/` is empty, so these pins hold at `HEAD`
(`9debba18`) too and the two later commits are record-only.

## 1. Source and candidate identities (pinned)

| Fact | Value |
| --- | --- |
| Source base | `372281f4a473300efb474d5a6573954c15ade367` |
| Record-only commits since | `61a930e8`, `9debba18` (no `v12/` change) |
| Preceding checkpoint | `433b09d6963ca9789700849b640e242e772b9867` (W321688) |
| W321688 accepted manifest | `baton:work/records/2026/10/finding-v12-pilot-dossier-binding/correction-322441/DIGESTS.json`, sha256 `e8f3f8d96aea26dccbb231310e6e05e33be5cbe23f7464548e32db435e532e25` |
| W321689 accepted manifest | `baton:work/records/2026/10/finding-v12-pilot-owner-disposition/candidate-321689/DIGESTS.json`, sha256 `dbc163c7dc3f08fcf17030b78923029431c2f615c9bf9c797c5c9223a62b1c77`, ten paths |
| W325034 accepted manifest | `baton:work/records/2026/10/finding-v12-pilot-human-approval-boundary/boundary-325197/MANIFEST.json`, sha256 `dd2d071a1669fe861a7a4e3eaea80ed4f2310ad9fe7aafd593f56a0c1a907a4f`, 6 members |
| W325035 accepted manifest | `baton:work/records/2026/10/finding-v12-pilot-diagnostic-recovery-matrix/matrix-325259/MANIFEST.json`, sha256 `970a1a22f209069a7db1595d8d02f34ad40584258ab8d550a31a3d239dd26309`, 12 members |
| Authority store schema | `6` (schema 5 refused, no migration — owner M321965/M321966) |
| Instance selector schema | `baton.v12.stack-instance/1` |
| Recovery-set schema | `baton.v12.instance-recovery-set/3` |
| Bootstrap input schema | `baton.v12.stack-bootstrap/1` |

Child evidence provenance: both W325034 and W325035 runs recorded the same
product base as this packet, so no pin differs between them. The fixture task
their candidates were produced from is `w119114-composed-lifecycle`, task
digest `sha256:5d9f80e2…`, input manifest digest `sha256:76d530a9…`, Job input
identity `sha256:3b3e19f2…` — disposable fixture values, named here so a
reviewer can tell them apart from the production inputs §6.4 leaves open.

## 2. The packaged surface (pinned)

One installed command, `baton-v12-stack`, with thirteen subcommands —
re-read from `tools/stack_command.COMMANDS` this claim: `bootstrap`,
`disposition`, `identity`, `logs`, `manager`, `monitor`, `publish`, `record`,
`repository`, `start`, `status`, `stop`, `view`.

The two the pilot added are `record` (W321688 — dossier binding, evidence
citation, recovery manifest and check) and `disposition` (W321689 — pending
owner action, approve/deny, human integration, closure). Their operator
procedures are `baton:work/records/2026/10/finding-v12-pilot-dossier-binding/RECOVERY.md` and
`baton:work/records/2026/10/finding-v12-pilot-owner-disposition/PROCEDURE.md`; neither is restated here,
because a packet that paraphrases a procedure is a second copy that drifts.

The bundle is a PyInstaller one-folder build from `packaging/stack.spec`. It is
host-specific by construction and reports its own identity through
`baton-v12-stack identity`, which a deployment records rather than assumes.
`bootstrap` refuses a distro that is not a frozen build or whose packaged
schema assets and native validator did not travel.

## 3. Deployment composition (pinned shape, proposed values, open selections)

`bootstrap` requires exactly these nine inputs: `schema`, `state_root`,
`checkpoint_profile`, `integration_profile`, `retention_policy_digest`,
`retention_disposition`, `pool_generation`, `policy_generation` and
`receipt_participants` (`verification`, `review`, `approval`). Optional:
`integration_target`, `integration_target_reference`,
`integration_workspace`, `integration_observer`, `integration_instructions`,
`integration_preparation`, `result_judgment_workers`, and — W321689's —
`owner_participant`, which grants `approve`/`integrate`/`close` in each bound
Work's own scope and deliberately not `verify` or `review`.

Derived rather than configured: the authority identity (generated once at
install and persisted at the destination), the store paths, and the Job
bindings. Routes are `implementation -> impl`, `review -> rview`,
`integration -> integration`.

Instance layout members, all derived from one destination: `authority_store`,
`job_store`, `control_store`, `integration_store`, `deployment`,
`deployment_state`, `distro`, `identity`, `instance`, `justfile`, `lock`,
`logs`, `record`, `repository`, `state`, `stores`, `command`.

### 3a. Proposed participants and grants — a PROPOSAL for review

These are concrete values the pilot's selected shape implies. They are
**proposed for review, not selected**; §6.5 remains the owner's.

| Role | Proposed address | Grants | Why separate |
| --- | --- | --- | --- |
| implementation worker | `baton.claude` | none (acts by claim on route `impl`) | the producer may not judge its own result |
| review worker | `baton.reviewer` | none (acts by claim on route `rview`) | the native independent review assignment |
| verification receipt actor | `baton.verifier` | `verify` | W325034 proves the judgment must be a separate actor's |
| review receipt actor | `baton.approver-review` | `review` | distinct from the owner and from the verifier |
| owner | `baton.slaw` | `approve`, `integrate`, `close` — and **not** `verify` or `review` | single-human approval is the pilot's selection |
| integrator | `baton.integrator` | `integrate` for the automatic path only | not used on the human-approved path (§9) |
| diagnostic handler | `baton.diagnostician` | `manage-work-labels` if labels are used | W325035 proves the handler is an explicit deployment selection |

Policy generation: the grants above must be written **before** any dependent
operation and the generation pinned at that point; the W325034 evidence world
recorded `policy_generation: 14` in `scope:deployment` for its own disposable
instance, which is a fixture value and not a production pin. The production
generation is whatever `bootstrap` records for the selected instance and must be
read back, not assumed.

Pool generation and `policy_generation` inputs stay owner-selected (§6).

### 3b. The submitted Job shape — PINNED, and it is the control

**For a Work whose approval is the human's, the submitted Job declares two
stages: `implementation` and `review`. It does not declare an `integration`
stage.** This is the control that keeps automatic admission away from the
owner's decision, and it is a submission the deployment already composes —
not a new operation and not a product change.

Why it has to be the composition rather than a rule in this document: the
serving manager itself reaches `admit_accepted` (`tools/stage_execution.py`
3118, 3153) and `continue_accepted` (3149) during ordinary progress, with the
deployment's own verification, review and approval sessions. An operator
instructed not to call a function is not a control when the manager can call
it. With no integration stage in the Job there is no call site in that Job at
all.

What the two-stage shape preserves, driven in
`baton:work/records/2026/10/finding-v12-pilot-workflow-rehearsal/composition-325757/`
scenario 1 (15 checks):

* pickup, the real worker turn, the implementation ending, the independent
  review assignment and its real turn — all served normally;
* **the candidate is published** at the implementation ending, and its
  `candidate_digest` equals the reviewed frozen checkpoint's own head, so the
  receipt actors have the exact proposal, line and checkpoint to judge;
* **all four receipts absent**, through 40 further ticks and a fresh serving
  composition over the same stores with `recover()`;
* no falsely complete integration stage, because none is declared;
* the Work handed on to the configured outgoing route with no handler, where
  the owner's `disposition` acts take it.

Delivery on this shape is the human's act, recorded by `disposition
integrated` against a human integration record — which is the pilot's selected
meaning of integration, not a stage a manager runs.

**The outgoing route is a deployment operand.** Each worker carries the route
its own ending hands the Work on to (the composed document's per-worker
`review_route`), so the review worker's outgoing route should name the route
the OWNER is served on. In the evidence fixture it is the integration route,
which is why that scenario's Work lands there; §6.8 is where the
production route and its handler are selected.

## 4. Effective limits (pinned)

Re-read from `job_manager/execution_limits.py` this claim.
`CURRENT_GENERATION` is `1`; per invocation, in seconds: `provider_turn` 3600,
`ordinary_verification` 900, `integration_verification` 1800,
`host_verification` 300. Bounds `MIN_SECONDS` 1 and `MAX_SECONDS` 86400.
`LEGACY_GENERATION` 0 carries the same four values and remains readable for
compatibility.

## 5. Retention and recovery (pinned contract, owner obligations retained)

The recovery set is a closed membership, not a discovery: stores
`authority_store`, `job_store`, `control_store` (each with its `-wal`, `-shm`
and `-journal` bytes digested, not merely listed); retained trees `state`,
`logs`, `repository` bound by content manifest; and provenance `deployment`,
`identity`, `runtime` bound by value.

`record recovery-manifest` emits that set. **`record recovery-check` reports
and refuses; it never admits anything** — RECOVERY.md's own words, and this
packet previously implied otherwise. It refuses a set that is missing,
changed, unreadable, carries declared-missing members, or is not this
deployment's store; a clean report is the **precondition** for an operator's
admission, not the admission.

Three obligations are therefore the operator's and are not discharged by any
command in this packet:

1. **Stop admissions** — and stopping the supervisor is explicitly not that;
   `tools/stack.py` stops supervisor processes and not every Job runtime.
2. **Positively account for every runtime and launch.** Stopping the manager or
   releasing a claim is not writer cessation. If any runtime state is unknown,
   the gate is retained and no cut is selected.
3. **Admit one writable instance.** Nothing in the product fences a second
   writable copy of a restored set.

What the pilot's own evidence does and does not add here: W325035
`matrix-325259` scenario 3 proves a manager *reconstructed over the same
retained disposable authority* keeps the exact assignment, history and runtime
ownership, and that a second live composition duplicates nothing — and
`Authority.stored_identity` proves store kind and UUID only. **That is not
backup restoration, not failover, and not exclusion of another writable copy.**
W321688's accepted recovery-set contract and its restored-readback rehearsal
remain the authority for restoration; they are cited, not re-proved.

Slawomir is the production backup/restore authority and the sole Git owner. No
real instance is copied or restored by any procedure in this packet; every
rehearsal used disposable instances only.

## 6. Owner selections that remain OPEN

These are the values a deployment cannot derive and this packet will not
invent. Each needs an explicit owner selection before the packet is
executable.

1. **Destination root** for the pilot instance (`state_root`), and whether it
   is retained or disposable.
2. **Worker image digests** for the implementation, review and integration
   roles — selected by validated digest in the owning record, as
   `tools/worker_image.py` requires; a fresh build result is a candidate, not
   a selection.
3. **Credential sources** and the `--network` grant for any provider-backed
   attempt. The default network is `none`; a grant is something somebody asks
   for.
4. **`retention_policy_digest`**, **`checkpoint_profile`** and the
   **integration profile**'s `profile_kind`/`profile_version`/
   `instructions_digest`; plus `pool_generation` and the `policy_generation`
   input.
5. **Participants**: the addresses in §3a. The pilot's selection is
   single-human approval, so the owner participant is one address and is not
   also a receipt actor. §3a is a proposal; the production addresses are the
   owner's.
6. **Whether live-provider execution is selected at all.** Everything in this
   pilot to date is deterministic; a live attempt needs its own stated
   provider question under AGENTS.md's v12 verification default.
7. **The dossier locator** for the new pilot Work (W39435 grammar: one flat
   segment with a collision-resistant hex suffix).
8. **The owner's route** — which route the review worker's ending hands a
   human-approved Work on to, and which participant is served on it. §3b pins
   that the route is a deployment operand; which route it is remains open.
9. **The diagnostic selection**: which route carries diagnosis — an added
   handler on the failed Work's own route, or a dedicated diagnostic Work on
   its own route — and which participant staffs it. W325035 proves both
   mechanisms; which one the pilot uses is a policy choice, and automatic
   routing on every exceptional stage is neither proved nor required.

## 7. Rollback (pinned procedure, no deployment selected)

Before admission, abandoning the pilot leaves v11 untouched and preserves any
created v12 intent. After admission: stop new pickup, fence or cancel the
exact v12 assignment through the supported owners, positively account for every
runtime and launch, and preserve holds and output. Stopping the supervisor
alone is explicitly insufficient — `tools/stack.py`'s own
`runtime_boundary`/`_stop_admitted` say so. If runtime state is unknown the
gate is retained; no conflicting v11 replacement may start. The v12 Work stays
the historical authority even if abandoned or non-satisfying.

Two evidence-backed notes for the rollback path: a cancelled assignment is not
a cancelled Work, and the **runtime-quiescence gate survives the
cancellation** — after cancelling, a re-claim is refused with `Work is blocked
by 'runtime-quiescence:1'` until that gate is discharged
(`matrix-325259` scenario 8). An honest abandonment is
`disposition close --outcome non-satisfying` with the operator's own rationale,
which records no acceptance.

## 7a. What the rehearsal established — and the claims it has withdrawn

**Established.** The joined behaviour this Work owed is covered by accepted
child evidence; `baton:work/records/2026/10/finding-v12-pilot-workflow-rehearsal/reconciliation-325675/COVERAGE.md` maps every one of
M324395's five proofs and the FINDING's acceptance list to the exact scenario
and assertion it rests on, and re-verifies both child manifest digests.
Headline: a terminal result reaches a native independent review and a bound
successor (`matrix-325259` sc. 4); independent `Session.verify`/`Session.review`
judgments precede the owner's disposition **with the approval still absent**,
and the owner's `approve`/`integrated`/`close` then complete it with a readback
(`boundary-325197` sc. 2); failed, empty and unknown outcomes reach an explicit
diagnostic owner and are never accepted (`matrix-325259` sc. 5, 6, 2); a lost
launch reply is adopted across a restart without duplication
(`matrix-325259` sc. 1, 3); stale and wrong-principal acts refuse and change
nothing (`matrix-325259` sc. 7, `boundary-325197` sc. 2).

**Withdrawn, with the historical observation preserved.** This section
previously said the packet "cannot promise single-human approval on the native
path". That conclusion is superseded by W325034 and is withdrawn. The
observation behind it stands, narrower and operationally important: the
*automatic integration admission* path writes verification, review and approval
together (`integration/driver.py _accepted_receipts`, called by
`admit_accepted` and `continue_accepted`), so a deployment that runs it for a
human-approved Work pre-empts the owner and the owner's later `approve` is
refused as immutable. The record is `baton:work/records/2026/10/finding-v12-pilot-workflow-rehearsal/rehearsal-324985/RECEIPT-BOUNDARY.md`; the
consequence is §9's rule. **No product defect is claimed by this Work.**

Likewise withdrawn: the earlier reading that no supported operation names a
diagnostic owner (superseded in `baton:work/records/2026/10/finding-v12-pilot-diagnostic-recovery-matrix/matrix-325138/SUPERSESSION.md`), and the
earlier claim that the composed fixture exposed no engine-absence seam.

## 8. Coverage, and the limits that ride with it

`baton:work/records/2026/10/finding-v12-pilot-workflow-rehearsal/reconciliation-325675/COVERAGE.md` is the map. Summary of its sources: four
**separate** deterministic runs over four disposable worlds — W321688's
recovery rehearsal, W321689's disposition candidate, `boundary-325197` (49
checks, 2 scenarios, self-check failed as intended) and `matrix-325259` (117
checks, 8 scenarios, self-check failed for its own named reason). Nothing in
this packet claims they were one continuous session.

Limits carried forward, in the packet because they bound what an operator may
conclude:

1. **No live execution.** Engines and providers are simulated at their own
   boundary and labelled per scenario; verifier, reviewer, owner and diagnostic
   judgments are simulated and labelled. The human integration record's own
   bytes carry forty zeroes for the commit: a zero commit is a labelled
   fixture, not human delivery evidence.
2. **Same-authority restart ≠ restoration or failover** (§5).
3. **Automatic diagnostic routing is not proved or required** (§6.8).
4. **Harness classification.** `boundary-325197`'s runner used the broad
   expected-failure classifier, so a setup or cleanup error could in principle
   have satisfied its self-check. It did not: the retained
   `scenario-0-harness-self-check.json` records `failed_check` = "the review
   stage is completed immediately after submission (INTENTIONALLY FALSE)" with
   no `failure` and no `cleanup_failure` member, and the accepting review
   independently validated those facts. The strict classifier — the intended
   `CheckFailed` by name, with setup and cleanup errors counted unexpected —
   is in `baton:work/records/2026/10/finding-v12-pilot-diagnostic-recovery-matrix/matrix-325259/matrix3.py` and is what any rerun must use. A zero exit
   alone is never acceptance.
5. **Fixture version control is the fixture's own.** The imported composed
   fixture builds a disposable history inside its temporary root under
   `GIT_CONFIG_GLOBAL=/dev/null`. No procedure or rehearsal in this pilot
   mutates this repository's history, index or working tree.

## 9. The ordered supported operations

The sequence an operator runs, with the one prohibition the receipt-boundary
observation justifies. Session transitions are the participant-bound face;
`record`/`disposition` are the installed subcommands.

**A. Result pickup.** `manager` serves the two-stage Job of §3b; each stage is
derived from canonical state by the sweep. Nothing is claimed, started, commanded or ended by hand.
Read state with `status`; read one attempt's retained raw output with `logs`.

**B. Independent verification and review** — on the candidate the lifecycle
published, by actors who are not the owner:

1. `Session.verify(proposal_id, verification_id, observation, operation_id)` as
   the verification actor, after evaluating the evidence. The judge evaluates
   the five requirement clauses itself — `task_id`, `task_digest`, `argv`,
   `input_manifest_digest` and a status of exactly `0`, against
   `Integration.required_tests`; `ordinary_test_evidence` cross-binds the
   observations but does not establish that the required command ran and
   exited zero.
2. `Session.review(proposal_id, review_id, disposition, operation_id)` as the
   review actor.

**The prohibition is enforced by §3b, not by this sentence.** The Job carries
no integration stage, so nothing in it can reach
`admit_accepted`/`continue_accepted` — which write all three receipts
including the approval, after which the receipt is immutable and the owner's
`approve` is refused. Composing an integration stage for a human-approved Work
re-creates that call site; a deployment that does so takes the decision away
from the owner by configuration, whatever any document says. Measured contrast:
`composition-325757` scenario 3 and the retained
`baton:work/records/2026/10/finding-v12-pilot-workflow-rehearsal/rehearsal-324985/RECEIPT-BOUNDARY.md`.

**C. Human approval, integration and closure** — the owner, once:

3. `disposition pending --work <id>` → the owner action due
   (`approval-due` when verification and review are published and the approval
   is absent).
4. `record bind` the canonical dossier **before** any human integration
   citation; the citation refuses without it.
5. `disposition approve --work <id> --proposal <id> --expect-review <receipt>
   --expect-candidate <digest> …` as the owner. An identical request replays and
   preserves the receipt identity; a stale candidate digest, a wrong review
   receipt or a wrong principal is refused.
6. `disposition integrated …` citing the human integration record (its
   evidence digest is bound into the request), then
   `disposition close --outcome satisfying --rationale "…"`.
7. Read it back: the Work answers `closed` with the acceptance clause, the
   commit and the cited record intact.

An honest unhappy ending is step 6 with `--outcome non-satisfying` and the
operator's own rationale, after cancelling the live assignment if one is held.

**D. Diagnostic claim** — when a stage is `exceptional` (provider failed, empty
turn) or a runtime is unknown:

8. Notice it: the stage state in `status`, and `logs` for the retained output.
   Nothing routes it automatically.
9. Either `add_route_handler(<the Work's route>, <diagnostic participant>)` and
   let that participant `Session.claim` the Work — the assignment then names
   that participant and its principal — or `create_work(<id>, <diagnostic
   route>, labels=…)` for a dedicated diagnostic Work claimed by its own
   participant, since one principal holds one active claim.
10. Labels need `manage-work-labels` in the Work's scope; with it,
    `label_work` makes the failure discoverable through `works_with_labels`.
11. An unknown runtime stays gated: the axis is not advanced and the identity
    is not erased until the engine's own absence sentence names that exact
    identity.

**E. Recovery selection.** `record recovery-manifest` after the three §5
obligations are met; `record recovery-check` on the restored set, remembering
that a clean report is a precondition and not an admission. A manager
restarted over the same instance retains exact ownership (`matrix-325259`
sc. 3); a *restored* instance is W321688's contract and the operator's
accounting.

## 10. What this packet asks of the owner

Review the coverage map and the limits, then make the §6 selections — in
particular §6.5 (participants, against the §3a proposal), §6.6 (whether live
provider execution is selected at all) and §6.8 (the diagnostic selection).
Until those are made this packet is reviewable and not executable, which is the
FINDING's own rule and the reason nothing here is filled in with a plausible
default.
