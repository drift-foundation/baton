## Current: independently accepted, human checkpoint pending

See review-2026-11-19T15-48-26Z.md. All eight candidate paths verified. Live deployments unchanged.

# Plan

1. Claim, revalidate diagnosis, read v12/DESIGN.md and reproduce deterministically.
2. Pin exact host offer/cancellation/delegation and test path ownership before editing; codexpc owns this correction and PROGRESS, K holds host edits. No labels CLI/create feature changes or installed instance changes. Necessary paths bounded by outcome, not a rigid file list.
3. Implement positive-refusal retirement and fenced overdue accepted-offer settlement with correct Job-state propagation. Unknown/transient outcomes must reconcile actual possibly committed claims, not fabricate refusal.
4. Verify claim refusal, overdue cancellation, repeated ticks/restart, successful/uncertain claim races, no duplicate effects/launch after fence, no false claim adoption from terminal settlement. Real owner APIs/stores with deterministic boundaries; no live instance or direct operational SQL.
5. Hand off candidate digest, paths, focused commands/counts/durations and limits to baton.decide for independent review; human checkpoint only. No full suite, packaging build or live run selected.

Native labels Job continues independently in installed native-labels-4 at a62bc9a3. Parent relationship to W321608 requires owner action; standalone ledger Work and canonical binding are established, no scheduling edge claimed.

## E385224 owned paths and implementation boundary

Codexpc exclusively owns the following correction paths while K holds host edits (native labels remains isolated):
- `v12/python/src/baton_v12/worker_manager/offers.py`
- `v12/python/src/baton_v12/job_manager/delegation.py`
- `v12/python/src/baton_v12/job_manager/manager.py`
- `v12/python/src/baton_v12/job_manager/scheduler.py`
- `v12/python/tools/stage_execution.py`
- `v12/python/tests/job_manager/test_accepted_offer_retirement.py`

Use existing authority settlement, never local expiry of accepted claims. Positive refused/precondition claim answers may request retirement; ambiguous/unknown/transport answers remain reconcilable. Per-tick overdue settlement reaches only bound admitted live episodes through their selected worker, then republishes owner states before adoption/launch. Terminal offer settlement receipts are refused claims, not successful adoption. No schema/spec or labels changes. New focused regression module will drive actual stores/owner APIs and deterministic Authority boundary; existing focused offer/recovery/cancellation/pool suites preserve adjacent behavior.

Additional owned test path: `v12/python/tests/tools/test_stage_execution.py`. Update the three wrong-route containment classes to assert permanent positive-refusal retirement, no false success or revival, released logical capacity, and continued independent Job progress.

Additional owned path: `v12/python/tools/parallel_test.py`, solely register the new isolated regression module in the parallel registry as TESTING.md requires.

## Current state

Steps 1–4 complete; step 5 candidate/evidence prepared in HANDOFF.md and candidate/manifest.json, returning to baton.decide for independent review. No deployment or full-suite acceptance claimed.
