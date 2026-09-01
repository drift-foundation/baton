# Plan

1. [done] Preserve W52821 run5b's unresolved evidence and confirm that no
   container remains while the exact assignment is still live.
2. [done, reviewer 2026-09-01] Revalidate the assignment, attempt, quiescence,
   retention and cleanup transitions against the current v12 tree. The exact
   code/spec/evidence map is in `evidence/research-2026-09-01/README.md`.
3. [ready for approval] Specify the smallest public end-or-fence transition
   and its idempotent recovery semantics without deciding proposal
   disposition: a distinct already-quiescent finalization operation plus an
   explicit operator mode. Resolve the three open decisions in `FINDING.md`.
4. [pending, after W52821 disposition and overlap revalidation] Implement the
   approved correction in its own v12 container with focused normal, terminal
   disposition, retry, crash/restart, no-side-effect and wrong-identity tests.
   Preserve W61599 and the exact W52821 import rather than overlaying them.
5. [pending independent review] Review the retained proposal and prove that
   assignment capacity is released before cleanup is admitted, custody stays
   pending without a retention decision, exact cleanup later preserves any
   explicit keep, and only positive absence satisfies the authority gate.
