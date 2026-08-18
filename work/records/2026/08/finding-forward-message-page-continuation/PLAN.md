# Plan

Tracked as independent v11 Work W130. It is not a W2 capability-gate blocker.

1. [done] Reproduce the exact-limit empty continuation through canonical
   JSON with a focused regression.
2. [done] Apply the bounded `limit + 1` proof-row rule to forward Thread
   Message pagination without changing ordering or cursor exclusivity.
3. [done] Cover short, exact, overflow, chained-page, and retry cases.
4. [done — independently reviewed 2026-08-17] Run focused and workflow tests;
   the 14-test independent gate passed. The complete combined v11 gate remains
   W159's responsibility while its later request-default change is active.
