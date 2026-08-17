# Plan

**Status — 2026-08-17:** signed off in
`review-2026-08-17T00-13-23Z.md`; the R1 width correction and complete v11
gate are green. W187 may close satisfying.

## Revalidation — 2026-08-16

- The authority already projects `first_open_blocker` deterministically by
  permanent Work creation order and `open_blockers` from the same snapshot.
  No projection, schema or dependency-semantic change is needed.
- `blocker_cue()` is the one formatter to change: render `Wn` and `Wn+N`
  instead of `← Wn` and `← Wn +N`.
- `_render_table()` owns the sole `Blk` heading. Rename it `Wait`; preserve the
  existing whole-column responsive omission and `[b] deps` navigation.
- Supersede W39's old arrow/`Blk` presentation assertions while retaining its
  deterministic-order, one-batched-read, refresh, containment distinction,
  narrow omission, and JSON/TUI parity coverage.

1. Revalidate wide/narrow Work-table column allocation and dependency order.
2. Rename `Blk` to `Wait`, remove the arrow and format multiple blockers as
   deterministic `Wn+N`.
3. Preserve `[b] deps`, containment indentation and all authority semantics.
4. Add virtual-screen coverage for zero, one and several blockers at wide and
   narrow widths.
5. Run the complete v11 gate and return for independent review.
