# Held-integration status join, claim129904

Implements review-2026-09-09T18-11-13Z.md and the current PLAN. The existing
uncertain-effect fixture proves the serving hold; it does not prove the actual
configured CLI status join. The completed-state and generic locator evidence
is reused, not rerun.

One new two-case module exercises `tools.job_manager.main` with `status`, the
control store and configured `tools.stage_execution:observing_factory`.
The positive ties stage/episode/attempt/allocation/runtime to public owners
and checks exceptional state and actual absence of exchange/artifact/activity
logs. The negative configures a missing coordinator and must refuse with no
partial success output or invented store. Both compare public owner records
and protected database bytes/modes and guard serving capabilities. SQLite
WAL/SHM coordination effects remain allowed by the accepted opener contract.

Run from `v12/python`: `PYTHONPATH=src:. python3 -m unittest -v
tests.tools.test_stage_execution_status_hardening`. Expected under3s;
20s cumulative cap including failures. The runner records imported Python
source hashes before/after each run, keeps logs and readback, and imposes the
remaining cumulative timeout. No source/existing-test/registry edits or broad
run. Fixture-owned temporary stores and subprocesses require no live service.

## First-run correction

Run1: missing coordinator passed; the positive correctly reached exceptional
status and matched owners, but its last assertion incorrectly expected activity
itself to be null. The public reader returns an attempt-bound activity record
with null `bytes_observed` and `observed_at`. Correct that new assertion to the
exact existing contract; no production defect or accepted behavior change.
Run2 repeats the pair to complete the positive preserved-state checks and
validate the final candidate. Used1.759804s;18.240196s remain before run2.
