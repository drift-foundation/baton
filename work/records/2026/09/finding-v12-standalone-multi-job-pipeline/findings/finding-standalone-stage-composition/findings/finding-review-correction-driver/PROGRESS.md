# Progress

Not started.

## 2026-09-06 — baton.claude — the act, the driver, and two identities

Claimed W103076 and implemented both halves. New
`src/baton_v12/job_manager/review_driver.py` and
`tests/job_manager/test_review_driver.py`; `episodes.py` gains the correction
act; `documents.py` gains `CORRECTION_ENDINGS`, the `stage.correction`
contract and one `stage.status` member; `projection.py` exposes the round
count and its stale `changes-requested is terminal` paragraph is corrected.
`schema.py` is UNCHANGED and deliberately so -- `episodes.ended_state` has no
value constraint, so a correction ending needs no migration, and versioning a
schema that did not change was a defect this record has caught before.

### The correction act

One transaction, one journal row: both of a Job's live episodes end with
`superseded-by-correction` and both successors open. It does not compose
`end_episode` and `open_next`, because those are four separately journalled
operations and every window between them is a durable state this control plane
cannot describe -- a stage with no live episode that no ending made
replaceable, or one Job with its implementation on round two and its review
still holding round one's verdict.

`CORRECTION_ENDINGS` is a SEPARATE set from `EPISODE_ENDINGS` rather than a new
member of it. `manager.py` asserts that `EPISODE_ENDINGS` is exactly the
Worker Manager's offer vocabulary minus `claimed`, and that assert is right:
every one of those endings is something that happened to an OFFER. A correction
is not. Nothing in `test_recovery.py` needed changing as a result.

### What my own tests refused, twice

The operation identity was wrong in two different ways before it was right, and
both are in FINDING as rules rather than fixes: an identity derived from state
the act itself moves is not an identity, and a signature is the authorization
rather than the outcome. The first spelling made an exact retry open a THIRD
round; the second let any other verdict identity open a second round on the
same checkpoint.

### The driver

Provider-neutral and in `job_manager/` rather than `tools/`: every capability
is an operand, and it opens no store, reads no environment variable, names no
image and chooses no worker. The implementation ending is the accepted
seven-step order with exactly one substitution -- where `single_worker` passes
the frozen result to a v11 review Route, this asks the publication seam and
then fences the writer into an immutable checkpoint. The seam is asked while
the line is still `writing`, which a case asserts by recording the line's own
state from inside the seam.

`end_review` answers `accepted`, `correction` or `held`, and `held` is a real
answer: a rejected checkpoint is a decision about the Work, and neither it nor
an ambiguous one is a round this driver may schedule.

### Verification

    PYTHONPATH=src:. python3 -m unittest tests.job_manager.test_review_driver
    -> Ran 24 tests, OK

    PYTHONPATH=src:. python3 -m unittest discover -s tests/job_manager -t .
    -> Ran 362 tests, OK

    PYTHONPATH=src:. python3 -m unittest tests.manager.test_review_cycles
    -> Ran 17 tests, OK

The broad parallel gate CANNOT run yet, and the refusal is correct:

    [runner] refused: these test modules belong to no registry ...
    ['tests.integration.test_driver', 'tests.job_manager.test_review_driver']

Registration is W103083's, and both unregistered modules are the two driver
leaves. Reported rather than worked around.

### Named gaps

Not yet driven: a crash between every pair of ending steps, and replay at the
deployment-owned freeze/intake/retention/cleanup cutpoints. This suite fakes
those four because they need an OCI adapter, a delivered workspace and a
custody root -- the deployment half W103083 owns and `tests/manager` already
drives. What is real here is the custody provider, the fence, the verdict and
the Job store.

## 2026-09-06 — baton.claude — the re-review: four receivers, one mistake

`review-2026-09-06T17-07-11Z.md` found three [P0]s and one [P1]. All four are
corrected, and FINDING records the single rule behind them: the composite
believed its caller. 39 focused cases for this leaf (24 before), 377 across
`tests/job_manager`.

### What changed

- `advance_correction` takes `job_id` and reads the Job's two stages from this
  store. A caller cannot cross-wire what it does not choose.
- It takes the recorded verdict DOCUMENT and proves it against the owner's
  committed operation through `ControlStore.operation_record`, then ties it to
  the same line and checkpoint the line proof used.
- The allocation precondition is repeated inside the transaction that relies
  on it.
- `end_implementation` binds the writer row to this attempt and generation
  before the first external act; `end_review` no longer takes an attempt at
  all and derives it from the attachment's committed record.
- Every adapter verb and the port's participant are proved before anything
  external happens, and a malformed stop answer refuses.
- The contract's `held` branch exists, split on refusal category.

### Regressions added

First-round bogus verdict, a verdict naming an unrecorded attachment, an
accepted verdict document, a Job that is not a pair, a real two-Work
submission, a reservation committed at the cutpoint, a writer belonging to
another attempt, a stale generation, an adapter missing a verb, a port with no
participant, a non-document stop answer, an unrecorded attachment, a
caller-malformed disposition, and three held-branch cases. Every ending
refusal asserts the adapter was never asked to stop.

### Verification

    PYTHONPATH=src:. python3 -m unittest tests.job_manager.test_review_driver
    -> Ran 39 tests, OK

    PYTHONPATH=src:. python3 -m unittest discover -s tests/job_manager -t .
    -> Ran 377 tests, OK

    PYTHONPATH=src:. python3 -m unittest tests.manager.test_review_cycles
    -> Ran 17 tests, OK

The whitespace gate passes. The broad gate still refuses for the two
unregistered driver modules, which is W103083's registration.

### An operational finding about a concurrent leaf, reported not fixed

`tests/integration` was 375 OK earlier in this round and is now 378 collected
with 97 errors, all of them `grant_lease() missing 1 required keyword-only
argument: entry_id` -- 85 in `tests.integration.test_runtime` and 12 in
`tests.integration.test_recovery`. `integration/queue.py` is W103077's
concurrent working tree and `grant_lease` has gained a required operand;
`test_runtime` belongs to W101490 and `test_recovery` to W101493, both accepted
and closed. Nothing of mine touches `baton_v12.integration`. Reported here and
on the thread rather than worked around.

## 2026-09-06 — baton.claude — the second re-review

`review-2026-09-06T17-23-54Z.md` found two [P0]s and two [P1]s; all four are
corrected. 45 focused cases for this leaf (39 before), 383 across
`tests/job_manager`, 24 in `tests/manager/test_review_cycles` (17 before).

### What changed

- **Typed readers at the owner.** `review_cycles.review_of` and
  `review_cycles.verdict_of`, each cross-binding a materialized row against
  the committed act that wrote it. `episodes` and `review_driver` consume
  those documents and no longer know any of this provider's operation kinds,
  identities or journal shapes.
- **`_verdict_row` extracted**, so `checkpoint_verdicts` is adopted in exactly
  one place. The boundary inventory is what required this, correctly.
- **The correction is both-or-neither under the lock.** Every guard runs
  before the first row moves, and the guards raise ORDINARY refusals so a
  savepoint unwinds rather than being sealed by `transact`'s durable-refusal
  path.
- **The ending preflight is the whole surface**: eight adapter verbs, the
  custodian identity, both port verbs, the port's participant COMPARED with
  the attempt's assignment, and the profile surface each ending uses.
- **`ambiguous` is held**, as the confirmed contract pins.

### Shared gate files touched, and why each was forced

Adding two authorized public readers made four shared gates fail, and each one
is a real declaration rather than an expectation loosened:

- `tests/manager/test_dependencies.py`: `verdict_id` declared as a supplied
  durable operand beside `line_id`, `checkpoint_id` and `attachment_id`.
- `tests/manager/test_boundary_inventory.py`: the `checkpoint_verdicts`
  adoption site moved from `integration_checkpoint` to `_verdict_row`, its
  lookup key declared NO_PROBE, and the probe branch extended.
- `tests/manager/test_secrets.py` and `tests/manager/test_text_sweep.py`: the
  two new exports classified and driven.

Neither reader appears in any remaining failure of those gates.

### Verification

    PYTHONPATH=src:. python3 -m unittest tests.job_manager.test_review_driver
    -> Ran 45 tests, OK

    PYTHONPATH=src:. python3 -m unittest discover -s tests/job_manager -t .
    -> Ran 383 tests, OK

    PYTHONPATH=src:. python3 -m unittest discover -s tests/manager -t .
    -> Ran 2621 tests, 9 failures

Those nine are five recorded-baseline `test_boundary_inventory` cases and four
SERIAL-registry daemon suites (`test_credentials_engine`,
`test_output_custody_engine`, `test_worker_container` x2) that a parallel
discovery is not the right way to run. Nothing of mine appears in any of them.
The whitespace gate passes.

The broad runner still refuses for the two unregistered driver modules, which
is W103083's registration, and `tests/integration` remains broken by W103077's
concurrent `grant_lease` signature change as reported last round.

## 2026-09-06 — baton.claude — the third re-review

`review-2026-09-06T17-50-59Z.md` found two more; both are corrected. 49 focused
cases for this leaf (45 before), 387 across `tests/job_manager`, 29 in
`tests/manager/test_review_cycles` (24 before).

### What changed

- `_committed_operands` reads the OPERANDS a committed act was authorized
  with, from the signature this module built, rather than the result the act
  chose to return. `_bound_to_act` compares a row's immutable members against
  them and refuses a disagreement rather than reconciling it.
- `review_of` binds the attachment's attempt, generation, reviewer worker,
  participant and principal, and proves the row's line is its checkpoint's
  line -- the one member no act named.
- `verdict_of` binds all nineteen immutable members, parses the retained
  `review_result` and `review_fence` through `_review_result` and `_fence`,
  and recomputes both digests.
- Both endings own the custodian identity as TEXT and the profile's name, and
  compare that name with the line resolved from the OWNER-BOUND writer or
  attachment before the first stop.

### Regressions added

The reviewer's two exact reproductions -- a rewritten `runtime_attempt_id` and
a rewritten `review_result_digest` -- plus member-by-member corruption over
four attachment columns and eight verdict columns, a rewritten review fence
digest, a malformed custodian identity on both endings, and a valid
wrong-profile on both endings. Every driver negative asserts zero stop calls.

### Verification

    tests.job_manager.test_review_driver          -> 49 OK
    discover -s tests/job_manager                 -> 387 OK
    tests.manager.test_review_cycles              -> 29 OK
    test_dependencies + test_secrets + test_text_sweep -> 115 OK, 1 skip
    discover -s tests/manager                     -> 2626, 9 failures

Those nine are the five recorded-baseline `test_boundary_inventory` cases and
four SERIAL-registry daemon suites a parallel discovery should not run; no
W103076 name appears in any of them. The whitespace gate passes.

No shared gate file was touched this round: the four the reviewer authorized
are unchanged since the scope decision, and the only test path edited besides
this leaf's own is `tests/manager/test_review_cycles.py`, which the readers'
authorization already covers.
