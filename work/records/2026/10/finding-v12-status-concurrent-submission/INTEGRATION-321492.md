# Integration — baton.merge, claim321492, 2026-10-18

Imported the independently approved cumulative candidate from review-2026-10-18T07-32-54Z.md and evidence/review-321452/CANDIDATE.json. Read canonical handoff through E321490 and discussion T319114 through M319391; claimed at E321492.

Before any target mutation, the entire three-path set passed authority, immutable candidate hashes, cumulative patch digest, original-base bytes, target regular-file/non-symlink, owner-write and overlap checks. Current HEAD matched declared base9055843b5d258f5bfbb523815d034ee0c14075d6. TASK.md explicitly schedules regression additions to the existing status suite; independent review enumerates test_status.py and evaluates all additions without weakening existing assertions. FINDING/PLAN and the explicit integration handoff authorize this import.

Imported only:

- v12/python/src/baton_v12/job_manager/projection.py
- v12/python/src/baton_v12/job_manager/store.py
- v12/python/tests/job_manager/test_status.py

Content was written through checked existing file descriptors without custody modes or replacement. All three modes remained 0664. Final SHA256 values equal CANDIDATE.json. The complete resulting binary diff equals cumulative.patch byte for byte, SHA256 83dd800908bb32cb1c7f254b4345f8417b67d281141a6059107dda91f91d4a1c. Diff inspection confirms exactly the three approved product/test paths, 1018 insertions and70 deletions; git diff --check passes. Unrelated existing dossier changes were preserved. No staging, commits or other Git mutation.

Bounded deterministic integration verification:406 tests pass in3.230s against the actual imported working-tree Python sources. Exact package module names, temporary root, timing and transcript are in evidence/integration-321492/tests-short-path.json and tests-short-path.txt. Python3.13.7, bytecode disabled, explicit source/package import paths, unittest,60-second outer timeout; disposable short /tmp root removed by TemporaryDirectory. No live provider or Docker execution.

Preserved earlier verification outcomes: an initial top-level-module invocation ran253 entries with three relative-import errors (2.026s); package-qualified invocation ran406 with the previously documented long-path diagnostic assertion failure in unchanged test_store_readonly.py (5.367s). Correcting only the harness to package-qualified modules and a short temporary path produced the passing result. No test assertions changed. Total measured test-run time10.623s; process setup time is additional.

Both original provider attempts remain timeout/exceptional/unable, and formal adapter verification remains absent. Passing integration tests do not establish successful end-to-end provider completion or deployment.

Next: baton.decide / baton.slaw reviews the prepared diff and owns the pending human Git checkpoint. Suggested commit message: `v12: make Job status coherent across concurrent submissions (W319114)`. No commit has been made by this integrator. No further code correction or live rerun is needed for this bounded integration result.
