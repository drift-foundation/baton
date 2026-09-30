# PROGRESS — W316918, claim 317016, baton.claude

Implementer progress for "V12: Release final reviewer allocation after proven
completion". FINDING.md and PLAN.md are reviewer-owned and were not edited.

## What the residual was, established before anything was written

I reproduced it deterministically over the real composed runtime before
forming any hypothesis, with a temporary probe class in
`tests/tools/test_stage_execution.py` (since removed and replaced by the
acceptance suite below). Driving one Job through a real implementation turn,
a real reviewer container and an accepted verdict, then ticking:

```
AFTER REVIEW TURN {'implementation': 'completed', 'review': 'answering', ...}
  allocations: [('implementation', 'released', ..., 'cleanup-retained'),
                ('review', 'reserved', None, None)]
tick 1 {'implementation': 'completed', 'review': 'completed', ...}
  allocations: [('implementation', 'released', ...),
                ('review', 'reserved', None, None)]      <-- completed, still held
tick 2 {'implementation': 'completed', 'review': 'completed', ...}
  allocations: [..., ('review', 'released', ..., 'cleanup-retained')]
```

That is the deployed shape exactly: implementation released at 15:18:51.356
with `cleanup-retained`, review reserved at 15:18:51.362 with `released_at`
null.

**The cause.** `manager.sweep` reconciled scheduler capacity from a `held`
projection taken *before* its own acts. The cleanup axis becomes terminal
*inside* `conclude` — the ending freezes the result, takes the intake receipt
and authorizes cleanup — so the release was owed to a tick that had already
looked, and landed on the next one. For every stage but the last that is a
one-tick delay nobody sees. For the last stage of a Job there is no next tick:
a supervisor stops once its stages are completed, and it stops *between* the
completion and the release. The allocation then stays `reserved` for the life
of the store.

`scheduler.reconcile_allocations` itself was never wrong, and I did not change
it. Given a projection whose cleanup axis is terminal it releases the exact
allocation with the right reason, and `test_scheduling` already pins that rule
from both sides. What was wrong was *when* it was asked.

**Not conflated with the workspace token.** The workspace was retained and is
still on disk; the release reason says `cleanup-retained` and claims nothing
about the container, the credential or the workspace. An acceptance case
asserts the retained workspace directory still exists after the release.

## The correction

`v12/python/src/baton_v12/job_manager/manager.py` — one added call at the end
of `sweep`, after `_recover_endings`:

```python
scheduler.reconcile_allocations(
    store, projection.stage_states(store, operations))
```

- It adds no rule and weakens no hold: same function, same release endings,
  same `complete`/`retained`-with-no-blocker test, same holds for running,
  unknown and unsettled cleanup.
- It is idempotent by construction — the loop only considers `LIVE_STATES`, so
  an allocation this tick already released is skipped, and `_move` answers the
  settled row rather than recording a second release.
- **The sweep report did not change.** Its contract is closed
  (`documents.CONTRACTS["sweep"]`), and a release is already visible where a
  reader looks: the allocation's own `allocation_state`, `released_at` and
  `release_reason`, which is what a status document carries. An acceptance
  case asserts the report's member set is unchanged.

No other product file was touched. No scheduling redesign, no change to
`scheduler.py`, `stage_execution.py`, `single_worker.py` or the supervisor
stopping boundary.

## Ownership

| Path | Owner | What |
| --- | --- | --- |
| `v12/python/src/baton_v12/job_manager/manager.py` | **W316918** | the one added reconciliation |
| `v12/python/tests/job_manager/test_final_allocation_release.py` | **W316918** (new file) | 14 sweep-level cases |
| `v12/python/tests/tools/test_stage_execution.py` | **W316918** for `TheLastStageReturnsItsCapacityWhenItCompletes` only | 10 runtime-level cases |
| `v12/python/tools/parallel_test.py` | **W316918** for the one appended registry entry | registers the new module |
| `FINDING.md`, `PLAN.md` | reviewer | not edited |

`tests/tools/test_stage_execution.py` also holds my accepted W236087 classes
(`TheFAILEDReviewEndingReadsRetainedFactsOverRealStores`,
`TheFAILEDReviewSettlesDurablyOverTheRuntimeWorld`); neither was edited.

**Coordination with W316915** (V12: Make Job status use genuinely read-only
store openers, passed for review this cycle): no shared path. W316915 owns
`v12/python/tools/job_manager.py` and `v12/python/tests/job_manager/test_tool.py`;
W316918 touches neither. The only file in `tools/` I touched is
`parallel_test.py`, which W316915 does not.

## The acceptance, and why it is split across two levels

**`tests/job_manager/test_final_allocation_release.py` — 14 cases, 0.10s.**
The ordering rule against a fake deployment whose `conclude` settles the
cleanup axis, because that is where the real Worker Manager settles it. A
fixture that set a terminal cleanup *before* the tick would describe the one
state in which this defect cannot appear. One logical worker per lane, so
"did the last stage give its capacity back" and "can another Job run" are the
same question.

- release once, with the settling assignment, its episode, `released_at` and a
  reason matching the cleanup that was proven (`complete` and `retained`)
- a later independent Job's admission takes the freed worker and principal
- its negative: while the finished attempt still holds the only review worker,
  the next Job reserves nothing — which is what the deployed instance would
  have done on its second Job
- released exactly once: three further ticks, a restart on a new incarnation
  over the same store, one `allocation.released` journal row, `released_at`
  never restamped
- a released assignment is never reserved again (durable refusal)
- held: unsettled (`pending`), unknown (`None`) and `running` cleanup
- the hold is not widened either — a live execution axis with a terminal
  cleanup still settles, because the rule reads cleanup and not execution
- `changes-requested` settles on its own cleanup, so the disposition is not
  the axis
- the sweep report's member set is unchanged

**`tests/tools/test_stage_execution.py::TheLastStageReturnsItsCapacityWhenItCompletes`
— 10 cases, 5.3s.** The real composed lifecycle: real containers through the
fake engine, a real reviewer verdict, the real ending, cleanup and settlement.
This is the only level that can prove the thing that made this a residual
rather than a delay — that for the last stage the completing tick is the only
tick there will be. Every case measures **one** tick.

- the tick that moves review `answering → completed` also releases its
  allocation, with `cleanup-retained` and a non-null instant
- at the moment every reader calls the Job completed, no allocation of it is
  live
- the accepted verdict, the sealed result it was read from and the accepted
  integration checkpoint all survive the release, and the Job still drives on
  to `integration: claimed`
- the retained workspace directory is still there
- three further ticks change neither instant nor reason; one journal row
- the implementation allocation is still released on its own tick for its own
  cleanup — a control that would catch a fix which freed capacity early
- **correction-then-accepted**, measured separately because its code path
  differs: a second review episode means one stage carrying two allocations,
  which is exactly where a settlement could name the wrong one. Both episodes
  release, for their own endings, and all four allocations of the corrected
  Job end released.

Borrowed rather than subclassed, on this file's own idiom
(`OrdinaryTerminalLifecycle`): inheriting the composed class would silently
re-run its nine cases under my name.

**A correction to my own first draft.** My `allocations()` helper keyed rows
by stage kind, which collapses a correction round's two allocations of one
stage into one entry — so the two cases about two episodes passed while one
of the two rows was never read. It is a list keyed by assignment now, and
`live()` keeps duplicates. Both cases discriminate after the repair; before
it, one of them passed with the defect present.

## Mutation evidence — `MUTATIONS-317016.json`

Every mutation caught; unmutated and restored runs clean.

| | mutation | caught by |
| --- | --- | --- |
| M1 | the final reconciliation removed again (the defect) | 17 cases |
| M2 | asked with the **pre-act** projection instead of a re-derived one | 17 cases |
| M3 | the release rule widened to treat `pending`/`running`/unknown cleanup as proven | 13 cases |

M2 matters most: it proves the fix is the *re-derived state*, not merely one
more call. M3 targets the rule the new call site invokes and proves the
negative cases really hold capacity rather than passing vacuously.

## Verification actually spent this claim

| suite | tests | seconds | result |
| --- | --- | --- | --- |
| whole `tests/job_manager` | 942 | 11.8 | OK |
| `tests.tools.test_stage_execution` | 477 | 207.0 | OK |
| focused (new + scheduling + sweep + status + integration capacity) | 307 | 2.2 | OK |
| adjacent tools suites (hardening ×2, scheduler_trace, pool, quiescent, correction_restart) | 256 | 66.7 | 2 pre-existing failures, below |
| W236087 dossier (`test_correction_packet`, `test_connected_packet`) | 237 | 29.6 | 1 pre-existing failure, below |
| mutation harness (3 mutations × 2 suites, plus clean and restored) | — | ~42 | all caught |

Live runs: 0. Deployed reads: 0. Deployed cleanup or integration: 0.
Credential changes: 0. Git or graph mutations: 0.

## Findings I am reporting rather than fixing

These three failures all reproduce with my correction disabled, so none is
caused by W316918. None is in a file W316918 owns.

**F1 — `tests.tools.test_single_worker` /
`test_correction_packet.TheCORRECTED_OPERATOR_SEQUENCE.test_THE_STATUS_COMMAND_IS_THE_GENERATED_ONE_AND_THE_PARSER_TAKES_IT`
is a consequence of W316915.** That case builds two **zero-byte** store files
and expects STATUS to answer `jobs: []`. W316915 made `_status` open through
`JobStore.open_readonly`, which refuses an empty database rather than
initializing one:

```
ContractRefusal: the database at '/tmp/status-reader-.../db/jobs.sqlite3' is
empty; a read-only Job store refuses it rather than initializing one
```

The refusal is the behaviour W316915 was selected for and its own 13 cases
pin. The fixture was relying on the fail-open STATUS used to have. The repair
belongs in that dossier's test — initialize the two stores instead of touching
zero-byte files — and I did not make it under this claim, because
`test_correction_packet.py` is W236087's accepted dossier test and W316915 is
under independent review right now. Routing it is the reviewer's call.

**F2 — the parallel-test registry check was already red.** With my new module
registered, `tests.tools.test_parallel_runner.TheRealRegistryDescribesTheRealTree`
still refuses 17 pre-existing tracked modules that belong to no registry:
`tests.job_manager.test_store_readonly`, `tests.manager.test_attempt_logs`,
`tests.manager.test_claude_context`, `tests.manager.test_dogfood_entry`,
`tests.manager.test_fixture_dispatch`, `tests.manager.test_importing_fixture`,
`tests.manager.test_integration_generation`, `tests.manager.test_maintenance`,
`tests.manager.test_proposing_fixture`, `tests.manager.test_provider_context`,
`tests.manager.test_provider_context_delivery`,
`tests.manager.test_w197661_verifier`, `tests.tools.test_accepted_base`,
`tests.tools.test_attempt_logs_command`, `tests.tools.test_correction_restart`,
`tests.tools.test_managed_apply`, `tests.tools.test_pool`. I registered mine so
as not to add to that debt; placing the other 17 needs a decision about what
each owns, which is not this Work's.

**F3 — two adjacent suites fail on signatures unrelated to capacity**, both
identically with my change disabled:
`tests.tools.test_stage_execution_hardening.ConstructionUnwindsConcreteHandles.test_worker_construction_failure_closes_every_acquired_handle`
(expects handles `['coordinator', 'authority']`, gets
`['implementation', 'coordinator', 'authority']`) and
`tests.tools.test_quiescent_assignment_finalization.TheQuiescentAssignmentIsEndedAndNothingElseIs.test_it_takes_no_agent_and_no_runtime_capability`
(expects `['store', 'port', 'attempt_id', 'reason']`, gets two more:
`govern`, `cessation`).

**F4 — `tests/tools/test_managed_preparation.py` and `test_managed_apply.py`
cannot be imported under `PYTHONPATH=src:.`**: they do
`import integration_bundle`, a flat `tools/` module. Adding `tools` to
`PYTHONPATH` shadows the `tests.tools` package and breaks loading instead.
Those two suites are therefore unmeasured this claim; they run through the
parallel runner, which resolves paths per registry entry.

## What is left, and what I deliberately did not do

Nothing in the bound acceptance is outstanding. Not done, and none of it is
implied by the FINDING:

- no live run, no deployed store read, no deployed cleanup or integration
- no change to `scheduler.py`, the supervisor stopping boundary, or any other
  product file
- no new sweep-report member (its contract is closed)
- no repair of the deployed Job's already-reserved allocation; this correction
  changes what a sweep does from now on and does not rewrite history
- no repair of F1–F4
