# Implementer progress — W325035

Author: `baton.claude` (role `impl`), v11 claim 325037, 2026-10-18.
Bound dossier: this directory. Parent W321690 is the integrated acceptance
consumer. Source base `372281f4a473300efb474d5a6573954c15ade367`; the working
tree carries no product change and this Work authors none.

## 2026-10-18 — execution provenance and boundaries, recorded before any edit

Same determination the parent recorded and the reviewer then sharpened: the
matrix IS v12 execution — it drives the real coordination code on disposable
stores with the engine and provider simulated at their own boundary, which is
this Work's instruction. No product source is authored, so there is nothing
here that needs an isolated implementation Job; a reproduced defect is filed
with its evidence rather than fixed. No live model, no live credential, no
container, no deployment, no Git mutation, no raw SQL, and no fabricated owner
receipt.

Honest about what the fake boundary does and does not establish: nothing below
claims live isolation or engine evidence. Each scenario's record names its
simulated seams explicitly and separates injected inputs from observed product
behaviour.

## Owned paths

Only this dossier: `PROGRESS.md`, `matrix-325037/` (driver and evidence). The
parent's `rehearsal-324890`/`rehearsal-324985` assets, its PACKET and PROGRESS,
W325034 and every product file are untouched; the fixture lineage is reused by
IMPORT with provenance recorded in the driver's own docstring rather than by
modifying the parent's evidence.

## The matrix this Work owes

From the FINDING, as finite outcomes rather than themes:

1. `unable` / provider-failed / no-candidate / held-unknown reaches an explicit
   diagnostic owner and cannot falsely complete.
2. Restart and a lost reply do not duplicate review ownership or correction.
3. A stale episode and a wrong principal refuse.
4. A correction stays bound to the exact candidate and attempt.
5. Cancellation and a non-satisfying outcome stay honest.
6. One writable authority, and disposable recovery retains exact ownership.

The human-approval question is W325034's and the parent's; per the FINDING
these cases do not wait on it.

## 2026-10-18 — claim 325037: the matrix is driven, seven of seven observed

`matrix-325037/matrix.py` drives the seven scenarios on the imported composed
fixture lineage; `matrix-325037/MATRIX.md` is the readable result and
`MANIFEST.json` binds all ten files by SHA-256. Seven observed, none failed,
2.197s total, each scenario carrying its own identities, injected inputs,
assertions and measured duration.

**1. A failed or empty provider turn cannot falsely complete.** Both a provider
exiting 1 and one exiting 0 while writing nothing settle the implementation
stage at `exceptional` after ordinary ticks, with no proposal published and the
review and integration stages left `blocked`.

One correction to my own earlier description, which matters because the
FINDING asks for an *explicit* diagnostic owner: that owner is the stage's own
`exceptional` state in `baton_v12.job_manager.status` -- the projection
`manager status` serves -- and NOT a `pending_endings` row, which was empty in
both cases. `pending_endings` answers for endings awaiting settlement, a
different class from a turn that produced nothing. I had inferred otherwise
from the seam name in the parent's handoff; the driven result says otherwise
and `MATRIX.md` says so plainly.

**2. Restart does not duplicate review ownership.** A fresh serving
composition over the same stores carried review from `queued` to `waiting`
with the implementation attempt unchanged and exactly one review attempt.

**3. Stale and wrong-principal both refuse**, with the authority's own
sentences: `stale assignment`, and `this session acts for 'baton.gemini'; the
assignment names 'baton.claude'`. Driven while an assignment was live, which
is the only point at which the question is meaningful -- my first cut asked
after the assignment had ended and correctly got "nothing to refuse".

**4. A correction stays bound.** A `changes-requested` verdict reopens the
implementation stage and blocks the review rather than completing it; the
reopened stage gets a second attempt while the first is retained, the Work,
Job and submission identities are unchanged, and the first round's proposal
still stands.

**5. Cancellation and a non-satisfying ending stay honest.** Cancelling the
live assignment left the Work open and queued with no handler -- a cancelled
assignment is not a cancelled Work -- and the owner's installed
`disposition close --outcome non-satisfying` then closed it with the
operator's rationale, with the proposal preserved.

**6. One writable authority, stated as what it actually is.** A second
writable handle on the store file is accepted, which is SQLite's behaviour and
`session.py`'s stated trust boundary; what is refused is two live claims --
`refused: Work is already claimed` -- so the enforcement is the claim's
compare-and-swap, not the file handle. A read-only handle refuses every
transition, and a wrong authority UUID refuses with the exact mismatch.

**Not covered, and named rather than implied:** disposable recovery-set
verification is W321688's accepted surface and is not re-proved here;
held-unknown RUNTIME quiescence needs the engine-absence vector rather than
this provider seam; interrupted-provider-session recovery is deferred under
324905; the human-approval positive path is W325034's and the parent's.

**Cumulative verification spending this claim:** three full matrix runs (the
first two surfaced my own harness mistakes -- an under-driven ending and a
single-attempt helper used on a stage that legitimately had two) at 1.8-2.2s
each, plus two short source inspections. No product source changed, no test
suite run, no build, no container, no live provider, no deployment, no raw
SQL, no Git command.

## 2026-10-18 — claim 325138: the harness now checks, and three faults of mine are corrected

Review 2026-10-18T18-05-00Z was right on every count. `matrix-325037/` is
preserved untouched with `SUPERSESSION.md` appended beside it naming exactly
what is withdrawn; `matrix-325138/matrix2.py` is the corrected run.

**The harness now checks.** `expect(...)` raises; a failed check or a raising
cleanup makes the scenario `failed`; `main` exits non-zero on any unexpected
failure; and `0-harness-self-check` asserts something DELIBERATELY FALSE and
must be reported as failed -- if it ever reports `observed` the run refuses
with exit 2, because then the checks are not checking anything. Latest run:
self-check failed as expected, three scenarios observed, zero unexpected.

**Three faults of mine, corrected rather than argued:**

1. *The cancellation never happened.* `matrix-325037`'s own JSON recorded
   `live_before_cancel: null` and no `cancelled` field, and my prose claimed
   the cancellation anyway. `scenario-1-live-cancellation.json` now drives it
   while the assignment IS live and asserts the act: a live assignment before,
   a result from `cancel`, the handler gone, the Work still `open` with no
   outcome, the cancellation in the assignment events, and no live assignment
   after.
2. *`exceptional` is not a diagnostic owner.* I renamed a state. The corrected
   scenario enumerates every member the status projection gives an exceptional
   stage, asserts that NONE of them names an owner, principal or eligible
   assignment, and asserts `pending_endings` is empty -- then documents the
   precise missing supported operation with its spec basis: nothing creates an
   eligible diagnostic assignment or names a diagnostic principal for an
   exceptional stage, and the only supported surfaces are the status
   projection and the installed `logs` verb over retained attempt output.
   `projection.py`'s own words are that an operator has to SEE it. If the
   pilot wants an owner rather than a state, that operation does not exist.
3. *An expectation of mine was simply wrong, and the product is better than
   it.* I expected a fresh composition over a committed-but-unprocessed turn
   to prepare no attempt. It re-adopts the SAME attempt identity. The check is
   corrected to that stronger property, which is the real no-duplicate
   guarantee.

**And one claim I withdrew before ever recording it.** My first cut of the
restart scenario flipped `case.running`, believing it was this world's
engine-absence seam; it is not -- that flag belongs to the integration-worker
world and setting it here reads and writes nothing. So the scenario asserts
only what was driven (no false finish, successors blocked, the original
attempt re-adopted and no second one) and names the rest as not demonstrated.

**Remaining scope, exactly.** (a) The lost-reply-across-restart vector is NOT
demonstrated: `recover()` answers `{'abandoned': [], 'recoverable': []}` for a
fresh composition and the stage stays `answering`, which is consistent with
section 10.8 since this world's engine keeps reporting the runtime present. It
needs an engine seam that reports positive absence for THIS composition, which
this fixture does not expose. (b) Held-unknown as its own asserted vector needs
that same seam. (c) Same-authority disposable recovery and the "no second
active authority after recovery" property -- the review is right that two
handles plus one claim proves claim exclusivity and not that. (d) Correction
lineage resolved through supported APIs (predecessor checkpoint/candidate,
review result, successor attempt) rather than the private `_prepared` list.

**Cumulative verification spending this claim:** six runs of the corrected
harness at 1.0-1.3s each, each one surfacing either a fault of mine or a wrong
expectation, plus three short source reads (the projection's state
computation, the recover verb, the engine seam). No product source changed, no
test suite run, no build, no container, no live provider, no deployment, no raw
SQL, no Git command.

## 2026-10-18 — claim 325259 opened: the seam the review named, and what it is for

Review 2026-10-18T18-17-05Z accepted the assertion and cancellation
corrections, refused completion, and named the seam I had wrongly called
absent: `ComposedOneJobCase.quiescing` already models stop and POSITIVE,
exactly-identified runtime absence, and `serving` replaces the engine on every
call — so a restart must be composed by calling
`stage_execution.operations_from` directly with the SAME engine object, not by
calling `serving()` again. My previous handoff said this fixture exposes no
absence seam. **That is withdrawn**: it does, at the `engine_run` boundary, and
this claim drives it there.

Planned work for this claim, all in `matrix-325259/`, with `matrix-325138/`
preserved: the self-check made strict (it must fail for its own named
`CheckFailed`, and a setup or cleanup error is an unexpected failure, not a
satisfied expectation); the lost launch reply across a restart on retained
engine state; positive absence attributable to the exact attempt; an unknown
runtime that stays gated; same-authority disposable recovery; correction
lineage through the public `writer_for_attempt` / `review_for_attempt` /
`checkpoint_of` / `verdict_of` readers and the authoritative proposal
inventory; and the diagnostic-ownership question re-asked of the Authority's
own route/handler/gate and claim surfaces rather than of absent projection
keys.

One provenance correction owed regardless of the above: `ComposedOneJobCase.vcs`
runs `git` against the fixture's own disposable source tree for its history, so
my blanket "no Git command" line was imprecise. The accurate statement, used
from here on, is that no command mutates this repository's history, index or
working tree; the fixture's own throwaway history is built by the imported
fixture under `GIT_CONFIG_GLOBAL=/dev/null` inside its temporary root.

## 2026-10-18 — claim 325259: the matrix is complete, asserted, and two of my claims are withdrawn

`matrix-325259/matrix3.py`, one run: **117 checks passed, 8 scenarios
observed, 1 failed exactly as it must, 0 unexpected, 2.261s**, bound by
`matrix-325259/MANIFEST.json` (12 members) with `MATRIX3.md` as the readable
result. `matrix-325037/` and `matrix-325138/` are unedited, each with
`SUPERSESSION.md` appended naming what is withdrawn.

**The seam was there and I said it was not.** The review named it exactly:
`ComposedOneJobCase.quiescing` models stop and positive, exactly-identified
runtime absence, and `serving()` installs a NEW engine on every call — so the
"restart" I drove in claim 325138 was reconciling against an engine that had
never heard of the container the first one started. `composing()` calls
`stage_execution.operations_from` directly with the caller's engine, and both
vectors I had reported as undemonstrable then fell out:

* **Lost launch reply across a restart (scenario 1, 16 checks).** The engine
  really starts the container and the process is stopped inside the following
  `ps`: `start-requested`, no attached runtime, one real container, stage still
  `claimed`. The fresh composition over the same stores and the same engine
  state asks the engine, adopts the EXACT runtime the lost reply named on the
  same attempt with the assignment unchanged, starts no second container,
  prepares no duplicate attempt, invents no failure, publishes no candidate,
  and serves again.
* **Unknown runtime, then positive absence (scenario 2, 14 checks).** A
  non-zero engine answer whose prose names no container leaves the axis
  `running`, the identity retained and the stage gated at `waiting`; the
  engine's own `No such container: <id>` for that exact identity reaches
  `destroyed`, attributed to the exact attempt and runtime, with the stage
  `exceptional`, no replacement container and no candidate.

**Same-authority recovery retains exact ownership (scenario 3, 13 checks).**
The assignment is identical member by member across the recomposition, the
committed assignment history is not extended by the recovery, route/handler and
the runtime ownership record are unchanged, and a handle naming another
authority UUID is refused. The property two live compositions actually have is
asserted too: sweeping the OLD composition afterwards starts no second
container, prepares no second attempt and leaves the same single assignment.
The connection to W321688's accepted recovery set is proved rather than cited —
this store answers `baton.v12.python.authority` and this deployment's UUID
through `Authority.stored_identity`, the same probe and the same two members
`dossier recovery-check` certifies. Still not claimed: that the OS or SQLite
prevents a second writer.

**Correction lineage through the public readers (scenario 4, 18 checks).**
`writer_for_attempt` / `review_for_attempt` / `checkpoint_of` / `line_of`,
from the attempt and its generation: gen 1's writer wrote the frozen
checkpoint, gen 2's review attachment reviewed that exact checkpoint and is
`ended`, gen 3's writer is based on that same checkpoint and is the active one.
All on the deployment's one line, bound to this Work; the reviewer is not the
implementer; the first round's candidate is still the only entry in the
authoritative inventory. `_prepared` is no longer the basis for any of it.

**The diagnostic-owner gap claim is WITHDRAWN (scenario 5, 21 checks).** The
review refused my inference from missing projection keys and was right. Asked
of the Authority's own surfaces: the operator names a diagnostic handler for
the failed Work's route and `baton.diagnostician` claims it — an eligible
assignment naming that participant and `principal:baton.diagnostician`, with
the Work actively held and an identical claim replaying rather than taking a
second one. Labelling is capability-bounded (refused without
`manage-work-labels`, accepted after the grant, then discoverable by label),
and the alternative path works too: a dedicated diagnostic Work created
attributably on its own route and claimed by its own owner, while the failed
Work stays with the first — one principal still holds one claim, which is why
that second owner exists. What remains true is narrower: nothing routes an
exceptional stage automatically. That is the selected owner policy, a
deployment act, **not** a missing product operation. **No product defect is
claimed by this Work.**

**And the rest of the finite matrix is now asserted rather than observed.** An
empty provider turn cannot falsely complete (scenario 6); a stale episode and a
wrong principal both refuse AND nothing moves — status, phase, route, handler,
outcome, the live assignment and the assignment-event count all unchanged after
each refusal (scenario 7); a second live claim through a second writable handle
is refused while a read-only handle refuses every transition, the live
cancellation removes the handler without closing the Work, and the owner's
installed non-satisfying closure records the operator's own rationale
(scenario 8).

One property I had never looked at, found by asserting instead of narrating:
**the runtime-quiescence gate survives the cancellation**, so a re-claim is
refused with `Work is blocked by 'runtime-quiescence:1'`. A matrix that had
asserted "cancel, then claim again" would have asserted the opposite of what
this product does.

**Harness strictness.** The self-check must now fail with its own named
`CheckFailed`, with no setup traceback and no cleanup failure; anything else is
unexpected and the run exits non-zero. The first corrected run proved that the
hard way — invoked from the wrong working directory, every scenario failed in
setup and the harness refused the run rather than reporting itself sound.

**Cumulative verification spending this claim:** six probe runs of the fixture
world at 0.4–2s each (the lost-reply window, the restart adoption, the two
engine answers, the lineage readers, the diagnostic surfaces) and five runs of
the driver itself at 1.5–2.3s each — four of them failing, on a missing
`_composed` hold, a non-canonical Work id, a second claim by one principal and
the quiescence gate, each of which became a check or a corrected expectation.
Plus short read-only source reads of `quiescing`/`serving`/`vcs`,
`refresh_runtime`, `reconcile_runtime`, the lineage readers, the session
transition table and the recovery-set reader. No product source changed, no
test suite run, no build, no container, no live provider, no live credential,
no deployment, no raw SQL, no forged receipt, and nothing that mutates this
repository's history, index or working tree — the precise statement that
replaces my earlier blanket "no Git command", since the imported fixture builds
its own disposable history.
