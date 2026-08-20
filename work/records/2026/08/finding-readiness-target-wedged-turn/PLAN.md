# Plan

**Status — 2026-08-20:** independent review round 2 is clean. The round-1
authoritative-turn race, shutdown timer leak, and tautological assertion were
corrected and verified in `review-2026-08-20T15-30-05Z.md`.

1. [done] Capture the W2938 missed-review episode from canonical readiness,
   dispatcher, runtime lease, and target-session evidence.
2. [done] Rule the v11 recovery policy for a loaded target whose active turn
   is waiting indefinitely for input.
3. [done] Implement target health/queue diagnostics and safe recovery or
   explicit failure without approving agent commands: `respondError` and
   `interruptTurn` on the client, `#denyAndRecover`/`#interruptBlocked`/
   `#clearBlocked` in the bridge, the bounded `approvalRecoveryMs`, a `#drain`
   that refuses while blocked, and a `statusSnapshot` that distinguishes
   loadable-and-idle from loaded-but-unable.
4. [done] Focused multi-event, recovery, redelivery, identity, and
   lifecycle-status regressions: ten cases in
   `tools/codex-event-bridge/test/event_bridge.test.mjs` (147 passed), plus
   the superseded runtime-publisher case corrected in place. Full v11 gate:
   2746 parallel, 52 serial, 55 ACP.
5. [done] Independent review round 2 passed before deployment.
