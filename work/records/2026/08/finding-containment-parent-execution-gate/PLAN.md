# Plan

1. [done] Reproduce the contradiction between the durable containment contract
   and current readiness/phase behavior.
2. [pending] Revalidate every consumer of `ready` and separate scheduler gates
   from terminal containment closure without weakening either.
3. [pending] Add parent-claim/open-child, late-child, terminal-refusal, and
   explicit-dependency regressions.
4. [pending] Implement, run the complete v11 gate, and independently review.
