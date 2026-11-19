# W385263 Option A registry correction — ready for delta review

2026-11-19, baton.codxpc, claim E385282. Authority M385280; ownership M385283. Response to review-2026-11-19T18-59-06Z.md. **Correction complete; independent acceptance pending.** No blocker or additional owner decision remains.

## Delta and classification

Registered `tests.tools.test_job_observation` in `v12/python/tools/parallel_test.py` PARALLEL_MODULES with isolation rationale. The existing package mapping assigns it to tools-pure. Tests use pure in-memory observations and case-owned TemporaryDirectory snapshot files, without shared fixtures/resources, engines, providers or network. The correction is four added registry/comment lines; no test assertions or product behavior changed.

All six original candidate hashes remain byte-identical. The initial 299-test evidence is retained and applies to those unchanged files; it is not relabelled as a rerun of the entire candidate. No full suite, build, engine/provider operation, deployment or Git mutation occurred. K's native-labels diagnosis and owner DESIGN changes are untouched.

## Refreshed candidate

Canonical dossier: work/records/2026/11/finding-v12-shared-work-liveness.
Current candidate: candidate-option-a-registry/manifest.json.
Manifest SHA-256: 7c1da2d2acc6aea1b3fd3e65b02eb6ab8ec21379ddc9462d361c72ad4d52c16f.
Base checkpoint: bcb5e5416f0accfe0551c7a8aa7d71305e66a0e4.
Prior manifest: ffbc3191040403ca37b8d92cce2a85ca5ce5d08d00239a3be9e2d0e11b23e9f3 (preserved in candidate-option-a/).

Seven exact paths in the refreshed manifest/files:

- v12/python/tools/job_observation.py
- v12/python/tools/job_viewer.py
- v12/python/tools/stack.py
- v12/python/tests/tools/test_job_observation.py
- v12/python/tests/tools/test_job_viewer.py
- v12/python/JOB-VIEWER.md
- v12/python/tools/parallel_test.py — the sole correction delta.

Candidate files and base hashes are bound by manifest.json. The original six baseline files remain under evidence/option-a/base; registry baseline is evidence/registry-correction/parallel_test.py.base. registry-delta.diff is the review delta. tracked.diff excludes new untracked files; manifest/files is the complete candidate. Prior handoff preserved verbatim in evidence/registry-correction/prior-HANDOFF-OPTION-A.md.

## Focused verification

Whole-tree read-only registry and group checks: **188 registered / 188 discovered modules, complete**, 0.004536 seconds. This checks metadata, not execution of all modules.

Runner regressions: **72 tests, 0 failures/errors/skips**, 16.334619 seconds (`tests.tools.test_parallel_runner`).

Real runner collection/sharding/execution/accounting, explicitly selecting only tests.tools.test_job_observation: **7 collected and 7 executed**, zero failures/errors/skips and no missing, duplicate or unexpected IDs; **0.333022 seconds** including cleanup. Result directory removal and no live tracked processes verified. Uses the full validated registry with the existing collect(modules=...) selection, not a replacement registry or full-group run.

Command from repository root:

```sh
TMPDIR=/home/sl/src/baton/work/scratch/w385263-tests PYTHONPATH=/home/sl/src/baton/v12/python/src:/home/sl/src/baton/v12/python timeout 180 python3 work/records/2026/11/finding-v12-shared-work-liveness/evidence/registry-correction/verify.py
```

Evidence: registry.json, runner-tests.log/json, accounted.json, accounted-progress.log and accounted-raw/ under evidence/registry-correction/. Exact reproducible wrapper: verify.py. git diff --check passed. No installed/live behavior claim; original Option A observation limitations remain.

The first wrapper attempt also passed 72 runner regressions (16.332506 seconds) and seven shard tests, then failed its evidence cleanup assertion with AttributeError because shutdown resets result_root to None. This was a wrapper bug, not a test or registry failure. Preserving the pre-shutdown root path fixed the assertion; the full bounded wrapper was rerun successfully above. Original logs, wrapper and error note remain under first-verification/. First accounted wall duration was not recorded; per-child reported collection 0.16 seconds and execution 0.20 seconds are not presented as full wall timing. No failed evidence was discarded.

## Review condition

Delta review should confirm registry placement/isolation, complete 188-module registry/group validation, exact seven-test accounting and seven-path manifest, with the original six bytes unchanged. HANDOFF-OPTION-A.md now denotes this refreshed candidate; FINDING/PLAN/PROGRESS and latest review identify the authorized scope. Pass to baton.decide for independent review, verify release, retain receipts under evidence/registry-correction/.
