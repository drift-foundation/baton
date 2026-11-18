# K first checkpoint — read-only revalidation and bounded plan (W383215)

2026-11-18, K (`baton.prompt` interactive, no claim). Answers HANDOFF-20261118.md / T383215 seq 385142. Nothing edited under `v12/`, no test executed. Baseline HEAD `c9e53b5f` (clean apart from this dossier's FINDING/PLAN/HANDOFF). Read: FINDING/PLAN/HANDOFF, DESIGN LIM-5, CONTROL-SELECTION-383131.md (sha256 `4af2b7d2…` matches FINDING), CONTROL-378038.md, overlap dossiers' current PLAN/FINDING, canonical `detail` of W383215/W321608/W321776/W371295/W375517/W375518/W383217.

## 1. Canonical state (read 2026-11-18)

- W383215 `queued`, route `baton.impl` (handler pool `claude`), handler none, next `baton.bug`, ready, no blockers; blocks W383217 (`block`). Parent W321608 `block`, route `baton.bug`/rvpc.
- W321776 `queued`/unclaimed (rview route). W371295 `block` (next baton.impl). W375517, W375518 `block`, route `baton.codx`, unclaimed. No live writer on any shared file.

## 2. October claims revalidated against c9e53b5f

Exists (reuse, unchanged):

- Active cancellation owner: `worker_manager/attempts.py:3180 request_cancellation` — journals `attempt.cancel:<digest(attempt, fixed assignment)>` intent, then `port.cancel` (Authority fence of the exact four-member assignment), then session quiescence and `_order_quiescence` (agent cancel, runtime stop). Replay-stable derived identities (`_cancel_operation_id`, `_authority_cancel_operation_id`). Return is an order, not cessation. `unstarted_cancellation_of` (3320) proves a cancellation that never ran.
- Pre-attach assignment fence: `worker_manager/intake.py:3951 fence_pre_attach_abandonment` (claimed, no runtime attached). Attached silent runtime: `intake.abandon_attempt` (2667), which adopts a prior cancellation's fence (`_committed_cancellation`, 3731).
- Composition reach: `tools/single_worker.py:2793 cancel_attempt` → `_Operations.cancel_attempt` (3499); `tools/stage_execution.py:4760 StageExecution.cancel_attempt` routes by the recorded scheduler allocation to the worker that started the attempt. Pinned by `tests.tools.test_single_worker.TheDeploymentCanStopWhatItStarted` and `tests.job_manager.test_native_stop_restart.test_cancellation_stops_exact_runtime_before_expiry_without_releasing_hold`.
- Installed instance-addressed command model: `tools/stopped_settlement.py` (COMMANDS prefix dispatch from `tools/job_manager.py:1242 main`; `stack_command` `manager` verb → `job_manager.main`, stack_command.py:81). Binding = instance destination + authority uuid + runtime digest + deployment digest + store paths; read-only recognition before any writable open; `InstanceOwnership.held()`/`invocation()` (tools/fresh_attempt_ports.py:145/168).
- Job store journal: `JobStore.transact/replay/operation_record` (store.py:965/1069/1122); `SCHEMA_VERSION = 9`.
- Successor/admission openers that must honour a fence: `projection._owed` (728: `queued` → `admit`, `offered` → `claim`), `manager._replace` (657) + `projection.replaceable` (92, `REPLACEABLE_ENDINGS` = abandoned-after-restart/-exclusion), `episodes.open_next` (228), `episodes.advance_correction` (560) via `review_driver.open_correction` (1786) and `StageExecution.routed` (4608, `correction_policy: decline` exists), `fresh_attempt.admit` (183, requires exceptional prior stage).
- Serving loop: `manager.serve` (832) with an injected per-tick `reclaim` pass composed in `tools/job_manager._serve` (1163) / `_reclaiming` (427). `_ReclaimAdapter.stop` was renamed `stop_expired` (job_manager.py:219) since the research; the research's seam map otherwise holds.
- Per-attempt runtime deadline pins with `action: cancel` (`worker_manager/deadlines.py`, W32577) reuse the same cancel identities; they are the per-attempt mechanism, not the Job contract (W383217 successor).

Missing (confirmed, 2026-11-18):

- No installed cancel verb: `job_manager.main` parses submit / fresh-attempt / create / status / serve plus the three settlement commands only.
- No persisted Job-store cancellation record or admission fence: no table, column, operation kind or reader; `STAGE_STATES` (documents.py:170) and `STATUS_SCHEMA = baton.v12.job-status/7` carry no cancellation; none of the openers above consults one.
- No serving-loop act that carries out a requested cancellation. Only the serving composition holds the worker's port/adapter (`request_cancellation` refuses a port for another participant); `InstanceOwnership.held()` refuses while a serving manager holds the instance guard, so an external process cannot order cessation of an active runtime while the manager runs.
- No cancellation reporting (status/monitor) and no 120 s bounded-shutdown/unresolved classification for cancellation (the authoring supervisor's is a separate composition).

Cleanup-campaign deltas since the research pin 8876bf95: attempts.py, tokens.py, maintenance.py, stage_execution.py (314e067c revoked-replay boundaries), intake.py/workspaces.py (438eefa6), authority/store.py, contracts/errors.py (2e330649). Import paths used above are current. `tools/parallel_test.py` now has explicit registries: every new test module must be registered in exactly one (TESTING.md §6).

## 3. Bounded implementation approach (two stores, no cross-store transaction, effects after durable fence)

A. Job-store owner, new module `src/baton_v12/job_manager/cancellation.py`:
   `request(store, *, job_id, reason)` journals `job.cancel:<job_id>` through `transact` with signature over `{job_id, reason}`; the committed record captures the Job's stages and live episodes/attempts at request time (same transaction, same store). Exact replay returns the committed record; a changed reason collides (journal signature refusal); a Job the store does not hold refuses. Readers: `fence_of(store, job_id)` and a connection-level `fenced(connection, job_id)` for use INSIDE other owners' Job transactions (same database, no I/O). Journal-only by derived identity: no Job-schema bump, so no contention with the W371295/W375517 version-10 selection. If review wants a per-target table, that is a coordinated schema decision, not taken here.

B. Fence consumers (Job store, decided inside existing write transactions so a cancel-vs-admit race is settled by the write lock):
   - `projection._owed`: a fenced Job's stages owe no `admit`/`claim`; stage state `cancelled` (new member of `STAGE_STATES`/`TERMINAL_STAGE_STATES`; `STATUS_SCHEMA` → /8; Job entry gains `cancellation`). Contract change, flagged for review; `fresh_attempt._TERMINAL` and viewers are checked for the new member.
   - `manager._replace`/`projection.replaceable`: never reopens an episode of a fenced Job.
   - `episodes.open_next` and `episodes.advance_correction`: refuse inside `act(connection)` when fenced (restart, replay and lost replies cannot reopen).
   - `fresh_attempt.admit` unchanged: a cancelled Job is not a failed Job; REC-7 eligibility is not widened or narrowed here (recorded limit for the successor).
   - A replacement generation is already protected: `AuthorityPort.cancel`/`Authority.cancel` fence the exact four-member assignment, so a stale request cannot stop a later generation.

C. Cessation pass, injected per tick beside `reclaim` in `tools/job_manager._serve` (new `tools/job_cancellation.py`; `manager.serve` gains one optional injected pass, same shape as `reclaim`): for each pending target it chooses the existing owner by observed state and journals the per-target outcome as `job.cancel.target:<attempt_id>` AFTER the external call returns:
   - not admitted / no live episode: retired before admission, nothing external;
   - `offered`, unclaimed: fenced Job owes no claim, the offer lapses by `offers.expire_overdue` (existing TTL); reported pending with reason;
   - claimed, no runtime attached: pre-attach fence through the owning worker composition (routed by allocation like `cancel_attempt`; a small additive composition method if `single_worker` exposes none);
   - runtime attached (starting/running/answering): `StageExecution.cancel_attempt` → `request_cancellation` (fence, then order); cessation proof stays with the ordinary ending/`intake.cleanup_of`/reclaim; `ordered_at` recorded; after 120 s without proof the status reports `unresolved-shutdown`, hold retained, reconciliation continues;
   - ended/completed/exceptional: fence only; outputs, verdicts and settlement untouched.
   Restart/lost reply: the pass re-derives from both stores and replays the derived identities (no second Authority cancel; FakeSession call counts prove it).

D. Installed commands in `tools/job_manager.py` dispatch (same prefix mechanism as settlement): `cancel-job --instance SEL --job JOB --reason TEXT` (request + fence; does NOT take the instance guard, so it works while the manager serves; per-Job `invocation` flock serialises concurrent requests; with no serving manager it reports cessation pending honestly) and `cancel-status --instance SEL --job JOB` (read-only; opens no writable handle; combines the Job journal with read-only control-store axes; reports ordered/ceased/pending/unresolved per target). Stale instance/authority/deployment binding refuses as settlement does. The command requests and reports; it never composes a second controller or kills a container.

E. Not in scope: finite deadline/correction policy (W383217), build/install/live engine, supervisor stop semantics, settlement behaviour, schema migration.

## 4. Shared-file concerns (actual paths)

- `tools/job_manager.py`, `tools/single_worker.py`: named initial owner of W375518 (blocked, unclaimed; waits on W375517, blocked). K's edits are additive (dispatch prefix, one injected pass, one routed composition method) and will be listed with digests; W375518 rebases on the accepted result. No concurrent writer today.
- `src/baton_v12/job_manager/{documents,projection,manager,episodes}.py`: W371295/W375517 touch schema/creation/store; K plans NO schema change and no creation-path change. STATUS_SCHEMA bump is flagged; W375518's creation-status members would follow serially.
- `tools/stage_execution.py`: W371295 chain (W376731/W376741) owns admission/carrier composition; K touches only cancel-adjacent additive code.
- `worker_manager/attempts.py`, `intake.py`, `authority/*`: no change planned (reuse only).
- `tools/parallel_test.py`: registry entries for the two new modules.
- W321776: exchange/operator context work, no overlap. W383217 consumes `cancellation.request`/`fence_of` and the status members.

## 5. Focused named test set, commands and estimates

New modules (registered parallel; groups `job_manager` and `tools-pure`):

- `tests/job_manager/test_job_cancellation.py`: request/replay/changed-request/unknown-Job; fence readable inside a transaction; queued stage owes no admit; abandoned ending not replaced; `open_next`/`advance_correction` refuse; two-connection cancel-vs-admit race (pattern of `test_scheduling.test_one_stage_episode_wins_a_two_connection_reservation_race`); reopen-store restart keeps the fence; status reports `cancelled`/`cancellation`. Estimate 2–6 s.
- `tests/tools/test_job_cancellation_command.py` on the `InstalledSettlement`-style installed instance fixture plus `ServingCase` composition with the fake engine: cancel-job with stopped manager (pending, honest); exact replay and changed reason; foreign instance/authority/deployment refusal; read-only surface opens nothing writable; ended Job keeps outputs/verdict; active runtime: one serving tick orders `request_cancellation` through `StageExecution.cancel_attempt` (Authority fence recorded, `cancel-requested` axis, stop vector issued), late launch reply after the fence refused, 120 s clock advance → unresolved-shutdown with hold retained, re-run after simulated crash replays without a second fence; claimed-not-started target pre-attach fence. Estimate 15–60 s (settlement command classes ran 1–2 s each; serving composition cases 1–4 s each in r3).

Existing regression ids (unchanged, run as-is; r3 durations in brackets):
`tests.manager.test_attempts.CancellationFencesBeforeItStops` [0.55 s], `tests.job_manager.test_native_stop_restart` [0.65 s], `tests.tools.test_single_worker.TheDeploymentCanStopWhatItStarted` [0.38 s], `tests.job_manager.test_sweep` [~4 s], `tests.job_manager.test_status` [1.1 s], `tests.tools.test_stopped_settlement_command` [est. 5–15 s], `tests.job_manager.test_review_driver` [9.3 s, serial registry], `tests.manager.test_runtime_deadlines.Deadlines` [1.4 s], `tests.tools.test_job_viewer` and `tests.job_manager.test_fresh_attempt.TheAdmission` if the state vocabulary changes [0.5 s].

Commands (from `v12/python`, prepared interpreter via the recipes):

```
TMPDIR=/var/tmp BATON_V12_DISK_ROOT=/var/tmp just test-one tests.job_manager.test_job_cancellation tests.tools.test_job_cancellation_command
TMPDIR=/var/tmp BATON_V12_DISK_ROOT=/var/tmp just test-one tests.manager.test_attempts.CancellationFencesBeforeItStops tests.job_manager.test_native_stop_restart tests.tools.test_single_worker.TheDeploymentCanStopWhatItStarted tests.job_manager.test_sweep tests.job_manager.test_status tests.tools.test_stopped_settlement_command tests.job_manager.test_review_driver tests.manager.test_runtime_deadlines.Deadlines
TMPDIR=/var/tmp BATON_V12_DISK_ROOT=/var/tmp just test-group job_manager      # est. 1–2 min
TMPDIR=/var/tmp BATON_V12_DISK_ROOT=/var/tmp just test-group tools-pure        # est. 3–6 min
TMPDIR=/var/tmp BATON_V12_DISK_ROOT=/var/tmp just test-group scans             # once before handoff; registry/contract/boundary sweeps, est. 5–7 min (boundary inventory's longest case 66 s in r3)
```

Groups declared: job_manager, tools-pure, scans (registry + any ownership entries new public owners need); manager-pure only if a worker_manager file is touched (none planned). No full suite, no engine, no live provider.

Durations above are estimates from r3 class timings; measured values are recorded at implementation.

## 6. Exact assignment operation needed (owner only)

Same arrangement as W384870 (seq 384882/384883): owner moves the unclaimed Work to the owner route and holds the claim; K works interactively under it, no identity borrowing.

```
/home/sl/opt/baton/v11/0650c61/bin/baton --config /home/sl/baton-v11.14aecfb/baton.json --participant baton.slaw reroute work=W383215 to=baton.decide reason="Arrangement B: owner-held claim; K implements as interactive copilot"
/home/sl/opt/baton/v11/0650c61/bin/baton --config /home/sl/baton-v11.14aecfb/baton.json --participant baton.slaw claim work=W383215
```

Expected readback: `detail work=2b077949-W383215` shows phase `active`, handler `slaw`, route `baton.decide`. K then records baseline/ownership in a new PROGRESS.md before the first edit. Independent review stays on baton.bug/rvpc at handoff.

## 7. Open points for the coordinator (no decision taken)

- Stage state `cancelled` + STATUS_SCHEMA /8 is a documented contract change inside accepted scope; confirm or name the alternative (cancel-status only).
- `fresh_attempt.admit` eligibility after cancellation stays as is (reported limit).
- Journal-only persistence (no Job-schema bump) chosen to stay clear of the version-10 owners.

## 8. Pinned corrections after review-2026-11-18T18-48-35Z (K, 2026-11-18, before any edit)

Claim readback at pinning time: W383215 still `queued`, route `baton.impl`, handler none (seq 385144 read; `detail` episode_seq 383249). Implementation does not start until the owner's reroute+claim (section 6) reads back `active`/`slaw`. These pins supersede sections 3–5 where they differ.

1. Status semantics (review 1). No new stage state and no new terminal vocabulary. `STAGE_STATES`/`TERMINAL_STAGE_STATES` unchanged; a worker ending with disposition `cancelled` keeps projecting `exceptional` exactly as today; completed outcomes, verdicts, outputs, holds and settlement are never rewritten. Reporting is ADDITIVE: the Job status entry gains `cancellation` (null when none requested) with `{operation_id, requested_at, reason, trigger_at, shutdown_bound_seconds: 120, shutdown: within-bound | unresolved | unknown-time, targets: [...]}`; each target reports `{stage_id, episode, attempt_id, observed, effect, state}` where state ∈ `retired-before-admission | awaiting-offer-lapse | fenced-unstarted | ordered | ceased | ended-before-request | held-unknown`. `ceased` is asserted only from the existing ending/cleanup owners (`intake.cleanup_of`, settled reclaim), never from an order's return. Adding the member revises the closed status contract to `baton.v12.job-status/8`; that is the only contract change and it is additive. `cancel-status` prints the same `cancellation` object.

2. Write-side fences (review 2), each inside the Job store's own transaction (same database, no cross-store work under the lock): `scheduler.reserve.perform` (the reserve-before-offer write; a fenced Job gets no allocation, hence no offer), `episodes.open_next.act` (no replacement episode), `episodes.advance_correction.act` (no correction round), `fresh_attempt._reserved.act` (no successor reservation, see pin 5). Read-side guards before already-computed serving actions: `projection._owed` (no admit/claim owed), `PooledManagerOperations.claim` (re-read fence before `submit_claim`), `manager._launch` (re-read fence before `operations.launch`). Anything that wins a race past a read-side guard is a LATE TARGET: the cessation pass derives targets every tick from the Job's live episodes and the control store's attempt axes (the request-time snapshot is evidence only) and reconciles them through existing owners — claimed/no runtime → `intake.fence_pre_attach_abandonment` via the allocation-routed worker composition; runtime attached → `StageExecution.cancel_attempt` → `request_cancellation`. A pre-existing offer is not left claimable: the manager's `claim` is fenced, and an accepted-but-unclaimed offer is reported `awaiting-offer-lapse` until `offers.expire_overdue` ends it (TTL contributes to the ending; the fence is the refused claim + refused reserve). Replacement generations on the Work are untouched because every fence names the exact four-member assignment.

3. Target identity and replay (review 3): `job.cancel.target:` + digest(`{authority_uuid, job_id, stage_id, episode, attempt_id, effect}`); the record stores the owner's returned manager/authority operation ids (e.g. `attempt.cancel:…`, `authority.attempt.cancel:…`) and the assignment generation read from the control store outside the Job transaction. A target record proves an ORDER, never completion; the pass keeps reconciling the target every tick until an existing owner proves cessation or reports a hold. Lost replies and late effects are recovered by the owners' own derived identities (`request_cancellation`, `unstarted_cancellation_of`, `fence_pre_attach_abandonment` replay); the FakeSession call count proves one Authority cancel per generation.

4. Timing (review 4): the trigger is `requested_at`, stamped by the Job store clock inside the `job.cancel` commit and immutable thereafter. `shutdown = unresolved` when cessation is unproved and `now − requested_at ≥ 120 s`; `unknown-time` when `now < requested_at` or the clock cannot be read; retry, restart, replay and an offline manager never move `requested_at` and never assert cessation. No new deadline policy (W383217).

5. Fresh attempt (review 5): `fresh_attempt.admit` REFUSES a prior Job that carries a `job.cancel` record — in `_prior` (cheap, outside the lock) and again inside `_reserved.act` (decides). Proof set: cancelled worker attempt projected `exceptional` then fresh-attempt refused; a pre-existing exceptional stage plus a cancel request racing the reservation on two connections (whichever commits first decides, no successor Job after the fence); an already-admitted fresh attempt before the request is left intact (it is a different Job).

6. Instance binding and concurrency (review 6): `cancel-job` verifies the instance selector and deployment binding read-only (as settlement does) BEFORE opening the Job store writable under its own incarnation; it takes NO manager instance guard and NO `InstanceOwnership.invocation` lock. Serialization is the Job store's own `BEGIN IMMEDIATE` journal: identical requests replay one committed record, a different reason collides, and concurrent serving ticks interleave by SQLite locking. Proofs: request while a serving composition is open and ticking; two concurrent requests; a direct `StageExecution.cancel_attempt` owner call racing the pass (one fence, both converge).

7. Verification (review): first the two new modules plus the named existing focused ids in section 5; broader groups only for a concrete change with recorded reason and expected duration (status contract revision → `tests.job_manager.test_status`, `tests.tools.test_job_viewer`; registry additions → `tests.tools.test_parallel_runner`; a new public owner function → the boundary/contract inventories, est. 5–7 min, run once before handoff). No full suite, no engine, no live provider, no Git mutation. Results return to the interactive coordinator in this session.
