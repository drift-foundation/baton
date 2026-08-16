# Plan

1. Revalidate the two-level `↳` containment renderer, dependency projections,
   responsive column budget, and the authority-local selector work.
2. Expose the deterministic live blocker-selector summary in the canonical
   Work-list projection without a TUI N+1 read.
3. Render `← Wn` / `← Wn +N` separately from the `↳` child marker and remove
   the `Ready` column from wide and narrow Work tables.
4. Cover one blocker, several blockers, satisfied historical edges, combined
   child-and-blocker rows, sorting/filtering/refresh, narrow omission, JSON/TUI
   parity, and `[b] deps` consistency.
5. Run focused coverage and `just test-v11`; return for independent review
   before the next immutable trial release.

**Scheduling:** queue this Work behind authority-local selector W4 so every
visible dependency cue uses the same reviewed `Wn` identity contract.

**Review gate — 2026-08-16:** changes requested in
`review-2026-08-16T15-16-41Z.md`. The presentation contract passes, but
`first_open_blocker` currently adds one authority SELECT per projected Work.
Replace it with one batched tree-window read, pass the additive scaling
regression, rerun focused/full v11 gates, and return W39 for review.

**Signed off — 2026-08-16:** round two is accepted in
`review-2026-08-16T15-21-16Z.md`. Home, children, and tree batch blocker
selectors once per projection window; detail shares the helper. The scaling,
behavior, and parity gates pass independently. W39 may close satisfying.
