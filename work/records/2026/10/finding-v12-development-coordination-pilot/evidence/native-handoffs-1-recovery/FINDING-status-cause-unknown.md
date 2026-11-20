# Separate finding: v12 status reports "cause unknown" for an ending the retained result records as a provider timeout

Prepared 2026-11-20 by K (`baton.prompt`, no claim) under W321608 as independently assignable work. It is a reporting defect in the v12 host status/diagnostic composition, not part of the W385331 implementation recovery, and it is prepared for `codexpc` (`baton.codxpc`, endpoint `baton.codx`). Nothing here was changed in the product; no store was opened directly; every fact below comes from the published status document, the installed read-only CLI and the retained, custody-sealed worker output.

## Observed (native-handoffs-1, Job `w385331-handoffs-1`, attempt `attempt-15d73943…`)

- `just --justfile /home/sl/baton-instances/native-handoffs-1/justfile status` prints `w385331-handoffs-1/implementation: exceptional; cause unknown` and `operation unknown` (`just-status.txt`).
- `baton-v12-stack view --status state/status.json --job w385331-handoffs-1` prints `reason failed: stage ended exceptionally; cause unknown` and `operation unknown` (`view-job.txt`).
- `state/status.json` (schema `baton.v12.job-status/9`, copy `status-17h15.json`): the stage carries `attempt_diagnostics.cause: null` with `unknown.why = "no component of this manager recorded ordering a cessation for this attempt, and no start or preparation failure is recorded either; which component ended it, if any did, is unknown"`, `exchange: null`, `runtime.execution_runtime: destroyed`, allocation `release_reason: cleanup-retained`, and a frozen `proposal` artifact locator.
- The same manager sealed the worker's completion manifest (`worker-output.json`, custody-held beside the frozen proposal): `disposition: "unable"`, `manifest_id: "completion-unable"`, `result_metadata["baton.git-proposal/1"].recap = "provider-failed: the provider did not finish within 3600s (24 changed path(s))"`, `result_metadata["baton.git-ordinary-tests/1"].status = null`.
- The frozen proposal's own `result.json` (sha256 `cf44d19a…`) records `disposition: "provider-failed"`, `provider.failure_reason: "timeout"`, `provider.seconds_bound: 3600`, `provider.seconds_bound_source: "job-default"`, `why: "the provider did not finish within 3600s"`, `verification: null`; `verification.txt` says `no verification was attempted`.
- The provider log status files say stdout was drained to its end and stderr is a partial prefix (`provider.stdout.status.json`, `provider.stderr.status.json`); the retained native session spans 2026-11-20T15:23:26Z to 16:23:23Z, i.e. the 3600 s provider-turn bound.

So the host knows exactly how this attempt ended: the worker answered `unable` with a typed `provider-failed/timeout` result, the manager sealed it, the projection mapped the frozen `unable` to `exceptional`, and every operator surface then says the cause is unknown.

## Confirmed code locations (read-only, host tree 3d05430f)

- `v12/python/src/baton_v12/job_manager/projection.py:58` — `_DISPOSITIONS = {"completed": "completed", "unable": "exceptional", …}`: the stage state is derived from the sealed worker disposition, so the disposition is available to the projection.
- `v12/python/src/baton_v12/worker_manager/failure_cause.py` (`attempt_failure_cause_of`, line 1197) — composes only cessation intent/outcome records, token facts, start/preparation failures and the attempt row's runtime/cleanup axes. It never reads the sealed `worker_disposition` nor the completion manifest's typed `result_metadata`, so an ending the worker itself declared reaches `cause: null` with "which component ended it, if any did, is unknown".
- `v12/python/tools/job_observation.py:284` (`_reason`) — prints `"cause unknown"` unless `stage.exchange.terminal` carries a fault code; for this deployment `exchange` is `null` (projection.py:382-393 documents that `exchange: null` means "nobody looked"), so a typed provider timeout prints as unknown.
- `v12/python/tools/attempt_diagnostics.py` — a read-only projection over the same diagnostic document, so it inherits the gap (`attempt-diagnostics.json`).

## Prior occurrence

The same text appeared on native-labels-5 (PROGRESS.md 2026-11-20, "`attempt_diagnostics cause: null` is a reporting gap (the composition never reads the sealed disposition)") where the underlying cause was a verification failure (`unable`/`verification-failed`). This second occurrence has a different cause (provider timeout) behind identical wording, which is the defect: distinct, host-known endings are reported as one unknown.

## Proposed direction (decision support, not authority)

- Compose the worker's sealed disposition and the typed outcome members already present in the completion manifest (`baton.git-proposal/1.recap` is prose; prefer the frozen result's closed members `disposition`, `provider.failure_reason`, `provider.seconds_bound`, `verification`) into the attempt diagnostic as wrapped, bounded members under the existing `FIELD_BOUND`/`CAUSE_MEMBERS` rules, with a new closed answer such as `worker-declared-ending` distinct from `unknown`.
- Let `_reason` print `failed: worker ended unable; provider timeout at 3600 s (job-default)` and `verification not attempted` when those members are known, and keep `cause unknown` only when no record exists.
- Keep "unknown" honest: never infer a cessation from the disposition; a declared ending is a different axis from who stopped the runtime (REC-1, REC-4).
- Affected logical groups and focused coverage: `tests.manager.test_attempt_failure_cause`, `tests.tools.test_attempt_diagnostics`, `tests.tools.test_job_observation`, `tests.tools.test_job_viewer` (all registered in `tools/parallel_test.py`), plus a projection fixture that seals an `unable` completion with a `provider-failed/timeout` result and asserts the printed reason. Deterministic only; no live provider.
- Scope suggestion: `v12/python/src/baton_v12/worker_manager/failure_cause.py`, `v12/python/src/baton_v12/job_manager/projection.py`, `v12/python/tools/job_observation.py`, `v12/python/tools/attempt_diagnostics.py`, their tests, and `v12/STACK.md` if the status vocabulary is documented there. The deployed bundle must be rebuilt before an installed instance shows the change.

## Prepared Work creation (coordinator/owner runs it; K did not)

```
/home/sl/opt/baton/v11/0650c61/bin/baton --config /home/sl/baton-v11.14aecfb/baton.json --participant baton.prompt create team=baton kind=codx title="v12 status reports cause unknown for a worker-declared provider timeout" origin=decomposition classification=confirmed-defect priority=normal parent=2b077949-W321608 body="$(cat /home/sl/src/baton/work/records/2026/10/finding-v12-development-coordination-pilot/evidence/native-handoffs-1-recovery/FINDING-status-cause-unknown.md)"
```

`kind=codx` names the implementer endpoint `baton.codx` (route `implpc`, handler codexpc); if the coordinator prefers to assign through its own route, `kind=decide` and a later pass are the alternative. Evidence paths in this file are repository-relative under `work/records/2026/10/finding-v12-development-coordination-pilot/evidence/native-handoffs-1-recovery/`.
