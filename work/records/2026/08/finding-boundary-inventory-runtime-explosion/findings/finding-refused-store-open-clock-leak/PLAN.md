# Plan

1. [done] Reproduce and trace the leaked connection independently through the
   boundary driver and the focused store test.
2. [done] Revalidate the prior clock-fault ruling and widen the existing
   close-on-error lifetime through post-construction `_now()` validation without
   translating the configured clock's own exception.
3. [done] Add a focused descriptor/connection-lifetime regression for
   refused clock answers and clock-raised faults.
4. [done; independently signed off] The focused store and W54182 probe-driver
   gates pass under `-W error::ResourceWarning`; commands and results are in
   `PROGRESS.md`. No aggregate inventory was run. Independent sign-off:
   `review-2026-08-31T16-28-33Z.md`.
