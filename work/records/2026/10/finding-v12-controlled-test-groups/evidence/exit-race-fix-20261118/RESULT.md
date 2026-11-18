# M385119 — second full run's one failure: the controller's late stop kills its exiting manager

K (copilot, no claim), 2026-11-18, over owner checkpoint `5b9659f0`. Bounded correction of the one failed id of
`evidence/final-suite-20261118-r2/` (`tests.tools.test_next_run_flow.JoinedFlow.test_two_tasks_and_failed_start_recovery_after_one_installation`).
Focused deterministic tests only; full-run environment retained; no group/full/live/Docker run; no Git mutation. The r2
evidence is untouched.

## Verdict: a product ordering defect in the authoring controller/manager pair, exposed by load, not a fixture timing assumption

The second run's inner result is complete and truthful (settled, implementation completed, valid verified candidate, no
held cause, runtime destroyed and token returned). The outer report is `held` with `child_status -15` at 3.254 s
against a 12 s bound. Exact ordering, reconstructed from `final-suite-20261118-r2/failed-scenario.json` (same host
monotonic clock; `cleanup_seconds` 4 so the controller's tail is 2 s):

| step | who | evidence | time |
|---|---|---|---|
| inner outcome finalized | manager child (`baseline.main` returns) | `outcome.json.finished_at` | 15:11:51.150Z |
| manager's own shutdown begins: `guard.stopping.set(); shutdown.begin()` | child `child_main` finally | `progress.json.deadline` 71521.0037 = begin + 2 | mono 71519.004 |
| enforcement thread's final tick publishes `stopping`/`finished` | child enforcement thread | status snapshot (read by the controller) | 71519.00–71519.03 |
| controller poll sees `stopping`/`finished`, shortens its deadline to now+4, writes the stop request, `killpg(SIGTERM)` | controller `supervise_process` lines 337-346 | `shutdown.json.deadline` 71521.035 = request + 2; `shutdown_deadline` 71523.035 | mono 71519.035 |
| manager had already published `final enforcement publication` and RESTORED its previous SIGTERM disposition (`SIG_DFL`) | child `child_main` finally (old lines 545-547) | `progress.json.step` = final enforcement publication, no later step | before 71519.035 |
| manager dies of the controller's SIGTERM during interpreter exit | child | `child_status -15` (`CLD_KILLED` 15), `child_exited true` | 71519.04–71519.3 |
| controller reports `held` (child status not 0), returns 1 | controller | `state held`, `faults []`, `operator_signals []` | elapsed 3.254 s |

The first run of the same test shows the race NOT taken: no `.shutdown.json` was written at all (the child had exited
before the controller's next 0.25 s poll), `child_status 0`, `completed`. The window is
[manager restores `SIG_DFL`, manager process exit): interpreter finalization of a process holding SQLite stores and a
fixture worker thread. Under 32-way parallel load that window exceeds the controller's poll interval often enough to
be hit; it exists in production (`python -m tools.authoring_enforcement`) exactly the same way. Enlarging timeouts
would not remove it: the controller's SIGTERM is issued on observation of the manager's own completion, not on a
deadline.

Why the controller signals at all: `supervise_process` treats `finished` as a reason to set `stopping` and, for a
child that has not exited, to request shutdown and SIGTERM its process group. That is the designed cooperative stop
(RUN-5), and the manager's handler for it only sets its stopping event. The defect is on the manager side: it restored
the default disposition before leaving, so the one signal it is designed to absorb became a death during exit and
discarded its truthful exit status.

## Product change (one file)

`tools/authoring_enforcement.py` `child_main`: the cooperative SIGTERM/SIGINT dispositions are installed for the whole
process lifetime and never restored to the defaults (`previous` and the restoring `finally` removed; the shutdown
sequence itself is unchanged). `child_main` only ever runs in the dedicated manager process (it binds its lifetime to
the controller with `prctl` and checks `getppid`), so nothing else ever ran after that restoration. The controller is
unchanged: it still requests shutdown and terminates on `stopping`, and still SIGKILLs at its deadline, so a manager
that does not leave is still ended there and reported `-9`, exited and `held`. `running_as`, envelope, halt, token and
enforcement semantics are untouched; no spec change (RUN-5 cooperative stop, host enforcement final).

## Witnesses (fixture flag + two JoinedFlow cases, `tests/tools/`)

- `next_run_flow_fixture.py`: `--fixture-exit-delay=SECONDS`, carried to the WATCHDOG'S CHILD like `--fixture-deny-line`;
  the child registers an `atexit` hook that records `manager-exit-delay` (monotonic time and the NAMED SIGTERM
  disposition it meets: `SIG_DFL`/`SIG_IGN`/repr) and sleeps. That holds the real manager in its exit after `child_main`
  returned, so the controller's late stop lands every time instead of only under load.
- `test_a_late_controller_stop_during_the_managers_exit_keeps_its_completed_status` (delay 1.5 s): proves the ordering
  (the controller's stop request was written after the manager entered its exit: `linger.monotonic <= request.deadline - 2`),
  that the manager met it with the controller child's own cooperative handler (`child_main` lambda, never `SIG_DFL`),
  no operator signal, and `(start, child_status, state) == (0, 0, completed)` with the inner outcome settled/completed.
  BEFORE the product change this exact case fails `(1, -15, 'held')` with the disposition recorded as `SIG_DFL`
  (`pre-fix-witnesses.log`, `pre-fix-witness-disposition.log`: the stop request landed 0.19 s after the manager entered
  its exit).
- `test_a_manager_that_never_leaves_after_its_final_publication_is_killed_at_the_deadline_and_held` (delay 60 s): the
  kept disposition cannot make a manager immortal; the controller requests shutdown, SIGKILLs at its shortened deadline,
  reports `child_status -9`, `child_exited`, `held`, elapsed within the 12 s total bound, and the settled inner outcome
  does not make it a success. Before the change this case also died `-15` (the absorbed signal, not the backstop).
- No existing test's assertions or expected behavior changed; `OuterDeadline` (controller terminate/kill timing with a
  fake child) passes unchanged.

## Verification (all under `just test-one`, prepared interpreter, TMPDIR/DISK_ROOT=/var/tmp)

Pre-fix reproduction (product untouched, full-run env): both witnesses FAIL with `-15` — `pre-fix-witnesses.log`.
Post-fix (full-run env): both witnesses OK in 12.5 s, 0 new /var/tmp entries — `post-fix-witnesses.log`.
Batch (`run-batch.sh`, `summary.tsv`, `runs/*.log` with per-run /var/tmp and container listings), every module that
composes or imports the controller, under the full-run env (`BATON_V12_WORKSPACE_GROUP=1001`,
`BATON_V12_INITIAL_ACCESS_ENGINE=1`, both images) AND the default env:

| module | tests | full-run | default |
|---|---|---|---|
| tests.tools.test_next_run_flow (3 existing + 2 new) | 5 | OK 38 s | OK 38 s |
| tests.manager.test_authoring_enforcement | 34 | OK | OK |
| tests.manager.test_authoring_shutdown_deadline (real baseline shutdown matrix) | 10 | OK 61 s | OK 60 s |
| tests.manager.test_authoring_manager_guard | 7 | OK | OK |
| tests.tools.test_next_run_managed | 34 | OK | OK |
| tests.tools.test_next_run_recovery | 5 | OK | OK |
| tests.tools.test_next_run | 11 | OK | OK |
| tests.job_manager.test_serving_renewal | 14 | OK | OK |
| tests.job_manager.test_native_stop_restart | 6 | OK | OK |
| tests.job_manager.test_native_permission | 20 | OK | OK |

146 tests per environment, 292 OK; every run 0 new /var/tmp entries and 0 new containers. Groups touched: tools-pure,
manager-pure, job_manager (declared per TESTING.md). Not run (not released): scans, groups, full suite.

## Candidate

Over `5b9659f0`, 3 files, +102/-12 (`candidate.diff`, `CANDIDATE-SHA256.txt`): `tools/authoring_enforcement.py`
(product), `tests/tools/next_run_flow_fixture.py`, `tests/tools/test_next_run_flow.py`. Source identity
`source.json`: HEAD 5b9659f0, changed 3, content digest `f079e72922a7c247d9c1474aa19b7d65eaddeebdf27a55abe657f8db5ca79aef`.
`git diff --check` clean. No runner registry pins the controller's bytes (packets hash the installed copy at
composition, as the flow and shutdown fixtures do).

## Next

Technical AND priority review of this candidate; owner checkpoint; a fresh evidence directory and owner-run full suite
(a new packet pinned to the next checkpoint, as `final-suite-20261118-r2/PREREQUISITES.md` was); independent final
accounting; child/parent closure; final check-in.
