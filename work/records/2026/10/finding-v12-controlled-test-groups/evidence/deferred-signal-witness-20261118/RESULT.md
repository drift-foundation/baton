# M385131 — third full run's one failure: the deferred-injection witness repaired (fixture/test only)

K (`baton.prompt`), 2026-11-18, under the owner's parent claim of W384870; K holds no claim. Scope per
`review-2026-11-18T16-52-54Z.md` (acceptance of codexpc report `evidence/review-r3-signal-count-20261118T165143Z.md`).
No product file changed. No group/full/live/Docker run. No Git mutation. The r1/r2/r3 evidence is untouched.

## Verdict

**Confirmed fixture ordering assumption, now removed.** `absent_cleanup` self-sent one SIGTERM at `defer`'s return and
copied `received`, and the matrix (`test_authoring_shutdown_deadline.py:204`) expected `['signal 15', 'signal 15']`:
the controller's stop plus the injection. Nothing orders the controller's stop before that copy. The injection is now
a separately identifiable signal, acknowledged by its own handler callback, and the controller's ordering is observed
and named rather than assumed. No product regression; no count relaxation, sleep, skip, deadline change, serialization
or rollback of c2cb0887.

## Mechanism (measured, `pre-fix-probe-absent_cleanup-timeline.txt`, idle host, times from the controller's entry)

| instant | event |
|---|---|
| 0.002 s | controller `supervise_process` starts; its stop fires at `deadline - reserve` = +6.0 s, polled every 0.25 s |
| 0.216 s | manager `_supervise` starts; its own serving bound `total - cleanup` = 6 s trips at 6.216 s, checked once per ~1 s serving tick |
| 6.247 s | manager enforcement thread reaches `stop_at`, cancels the fake runtime (`docker stop`) |
| 6.255 s | controller SIGTERM (`outer_signal`); `Termination._handle` in raise mode records `signal 15`, raises; serving ends `interrupted` |
| 6.256 s | `defer` returns; fixture self-sends SIGTERM; copy shows two entries |

Whether the controller's stop (6.0–6.25 s) or the manager's own loop end (6.216 s plus the tick phase, or the cancelled
runtime's terminal state seen on the next tick) ends serving is decided by the serving tick phase, not by any protocol.
When the loop ends first, `defer` runs before the controller's stop and the copy holds one entry: the r3 observation.
The exact r3 interleaving remains unproved (its journal was not retained); the mechanism above is sufficient on its own.

## Correction (2 files, `candidate.diff`, `CANDIDATE-SHA256.txt`)

`tests/manager/shutdown_fixture.py`
- `Journal` (rows written to `events.jsonl` AND kept in memory); `observed_termination(journal)` patches the real
  `Termination._handle` so every callback is journaled: number, mode it ran in, whether it raised, `received` after.
- `inject(termination, journal, send=os.kill)`: sends `INJECTED_SIGNAL = SIGINT` to the process (the `Termination`
  handler treats SIGINT and SIGTERM identically; the number differs from the controller's SIGTERM so the callback is
  the injection's own and cannot be coalesced with, or satisfied by, the controller's delivery), then spins, bounded
  by `ACKNOWLEDGEMENT_SECONDS = 2`, until a `termination_callback` for that number appears AFTER the send; records
  `deferred_signal_sent` (mode, `received_before`, main thread) and `deferred_signal_returned` (acknowledged, the
  callback row, `received_before`/`received`). A handler still in raise mode propagates out of `inject`, so the
  returned row never appears.
- The injection runs from a wrapper around the real `Termination.defer` (after it returns), not from the `sys.settrace`
  hook, so the injected callback is itself traced and journaled (it was invisible before: handlers invoked while the
  trace function runs are untraced).
- `deferred_injection_unreached(events)` names every missing fact (mirror of `unreached`): exactly one sent/returned
  row; sent in defer mode on the main thread; the injected record absent before the send; acknowledged by its own
  callback in defer mode that did not raise; `received` extends `received_before` by exactly one injected record and
  nothing but controller records; no injected-number callback raised.
- `controller_ordering(events)`: `controller stop before the injection` / `controller stop after the injection, while
  deferring` / `controller stop sent, not seen by the Termination handler` / `no controller stop` / `no deferred
  injection`. Observed, never forced.
- `INJECTIONS['absent_cleanup']` is still `deferred_signal_returned`; the mode's scenario guard is unchanged.

`tests/manager/test_authoring_shutdown_deadline.py`
- Composition `absent_cleanup`: the exact-two assertion is replaced by `deferred_injection_unreached(events) == []` and
  `controller_ordering(events)` not in (`no deferred injection`, `no controller stop`); the ordering is recorded in
  `summary.json`. Every other assertion of the mode (runtime quiescent/exact stop, token retained not returned/revoked,
  empty faults, outstanding cleanup held, final publication before the request deadline, manager reaped, not -9) is
  unchanged and still independent of the count.
- New `DeferredInjectionWitness` (in-process, real `Termination`, real `os.kill` to self, every delivery acknowledged
  before the next send; the SIGTERM a case sends stands in for the controller's and is labelled so):
  - stop BEFORE the injection: raise-mode SIGTERM interrupts, `defer`, injection acknowledged and returns;
    `received == ['signal 15', 'signal 2']`, callbacks `(15 raise KeyboardInterrupt), (2 defer None)`.
  - stop AFTER the injection: `defer`, injection acknowledged, SIGTERM recorded in defer mode and returns;
    `received == ['signal 2', 'signal 15']`.
  - the same number twice (the historical exact-two, kept where it is deterministic): `['signal 15', 'signal 15']`,
    first raised, second returned.
  - missing injection (`send` no-op) after a prior callback: unacknowledged after the 2 s bound, witness names
    `never acknowledged`, `no handler callback`, `0 injected records`; the prior `signal 15` does not satisfy it.
  - handler still raising at the injection (no `defer`): `KeyboardInterrupt` escapes `inject`; witness names
    `0 deferred injections returned`, `still in raise mode`, `raised KeyboardInterrupt`.
  - synthetic journals: prior injected record, double delivery, rewritten list, raised callback, each named;
    ordering vocabulary checked.

## Verification (full-run environment: TMPDIR/DISK_ROOT=/var/tmp, WORKSPACE_GROUP=1001, INITIAL_ACCESS_ENGINE=1, both images)

| run | log | result |
|---|---|---|
| in-process classes (`DeferredInjectionWitness`, `IntendedScenarioGuard`, `FastContract`) | `post-fix-in-process-classes.log` | 15 OK, 2.05 s |
| whole module, pass 1, matrix journals retained | `module-run-1.log`, `module-run-1-journals/` | 16 OK, 62.1 s; `absent_cleanup`: controller stop before the injection |
| whole module, pass 2 | `module-run-2.log` | 16 OK, 62.2 s |
| accepted controller/manager witnesses `tests.tools.test_next_run_flow` (late-exit positive, hung-child negative, original 3) | `next-run-flow-witnesses.log` | 5 OK, 38.0 s |
| real composition, natural ordering, 5 ad-hoc runs | `post-fix-probe-absent_cleanup-5-runs.txt` | 5/5 witness `[]`, `controller stop before the injection`; injected callback traced, acknowledged at once |
| real composition, FORCED stop-after-injection, 3 ad-hoc runs (probe-only gate on the controller's SIGTERM, `probe-late-ordering.py`) | `post-fix-probe-late-ordering-3-runs.txt` | 3/3 witness `[]`, `controller stop after the injection, while deferring`; held, runtime quiescent, token retained, no faults, final publication 0.82 s before the request deadline |
| /var/tmp residue | `var-tmp-before/after-module-run-{1,2}.txt` | identical listings (0 new entries) both passes; probe roots removed with `disk_roots.remove_owned_root` |

`module-run-1-journals/` keeps each mode's `events.jsonl`, `outer.log`, outcome and enforcement/manager/shutdown
documents (1.2 MB); the retained storage/launch trees (14 MB, product custody modes) were removed as fixture output.
In the forced-late probe the `outer_signal` row is written by the fixture before the gated send; `probe_gate_released`
is the actual send instant.

Groups: manager-pure (`tests.manager.test_authoring_shutdown_deadline`), tools-pure re-verified unchanged. No test
module added; no registry change.

## Limitations

- The composition cannot force either ordering without altering the controller's or the manager's timing, so it
  records the one it saw; the deterministic ordering proof is in-process at the real `Termination` boundary, and the
  forced-late composition evidence is probe-only (not a test).
- Handler-level evidence (`termination_callback`) and the controller's OS send (`outer_signal`) are distinct rows;
  a controller SIGTERM landing after `Termination.restore` is met by `child_main`'s cooperative handler and is then
  visible only as the send.

## Product/spec observation (reported, not changed)

In the stop-after-injection ordering the manager ends serving by its own bound or by the cancelled runtime's terminal
state on its next serving tick, up to ~1 s after the controller's stop request; with the matrix bounds (total 10,
cleanup 4, tail 2) that leaves the manager as little as ~0.8 s of its shutdown budget before the controller's request
deadline (measured 0.82 s with a 0.27 s tick lag). The lifecycle assertions held in all forced runs. Whether the
manager's serving bound should be measured from the controller's envelope rather than its own start is a spec question
for the owner; it is not within this correction.

## Candidate

HEAD c2cb08877495b3124f426dc31e6fa76e37e8e1d9; changed 2 (`source.json`, identity
0f5ad56f67cf34762048742f6bdd21c6db346f1d97e9d2634fac39982884dfc0): `v12/python/tests/manager/shutdown_fixture.py`
(9b07921e…), `v12/python/tests/manager/test_authoring_shutdown_deadline.py` (d3949af0…); +284/-9.

## Next

Technical and priority review of this candidate; owner checkpoint; coordinator's fresh full-run wrapper; final complete
accounting; child/parent closure; final check-in. No green full-suite claim.
