# Owner-selected reviewed-byte integration

baton.prompt, 2026-10-19. Owner M334597 selects human-plus-agent integration of candidate-333964-final under review-2026-10-19T17-25-12Z.md. No managed Handler claim was taken; this is the selected interactive integration, not implementation or independent review. Owner subsequently requests a Git checkpoint; staging/commit remain human-owned.

Preflight verified reviewed MANIFEST.json SHA25660bcecee17f0ff96827f16203e9eedcde01b02634c441c3d646881c1bb29bfab and all18 members, six candidate hashes, four regular owner-writable target files matching the exact reviewed base hashes, and absence of both new paths. No symlink parents or executable targets. W333486 was unclaimed and blocked on this prerequisite at snapshot334600; no active overlapping product edit was observed. Unrelated paired-context edits were preserved.

Imported only the six paths enumerated in CANDIDATE.json. All six post-import SHA256 values match the independently accepted candidate. Existing intake.py, test_attempts.py and test_tool.py have filesystem mode0664; attempts.py has0644. The first preflight's stricter filesystem0644 assertion refused before any writes; the corrected preflight verified regular owner-writable non-executable repository modes and preserved those modes on existing files. Both new files have0644. No custody read-only modes imported; Git non-executable mode semantics unchanged.

Bounded integration verification from v12/python, PYTHONPATH=src:., 45s per-run timeout:

`python3 -m unittest tests.manager.test_authoring_enforcement tests.manager.test_attempts.CancellationFencesBeforeItStops tests.job_manager.test_tool.TheStatusSurfaceMayReadIntegrationAndStillActOnNothing tests.job_manager.test_tool.TheRecoveryPassVisitsTheUNCERTAINTokensToo`

Result:72 tests PASS, unittest2.611s, command wall2.765966091s. git diff --check passes. This verifies imported bytes with deterministic fake boundaries and local process tests; no live engine/provider, pilot retry or deployment. Existing independent review evidence remains unchanged. No new source correction or test expectation change beyond accepted bytes.

Human checkpoint pending: `fix(v12): enforce isolated authoring deadlines and expiry`. No staging/commit performed by agent. W333735 remains open pending owner disposition; do not silently clear W333485/W333486 dependency gates. Later authoring packets must bind this accepted correction; old execution333532 remains forbidden. Diagnostics must rebase any overlapping intake.py/attempts.py candidate onto these integrated bytes with independent review; no overwrite or silent conflict resolution.
