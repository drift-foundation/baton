# C2 progress

## 2026-09-16T00:32:40.733122+00:00 — baton.tuner claim182279

Owner182276 scope pinned before implementation; C1 accepted shared hashes and all recorded dependencies revalidated. BASE-182279 preserves the baseline. Beginning counted recomposition and independent invalid-evidence checks. Prior cumulative author211.3880788211536s and reviewer104.8836736070516s preserved separately; no new test execution yet. Missing initial PROGRESS.md recorded in FINDING.

## 2026-09-16T00:43:18.780508+00:00 — baton.tuner claim182279 complete, awaiting independent review

CANDIDATE-182279.json SHA256 055b765cf539d472fda98dabc173973162214babbd51a97b758d70499086b628 binds the exact two-file extension of the independently accepted C1 bases. EVIDENCE-182279.json SHA256 9091bf68a01b80484af3389f9652d2780eb3da44e464550e911058bbc644af27 binds all nine current runs and final exports. HANDOFF-182279.md records implementation, tests, candidate provenance, limitations, failures and cleanup.

Observed final C2: boundary ticks3/4, incarnation correction-0 to correction-3, old store handles closed and fresh composition over the same durable paths. Initial runtime already destroyed/result retained. Provider and engine old-use counts are each1 before, immediately after, after a scheduler tick and at final completion; revised use has exactly1 of each. The actual correction/review/managed import/final path completes in23 ticks. This proves manager recomposition in one process after a durable result, not live-runtime survival or host/power-loss exactly-once.

Final runs6–9 pass15 tests: CountedReopen2, CountedReopenInvalidEvidence6 with15 separately labelled corruptions, and unchanged C1 positive2/negative5 with13 corruptions. Both streams reject duplicates separately, including the fresh correction and a use relabelled as another attempt. The18 predecessor artifacts still validate at their unchanged digests without schedule execution. No product source changed. Exact C1 classes/assertions preserved; only the shared harness gains optional counting/reopen, exact actual input observations and cache-independent mount evidence.

All nine groups absent, no timeout, source hashes stable; final runs match candidate. Initial extractor/cache and overly deep contract-digest mistakes are preserved in runs1/2 and corrected only in the authorized harness. Actual engine operation is represented by its --name input operand, not the nonexistent draft label. New author verification22.91245227609761s, cumulative234.30053109725122s; reviewer104.8836736070516s separate. git diff --check and exact zero-fuzz patch reconstruction pass.

This explicitly supersedes in-progress C2 as the current action. Release the two exact candidate paths to baton.feat for independent review, then baton.ops. No independent C2 acceptance, Work closure, parent joined acceptance or external release is claimed. All earlier decisions/evidence remain chronological history.
