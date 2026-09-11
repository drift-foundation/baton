# Assemble the standalone stage process

Ledger Work: W103083

Parent: `work/records/2026/09/finding-v12-standalone-multi-job-pipeline/findings/finding-standalone-stage-composition/`

## Confirmed scope — 2026-09-06

After both disjoint stage drivers are accepted, bind them to the persistent Job
Manager's production process, runtime profiles, credentials, status, and
restart loop. This leaf owns shared process/configuration paths and the narrow
single-Job composition verification. It does not redesign either driver or
run the final two-Job proof.

The assembly must require no ordinary operator transition after submission,
must keep reviewer and implementer sessions distinct, and must recover from a
manager restart using durable state rather than container stdin/stdout.
Adding and editing focused tests and deployment fixtures inside the final
reviewed path set is explicitly authorized.

## Reviewed assembly boundary — 2026-09-06

**Observed:** `tools.job_manager` already loads an explicit
`module:attribute` serving factory and releases its returned object. No CLI
change is needed. `tools.single_worker` contains the accepted OCI, credential,
source/workspace, file-exchange, ending, and observation composition, but it is
closed around one implementation Work and hard-codes the v11 review pass.
Copying that implementation for reviewers and integrators would create three
deployment opinions over the same security boundary.

**Required assembly:** after W103076 and W103077 are accepted, extract or
parameterize only the reusable worker-launch half of `single_worker` while
preserving its schema-4 bootstrap behavior and tests. Add one closed
stage-execution configuration that binds the Authority, Job/Control/
Integration stores, active pool generation, per-worker role/profile/image/
adapter/network/credential inputs, checkpoint profile, canonical target,
integration profile and actor sessions. Build all required worker operations,
wrap them with `PooledManagerOperations`, then wrap that with the two accepted
stage drivers. Construction failure releases every already-opened handle;
status receives a genuinely observation-only factory.

The configuration must reject implementation/review Work mismatch, duplicate
participant or principal where independence forbids it, a missing receipt or
integration capability, and a path inside the checkout for mutable deployment
state before any durable act. It carries no bearer or credential bytes.

**Frozen path ownership:** `v12/python/tools/stage_execution.py`,
`v12/python/tools/single_worker.py`,
`v12/python/tests/tools/test_stage_execution.py`,
`v12/python/tests/tools/test_single_worker.py`, and
`v12/python/tools/parallel_test.py`. `tools/job_manager.py` is explicitly out
of scope unless accepted driver interfaces prove it cannot load/release the
factory it already supports. Any such change requires targeted review.

**Required verification:** configuration ownership and no-secret sweep;
partial-construction cleanup; independent implementation/review sessions and
mount postures; one correction on one persistent line; manager restart before
and after every accepted driver cutpoint; status/log locators while queued,
running, reviewing, changes-requested, integrating, completed, exceptional,
and held; and an interrupted integration that remains blocked for manual
recovery. The final two-Job concurrency/resource proof remains W71879's.

## Interface revalidation — 2026-09-06 — baton.claude

PLAN item 1 is the gate that runs before anything shared is touched, and it
finds one material gap. Everything else the assembly needs is present.

**WHAT IS PRESENT, checked against the tree rather than the plan.**
`tools.job_manager` already loads and releases a `module:attribute` serving
factory, so no CLI change is needed. `PooledManagerOperations` already reserves
a review worker after excluding the implementation worker, participant and
principal. `tools.single_worker` carries the accepted OCI, credential,
source/workspace, exchange, ending and observation composition behind
`_SingleWorker`, `_Operations`, `_Observation` and four factory functions, and
its launch half is separable. Both accepted drivers expose exactly what the
plan assumed: `prepare_implementation`, `prepare_review`, `end_implementation`,
`end_review`, `open_correction`, and `publish_candidate`, `admit_accepted`.

**THE GAP: NOTHING IN THIS BUILD CAN RETAIN A PROPOSAL MANIFEST, AND
PUBLICATION SELECTS ON ONE.** `driver.publish_candidate` takes
`proposal_manifest_digest` and resolves it with `load_manifest(manager, ...,
"proposalManifest")` -- a manifest the manager must already hold. This build
has no path that retains one:

- `request_freeze` retains exactly ONE manifest, the sealed result, through
  `manifests._retain_canonical` inside `output._record`.
- `retain_manifest` has two callers in the whole tree, `single_worker` and
  `dogfood_operator`, and both retain `inputManifest`.
- `proposal.publish` IS in the worker-control vocabulary and `proposalPublishBody`
  carries `proposal_manifest_digest` -- and neither string appears anywhere in
  `baton_v12.worker_manager` or `tools`. The control act is unimplemented.
- No accepted operation answers a collected artifact's BYTES. `custody_act`
  performs one of six verbs over a workspace root and answers a verb-shaped
  document, not a file a deployment names.

So the assembly can build every operand of the publication seam except the one
it selects on. This is the step that must run while the producer assignment is
still live, so it cannot be deferred to a later round of the same attempt.

**A SECOND, SMALLER MISMATCH, recorded because it is real and is NOT a
blocker.** W103076's seam is `publish(attempt_id, result_id, manifest_digest,
artifacts, proposal)` and W103077's verb is `publish_candidate(manager,
publisher, *, attempt_id, proposal_manifest_digest)`. Adapting one to the other
is ordinary assembly work and needs no decision -- given a digest to pass.

**Disposition.** Reported for targeted review rather than worked around. The
assembly must not invent a proposal manifest of its own: a deployment that
built the document the Authority publishes against would be making the claim
the worker is supposed to make, which is the same class of defect as a core
that invents its own verification. Two resolutions look sound, and the first
is recommended:

1. New Work under the parent implementing the `proposal.publish` control act in
   the Worker Manager's exchange, so the worker declares its proposal manifest
   and the manager retains it exactly as it retains the sealed result.
2. A targeted change to `publish_candidate` taking the proposal DOCUMENT from
   an accepted reader rather than a pre-retained digest -- which still needs
   something that answers a collected artifact's bytes.

Every other part of this assembly is unblocked and can be built under either.

## Independent interface-gap review — 2026-09-06

**Confirmed:** the missing retained `proposalManifest` producer is real.
W103077's focused tests mock the document returned by `load_manifest`; no
production caller retains that definition, and the concrete worker currently
emits empty proposal `result_metadata`. W103083 must not invent the missing
evidence or defer publication past the producer fence.

**Clarified:** `proposal.publish` is already the frozen manager-to-Authority
act implemented by W103077, not a worker declaration to add to Worker Manager.
The missing boundary is now W103874, a sibling under W103068 that produces and
retains the complete manifest from a worker-owned opaque proposal claim plus
facts re-read from their manager/Authority owners. The generic Worker Manager
remains artifact-neutral. This assembly resumes only after W103874 is accepted.

## Approved bounded delivery — 2026-09-06 — baton.prompt for Slawomir

This ruling supersedes the earlier **Required verification** paragraph as a
completion gate and the interface revalidation's proposed addition of a
worker-side `proposal.publish` operation. The independent correction above
is authoritative: W103874 produces the missing manifest; publication remains
the existing manager-to-Authority act.

K owns the shared assembly's existing five-path set. The first accepted
composition must run one submitted Job through implementation, independent
review, one same-line correction, acceptance, integration and terminal handoff
without ordinary operator transitions. It must use the real retained-manifest
producer rather than a mock that supplies the missing document. A deterministic
local runtime may stand in for a model; the assembled stores, drivers and
manifest producer must be exercised together. The later two-Job live proof
continues to own the actual concurrency demonstration.

Keep focused checks for role/session separation, configuration refusal before
launch, observation-only status, one representative restart/replay cutpoint,
and preservation of operator-held uncertain integration. Existing safety
invariants and cleanup behavior remain requirements. Do not expand this leaf
into an exhaustive failure-injection or status cross-product campaign.

The expanded restart/status/partial-construction matrix moves to the independent
follow-up `work/records/2026/09/finding-v12-stage-composition-hardening/`,
intended for baton.tuner after a stable composition is available. It is neither
a child nor a blocking prerequisite of this provider or the first two-Job proof.
Concrete defects preventing the bounded lifecycle still block delivery; merely
unexecuted additional coverage does not.

Before edits, inventory the five shared paths against the accepted driver
baseline. Preserve the existing registry additions in `parallel_test.py` and
report only this leaf's additions. No agent stages, commits, or restores them.
Checkpoint separately when the serving factory is wired, when the composed
lifecycle passes, and when the focused restart check passes. Report a newly
missing public capability as its own bounded Work before widening paths.

Scheduling correction later on 2026-09-06: the hardening follow-up W103950 is
approved dependent work, not discretionary parked work. Slawomir directs a
dependency on this assembly so tuner becomes eligible automatically when the
prerequisite closes. This supersedes any requirement for a separate unpark or
new scheduling approval, without adding hardening to this assembly's gates.

## Independent assembly review — 2026-09-07 — baton.codex

**Confirmed; changes requested:** handoff M110452 is a partial assembly, not
the completed bounded delivery. The real serving path forwards to bootstrap
worker callbacks that refuse review/integration stages; driver-facing attributes
are unused. The public factory omits required actor sessions and bypasses their
validation, and no observation-only factory exists. The 45 focused tests pass
but exercise helpers directly, stop before integration/terminal handoff, and
do not demonstrate manager restart or operator-held uncertain integration.

The approved delivery and five-path boundary remain unchanged. This clarification
supersedes any completion implication of PROGRESS checkpoints describing the
drivers as wrapped or the helper-only tests as the composed lifecycle/restart.
It does not supersede the historical partial evidence or widen W103950 coverage.

Exact findings, corrections and independent evidence: `review-2026-09-07T13-29-13Z.md`;
retained candidate manifest and reproduction: `evidence/review-110456/`.
PLAN items 2–4 require implementation correction; independent sign-off is withheld.

## Independent correction review — 2026-09-07 — baton.codex

**Confirmed; changes requested:** M110672 connects the mount/ending hooks and
provides an observation object. The independent first-launch probe reaches one
commanded implementation runtime with real local stores and fake engine/profile.
This supersedes the earlier finding that the implementation serving callbacks
are wholly disconnected; it does not establish the required complete lifecycle.

**Confirmed:** actor method presence is not capability authorization. Composition
accepts an approval Session whose actor holds no approve capability; malformed
session identity refuses after control-store configuration, and a mismatched
pool generation refuses only after activating the pool. Fix validation ordering
and effective-scope authority checks inside the existing five-path boundary.

**Confirmed provider gaps:** the reviewer verdict channel and production
integration run port are absent. Filed W110772 and W110774 with canonical
sibling records `../finding-review-verdict-channel/` and
`../finding-integration-runtime-port/`. Their interface/path proposals need
review before implementation; fixtures cannot substitute for their delivery.

**Confirmed later-pass defect:** post-checkpoint-fence ending replay refuses
both in writable-mount preparation and the driver active-writer guard. W110783
records it for restart hardening, without gating a first proof that selects an
unaffected representative cutpoint. Public checkpoint/writer readers exist;
the missing-reader diagnosis in M110672 is not sufficient.

Exact verdict, evidence and limits: `review-2026-09-07T14-12-42Z.md`, `evidence/review-110736/`.
The approved bounded lifecycle/restart/held-integration acceptance remains live.

## Independent configuration re-review — 2026-09-07 — baton.codex

**Confirmed:** M110896 corrects both P1s from review 14:12:42. Real scoped
capability checks replace method-presence authorization, and malformed actor /
wrong pool-generation probes now refuse without group, pool or integration
store changes. A valid composition retains all four receipt grants.

**Confirmed; bounded changes requested:** the policy-generation positive-integer
check still accepts 9007199254740992, constructs deployment state and then the
Authority refuses that operand as outside its interoperable range. Apply the
existing public MAX_SAFE_INTEGER limit before setup. This explicitly does not
require equality with the Authority's live policy_generation reader; current
approval binds the configured value without that equality rule.

**Confirmed record correction:** the newest PROGRESS entry was prepended.
Its author must preserve the earlier account as the prefix and append the new
entry and response, without rewriting older episodes. Reviewer leaves PROGRESS
to its implementation owner.

Exact review/evidence: `review-2026-09-07T14-44-03Z.md` and
`evidence/review-110968/probe-output-corrected-call.json`. Five candidate hashes
match the handoff; existing reported suites were audited and the new independent
probes run. Full lifecycle/restart/held-integration acceptance remains pending.
Complete this small correction round before recording the W110772/W110774
gates; their gates should not prevent an available configuration/record fix.

## Independent bounded correction acceptance — 2026-09-07 — baton.codex

Claim111157 reviewed pass111137. Both P2 corrections from review14:44:03 are
accepted with no blocking finding in this round. The Authority's public
MAX_SAFE_INTEGER bounds both configured generations before any setup; the
existing lower/type/bool checks remain and no live-generation equality was added.
Actual operations_from probes reject maximum-plus-one for both generations with
unchanged group/pool/integration-store state; maximum policy generation composes.

PROGRESS now appends the previous new section and this response after the older
account. The earlier review did not preserve a PROGRESS snapshot, so complete
historical byte equivalence is not independently proved; current order and
historical contents were reviewed and a current full snapshot is now retained.
Reviewer did not edit PROGRESS. All five candidate hashes match; all25 prior
test classes are AST-identical and five cases are additive. Reported74 passing
stage tests and730 tools tests with the same prior registry error were audited,
not rerun. Three independent factory probes and whitespace checks pass.

**Supersedes immediate bounded-changes-requested status:** these configuration/
record corrections are complete. Review: review-2026-09-07T15-10-51Z.md;
exclusive evidence: evidence/review-111157/. Now record provider dependencies
W110772/W110774 before remaining assembly work. The complete factory lifecycle,
representative reconstructed restart and held integration remain unproved and
required. No full Work sign-off, live execution or import authorization.

## 2026-09-07T15-51-57Z — mandatory retained-result cleanup proof

**Confirmed decision:** owner reroute111426 accepts W105982's reconciliation in
`baton:work/records/2026/09/finding-v12-private-line-custody-locators/review-2026-09-07T15-46-38Z.md`.
Its accepted configured-access/checkpoint evidence may be reused. The remaining
sealed-result retention, ordinary-cleanup and reopening proof is now explicitly
mandatory in this assembly's existing first-delivery lifecycle acceptance and
the parent W103068 acceptance. This is not deferred W103950 hardening.

Bind the launched attempt and durable line/object pin to the actual completion
and frozen sealed result. Exercise real public intake and retention operations
and retain their receipts, then ordinary manager-authorized cleanup. Reopen the
retained manifest and artifact bytes at their recorded locators and verify their
digests; reopen the same persistent line and validate its durable pin after
cleanup. Record that sibling custody stayed outside every writable worker mount.
Path inequality, checkpoint Git-reference survival, fixture teardown and canned
receipts cannot substitute. Cross-link this proof and its independent acceptance
in the parent record and the owning W105982 dossier.

This preserves the approved five-path focused-test/deployment-fixture authority
and the separate custody additive-only scope; shared paths remain serially owned.
Identify additional path, assertion-change or execution scope before execution
for scoped disposition. The deterministic local-runtime allowance remains; this
administrative decision grants no new live runtime or implementation authority.
Claim111429 records this requirement before removing only W103068's dependency
on full W105982 closure. W105982/W106673 stay open, and production confirmed
shutdown and the experiment's separate adoption gate remain unchanged.

## 2026-09-08 — approved port/assembly continuation contract

Slawomir approved including normal asynchronous continuation in W110774's public
integration driver. Read ../finding-integration-runtime-port/
HANDOFF-CONTRACT-2026-09-08.md and its dated FINDING decision before this Work's
remaining implementation. This supersedes the earlier open serving-decision
posture: prepare the exact attempt before admission; start once; on subsequent
ticks in the same live execution refresh runtime evidence and use the approved
normal-continuation operation. Do not repeatedly call admit_accepted for a running
delivery. Restart loses that local continuity and retains the existing hold path.

The port owns public driver receipt/finalization composition; this Work owns the
factory, tick and read-only observation wiring. Integration's typed result must
be observed without manufacturing an ordinary worker-exchange terminal. The
one-Job lifecycle and mandatory intake/retention/cleanup/custody proof stay here.
Existing five-path scope remains unchanged. Serial shared registry ownership:
W110774 completes its additive parallel_test.py entry before this Work edits it.

## 2026-09-08 — proposed disposition of obligation115920

Author: baton.prompt, decision support pending Slawomir's response to115920.
This entry supplies concrete recommendations, not an enacted owner approval.

1. Derive required_tests from the configured implementation task and its bound
   input manifest for the accepted checkpoint's producer, including correction
   attempts. Supply task_id, the digest of the exact task bytes, verification
   argv, and input_manifest_digest to both admission and normal continuation.
   Revalidate Job/producer/input correspondence; do not derive the requirement
   from the worker's reported test observation or accept missing/mismatched
   configuration. The accepted driver's _owned_requirements docstring already
   names this W103083 derivation; a new top-level configuration member is not
   needed. Preserve the closed configuration schema and admission comparisons.
2. W103083 owns assignment lookup via the public runtime.adopt_delivery and
   runtime.published_assignment readers at the configured delivery home, exact
   stage attempt and workspace group. On later mutation ticks, refresh first
   and select continue_accepted only when the existing port's
   may_continue(assignment, delivery) confirms the exact live marker. Reading
   a persisted assignment grants no continuation permission. A fresh serving
   incarnation or lost marker preserves the driver's existing restart/hold
   behavior; absent or malformed delivery must not invent an assignment or
   cause a duplicate start. Read-only status never refreshes or settles.

Both corrections stay in the existing five-path assembly scope; W110774's
accepted provider remains closed. Add focused coverage of requirement binding
and mismatch refusal, same-process continuation, restart marker loss, malformed
delivery, and read-only observation while preserving existing assertions.
Reuse accepted provider evidence. No broad rerun is needed merely to decide
this obligation; required verification still follows the existing work plan.
Upon approval, the implementing claimant appends the confirmed response
reference here and updates the plan before editing implementation.

## 2026-09-08 — owner approval of obligation115920, confirmed

Slawomir approved the proposed disposition above in M115946, on this Work's
thread: derive `required_tests` from the configured producer task and its bound
input manifest, independently of reported results; the assembly owns assignment
lookup through the public `adopt_delivery` and `published_assignment` readers
and uses the existing `may_continue` check after refresh; preserve restart
holds, read-only status, the five-path scope and existing assertions, with
focused regressions added. W110774 remains closed.

Recorded by baton.claude under claim115958, which relied on that message before
editing and appends this durable reference for the next reader. Both items are
implemented in `tools/stage_execution.py` and covered in
`tests/tools/test_stage_execution.py`; PROGRESS carries the account.

## 2026-09-08 — independent interface correction review, claim116043

**Confirmed; changes requested.** Pass116036's two approved interface changes
do not yet work with the real assembled operands. `required_tests` sends the
factory's already-held worker deployment through the closed raw-document
validator and refuses its four derived members. The public delivery reader
gets an integer gid because StageDeployment discarded the nominal group.
A fresh published-but-never-started port then skips prepare and refuses for
missing execution-local prepared credentials. Independent0.364s evidence
exercises actual factory/manager/delivery/driver/port boundaries with no daemon
or model: `evidence/review-116043/audit.json` and retained candidate snapshots.

These findings supersede any implication that the two interface corrections
are independently accepted; the owner's derivation and continuation decisions
remain unchanged. Exact corrections and proof boundaries:
`review-2026-09-08T04-06-54Z.md`. Preserve held producer bytes, carry the nominal
WorkspaceGroup, and prepare idempotently before never-started admission while
retaining no-refresh and started/uncertain restart holds. W110774 stays closed.

**Proposed exact assertion disposition:** because M115946 says preserve existing
assertions, ops must approve changing only the new never-started dispatch test's
call-list expectation to include prepare after observed, keeping its no-refresh,
single-admission and no-continuation assertions. Other correction coverage is
additive within the existing five paths. No source or test was edited in review.

All five hashes match the handoff;26 prior classes unchanged and seven cases
added. Gate log retained with exact reported hash and12 unchanged historical
diagnostics now tracked by W115824. Full lifecycle, reconstructed restart, held
integration and mandatory W105982 custody proof remain incomplete and required.

## 2026-09-08 — exact assertion approval already recorded in M118923

baton.prompt re-read T103083 at snapshot118957. Slawomir's M118923 explicitly
approves the review116043 never-started test changing its recorded calls from
observed alone to observed then prepare, while preserving no-refresh, exactly
one admission and no continuation. It also directs completing all three
reviewed corrections in the existing five paths with real-factory and fresh-port
controls; started/uncertain holds and unrelated assertions remain unchanged.
The test spelling in that message contains a whitespace split in "refreshed";
the named review and exact behavioral delta unambiguously identify
TheIntegrationStageConsumesTheAcceptedPort.test_a_delivery_with_no_started_runtime_is_not_refreshed.

This confirmed approval supersedes the pending disposition paragraph above for
that exact change only. Claude's later asynchronous obligation118938 repeats
the same request. It adds no scope and needs no new product ruling. The existing
M118923 approval is the implementation authority; ops still owns answering the
duplicate obligation. No source or PROGRESS changes were made by this entry.

## 2026-09-08 — partial acceptance and mandatory split, claim119091

**Confirmed:** the held/raw and nominal-group defects are corrected through
actual factory probes. The fresh never-started retry still skips prepare and
refuses. Review: review-2026-09-08T12-41-47Z.md; evidence/review-119091/.
M118923 and M118986 both predate handoff119024. This explicitly supersedes
any current claim that assertion approval is missing; no further permission
is required for the exact already-approved change.

**Confirmed scheduling decomposition under EFFECTIVE-BATON.md:** repeated
partial handbacks leave substantial independently deliverable proof unstarted.
W119113 owns the existing two-path never-started correction; W119114 owns the
remaining full one-Job lifecycle/custody/restart/held proof within the original
five paths, serially after correction acceptance. They are separately bound
siblings at ../finding-assembly-unstarted-preparation/ and
../finding-composed-one-job-proof/. W103083 keeps all historical evidence and
final joined acceptance. This supersedes the plan to send another undivided
correction-plus-proof pass through this Work. No accepted behavior, assertion
limit, path set or runtime authority is expanded; all original capability gates
remain mandatory, including custody. Live dependencies are recorded in Baton.

## 2026-09-09T17:57:08.562564+00:00 — joined assembly accepted

review-2026-09-09T17-57-08Z.md accepts the exact final five-file composition under reviewer
claim129777, joining accepted W119113 and W119114 with W122060 and A/B/C.
This supersedes the remaining-incomplete disposition from the September8 split.
The mandatory ordinary-cleanup/retained-result/line-pin proof is delivered and
cross-linked to W105982 and the parent. CONSUMER-HANDOFF-2026-09-09.md supplies exact
commands, fixture/profile/locator selectors and evidence limits. No new source
changes or duplicate suite run;31 parallel scan failures remain separate and
unwaived. Standing W71830 test authority supersedes old per-test gates.
