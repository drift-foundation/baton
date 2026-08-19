# Plan

1. [done 2026-08-19] Revalidate the `pass` authorization boundary and
   route-selection invariants against the latest authority. `pass`'s handler
   gate is right and unchanged; what was missing is that its reasoning has no
   force when nobody holds the Work.
2. [done] The `reroute` transition, its CLI/JSON surface, and its
   advertisement in `available_transitions` while unclaimed.
3. [done] Authority, race (both orderings), event-journal,
   direct-projection and linked-projection regressions — the last of which
   found and fixed a linked-view defect W30 named first; see `PROGRESS.md`.
4. [done] Focused verification and the complete v11 gate, then returned for
   independent review.

**Status — 2026-08-19:** awaiting review. One question for the reviewer:
whether W30's remaining scope is now empty.
