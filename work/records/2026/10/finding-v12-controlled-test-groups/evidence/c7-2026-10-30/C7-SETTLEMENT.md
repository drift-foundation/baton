# C7 — the shutdown matrix's three "token settlement" modes (2026-10-30)

K (Claude, interactive copilot as baton.prompt) under the owner-held claim
E384905 (arrangement B); K holds no claim. Answers review-2026-10-30T16-20-31Z
"next bounded milestone: C7's three shutdown modes; investigate token settlement
against the accepted lifecycle contract and preserve genuine defect coverage".
No product change. Files: `tests/manager/shutdown_fixture.py`,
`tests/manager/test_authoring_shutdown_deadline.py` (CANDIDATE-SHA256.txt).

## What the three failures were, and what they were hiding

Re-baseline (c7-before-fit-vacuous-matrix.log, retained under scratch): modes
`blocked_sweep` and `absent_cleanup` erred on `row['token']` being None and
`unknown` found no revoked-unreturned token. Reading the retained enforcement
reports showed the attempt in EVERY mode at `execution_runtime: not-started`,
`runtime: None`, `token: None`, and no `fake_engine` call at all. The start was
refused before the engine, and the eight "passing" modes passed vacuously: the
matrix had measured nothing since 2026-10-22.

The fixture journals its own `events.jsonl`; I added three journal rows to it
(`token_acquire`, `token_acquire_refused`, `start_refused`) so a retained run
says why a start never happened. They showed, in order:

1. `ContractRefusal: selected envelope cannot support the populated provider
   and verification limits` (diagnosis/blocked_sweep-start-refused-envelope.events.jsonl).
   Since 30245386 (W325959, "compose native token lifetimes") the enforcement
   controller composes a PERMISSION ENVELOPE for every start
   (`authoring_enforcement.permission_policy`) and refuses a start whose
   provider turn plus ordinary verification exceed the envelope's execution
   window `total_seconds - cleanup_seconds`. The fixture's Job asked for a
   20 s provider turn (plus the 900 s ordinary-verification default) inside a
   4 s window.
2. After fitting the Job limits: `SupervisorRefusal: the packet declares a 20s
   provider turn and the submitted Job's effective ceiling is 2s`
   (`authoring_baseline`): the packet's `turn_seconds` must equal the Job's
   provider turn.
3. After that: `ContractRefusal: remaining execution envelope cannot support the
   populated invocation limits` (diagnosis/blocked_sweep-acquire-refused-remaining-window.events.jsonl):
   the envelope's `eligible` predicate re-checks the limits against the
   REMAINING window at acquisition time, and the start reaches the token about
   1.3 s into the run, so a 4 s window left 2.7 s for a 3 s need.

Fixture corrections (all in `prepare`/the `acquire` wrapper):
- Job `execution_limits = {provider_turn_seconds: 2, verification_command_seconds: 1}`;
  packet `turn_seconds: 2`; diagnostic bounds `total_seconds: 10` (was 8),
  `cleanup_seconds: 4` unchanged, so the window is 6 s and 4.7 s remain at
  acquisition. Every mode still finishes well inside the test's 15 s bound
  (retained/summary.json: 1.5–8.0 s per mode).
- The `acquire` wrapper no longer injects `seconds=2`/`900`: `tokens.acquire`
  refuses a duration beside a permission envelope ("choose a duration or an
  execution envelope, not both"), and the envelope IS the lifetime now.

With that, `normal` reaches the fake engine's scripted `create` refusal again
(retained/normal.events.jsonl), and the three modes run a real runtime
(`runtime-single-1`): c7-after-fit-before-assertions.log shows them failing
on the OLD settlement assertions only.

## The token-settlement question, against the accepted contract

The old assertions expected, inside the run: observation `absent`, token
`returned` (blocked_sweep, absent_cleanup) and token `revoked` and not
returned (unknown). Those came from the injected 2 s token: it EXPIRED during
the blocked sweep and `Lane.tick`'s overdue path ran
`intake.reclaim_expired_resource` + `settle_revoked_resource` (stop, rm,
revoke, return). Under the envelope the token expires at `expires_at =
started_at + total_seconds`, which is also the controller's own deadline, so
no expiry reclaim can run inside the run by construction.

What the controller does at `stop_at` instead is its accepted contract, pinned
by its own tests in `tests/manager/test_authoring_enforcement.py` (144 OK after
B3 slice 1, independently accepted 2026-10-30T09:29:47Z):
- `held_before_expiry` / `test_deadline_stops_token_bound_writer_through_production_cancellation`:
  the deadline stops the exact runtime THROUGH PRODUCTION CANCELLATION; the
  token is neither revoked nor returned, zero renewals; observation
  `quiescent`; positive cessation does not repeat the stop.
- `test_early_deadline_uses_cancellation_not_token_renewal_or_early_revoke`.
- `test_unknown_engine_stop_preserves_fence_and_hold_then_retries`: an engine
  that cannot be asked keeps the token neither returned nor revoked, carries
  the fault, and the stop is retried under the same operation.
- `test_expiry_reclaims_exact_runtime_without_a_serving_tick` keeps the
  expiry-reclaim coverage (revoked, returned, absent) where it belongs.
The settlement of a stopped execution whose worker never cleaned up is the
retained-failure settlement owner's (W375444/8876bf95, `tokens.settlement_fence`,
`tools/stopped_settlement.py`; 17 + 379 focused tests accepted 2026-10-28).

The retained reports of the fitted run (retained/*.enforcement.json) show
exactly that contract: `blocked_sweep`/`absent_cleanup` rows have observation
`{runtime-single-1, quiescent}`, token `container runtime-single-1, returned
False, revoked False, renewals 0, settlement_fence None`, no faults; the
fake engine journal shows `stop` issued for the exact runtime at the 6 s
`stop_at` while the serving side was blocked (blocked_sweep) or signalled
(absent_cleanup); `unknown` carries `TimeoutError: selected fake engine
uncertainty` in the row's faults with observation `uncertain` and the same
held token. The workload outcome still lists the attempt under
`outstanding_cleanup`.

Assertions retargeted accordingly (both blocks carry the citation):
- blocked_sweep/absent_cleanup: every row observation `(runtime-single-1,
  quiescent)`; token `(container runtime-single-1, returned False, revoked
  False)`; no row faults; the fake engine's `stop` calls name exactly
  `runtime-single-1`; `outstanding_cleanup` retained as an actionable hold.
  The envelope/deadline assertions (`shutdown_progress.deadline <= request
  deadline`, final snapshot published before the request deadline) and the
  `deferred_signal_returned` check are unchanged.
- unknown: a row whose token binds `runtime-single-1` and is neither returned
  nor revoked; an `uncertain` observation; the engine fault carried.
- the token's terms (new, all modes with a token): `permission.policy` names
  this run and the packet's `total_seconds`/`cleanup_seconds`, `seconds` is
  None, `renewals == renewals_remaining == 0` (replaces `seconds == 2`).

This is not a weakening: the matrix regains its subject (real runtimes in all
eleven modes), still proves the exact runtime is stopped despite a blocked or
absent serving side, and now pins the token hold the stopped-settlement owner
relies on; the revoke/return behaviour it used to assert is the expiry path,
covered where the controller's accepted tests cover it. A product reading
that the controller SHOULD settle (rm + return) at `stop_at` would contradict
`held_before_expiry` and is a specification question for the owner, not
something this fixture can decide.

## Verification

- `just test-one tests.manager.test_authoring_shutdown_deadline`
  (c7-shutdown-matrix.log, retained run `BATON_SHUTDOWN_EVIDENCE` → scratch,
  reports copied under retained/): 4 OK in 60.2 s, all eleven modes.
- Six C7 modules together, `test_authoring_shutdown_deadline`,
  `test_authoring_enforcement`, `test_authoring_manager_guard`,
  `test_credentials`, `test_runtime_lane`, `test_reconciliation_worker`
  (c7-six-modules.log): 231 OK in 75.4 s. C7 is 34 → 0.
- Group: `tests.manager.test_authoring_shutdown_deadline` is a PARALLEL_MODULES
  entry and follows its package group (`manager-pure`); no registry change.
- Measured durations: vacuous matrix 35.1 s; fitted matrix 60.2 s (eleven
  modes, 1.5–8.0 s each, outer timeouts untouched).

No full suite, engine daemon, live model, Git mutation or other agents.
Scratch (`work/scratch/w384870-c7/`) holds the full retained runs incl.
control stores; the dossier keeps the reports, journals, scripts and logs.

## Correction and guard — after review 2026-10-30T17:17:47Z

CORRECTION of the wording above and of M384924/PROGRESS: "real runtimes in all
eleven modes" is FALSE. Five modes (`normal`, `delayed_snapshot`,
`snapshot_before`, `stuck_snapshot`, `stuck_workload`) select the scripted
`create` refusal in FakeEngine and never start a runtime; `pre_signal` never
invokes the author at all; every engine here is the fixture's FAKE engine, so
no actual engine-container coverage is established by this matrix. Only the
five runtime modes (`blocked_sweep`, `absent_cleanup`, `stuck_cleanup`,
`stuck_accounting`, `unknown`) run a fake runtime (`runtime-single-1`). The
retained journals (retained/*.events.jsonl, summary of all eleven below) say
exactly that:

| mode | engine calls | start refusal | selected injection |
|---|---|---|---|
| normal, delayed_snapshot, snapshot_before, stuck_snapshot, stuck_workload | ps, create, ps | scripted create refusal | snapshot_delay / workload_publication_stalled / none (normal) |
| blocked_sweep, unknown | ps, create, start, …, stop | none | blocked_serving_sweep |
| absent_cleanup | ps, create, start, … | none | deferred_signal_returned |
| stuck_cleanup / stuck_accounting | ps, create, start, … | none | stalled_cleanup_sweep / stalled_workload_accounting |
| pre_signal | none | none | injected_pre_supervision_signal |

GUARD (P2): `shutdown_fixture.unreached(mode, events)` lists every intended-
scenario fact a mode's journal lacks, from a declarative table
(`RUNTIME_MODES`, `CREATE_REFUSAL_MODES`, `INJECTIONS`, `SCRIPTED_CREATE_REFUSAL`):
a token acquired under the envelope; the fake engine's `create`; for runtime
modes an actual `start` and no start refusal; for create-refusal modes no
`start`, the scripted refusal text reaching the start and no unscripted
refusal; for `pre_signal` no acquisition, no create, no refusal; for every
mode its selected injection; and any `token_acquire_refused`. The matrix
asserts `unreached(mode, events) == []` for each mode before anything else.
`IntendedScenarioGuard` (6 tests) proves the eight-day journal shape cannot
pass an engine-reaching mode (envelope refusal, no create/start, missing
injection all named), an unscripted refusal cannot pass a create-refusal mode
(the old `normal` branch's gap), a started runtime fails a create-refusal
mode, every selected injection's absence is detected, a `pre_signal` journal
that invoked anything fails, and an unlisted mode declares no scenario.

Verification of the guarded module: `just test-one
tests.manager.test_authoring_shutdown_deadline` with retained evidence
(c7-shutdown-matrix-guarded.log, retained/summary-guarded.json): 10 OK in
60.2 s (3 FastContract, 6 IntendedScenarioGuard, the eleven-mode matrix with
`unreached(mode, events) == []` asserted per mode); the guard and fast classes
alone (c7-guard-unit.log): 9 OK in 0.05 s. CANDIDATE-SHA256.txt refreshed.
