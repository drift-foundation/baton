# Plan

**Status — first-cut rule confirmed 2026-08-18.** The live W5 → W6 → W101
stall demonstrates the scheduling gap. Implementation is authorized only for
the binary within-pool blocker preference pinned in `FINDING.md`; the broader
effective-priority model remains deferred.

1. [done] Confirm the first-cut within-pool blocker preference with Slawomir.
2. [done] Revalidate every canonical ordering surface and readiness
   consumer against the confirmed binary model.
3. [done] Implement one canonical blocker predicate without changing
   explicit priority or claimability.
4. [done] Add workflow tests for one blocking versus one free-standing Job,
   blocker removal, different explicit pools, parked/claimed exclusion, and
   JSON/TUI/readiness parity.
5. [done] Run focused and complete v11 gates and return for independent
   review.
