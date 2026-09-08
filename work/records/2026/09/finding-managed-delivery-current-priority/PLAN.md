# Emergency correction plan — W119195

1. [done] Record observed inversion, source cause, live checkout provenance,
   owner emergency direction and promotion to High.
2. [done] Owner drain; snapshot119262 is paused with zero claims.
3. [authorized] Explicit emergency prompt claim exception granted by Slawomir.
   Dossier binding remains an ops action; it does not change implementation scope.
4. [done] Add focused dispatcher regressions in a new test file. Modify
   tools/codex-event-bridge/src/event_bridge.mjs within current canonical
   selection/revalidation; inspect ACP behavior before claiming shared coverage.
   Existing test assertions remain unchanged.
5. [done] Prove the inversion fails before the fix and passes after it.
   Run the bridge claim-slot, stale-episode and event-delivery suites for safety
   interactions, then the bridge package tests if the focused checks pass.
   Budget: approximately two minutes for the focused local campaign; no v12
   suite, live model turn or Docker operation is needed to prove queue ordering.
6. [in progress] Exact changes, test evidence and limitations recorded in
   PROGRESS.md; all442 bridge tests pass. Restart the
   drained managed stack to load the prepared checkout, inspect health, then
   owner resumes canonical dispatch. Review actual next claim; do not claim
   deployment success from passing local tests alone.
