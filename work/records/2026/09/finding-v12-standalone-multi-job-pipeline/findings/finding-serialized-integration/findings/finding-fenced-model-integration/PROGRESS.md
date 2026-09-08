# Progress

Ledger Work W101492 created; implementation waits for the runtime and
candidate-admission leaves.

## 2026-09-06 — baton.claude — the assembly, which is mostly a decision

W101492's first implementation round, against both blockers closed. New
`src/baton_v12/integration/execution.py` and
`tests/integration/test_execution.py`, one `tools/parallel_test.py` registry
entry, and the package `__init__` re-exporting the verb. 27 focused cases for
this leaf; 329 across the whole integration package.

### What the revalidation changed about the plan

Item 2 asked me to implement "the live-grant-to-exclusive-target-access seam
and generic Work instruction/result exchange". Both already exist and are
accepted: `runtime.compose_assignment` reads the live grant, the accepted entry
and the grant it follows out of ONE relationship pass and refuses an attempt or
profile kind that is not the grant's or a predecessor the manager has not
observed stopped, and the durable delivery is the exchange. Building either
here would have been a second one.

So this leaf is an ASSEMBLY, and what it adds is the ONE decision both leaves
deliberately refused: **which coordinator verb a model's claim earns.**
`runtime.observed_result` adopts a claim in the coordinator's own three
terminal words and settles nothing, because choosing between
`settle_integrated`, `refuse_entry` and `block_target` is a decision about the
world and belongs where the whole attempt is visible.

### The proof this leaf adds on its own

**Nothing settles behind a running model.** A terminal document in the delivery
is the runtime's CLAIM that it finished; whether the runtime is gone is the
manager's durable `execution_runtime` row, read through the same function the
runtime boundary uses for a predecessor. Settling behind a runtime that is
still up would record a result about a tree that is still moving. Every
non-quiescent state refuses and both positive ones settle, driven per state.

The other proof is the ruling's second cutpoint, already required: the live
grant is re-read immediately before settlement.

### Where the two vocabularies meet, and why it is here

`runtime.observed_result` adopts a result whose `detail` is a document and says
no more -- that boundary's own commentary records that what a verification must
CONTAIN belongs to the leaf performing the import. This one. So `_settled` owns
the model's detail as the settlement its outcome requires, and it does that
through `queue._settlement` rather than a second spelling of the coordinator's
rules: what this module admits is exactly what the store will accept. A detail
the coordinator cannot record is runtime material outside its contract, so it
becomes a HOLD rather than an exception -- the least trusted program in the
deployment must not be able to raise out of a sweep.

### What it does not do

It stages and commits nothing. It repairs nothing, decides no policy, and
RECOVERS NOTHING: an unanswered attempt is `running`, reported with its grant
and its entry exactly as they were, because under the owner ruling of
2026-09-06 an interruption is an operator's. `settle_observed` is separate from
the start for the same reason -- a later incarnation adopts the delivery off
the disk and settles a model that finished after the first sweep looked,
without starting anything.

### Verification

    PYTHONPATH=src:. python3 -m unittest tests.integration.test_execution \
        tests.integration.test_admission tests.integration.test_runtime \
        tests.integration.test_coordinator
    -> Ran 329 tests, OK (skipped=1)

One class per acceptance clause:
`TheSmallestEligibleEntryIsTheONEThatRuns` (rank order, the model asked for the
entry the grant named, an empty queue starting nothing, a second attempt never
reaching the model while one is live, and two targets integrating
concurrently), `TheModelSCLAIMEarnsExactlyOneVerb`,
`NothingSettlesBehindARunningModel`, `AnUnansweredAttemptIsReportedAndLeftAlone`
(including a restart that settles from the disk), `UnreadableOrForeignMaterialHoldsTheTarget`
and `ThePortIsInjectedAndTyped`.

Broad sweep, both phases, re-run AFTER the package export was added rather
than reported from the run that preceded it:

    -> parallel source: 579 shards, 4051 tests, 6 failures, 0 errors, 4 skipped
    -> serial source: 16 shards, 235 tests, 4 failures, 13 skipped

4286 tests, 10 failures, byte-identical to the recorded baseline. The
whitespace and registry gates pass.

## 2026-09-06 — baton.claude — the review: two proofs about the wrong instant

`review-2026-09-06T14-35-14Z.md` accepted the coordinator verb mapping and
found two [P0]s and one [P1]. All three are corrected. 39 focused cases for
this leaf (27 before), 341 across the integration package.

### [P0] Admission proved a moment, and execution is a different moment

Every member of the account was proved from its accepted producer when the
entry received its rank -- and an entry WAITS. Authority may advance the
canonical target, or a producer may cease to agree, while it sits in the queue.
The assembly gave such an entry writable access and could settle it integrated.

`admit_candidate` is now `resolved_account` plus `enqueue`, and execution
re-runs that same resolution under the live grant, before the delivery is made
and before the model is asked. Using admission's OWN function rather than a
second reading of the same sources is the point: two spellings of one proof
drift exactly where it matters. The selectors come out of the stored entry, and
every member of the fresh answer must equal the admitted one.

Driving it taught me something worth recording: the producers' own
cross-binding catches most staleness FIRST -- an advanced canonical target
refuses inside `resolved_account` rather than reaching my comparison. So the
suite drives both halves, including one change no cross-binding touches (the
Job's own `test_scope`, whose digest is a member nothing else corroborates),
which is the case that exercises the member-for-member comparison itself.

### [P0] A positive observation is about an instant

The quiescence proof was real and could be satisfied by an observation made
BEFORE the model ran, because nothing bound the port to the manager's lifecycle
for that attempt. The reviewer found it in my fixture -- which recorded
`destroyed` and then invoked the writer -- and was right that the fixture could
only demonstrate it because the code permitted it.

An attempt already observed stopped is now refused BEFORE the port is asked,
and the same attempt must be observed stopped before its claim settles. The
pair is what pins the observation to the interval that matters, and the fixture
now drives the legal sequence: the manager records `running`, the port writes,
the port's own `runs_after` records the stop, and a case asserts the state seen
at the moment the model finished was `running`.

### [P1] A test that never touches the target proves nothing about it

The model wrote only `result.json`, so a "clean import" marked an entry
integrated and released its lease when no candidate byte had moved --
`imported_paths` was prose in an untrusted claim. The port now performs a
bounded transformation against a disposable target; every case snapshots bytes
and modes; success is proved to change exactly the declared path and nothing
else; and refusal, stale evidence and malformed output each leave every byte
and mode where it was. The promised live-grant race is driven too: a third
party blocks the target and recovers the holder while the model finishes, and
the settlement refuses.

**One boundary that correction made explicit rather than closed**, recorded
because it is real: this seam CANNOT tell whether the model imported what it
claims. The coordinator records the runtime's account, and proving that account
against the target is the verification the model performs under its own Work
instructions -- which is why the settlement's `verification` member is the
model's and core invents none. A case says so plainly rather than leaving the
gap to be discovered.

### Verification

    PYTHONPATH=src:. python3 -m unittest tests.integration.test_execution \
        tests.integration.test_admission tests.integration.test_runtime \
        tests.integration.test_coordinator
    -> Ran 341 tests, OK (skipped=1)

Broad sweep, both phases:

    -> parallel source: 582 shards, 4063 tests, 6 failures, 0 errors, 4 skipped
    -> serial source: 16 shards, 235 tests, 4 failures, 13 skipped

4298 tests, 10 failures, byte-identical to the recorded baseline. The
whitespace and registry gates pass.

`admission.py` changed in this round -- the resolution is factored out of
`admit_candidate` with no behaviour change, and its 15 cases still pass
untouched. That module is W101491's; the extraction is K's shared-boundary
change and is named here so it is not mistaken for the tuner's.

## 2026-09-06 — baton.claude — the re-review: an interval needs both its edges

`review-2026-09-06T15-03-04Z.md` accepted the execution-time re-resolution and
the corrected fixture, and found two [P0]s and two [P1]s. All four are
corrected. 46 focused cases for this leaf (39 before), 349 across the
integration package.

### [P0] A proof that takes time needs a cutpoint at both its edges

The grant was proved when the assignment was composed and again after the model
answered, and between them sat a cross-store producer proof. The reviewer ended
and abandoned the lease from inside that proof and watched the port write
anyway; the completion cutpoint then refused, after the target had moved.

The grant is now re-read immediately before the port receives writable work.
Two cutpoints, two races -- "did it end while I was proving" and "did it end
while the model ran" -- and neither substitutes for the other. Both are driven,
including the reviewer's exact interleaving from the Authority callback.

### [P0] A writer interval needs a START, not just an end

Refusing only `quiescent` and `destroyed` let five states through, and none of
them says no runtime is writing: `start-requested` and `running` have one,
`cancel-requested` and `stopping` are taking one down, and `uncertain` is the
state the manager's own table will not let become `destroyed` because nobody
looked successfully. `not-started` is the ONE state this assembly asks a port
in, and every other state is driven as a negative with the port untouched and
the target unchanged.

**"Not terminal before, terminal after" bounds nothing**, which is the general
form of what I got wrong twice in this leaf. It also makes
`materialize_delivery`'s contract realizable rather than nominal: the fixed
namespaces exist before the runtime that will mount them, because there is no
runtime yet. A case watches from inside the port's own start transition and
asserts both the delivery and the published assignment are already there.

### [P1] An ordinary staleness has a verb, and this record already ruled it

Raising left the entry `leased` behind a live lease -- fail-closed, and turning
an ordinary stale candidate into manual recovery while rank two waited. The
targeted review of 2026-09-05 had ruled it: an ordinary policy, scope or target
failure found before mutation terminally refuses THAT entry and the queue moves
on. The split is made on the coordinator's OWN refusal category, so the two
branches cannot drift from the vocabulary that defines them, and both are
driven.

**One operational consequence I did not expect and have recorded**: an attempt
recorded for an integration that refuses before starting still has to be
RECONCILED by the manager. The next grant's predecessor is that attempt, and
`target_access` proves a predecessor stopped; an attempt whose port was never
asked has no runtime, and saying so is the manager's own
`not-started -> destroyed` transition. This assembly does not perform it -- that
is the deployment's reconciliation -- but a deployment that omits it wedges the
target's next grant, so the case that proves the queue moves on performs it
explicitly and says why.

### [P1] A verification the model did not derive is not evidence

The fake's verification was a constant, so my case checked the target
independently while the recorded account said nothing about it. The model now
reads back the bytes and mode it wrote, the persisted verification is compared
with those exact facts, and every imported path's mode is asserted against one
an importer ESTABLISHED -- with a case under a restrictive umask, because
`open(..., "wb")` takes whatever the umask leaves. The core limitation is
unchanged and still stated in its own case: this is the model's account, and
core invents no verification of its own.

### Verification

    PYTHONPATH=src:. python3 -m unittest tests.integration.test_execution \
        tests.integration.test_admission tests.integration.test_runtime \
        tests.integration.test_coordinator
    -> Ran 349 tests, OK (skipped=1)

Both reviewer reproductions, run from the repository root as the review ran
them:

    PYTHONPATH=v12/python/src:. python3 /tmp/w101492_grant_gap.py
    refusal: denied ... a grant is proved live at the moment it is used
    model asked: []   target changed: False

    PYTHONPATH=v12/python/src:. python3 /tmp/w101492_runtime_gap.py
    refusal: denied the runtime of attempt 'attempt-1' is 'uncertain' ...
    model asked: []   target changed: False

Broad sweep, both phases:

    -> parallel source: 583 shards, 4071 tests, 6 failures, 0 errors, 4 skipped
    -> serial source: 16 shards, 235 tests, 4 failures, 13 skipped

4306 tests, 10 failures, byte-identical to the recorded baseline. The
whitespace and registry gates pass.

One tidy-up in the same round: `test_execution.py` carried its constants block
twice, from my own restore script re-inserting a block that had already landed.
There is one now.
