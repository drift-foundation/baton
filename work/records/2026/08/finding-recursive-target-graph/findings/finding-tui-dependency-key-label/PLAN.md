# Plan

**Status — 2026-08-16:** signed off in
`review-2026-08-16T15-49-33Z.md`. The former W14 serial blocker is closed.

1. Replace the visible `b links` footer/help label with `[b] deps` everywhere
   it describes the dependency-neighbor view.
2. Preserve the `b` binding, graph projection, and empty-state behavior.
3. Add focused wide/narrow PTY assertions preventing the ambiguous label from
   returning.
4. Run focused coverage and `just test-v11`, then return for review.

**Superseded — 2026-08-23:** item 2's preserved-`b` requirement is no longer
actionable. `work/records/2026/08/finding-tui-dependency-key-d/` owns the
replacement `[d] deps` binding and explicit removal of `b`; the completed
historical correction above remains evidence of the earlier contract.
