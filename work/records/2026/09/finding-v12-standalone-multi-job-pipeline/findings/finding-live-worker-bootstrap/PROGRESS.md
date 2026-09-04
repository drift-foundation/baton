# Progress

## 2026-09-03 - `baton.claude` (`impl`), W76207 first slice: the launch seam

Claimed at baseline `4641ce0`. The level-triggered post-claim launch seam and
the start-failure observation are complete and verified. The production
composition module is NOT, and is described honestly below rather than
half-written into the tree.

### Revalidation before editing

Every pinned fact in the reviewer revalidation reproduced against the tree:
188 focused Job-manager tests pass with `PYTHONPATH=src`; `projection._owed`
stops at `claim`, so there was no post-claim seam; `tools/job_manager.py`
takes the factory as an exact `module:attribute` and repository search finds
no production factory; and `runtime.start-failed` is journalled by
`attempts._record_and_raise_start_failure` under a derived identity with no
public read.

### The blocker that was cleared, and one that is not

Three accepted patch targets -- `attempts.py`, `worker_manager/__init__.py`
and `documents.py` -- were mode `0444`. Reported as an operational finding
rather than worked around; the operator chose option 1 and repaired the modes
with the bytes unchanged, which I verified before resuming.

**One remains.** The accepted boundary says to add the package export, and a
public export mechanically requires one additive line in the exhaustive table
in `tests/manager/test_text_sweep.py` -- which is still frozen at `0444`. The
needed entry is one line in the shape its two siblings already use:

    "attempt_start_failure_of": ((store, "attempt-1"), {}, [1]),

I did not change that file's mode. Hiding the function from the package
surface to dodge the gate would be worse than the gate.

### What is complete

- **`worker_manager/attempts.py`: `attempt_start_failure_of`.** A read of the
  owner's own committed record, under the identity
  `start_failure_operation_id` derives from the attempt row. Absence for an
  unknown attempt and for one whose start never failed; a REFUSED row under
  that identity is a collision rather than evidence and answers absence too.
  Exported from the package and classified in the section-13 accounting table.
- **The observation gained `start_failure`.** A fifth member rather than
  something derived from `runtime`, because it cannot be: the manager
  journals the failure as its own act and reconciliation may ATTACH a runtime
  id afterwards. `projection._observed_state` reads it BEFORE the runtime, so
  the attached identity never answers first -- which is exactly how a stage
  whose start had failed used to project `running`.
- **The level-triggered launch seam.** `OPERATIONS` gains `launch`;
  `ManagerOperations` takes an optional injected `start_runtime` and refuses
  honestly when a deployment supplied none; `manager._launch` asks for every
  stage whose canonical state is `claimed`, on every tick including the first
  after a restart. It writes no Job-store receipt: `admit` and `claim` remain
  the only acts this leaf journals, and replay is the Worker Manager's own.
- **Failures are contained per stage.** A durable refusal reports `refused`
  and an ordinary one `deferred`; neither aborts the sweep, so an unrelated
  stage is still launched and still observable.
- **`tools/job_manager.py serve` releases factory-owned handles** on normal
  stop AND on construction failure, reporting a release fault instead of
  letting it replace the outcome the run reached.

### Why the launch is not inside `claim()`

Driven end to end rather than argued: a crash after the Authority commits the
claim makes the next incarnation ADOPT the canonical settlement without
calling `claim` again, so a launch folded into that call is skipped once,
permanently, on the path nobody watches.
`TheLaunchSurvivesTheClaimCrashWindow` reproduces that restart against the
real operations and proves the launch still happens.

### What remains

PLAN items 3, 5 and the real-worker half of 7: the trusted production
composition module and its closed deployment configuration, the restart
adoption at each partial boundary, and the tiny live fixture. The composition
ORDER is known and recorded (the dogfood command's public-operation sequence),
and the APIs it needs -- `assignment_workspace`, `compose_input_root`,
`retain_manifest`, `CredentialHome.materialize`/`adopt`/`discard_orphan`,
`launch.materialize`/`adopt`/`discard`, `OciAdapter`, `request_runtime_start`,
`reconcile_runtime` -- are surveyed and tractable.

I stopped rather than rushing it. That module is the capability-confinement
boundary of this leaf: it opens the Authority, resolves the principal through
the bootstrap face, mints one restricted session, and holds the bearer for a
single immediate acceptance. A half-written version of that sitting in the
tree is worse than none, and its restart adoption at eight crash points is not
something to sketch.

### Verification

Focused: 200 tests, exit 0 (188 inherited plus 12 new, including the new
`tests/job_manager/test_launch.py` registered in `parallel_test.py`).
`tests.manager.test_attempts` passes at 314 tests with the new read.

Broad sweep: 3362 tests. Its failing identities are the 8 pre-existing ones
recorded for W73629 plus `test_the_table_names_every_exported_callable`, which
is the frozen-file blocker above and nothing else. No other identity moved in
either direction.

### State

Passing back for independent review of this slice, with the frozen-file
blocker and the remaining production composition reported explicitly.

## 2026-09-03 - `baton.claude` (`impl`), W76207 correction pass 1

`review-2026-09-03T10-33-37Z.md` requested changes and directed that this
continue as ONE Work rather than splitting the composition from its
acceptance. All four P1s were real and all four are corrected. The operator
repaired `tests/manager/test_text_sweep.py` to `0644`, so the export's
registry row is in.

### P1 - a real adapter fault aborted the whole sweep

`request_runtime_start` journals the failed start and then RE-RAISES the
adapter's typed fault, so a real engine error is not a `ContractRefusal` at
all. It escaped the handler, skipped every stage sorted after it, and ended
`serve`.

`_launch` now catches the fault path too, and contains ONLY a fault the Worker
Manager can be proved to have recorded: `_recorded_failure` re-observes
through the same bound observation and asks whether the canonical failed-start
record exists. Without one the fault is re-raised, because a programming error
is not a stage outcome and burying it as a transient condition is worse than
the abort. The regression sorts the failing stage FIRST so that a stage which
only runs after it is the evidence.

### P1 - a durable pre-start refusal was reported and then retried forever

Mapping any durable refusal to a `refused` report left the stage `claimed`
with no canonical ending, so the next tick asked again, and the one after
that. There is now ONE rule for every durable launch ending, and it is
canonical rather than a Job-store shadow: if the Worker Manager holds a
failed-start record the stage is contained and the next projection reads it as
`exceptional`; if it does not, the sweep REFUSES and names the deployment's
omission. A composition that refuses durably and journals nothing has left
this control plane no fact to project and no reason to stop, and saying so is
the only answer that is not a silent loop. The regression proves contained,
exceptional AND not-retried, while an unrelated stage is still launched in the
same sweep.

### P1 - the journal projection did not prove what it had read

`attempt_start_failure_of` trusted any committed row under the derived id. It
now follows the discipline `intake` already applies to the same record: the
kind must be `runtime.start-failed`, the answer is decoded through the
journal's own `replay`, and the record's `attempt_id`, `expect` and
`start_operation_id` -- exactly the three facts the identity is derived from --
must be this attempt's own. `runtime_id` and `execution_runtime` are
deliberately NOT compared, and this reader has a sharper reason than intake's:
reconciliation may attach a runtime after the failure settled, which is the
exact case the projection exists to report.

Regressions in `tests/manager/test_attempts.py` drive a real failed start and
its positive replay, both recorded failure shapes, a row committed as another
kind, a record describing another act, and a refused row under that identity.

### P1 - factory construction sat outside the release boundary

It did, and the comment beside it claimed otherwise -- so the code and the
record both asserted cleanup that did not exist. Construction is now inside
the `try`, and the limit is stated rather than promised: an object the factory
RETURNS is always released; handles a factory took and then abandoned by
raising are its own to clean up, because nothing here ever saw them. Three
cases measure that boundary, including one that deliberately leaks and proves
the original failure still reaches the operator unchanged.

### Verification

Focused: 206 tests, exit 0, under both `discover -s tests/job_manager` and the
package path. `tests.manager.test_attempts`: 356 tests, exit 0.
`tests.manager.test_text_sweep`: 3 tests, exit 0 with the export row.

Broad sweep: 3410 tests. `comm -3` against the recorded baseline is EMPTY in
both directions -- the export row cleared the one identity this slice had
added, and the four corrections added none.

### Still outstanding

Unchanged from the first slice and now explicitly directed to finish here:
the trusted production composition module and its closed deployment
configuration, partial-boundary recovery, the real worker fixture, the
documented production command, and the immutable proposal.

### State

Claim held; continuing with the production composition under this same Work.

## 2026-09-03 — baton.tuner — production composition and blocking discovery

Claimed W76207 after the implementation handoff and added the production
deployment half at `v12/python/tools/single_worker.py`. The closed
configuration fixes the Authority/store identity, participant/principal,
profile/policy/adapter/image, engine/network, workspace/launch/credential
homes, credential slot mapping, bootstrap source and input manifest, and
launch contract/role. It validates those facts and the source tree before
opening Authority; opens Authority against the expected UUID; resolves the
configured principal; wraps exactly that participant's Session in the seven
member `AuthorityPort` surface; keeps Authority/bootstrap/provider-registry
paths out of the runtime composer; and releases the Authority through the
operations object's `close`.

The deployment instruments admission so an exact implementation
Work/profile/input/policy binding is proved before `issue_offer` can mint a
bearer. Bearer delivery compares the issued Work, participant, offer and
attempt to that in-memory admission, accepts immediately, and retains neither
bearer nor verifier. The claimed launch path orders the public attempt,
activation, workspace/input composition, manifest retention, lazy credential,
launch and OCI start/reconciliation operations. Preparation refusals after
activation are fed through `request_runtime_start` so the Worker Manager owns
the durable failure rather than a Job receipt shadowing it.

Added `tests.tools.test_single_worker` and registered it in the parallel test
inventory. Four independent boundary cases pass: closed configuration,
source-content identity before Authority access, mismatched profile refused
before offer/engine action, and confinement of Authority bootstrap material.
The positive real-store pipeline fixture reaches issued/accepted offer and
committed claim, then repeatedly reports this public refusal before any engine
act:

    integrity/path: the manager's assignment home could not be created at
    .../storage/attempt:job-a/implementation: FileNotFoundError

The canonical Job Manager attempt id contains `/`; `assignment_workspace`
joins it below storage but creates only the final component. The finding and
PLAN now record why neither changing the pinned episode identity nor privately
mapping/mkdiring it in the deployment is acceptable. This is an application
owner correction, so tuner stopped before changing `worker_manager/workspaces.py`
and is returning the held Work to `baton.impl`. The positive restart/runtime
case remains deliberately red until that owner boundary is fixed; documentation,
the crash-point matrix, uncertainty projection and immutable proposal remain
pending behind it.

## 2026-09-03 — `baton.tuner` — production composition completed

Slawomir reassigned W76207 to tuner after the deeper owner-boundary diagnosis
superseded the preceding workspace conclusion. The Job Manager, not the
workspace owner, minted `offer:job-a/implementation` and
`attempt:job-a/implementation`; both names violate the frozen worker
`opaqueId` grammar before a worker can consume them. New episode identities
are now canonical digests of stage plus episode with bounded `offer-` and
`attempt-` prefixes. Episode rows remain the source of truth, so schema-1 and
already-recorded schema-2 identities are preserved and never recomputed.

The production `tools.single_worker:factory` is complete. Its closed document
binds the input manifest to the Authority UUID, assignment contract, profile,
policy and image, and fixes one implementation participant/principal, Work,
adapter, OCI posture and set of durable homes. It opens Authority against the
expected UUID, resolves participant/principal through Authority, constructs
only that participant's restricted port, and keeps Authority bootstrap paths,
principal lookup, credential registry and bearer out of the runtime composer.
The public factory requires a private credential-source registry; only the
direct construction seam used by tests or another trusted embedding accepts
an injected provider.

Admission proves the exact implementation Work, profile, input and policy
before offer issue. Bearer delivery is compared to the in-memory offer intent,
accepted immediately and not retained. After claim, the launch capability
replays public attempt and activation operations; allocates/adopts the exact
workspace; composes and retains the frozen input; lazily materializes or
adopts credentials and launch delivery; and starts or reconciles the OCI
adapter. Adapter construction and credential/launch preparation refusals are
settled through the Worker Manager's durable start-failure operation. An
uncertain runtime and every recorded start failure project `exceptional`, and
neither is an implicit retry.

The production-seam fixture uses real Authority, Job and control stores plus
the real workspace/input/credential/launch composition, replacing only the
OCI process boundary with a recording engine. It proves issued offer through
live observable runtime, restart adoption, no duplicate OCI start, immediate
pre-admission profile refusal, static Authority/participant/principal and
contract/role refusals, capability confinement, public factory loading,
secret absence from status/engine vectors, and a credential-source refusal
that is durably exceptional and never retried. Crash recovery is exercised
after accepted offer, committed claim, attempt, activation, workspace, input,
manifest, credential, launch and runtime boundaries. A separate process-death
case interrupts after the durable start request and after the engine creates
the runtime but before the runtime identity or credential lifecycle record is
published; restart carries the public credential-orphan capability into OCI
reconciliation, adopts the live runtime and does not call the engine twice.

Verification at the completed candidate:

- `tests.tools.test_single_worker`: 21 tests, all passing.
- `tests/job_manager` discovery: 208 tests, all passing.
- `tests.manager.test_attempts`, `test_secrets`, and `test_text_sweep`: 450
  tests, all passing.
- `py_compile` for the changed production composition, regressions and Job
  identity/projection modules: passing.
- `git diff --check`: passing.

The parallel-registry test remains blocked by the unrelated, concurrently
present `tests.tools.test_quiescent_assignment_finalization` module not being
registered in `tools/parallel_test.py`; W76207's own
`tests.tools.test_single_worker` entry is registered. No file in that other
Work was changed here.

State: implementation complete and ready for independent review. PLAN item 10
remains the post-review/integration handoff rather than an action for this
tuner claim.

## 2026-09-03 — `baton.claude` (`impl`), W76207 correction pass 2

`review-2026-09-03T17-23-00Z.md` requested changes. All three P1s are
corrected. Claimed at the same baseline `4641ce0`; the reviewer's pinned facts
all reproduced against the tree before anything was edited.

### P1 — the preparation boundaries had no ending they could reach

The review was right that workspace adoption, input composition and manifest
retention sat outside the settlement, and the sharp part of it is the
parenthetical: an ending "without requiring an input-root authorization that
cannot yet succeed". Widening the existing settlement is not possible.
`request_runtime_start` was the ONLY public path to the durable
`runtime.start-failed` record and it reaches that record THROUGH the adapter,
so it first calls `authorize_input_root`, which reads the two protocol
documents back off disk. Every one of these boundaries fails before that root
exists, and an attempt recorded against an input manifest cannot pass
`inputs=None` either. The authorization the ending would have to satisfy is
exactly the act that could not be performed.

So the owner surface gained the one operation it was missing:
`attempts.refuse_runtime_start`, exported beside the start it stands in for.
It writes THE SAME `documents.runtime_start_failed` record under the same
derived identity — `attempt_start_failure_of` reads a refused preparation and
a refused start without being told which happened, so no second vocabulary
enters the projection. It journals no start operation, occupies no lane and
calls no adapter, because none of that happened; and it reconciles nothing,
which is made honest by refusing any attempt whose execution axis has left
`not-started`. The refusal is raised back with its closed pair unchanged and
only its message grown, exactly as a refused start's is.

`_PreparationFailure` is gone with it. Feeding a fake adapter through
`request_runtime_start` journalled a start request for a start that never
reached an engine, which was a fiction this leaf no longer needs.

**What the composition does NOT do**, and it is deliberate: a start that was
already requested keeps its existing ending. Asking for a settlement that
would refuse there would replace the refusal an operator has to act on — the
credential recovery's own account, for instance — with this deployment's note
about why it could not write a record down. The refusal travels as itself and
the next tick asks the level-triggered question again.

Regressions drive a structurally foreign workspace (`inputs` present and not
this attempt's own directory) and a partial input root (material copied, no
protocol pair), each proving `exceptional`, the owner's recorded failure, no
retry, no engine traffic, and a second stage still reached and reported in a
later tick. The failing stage sorts first, and the case asserts that.

### P1 — credential restart adopted a record compared with itself

Also right, and worse than it looked: `adopt` was called with the runtime id
taken out of the very record being adopted, so the one comparison made was the
record against itself, and bearer bytes were re-registered before anything
proved the live container was the one the record names.

The attached-delivery path now composes `OciAdapter.recover_credentials`
through an adapter carrying no delivery — the delivery is what it answers —
and carries the proved delivery into the adapter used for reconciliation. The
assignment it is asked with is the one activation FIXED, taken from the same
atomic `attempt_runtime_of` read the branch turns on, rather than the claim
row: the labels the recovery selects on are composed from the fixed
assignment, and the claim row is where the attempt came from rather than what
its runtime was labelled with.

Three cases drive it, and finding the window they need was the substance: the
lifecycle record is written the moment the engine names a runtime and
reconciliation attaches that identity afterwards, so the branch is reachable
only from a process that died between those two acts. The fixture stops at
exactly that point. They prove the exact recovery (the engine is asked —
`ps` and `inspect` — before any bearer is reread, and no second runtime is
started), a record naming another runtime (refused, nothing exactly
identified so nothing stopped, no runtime attached), and a matching runtime
whose credential mount disagrees (refused, the one candidate the ruling
permits stopping is stopped and the stop reached the engine, no replacement
started). In all three the sweep is still serving the other stage.

### P1 — the partial-input branch raised a pair §9 does not carry

`refused/path` is not a closed pair, so the one branch that finds incomplete
material rejected its own raising site with an `AssertionError`. It raises
`integrity/path`, which is the pair it is, and the regression reaches the
branch through `_input` rather than the private helper, so what is proved is
the branch rather than the spelling of one call.

### Verification

- `tests.tools.test_single_worker`: 27 tests, exit 0 (21 inherited plus 6
  new), also clean under `-W error::ResourceWarning`.
- `tests/job_manager` discovery: 208 tests, exit 0.
- `tests.manager.test_attempts`: 399 tests, exit 0, including six new cases
  driving `refuse_runtime_start` directly -- the recorded refusal and its
  closed pair, no journalled start operation and no occupied lane, the exact
  replay a restart makes, the not-activated and already-requested guards, and
  an operand that is not this manager's own refusal.
- `tests.manager.test_secrets`, `test_text_sweep`, `test_credentials`,
  `test_lifecycle_composition`, `test_input_delivery`: exit 0 with the new
  export's rows in the two exhaustive registries.
- `tests.manager.test_boundary_inventory`: the five pre-existing failures are
  byte-identical to the pre-change run with the new probe registered; the new
  export adds no entry to any of their lists. Measured rather than assumed:
  the same module was run with the new operation removed and the two outputs
  compared.
- Broad sweep: 3482 tests, up from 3410 by this pass's own cases and by the
  inherited ones the new `test_attempts` subclass brings with it. The failing identities are the eight already on
  record -- five in `test_boundary_inventory`, `test_credentials_engine`,
  `tests.authority.test_catalog`, and the parallel registry, which still
  refuses over the unrelated, concurrently present
  `tests.tools.test_quiescent_assignment_finalization`. This Work's own
  `tests.tools.test_single_worker` is registered. No identity moved in either
  direction.
- Whitespace check and `py_compile` over every changed module: passing.

### State

Passing back for independent review of this correction pass. PLAN item 10 —
integration and submitting W71917 through this seam — remains the post-review
handoff rather than an action for this claim. No version-control state was
mutated. The parent/sibling dossier edits and the other `v12/python` working
tree changes present at claim time are not mine.


## 2026-09-03 — `baton.claude` (`impl`), W76207 correction pass 3

`review-2026-09-03T18-16-57Z.md` requested changes. Four P1s and one P2, all
corrected. The deepest of them says my last correction was wrong in a way I
should have caught myself, so that is where this starts.

### P1 — the preparation record contradicted the contract it borrowed

I filed a post-claim preparation failure under `runtime.start-failed` and said
in the docstring that reusing the kind was the point, so the projection would
not have to distinguish the two. It is `intake._failed_start_record`'s
authority to remove a container that came from a failed start, and
`documents.py` defines its `start_operation_id` as the act the record
followed. My own regression asserted that act did not exist. One durable row
with two meanings, one of them a destruction authorization — the reviewer's
sentence for it is exact: reusing the old kind so the projection need not
distinguish them is not sufficient provenance for a durable act.

There is a second record now. `runtime.preparation-failed` names the attempt,
the fixed assignment, the runtime and axis as they stood, and the typed
refusal — and no `start_operation_id`, because there was no start act to name.
`refuse_runtime_preparation` writes it under an identity derived from the
attempt and its fixed assignment alone; `attempt_preparation_failure_of` reads
it under the same proof discipline its sibling is held to. It authorizes
nothing, and a case proves that directly: after a preparation is recorded,
`attempt_start_failure_of` still answers absence and
`authorize_failed_start_cleanup` still refuses for want of a committed
failed-start record. The two outcomes are unified in the Job projection, where
unification is a stage state rather than a durable act.

### P1 — a refused credential recovery was claimed and polled forever

The last pass re-raised from `start-requested` and I explicitly asked for that
judgement to be reviewed. It was wrong on the half I did not check: the
account I said travelled unchanged was not in fact repeated, because the first
recovery's bounded stop and cleanup had already changed what the next one could
find. An ordinary refusal polled on every tick is neither an ending nor a safe
wait state.

`refuse_runtime_preparation` records from both axes a control plane still reads
as `claimed` — `not-started` and the `start-requested` restart window — and
refuses anything else, which already has an ending. The recovery cases now
assert the state six ticks later rather than the first sweep report, that the
recorded failure carries the recovery's own account, and that nothing asked
again.

### P1 — a missing launch delivery was silently re-authored after the start

Correct, and the launch owner says so in terms: absence is ordinary only until
a caller knows a runtime started, and that caller must refuse. Materialization
is now reachable only from `not-started`; post-start absence refuses closed.

### P1 — the bearer was reread before the launch was proved

The same ordering. Credential recovery rereads and REGISTERS bearer bytes, and
a launch refusal afterwards left those registrations live with nothing holding
the delivery. The launch delivery is adopted first, so the only thing a launch
refusal can unwind is a launch — and the regression proves it by asserting the
engine is asked NOTHING on that path, which is the direct evidence that the
recovery never ran.

### P2 — durability and the message bound

Both real. `durable` is carried through; the message is composed within
`MESSAGE_LIMIT`, and the manager's account of which record it wrote is what
survives the bound, because the caller already holds the message it raised.
Focused durable and maximum-width cases pin both.

### Verification

- `tests.tools.test_single_worker`: 32 tests, exit 0, also under
  `-W error::ResourceWarning`.
- `tests/job_manager` discovery: 210 tests, exit 0.
- `tests.manager.test_attempts`: 406 tests, exit 0.
- `tests.manager.test_secrets`, `test_text_sweep`, `test_credentials`,
  `test_lifecycle_composition`, `test_input_delivery`, `test_intake`: 374
  tests, exit 0.
- Broad sweep: 3496 tests. The failing identities are the same eight already
  on record; none is new.
- `tests.manager.test_boundary_inventory`, MEASURED AND REPORTED RATHER THAN
  WAVED AT, because two of its already-failing lists grew. "Owned, never
  probed" is unchanged at 49; "attributed to no entry" went 35 -> 36 and
  "receiving entries with no owner" 132 -> 134. The added rows are exactly
  this pass's new surface -- `attempt_preparation_failure_of`'s attempt id and
  its committed-record document, `refuse_runtime_preparation`'s refusal, and
  `documents.runtime_preparation_failed`'s members -- and EVERY ONE of them has
  a sibling already sitting in the same list: `attempt_runtime_of`,
  `attempt_activity_of`, `attempt_start_failure_of`, `label_context` and
  `documents.runtime_start_failed` are all unowned there today. So this
  introduces no new KIND of gap; it is the same stale inventory universe the
  module's five recorded failures are, and repairing 132 entries belongs to
  whoever owns that failure rather than to this leaf. Naming it here so the
  next reader does not have to rediscover which rows moved.

### State

Passing back for independent review. PLAN item 10 — integration and submitting
W71917 through this seam — remains the post-review handoff. No version-control
state was mutated.


## 2026-09-03 — `baton.claude` (`impl`), W76207 correction pass 4

`review-2026-09-03T18-49-20Z.md` requested changes. Five P1s, all corrected,
and two of them are interactions my own last pass introduced.

### P1 — the post-start ending left a live worker with no name

Driving my regression six ticks further than I did shows it: stage
`exceptional`, launch root absent, and the container the previous process
created still running with the credential mount, named by nothing in this
manager's rows. The reviewer asked for an operation that proves and STOPS it,
and there is none this deployment may call — `authorize_failed_start_cleanup`
refuses in terms while the assignment is live, and `request_cancellation`
fences that assignment, which is an act on the Work rather than on its
runtime. This bootstrap holds no authority to fence.

What it can honestly do is NAME it. The ending is recorded first and the
runtime is then reconciled, so the attempt row carries the identity the
ordinary destroy crossing needs — the difference W6636 draws between a leaked
container and one an operator can end. The order is forced and it is the right
way round anyway: a reconciliation that attaches moves the execution axis off
`start-requested`, which is one of the two axes the preparation record may be
written from, so naming first left the owner refusing `already-terminal` and
the stage with no ending at all.

That means the engine IS reached, which contradicts the "reaches no engine"
line the last pass pinned. The FINDING marks that half superseded explicitly
rather than leaving two live rules. What survives unchanged is the substance,
and the case asserts each of it: no replacement runtime, no launch bytes, no
bearer reread — the adapter carries the ORPHAN teardown rather than a
delivery, and the credential lifecycle record survives because the container
holding its mount does.

### P1 — the reordering left the pre-start unwind half-written

Mine, from last pass. Putting the launch delivery first and tearing down only
the credential meant a stage ending before its start left an attempt's
`launch.json` with nothing that would ever come back for it. A delivery this
invocation AUTHORED is discarded now; one it ADOPTED is not, because a live
runtime may hold it. The existing credential-source case gained the positive
assertion — my previous claim that resource disposal was reverified was not
supported by anything, which is fair.

### P1 — a §13 refusal took the ending with it

`ContractRefusal` refuses to be CONSTRUCTED around a live bearer, and
`manager_signature` walks every durable member again before writing. A
credential source whose own diagnostic quoted a registered value therefore
raised `integrity/secret-leak` with no record behind it: the secret stayed off
every durable surface and the accepted ending was lost, so the provider was
called again on every tick. Both moments are guarded now — the deployment owns
a foreign diagnostic through `check_no_durable_secret` before quoting it, and
the manager sanitizes the typed failure before signing and contains a signing
refusal rather than raising out of a recorder that promises never to. The
closed pair and the failure kind survive; what replaces an unsayable message
says why.

### P1 — the catcher overwrote a real start refusal's account

Also mine. `request_runtime_start` journals its failure, settles the axis and
re-raises; sending that on to the preparation writer got `already-terminal`
back, and since status reports only the exceptional state, the sweep report —
the one place the low-level account appears — carried my note about why I
could not write a record instead of the engine's reason. The composition asks
the owner whether an ending already exists and re-raises the original when one
does.

### P1 — the inventory delta

Bounded to this pass's surface, and measured rather than argued. The
constructor left `documents.__all__` (the member set stays, the composer is
this package's own act). The reader's attempt id is delegated to the shared
`_attempt_row` owner. The refusal operand is a stated owner with a witness
that drives four stand-ins, including one that looks like a refusal. And the
two ending readers now share one `_committed_record` owner with one literal
label, which is both the reason the orphan count returns to its baseline and
the better code: the kind check, the journal decode and the document
ownership were written out twice for one rule.

Three counts, before and after: owned-never-probed 49/49,
attributed-to-no-entry 35/35, receiving-entries-with-no-owner 132/132. No
W76207 delta. The five failing identities in that module are the pre-existing
ones and I did not widen this Work into repairing them.

### Verification

- `tests.tools.test_single_worker`: 34 tests, exit 0. The two new cases were
  each driven against the unfixed code first and reproduce the reviewer's
  exact findings — `('refused', 'already-terminal') != ('policy', 'denied')`
  and `'claimed' != 'exceptional'`.
- `tests.manager.test_attempts`: 406 tests, exit 0.
- `tests/job_manager` discovery: 210 tests, exit 0.
- `tests.manager.test_secrets`, `test_text_sweep`, `test_credentials`,
  `test_lifecycle_composition`, `test_input_delivery`, `test_intake`: 374
  tests, exit 0.
- `tests.manager.test_boundary_inventory`: the five pre-existing failures,
  with the three counts at baseline as above.

### State

Passing back for independent review. PLAN item 10 — integration and submitting
W71917 through this seam — remains the post-review handoff. No version-control
state was mutated.


## 2026-09-03 — `baton.claude` (`impl`), W76207 correction pass 5

`review-2026-09-03T19-24-19Z.md` requested changes. Four P1s, all corrected.
Three of them are consequences of the shape I chose last pass, and the fourth
is a contract I wrote and then contradicted.

### P1 — naming after the record had no second chance

I wrote in the last pass that recording first "leaves the ending durable and
the naming still owed, which is the direction that loses least". That was
wrong and the reviewer's probe shows why: the record makes the stage
`exceptional` and the control plane calls this deployment only for `claimed`
stages, so nothing ever comes back for the naming. And only the branch where
`launch.adopt` answered ABSENCE reached it — contradictory material, which
`adopt` refuses rather than answering `None` for, bypassed it entirely.

The identification rides the owner's own call now, BEFORE the record:
`refuse_runtime_preparation` takes an optional adapter and reconciles first.
That is the order `_settled_and_recorded` already fixes for the sibling record
and for the reason it gives — the record NAMES the runtime the reconciliation
attached, so recording first durably says `None` about a runtime that exists.
It also makes a crash in between leave the stage claimed, which the next tick
drives through the same path again. The deployment passes that adapter for
every boundary that refuses after a start was requested, so no branch is
special, and the reconciliation never raises out of the recorder.

That forced the guard to change too. An axis check was the wrong question
twice over: which value the axis holds does not say whether an attempt has an
account already, and this operation now moves that axis itself. What it defers
to is the sibling record — a start act that failed has its own, and a
preparation ending written over it would be a second account of one act.

The residual window is named rather than left to be found: a crash between the
reconciliation and the record leaves the stage `running` with the runtime
attached. That is the direction that loses least here — the container is named
and observable, and what is lost is the composition's own refusal rather than
the runtime.

### P1 — authorship was the wrong ownership boundary

Mine, from last pass. A launch document published by a process that crashed
before its credential is ADOPTED by the next one, so the invocation that ends
the stage did not author it — and my rule then left its root present forever
with no runtime that could ever have mounted it. What decides is the state the
manager already proved: `not-started` says no runtime received either
delivery, so both are this composition's to end. After a start was requested
neither is.

### P1 — an untrusted bearer could wedge the manager

This is the adversarial equality the §13 suite already treats as valid, and I
had not thought about it. A provider answer equal to this attempt's own
durable identity is registered live by `materialize`, and every later §13 walk
over a row carrying that identity then refuses — so the manager could not read
its own attempt, nothing could be settled, recorded or reported, and both
roots stayed on the host. The cleanup `try` now spans the start request too,
so the colliding value is released — after its bytes are proved gone — before
durable state is read again.

### P1 — the record had two meanings and I wrote both

The schema comment, the reader's docstring and the dossier ruling all said the
record proves no start act happened; the continuation path I added in pass 4
writes it after one did. One meaning is pinned now, in all four places at
once: it is the DEPLOYMENT'S ending — its composition could not carry the
attempt further — and it says nothing about whether a start act occurred, what
exists on the engine, or what may be removed. The obsolete wording is marked
superseded in the FINDING rather than rewritten.

### Verification

- `tests.tools.test_single_worker`: 41 tests, exit 0, with four new cases —
  a crash between ending and identification, contradictory launch material, a
  launch adopted after a crash and then stranded by a provider refusal, and an
  end-to-end bearer equal to the attempt id.
- EACH new case was driven against the unfixed code first and reproduces the
  reviewer's finding: `None != 'runtime-single-1'` for both naming cases,
  `True is not false` for the stranded launch, and the §13 refusal escaping
  the sweep for the colliding bearer.
- `tests.manager.test_attempts`: 408 tests, exit 0, including the new
  reconcile-then-record, deferred-to-start-failure and
  identification-never-takes-the-ending cases.
- `tests/job_manager` discovery: 210 tests, exit 0.
- `tests.manager.test_boundary_inventory`: the five pre-existing failures,
  counts at 49/35/132 — no W76207 delta. The new adapter operand is a stated
  owner forwarded to `reconcile_runtime` with a witness that drives an
  unusable adapter and proves the ending is still recorded.

### State

Passing back for independent review. PLAN item 10 — integration and submitting
W71917 through this seam — remains the post-review handoff. No version-control
state was mutated.

## 2026-09-03 — `baton.claude` (`impl`), W76207 correction pass 6

Responding to `review-2026-09-03T21-24-16Z.md`. One P1, and it says my last
correction moved the loss rather than closing it. It is right, and the reason
is one I should have drawn myself when I named the window instead of weighing
it.

### P1 — reconcile-before-record still loses the preparation ending

I wrote last pass that a crash between the reconciliation and the record
"leaves the stage `running` with the runtime attached… the direction that
loses least". The probe shows what that costs: `running` is not a state the
control plane asks this deployment about, so the ending is not delayed, it is
gone — and the stage that failed is projected as an ordinary running success
that no launch will ever follow.

WHAT I HAD NOT SEEN IS THAT THERE IS NO THIRD ORDER. Recording first makes the
stage `exceptional` and the control plane stops asking; naming first makes it
`running` and the control plane stops asking. Whichever act goes first is the
one that removes the obligation to finish, so the two orderings are the same
defect twice and the argument I used to choose between them was never about
the thing that decides. The review named the two shapes that can close it, and
I took the first: an atomic owner commit after external identification.

ASKING AND RECORDING ARE NOW SEPARATE, AND COMMITTING IS ONE ACT.
`attempts._identify` makes every adapter call and answers a plan with no
durable effect; `_reconciled` owns what that plan means durably;
`reconcile_runtime` is exactly those two halves, so nothing changes for its own
callers. The ending applies the plan INSIDE the transaction that writes
`runtime.preparation-failed`, through `_attach`'s new `within` operand, which
performs the compare-and-swap and its observation on the owner's open
connection rather than opening a second transaction. A death anywhere in the
interval leaves neither fact and the stage still `claimed`.

THE SPLIT IS BETWEEN ASKING AND RECORDING RATHER THAN A MERGE OF THE TWO
OPERATIONS, and that is deliberate: an owner holds `BEGIN IMMEDIATE` for the
whole of its act, so an adapter call made under it would hold every other
writer out for as long as a remote engine takes to answer. Nothing asks the
engine from inside a transaction.

THE PLAN IS AN OPERAND BY IDENTITY. The signature carries the attempt, its
fixed assignment, the failure and WHICH runtime the engine named — never the
adapter's prose about it. An ending naming a different runtime still collides
rather than replaying, and the same ending described differently still
replays.

AND MY OWN WITNESS FOR THAT FOUND TWO HOLES I HAD JUST OPENED. Naming the
runtime rather than the decision word is better for an operator and it puts an
ADAPTER-SUPPLIED value into two places it had never been: the refusal message,
which `ContractRefusal` will not be constructed around when the registry holds
it live, and the ending's own signature, which is a §13 walk. The first would
have replaced this manager's ending with an assertion at the raising site; the
second left the ending unsignable and the control plane asking again on every
tick — the exact loop this record exists to stop, reintroduced by the
improvement. The account is checked before it is raised and drops the name
alone, saying why; the signature folds the name in as a digest, which
distinguishes the two acts exactly as the value would and quotes nothing. The
durable row needed nothing from me: the store already refuses to persist such
a value, so the attachment refuses, is contained, and the ending stands over
the axes that containment leaves. I would not have found either without
writing the witness, and I am recording that rather than presenting the guard
as something I designed up front.

TWO SMALLER CONSEQUENCES I AM STATING RATHER THAN LEAVING TO BE FOUND. Within
the ending the attachment is not a separately journalled `attempt.attach`
operation — it is one of the two facts the ending commits, and the outer row is
what a retry replays; the compare-and-swap is idempotent, so an independent
later `reconcile_runtime` still answers the same attachment. And the record's
axes are now composed INSIDE the act, after the attachment, because predicting
them beforehand would durably assert a prediction whose one wrong case is the
contained one — the case a reader most needs the truth about.

CONTAINMENT SURVIVES IN BOTH HALVES. Asking is contained outside the act as
before; applying is contained inside it by its own savepoint, so a refused
attachment is rolled back alone and the record still stands over the axes that
rollback leaves standing. A `BaseException` is deliberately not contained: a
process being torn down must not commit half of this.

### One thing I am reporting rather than fixing, because it is outside this
### patch boundary

**Open, not confirmed.** The sibling ending has the same SHAPE of interval.
`_settled_and_recorded` is still two acts — `_settle_failed_start` reconciles
and attaches, then `_record_start_failure` writes the row — and its docstring
gives the same "the order is the content" reason mine used to. If a process
dies between them the runtime is attached with no start-failure record, which
projects the stage `running`, and the control plane calls this deployment for
`claimed` stages alone.

WHAT I HAVE NOT ESTABLISHED is whether this deployment can reach it. The
dangerous case needs the engine to have created a container AND the start to
be refused afterwards, and the refusal fixtures I have leave no container, so
reconciliation answers `uncertain` rather than attaching. I did not widen this
Work to chase it: `request_runtime_start` and `runtime.start-failed` are
W6636/W26294 machinery rather than this Work's patch boundary, and the review
bounded this pass to the preparation ending. I would rather it be weighed and
given its own record than silently carried in a leaf that was scoped to one
P1. If you read it as in scope, say so and I will take it.

### Verification

- `tests.tools.test_single_worker`: 45 tests, exit 0, with the new
  `TheEndingAndTheNamingAreOneAct` case that interrupts exactly after the
  attachment lands inside the act and before the ending row exists.
- `tests.manager.test_attempts`: 412 tests, exit 0, with four new focused
  cases — the same interval at the manager boundary, an attachment that
  refuses being contained while the ending stands over the real axes, a
  stable identification replaying rather than colliding, and an identified
  name the secret registry holds live.
- BOTH crash regressions were driven against the pass-5 ordering first,
  reconstructed from the module's own privates. They reproduce the reviewer's
  probe exactly: `'runtime-single-1' is not None` at the production seam and
  at the manager, with the stage `running` on the crash and on the later tick,
  no preparation record, and zero later engine calls.
- The reviewer's preserved probe at `/tmp/w76207_reconcile_record_crash.py`
  now reports `claimed` after the crash and `exceptional` after the next tick,
  runtime named, one start, no replacement launch bytes.
- `tests/job_manager` discovery: 210 tests, exit 0. The six focused manager
  suites: 374 tests, exit 0.
- `tests.manager.test_boundary_inventory`: the same five pre-existing
  failures, counts back at 49/35/132 with no W76207 delta. Three `DELEGATED`
  entries and three injected probe sites follow the questions to `_identify`;
  the probes themselves are unchanged and still drive the public operation.
- Broad sweep `tests` discovery: 3517 tests, the same eight recorded failing
  identities and none new — the five boundary-inventory ones, the real-daemon
  bearer sweep, the parallel-runner registry and the Authority migration
  catalogue.

### State

Passing back for independent review. PLAN item 11 — integration and submitting
W71917 through this seam — remains the post-review handoff. No version-control
state was mutated.

## 2026-09-03 — `baton.claude` (`impl`), W76207 correction pass 7

Responding to `review-2026-09-03T22-00-26Z.md`. Two P1s, both corrected, and
the first is the one I handed you as Open last pass. You resolved it the other
way and you were right to: I said I had not established that this deployment
could reach it, and the shape that reaches it is one line of fixture — an
engine that denies a start it has already made.

### P1 — the sibling start-failure ending kept the same window

Corrected the same way and with the same owners, which is the point. Asking is
`_identification` and committing is `_identified_within`, both shared now, so
`_settled_and_recorded` and `_record_preparation_failure` are the same shape
rather than two spellings of one rule. `_record_and_raise_start_failure`
applies the plan inside the transaction that writes the row.

`_settle_unknown_start` came inside with it, and that is the half I would have
missed if I had only moved the reconciliation. It was a THIRD separate write,
and `uncertain` is a state the projection reads as terminal — so a death
between it and the record leaves an ended-looking stage with no ending, which
is the same defect one step further out. It also loses the `adapter` operand it
never used.

WHAT THIS DOES NOT RECOVER, said plainly because the regression asserts it. The
engine's account of WHY the start failed does not survive a death in that
interval: the record was its only durable trace. A resumed manager re-derives
from canonical state and the engine, and if a container carrying the labels
exists and observes as running it reports `running` — the same conclusion it
would reach had the process died one statement earlier. What atomicity buys is
that the stage never rests where the control plane will not revisit it, and
that no ending is ever written without its naming.

### P1 — the sibling guard went stale across the identification

I had not thought about the interval at all: I moved the engine query out of
the transaction for the write-lock reason and did not ask what could commit
while it ran. The guard is asked again inside the ending's transaction, where
there is no interval, and refusing there unwinds the attachment too because
they are one act.

The door check stays. It is not a duplicate of the inner one: it refuses the
ordinary case early with the closed pair callers already read, before anything
is asked of the engine, and both sites now say that the first read is not the
decision. That is the two-moment shape `request_runtime_start` already uses for
the lane.

A LOST RACE IS CONTAINED RATHER THAN RAISED. The caller is entitled to the
refusal it actually raised, and the control plane reads the start act's record
and reports that stage exceptional through it. Raising `already-terminal` here
would be the account swap review 2026-09-03T18:49:20Z already found on the
sequential path, arriving by a different door.

### OPEN — the pre-start unwind can remove a live container's mounts

Found while building the failed-start regression, reported rather than
corrected, and recorded in the FINDING.

`single_worker._unwound` decides from `fresh`, the execution axis as it stood
BEFORE the start was requested. A start that reached the engine, created a
container and then reported failure arrives there still called fresh, so the
credential root and the launch document are removed although a container may
hold both mounts. `OciAdapter._undelivered` owns exactly that question, asks
the engine, answers `unresolved` and removes nothing — and this deployment
removes it anyway. Measured: with the unwind unchanged the launch root is
absent after such a start; with it skipped the root survives.

I TRIED TO FIX IT AND STOPPED, twice. Deciding from the execution axis skips
the settled-`uncertain` path where a colliding bearer must still be released,
and takes the whole untrusted-bearer regression down with it. Deciding from
the attached runtime identity cannot even be READ on that path, because the
attempt row carries the very value §13 is refusing over — the read that would
decide is blocked by the condition the teardown exists to clear. Thirty-five
tests failed each time, and each failure was a rule already pinned in this
record.

The direction that works is to defer to the owner that already computed the
answer: only the paths where no owner has decided are the deployment's to end.
That needs `_undelivered`'s `unresolved` to reach the deployment as a value
rather than as refusal prose, which is a change to a boundary this Work did not
open. I would rather hand you that than make a fourth attempt inside a pass
scoped to two P1s. If you read it as in scope, say so and I will take it.

### Verification

- `tests.tools.test_single_worker`: 47 tests, exit 0, with a new
  `TheFailedStartEndingCommitsWithItsNaming` class: the ordinary denied start
  that left a container ends `exceptional` and names it, and a death in the
  exact interval leaves neither fact with the stage still `claimed`.
- `tests.manager.test_attempts`: 425 tests, exit 0, with three new cases — the
  settlement and the record landing together or not at all, the uncertain
  settlement proved part of the same act and resumable from what the rollback
  left, and the interleaving case proving exactly one ending survives.
- All three reviewer probes now report the corrected state:
  `w76207_start_failure_crash` gives `start-requested` / `runtime_id: null` /
  no record / one start; `w76207_competing_endings` gives the start record
  present and the preparation record absent; `w76207_reconcile_record_crash`
  still gives `claimed` then `exceptional`.
- `tests/job_manager` discovery: 210 tests, exit 0. The six focused manager
  suites: 374 tests, exit 0.
- `tests.manager.test_boundary_inventory`: the same five pre-existing
  failures, counts at 49/35/132 with no W76207 delta.
- Broad sweep `tests` discovery: 3532 tests, the same eight recorded failing
  identities and none new.

### State

Passing back for independent review. PLAN item 12 — integration and submitting
W71917 through this seam — remains the post-review handoff. No version-control
state was mutated.

## 2026-09-03 — `baton.claude` (`impl`), W76207 correction pass 8

Responding to `review-2026-09-03T22-20-58Z.md`. One P1, and it is the finding I
handed you as Open last pass: you confirmed it, ruled it in scope, and named
the direction I had proposed. Taking it.

### P1 — the deployment removed a live failed-start runtime's mount sources

WHAT WAS WRONG WITH MY TWO ABANDONED ATTEMPTS, now that the right shape is in
front of me. Both tried to re-derive the answer from durable state — the
execution axis, then the attached runtime identity — and neither is a fact
about WHO DECIDED. `OciAdapter._undelivered` had already asked the engine, seen
the live runtime and deliberately left both roots `unresolved`; it was the only
party that knew, and it said so only in the refusal prose its caller composes.
So the deployment could not tell a boundary an owner had settled from one
nobody had reached, and guessed — with the pre-start `fresh`, which is right
for the second case and wrong for the first.

THE ANSWER CROSSES AS A VALUE. `_undelivered` keeps the same structured
`{"credentials": ..., "launch": ...}` it already returned on the adapter as
`settlement`, and `_unwound` reads it. A settlement present means both mounts
were decided on that owner's own engine evidence and there is nothing here to
end. `None` means no owner reached the boundary, and there `fresh` remains the
whole rule — a refusal raised before the adapter existed, or before `start`
reached its settlement, still ends both local deliveries. The split in
`_undelivered` between recording and settling exists so every one of its exits
is kept without repeating the assignment at each.

THE BEARER STAYING REGISTERED IS THE SAME RULE, not a second one, and it is
why I could not simply "release the registration and keep the bytes":
`CredentialHome.tear_down` releases the registry only after the bytes are
proved gone, deliberately, because a registry released while a file still holds
the value says a credential is dead while it is readable on disk. A root that
may still be mounted keeps its registration.

### Verification

- `tests.tools.test_single_worker`: 49 tests, exit 0, with two new cases in
  `TheFailedStartEndingCommitsWithItsNaming` — the live runtime's two mount
  sources are left where they are, with its bearer still registered and the
  stage still exceptional and non-retried; and a refusal before that boundary
  still ends both local deliveries and releases the bearer.
- THE THREE SIDES DISCRIMINATE, which is the evidence that the change is the
  defect and nothing else. Driven against the pass-7 unwind, the live-mount
  case fails on exactly the launch root, while the pre-boundary case and the
  existing colliding-bearer case both pass under either rule.
- The reviewer's `/tmp/w76207_live_mount_unwind.py` now reports
  `launch_root_exists: true`, `credential_root_exists: true`,
  `credential_registered: true`, `stage_state: exceptional`.
- `tests/job_manager` discovery: 210 tests, exit 0. Eight focused manager
  suites including `test_oci` and `test_attempts`: 910 tests, exit 0.
- `tests.manager.test_boundary_inventory`: the same five pre-existing
  failures, counts at 49/35/132 with no W76207 delta. The kept settlement is
  an attribute beside the deliveries it is about, and `_settling` is private
  with the one operand its caller already owns.
- Broad sweep `tests` discovery: 3534 tests, the same eight recorded failing
  identities and none new.

### State

Passing back for independent review. PLAN item 13 — integration and submitting
W71917 through this seam — remains the post-review handoff. No version-control
state was mutated.

## 2026-09-03 — `baton.claude` (`impl`), W76207 signed off

`review-2026-09-03T22-32-34Z.md` signs off correction pass 8 with no further
findings. Eight correction passes, and the shape of the campaign is worth
recording once rather than being reconstructed from the passes:

- Passes 1–4 built the post-claim launch seam and the preparation ending, and
  each pass's own correction created the next pass's defect at the boundary
  just outside it.
- Passes 5–7 were one defect found three times: an ending and the fact that
  names it are two durable acts, and EITHER order loses the ending across a
  process death, because whichever act lands first moves the stage out of the
  one state the control plane drives. That is now one transaction for both
  endings, with the engine asked before it opens.
- Pass 8 closed the last one: a decision an owner had already made, carried
  only as refusal prose, so a second party re-derived it and got it wrong.

REVALIDATED AT HANDOFF against the signed-off tree: `test_single_worker`,
`test_attempts` and `test_oci` 585 exit 0, `tests/job_manager` discovery 210
exit 0. The working-tree path set is unchanged from what the review saw.

### State

Signed off; passing to `baton.ops` rather than closing. PLAN item 13 is the
remaining act and it is not this role's: no immutable proposal or candidate
digest was produced, so `baton.merge` has nothing to import, and what is left
is owning the remaining diff as Git state and deciding W71917 — the blocked
Work this seam exists to carry, itself routed to `baton.ops`. No
version-control state was mutated at any point in this Work.
