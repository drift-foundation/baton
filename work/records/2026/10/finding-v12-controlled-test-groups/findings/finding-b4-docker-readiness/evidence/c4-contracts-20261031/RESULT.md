# C4 contract corrections — W384944 / E384962

Implemented the two required corrections from review-2026-10-31T02-33-07Z.md in `v12/python/tests/manager/test_integration_worker.py` only. The unsupported launch case now selects /999, proves it is unsupported, and retains status 2, launch-error classification, presented/supported generations and another-generation diagnostic assertions. Supported envelope parsing coverage and product reader are unchanged.

The clean provider result remains an exact closed-key assertion, now including seconds_bound=3600 and seconds_bound_source=worker-default. Traced invoke_provider through the provider result and _resolved_bound: this fixture supplies no Job context, so the adapter's PROVIDER_SECONDS default (3600) and worker-default origin apply. No assertions were weakened.

Stable allocation: a8cbc9745d1eff51bcfb04d2fe4bb96a5ea3b12d; all 1133 manifested paths verified before transfer, with only the allocated test different. Full source hashes before/after each run show no drift. Shared file still matched accepted f5a443a9437992daaa7971209748c6f1edb0adb8982246216d99256614bb2a50 before transfer. Candidate SHA-256: a2ffd5dce0c41fb37c1f54f45589e992ad18bb3c9e2d9dd7df2e8a16a8c713f3. Exact base/candidate/diff retained here.

Prepared interpreter, deterministic provider seams, just test-one: affected two cases passed (0.010s unittest, 0.2640s command wall); entire module 83 passed, zero failures/errors/skips (17.885s unittest, 18.1329s command wall). Total measured command wall 18.3969s. Logs and summaries enumerate every collected/started ID with no missing or duplicate IDs. Both new run roots empty and removed.

Both prior exact roots matched their inventories (937 and 370 entries) and were removed after checking task ownership and live references. Four inventoried credential fixture links in the second root pointed inside that root and were unlinked without following. Initial conservative scans stopped before mutation on protected infrastructure and symlinks; follow-up inspection classified them explicitly. No task executor references were found; original executions had exited. Protected systemd/PAM/SSH processes predating the fixtures could not be fully inspected; recorded in cleanup.json. Original inventories remain intact.

No other product/test paths changed; no Docker, build, live provider, broad suite or Git mutation. This establishes the allocated snapshot module only; joined current-tree/B4 acceptance remains pending independent review and parent coordination.
