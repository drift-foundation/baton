# Plan

1. [done 2026-08-19] Revalidate the observed direct-versus-linked route
   mismatch against the current projection code and W230 tests. The cause is
   exact; every other endpoint resolution in the projection was swept for the
   same omission. See `PROGRESS.md`.
2. [done — landed under W128 on 2026-08-19] Make the shared linked-Work
   summary pass the far Work's durable selected route into endpoint
   resolution. W128's own acceptance boundary required direct and linked
   views to agree, its test failed on this defect, and the overlap was
   reported in that handoff rather than absorbed.
3. [done] Dependency-both-directions, containment both ways, BOTH non-gating
   relationships from both sides, a sweep over every relationship `far()`
   serves, default-route and no-alternates controls, a terminal neighbour,
   the withdrawn-alternate case, and the console neighbour view.
4. [done] Focused tests and the complete v11 gate, then returned for
   independent review.

**Status — 2026-08-19:** awaiting review. One question for the reviewer:
whether this record's disposition should account for the correction having
landed under W128.

