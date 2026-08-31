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
7. [changes requested] Independent review is recorded in
   `review-2026-08-31T16-16-32Z.md`. Resolve the leaked refused-open handle in
   contained W54881 and correct or narrow the false immutable-AST claim, then
   return for focused re-review. Do not run the aggregate inventory.
