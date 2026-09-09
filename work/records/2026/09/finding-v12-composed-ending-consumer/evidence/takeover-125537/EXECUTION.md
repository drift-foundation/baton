# W122060 bounded proof takeover — claim125537

Question: after coherent fixture policy/target/instruction provisioning, does
one submitted Job and retained line complete correction, accepted review,
integration and terminal handoff through actual workers and ordinary ticks?
Only after that passes, does a newly reconstructed manager recover the committed
handoff before local acknowledgement without duplicating its effects?

Before execution: cumulative20s verification budget, counting iterative runs.
Reserve at least8s for the restart cut and focused final checks. From
`v12/python`, `PYTHONPATH=src:.`, use `python3 -m unittest -v` with exact new
methods in `tests.tools.test_stage_execution.OrdinaryTerminalLifecycle`, first
`test_one_job_completes_correction_integration_and_terminal_handoff`, then
`test_committed_handoff_recovers_before_local_acknowledgement`. Run only changed
fixture controls and preserved relevant negatives if budget remains; reuse the
review's existing module/provider evidence, with no full module or broad run.
The retained runner limits each process to remaining time and records every
command, output and elapsed time. Stop/report any source boundary outside this
test-only allocation before changing production code.

Operational lookup findings: guessed files `src/baton_v12/integration/targets.py`
and `v12/python/worker/integration_entry.py` were absent. The actual target
owner is `src/baton_v12/integration/queue.py`, found by symbol search; workload
location is resolved from the existing accepted integration-port fixture.
No required policy or dossier file was omitted.

Follow-up lookup findings: guessed `job_manager/operations.py` and `stages.py`
were absent; symbol search located `manager.py` and `projection.py`.

After verification5, bounded diagnostic question: does the actual integration
result report success, and do three subsequent ordinary ticks invoke the
integration consumer? Run `verify.py --probe` once with a3s process ceiling,
charged to the same20s cumulative allocation. This reads public owner results
and counts the existing consumer call; it does not invoke a provider to advance
the state or modify production. Preserve full results in `probe.json`.

Probe1 also found a fixture precondition: the disposable target inherited the
process umask mode rather than the reviewed Git ordinary0644 mode, so its
durable result correctly refused target drift. Provision that test target in
setUp before workers run; retain the refusal in
`probe-before-target-provisioning.json`. Repeat the same3s diagnostic once,
then the exact positive selector if its worker result succeeds. No owner
preflight is changed or bypassed.

Probe2 reached a missing disposable scratch mount root before provider startup.
The real workload creates its private report directory inside an existing
scratch root, as the accepted integration-worker fixture does. Supply that
root in the new fixture; retain probe2 in `probe-before-scratch-provisioning.json`.
Run the exact positive selector next (same remaining cumulative budget), then
repeat the3s diagnostic only if it reaches the known scheduling refusal.

Verification8 reached the adapter with an unprovisioned credential namespace
and home. Mirror the existing actual worker fixture: create its disposable
agent home, map a fake credential mount, and honor the provider runner's
environment/output descriptors. Repeat the exact positive selector, followed
only by the already declared3s scheduling probe if worker integration succeeds.

`base.json` and `base-*` retain all four reserved consumer paths. Only the stage
test may differ at handoff. Existing assertions and negative classes stay intact;
new positive proof is additive. All stores, source histories and worker turns
used by the fixture are disposable; there is no live runtime, model or secret.
