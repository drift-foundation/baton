# Plan

**Status:** queued as a same-schema TUI projection correction; do not interrupt
active W4.

1. Revalidate every TUI Work-table surface against the structured Current/Next
   projection and define the explicit unresolved marker.
2. Render resolved route handles in both columns; keep null as `-` and retain
   complete endpoint facts in JSON and details.
3. Cover differing kind/route names (`feat` → `rview`), current implementation,
   review return, null Next, retired/unresolved endpoints, linked external Work,
   responsive widths, and JSON/TUI parity.
4. Run focused tests and `just test-v11`, then return for independent review.
