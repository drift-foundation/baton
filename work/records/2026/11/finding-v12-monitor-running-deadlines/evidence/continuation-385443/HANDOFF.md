# W385427 — E385443 review handoff

Implementation complete for independent review; not accepted or authorized for import. The earlier partial packets are superseded as current candidates and retained unchanged as history.

## Candidate and custody

Base `7ac02c7f01cc59b43ade0c98b55be59ea750af41`. Candidate tree SHA-256 `5348d4b36c4ac36e7152c3f1a51731154a62c658f340658fb760190627f156e5` (hash of exact `candidate.sha256` bytes); manifest SHA-256 `e29153d8a92629863f8e7cbc10441bcf1ceb2dc500cbf1d50a07dd1a618a1f3f`. Thirteen changed paths, below. Full candidate and base bytes are in `candidate/` and `base/`; `review-diff.patch`, `manifest.json` and `candidate.sha256` bind the delta. Host product bytes at all thirteen paths still match base. No host product import, native-line edits or live instance changes.

Canonical packet: `work/records/2026/11/finding-v12-monitor-running-deadlines/evidence/continuation-385443/`. Decisions: owning `FINDING.md` E385435 producer selection and owner fixture exception, `PLAN.md` isolated overlap allocation, M385440/M385442 retained in `thread.json`. Claim E385443.

## Outcome

Provider process creation now records attributable start, configured provider-turn deadline and direct-child end through the existing optional exchange publication cadence. Exchange readback validates command/session/attempt/operation identity and chronology. Missing, invalid or foreign timing is unknown and cannot change canonical exchange state. Shared status/monitor interpretation distinguishes Job age, invocation duration, activity and named provider/stage/Job deadlines; ties and partially known limits are qualified. It preserves the original Job/stage origins across continuation, the 15-second freshness rule and the distinction between a reached deadline and cessation. Blocked never-started stages no longer inherit episode age as runtime.

The optional closed document is `invocation.json`, schema `baton.worker-exchange.invocation/1`, with session, attempt_id, sequence_id, command_digest, operation, operation_id, scope=provider-process, started_at, deadline_at and nullable ended_at. UTC timestamps use the existing canonical millisecond grammar. It is bounded/no-follow read by the existing exchange parser. No collector, log parser, timeout-policy change or database migration. Job status adds optional created_at from the admitted submission origin.

## Verification and accounting

Final focused run: **347 passed, 0 failures/errors/skips**, 2.302s unittest / 2.565698011s wall (`focused-3.log/json`). Modules: tools.test_job_observation, tools.test_job_viewer excluding only its two deep cases, job_manager.test_status, manager.test_exchange, and manager.test_claude_agent.ProviderInvocationTiming. PATH rejected Git for this run. Six provider timing tests include real harmless local Python process start/end, a Popen recording seam, timeout, spawn failure, injected-runner unknown and optional publication failure. No real model, engine or live Job.

Final separately confined compatibility run: **2 passed, 0 failures/errors/skips**, 11.458s unittest / 11.662241865s wall (`compatibility-5.log/json`). These are exactly the two owner-approved TheRealObservationReaderReachesTheView cases; original assertions preserved. Combined final coverage: **349 passed**, 14.227939876s measured wall across the two final runs. No unresolved test cases in this selected set. This is focused evidence, not a full-suite or native-candidate acceptance claim.

Earlier iterations retained: focused-1 346 tests/1 failure, 2.541776129s wall (namespace fixture omitted new optional files); focused-2 346 passes, 2.565402474s wall; compatibility rounds1–4 each2 failures, respective wall 1.080897440s, 1.399542012s, 13.783273862s, 18.826663976s. `DIAGNOSIS.md` names actual errors. Initial missing unchanged worker schema was a worker input-validation fault, not Git. Later guard omissions: check-attr, global --no-optional-locks, then local archive-to-tar. Each stopped run is preserved; only the exact confined command shapes were admitted. The final two passes resolve the compatibility gap without modifying its assertions. Earlier episodes' costs remain in their own packets and are not included in this episode's run totals.

## Git boundary and recoverability

Owner exception was limited to those two tests in fresh disposable fixture repositories. `guard-proof.json` proves the read-only host mount refused writes and validator rejected owner-checkout operations; `guard-final-proof.json` binds the final guard and verifies new command shapes plus outside-root refusal. Bubblewrap mounted all host paths read-only except each newly created run directory, disabled network, isolated PIDs and dropped capabilities. Git wrapper rejected redirected gitdirs, external endpoints/paths and unlisted commands; hooks/signing and ambient Git config were disabled. No exception was applied to the owner checkout or native line.

Every run retains exact Git argv, cwd and target in `compatibility-N-git.jsonl`, internal Git Trace2 in `compatibility-N-git-trace2.jsonl`, worker faults before cleanup in `compatibility-N-diagnostics.jsonl`, output and wall accounting. `git-operation-summary.json` indexes all verbs and targets. Final run:442 entrypoint invocations, **zero refusals**. Fixture cleanup removed disposable repositories; required logs and input hashes are durable here. The allowed native stderr showed integration claimed, but matching final state did not prove matching cause; no native diagnosis or repair is claimed.

Reconstruct on another computer from base source plus all thirteen candidate files. Restore normal base worker packaging inputs, specifically `fixture-inputs.json`; install base dependencies. Run `run_focused.py` from reconstructed `v12/python` with PYTHONPATH=src:., bytecode disabled, disk-backed TMPDIR, no-git shim first on PATH. The compatibility scripts retain this host's absolute paths as evidence; remap their candidate/venv/fresh scratch roots for a new computer, retain identical confinement and only the same two tests. They are verification helpers, not permission for another native run. Owner still owns Git checkpoint/backup of this dossier; local preservation is not a claim of remote backup.

## Test changes and limitations

Changed test paths are enumerated below. test_status adds submission origin assertion; observation/viewer tests replace the false episode-elapsed expectation and add shared timing qualification cases; test_exchange adds correlated readback/restart/foreign-fact and producer-to-view coverage, extending its namespace-budget fixture to include both invocation names; test_claude_agent adds six process-boundary cases. Genuine defect coverage and deep pipeline assertions remain.

No owner decision remains for this implementation. Independent review must assess the additive diagnostic contract and complete delta. End time proves direct-child completion only, not descendant cessation. Abrupt termination before publication can leave end unknown; old/injected workers without attributable facts stay unknown. Rendering uses snapshot observation time, not a synthetic continuously advancing canonical clock. W385424 overlap remains: compose serially and independently review joined source before any host import. This packet does not accept, modify or supersede W385424's candidate.

## Changed paths

- `v12/python/src/baton_v12/job_manager/documents.py`
- `v12/python/src/baton_v12/job_manager/projection.py`
- `v12/python/src/baton_v12/worker_manager/exchange.py`
- `v12/python/tests/job_manager/test_status.py`
- `v12/python/tests/manager/test_claude_agent.py`
- `v12/python/tests/manager/test_exchange.py`
- `v12/python/tests/tools/test_job_observation.py`
- `v12/python/tests/tools/test_job_viewer.py`
- `v12/python/tools/job_observation.py`
- `v12/python/tools/job_viewer.py`
- `v12/python/tools/stack.py`
- `v12/worker/baton_worker.py`
- `v12/worker/claude_agent.py`
