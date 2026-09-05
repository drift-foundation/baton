# Progress

## 2026-09-04 — baton.claude — implementation, and one operational finding

### Operational finding: this candidate was built on a checkout that changed underneath it

Recorded first because it bounds everything below it, and because standing
policy is to log rather than work around.

At approximately 07:53 local, while this implementation was in progress, the
whole W83781 candidate was removed from the working tree by something other
than this session: all seventeen of its source paths and its three record
files went from dirty to clean, with `HEAD` unchanged at `389cdd4`. That Work
had been passed to `baton.bug` for review and was not integrated; its content
survives only in the immutable proposal at
`/home/sl/baton-proposals/baton/W83781/2026-09-04T09-30-00Z`.

Two of this Work's own edits were collateral, because they live in files
W83781's candidate also touched:

- `tests/job_manager/fixtures.py` lost `FakeOperations.refresh_runtime`
  entirely (the file reverted to its committed content);
- `tools/single_worker.py` lost `_SingleWorker.refresh_runtime` and the
  `refresh_runtime=` wiring, while the `_Observation` class added in the same
  file at the same time SURVIVED.

Both were re-applied and both suites pass again. The point of recording it is
not the inconvenience: an implementer cannot certify that a candidate matches
what was measured if a third party is rewriting the same paths, and a
partially-clobbered file that still imports is exactly the shape that gets
packaged without anybody noticing. Every measurement below was taken after the
re-application and against the tree as it now stands.

**This dossier's pinned baseline is no longer reproducible as written.** The
reviewer's revalidation records "74 `tests.tools.test_single_worker` cases and
70 combined `tests.job_manager.{test_exchange,test_sweep,test_tool}` cases".
Those 74 were measured on a checkout that carried W83781; on the tree as it is
now the same module runs **71**, and the combined 70 is unchanged. Nothing
about this Work's boundary depends on the difference — W83781 added three
production-composition cases and no behaviour this Work reads — but a reviewer
comparing counts should be told which tree each number came from rather than
discovering the gap.

### The re-read the operator asked for, and what it found — 2026-09-04

The operator restored W83781's reviewed targets to base and asked for both
complete diffs to be re-read rather than assumed, on the grounds that in-flight
bytes may have been displaced. That was the right instruction and it found two
things, in opposite directions.

**Displaced and reconstructed.** `_SingleWorker.refresh_runtime` and its
`refresh_runtime=` wiring had gone from `single_worker.py` while
`_Observation`, added to the same file in the same edit, survived; and
`FakeOperations.refresh_runtime` had gone from `fixtures.py` entirely. Both
were reconstructed from plan items 1 and 2.

**Present and wrong, which a diff alone does not show.** `_Observation`
carried an Authority-binding comparison written while W83781's candidate was
in this checkout. It reads `JobStore.authority_uuid` — an attribute W83781
INTRODUCES and this Work's declared base does not have — so on the current
base `getattr` answers `None`, the comparison never matches, and it would have
refused every observation including every correct one. Nothing in this
dossier asked for that check.

It is removed rather than repaired, and the ordering is why: W83781 is ordered
behind W85500 rather than integrated over it, so a candidate here must not
depend on it. The binding belongs to that Work's boundary and is its to
enforce, in `operations_from` and in the store itself. The reason is written
at the site so a later reader does not restore it by sympathy.

The checkout is now base + W85497 + W85500. `job_manager.py` carries exactly
the `--observe` operand, `_Observing`, `_exchange_read` and
`_observation_from`, its only deletions being the two `_status` lines those
replace; `single_worker.py` carries exactly `refresh_runtime`, its wiring and
`_Observation`, with no deletions at all.

Focused verification after the reconstruction, all passing: `tests.job_manager`
246, `tests.tools.test_single_worker` 71, and
`test_exchange`+`test_sweep`+`test_tool`+`test_delegation` 84.

### Done: the serving runtime refresh (plan 1, 2)

`delegation.OPERATIONS` gains `refresh_runtime`, and `ManagerOperations` takes
an optional `refresh_runtime=` capability beside the three exchange ones. It
is a fourth capability rather than a member of `observe` because `observe`
answers what the control store RECORDS, and this asks the engine and records
the answer.

`manager.sweep` gains `_refresh` as the third pass in front of derivation,
beside `_observe` and `_replace` and for the same reason: the runtime axis is
state the tick can already know is stale. It runs before the first
`stage_states`, because what a stage owes and what a status says are both
derived from that projection — refreshing afterwards would decide this tick's
acts from last tick's runtime truth. A typed refusal is contained per stage
and reported against the stage that raised it, so one damaged attempt cannot
stop the sweep projecting anything.

The sweep document gains `refreshed`, a list of `stage.refresh` entries
carrying the stage, episode, attempt, the recorded state (or `not-asked` when
the deployment supplied no refresh) and, on a contained refusal, the typed
category and code only — never a refusal's prose, which is composed from
values a worker wrote.

`tools/single_worker.py` implements it with the naming-only OCI adapter and
the existing public `reconcile_runtime`. The adapter is built with no
credential delivery, no orphan and no launch delivery: all three exist for a
START, and this call identifies and observes. An attempt with no attached
runtime, or one already `destroyed`, answers `None` rather than asking a
question about a container that does not exist or that the transition table
has nothing after.

### Done: the observation-only status surface (plan 5, source half)

`tools/job_manager.py status` gains `--observe module:attribute`, resolved by
its own importer rather than reusing `--operations`' — reusing one name would
let a status run be handed a serving factory that opens an Authority and
carries mint, dispatch, ending and pass. The resolved object contributes
exactly one member, taken BY NAME: `observe_exchange`. Passing the object
itself through to `ManagerOperations` would hand it whatever else it happened
to carry.

`_Observing` is `_ReadOnly` plus that one durable-file read. It deliberately
does NOT refresh the runtime, and the class says why: reconciling records what
it saw, so a status command that refreshed would be a read that mutates. The
runtime axis in a status document is exactly as fresh as the serving loop that
last advanced the store.

`tools/single_worker.observation_from` / `observing_factory` build it from
immutable configuration and the already-open control store. It configures no
workspace group or storage, certifies no profile, constructs no credential
home, opens no Authority, mints no session, and holds no engine. It accepts
the Job store without reading it, exactly as `operations_from` does — the
Authority-binding comparison an earlier draft carried here is removed and the
re-read section above says why.

### Done: the evidence (plan 3, 4, the test half of 5, and 6)

**The fault/exit race, through the real owners.**
`AFaultedTerminalSurvivesTheContainerThatWroteIt` drives the REAL
`baton_worker` over the REAL exchange this deployment composed, with a
provider substitute whose turn fails; the worker's own rule produces the
correlated faulted terminal and returns 1. The container then exits UNASKED,
which is the race — nothing ordered it, so nothing in the manager had a reason
to look. The next sweep reports `exceptional` with the typed `fault_code` from
the durable file AND `quiescent` from the exact container, neither derived
from the other, with no engine start to find it out.

The fault code is `agent`, not run6's `output`. That is stated in the case and
is a deliberate choice: `output` is raised when a well-formed `work` answer
cannot name the completion envelope, and the worker PUBLISHES that envelope
itself from the answer — so producing it needs a broken publication rather
than a failing provider, which is a different defect and not this Work's.
Every member of `exchange.FAULT_CODES` reaches the projection identically: the
terminal's `ending` is what maps to `exceptional`. The case asserts the code
is in that closed vocabulary as well as naming this one, so a build that
widened the set fails there.

**The negative half, read from the owners' own records.** No intake receipt,
no retention, no act, no second command, one provider turn, one engine start,
the same episode. Repeated sweeps replay identical facts. A fresh incarnation
reopens both stores and reaches the same answer by rereading the same bytes,
with the retained terminal still present afterwards.

**Isolation and ordering, at the seam.** `test_sweep` proves exactly the
stages with a live episode are refreshed, that a deployment with no refresh
reports `not-asked`, that what the refresh recorded is what the same tick
projects, that one stage's refusal leaves every other stage refreshed with the
refusal's prose nowhere in the report and the tick's owed acts still
performed, and that repeated sweeps ask again and change nothing else.

**Both `--observe` branches.** `test_tool` proves the default is unchanged at
`exchange: null`, that the operand is resolved, asked for every stage and
released exactly once, that the composition carries no act and no refresh,
that a factory with no `observe_exchange` is refused by name, that a
non-`module:attribute` operand is refused, and that a refusing read still
produces a document rather than exiting. The exchange REACHING a status
document is proved where a real claim exists — in the production composition,
because `delegation._bound` correctly drops attempt-keyed observations for a
stage no claim binds to.

**One fixture change outside the authorized list, stated rather than
buried.** `tests/job_manager/fixtures.py` is not in this dossier's
test-change authority and is changed anyway, in two ways the new capability
requires and no case can supply for itself: `FakeOperations` gains
`refresh_runtime` (it is the closed surface a deployment must supply, so an
object without it is no longer that surface), and `operations()` forwards
`**supplied` so a case can name one optional capability. The refresh is
recorded in a SEPARATE list rather than in `calls`, deliberately: cases in
`test_restart.py` — which this Work has no authority to edit — assert `calls`
exactly to prove a pass performed nothing, and a per-tick observation every
live stage receives would change what those assertions mean. No existing
fixture behaviour changed.

**DEPLOYMENT.md** now names the three freshnesses: the serving loop is the
only thing that reconciles, `status --observe` reads the durable exchange and
deliberately does not refresh the runtime, and the bare read-only status is
unchanged.

### Measured

Job Manager 246 → 260. Production single-worker composition 71 → 77. The
dossier's combined `exchange`/`sweep`/`tool` baseline 70 → 81. Whole tree
3727 with the seven failures and one error that reproduce without this
candidate. Reproduced from base plus patch alone into a clean tree: every
candidate byte matched and both focused suites pass there.

## 2026-09-04 - baton.claude - response to review-2026-09-04T14-27-54Z

Three P1s, all reproduced and corrected. The first was the sharpest: a pass
added to stop one stage blinding the manager could itself blind it.

### [P1] An observation failure could abort the whole sweep

`_refresh` contained only `ContractRefusal`, and the manager called `.get` on
whatever came back. So a deployment answering a scalar aborted the tick with
`AttributeError`, and any other operational failure propagated - both BEFORE
the first projection, which suppressed an exchange terminal that was readable
on disk the whole time and stopped every unrelated stage. That is this Work's
own defect arriving by a different road.

Corrected in two places, because there are two different problems.

**The seam owns the result contract.** `delegation._refreshed` accepts `None`
or a mapping whose `execution_runtime` is in the closed `REFRESH_STATES`, and
refuses anything else as `integrity/schema`. The vocabulary is spelled in this
leaf rather than imported: it is the set THIS build will accept from a
deployment, and a value added to the Worker Manager's axis later is a value
somebody has to decide to accept here too.

**The pass classifies what escapes, and discloses it.** A `ContractRefusal`
reports its category and code. An `OSError` from the engine boundary becomes
`uncertain / engine-unreachable` - an engine that could not be asked is not a
runtime that is gone, and nothing is recorded from it, so the runtime axis
keeps whatever it last knew. Anything else is contained as
`fault / refresh-fault` carrying the exception TYPE.

That last one is containment with disclosure and not a blanket catch, and the
distinction is worth being explicit about because the review warned against
exactly the wrong version of it. Nothing is swallowed: the stage carries a
`fault` detail naming what broke, so an operator sees which deployment failed
and a defect cannot pass for an ordinary `not-asked`. What is refused is the
alternative - letting one stage's implementation defect stop every other
stage from being observed, which the acceptance forbids in as many words. The
type name is this manager's read of an in-process object and never a
worker-authored byte; no message crosses.

Five regressions: malformed shapes and vocabulary across five values, a thrown
`OSError`, a thrown `RuntimeError` - the review's own two probes among them -
each proving the other live stage still gets its answer and the tick's owed
acts still happen, and one proving a readable faulted exchange is still
projected `exceptional` while the refresh is broken.

**The fake now applies the real seam's rule** by calling `_refreshed` itself. A
stand-in more permissive than `ManagerOperations` would let a case pass that
production could not, which is the one thing it must never do.

### [P1] An explicit `--observe` was silently ignored without `--control`

`_status` answered `Unobserved()` before it looked at the operand, so an
operator who ASKED for observation got a successful run, `exchange: null`, and
no indication the request had not been performed. That is the same shape as
the defect this Work exists to correct: a surface reporting an absence it never
went to look for.

The combination is now refused with prose naming what is missing and why -
`launch.adopt` needs the workspace group the control store holds, so there is
nothing an observation factory can read without one. Refused rather than made
to work some other way: the operand names a deployment factory, and honouring
it without a control store would mean inventing a second composition nobody
reviewed. The regression also proves the factory is never resolved, so the
refusal is about the operand combination rather than about anything a factory
did.

### [P1] No behavioural proof of the no-durable-mutation boundary

The existing cases test capability absence and that `refresh_runtime` answers
`None`; neither would notice a durable write arriving by another route.

`test_a_real_observing_status_run_mutates_no_durable_state` runs the REAL
`tools.job_manager status --observe` through `main`, with both stores closed
first so nothing this process holds can mask a write, and compares every byte
of every durable file this deployment owns before and after - both stores,
their write-ahead siblings, and the launch and exchange trees, because a write
that landed only in a `-wal` file is still a write. The terminal must come back
in the same run, or the measurement is vacuous: an observation that returned
nothing would also mutate nothing. The snapshot is guarded against being empty
for the same reason.

### Re-run evidence

`tests.job_manager` 260 -> 265, `tests.tools.test_single_worker` 77 -> 78, the
dossier's combined exchange/sweep/tool baseline 81 -> 86, whole tree 3739 with
the same seven failures and one error that reproduce without this candidate.

### Still open

Independent review.

## 2026-09-04 - baton.claude - response to review-2026-09-04T19-08-40Z

Two P1s and one P2. Both P1s are reproduced and corrected, and the first of
them reverses an argument this progress file made a section ago. The reviewer
is right and the argument was wrong for a reason I had not looked at:
`manager.serve` keeps only the last tick.

### [P1] The refresh seam did not own a closed document

`_refreshed` accepted any `isinstance(answer, dict)` and read it through its
own `.get`. Both of the review's probes reproduce: an undeclared member was
accepted and silently discarded, and a `dict` subclass whose `.get` raises ran
that override inside the validation and propagated its `RuntimeError` out of
the boundary that exists to stop exactly that.

Replaced with the repository's existing owner, `boundaries.document`, which
takes a FRESH BUILT-IN COPY -- so a subclass is refused as "not JSON data"
before any of its methods can run, and the accepted answer is this seam's own
object rather than a live reference the deployment still holds -- and requires
exactly the named members, so an extra one is refused rather than dropped. The
closed `REFRESH_STATES` check stays where it was, after the shape.

Regressions in both places, because they are two different boundaries.
`test_delegation` drives `ManagerOperations.refresh_runtime` directly for the
extra member and the hostile subclass, asserts the refusal pair, and asserts
the accepted answer is a copy. `test_sweep` extends the existing malformed-shape
loop with the same two values and keeps proving that the other live stage still
gets its answer.

### [P1] Arbitrary defects were blanket-caught, and `serve` could lose them

The previous section of this file argued that `except Exception` here was
"containment with disclosure and not a blanket catch", on the strength of the
`fault / refresh-fault` detail it wrote into the sweep report. That argument is
wrong on the serving path and the review names why: `manager.serve` overwrites
`report` every tick and returns only the final one, so a defect contained on
any tick but the last is raised nowhere, recorded nowhere, and gone completely
as soon as one tick succeeds. A disclosure a successful tick erases is not a
disclosure. I had reasoned about a single `sweep` call and not about the loop
that actually runs it.

Corrected as the review directs, at the seam that can actually tell the
difference:

**The deployment names its own engine failures.** `delegation` gains
`RefreshUnavailable`, carrying the originating failure's TYPE NAME and no
message. `tools.single_worker._SingleWorker.refresh_runtime` translates
`OSError` and `subprocess.TimeoutExpired` from `reconcile_runtime` into it and
nothing wider. Those two are one operational fact in two Python types -- a
missing engine binary or a dead daemon socket, and a `subprocess.run` that hit
its deadline -- and the second is the review's own example of a value that used
to reach the blanket branch and be reported as an implementation fault.

**The manager contains exactly two conditions.** `ContractRefusal` and
`RefreshUnavailable`. The `except OSError` branch went with the blanket one:
the manager was deciding on every deployment's behalf what an unreachable
engine looks like, and a control plane composed over something other than an
OS process would have been wrong in both directions. Anything else ends the
tick and reaches whoever is running the loop.

The acceptance's stage-isolation sentence is unchanged and still holds:
malformed evidence and a named unreachable engine stay contained per stage,
the other stage is still refreshed, the tick's owed acts still happen, and a
readable faulted terminal is still projected `exceptional`. What is no longer
contained is this control plane's own defects. FINDING.md records that as a
clarification of that sentence and an explicit supersession of the previous
candidate's reading, so the argument I made above is preserved rather than
quietly deleted.

Six regressions. At the seam: an unreachable engine is `uncertain /
engine-unreachable` while the other stage is refreshed and both stages' owed
acts still happen, a `TimeoutExpired` is the same answer, an unreachable engine
never suppresses a readable exchange, and an arbitrary `RuntimeError` escapes
`sweep`. At the production composition, driven through the REAL engine
boundary rather than a stand-in for the translation -- the `Exiting` fixture
gains an optional `raising` -- an `OSError` and a `TimeoutExpired` each become
`uncertain / engine-unreachable` with the runtime axis untouched and the
durable terminal still projected `exceptional`, and a `RuntimeError` escapes.

### [P2] Proposal metadata contradicted its own finding

Correct and worth fixing rather than explaining: the packaged `PROGRESS.md`
and the manifest's `test_changes` still called the `fixtures.py` edit
unauthorized, from before the dated scope clarification that authorized it.
The next proposal's `test_changes` names it as authorized by that
clarification and keeps its narrow scope and no-weakening constraints. The
account above is this file's own correction of the same statement.

### Also changed

`DEPLOYMENT.md` now states what a failing refresh does: which two failures are
contained per stage and how each is reported, that nothing is recorded from an
unreachable engine, that neither containment touches the exchange axis, and
that anything else ends the tick -- with the `serve`-keeps-only-the-last-tick
reason, because that is what makes the boundary make sense to an operator.

### Re-run evidence

`tests.job_manager` 265 -> 267, `tests.tools.test_single_worker` 78 -> 81, the
dossier's combined exchange/sweep/tool baseline 86 -> 87, `test_delegation`
17 -> 18, and `test_sweep` 26 -> 27. All pass.

The whole tree ran twice against these bytes, 3752 cases each time: once with
seven failures and one error, once with eight and one. The extra one is
`test_dogfood_retry_engine::DockerPublicRetry::test_an_explicit_discard_still_
ends_complete_and_removes_the_tree`, and it is not this candidate's. That
module and `tools/dogfood_operator.py` import nothing from
`baton_v12.job_manager` -- they reach the engine through `worker_manager`
alone -- so no path this candidate changes is on theirs; it failed in one run
and passed in the other against identical bytes; and run alone against these
bytes it passes all four of its cases. Its failure is the real-daemon
quiescence race a host carrying leftover `baton-runtime` containers from
previous days produces, which is also what `test_credentials_engine` reports.
The error is the pre-existing parallel-runner registry one, and this candidate
adds no test module.

### One thing the implementer could not verify

The reverse-apply check on the packaged patch was NOT run here: this
deployment's PreToolUse policy hook refuses every Git patch-application
invocation, including the read-only check form. Recorded rather than worked
around. The reviewer runs it independently, as the last review did, and the
manifest says so in as many words.

### Still open

Independent review of the corrected candidate.

## 2026-09-04 - baton.claude - response to review-2026-09-04T21-52-30Z

One P2, in two places, and both are the same kind of error: prose that
described a path nobody had run. Corrected, and the first one is now measured
so it cannot drift back.

### [P2a] The unreachable-engine promise named a case it does not cover

`DEPLOYMENT.md` and the `refresh_runtime` comment both listed "a dead daemon
socket" among the failures reported `uncertain / engine-unreachable`. The
review reproduced the real answer through this composition and it is `policy /
denied`. I reproduced it independently: the runner is the Docker CLI, and a
daemon that is not listening does not stop the CLI from RUNNING -- it runs and
exits non-zero, `OciAdapter.list` calls `_denied` on a non-zero listing, and
`_SingleWorker.refresh_runtime` translates only `OSError` and
`TimeoutExpired`, so the refusal reaches `manager._refresh`'s
`ContractRefusal` branch and the stage carries `policy / denied`.

I had reasoned from "the daemon is gone" to "the socket connection fails in
this process", and the process that fails is the CLI's, one boundary further
out. The accepted containment is unaffected -- per stage, nothing recorded on
the runtime axis, exchange still read -- which is exactly why the error was
survivable in code and not in documentation: an operator who read this would
have gone looking for `engine-unreachable` after killing a daemon and found a
`denied` they had been told meant something else.

Both texts now promise only what the boundary distinguishes: an invocation
that could not be made (`OSError`) and one that hit its deadline
(`TimeoutExpired`). Both also state what a dead daemon actually produces,
because leaving that out would make the corrected text merely silent about the
symptom an operator is most likely to hit.

NO TYPED ADAPTER FAILURE IS ADDED. The review's alternative, and I am not
taking it in this bounded correction: it is a designed adapter change, it
belongs to `worker_manager` rather than to this Work, and the wrong version of
it -- wrapping every OCI `ContractRefusal` -- would report a mislabelled image
or a hand-edited listing as an unreachable engine, replacing one false promise
with a worse one. FINDING.md pins the ruling and says the typed failure must
be designed and pinned before it exists.

ONE ADDITIVE REGRESSION, because a corrected sentence is only as durable as
whatever measures it.
`test_a_dead_daemon_is_a_refusal_and_not_an_unreachable_engine` drives the
production composition with the Docker CLI's own non-zero
`Cannot connect to the Docker daemon` answer and requires `policy / denied`,
an untouched runtime axis, the daemon's prose absent from the report, and the
durable terminal still projected `exceptional`. It fails if somebody adds the
typed adapter failure without saying so. The `Exiting` fixture gains an
optional `refusing` answer beside its existing `raising`; every other case's
engine is unchanged and nothing existing was edited or weakened.

### [P2b] The fault/exit class described a reproduction it does not perform

The class docstring said its agent produces `fault_code: output` and that this
is "exactly the code run6 produced", while `Silent.work` raises, the
assertions require `fault_code: agent`, and `Silent`'s own docstring explains
at length why `output` needs a broken completion-envelope publication instead.
The class-level text was written before that reasoning and never revised, so
the file contained its own refutation two screens apart.

It now says what these cases reproduce: the RACE and not the code -- a
correlated faulted terminal on disk, the container gone, nothing having asked
-- with the `fault_code: agent` result named, the run6 `output` difference
named, and the pointer to `Silent` for the reasoning. The case docstring at
the unreachable-engine test carried the same dead-daemon claim as the source
comment and is corrected with it.

### Re-run evidence

`tests.tools.test_single_worker` 81 -> 82 (the one added case), `tests.job_manager`
267 unchanged, the dossier's combined exchange/sweep/tool baseline 87 unchanged,
`test_delegation` 18 unchanged. All pass. No existing case was edited.

### Still open

Independent review of the corrected candidate.

## 2026-09-04 - baton.claude - response to review-2026-09-04T22-11-30Z

Packaging only, as the review directs. NO SOURCE, TEST OR DOCUMENTATION BYTE
CHANGED. The twelve source paths in the new proposal are byte-identical to the
working-tree bytes that review compared, and the only record change is this
section.

### Operational finding: the reviewed bytes are already committed

Recorded first, because it changes what the package MEANS and it is not mine
to rule on.

The previous session ended while this Work was claimed. Between then and this
one, the checkout moved: `HEAD` is now `0650c61` -- "fix(v11): preserve live
claims across ACP poke settlement", committed 2026-09-04T22:14:13Z, three
minutes after the review that returned this Work for packaging -- and every
one of this candidate's twelve source paths is IN that commit, byte-identical
to what the review examined. The working tree is clean for all twelve. The
three record files are still untracked and are not in it. That commit also
carries several other Works' source, including the dogfood operator, the
Claude agent worker and the ACP bridge.

Measured rather than assumed. For each of the twelve paths the SHA-256 at
`0650c61` equals the candidate digest this proposal records, and the SHA-256 at
`389cdd4` equals the base digest the previous manifest recorded and this one
re-verifies. All twelve base digests still match, so the declared base has not
drifted; it has simply stopped being `HEAD`.

Two consequences a reviewer and an integrator each need:

- The proposal still declares base `389cdd4`. That is the only commit this
  patch applies to, the base every measurement in this dossier was taken
  against, and the base whose per-path digests verify. Declaring `HEAD`
  instead would produce an empty source patch and turn a reviewable change
  into a document about nothing.
- Applying that patch FORWARD to the current checkout will not be clean.
  `baton.merge` will find every source target matching the CANDIDATE rather
  than the declared base, and its authority preflight should refuse for drift
  rather than import. The manifest says so under `base_and_head` in as many
  words, so the refusal is met as a disclosure rather than discovered.

Whether that commit already discharges this Work's integration is an operator
ruling. So is whether a v12 job-manager candidate belonging to a Work still
awaiting review belongs in a commit whose subject is a v11 ACP fix. I am
reporting both rather than deciding either, and I have changed nothing in
response to them.

### Re-measured against the packaged bytes

From `v12/python`, `PYTHONPATH=src:../worker`: `tests.tools.test_single_worker`
82, `tests.job_manager` 267, the dossier's combined exchange/sweep/tool
baseline 87, `test_delegation` 18. All pass, and all four match what the last
round reported. Whole tree 3753 cases, 7 failures, 1 error, 14 skipped: the
five boundary-inventory, one authority-catalog and one real-daemon host-state
failures, plus the parallel-runner registry error, which names
`tests.tools.test_quiescent_assignment_finalization` as the unregistered
module. None of those four modules mentions `job_manager` anywhere and this
candidate adds no test module. The dogfood-retry failure the previous round
recorded did not reproduce here.

The whole-tree number is NOT comparable with the 3739 and 3752 of the previous
two proposals, and the reason is now a commit rather than a dirty checkout:
`0650c61` brought other Works' test modules into the tree. The focused counts
are the ones that bound this candidate and they are stated before and after on
the same tree.

One measurement worth writing down because I had it wrong first. Run
STANDALONE with `PYTHONPATH=src` alone, `tests.tools.test_single_worker` errors
15 of its 82 cases with `ModuleNotFoundError: baton_worker`. Four of the
fifteen are in `TheAnsweredEndingRunsThroughTheRealOwners`, which predates this
candidate: the module reaches the real worker through a `sys.path` entry that
`tests/manager/test_worker_entry.py`, `test_worker_image.py` and
`test_claude_agent.py` each add as an import side effect under whole-tree
discovery. Pre-existing coupling, not this candidate's, and the manifest now
states the exact command rather than a bare count.

### What the manifest corrects

The 22:11:30Z review named four stale facts and all four are fixed: the
dead-daemon boundary text, the fault/exit class count and what it actually
proves (TEN cases, and the RACE rather than run6's `output` code), the
candidate and record digests and byte counts, and the test-change account. The
`corrections` list gains the 21:52:30Z P2 entry it never had and a packaging
entry for this round. `base_and_head` is new.

### Still open

Independent review of the digest-bound proposal, and the operator ruling above.

## 2026-09-04 - baton.claude - response to review-2026-09-04T22-54-17Z

One P2, in proposal metadata. Correct, reproduced, and fixed. NO SOURCE, TEST
OR DOCUMENTATION BYTE CHANGED: the twelve source paths carry the same digests
they did in the 22-49-00Z proposal, and PROGRESS.md is again the only record
change, so only the patch and the digests move.

### [P2] The manifest's live boundary still made the promise its own corrections retract

`boundary[6].how` still said the deployment's translated `OSError` covers "a
missing engine binary or a dead daemon socket". That is exactly the claim
review 21-52-30Z measured false and that DEPLOYMENT.md and the
`refresh_runtime` comment were corrected to drop a round earlier.

How it survived is worth writing down, because it is a packaging failure mode
rather than a typo. Repackaging, I went through the manifest sections the
22-11-30Z review NAMED -- acceptance, corrections, verification, test_changes,
the digests, the base note -- and added `base_and_head`. I never opened
`boundary`, because nothing had told me to. So the same manifest ended up
asserting the corrected fact in two sections and the retracted one in a third,
and the reviewer is right that the contradiction is worse than the stale line
alone: `boundary` is the section describing what the candidate DOES, so an
integrator reads it as current proposal truth and the accurate entries
elsewhere look like history.

`boundary[6].how` now names only what the deployed translation distinguishes --
an invocation that could not be made at all (`OSError`, such as a missing
engine binary) and one that reached its deadline (`TimeoutExpired`) -- and
states that a dead Docker daemon currently reaches the separate `policy /
denied` refusal path, is contained per stage, records nothing on the runtime
axis, and is not `uncertain / engine-unreachable`. It is now the same sentence
the source comment, DEPLOYMENT.md, `acceptance[5]` and `corrections[5]` make.

### The rest of the manifest, audited rather than assumed

Fixing only the line a review points at is how the next round gets the same
finding somewhere else, so I searched every string in the manifest for
`daemon`, `socket`, `unreachable` and `OSError`. Fifteen hits across seven
sections. `boundary[6]` was the only live false claim; the other fourteen are
accurate or are explicitly historical.

One of them deserves naming because it looks like the same defect and is not.
`corrections[0].resolution` still says an `OSError` becomes
`uncertain / engine-unreachable` and anything else is contained as
`fault / refresh-fault`. That is the 14-27-54Z round's own account of what it
did, and `corrections[4]` is the 19-08-40Z entry that supersedes it in the same
list. It stays: the corrections list is chronological history, and rewriting an
entry to match the current rule would delete the reasoning that explains why
the current rule is not the obvious one. What the reviewer objected to was a
LIVE description contradicting a correction, which is a different thing.

### Verification

Nothing to re-run for a metadata change, and I did not pretend otherwise --
but the checkout is shared, so I re-verified the bytes rather than assuming
them. `HEAD` is still `0650c61`, all twelve source paths still match the
22-49-00Z candidate digests exactly, and all three record paths still match
except PROGRESS.md, which this section changes. The focused counts recorded in
the manifest were measured against these exact source bytes and are unchanged:
single-worker 82, job-manager 267, exchange/sweep/tool 87, delegation 18.

The reverse-apply check is still not run here; the previous review ran it
independently against the 22-49-00Z patch and it passed.

### Still open

Independent review of the regenerated proposal, and the operator ruling on the
already-committed source recorded in the previous section.
