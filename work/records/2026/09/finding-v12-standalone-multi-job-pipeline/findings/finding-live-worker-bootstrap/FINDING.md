# Bootstrap one live worker from the persistent v12 Job Manager

Ledger Work: W76207

Parent: `work/records/2026/09/finding-v12-standalone-multi-job-pipeline/`

## Confirmed gap — 2026-09-03

W71875 delivered a persistent Job Manager, submission/status documents and a
restart-safe control loop. Its production surface deliberately owns only the
`admit` and `claim` acts. `job_manager.py serve` requires an explicit trusted
deployment operations factory, but the repository supplies no production
factory that connects an accepted claim to a live worker runtime. Test fixture
factories are not a deployment, and the retired supervised dogfood operator is
not the standalone manager.

This leaves a bootstrap cycle: W71917 was approved as the first ordinary Job
run through the manager, but the runtime start it needs was deferred to
W71917/W71877. A submitted W71917 document could be recorded and offered, but
could not execute.

## Confirmed correction

Add the smallest trusted production composition that drives one claimed
implementation stage into one live worker using existing public v12
Authority, Worker Manager, OCI adapter, credential, launch and workspace
capabilities. This leaf is coordinated and implemented through v11 because it
creates the mechanism needed for v12 to execute its next leaf itself.

The bootstrap may use the existing workspace/source delivery boundary only to
start that first worker. It must not call `dogfood_operator.py`, use a test
fixture as production code, construct another full candidate archive, or
invent pool, review, correction, integration, or Git policy. W71917 owns the
replacement immutable-source and disk-backed-workspace boundary; W71877 owns
pool scheduling.

## Acceptance

- A documented production command starts the persistent Job Manager with an
  explicit trusted operations factory; no test module or private store access
  is used.
- The factory supplies the Authority/Worker Manager capabilities explicitly,
  resolves configured identity through the trusted Authority API/bootstrap
  face, and never broadens the restricted Authority Session.
- Bearer delivery is single-use and non-persistent. An accepted offer advances
  through claim into one real OCI worker runtime using existing public manager
  operations.
- A tiny implementation fixture proves the runtime is live and observable from
  Job status without per-transition operator commands.
- Restart adopts the durable Job/control state and does not duplicate the
  offer, claim, workspace, or runtime.
- Failure is reported as an exceptional stage without wedging the manager;
  no pool-size, retry, review, or integration policy is introduced.
- The resulting seam is sufficient to submit W71917 as the first ordinary
  self-hosted v12 workload.

## Test-change authority

This Work authorizes adding tests and editing existing tests under
`v12/python/tests/job_manager/`, `v12/python/tests/manager/`, and
`v12/python/tests/tools/` only for the production operations factory,
single-worker launch composition, status observation, restart adoption, and
negative capability boundaries above. Any deletion or weakened expectation
requires explicit independent review.

## Reviewer revalidation — 2026-09-03

### Observed baseline

- The current baseline is `4641ce0`. With `PYTHONPATH=src`, discovery under
  `v12/python/tests/job_manager/` runs 188 tests and all pass. The first
  attempted discovery omitted that required source-layout setting and failed
  only at import; it is not product evidence.
- `tools/job_manager.py` still accepts the trusted factory as an exact
  `module:attribute` and calls it with the already-open Job and control stores.
  Repository search finds no production factory. The tool also has no
  lifecycle contract for releasing an Authority handle opened by a factory.
- `job_manager.delegation.ManagerOperations` owns exactly the admission seam:
  one participant-bound `AuthorityPort`, one ephemeral bearer mint, and one
  delivery capability. `admit` issues and delivers the bearer once; `claim`
  submits the accepted claim. `projection._owed` intentionally stops at the
  claimed state, so neither an ordinary tick nor restart reconciliation has a
  level-triggered post-claim launch call.
- Putting the launch only inside `ManagerOperations.claim` is therefore not a
  valid correction. A crash after the Authority commits the claim causes the
  next manager to adopt the canonical `offer.settle` receipt without calling
  `claim` again, permanently skipping every launch step after it.
- The required lower-level acts already exist and are restart-addressable:
  `record_attempt`, `activate_assignment`,
  `workspaces.assignment_workspace`, `workspaces.compose_input_root`,
  `retain_manifest`, `credentials.CredentialHome`, `launch.materialize` /
  `launch.adopt`, `OciAdapter`, `request_runtime_start`, and
  `reconcile_runtime`. `assignment_workspace` re-adopts the same structurally
  proved attempt roots, while launch and credential delivery have explicit
  adoption/teardown faces. No production composition currently orders them.
- `attempt_runtime_of` is the public durable runtime observation used by the
  Job projection. The Worker Manager separately journals
  `runtime.start-failed`, but the Job Manager has no public observation of
  that record. Its projection presently treats any attached `runtime_id` as a
  running stage even when the start operation has a durable failure record.

### Proposed implementation boundary

The approved correction is a one-worker deployment composition plus one
level-triggered Job-manager launch seam. It is not a pool. The deployment has
one configured participant, canonical principal, runtime profile and adapter;
it accepts only the implementation stage and exact profile/input policy it was
configured for. A second worker, eligibility selection, affinity, review, and
capacity accounting remain W71877.

The production factory must perform all static configuration validation before
it issues an offer. It opens the Authority with an expected UUID, resolves the
configured participant and principal through the trusted bootstrap face, mints
exactly that participant's restricted session, and gives only the session to
`AuthorityPort`. The runtime composition never receives the Authority store
path, bootstrap object, another participant's session, or raw SQL access.

Bearer delivery is the worker's immediate accept decision. The callback owns
the issued document, compares its participant, Work, attempt and configured
profile/input binding, calls public `accept_offer` once with the in-memory
bearer, and retains neither value nor verifier. On restart, an unaccepted offer
is abandoned by the integrated recovery rule; an accepted one is continued
from durable claim state without reconstructing the bearer.

After admission/claim reconciliation, every serving tick must reacquire the
bound canonical stage observation. A claimed implementation with no settled
start is passed to one explicit launch capability. That capability composes,
in order, the public attempt record, exact claimed assignment activation,
bootstrap input/workspace delivery, manifest retention, lazy credential
materialization, immutable launch delivery, constrained OCI adapter, and
`request_runtime_start`. The next tick calls the same capability until the
canonical runtime is running or carries a durable exceptional ending. Status
is read-only and never calls this capability.

Restart branches on canonical facts, not on filesystem presence alone:

- a missing attempt is recorded; an existing exact attempt is replayed;
- an unfixed attempt is activated from the claimed offer's exact assignment;
- the same attempt workspace is structurally re-adopted, never allocated under
  another identity;
- a complete input and launch delivery is adopted by its public byte/identity
  proof; contradictory or partial material refuses rather than being repaired;
- credential material is created only after activation. A crash before the
  runtime-start journal may tear down the exact orphan before rematerializing;
  a delivery published for a named runtime is adopted through its lifecycle
  record and never reread from configuration as if new; and
- `start-requested` is reconciled through the OCI adapter before any new start.
  `running` is observed, not started again; `uncertain` is exceptional and is
  not an implicit retry authorization.

The Worker Manager's durable start-failure record needs one public read (or an
equivalent addition to its existing runtime projection) so the Job projection
can report `exceptional` even when reconciliation attached a runtime identity
after the adapter fault. This is a read of the owner record, not a second
runtime state. A plain configuration error is refused before admission;
post-claim start failure is recorded by the existing Worker Manager operation,
contains that stage, and does not stop later stages from being observed.

### Expected patch boundary

- Add the level-triggered launch capability to
  `src/baton_v12/job_manager/delegation.py` and invoke it from
  `job_manager/manager.py` only after the admission/claim pass has reacquired
  current bound observations. Keep `admit` and `claim` as the only receipt acts
  W71875 owns; launch replay is derived from the Worker Manager's own attempt
  and operation journal rather than a new Job-store state machine.
- Add the narrow start-failure read to `worker_manager/attempts.py` and the
  package export, and use it in `job_manager/projection.py` to derive
  `exceptional`. Do not expose a store path, connection, or generic journal
  scan.
- Add one production composition module under `v12/python/tools/` and a
  documented trusted deployment configuration. The configuration fixes the
  Authority UUID, participant/principal, exact profile and adapter identities,
  Docker image digest, engine/network posture, workspace/launch/credential
  homes, bootstrap input manifest/material, launch contract and role. Provider
  credential bytes and the offer bearer remain live capabilities, never
  members of that document or an environment variable.
- Ensure `tools/job_manager.py serve` releases every factory-owned handle on
  normal stop and construction failure. `submit` and read-only `status` remain
  capability-free.
- Add focused cases under the already authorized Job-manager, manager and tool
  test directories. No change belongs in `dogfood_operator.py`; the new module
  may follow its public-operation ordering as evidence but must neither import
  it nor extract its review, output, retention, handoff or archive machinery.

### Focused regressions

Positive coverage must drive an issued bearer through immediate acceptance,
the next derived claim, exact activation and a real/fake OCI start, then read
the runtime identity and `running` stage through the ordinary status command.
The fixture is deliberately tiny and is not a second candidate archive.

Negative and recovery coverage must prove wrong Authority UUID, participant,
principal, profile, digest, input, session capability, credential selection,
workspace/launch replacement and foreign runtime labels refuse before the
corresponding outward act. Crash points after accepted offer, committed claim,
attempt record, activation, workspace/input creation, credential creation,
launch creation and start request must resume without a duplicate offer,
claim, attempt, root, credential delivery or runtime. A settled start refusal
must project `exceptional`, while a second independent stage remains
observable and the serving loop continues. No case may introduce automatic
retry, pool selection, review, correction, integration, Git, or dogfood policy.

### 2026-09-03 implementation discovery: Job attempt paths do not allocate

**Observed.** The first production-composition fixture reached a real accepted
offer and claim, then the public `assignment_workspace` operation refused
before any engine act. Job Manager episode 1 durably derives
`attempt:job-a/implementation`; `assignment_workspace` joins that canonical
attempt identity below the configured workspace storage and calls `os.mkdir`
only for the complete home. The intermediate `attempt:job-a` directory is
absent, so the operation answers `integrity/path` with `FileNotFoundError` on
every serving tick. The real launch and credential homes use recursive
creation, but they are separate roots and cannot make the workspace parent.

**Confirmed.** Changing the Job Manager's stored attempt spelling is outside
this bootstrap correction: schema-1 journal and episode compatibility pins the
existing `attempt:{job-id}/{kind}` identity. Supplying a different identity to
`assignment_workspace` would also contradict the attempt whose custody and
runtime lifecycle the Worker Manager owns. A deployment-side private mkdir is
not an acceptable hidden workaround for a public operation that cannot consume
the other component's canonical identity.

**Required correction.** Before the live-worker acceptance can pass, the
workspace owner must safely create or structurally adopt the manager-owned
intermediate directories of a valid nested assignment identity, while keeping
the final assignment home's existing no-link/exact-path proof. This is an
application-code correction and is handed back to the implementation role;
the tuner does not alter that owner boundary on its own authority.

### 2026-09-03 supersession: derive valid new episode identities

**Superseded.** The preceding required correction is not the current rule.
Making the workspace owner encode Job attempt paths passed that boundary and
immediately proved the same stored offer and attempt identities invalid under
the frozen worker-control `opaqueId` grammar: `/` is forbidden and the width is
bounded. An assignment manifest carrying the exact claimed identities was
therefore refused before input composition. A filesystem-only encoding would
hide one symptom while leaving the canonical identity impossible to deliver to
the worker.

**Confirmed.** The Job Manager is the owner that minted the incompatible
identities. New episode identities must be deterministic, bounded `opaqueId`
values derived from stage plus episode without embedding either as path text.
Episode rows remain the durable source of truth, so identities already stored
by schema-1 migration or an earlier schema-2 process are preserved exactly;
restart never recomputes them. New and replacement episodes use the corrected
derivation. The workspace and custody owners retain their existing rule that
an identity is one name and never a path.

### 2026-09-03 decision: the preparation that can never reach a start

**Partly superseded 2026-09-03 by "the preparation failure is its own record"
below.** The gap this section states, and the reason `request_runtime_start`
cannot close it, both stand. What is superseded is the correction's choice of
KIND: filing the preparation under `runtime.start-failed` gave one durable row
two meanings, and the section below replaces that with a record of its own.
The "Boundary" paragraph at the end of this section is superseded outright.

**Observed.** Independent review `review-2026-09-03T17-23-00Z.md` [P1] found
that workspace adoption, input composition and manifest retention ran outside
the composition's failure settlement, so a foreign workspace, a partial input
root, a changed source or a retained-manifest collision returned to
`job_manager.manager._launch` with no failed-start record: an ordinary refusal
was reported `deferred` and asked again on every tick, and a durable one
aborted the whole sweep.

**Confirmed.** The settlement could not simply be widened to cover them.
`request_runtime_start` was the ONLY public path to the durable
`runtime.start-failed` record, and it reaches that record through the adapter
-- so it first calls `authorize_input_root`, which reads the two protocol
documents back off disk. Every one of these boundaries fails BEFORE that root
exists, and an attempt recorded against an input manifest cannot pass
`inputs=None` either. The authorization the ending would have to satisfy is
exactly the thing that could not be done, which is why the reviewer's wording
is "without requiring an input-root authorization that cannot yet succeed".

**Correction.** `worker_manager/attempts.py` gains one narrow public
operation, `refuse_runtime_start(store, *, attempt_id, refusal)`, exported
beside the start it stands in for. It writes THE SAME
`documents.runtime_start_failed` record under the same derived identity, so
`attempt_start_failure_of` reads a refused preparation and a refused start
without being told which happened and no second vocabulary enters the
projection. It journals no start operation, occupies no lane and calls no
adapter, because none of that happened; and it reconciles nothing, which is
made honest by refusing any attempt whose execution axis has left
`not-started` -- such an attempt has been through the start path and its
ending belongs to the operation that took it there. The refusal is raised back
with its closed pair unchanged and only its message grown, exactly as a
refused start's is.

**Boundary.** A start ALREADY REQUESTED keeps its existing ending. The
deployment does not ask for a settlement it cannot have there: the preparation
refusal travels out as itself, the control plane reports it, and the next tick
asks the level-triggered question again. Replacing it with this deployment's
account of why it could not write a record down would hide the refusal an
operator has to act on.

### 2026-09-03 decision: credential restart proves the live runtime first

**Observed.** The same review [P1] found the composition read the credential
lifecycle record and called `CredentialHome.adopt` with the runtime id taken
out of that same record -- the record compared with itself -- and never
composed `OciAdapter.recover_credentials`. Bearer bytes were re-registered
before anything proved the live container was the one the record names or that
it holds the intended mount.

**Confirmed.** `recover_credentials` (W6634) is the owner boundary for exactly
that question: it derives the attempt's whole label set, identifies exactly one
live runtime, compares the record's runtime id with the engine's answer,
inspects the runtime's actual mounts, and only then calls `adopt` itself.
Ordinary `reconcile_runtime` performs none of those checks.

**Correction.** The attached-delivery restart path composes that public
operation through an adapter carrying no delivery -- the delivery is what it
answers -- and carries the proved delivery into the adapter used for runtime
reconciliation. A disagreement raises, and the operation's own bounded stop and
cleanup ride out with the refusal untouched: nothing re-registers a bearer,
accepts output or repairs what disagreed. An `absent` lifecycle state is the
other branch rather than an ending, because the record is written only once
there is a runtime to name.

**Also corrected.** The partial-input branch raised `refused/path`, which is
not one of §9's closed pairs, so the one branch that finds incomplete material
rejected its own raising site with an `AssertionError`. It raises
`integrity/path`, which is the pair it is.


### 2026-09-03 supersession: the preparation failure is its own record

**The "no start act" half is superseded 2026-09-03 by "one meaning for the
preparation record" below.** Keeping the record separate from
`runtime.start-failed` and granting it no destroy authority stands. What is
superseded is the claim that it proves no start act ever happened: the
continuation path writes it after an earlier process performed one.

**Observed.** Independent review `review-2026-09-03T18-16-57Z.md` [P1] found
that recording a post-claim preparation as `runtime.start-failed` contradicts
the contract that record already has. `documents.py` defines its
`start_operation_id` as the act the record followed, and
`intake._failed_start_record` reads the row as this manager's account that a
runtime CAME FROM a failed start -- which is what authorizes destroying that
container. The preceding correction wrote the record with no such act, and its
own regression asserted the named start operation did not exist.

**Confirmed.** One durable row cannot carry both meanings, least of all when
one of them is a destruction authorization. Reusing the kind so the Job
projection would not have to distinguish the two outcomes is not provenance
for a durable act; the two facts differ in exactly what a later reader needs.

**Correction.** The Worker Manager gains a SECOND record.
`documents.runtime_preparation_failed` names the attempt, the fixed
assignment, the runtime and axis as they stood, and the typed refusal -- and
deliberately no `start_operation_id`, because there was no start act to name.
`attempts.refuse_runtime_preparation` writes it under an identity derived from
the attempt and its fixed assignment alone, and
`attempts.attempt_preparation_failure_of` reads it back under the same proof
discipline its sibling is held to. It journals no start operation, occupies no
lane, calls no adapter and reconciles nothing, and it authorizes nothing: the
only consumer is the projection that has to report the stage. The two
outcomes are unified in `job_manager/projection.py`, where unification is a
stage state rather than a durable act.

**Boundary, replacing the superseded one above.** The record is written from
BOTH axes a control plane still reads as `claimed`: `not-started`, and the
`start-requested` restart window in which a start was journalled and no
runtime was ever attached. Anything else already has an ending and is refused.
The earlier rule -- that a start already requested keeps its existing ending,
so the deployment re-raises there -- is superseded: review
`review-2026-09-03T18-16-57Z.md` [P1] showed it left a failed credential
recovery `claimed` and polled on every tick, and the account it claimed to
preserve was not in fact repeated, because the first recovery's bounded stop
and cleanup had already changed what the next one could find.

### 2026-09-03 decision: the launch delivery is adopted, never re-authored

**"Reaches no engine" is superseded 2026-09-03 by "an ending names what it
leaves behind" below.** Everything else in this section stands: no replacement
document is authored after a start, no bytes are repaired, and no replacement
runtime is started.

**Observed.** The same review [P1] found the composition materializing a
launch document whenever `launch.adopt` answered absence, including after the
start operation had committed, and calling credential recovery BEFORE that
adoption.

**Confirmed.** `launch.adopt`'s own contract says absence is ordinary only
until a caller knows a runtime started, and that caller must refuse; this
finding already required a complete delivery to be adopted and contradictory
or partial material to refuse rather than be repaired. Authoring a replacement
under a container that may already hold the mount converts lost durable
evidence into state that looks valid. Separately, credential recovery rereads
and REGISTERS bearer bytes, so a launch refusal after it left those
registrations live with nothing holding the delivery and the next tick
repeated them.

**Correction.** The launch delivery is adopted before any bearer is touched,
and a materialization is reachable only from `not-started`. Post-start absence
refuses closed, creating no bytes and reaching no engine.

### 2026-09-03 decision: a settled refusal keeps its durability and its bound

**Observed.** Review [P2]: the re-raised refusal omitted `durable`, so a
durable input became non-durable -- and the Job control plane branches on that
flag to tell a condition from an ending. It also appended settlement prose to
an already-valid message without reserving the closed `MESSAGE_LIMIT`, so a
maximum-width refusal became a raw `AssertionError` at the raising site.

**Correction.** Durability is carried through, and the message is composed
bounded. The manager's account of which record it wrote is what survives the
bound; the caller already holds the message it raised.


### 2026-09-03 supersession: an ending names what it leaves behind

**Observed.** Independent review `review-2026-09-03T18-49-20Z.md` [P1] drove
the post-start launch-absence case six ticks further than its regression did
and found the stage `exceptional`, the launch root absent -- and the container
the previous process created still running with the credential mount, named by
nothing in this manager's rows. An ending that leaves an unmanaged live worker
is not a bounded failure.

**Confirmed, including what cannot be done.** The reviewer asked for an
operation that proves and STOPS the exact runtime. There is none this
deployment may call. `authorize_failed_start_cleanup` refuses in terms while
the assignment is live -- "a failed start is fenced at the authority before
anything is destroyed, and this assignment is still authorized to execute" --
and `request_cancellation` fences that assignment itself, which is an act on
the Work this leaf is executing rather than on its runtime. This bootstrap
holds no authority to fence, so stopping here would be taking a decision the
cleanup contract reserves for a fenced assignment.

**Correction, and the supersession it forces.** The ending is recorded FIRST
and the runtime is then reconciled through `reconcile_runtime`, so the attempt
row carries the identity the ordinary destroy crossing needs. The order is not
cosmetic: a reconciliation that attaches moves the execution axis off
`start-requested`, which is one of the two axes a preparation record may be
written from. That means the engine IS reached on this path, which supersedes
the earlier "post-start absence refuses closed, creating no bytes and reaching
no engine". What survives unchanged is the substance: no replacement runtime,
no launch bytes, and no bearer reread -- the adapter carries the ORPHAN
teardown rather than a delivery, and the credential lifecycle record survives
because the container holding its mount does.

### 2026-09-03 decision: what this invocation authored, this invocation ends

**Observed.** The same review [P1] found the reordering had left the pre-start
unwind half-written: it tore down a credential delivery this call materialized
and never discarded the launch document this call had just authored, so a
stage that ends before its start leaves an attempt's `launch.json` with
nothing that would ever come back for it.

**Correction.** A launch delivery this invocation AUTHORED is discarded when a
later pre-start boundary refuses. One it ADOPTED is not: a live runtime may
hold it, and the launch owner's root is not this composition's to remove on a
delivery it did not make.

### 2026-09-03 decision: an unsayable account still ends the stage

**Observed.** The same review [P1]. `ContractRefusal` refuses to be
CONSTRUCTED around a live bearer, and `manager_signature` walks every durable
member again before a row is written. A credential source whose own diagnostic
quoted a registered value therefore raised `integrity/secret-leak` with no
record behind it. The secret never reached a durable surface and the accepted
exceptional, non-retried ending was lost; the provider was called again on
every tick.

**Correction.** §13 is enforced at both moments and neither may take the
ending with it. The deployment owns a foreign component's diagnostic through
`check_no_durable_secret` before quoting it; the manager sanitizes the typed
failure's message before signing, and contains a signing refusal rather than
raising out of a recorder that promises never to. The closed pair and the
failure kind survive in both cases, and what replaces an unsayable message
says why it was replaced.

### 2026-09-03 decision: a start that failed keeps its own account

**Observed.** The same review [P1]. `request_runtime_start` journals
`runtime.start-failed`, settles the axis and re-raises; the composition sent
that refusal on to the preparation writer, which refused `already-terminal`,
and the sweep report -- the only place the low-level account appears -- carried
this deployment's note about why it could not write a record instead of the
engine's reason for refusing.

**Correction.** The composition asks the owner whether an ending already
exists, and re-raises the original refusal when one does. A record is written
only for a boundary that has no owner ending of its own.


### 2026-09-03 supersession: one meaning for the preparation record

**Observed.** Independent review `review-2026-09-03T19-24-19Z.md` [P1] found
two live and contradictory statements about `runtime.preparation-failed`. The
schema comment, the reader's docstring and the dossier ruling above all said
it means no start act happened and none ever will; the continuation path added
in correction pass 4 deliberately writes it after a preceding process
performed a start act and left a running runtime.

**Confirmed and pinned, once.** The record is THE DEPLOYMENT'S ENDING: its
post-claim composition could not carry this attempt further. It is not an
account of whether a start act occurred, not an account of what exists on the
engine, and not cleanup authority. `runtime.start-failed` remains the only
account of a start act and the only record `intake` removes a container on.
The `execution_runtime` and `runtime_id` members say what the axes held when
the record was written — after any identification its writer performed — for
the same reason its sibling names them.

**Where this is written.** `documents.py`'s contract comment,
`attempts.refuse_runtime_preparation`, `attempts.attempt_preparation_failure_of`
and `DEPLOYMENT.md` now all say this and nothing else. The obsolete wording
above is marked superseded rather than rewritten.

### 2026-09-03 supersession: identification is level-triggered, not a step after

**Observed.** The same review [P1]. The preparation record makes the stage
`exceptional`, and the control plane calls this deployment only for `claimed`
stages — so a naming step that ran AFTER the record had no second chance. A
crash or an ordinary naming refusal in between orphaned the runtime
permanently, and only the branch where `launch.adopt` answered ABSENCE reached
the naming at all; a contradictory or partial delivery, which `adopt` refuses,
bypassed it.

**Correction, superseding "record the ending FIRST, then name".** The
identification rides the owner's own call, BEFORE the record:
`refuse_runtime_preparation` takes an optional adapter and reconciles through
`reconcile_runtime` first. That is the order `_settled_and_recorded` fixes for
the sibling record and for the same stated reason — the record names the
runtime the reconciliation attached, so recording first durably says `None`
about a runtime that exists. It also makes a crash in between leave the stage
CLAIMED, which the next tick drives through the same path again. The
reconciliation never raises out of the recorder: a refusal or fault from it
joins the account rather than taking the ending with it. The deployment passes
that adapter for every boundary that refuses after a start was requested, so
no branch is special.

**The residual window, named rather than left to be found.** A crash between
the reconciliation and the record leaves the stage `running` with the runtime
attached. That is the direction that loses least: the container is named and
observable, and the composition's own refusal is what is lost rather than the
runtime.

**This whole section's ordering rule is superseded 2026-09-03 by "the ending
and the naming are one act" below.** The residual window named above is not an
acceptable loss for this Work, and the reason the ordering was chosen — that a
crash leaves the stage `claimed` for the next tick — is only true of the
interval BEFORE the reconciliation commits. What survives is why the
identification must come first at all: the record names the runtime, so an
ending written without it durably says `None` about a runtime that exists.

### 2026-09-03 supersession: the ending and the naming are one act

**Observed.** Independent correction-pass review 2026-09-03T21:24:16Z [P1].
`reconcile_runtime` durably attaches the runtime, and an attached runtime
projects the stage `running`; `job_manager/manager.py` invokes the launch
capability for `claimed` stages alone. A process death between the
reconciliation and the preparation record therefore removed the very
level-triggered obligation the previous correction was written to preserve:
the next manager observed `running`, never re-entered the composition, and
never wrote the exceptional ending. A reviewer probe interrupted exactly there
and recorded `running` on both the crash and the later tick, `runtime-single-1`
attached, no preparation record, zero later launch or engine calls, one start.

**Confirmed: there is no third ordering.** Both orderings of two independent
durable acts lose this ending, and for one reason stated once:

- *Record then name* makes the stage `exceptional`, and the control plane
  stops asking — so the runtime is never named.
- *Name then record* makes the stage `running`, and the control plane stops
  asking — so the ending is never written, and a stage that failed is reported
  as an ordinary running success no launch will ever follow.

Whichever act goes first is the one that removes the obligation to finish, so
reordering the same two acts cannot close the interval. The review named the
two shapes that can: an atomic owner commit after external identification, or
an explicit durable pending obligation that stays level-triggered until both
facts are recorded.

**Correction, superseding "reconcile, then record".** The first shape. Asking
the engine and committing its answer are separated: `attempts._identify`
performs every adapter question and answers a plan with no durable effect, and
`_reconciled` owns what that plan means durably — so `reconcile_runtime` is
those two halves and nothing else changes for its own callers. The failed
preparation ending then applies the plan INSIDE the transaction that writes
`runtime.preparation-failed`, through `_attach`'s new `within` operand, which
performs the compare-and-swap and its observation on the owner's open
connection instead of opening a second transaction. A death anywhere in the
interval leaves neither fact and the stage still `claimed`, which is the
level-triggered state the next tick drives through the same path.

**No adapter call is made under the store's write lock.** The engine is a
remote process and an owner holds `BEGIN IMMEDIATE` for the whole of its act;
asking inside would hold every other writer out for as long as the engine
takes to answer. This is the reason the split is between asking and recording
rather than a merge of the two operations.

**The plan is an operand by identity, not by prose, and by DIGEST.** The
signature carries the attempt, its fixed assignment, the failure, and which
runtime the engine named — never the adapter's own account of why — so an
ending naming a different runtime still collides rather than replaying, and
the same ending described differently still replays. The engine's name for the
runtime is folded in as a digest rather than quoted, because `manager_signature`
is a §13 walk and an adapter-supplied value the secret registry holds live
would make the ending unsignable, which is the retry loop this record exists to
stop. The same rule holds the outward account: naming the runtime rather than
the decision word put an adapter-supplied value into a refusal message, and
`ContractRefusal` refuses to be constructed around a live one — so the account
is checked before it is raised and the name alone is dropped, with a
replacement that says why. The durable row is the store's own rule and needs
nothing from here: an attachment carrying such a value refuses, is contained,
and the ending is written over the axes that containment leaves standing.

**Within the ending, the attachment is not a separately journalled
operation.** It is one of the two facts the ending commits, and the outer
`runtime.preparation-failed` row is what a retry replays. The compare-and-swap
is idempotent, so an independent later `reconcile_runtime` still answers the
same attachment.

**The identification still never takes the ending with it.** Asking is
contained outside the act as before; applying is contained INSIDE it by its
own savepoint, so a refused attachment is rolled back alone and the record is
written over the axes that rollback leaves standing. A `BaseException` is not
contained: a process being torn down must not commit half of this act.

### 2026-09-03 supersession: the failed-start ending is one act too

**Observed.** Independent correction-pass review 2026-09-03T22:00:26Z [P1].
`_settled_and_recorded` was still `reconcile_runtime` followed by
`_record_start_failure`. The reconciliation attaches the runtime, an attached
runtime projects the Job stage `running`, and the launch capability is invoked
for `claimed` stages alone — so a death between the two acts made
`runtime.start-failed` permanently unreachable, which is the same defect and
the same reason as the preparation ending's. A reviewer probe interrupted the
record after a failed start had reconciled a created runtime and recorded
`execution_runtime: running`, `runtime_id: runtime-1`,
`start_failure_present: false`, `start_calls: 1`.

**Confirmed in scope.** The accepted correction requires a settled start
refusal to project `exceptional` after restart, and the existing failed-start
fixture proves the created-runtime shape is reachable. The pass-6 handoff
reported this as Open and outside the patch boundary; the review resolved it
the other way and that ruling stands.

**Correction, superseding "reconcile, then record — the order is the
content".** The order's stated reason survives — the record names the runtime
the reconciliation attached, so recording first would durably say `None` about
a runtime that exists — but the two acts are one transaction now, exactly as
`_record_preparation_failure` is. `_settled_and_recorded` asks through the
shared `_identification`, and `_record_and_raise_start_failure` applies the
plan inside the transaction that writes the row, through the shared
`_identified_within`. Nothing asks the engine under the write lock.

**The uncertain settlement rides the same act.** `_settle_unknown_start` was a
third separate write, and `uncertain` is a state the projection reads as
terminal — so leaving it durable without the record is the same lost ending one
step further out. It runs inside the transaction, contained by its own
savepoint, and its adapter operand is gone because it never used one.

**What this does NOT recover.** The engine's account of why the start failed
is not recoverable across a death in that interval: the only durable trace of
it would have been the record. A resumed manager re-derives from canonical
state and the engine, and if a container carrying the labels exists and
observes as running it reports `running` — the same conclusion it would reach
if the process had died one statement earlier. What atomicity delivers is that
the stage never rests in a state the control plane will not revisit, and that
no ending is written without its naming.

### 2026-09-03 decision: the sibling guard is asked again where there is no interval

**Observed.** The same review [P1]. `refuse_runtime_preparation` checks
`attempt_start_failure_of` at its door and then queries the engine before its
transaction opens. A start failure committed in that interval passed the stale
check, and a preparation record was then committed beside it — two accounts of
one attempt, which is what the guard exists to prevent. A reviewer probe
committed the start ending from the identification interval and observed
`start_failure_present: true`, `preparation_failure_present: true`.

**Correction.** The sibling is asked again INSIDE the ending's transaction,
where there is no interval. If the start act's own record won the race it is
the sole ending and the sole cleanup authority, so neither the preparation row
nor the attachment it would commit may land — and refusing there unwinds both,
because they are one act. The door check stays: it is what refuses the ordinary
case early, with the closed pair callers already read, before anything is asked
of the engine. This is the two-moment shape `request_runtime_start` uses for
the lane, and it is stated in both places that the first read is not the
decision.

**The caller still reads its own refusal.** A lost race is CONTAINED and
accounted for rather than raised as `already-terminal`: the deployment is
entitled to the refusal it actually raised, and the control plane reads the
start act's record and reports that stage exceptional through it. Replacing
the engine's reason with this manager's note about a race is the account swap
review 2026-09-03T18:49:20Z already found on the sequential path.

### 2026-09-03 decision: the unwind defers to the owner that already decided

**Resolved 2026-09-03 by independent review 2026-09-03T22:20:58Z [P1], which
confirmed the OPEN entry below and ruled it in scope.** The reviewer's own
mount probe recorded `launch_root_exists: false`,
`credential_root_exists: false` and `credential_registered: false` beside a
live `runtime-single-1` whose recorded mount vector still names both deleted
paths.

**Correction.** `OciAdapter._undelivered` keeps its answer on the adapter as
`settlement` — the same structured `{"credentials": ..., "launch": ...}` value
it already returned — rather than only inside the refusal prose its caller
composes. `single_worker._unwound` reads it: an adapter carrying a settlement
has decided both mounts on its own engine evidence and there is nothing left
for the deployment to end. `None` means no owner reached that boundary, and
there `fresh` remains the whole rule, so a refusal raised before the adapter
existed or before `start` reached its settlement still ends both local
deliveries. Prose is not an API, and neither is a re-derivation: the two
narrower conditions tried in pass 7 each broke a rule pinned above, and the
reason both failed is that neither is a fact about WHO decided.

**Three sides, proved together.** A created-then-denied runtime keeps both
`unresolved` mount roots and its registered bearer; a refusal before the
adapter/start boundary ends both local deliveries and releases the bearer; and
the colliding-bearer path still releases its delivery before durable state is
reread and stays exceptional and non-retried. The first fails against the
pass-7 unwind and the other two pass under both, which is the discrimination
that says the change is exactly the defect and nothing else.

### 2026-09-03 OPEN — resolved above: the pre-start unwind could remove a live container's mounts

**Superseded 2026-09-03 by "the unwind defers to the owner that already
decided". The observation stands as recorded; only its OPEN status is
resolved.**

**Observed, not corrected at the time.** Found while building the failed-start
regression.
`single_worker._unwound` decides from `fresh` — the execution axis as it stood
BEFORE the start was requested — so a start that reached the engine, created a
container and then reported failure arrives there still called fresh, and the
credential root and launch document are removed although a container may hold
both mounts. `OciAdapter._undelivered` owns exactly this question, asks the
engine which runtimes carry the labels, answers `unresolved` and removes
nothing; the deployment then removes it anyway. Measured directly: with the
unwind unchanged the launch root is absent after a denied start that created a
container, and with it skipped the root survives.

**Why it is not corrected in this pass.** Two narrower conditions were tried
and each broke a rule already pinned in this record. Deciding from the
execution axis skips the settled-`uncertain` path, where a colliding bearer
must still be released — the untrusted-bearer P1 of 2026-09-03T19:24:19Z, whose
whole regression fails. Deciding from the attached runtime identity cannot be
read at all on that same path, because the attempt row carries the very value
§13 is refusing over, so the read that would decide is blocked by the condition
the teardown exists to clear.

**Proposed direction.** The deployment should defer to the owner that already
computed the answer rather than re-deriving it: `_undelivered` distinguishes
`torn-down` from `unresolved`, and only the paths where no owner has decided —
a refusal raised before the adapter's `start` was reached — are the
deployment's to end. That needs the adapter's answer to reach the deployment
as a value rather than as refusal prose, which is a change to a boundary this
Work did not open.

### 2026-09-03 decision: before a start, both deliveries are this leaf's to end

**Observed.** The same review [P1]. Ownership was read as "did this invocation
author it", which left a launch document published by a process that crashed
before its credential, adopted by the next one, and stranded forever by an
ordinary provider refusal — with no runtime that could ever have mounted it.

**Correction.** The state the manager already proved is what decides.
`not-started` says no runtime received either delivery, so the credential
delivery is torn down and the launch delivery discarded whether this
invocation authored or adopted it. After a start was requested neither is
removed: a container may hold the mount.

### 2026-09-03 decision: an untrusted bearer may not wedge the manager

**Observed.** The same review [P1], and it is the adversarial equality the
existing §13 suite already treats as valid. The credential provider's answer
is untrusted; one equal to this attempt's own durable identity is registered
live by `materialize`, and every later §13 walk over a row carrying that
identity then refuses. The manager could not read its own attempt, so nothing
could be settled, recorded or reported, and both roots stayed on the host.

**Correction.** The delivery's cleanup owner stays live across every pre-start
manager boundary that follows materialization — the start request included —
so the colliding value is released, after its bytes are proved gone, before
durable state is read again or an ending is recorded.

### 2026-09-03 review confirmation: both owner endings must be atomic and exclusive

**Observed.** Independent correction-pass review
`review-2026-09-03T22-00-26Z.md` found that the preparation correction closes
its reported attach/record interval, but leaves two adjacent owner races.
First, `_settled_and_recorded` still attaches a runtime and writes
`runtime.start-failed` as two durable acts; a process death between them leaves
the stage `running`, with no start-failure row and no later launch call.
Second, `refuse_runtime_preparation` checks for the sibling start-failure row
before its external identification query and does not revalidate inside the
ending transaction; a start failure committed during that query is therefore
followed by a preparation-failure row, leaving two accounts for one attempt.

**Confirmed.** Both are inside W76207's acceptance. A settled start refusal
must remain `exceptional` across restart, and the dedicated preparation record
must defer to `runtime.start-failed`, the sole account and cleanup authority for
a failed start act. The production composition cannot honestly ship while a
process death turns that failure into `running` or a race commits both endings.

**Required correction.** Apply an identified start result and its
`runtime.start-failed` row in one owner transaction, using the same no engine
call under lock boundary as the preparation ending. Within the preparation
ending's transaction, revalidate that no sibling start-failure row committed;
if one did, roll back the preparation attachment and row and preserve the start
act's account alone. Add exact crash and interleaving regressions.

### 2026-09-03 review confirmation: owner settlement gates deployment unwind

**Observed.** Independent correction-pass review
`review-2026-09-03T22-20-58Z.md` confirmed the OPEN recorded above. The
production created-then-denied fixture leaves `runtime-single-1` live with
credential and launch paths in its mount vector, while `_unwound` removes both
roots and releases the credential registration. The stage is exceptional and
the start-failure row names the runtime, but the live container's mounted
sources no longer exist.

**Confirmed.** This is inside W76207 and blocks its acceptance. It contradicts
the already-pinned rule that, after a start was requested, neither delivery is
removed because a container may hold the mount. The fact that
`OciAdapter._undelivered` already proved the deliveries `unresolved` makes the
deployment's second, stale decision less authoritative, not more.

**Required correction.** Carry the adapter owner's structured delivery
settlement across the start boundary, or provide an equivalent exact owner
capability; never parse refusal prose. The deployment may unwind locally only
when no runtime owner reached or decided that boundary. Preserve both mount
roots when a created runtime made the owner's result `unresolved`, while still
proving cleanup for pre-adapter failures and for the colliding-bearer path that
cannot read durable state until its local delivery is released.

### 2026-09-03 review confirmation: structured owner settlement closes the unwind defect

**Confirmed.** Independent correction-pass review
`review-2026-09-03T22-32-34Z.md` verified that the OCI adapter's structured
settlement is populated only after its engine-backed delivery disposition and
that the deployment consults it before the stale pre-start axis. The preserved
mount probe now leaves both sources and the bearer registration in place for
the live created runtime, while the production fixture still proves local
cleanup before that boundary and the colliding-bearer case still releases its
delivery before rereading durable state. The four preserved crash/race probes,
49 production-composition tests, and 536 combined OCI/attempt tests pass. No
further correction finding was identified; W76207 is signed off for its next
handoff, but no immutable proposal or candidate digest was reviewed here.
