# One fresh useful Job — final operator sheet, candidate302142

Owner302138 reports successful accepted preparation and selects output inspection/final command review. This sheet awaits independent final review before owner execution. Do not repeat setup. Preparation is complete; the Job has not started. Run the following as the ordinary uid/gid1000 host user, from any directory. No new generic authorization is needed after independent acceptance.

## Launch once, in a foreground terminal

```sh
env BATON_V12_STAGE_EXECUTION_CONFIG=/home/sl/baton-runs/single-job-257627-291715/deployment.json PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/home/sl/baton-instances/single-job-257627-291715/manager-source/v12/python/src:/home/sl/baton-instances/single-job-257627-291715/manager-source/v12/python /home/sl/.local/state/baton-v12-venv/bin/python -B /home/sl/baton-instances/single-job-257627-291715/manager-source/work/records/2026/09/finding-v12-single-implementation-proof/baseline.py --packet /home/sl/baton-runs/single-job-257627-291715/PACKET.json --incarnation single-job-257627-291715
```

This is the exact emitted start argv/environment. It owns submission. Do not submit separately, run a second supervisor, rerun after failure, or start the historical installation binary. Keep this terminal open and retain its output. The corrected supervisor and modules are under this instance's manager-source; installation-runtime is preserved historical provenance only.

## Status, from another terminal after launch

```sh
env BATON_V12_STAGE_EXECUTION_CONFIG=/home/sl/baton-runs/single-job-257627-291715/deployment.json PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/home/sl/baton-instances/single-job-257627-291715/manager-source/v12/python/src:/home/sl/baton-instances/single-job-257627-291715/manager-source/v12/python /home/sl/.local/state/baton-v12-venv/bin/python -B -m tools.stack_command manager --store /home/sl/baton-instances/single-job-257627-291715/db/jobs.sqlite3 --incarnation single-job-257627-291715-read --authority-uuid a9717c22436349f6832c7645b62d8f8f status --control /home/sl/baton-instances/single-job-257627-291715/db/control.sqlite3 --observe tools.stage_execution:observing_factory
```

This is the exact emitted status argv/environment, observing this Authority/Job/control store. Wait until launch creates the Job and control stores before using status; they were absent at inspection. Before that point, absence of status is not a failed Job and is not a reason to start another one. Status is a current read/observation, not a lease, a freshness guarantee after display, or evidence that a retained provider result passed independent review. Do not inspect SQLite directly.

## Stop

Press **Ctrl-C once in the foreground launch terminal**. This sends SIGINT to the running supervisor and enters its bounded cancellation/accounting path. Allow it to finish reporting the retained outcome. SIGTERM is also handled, but this foreground procedure needs no guessed PID, process-name kill or separate stop service. Do not close the terminal, issue repeated interrupts, kill containers by name, remove directories or normalize permissions as a substitute for this procedure.

An interrupt normally exits130 and retains a held outcome. A stopped supervisor is not proof that its exact producer ceased. Check retained cancellation/cleanup evidence and outstanding_cleanup. If the terminal does not return or no outcome is available, report the exact terminal output/status and preserve the instance; do not claim cessation or retry. The reviewed300-second total includes60 seconds reserved for cleanup; it is cooperative, not a proven hard deadline for arbitrary blocking host calls.

## Read the retained outcome

```sh
cat /home/sl/baton-runs/single-job-257627-291715/outcome.json
```

The file does not exist yet. After normal completion, expect exit0, state=settled, stopped=completed, no held reasons/uncertainty/outstanding cleanup, and one attributable implementation proposal for job-single-job-257627-291715. Inspect workload.proposals and attribution, the stage result and exact attempt identity. The proposed change should contain only docs/v12-first-job-inspection.md, under100 lines, based on the pinned excerpt; its meaningful correctness still requires independent proposal review. No model review/approval receipt or automatic integration is selected. A successful provider exit or output file alone is insufficient.

Exit1/held, exit130/interrupted, early refusal, missing output, or incomplete accounting is not success. Preserve outcome, command output, preparation records and workspaces; return them for diagnosis. Never rerun setup or launch against this spent identity. Do not treat missing logs as empty logs. Any later log command takes --logs and --attempt before its subcommand, using the exact retained attempt and launch-home locators; no guessed attempt or directory scan.

## Bound execution and actual verification

Authority a9717c22436349f6832c7645b62d8f8f; Work a9717c22-W1; Job job-single-job-257627-291715; submission single-job-257627-291715-submission. One fresh implementation, no reuse/retry/second Job. Provider180 seconds, verification30, total300 including cleanup60. Configured review identity is distinct but no review provider is launched. Bridge network, opus profile, selected Claude CLI2.1.247 image sha256:c862c055c6430addc918ca078a9e4d55f6bd8173ed9c9878a8ad9d6cad334ca2.

The owner-selected real-provider question is whether the actual credential authenticates and the installed Claude adapter/CLI starts and completes the corrected proposal-only task under the real engine/host access boundary. Fake-provider evidence proves the coordination/recovery path but cannot answer authentication, actual provider protocol or model-dependent output. This one real Job supplies useful documentation; it does not itself establish parallel adoption or context reuse.

Owner302138 successful setup report is corroborated by retained COMPLETE and preparation/grant/repository logs: two real independent clones succeeded; source HEAD is478531dd1a2ce229fa0ee80912a84126832428ce and source status is clean. All126 frozen source/input hashes,81 historical installation files,eight generated packet files and two source task inputs match. Retained selections match the independently reviewed spec exactly. No frozen bytecode exists. Actual held_packet and verify_imported_sources pass without opening stores; package origins are the frozen manager source. No FAILED record, outcome, Job/control/integration store existed at inspection. This is preparation/readiness evidence, not a claim of completed execution. Authority preparation result records handlers and four grants; its public preflight retains the route/scoped-grant readback limitation. No raw store was read.

Evidence: ACTUAL-VERIFICATION-302142.json, ACTUAL-READER-302142.json and FINAL-PACKET-302142.json. The final manifest hashes external immutable files but deliberately excludes mutable databases. The manifest itself and this sheet are bound by FINAL-CANDIDATE-302142.json. Final reviewer should recheck current bindings and these exact emitted argv/environment, reusing accepted deterministic positive/interruption/deadline/access proofs. No product/test correction or repeated live/setup execution is selected here.
