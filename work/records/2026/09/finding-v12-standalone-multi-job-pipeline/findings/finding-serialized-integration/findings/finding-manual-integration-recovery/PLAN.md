# Plan

1. [complete after final re-review] Revalidate K's accepted runtime/execution boundaries and enumerate the
   minimum retained facts an operator needs.
2. [complete after final re-review] Implement the disjoint status/diagnostics projection for one typed held
   condition without changing shared contracts.
   Routine status must not copy an arbitrary blocked-account reason: expose a
   leaf-owned safe classification and keep untrusted reason/detail behind the
   retained evidence digest and locator.
3. [complete after final re-review] Add explicit operator-action validation that first proves the old runtime
   cannot mutate; do not select or automate a recovery policy.
   Bind abandonment to one last manager snapshot: a newer `uncertain` state
   must refuse rather than be observed and ignored. Complete delivery,
   coordinator and answer validation before that snapshot; perform no fallible
   projection or external read between it and `abandon_lease`. The delivery
   validation and safe answer boundary are already corrected.
4. [complete after final re-review] Add focused interruption and
   no-automatic-action regressions, including quiescent-to-uncertain manager
   re-observation, invalid delivery before abandonment, safe already-blocked
   status, and successful abandonment replay.
5. [complete after final re-review 2026-09-06] The first review
   `review-2026-09-06T15-53-10Z.md` requested one P0 and two P1 corrections;
   `review-2026-09-06T15-59-32Z.md` retained the P0 until all fallible status
   work moved before the authoritative runtime cutpoint. The final review
   `review-2026-09-06T16-04-05Z.md` signs off all corrections with no findings.
