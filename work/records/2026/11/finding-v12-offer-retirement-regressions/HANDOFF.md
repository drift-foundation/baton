# W385251 correction — ready for independent review

Participant baton.codxpc, role impl; claim E385254. Base checkpoint `70c12fd642439961ead260211875a1bb348e2641` (includes accepted W385222 and status UX). Candidate manifest SHA-256 `71eb233ef65af9737818c64109f622dec12e19251479d5e4e4226a3a7a9892b1`; patch SHA-256 `21564236fda2495b56a2e9f7327d7e5753c872cafe0db463ae41ab5d6e31847c`.

## Changed behavior and resolved reports

1. Product fix: `PooledManagerOperations.settle_offer` skips released historical allocations. It never acts through a replacement worker to settle a past generation. `_worker` now refuses an unavailable binding by name instead of throwing KeyError. Live prior generations keep exact routing; uncertain/recovery-required allocations remain held. Three new routing regressions cover retired history, live prior generation and missing live binding. This resolves the three reported stage-execution failures in accepted-PR successor, newly created successor and restart-after-pool-advance paths.
2. Fixture correction: dogfood arc grants and its opened ControlStore now use one frozen fixture clock. The prior fixture mixed August acceptance with wall time, so deadline enforcement correctly retired it before activation. Keep real claim/activation and exact activate → materialize → start assertions, adding an assertion for the intended injected stop-before-engine refusal. This resolves the dogfood failure and its nested next-run/operator verification gate failures (including hostile ambient imports).
3. Selected behavior assertions: task delivery and retry lineage now require a permanent positive-route-refusal receipt in the ended episode, not indefinite offered/deferral state. Preserve first task bytes, independent task identities, handoff reason, released line and no second runtime/input delivery. This resolves the two remaining route-expectation failures while preserving accepted retirement, unknown-claim reconciliation and no-launch-after-fence coverage.
4. Separate pre-existing inventory correction: all three actual consumers synthesize the labels FINDING.md/PLAN.md in temporary checkouts. Add the exact synthetic path with named consumer rationale in test_parallel_runner.SYNTHETIC_RECORD_PATHS. Do not declare real dossier bytes as CONSUMED_INPUTS: tools/parallel_test.py is unchanged. This explicitly corrects the handoff's initial consumed-input hypothesis, as recorded in FINDING and M385255. Inventory enforcement still runs and passes.

All nine recovery-related failures and the separate inventory failure from K's accounted baseline are resolved in the joined run. No unresolved implementation failure or product decision remains; independent review is still required, including review of the corrected inventory classification.

## Exact candidate and ownership

Changed paths (six):
- `v12/python/src/baton_v12/job_manager/scheduler.py`
- `v12/python/tests/job_manager/test_scheduling.py`
- `v12/python/tests/tools/test_dogfood_operator.py`
- `v12/python/tests/tools/test_job_task_delivery.py`
- `v12/python/tests/tools/test_parallel_runner.py`
- `v12/python/tests/tools/test_retry_task_lineage.py`

Canonical dossier: `work/records/2026/11/finding-v12-offer-retirement-regressions`. Selected scope and classifications: FINDING.md; ownership/current state: PLAN.md; author account: PROGRESS.md. Candidate bytes: candidate/files/; exact path/base/final hashes: candidate/manifest.json; patch: candidate/candidate.patch; base bytes: evidence/base-paths.json. `evidence/compatibility-source.json` binds the combined tested source. `evidence/final-byte-check.json` confirms no candidate or K-file drift through verification.

K's accepted five paths (tools/pool.py and tests/tools/test_pool.py, test_bootstrap.py, test_single_worker.py, test_connected_creation.py) match K's candidate-layout-selection.sha256 and evidence/k-preserved.json byte for byte. None was edited. No host Git/index/history mutation.

## Focused and accounted results

- Focused final: **294 tests passed, 0 failures/errors/skips**, unittest 152.031 seconds; measured wall **152.366 seconds**, timeout 180s plus 10s kill grace. `evidence/focused-final.log` and `evidence/focused-run.json` contain results and exact argv/environment. Includes new routing cases, accepted-offer retirement, offered/committed/uncertain races, scheduling, the corrected fixtures, successor/restart compatibility and inventory.
- Accounted **tools-pure** combined compatibility: **collected 3420, executed 3420, passed 3420**, failures 0, errors 0, optional/required/fixture skips 0, fixture errors 0, duplicates 0, unaccounted 0. **211.612 seconds wall**, 8 workers, timeout 900s plus 10s kill grace. `evidence/tools-pure-final.log`, `evidence/tools-pure-ledger.json`, `evidence/tools-pure-run.json`. This includes K's five accepted layout paths and the nested operator-verification/next-run gates. The ledger supports these selected-group claims only, not full-suite acceptance.
- Re-run selections: `evidence/run_checks.py focused` / `tools-pure`; prepared Python3.13.7, PYTHONPATH=src:., TMPDIR and BATON_V12_DISK_ROOT=/var/tmp, PYTHONDONTWRITEBYTECODE=1.
- Current-tree baseline reproduced 4 failures/1 error across 7 tests in 4.323s (`evidence/baseline-current.log`). K's retained baseline/isolation evidence is referenced from FINDING and its original CORRECTION.md; not overwritten. Earlier import/fixture-author failures remain in focused-1/focused-2 logs. Focused-3 was interrupted and is not acceptance evidence. Owned-path `git diff --check` passes; K's pre-existing trailing blank line is preserved with its accepted bytes.

## Execution deviation and limits — disclosed

I mistakenly selected the engine-containing test_negative_race_endings module in focused-3. It built a disposable fixture image and ran Docker cases despite the no-engine/build scope. I interrupted the run when identified, retained the log and fixture identity, then removed the exact exited container, unique fixture image and fixture root; absence was checked. No broad prune, production-instance operation or live-provider call. Build cache may remain. Exact disclosure and cleanup: `evidence/EXECUTION-DEVIATION.md`, `evidence/accidental-engine-fixture.txt`, M385256. This was an execution error, not authorized acceptance evidence; it must remain visible to independent review.

Final verification uses only the deterministic named cases and accounted tools-pure registry. No full suite, packaging/combined bundle acceptance or next native kickoff is claimed. The next bundle/live attempt remains held pending independent acceptance and its existing selection. Return to baton.decide and release the claim; do not self-close.
