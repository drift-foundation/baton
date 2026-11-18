# W383215 candidate — installed native Job cancellation and admission fencing

K, 2026-11-18, under the owner's claim (W383215 active, handler slaw, route baton.decide, claimed 19:05:47Z). Base `c9e53b5fb2de65d6deff702c8c04b68dbee45c7e`. Candidate identity `sha256:84518e683dbbd1897aebc23116bef39611adfaf4d4786eea4147e151d32cc24c` over the 25 changed paths in `source.json` / `CANDIDATE-SHA256.txt`; bytes in `candidate.diff`. No Git mutation, no engine, no live provider, no build/install, no full suite.

## Outcome

Installed, instance/Job-addressed, replayable cancellation through the existing owners:

- `manager cancel-job --instance SEL --job JOB --reason TEXT` journals ONE `job.cancel:<job>` request in the Job store (signature over Job + reason: exact replay answers the committed record, another reason collides, unknown Job and blank reason refuse). `requested_at` is stamped by the store inside that commit and never moves: it is the LIM-5 shutdown trigger.
- The request IS the admission fence. Inside the Job store's own write transactions: `scheduler.reserve` (the reserve-before-offer write) refuses, `episodes.open_next` refuses a replacement, `episodes.advance_correction` refuses a correction round, `fresh_attempt._reserved` refuses a successor Job; `fresh_attempt.admit` also refuses after its replay check and before any owner is asked. Read-side guards precede already-computed serving actions: `projection._owed` owes no admit/claim, `PooledManagerOperations.claim` re-reads the fence before `submit_claim`, `manager._launch` re-reads it before `operations.launch` (reports `deferred`).
- The serving sweep carries the request out, level-triggered on each tick's live rows and control-store axes (never on the request-time snapshot): a claimed attempt with no runtime is fenced at the Authority through the composition that would have launched it (`fence_unstarted_attempt` → record + activate as the launch does → `intake.fence_pre_attach_abandonment`); an attached runtime is ordered through `StageExecution.cancel_attempt` → `request_cancellation` (exact-generation Authority fence first, then agent, then runtime stop). Each order is journalled as `job.cancel.target:<digest(authority, job, stage, episode, attempt, effect)>` with the owner's returned identities; it proves an order, never cessation. Refusals are contained per target and reported.
- Reporting is ADDITIVE: `job.status` gains `cancellation` (null when none), STATUS_SCHEMA `/7` → `/8` per documents.py's own convention; no stage state was added and a worker's `cancelled` ending still projects `exceptional`. Per target: `retired-before-admission | awaiting-offer-lapse | pending | fenced-unstarted | ordered | ceased | ended-before-request | held-unknown`; shutdown: `complete | within-bound | unresolved (≥120 s since requested_at without cessation proof) | unknown-time`. `cancel-status` prints the same report read-only. `ceased` is asserted only from the owners' axes (runtime destroyed / cleanup complete or retained) and only for an attempt this request ordered; an ending this request did not order is `ended-before-request` with its outcome untouched.
- Supervisor stop is not cancellation; no second admission ledger; no container is addressed by the command; no manager instance guard and no invocation flock are taken (the Job store journal serialises requests; concurrent serving ticks interleave by SQLite locking).

## Review pins (review-2026-11-18T18-48-35Z) and where each is proved

| pin | implementation | proof |
|---|---|---|
| 1 intent ≠ cessation; preserve ended outcomes; additive status | target states above; `ceased` only from owner axes; `ended-before-request` leaves the stage document byte-identical | `ClaimedAndRunningTargets.test_an_ended_job_keeps_its_outcome_and_nothing_is_ordered`, `test_a_running_stage_is_ordered_to_cease_and_reported_ordered` |
| 2 write-side fences, late targets, offers | reserve/open_next/advance_correction/_reserved under the lock; claim and launch re-read; the pass re-derives targets every tick | `TheWriteSideFences.*` (incl. two-connection cancel-vs-reserve race, correction under lock), `QueuedAndOfferedTargets.*`, command: `test_a_claimed_stage_is_fenced_and_never_started` (late launch refused by the owner, no engine start) |
| 3 identity-bound orders, continued reconciliation | `target_operation_id` binds authority uuid, Job, stage, episode, attempt, effect; the pass asks the owner again while the axis still says running (owner replays) and records one order | `test_the_order_is_level_triggered_and_recorded_once`; command: `test_an_active_runtime_is_ordered_through_the_composition` (one Authority fence, one engine stop, later ticks replay) |
| 4 120 s from the trigger, never reset | `requested_at` immutable; elapsed from it; `unknown-time` when unorderable | `test_the_bound_runs_from_the_request_and_never_resets`; command: pending-without-manager and restart cases keep `requested_at` |
| 5 no successor via fresh attempt | `admit` after replay + `_reserved.act` under the lock | `NoSuccessorThroughAFreshAttempt.*` (cancelled failed Job refused; cancel landing after the preflight refused under the lock; earlier admission intact) |
| 6 binding before writes, no competing guard, concurrency | selector/deployment binding recognised read-only first; writable Job store only for `cancel-job`; no guard/flock | command: `test_a_blank_reason_and_a_foreign_instance_refuse_before_writes`, `test_cancel_status_opens_nothing_writable_and_changes_nothing`, `test_a_direct_owner_call_and_the_pass_converge_on_one_fence`, request while the composition serves |

## Verification (measured)

| run | result | seconds |
|---|---|---|
| existing focused regressions before the new modules (9 ids/modules) | 237 OK | 3.3 |
| `tests.job_manager.test_job_cancellation` + `tests.job_manager.test_fresh_attempt` | 181 OK | 17.0 |
| `tests.tools.test_job_cancellation_command` + `tests.job_manager.test_job_cancellation` + `tests.tools.test_parallel_runner` | 104 OK | 17.7 |
| manager focused ids (`CancellationFencesBeforeItStops`, `Deadlines`, `ExplicitAbandonmentFencesBeforeItRemoves`) | 47 OK | 0.7 |
| `just test-group job_manager` | 1546/1546 OK | 17 |
| `just test-group tools-pure` | 3355/3355 OK | 145 |
| `just test-group scans` | 492 + 2 approved optional skips = 494 | 98 |

Groups were selected for concrete reasons (changed owner modules; changed tools and registry; new modules under the sweeps). The first group pass failed only in the eight status-schema consumers pinned to `/7`; those pins were moved to `/8` (listed below) and the second pass is clean. Logs: `group-*.log`, `focused-*.log`, `groups-run1-failing-shards.txt`.

## Test paths changed (standing authority; reasons)

New: `tests/job_manager/test_job_cancellation.py` (22), `tests/tools/test_job_cancellation_command.py` (10), both registered parallel. Pins `baton.v12.job-status/7` → `/8` because the additive member moved the version: `tests/job_manager/test_tool.py`, `test_execution_limits.py`, `test_native_permission.py`, `test_exchange.py`, `tests/tools/test_bootstrap.py`, `test_attempt_diagnostics.py`, `test_worker_visibility.py`; product pins `tools/stack.py` (standard-library launcher copy, held equal by `test_stack`) and the `tools/worker_visibility.py` docstring. No assertion was weakened; no test removed.

## Limits and observations (not changed here)

- A cancelled stage keeps the ordinary vocabulary, so a retired queued stage still projects `queued` and a cancelled worker ending still projects `exceptional`; the Job's `cancellation` member is where retirement is read. A dedicated vocabulary would be a specification decision.
- The pre-attach fence moves the attempt's runtime axis to `cancel-requested` with nothing attached (the owner's existing behaviour); the report reads the fence record for `fenced-unstarted`.
- After a composition restart the re-observed runtime may be `uncertain` (`held-unknown`); the report never calls that cessation.
- Cessation proof of an ordered runtime remains with the ordinary ending/cleanup/reclaim owners; this candidate orders, records and reports and adds no cleanup path.
- `fresh-attempt` after an explicit cancellation now refuses; a replacement after cancellation is a new explicit creation (REC-7 eligibility otherwise unchanged).
- W383217 consumes `cancellation.request` / `fence_of` / `report` and the `cancellation` status member.
- `v12/QUICKSTART.md` gained a "Cancelling a Job" subsection (operator surface).


## Correction after review-2026-11-18T19-56-12Z (P1) — corrected candidate

Corrected candidate identity `sha256:eb29c00abf71308d3224cce31bdc7cdabdc63b153dc22181a05d838c336e06f9` over 27 paths (supersedes `84518e68…`; one more path: `src/baton_v12/job_manager/delegation.py`, and `tests/job_manager/test_delegation.py`). Bytes in `candidate.diff`; digests in `CANDIDATE-SHA256.txt` / `source.json`.

Disposition of the counterexample: CONFIRMED and closed. The axis `cancel-requested`/`stopping` is the owner's intent, written before `adapter.stop`; the candidate suppressed re-ordering on it. Now the canonical observation carries the cancellation owner's recorded `attempt.cessation-outcome` (plain data), and the pass orders again on every tick until the owner records `ordered` for the ATTACHED runtime identity, cessation is proved (destroyed / cleanup terminal), or the worker answered (ending owners' path). A stage's terminal label suppresses nothing while an unanswered runtime is attached. The report says `order-failed` when the owner recorded stop-failed / engine-unavailable / fenced-not-ordered for this runtime, `ending-in-progress` for an answered attempt, and carries the owner's outcome per target. Orders are recorded only on `quiescence.ordered: true`.

Proofs: `tests.tools.test_job_cancellation_command.TheRequestWhileServing.test_a_transient_stop_refusal_is_retried_until_the_owner_records_the_order` (the reviewer's injection at the real `OciAdapter.stop`: refusal once → `order-failed`, owner `stop-failed`, zero stops; next tick → one stop, owner `ordered`, one order record; three later ticks quiet) and `test_the_failed_stop_state_survives_a_restart_and_is_retried`; `tests.job_manager.test_job_cancellation.ClaimedAndRunningTargets.test_the_order_is_decided_by_the_owners_record_not_the_axis`, `test_a_transient_stop_refusal_is_retried_on_the_next_tick`, `test_an_order_for_another_runtime_identity_does_not_cover_this_one` (generation isolation), `test_an_answered_attempt_is_left_to_its_ending_owners`, `test_a_terminal_label_does_not_suppress_a_live_unanswered_runtime`. The reviewer's `probe.py` rerun: one engine stop, following ticks ordered, its "REPRODUCED" assertion fails (`reviewer-probe-after-correction.log`).

| run after the correction | result | seconds |
|---|---|---|
| focused: both new modules + test_delegation + test_status + test_sweep | 195 OK | 3.1 |
| reviewer probe.py | counterexample not reproduced | — |
| `just test-group job_manager` (observation member, contract member) | 1550/1550 OK | 16 |
| `just test-group tools-pure` (observe shape reaches every composition) | 3357/3357 OK | 150 |

Queued retirement, no-successor, exact replay, identity, completed-outcome, 120 s and restart coverage from the first candidate is unchanged and still passing.


## Correction after review-2026-11-18T20-12-59Z (P1 late start) — corrected candidate

Corrected candidate identity `sha256:a97a74128d248ceaf1acfe3bcdba6decff6cc3d43f7cf1d84202489d5e665626` over 27 paths (supersedes `eb29c00a…`; changed since: `src/baton_v12/job_manager/cancellation.py`, `tests/job_manager/test_job_cancellation.py`, `tests/tools/test_job_cancellation_command.py`).

Disposition: CONFIRMED and closed. `effect_for` chose the pre-attach fence for every `runtime_id = None`; an absent attachment does not prove the start never happened. Now only `execution_runtime == not-started` with nothing attached is NEVER-STARTED (pre-attach fence, unless this store already recorded the Authority's fence answer); `start-requested` or any other axis with nothing attached is an in-flight start routed through `StageExecution.cancel_attempt` → `request_cancellation`, whose `_order_quiescence` resolves the token-bound container and fences the exact generation. The owner's recorded `ordered` outcome names that token-bound identity, so a later attachment of the same identity replays and a different identity is ordered afresh; holds are retained (the order returns no token). `intake._no_start_declared` is untouched; no new lifecycle.

Proofs: `tests.tools.test_job_cancellation_command.TheRequestWhileServing.test_an_interrupted_start_reply_is_cancelled_through_the_stop_owner` (the reviewer's injection: `OciAdapter.start` completes, its reply is lost; durable `start-requested`/no attachment; cancel-job → one tick → order-cessation ordered, one engine stop of the token-bound container, owner `ordered` naming it, zero `attempt.abandon`, token not returned, later ticks quiet) and `test_an_interrupted_start_is_still_cancelled_after_a_restart_and_late_attachment` (same state across a composition restart: one fence, one stop, replay afterwards, report never `complete`); `tests.job_manager.test_job_cancellation.ClaimedAndRunningTargets.test_an_in_flight_start_is_ordered_not_fenced` (in-flight → ordered, token-bound identity accepted, late same-identity attachment replays, `not-started` → fence). Reviewer's `late-start-probe.py` rerun: one stop after the ticks, target `ordered` (`reviewer-late-start-probe-after-correction.log`).

| run after this correction | result | seconds |
|---|---|---|
| focused: both new modules + test_delegation + test_status + test_sweep | 198 OK | 3.5 |
| reviewer late-start-probe.py | counterexample not reproduced | — |
| `just test-group job_manager` (cancellation owner changed) | 1551/1551 OK | 15 |

tools-pure was not rerun for this step: the only tools-side change is the command test module itself, which ran in the focused set; the previous tools-pure accounting (3357/3357) stands for the unchanged tool sources.
