# Plan

**Status — 2026-08-16:** signed off in
`review-2026-08-16T23-53-25Z.md`. The breaking output is projection 5.0, the
thread-less trial-assignment exception is explicitly approved and tested, and
the complete v11 gate is green. W179 may close satisfying and unblock W176.

## Revalidation — 2026-08-16

- `projection._message_count()` currently expands `_descendants()` and counts
  every Message reachable through that recursive Work set. Restrict its label
  query to the addressed Work's directly labelled Threads.
- `projection._my_pending()` currently selects obligations by recursive
  `obligations.work`. The ruled visible scope is the directly labelled Thread
  set, so select pending obligations through those Threads; a Thread visibly
  reused by several Work items contributes to each direct view just as its
  Messages do.
- `_row_view()` currently projects `new_count(...)["total"]`. Its plain `new`
  field must use the direct `own` count. Home, tree and detail already share
  `_row_view()`, so this is the common JSON/TUI correction rather than a TUI
  calculation.
- Keep `new` as the explicit recursive read, but name its union
  `subtree_total` rather than an unqualified `total`; retain `own`, immediate
  `children`, and `overlap`. Update every source/packaged workflow and parity
  consumer to the explicit name. This projection-shape correction requires a
  projection-version bump, not a SQLite schema change.
- Replace W36's recursive-default assertions with direct-scope assertions and
  add the pinned W24-shaped regression: direct parent Threads, open children,
  a hidden closed child, nested descendants, and a multiply-labelled Thread.
  Prove that row/detail counters match the Threads entering the Work exposes,
  while the explicit subtree read remains overlap-safe.

1. Revalidate every projection and TUI consumer of Work `message_count`,
   `my_pending_obligations`, `new`, and recursive New breakdowns.
2. Change default Work summary/detail counters to directly labelled Thread
   scope without making presentation expansion state authoritative.
3. Retain recursive information only through an explicitly named subtree
   breakdown with visible overlap accounting.
4. Update CLI/JSON/TUI parity and command documentation so agents and humans
   read the same direct defaults.
5. Add projection, workflow and virtual-screen regressions for open, hidden
   closed, nested and multiply-labelled descendants.
6. Run the complete v11 gate and return for independent review before W176.
