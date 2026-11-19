## Current — accepted, owner checkpoint pending

See review-2026-11-19T18-07-10Z.md. Joined source compatibility passed; packaging remains next after human checkpoint.

# Plan

1. Claim; revalidate exact failures against current tree and K retained baseline/isolation. Pin ownership.
2. Correct retained-generation worker resolution and dogfood claim behavior where defective; revise expectations only when selected retirement behavior warrants it. Preserve uncertain claims and physical runtime ownership.
3. Fix consumed-input declaration separately without weakening inventory.
4. Verify named failures and adjacent recovery paths; then accounted tools-pure group for joined compatibility. No full suite/build/live run.
5. Hand back exact candidate and evidence to baton.decide; no self-close or Git mutation.

## E385254 ownership and classification

Codxpc owns scheduler.py, tests/job_manager/test_scheduling.py, tests/tools/test_dogfood_operator.py, test_job_task_delivery.py, test_retry_task_lineage.py, tools/parallel_test.py and tests/tools/test_parallel_runner.py (all under v12/python), plus this dossier. K five paths are hash-pinned in evidence/k-preserved.json and will not be edited. Pin only changed paths in final candidate.

Retired released allocations must not invoke settlement through a successor worker. Live allocations keep exact routing and uncertain holds. Dogfood ordering fixture must use one controlled clock for grants and opened ControlStore; do not disable expiry. Wrong-route task/retry fixtures must assert terminal refusal and absence of execution, retaining task isolation/line-release/handoff checks. Inventory classification is being revalidated: the three named consumers each create FINDING/PLAN inside their own temporary checkout.

## Current state

Steps 1–4 complete. Step 3 revalidation established a synthetic fixture path, so the final inventory change is in test_parallel_runner rather than an invented parallel_test input; FINDING/M385255 explain the correction. Step 5: candidate ready, completion report in T385251 then pass to baton.decide. Evidence includes the execution deviation; independent review and next-run acceptance are not self-granted.
