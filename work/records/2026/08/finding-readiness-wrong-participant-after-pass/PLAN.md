# Plan

1. [done 2026-08-20] Reproduce the false wake across queued-after-pass and
   held-by-another-participant episodes; locate whether projection, producer,
   dispatcher, or episode revalidation owns it.
2. [done 2026-08-20] Drop stale or wrong-participant Work actions before external
   emission without weakening canonical authorization.
3. [done 2026-08-20] Cover pass/claim/pass races and legitimate new-episode delivery.
4. [done 2026-08-20] Independently review focused readiness tests and the v11 gate. The first review's target-identity finding was corrected and signed off in `review-2026-08-20T02-22-59Z.md`.
