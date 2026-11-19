# W385263 Option A implementation handoff

2026-11-19, baton.codxpc (impl), E385275; approval M385273 and ownership M385276. **Complete, awaiting independent review.** No unresolved implementation blocker or owner decision is needed for this candidate. Options B/C remain unapproved.

## Outcome and behavior

Status and monitor now share pure Job outcome, failure/gate, operation and activity interpretation in tools/job_observation.py. The monitor includes the same aggregate outcome and typed fault reasons as status. Status now shows attempt identity, reported operation and existing native-byte activity. Operation facts are labelled reported with unverifiable attempt association where the source cannot prove it; they are not claims about the current provider tool.

Both readers use the inclusive 15-second freshness policy, independent of poll frequency. Monitor file reads retain publication mtime from the same open descriptor as the bytes; both consumers check observation and publication ages. Rereading or freshly publishing old data cannot refresh its source time. Activity has its own original count/time: zero is known, absent/foreign-attempt activity is unknown, and terminal activity keeps its historical absolute timestamp. Existing Job/runtime details, noncanonical/stale qualifications and service-health checks remain. No JSON schema, publisher, activity producer, CLI invocation or live-instance change; no new collector/log parser/TUI.

Resolved gaps: 2-second monitor versus 15-second status disagreement; monitor ignored publication age; duplicated outcomes/gate/fault interpretation; known zero shown unknown; viewer accepted activity from a different attempt; status lacked existing activity/operation summary. Source parsing for freshness is shared, including UTC interpretation of timezone-less timestamps.

## Candidate and provenance

Canonical dossier: work/records/2026/11/finding-v12-shared-work-liveness.
Candidate: candidate-option-a/manifest.json, SHA-256 ffbc3191040403ca37b8d92cce2a85ca5ce5d08d00239a3be9e2d0e11b23e9f3.
Base checkpoint: bcb5e5416f0accfe0551c7a8aa7d71305e66a0e4. Exact base bytes: evidence/option-a/base/. Candidate bytes: candidate-option-a/files/. Every changed path has its base/candidate hash in the manifest; new paths have null base. tracked.diff is a convenience diff and excludes new untracked files; manifest/files is the complete candidate.

Changed product/test/document paths:

- v12/python/tools/job_observation.py — new pure common interpretation extracted from existing consumers.
- v12/python/tools/job_viewer.py — shared interpretation, outcome/operation rendering, publication age and fixed policy.
- v12/python/tools/stack.py — shared outcomes/stage/activity/freshness; service checks unchanged.
- v12/python/tests/tools/test_job_observation.py — new cross-consumer, identity, schema, clock and pure-dependency proof.
- v12/python/tests/tools/test_job_viewer.py — approved zero/freshness expectations; matching activity-attempt fixtures; shared-module import guard.
- v12/python/JOB-VIEWER.md — updated behavior contract.

Existing tests/tools/test_stack.py was reserved but needed no edits. Three former interval-policy tests are replaced by a cross-interval/inclusive-boundary matrix. Zero is removed from invalid-count cases because the owner selected known-zero semantics; unknown, malformed/oversized counts, foreign-attempt and missing data coverage remains. Fixture attempt IDs are now explicitly matched; separate negative coverage proves mismatches remain unknown. Existing no-action import checks include the shared module, whose own dependencies are checked as standard-library-only/no IO calls.

Decision files: FINDING.md owner Option A approval, CLI-OBSERVABILITY-ADDENDUM.md Option A, PLAN.md and owner-pinned v12/DESIGN.md OBS-2. DESIGN.md is a hashed read-only prerequisite, not an authored candidate path. Existing unrelated pilot records and owner DESIGN changes were preserved; no Git mutation.

## Verification and accounting

Focused final command from v12/python (timeout 180 seconds):

```sh
TMPDIR=/home/sl/src/baton/work/scratch/w385263-tests PYTHONPATH=src:. timeout 180 python3 /home/sl/src/baton/work/records/2026/11/finding-v12-shared-work-liveness/evidence/option-a/run_focused.py
```

Final: **299 tests, 0 failures, 0 errors, 0 skips; 34.127696 seconds measured**. Suites: test_job_observation, test_job_viewer, test_stack, test_worker_visibility. Covers both outcomes/failures/gates, operation qualification, zero/unknown/foreign activity, old activity in fresh snapshot, terminal times, exact 15-second observation/publication boundary and rereads, unchanged schemas, pure-model dependency boundary and existing deterministic local lifecycle/visibility compatibility. No engine/provider test or deployment performed. Expected negative-fixture diagnostics appear on stderr; test outcomes are in focused.log/json. git diff --check passed.

All development iterations retained:

| Evidence under evidence/option-a | Tests | Failures | Errors | Skips | Measured seconds |
| --- | ---: | ---: | ---: | ---: | ---: |
| first.log | 294 | 29 | 1 | 0 | 42.458 |
| second.log | 87 | 9 | 0 | 0 | 7.234 |
| focused-pre-final.log/json | 299 | 0 | 0 | 0 | 34.209723 |
| focused.log/json | 299 | 0 | 0 | 0 | 34.127696 |

First execution followed an editing-helper cwd error, so it still exercised old test expectations. Failures exposed stale policy fixtures, foreign-attempt fixture data, import/constant compatibility and new width behavior; all corrected before final acceptance. A negative publication-age rule introduced in the first draft was removed to preserve existing clock behavior. Second run exposed remaining old zero/drill-down expectations and a too-long combined attempt/operation row; these were corrected without dropping width or defect coverage. Unittest failure counts include subtest failures. Sum of reported suite/runner durations is approximately 118.029 seconds, not total wall time for the implementation. First-run process warning PID 2153366 was checked after suite exit and no longer existed. Final run had no such process warning.

## Limits and handoff condition

This is deterministic source verification, not a newly built/installed/live monitor proof. Existing activity may be unavailable, especially with reused HOME; quiet does not mean stuck and byte growth does not prove useful progress. Reported exchange operation lacks independently verified attempt binding and is labelled accordingly. Existing clock behavior clamps displayed negative ages; broader clock-anomaly policy is not added. CPU/memory, semantic transcript parsing, CLI streaming, new envelopes and collectors remain excluded.

Independent reviewer should inspect the exact manifest-bound files against approved Option A and recorded baseline. Owner retains Git. Protocol report/pass/release receipts are retained under evidence/option-a/.
