# Progress

Implementation entries belong to the assigned change author. FINDING.md and
PLAN.md pin event119712 and the exact six-path scope.

## 2026-09-08 — baton.claude, claim 120203

### Revalidation before editing (PLAN step 1)

Read FINDING.md, PLAN.md and the full linked
`baton:work/records/2026/09/finding-v12-standalone-multi-job-pipeline/findings/finding-standalone-stage-composition/findings/finding-composed-one-job-proof/CONSUMER-RECOVERY-PLAN-2026-09-08.md`
before touching source. Revalidated against the current tree:

- **Confirmed.** W119548's accepted interface is present and unchanged at
  `v12/python/src/baton_v12/worker_manager/intake.py`:
  `discharge_quiescence_gate(store, port, *, attempt_id,
  retention_policy_digest)` at line 1307 and `gate_discharge_of(store,
  attempt_id)` at line 1270, both exported from `worker_manager/__init__.py`.
  The replay short-circuit precedes every mutable read, as its record says. No
  drift; nothing in this provider re-derives or re-implements either.
- **Confirmed.** `projection._ending_owed` still returns `False` as soon as the
  Worker Manager's cleanup axis reaches `complete`/`retained`/`failed`, which is
  the exact defect: `authorize_cleanup` is the LAST act of
  `review_driver.end_implementation` and the SECOND-TO-LAST act of a composed
  ending, because the gate discharge and the routing follow it.
- **Confirmed.** `end_implementation` had no destroyed-runtime branch;
  `_quiesced` requires a positively quiescent runtime and `_own_writer` requires
  a writer still `active`, which the ending's own `freeze_checkpoint` revokes.
  So a re-entry after cleanup could not get past line two of the ending.
- **Confirmed.** `_ended_review` already carries a historical branch, triggered
  on `execution_runtime == "destroyed"` alone. Its trigger is deliberately NOT
  changed:
  `test_historical_eligibility_and_replay_require_the_complete_committed_history`
  drives `cleanup = 'pending'` with a destroyed runtime and requires the
  historical path with no adapter call, so narrowing the trigger would have
  broken an existing assertion. The positive-cleanup proof lives inside the new
  implementation branch instead, where nothing downstream proves it.
- **Confirmed.** The six owned paths were byte-unmodified in the working tree at
  claim time; the whole pre-existing diff was in `worker_manager`, `tools` and
  records.

### What was implemented

**New `src/baton_v12/job_manager/ending.py`.** Two journalled records in the
Job store's existing operation journal, under deterministic identities
`ending.intent:<stage_id>:<episode>` and `ending.settled:<stage_id>:<episode>`.
No schema change, no second database, no Worker Manager journal write. Public
surface:

    register_ending(store, attempt, *, assignment, disposition,
                    terminal_manifest_digest, retention_disposition,
                    retention_policy_digest)
    settle_ending(store, attempt, *, assignment, evidence)
    intent_of(store, stage_id, episode)          -> document or None
    settlement_of(store, stage_id, episode)      -> document or None
    ending_of(store, stage_id, episode)          -> {intent, settlement} or None
    pending_endings(store)                       -> [intent, ...]
    attempt_of(store, intent, stage=None)        -> episodes.attempting view

The intent carries the seven immutable selectors (`stage_id`, `job_id`, `kind`,
`episode`, `offer_id`, `attempt_id`, `work_id`), the exact four-part fixed
assignment, and the operands a resume needs: worker disposition, the worker's
completion manifest digest, and both retention operands. The terminal digest is
a SELECTOR, not proof — `review_driver._correlated` still checks it against the
envelope this manager measured. Every selector is compared back against the
stage and episode rows before a record is used, and a present record whose own
journalled signature does not name its bytes refuses
`refused/operation-collision` rather than reading as absence.

**`projection.py`.** `_ending_owed` asks the registered obligation before the
cleanup axis: a registered, unsettled ending is owed however terminal that axis
is and however little of the exchange a reader can see (`exchange: null` +
`cleanup: retained` is exactly what the crash leaves). A stage that registered
none keeps its current semantics unchanged; a SETTLED obligation falls through
to the same generic rules, so a settlement cannot make an unfinished cleanup
look done. `stage_states` reads `ending_of` for the LIVE episode only.

**`manager.py`.** New `_recover_endings` pass, last in `sweep`, driven from
`ending.pending_endings` rather than from `held`: it asks `operations.conclude`
with the view the recorded selectors still bind to, for every pending ending the
`_converse` pass did not already speak for. That covers the case no live-episode
projection can see — `advance_correction` ends the episode that owed the ending
and opens its successor, so the obligation belongs to a stage that has moved on.
Results are reported in the existing `spoken` list as `stage.exchange`
documents, so no document contract changed. Read-only `status` performs no
resume (it never sweeps).

**`review_driver.py`.** `end_implementation` now branches to a new
`_resumed_implementation` when `attempts.attempt_runtime_of` says the runtime is
already `destroyed`, before any operand is proved against a live one. The resume
performs NO adapter call, NO Authority act, NO worker call and NO publication:
it proves the cleanup axis positively settled (`complete`/`retained`), binds the
writer to the attempt and generation WITHOUT requiring it to still hold the line
(`_fenced_writer` — an active writer beside a destroyed runtime is refused),
proves the line's current checkpoint is this writer's own frozen one before
asking `freeze_checkpoint` for its committed replay, reads the retained frozen
result / intake receipt / retention decisions through `_retained`, and READS the
committed proposal evidence through a new seam verb. It answers with the
ordinary ending's document member for member.

The review historical branch keeps its trigger, its order and its refusal
wording; its four custody reads now come from the shared `_retained` so the two
resumes cannot drift apart. Its own `completed`-disposition rule stays in the
review branch, because that is the review's rule and not every ending's.

### Callable interface retained for W119114 (PLAN step 6)

The consumer glue needs exactly these, and nothing else was added:

- `job_manager.ending.register_ending(...)` before the first composed ending
  step that can reach cleanup, and `settle_ending(...)` after the driver
  evidence, the W119548 discharge where the recorded fence owes one, and the
  routing act have all succeeded. `evidence` requires `result_id`,
  `manifest_digest`, `receipt_digest` and optionally accepts `checkpoint_id`,
  `gate_discharge`, `outcome`, `routed`, `verdict_id`.
- `review_driver.end_implementation(...)` is called unchanged; the historical
  resume is selected from durable state, so the consumer supplies no flag.
- **NEW REQUIREMENT ON THE PUBLICATION SEAM.**
  `review_driver.PUBLICATION_HISTORY == ("published_of",)`. A historical resume
  requires `publication.published_of(attempt_id=...)` to answer the committed
  publication document (or `None`, which refuses). It is typed INSIDE the
  historical branch, so `PUBLICATION_SEAM` is unchanged and every existing
  ordinary-ending caller and test is unaffected. This is required because
  `Authority.publish` needs the LIVE producer assignment that this ending's own
  `freeze_checkpoint` already fenced — replaying the publication would refuse an
  act that succeeded, which is what the approved plan means by "read the
  committed proposal evidence". `tools/stage_execution.py`'s `Publication`
  already holds both halves of that read (`retain_proposal` + `load_manifest`,
  and its own `self.published` list), so this is a wiring addition inside
  W119114's own path rather than a new capability. Reported here rather than
  taken on the way past.
- `review_driver.HISTORICAL_IMPLEMENTATION_ENDING` and
  `review_driver.SETTLED_CLEANUP` are exported for the consumer's assertions.

### Verification

**Question, commands and budget recorded before execution.** The question the
runs answer: do the new records, the projection rule and the recovery pass
behave as specified, and does any existing Job-manager assertion change meaning
under them? Existing evidence cannot answer it — none of this code existed.
Planned scope is the approved component budget: the new focused module first,
then the affected Job manager test modules once, about 60 seconds total.

    PYTHONPATH=src:tests:. python3 -m unittest tests.job_manager.test_ending
    PYTHONPATH=src:tests:. python3 -m unittest \
        tests.job_manager.test_sweep tests.job_manager.test_exchange \
        tests.job_manager.test_status tests.job_manager.test_scheduling \
        tests.job_manager.test_recovery tests.job_manager.test_restart \
        tests.job_manager.test_launch tests.job_manager.test_delegation \
        tests.job_manager.test_store tests.job_manager.test_submission \
        tests.job_manager.test_documents tests.job_manager.test_tool
    PYTHONPATH=src:tests:. python3 -m unittest tests.job_manager.test_review_driver

Results are recorded below as each run completes.

#### Focused results (stage one of the two-stage cadence)

    tests.job_manager.test_ending                     29 tests, OK
    12 affected Job manager modules                  338 tests, OK, 0.8s
    tests.job_manager.test_review_driver             120 tests, OK, 3.0s

`test_review_driver` is 120 where it was 101: 17 additive cases in
`TheImplementationEndingIsReenterableAfterItsCleanup` and 2 in
`TheTwoResumesShareOneEvidenceContract`. No existing case was edited, renamed,
removed or weakened; the whole diff to that file is appended after its last
existing line.

What the new cases prove, named rather than counted: the resume answers the
ordinary ending's document member for member with sorted artifacts and the
committed publication; its checkpoint is byte-identical to the one the ordinary
ending froze; two further resumes answer the same and change nothing; the line
and its writer are untouched; a live runtime still gets the ordinary ending
(measured with an adapter whose every verb is a failed assertion); each of
`pending`, `blocked-on-intake` and `failed` cleanup refuses; an active writer
beside a destroyed runtime refuses; a foreign attempt, generation or session
refuses; each missing piece of retained evidence refuses by name; a changed
disposition, retention disposition, policy digest, partly-retained set or
foreign terminal envelope refuses; a missing or unfrozen checkpoint refuses
with no port call; and a seam without its replay half, or one that retains no
publication, refuses. Every refusal path asserts the Authority port's call list
and the control store's `total_changes` are unchanged.

#### Broad relevant regression sweep (stage two)

**The canonical parallel harness could not be used, and that is itself the
finding.** `python3 tools/parallel_test.py --jobs 2` refuses to start:

    [runner] refused: these test modules belong to no registry; add each to the
    parallel or serial list in tools/parallel_test.py after deciding what it
    owns: ['tests.job_manager.test_ending']

That path is W119114's under the approved split, so it was not edited. See the
operational finding appended to FINDING.md for the exact remaining one-line
registration and the alternative if the owner would rather not carry a blocked
gate between the two deliveries.

Question the sweep answers: does any registered non-engine test module change
meaning under these four source changes? The focused runs above cover only the
Job manager, so they cannot. Scope: the 77 modules of `PARALLEL_MODULES`, plus
`tests.job_manager.test_ending`, plus the two non-engine serial modules
(`tests.integration.test_driver`, `tests.job_manager.test_review_driver`). The
engine/daemon serial lane is deliberately excluded: it needs a Docker daemon
this managed turn has no authority to drive, and nothing in this change reaches
it. Budget: one run, reassess at about three minutes.

    PYTHONPATH=src:tests:. python3 -m unittest <77 parallel modules> \
        tests.job_manager.test_ending tests.integration.test_driver \
        tests.job_manager.test_review_driver
    -> Ran 5099 tests in 106.074s
    -> FAILED (failures=25, errors=1, skipped=4)

**Attribution of all 26, and none of them is a Job manager assertion.**

- 1 error — `tests.tools.test_parallel_runner.TheRealRegistryDescribesTheRealTree.test_every_v12_test_module_is_registered_exactly_once`.
  MINE, and it is the registry gap above: it fails precisely because
  `tests/job_manager/test_ending.py` exists and `tools/parallel_test.py` does
  not name it. It goes green with the one line W119114 owns.
- 24 failures — `tests.manager.test_boundary_inventory`, and 1 —
  `tests.manager.test_dependencies`. PRE-EXISTING BASELINE, not this change.
  Every one names a `worker_manager` source (`intake.py`, `output.py`,
  `review_cycles.py`, `oci.py`, `authority_port.py:AuthorityPort:satisfy_gate`)
  and none names a `job_manager` file. Both modules scan `worker_manager` and
  `contracts` only — `test_boundary_inventory.PACKAGE` is
  `worker_manager.__file__`'s directory and
  `test_dependencies.NoPublicOperationTakesInternalState.exported_functions`
  walks `(contracts, worker_manager)` — so neither can observe this Work at
  all. The blocker is already recorded, with a source-hash census, at
  `baton:work/records/2026/08/finding-v12-global-boundary-inventory-debt/findings/finding-lanes-inventory/evidence/census-blocker-120164.json`
  (W116972): "AuthorityPort.satisfy_gate obtains performing through getattr...
  Origin tracking recognizes satisfy_gate.kind, but the independent crossing
  projection lacks satisfy_gate." Recorded as an unrelated failure rather than
  pulled into this correction loop.

#### Candidate bytes and modes (PLAN step 6)

    8da734ac757126ad70cc64556c8568384fa4a6283f0304cc0eaf17a92a1bae16  664  v12/python/src/baton_v12/job_manager/ending.py
    8a15446c04ceec1e43bcafc41e22e87cf0419a4fff78daf03b06ffa47cea8796  664  v12/python/src/baton_v12/job_manager/projection.py
    f77a12f80c66e8dfb9ed700177b90fa4bda841788396304189f00230dfbd9c83  664  v12/python/src/baton_v12/job_manager/manager.py
    2aacdd853b96c03340cb3b7082699aa5106609a61717d3cc2254620d8227eeaf  664  v12/python/src/baton_v12/job_manager/review_driver.py
    a0ca21e92fb5ddf4721dff987ed68e459c874102440fbff1b0cf4e92399f63c7  664  v12/python/tests/job_manager/test_ending.py
    a3d8d28c2b58624c217d41ed4f4d3b0b4cbdf9bd33d9d99c9d52be837d7e9d8c  664  v12/python/tests/job_manager/test_review_driver.py

Exactly the six authorized paths; both new files are ordinary non-executable
mode. No other path in the checkout was changed by this claim, and no Git
operation of any kind was performed.

#### State

Awaiting independent review at `baton.bug`. The composed lifecycle itself is
NOT proved by this Work and is not claimed: the factory, tick, restart,
custody, correction and integration proof remain W119114's, and its consumer
glue is what will exercise the interface recorded above for the first time.
