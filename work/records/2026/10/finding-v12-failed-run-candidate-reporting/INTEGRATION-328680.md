# Reviewed-byte integration — baton.merge claim328680

Owner E328677 accepts candidate602d7c1401bb0903bc38c72c1d0f210eb8a2c62f per review-2026-10-19T02-17-47Z.md. Read current handoff through328680 and T321528 through326111, current scope/PLAN/PROGRESS, latest review and its referenced correction. No pagination remainder. Product verification and permission regressions are explicitly scheduled in accepted scope; newest review enumerates both changed existing test paths, the new test, and evaluates preserved expectations.

Before any import, checked the complete five-path set, candidate Git delta and exact blobs, original custody result/bundle/patch/verification hashes, byte-identical binary patch, reviewed base03b94fc80744671150cca1997712ee95a6537df5 and target HEAD4f344e602dac5cd4c234a075a31f39659d3b5f62. All four existing targets were non-symlink regular files, uid1000, owner-writable and byte-identical to reviewed base; new test absent; parents regular directories. No divergence at the affected paths, worker/Python source or supervisor subtree. Custody modes were not imported.

Imported only these five reviewed blobs:
- v12/worker/claude_agent.py (existing0644)
- v12/python/tests/manager/test_claude_agent.py (existing0644)
- work/records/2026/09/finding-v12-single-implementation-proof/baseline.py (existing0664)
- work/records/2026/09/finding-v12-single-implementation-proof/test_baseline.py (existing0664)
- work/records/2026/09/finding-v12-single-implementation-proof/test_candidates.py (new0644)

Final bytes and modes verified in evidence/integration-328680/final-paths.json. Diff inspected; tracked delta1244 insertions/25 deletions plus the reviewed new test. git diff --check and new-file whitespace check pass. No redesign or correction during import.

Selected unchanged focused verification argv passes192 tests, no skips, unittest7.883s / wall8.113917964s, ordinary disk-backed scratch and explicit credential-free environment. Exact command/environment/log in evidence/integration-328680/verification.json and verification.log. No broader suite or live provider/engine run. Historical cumulative time remains unknown.

Original run held/provider0/formal1 and its40 failures/20 errors remain unchanged; independent review reproduced those under descriptor TMPDIR and assigned the environment issue to W325695. This integration pass is separate evidence, not a clean original-worker-run claim. No deployed image or running supervisor was changed.

Human Git checkpoint pending. Suggested commit: `fix(v12): report retained failed-run candidates and effective timeouts`. Slawomir owns staging/commit and delivery disposition. W321776 remains gated on W321528 delivery; W325695 must rebind the eventual human checkpoint and coordinate overlapping worker/test ownership. No Git index/history mutation performed. Pass through baton.decide to approver baton.slaw.
