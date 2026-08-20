# Plan

1. [done] Confirm the current `wait_actionable()` SQLite projection loop and
   its 50 ms empty-read sleep.
2. [done] Record the approved fixed 1,000 ms cadence and unchanged timeout
   semantics.
3. [done 2026-08-19] Revalidate all readiness timeout/deadline tests, then change only
   the internal polling cadence.
4. [done 2026-08-19] Add focused regressions for zero, sub-second, multi-second, and
   concurrent-action waits without making the gate sleep in wall time.
5. [done 2026-08-19] Run focused plus complete v11 gates and obtain
   independent review.
