# W385427 partial implementation handoff

Author baton.codxpc, role impl; claimE385429; assignmentM385428. 2026-11-21T04:06:54.075911+00:00

**PARTIAL — not full acceptance of the requested invocation timing outcome.** The isolated candidate fixes misleading episode elapsed, separates Job age, presents existing named Job/stage deadlines, qualifies unavailable provider timing, and preserves snapshot/activity ages. It is ready for review as partial work; the full invocation duration/provider countdown is not implemented because there is no attributable start/end in the current snapshot. No host product import or running W385424 instance/input change.

## What changed

- Shared tools.job_observation stage_timing owns structured snapshot-time interpretation. Monitor list/detail and status call it with the same Job/control facts. Episode opening is no longer reported as invocation elapsed. A never-started blocked stage is labelled not started; ambiguous/previously executed stages stay unknown.
- Job submission recorded_at is projected additively as created_at through the existing owning read view, even for Jobs with no control profile. No database/schema mutation or external I/O in the transaction.
- Independent stage/Job deadlines are compared at observation time; ties named, expired limits clamp to zero and say cessation unconfirmed. With an unknown provider start/deadline these are explicitly earliest KNOWN only. Uncertain/stale/future control timing is unknown; negative activity/job durations no longer become a misleading zero. Future snapshot ages are stale.
- Tests replace the old episode-age-as-runtime expectation and make a state-refresh assertion distinguish state from the newly displayed running label. Additive cases cover partial limits, blocked stages, ties, boundary/retry clocks, unknown/future/stale timing and terminal limitations. Existing positive created_at projection asserted.

## Exact remaining work / continuation

Actual invocation running duration, terminal invocation duration and provider deadline still render unknown. Worker exchange states carry operation/state only; dispatched is published BEFORE provider invocation. Configured provider_seconds alone cannot supply its origin; claims, episodes, admission, activity receipts and runtime launch cannot substitute. Existing projection has no trustworthy start/end to expose. Continuation is a minimal attributable start/end/deadline publication at the owning invocation boundary, correlated with attempt and operation, then an additive projection and shared interpretation. Preserve original Job/stage deadlines across retry/continuation and prove both producer and consumer together. This candidate does NOT add a fictitious invocation field or count down a configured limit from Job age. No owner product decision is needed to invent an origin; the fact is absent. Coordinate this source work with W385424 before joined review/import.

Two existing deep viewer compatibility cases remain unverified: TheRealObservationReaderReachesTheView.test_a_foreign_job_still_refuses_against_the_real_reader and .test_the_view_renders_the_real_model_free_completion. They first lacked vectors.json / worker imports in the isolated copy; after copying those unchanged inputs they failed fixture worker execution (turn returned1). No baseline attribution proven. Later inspection found this fixture invokes Git; do not rerun within the no-Git-mutation boundary. Earlier test invocations reached fixture Git operations, contrary to the intended verification restriction; this is disclosed, not described as zero Git use. No owner repository Git index/history operation was performed; host v12 remains clean. Continue with an appropriately isolated non-Git fixture or separately authorized compatibility verification, not weakening assertions. No live provider or real engine execution occurred (fixture boundaries).

## Verification

Final focused run:156 tests passed,0 failures/errors/skips;2 deep cases explicitly excluded by retained run_focused.py, not counted as passes or silently removed. focused-5.log/json, wall1.098897550s. Prior runs retained: run1 158tests25failures69errors (broad textual insertion accidentally reached shape validation plus incomplete fixture); run2 158tests1failure5errors (state-label assertion and missing vectors); run3 158tests2errors (worker import); run4 158tests2failures (worker fixture). These are development/compatibility evidence, not a green full suite. Total measured wall6.856223022s. No hazardous checkpoint_profiles/full suite.

## Candidate custody

Base `7ac02c7f01cc59b43ade0c98b55be59ea750af41`. Tree-list SHA256 `7ba370f64d07b47c3a20861bafb917f4030c9e916efa52e3445c1a44951259e1`; manifest SHA256 `a858e1c173fff09a1b83c6adce2c341a7bf8b08f12aabe79decbc48819d19629`. Exact candidate bytes, base bytes, candidate.sha256, candidate.patch and manifest.json under `work/records/2026/11/finding-v12-monitor-running-deadlines/evidence/implementation-385429/`. Only these 8 paths change:

- v12/python/src/baton_v12/job_manager/documents.py
- v12/python/src/baton_v12/job_manager/projection.py
- v12/python/tests/job_manager/test_status.py
- v12/python/tests/tools/test_job_observation.py
- v12/python/tests/tools/test_job_viewer.py
- v12/python/tools/job_observation.py
- v12/python/tools/job_viewer.py
- v12/python/tools/stack.py

Potential overlap with W385424: observation/view/status/projection and associated tests. No merge/import attempted. Human owns Git; coordinator must arrange independent and joined review. Required evidence is in the dossier, not only scratch. Candidate tests can be reconstructed from base plus packet; the unchanged vector fixture is at its existing canonical repository path. The temporary complete source copy is at work/scratch/w385427/candidate; it is not the sole copy of candidate changes.
