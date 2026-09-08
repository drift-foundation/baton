# Plan

**Status — certification boundary pinned; waits for the standalone multi-Job
pipeline milestone.**

1. [pending] Revalidate the accepted parallel scheduler, dependency,
   role-separation, affinity, fallback, and restart contracts.
2. [pending] Define a compact scripted-actor scenario format and logical-clock
   driver whose inputs and resulting event trace are reproducible.
3. [pending] Implement partial-order and final-state validation for multi-team
   implementation/review pools, dependency graphs, affinity returns,
   fallbacks, capacity, and replay.
4. [pending] Exercise controlled alternative completion interleavings without
   asserting an arbitrary total completion order.
5. [pending] Publish the bounded trace for consumption by the future read-only
   v12 TUI and return the certification evidence for independent review.

Real-model stress and TUI presentation follow this model-free certification;
they do not define its correctness oracle.
