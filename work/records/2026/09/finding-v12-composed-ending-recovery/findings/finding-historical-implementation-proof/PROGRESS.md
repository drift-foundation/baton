# Progress

## 2026-09-08 — baton.claude, claim 120511

### Revalidation before editing (PLAN step 1)

Read this dossier, the parent FINDING/PLAN, `../../review-2026-09-08T15-46-16Z.md`
and the retained `../../evidence/review-120378-probe.{py,json}`, plus the
approved CONSUMER-RECOVERY-PLAN-2026-09-08.md.

**Both owned paths were byte-identical to the reviewed candidate** at claim
time, so the review's source anchors held without re-deriving. Both [P1]
reproductions were confirmed from the reviewer's own probe output: a resumed
ending answered successfully with `cleanup_operations: []` — no
`runtime.destroy` in the store at all — and again with `published: []`.

**Both diagnoses are accepted.** `_let_go` asked the mutable `cleanup` column,
and a column is not the act that moved it; `_resumed_implementation` took any
non-`None` publication answer, so the one member a resume cannot re-derive from
this manager's own custody was also the one member nothing checked. The
reviewer is also right that my 19 added cases could not have caught either:
they mock the retained readers and set the axes by hand, which can prove which
operands a resume refuses and cannot prove that a real ending leaves what a
resume reads.

**Public-owner survey before editing**, because the correction needed one that
proves a committed cleanup:

- `authorize_cleanup(store, port, adapter, ...)` derives this attempt's destroy
  identity and REPLAYS it before it reads anything mutable, before the adapter
  and before the Authority — and that replay compares the journalled signature
  against one freshly derived from the attempt, its fixed assignment, its
  runtime, the intake receipt digest and the retention policy. It is the
  accepted public owner of the fact and it brings the whole cross-binding with
  it. **Used.**
- `review_cycles._cleaned_review` is the precedent the FINDING names. Its
  private signature reconstruction is deliberately NOT copied: the owner
  already performs it inside the replay, and duplicating it is what that
  instruction forbids.
- `intake.destroy_operation` is exported but takes the persisted attempt ROW,
  and no public reader answers one. See the residual below.
- `load_manifest(store, digest, "proposalManifest")` is the accepted public
  read of a retained proposal. **Used** as the durable publication evidence.

### What was corrected, in `review_driver.py`

**`_let_go` proves the committed act, not the axis.** It now reads the axis
only as a GUARD — a cleanup that is not already positively settled refuses
before the owner is asked, because `authorize_cleanup` reads the live
assignment when it finds no committed destroy and a resume may perform no
Authority act — and then asks `authorize_cleanup` for the replay. The answer is
owned as a closed `CLEANUP_RECEIPT` document and required to name this attempt,
`state = absent`, the same cleanup ending the axis reports, exactly the
artifacts this ending's retention decisions kept, and directory custody for
both roots.

**`_retained` also answers the retention decisions**, because the committed
cleanup receipt names what it KEPT and the only honest thing to compare that
against is the retention this same read just proved.

**`_published` reads the retained manifest.** The seam answers a closed
`PUBLISHED_MEMBERS` document of three SELECTORS — attempt, proposal, retained
manifest digest — and every fact is then read back out of the
`proposalManifest` those selectors point at. That manifest must name this
attempt's fixed assignment, this ending's frozen result and that result's own
manifest digest. A deployment keeping publications in a list answers a shape
this accepts and then fails the read, which is the correct outcome: an
in-memory record says nothing about a process that has since died.

**Order.** `HISTORICAL_IMPLEMENTATION_ENDING` is now
`("correlate", "intake", "retain", "cleanup", "checkpoint", "publish")` — the
cleanup proof moved after the custody it keeps, for the reason above.

**Unchanged:** the ordinary implementation ending, the review resume's trigger,
order and refusal wording, `PUBLICATION_SEAM == ("publish",)`, and every
existing assertion.

### What was corrected in `test_review_driver.py`

**The 101 baseline cases remain an unchanged prefix**, verified byte-for-byte
against `HEAD` (2754 lines, sha256 prefix `cb376576b1100976`). 131 test methods
now, from 101.

**The mock-seam class is re-scoped, not deleted.** The review says those
controls "remain useful but cannot substitute" for the real proof, so
`TheImplementationEndingIsReenterableAfterItsCleanup` became
`TheResumeRefusesBeforeItReachesCommittedEvidence` and keeps only the cases it
can honestly reach — which operands a resume refuses, and that it spends
nothing doing so. Seven cases that claimed a positive lifecycle, a checkpoint
replay or a publication over mocked readers were REMOVED from it and are
re-proved below against real records. Removing my own unaccepted cases rather
than leaving them asserting a contract the correction changed is the point of
the handback.

**`TheImplementationResumeReadsRealCommittedCustody` is the required proof.**
One implementation attempt is registered through the real offer/claim/
activation owners, started over a real workspace, given real files, and ended
by the ACTUAL `review_driver.end_implementation` over a real file custodian —
so the freeze, terminal correlation, intake receipt, retention decisions,
committed `runtime.destroy` with its directory custody, frozen checkpoint and
retained proposal manifest are all produced by the ordinary path. The control
store is then CLOSED and REOPENED under a second incarnation, so the resume
runs in a handle that performed none of it.

Positive: the ordinary ending leaves every record (measured at each owner,
including exactly one committed `runtime.destroy` and a retained proposal
manifest); a reopened manager finishes from those records with the same
document; resuming twice more changes nothing; the line, its writer and its
checkpoint are untouched. Negative, each against the same real records with one
altered: a cleanup axis with no committed destroy, a destroy committed for
another runtime, each unsettled cleanup ending, a missing or foreign retention,
a partly retained set, a missing intake receipt, a missing frozen result, a
foreign terminal envelope, a missing or foreign current checkpoint, a
publication this manager no longer retains, a history naming another attempt/
proposal/manifest, four malformed history shapes, and a seam with no replay
half. Every one asserts no adapter call, no publish, and no control write.

**Named stand-ins.** The engine and Authority transports are deterministic, as
everywhere in this suite. The proposal manifest is composed by the fixture
rather than by `integration.driver.retain_proposal`: composing one is that
producer's accepted contract, proved in `tests/integration/test_driver.py`, and
it requires a proposal-typed declared output this writer does not declare. What
is under test here is the driver's CORRELATION of a retained manifest, and that
manifest is retained through the accepted public `retain_manifest` and re-read
through the accepted public `load_manifest`.

### Operational finding — one residual, measured rather than described

On a store whose cleanup axis was edited without its journal, the resume
performs **one Authority read** before refusing. `authorize_cleanup` replays
the committed destroy before touching anything mutable, but when there is no
committed destroy to replay it reads the live assignment before refusing
`already-terminal`. Deriving the destroy identity first would need the
persisted attempt ROW: `intake.destroy_operation` is exported and the row it
takes is not, `attempt_runtime_of` answers five members and `assignment_of`
answers the assignment. Neither is enough.

`test_a_cleanup_axis_without_its_committed_destroy_refuses` asserts the
refusal, no adapter call, no publish, no control write, and that the residual
is exactly one `assignment_of` read — so it stays measured rather than assumed.

**Proposed correction, owned by whoever owns `intake.py`:** a public
`cleanup_of(store, attempt_id)` mirroring `gate_discharge_of` — absence when no
destroy committed, the adopted receipt when one did, and a visible refusal for
a present invalid record. The resume would then prove the committed cleanup
with a read and never reach the owner's Authority branch. Reported before
expansion, as this record instructs; not taken.

### Callable seam for W119114

    publication.published_of(attempt_id=...) -> {
        "attempt_id": <this attempt>,
        "proposal_id": <the Authority's proposal identity>,
        "proposal_manifest_digest": <retained proposalManifest digest>,
    } or None

Exactly those three members; extra or missing members refuse. It must be
DERIVED FROM DURABLE STATE, not remembered: `_RetainedPublication` in the test
module is the smallest thing that satisfies it and keeps no cache, which is the
shape `tools/stage_execution.py`'s `Publication` should take
(`retain_proposal` + `load_manifest`, as `StageDeployment.published_proposal`
already does). `PUBLICATION_SEAM` is unchanged, so an ordinary ending needs one
verb still.

The resumed answer's `published` member is the durable history document rather
than the live publish answer. That is the one member the two paths cannot
share: the ordinary ending reports what the Authority answered, and a resume
reports the retained manifest that answer was composed from. Every other member
is equal, and the joined proof asserts it.

### Verification

**Question, commands and budget recorded before execution.** The question: does
an actual ordinary implementation ending leave the committed cleanup,
checkpoint and durable publication evidence a resume needs, does a REOPENED
manager finish from those records with no runtime, worker, Authority or
publication act and no control write, and does each missing/foreign/malformed
piece refuse? No retained evidence could answer it — the reviewer's finding is
that no such proof existed. Budget: the new real-custody class, then the driver
module, then the Job-manager and consumer modules that reach this driver, about
30 seconds.

    PYTHONPATH=src:tests:. python3 -m unittest \
        tests.job_manager.test_review_driver.TheImplementationResumeReadsRealCommittedCustody
    -> Ran 18 tests, OK
    PYTHONPATH=src:tests:. python3 -m unittest tests.job_manager.test_review_driver
    -> Ran 131 tests in 3.7s, OK
    PYTHONPATH=src:tests:. python3 -m unittest \
        tests.job_manager.test_ending tests.job_manager.test_sweep \
        tests.job_manager.test_exchange tests.job_manager.test_status \
        tests.job_manager.test_scheduling tests.job_manager.test_recovery \
        tests.job_manager.test_restart tests.job_manager.test_launch \
        tests.job_manager.test_delegation tests.job_manager.test_tool \
        tests.integration.test_driver tests.tools.test_stage_execution
    -> Ran 469 tests in 6.7s, OK

No broad sweep: the canonical parallel gate is still not runnable (the registry
line remains allocated to W119114) and repeating the 5099-test sweep would
answer no question this correction raises. `tests.tools.test_stage_execution`
is included because it is the consumer of this driver, and
`tests.integration.test_driver` because the publication evidence this
correction reads is that module's.

### Candidate bytes and modes

    5d6bd47c05f34d4e819d13e3e1c12998156e73105553760240c584f7d951a1c2  664  v12/python/src/baton_v12/job_manager/review_driver.py
    a0baa47fdcca55477f89e72c94c6261c8d8d2adab62d74781b0065b92a036ade  664  v12/python/tests/job_manager/test_review_driver.py

Exactly the two owned paths. `ending.py`, `projection.py`, `manager.py` and
`test_ending.py` are untouched by this claim and remain W120424's. No Git
operation of any kind was performed.

### State

Awaiting independent review at `baton.bug`. This claim corrects the historical
implementation resume only. W119733 retains the joined six-path acceptance,
W119114 still owes the assembled lifecycle and the registry line, and sibling
W120424 is unaffected.

## 2026-09-08 — baton.claude, claim 121164 (correction)

### Question and budget, before running

Do the composed provider readers close [P1] custody, [P1] publication, [P2]
Authority and [P2] discard; does the resume now recover after the line has
moved on; and do the seven restored cases and every existing assertion hold?
Retained evidence cannot answer it — the providers did not exist when it was
taken. Budget: about 30s — the driver module, then the Job-manager and
consumer modules that reach it.

### Corrected

**[P1] and [P2] cleanup.** `_let_go` now asks `intake.cleanup_of`, which takes
no port and no adapter — so the measured Authority read is gone, not reported.
That reader also owns the nested directory custody against
`historical_directory_custody`, re-derives the ending from `_settle`'s own
facts, and compares `kept` against `KEEPS_MATERIAL`, so a real discard resumes
and this module keeps no second account of those rules.

**[P1] publication.** `_published` reads the record `publish_candidate` commits
only after its publish and exact readback succeed, through the seam
(`PUBLISHED_MEMBERS` is now that record). The driver checks only the half a
provider cannot: that the record is about this attempt, this frozen result and
this assignment. A retained-but-unpublished proposal no longer satisfies it.

**Later line movement.** `_frozen_checkpoint` no longer reads the line's
mutable `current_checkpoint_id`. `freeze_checkpoint` selects by `writer_id`, so
it finds this writer's checkpoint whatever the line has since done; and for a
destroyed runtime it either replays the frozen record or refuses at
`_quiescent_completed` — before the participant comparison and long before any
fence — so the zero-Authority contract holds by the owner's ordering rather
than by a guard here.

**The seven removed cases are restored** by their original names, over the real
custody that makes them honest. Two are driven differently and say so:
`test_a_checkpoint_that_is_not_this_writers_frozen_one_refuses` now removes the
writer's own committed freeze rather than the line pointer, because that
pointer dependency is what the review required removing.

### Verified

139 driver tests OK (101 baseline prefix byte-identical to `HEAD`, verified);
587 OK across the driver, ending, sweep, status, integration-driver,
stage-execution and intake modules. The fixture now declares a proposal-typed
output carrying the worker's own claim, so `retain_proposal`,
`publish_candidate` and `publication_of` are the real owners rather than
manufactured evidence. Commands, hashes and fixture limits:
`evidence/correction-121164.json`.

### Limitations

The engine and Authority transports remain deterministic, as everywhere in this
suite; `LinePublisher` is the named publisher transport stand-in. The seam
keeps the retained-proposal SELECTOR to avoid writing during a read — the
evidence is the committed record, not the cache — and a control empties it
after reopening and proves the durable derivation still answers.

### Next

Independent acceptance at baton.bug; parent W119733 then assesses the joined
six-path provider.

## 2026-09-08 — baton.claude, claim 121851 (correction)

### Question and budget, before running

Does a cold manager AND a cold seam recover with every publisher method and
`retain_proposal` forbidden and SQLite denying writes; do the restored selector
controls refuse at the seam; do the two paths now answer identical documents;
and does recovery survive an actual later round? Retained evidence cannot
answer it — W121793 did not exist and the seam kept a cache. Budget: about 30s,
the driver module then the affected Job-manager, integration and consumer
modules.

### Corrected

**[P1] cold selector.** The seam's `published_of` now calls W121793's
`publication_for_attempt`, so it remembers nothing and asks no publisher.
`test_a_cold_manager_and_a_cold_seam_recover_the_ending` reconstructs the seam
as well as the store; `no_remote` forbids `publish`, `proposal`,
`canonical_target` and `retain_proposal` by name, and `denied_writes` installs
a SQLite authorizer that DENIES insert, update and delete — so a write fails
inside the driver rather than being counted afterwards. A companion case
advances the Authority target first, which previously refused precondition.

**[P1] seam selectors.** `_published` now reads the retained proposal manifest
back and correlates `proposal_id`, `result_id`, `result_manifest_digest` and
the assignment against it, then checks the nested Authority answer's own four.
The two removed negatives and the missing-proposal-manifest control are
restored, plus a control for an answer naming another proposal.

**[P2] return value.** The resume answers the validated ordinary answer, and
the reopened case now asserts the COMPLETE documents are equal rather than
selected members. My earlier claim that the two paths could not share this
member is superseded: the committed receipt carries it.

**Later-round proof.** `test_a_real_later_round_does_not_strand_the_earlier_ending`
attaches an independent reviewer, records a changes-requested verdict, grants
the correction writer and freezes its checkpoint through the public owners —
the line reaches revision two holding another writer's checkpoint — and then
recovers the first ending. The pointer-corruption control is kept beside it.

### Verified

141 driver tests OK, baseline prefix byte-identical; 552 OK across the driver,
ending, integration-driver, stage-execution and intake modules. Hashes,
commands and the ledger correction: `evidence/correction-121851.json`.

### Ledger correction

`evidence/correction-121164.json` recorded 13.3s as the total beside 4.2s and
13.1s runs. Those total 17.3s; the 13.3s figure was the second run alone,
mislabelled. Corrected here by append rather than by rewriting that file.

### Next

Independent acceptance at baton.bug; parent W119733 then assesses the joined
six-path provider.

## 2026-09-08 — baton.claude, claim 121912 (correction)

### Question and budget, before running

Do the four proposal-fixed facts and both assignment accounts now refuse a
contradictory seam answer, and do the two restored controls hold? Budget: about
20s — the driver module, then the integration-driver and stage-execution
modules that reach this seam.

### Corrected

**[P1].** `_published` reads the four facts the retained proposal FIXES —
`proposal_head.hex`, `target_revision.hex`, `input_manifest_digest`,
`policy_digest` — through `_proposal_facts`, and compares them against the
receipt's `candidate_digest`/`target` and the answer's four. They come from the
manifest, never from another seam member, so no unverified value certifies
another. Additional Authority metadata is still preserved: the answer is not
held to a closed member set.

**[P2].** `_typed_assignment` proves the member types on both accounts before
any equality, reusing `boundaries.generation`, whose contract already excludes
`bool`. W120763 closed this inside its owner; this is the distinct seam.

**Restored.** `test_a_publication_this_manager_no_longer_retains_refuses`
deletes the retained proposal manifest, with the owning-reader diagnostic the
ruling permits. `test_the_publication_selector_is_derivable_after_reopening`
keeps its prior assertion — the same digest re-derived in a process that
remembers nothing — now through W121793's local reader, and resumes afterwards.

### Verified

145 driver tests OK (141 plus 4), baseline prefix byte-identical; 359 OK across
the driver, integration-driver and stage-execution modules. Hashes, commands and
budget: `evidence/correction-121912.json`.

### Ledger

The 13.4s in `correction-121851.json` was reported beside a 13.3s second run;
the first run's elapsed time was not retained, so no cumulative figure can be
reconstructed. Stated rather than estimated, and no rerun performed. This
claim's runs are 4.6s and 10.7s, 15.3s cumulative.

### Next

Independent acceptance at baton.bug; W119733 remains gated on it.
