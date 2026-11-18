# Joined B4 verification — incomplete, harness interruption

Assignment M385053; claim E385055; participant baton.codxpc, role impl.

Exact committed source: `438eefa68f592e159f42cf1d190c7d7de4afde12`, materialized with declared consumed inputs, 1,134 files / 41 consumed-input files. No overlays, current K bytes, product edits or test edits. Source-before and source-after match all manifest hashes.

Collection: 242 unique IDs in 13 selections. Completed: 143 passed, zero failures/errors/skips, 88 successful subtests. One additional test started and was deliberately interrupted; 98 tests never started. This is NOT combined B4 acceptance and NOT evidence of a product failure. `accounted-summary.json` is the corrected accounting authority: the raw runner `summary.json` only knows completed ledgers and therefore calls all 99 without final ledgers unrun; `04/tests.log` proves one actually started.

## Results

| Selection | Passed | Seconds | Outcome |
|---|---:|---:|---|
| tests.manager.test_integration_worker | 83 | 18.432 | passed |
| tests.manager.test_private_line_access_engine | 4 | 2.466 | passed |
| tests.manager.test_input_delivery | 56 | 6.271 | passed |
| tests.manager.test_worker_entry_engine | 0 | 57.664 | interrupted: harness |

Remaining nine selections did not run. Exact expected IDs are in `collected.json`; per-selection invocations/logs/ledgers/results are in numbered directories. Ordinary deterministic/fake provider tests only; no live providers, supervised deadline tests or full suite.

## Confirmed blocker

The evidence-only `run-joined.py` Docker shim invokes every command with `subprocess.run(..., capture_output=True)` and writes stdout only after exit. The snapshot's `v12/python/tests/manager/test_worker_entry_engine.py:79` starts a streaming `docker exec` Session; `receive()` at line 96 requires each response before sending the next frame. Buffering in the shim prevents that response from reaching the test. First test: `DockerWorkerEntry.test_a_frame_for_another_session_is_refused_by_the_real_worker`. No unittest failure was emitted. After identifying this wrapper defect, sent SIGTERM to exact test process group 70575 at 57.664 seconds (600-second timeout was not reached). The runner stopped subsequent selections. Source repair was neither attempted nor indicated.

Required continuation: preserve streaming stdin/stdout/stderr for `docker exec` in an evidence-only wrapper (e.g. direct exec passthrough); preserve this interrupted attempt; verify remaining selections on the same immutable source with complete accounting. No candidate source repair is supported by this interruption. The single authorized build was consumed; its task tag was removed during stop cleanup. Image/build selection must be accounted for in continuation.

## Prerequisites, provenance and cleanup

Docker/group/flags/private image verified, interpreter Python3.13.7. One offline worker build, `--pull=false --network=none`, from installed pinned base; exact arguments and image IDs in build-plan/result. Build duration0.114s. Explicit image environment prevented implicit builds; shim rejects build/pull and adds `--pull=never` to runs. Initial metadata Go-template probe failed on absent Volumes; corrected full-inspect probe succeeded, retained evidence distinguishes both.

38 exact created container IDs are absent. 37 cleaned by completed tests; one interrupted-test container required exact label/image-validated forced removal. All pre-existing container IDs and image IDs remain. Task build tag removed. No task processes retained. Completed test temporary roots removed. Interrupted fixture archived to durable `04/interrupted-fixture.tar.gz` before deleting the exact task root; owned read-only directories required owner write permission for cleanup, recorded in cleanup-final.json. No authority store was queried directly; archived database is the disposable test fixture only. Snapshot remains disposable; manifest plus exact Git objects and durable evidence establish recovery inputs.

Execution helper: `python3 <this-evidence-directory>/run-joined.py` (do not rerun unchanged: known buffering defect). Each test selection uses prepared venv Python and `audit-tests.py` with failfast,600s timeout and process-group termination. Durations are measured, no cumulative budget gate inferred. `SHA256.json` covers preserved evidence files except itself.

Handoff: return W384944 to baton.decide for harness-continuation review; combined acceptance remains due.
