# Plan

1. [done] Reproduce the post-reboot 77/78 result and identify the ambient
   sample-state dependency.
2. [done] Revalidate the focused test against the placement authority and pin
   the owned temporary missing-marker fixture boundary in `FINDING.md`.
3. [done 2026-08-21] Isolate the combined entry-point case with its own
   temporary config/root and guaranteed fixture cleanup; make no placement
   authority or sample-state change. `v12/test/placement.test.mjs` is the only
   file touched.
4. [done 2026-08-21] Preserve distinct absent-root and missing-marker
   coverage, then run the complete self-contained v12 gate from a clean state:
   78/78 with the sample root absent, existing-unmarked, and existing-owned.
5. [done 2026-08-21] Independently review before including the v12 subtree in
   a commit. Accepted in `review-2026-08-21T13-38-10Z.md`; the complete gate
   passes 78/78.
