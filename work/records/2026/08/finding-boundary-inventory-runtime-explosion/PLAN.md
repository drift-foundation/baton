# Plan

1. [done] Record per-test timing and resource-growth evidence for the current
   inventory, isolating the 549-probe driver from unrelated assertion drift.
2. [done] Revalidate the repeated source-scan, probe-catalog construction
   and fixture-lifetime analysis against the current implementation.
3. [done] Implement the smallest correction that caches the immutable source
   snapshot and pure derived discovery projections, computes the key universe
   once, rebuilds only the now-cheap fixture-bound drivers per probe, and tears
   down every probe fixture immediately without changing inventory semantics.
   Do not retain today's catalog across fixtures: its closures capture stores,
   credential homes and ports. — `PROGRESS.md`, 2026-08-31.
4. [done] Add focused regressions for catalog construction count, fixture
   isolation, prompt cleanup on failure and deterministic diagnostics.
   `TheDiscoveryProjectionsAreBoundedAndImmutable` and
   `TheProbeDriverIsBounded`, each proved against the reverted shape.
5. [done] Route the inventory's surviving correctness failures — the 46
   owned-but-never-probed entries and the 3 probed-but-unowned ones — to
   bounded Work: **W54802**, filed as a `bug` to `baton.bug` with the full
   per-site list and a 2.3-second reproduction. And the revalidation of this
   item's slicing clause: the named, independently
   runnable slices it asks for already exist as W9707's
   `v12/python/tools/parallel_test.py` shards, where every `TestCase` class is
   one shard and the two whole-universe scan classes are split one test method
   per shard. With the driver at seconds rather than tens of minutes, the
   inventory no longer needs a slicing of its own; what remains actionable is
   the routing.
6. [done, within the bounds ruled at poke 54758] Compare the before/after
   inventory verdict, wall time and peak-resource evidence. The whole-module
   pre-correction rerun was terminated by supervision and is not to be
   restarted; the recorded 2,376.290-second W52800 run is the before
   measurement. Bounded parallel execution was not needed and was not used.
7. [done] The leaked refused-open handle is closed by W54881 and the false
   immutable-AST text is narrowed correctly.
   One regression gap remains: the shared-tree invariant test does not clear
   or recompute cached `_helper_returns()`, even though it walks the shared AST
   and is a member of `MEMOISED`. Make the test clear and recompute every
   derived member of `MEMOISED` after its before fingerprint, then return the
   same bounded slices; do not run the aggregate. Review:
   `review-2026-08-31T17-23-04Z.md`. Corrected: the case now derives its
   cleared-and-recomputed set from `MEMOISED` (every member except `_sources`)
   rather than from a hand-written list, so `_helper_returns` is covered and a
   projection added later is covered without an edit here. Measured on the
   walker rather than on `CacheInfo`, whose counters `cache_clear()` resets:
   the reverted form ran the shared-tree walker 0 times between fingerprints
   and the corrected form runs it once, and a mutation staged inside that
   walker is invisible to the reverted form and caught by the corrected one.
   The same three bounded slices were rerun with the unchanged five-failure
   verdict; no aggregate. — `PROGRESS.md`, third round.
8. [accepted evidence retained] The [P1] leaked refused-open handle from
   `review-2026-08-31T16-16-32Z.md` was contained as W54881, now closed
   satisfying. The [P2] false immutable-AST text and test name are narrowed as
   the supervision note required: the header comment, the `_sources()`
   docstring and the renamed
   `test_no_caller_can_poison_a_cached_derived_projection` now state only the
   invariant the snapshot actually has. Plan item 7 carries the remaining gap
   in that invariant's enforcing regression. No aggregate inventory was run;
   the focused gates and unchanged five-failure diff verdict are in
   `PROGRESS.md`, second round.
9. [changes requested] Independent review accepted the shared-tree regression
   correction. The offered adjacent issue is also within this Work:
   `test_the_package_is_parsed_once_however_many_projections_ask` still drives
   the same hand-written five-projection list. Its assertion would not change,
   but a future member of `MEMOISED` is invisible to its parse counter.
   Derive every member except `_sources`, assert more than five derived
   projections, and rerun only the bounded regression classes and focused
   arrival method. Do not run the aggregate or change semantic inventory data.
10. [done, after one held round] The item-9 edit was prepared and then held,
    because the review conditioned it on
    `tests/manager/test_boundary_inventory.py` being released and at that
    moment it was not: W39666 was active with `baton.codex` reviewing the same
    file, so a W54182 hunk would have landed in the diff that review was
    assessing. Asked at M55527 rather than decided unilaterally. A dependency
    edge on W39666 was considered and rejected: it would only have cleared
    when W39666 CLOSED, and what was needed was one sentence about file
    ownership.
11. [awaiting review] M55549 answered PROCEED NOW and W39666 was verified
    queued and unclaimed before the edit. The parse-once case now derives its
    projections from `MEMOISED` except `_sources` and asserts more than five.
    Staging a new reparsing `MEMOISED` member proves the point: the corrected
    form catches it and the reverted hand-written form does not. Bounded
    slices only: 11 OK and the arrival method 1 OK; no aggregate.
12. [done, independently signed off] The current integrated 555-probe driver
    remains warning-clean and bounded; both regression classes pass; the same
    five semantic-failure categories remain visible and separately owned.
    Close W54182 satisfying. Review:
    `review-2026-09-01T00-46-24Z.md`.
