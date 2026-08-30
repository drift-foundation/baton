# Plan: failed managed turn misses a secondary claim

1. [done 2026-08-29] Record the W39357/W39770 live incident and distinguish it
   from W4303's original-action orphan correction.
2. [in progress 2026-08-29] Bound W39868 as the high-priority tuner-lane
   correction. Recover the exact live W39357 claim through the configured
   operator path.
3. [done 2026-08-29 by `baton.tuner`] Extend failed-turn settlement to
   reconcile the participant's canonical claim slot when the original
   delivered action is released.
4. [done 2026-08-29 by `baton.tuner`] Add original-claim, secondary-claim,
   no-claim, reconnect,
   completion-order, duplicate-completion, incident, runtime-publication, and
   retained-queue regressions.
5. [verification done 2026-08-29; next, independent review] Focused bridge
   tests and the complete v11 gate pass. Request independent review, then
   deploy before relying on the correction.
