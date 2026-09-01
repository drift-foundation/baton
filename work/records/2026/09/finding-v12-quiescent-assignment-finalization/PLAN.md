# Plan

1. [done] Preserve W52821 run5b's unresolved evidence and confirm that no
   container remains while the exact assignment is still live.
2. [done, reviewer 2026-09-01] Revalidate the assignment, attempt, quiescence,
   retention and cleanup transitions against the current v12 tree. The exact
   code/spec/evidence map is in `evidence/research-2026-09-01/README.md`.
3. [done, approved 2026-09-01] Specify the smallest public end-or-fence
   transition and its idempotent recovery semantics without deciding proposal
   disposition: a distinct already-quiescent finalization operation plus an
   explicit operator mode. The operation accepts any recorded terminal worker
   disposition and refuses `none`.
4. [ready for implementation after current-tree overlap revalidation]
   Implement the approved correction in its own v12 container with focused
   normal, terminal-disposition, retry, crash/restart, no-side-effect and
   wrong-identity tests. W52821 is accepted and closed; preserve and revalidate
   W61599's overlapping work rather than overlaying it.
5. [pending independent review] Review the retained proposal and prove that
   assignment capacity is released before cleanup is admitted, custody stays
   pending without a retention decision, exact cleanup later preserves any
   explicit keep, and only positive absence satisfies the authority gate.
