# Plan

**Status — 2026-08-16:** active with `baton.impl` as W3; return through
`baton.feat` for independent review. Same schema-15 authority; no migration or
restart. The creation and compact-display rulings are confirmed.

1. Revalidate the priority contract against the current authority schema,
   event ledger, projections, CLI/TUI parity, authorization, and retry model.
2. Retain the existing required canonical Work priority with values `high`,
   `normal`, and `low`; creation accepts it optionally and defaults to
   `normal`.
3. Add an audited, effectively-once priority revision authorized to members of
   the owning team. Refuse cross-team mutation without changing authority.
4. Expose full priority in JSON and compact `Pr` values `Hi`, `No`, `Lo` in
   the TUI. Drop `Pr` first as one whole column under width pressure. Order
   root siblings by priority then `created_seq`; order each child sibling
   group identically while preserving containment. Do not change unrelated
   responsive columns.
5. Add positive, default, authorization, retry, restart/rebuild, ordering, and
   TUI/JSON parity regressions proving that priority never mutates workflow
   readiness, dependencies, ownership, phase, or status.

**Signed off — 2026-08-16 16:04Z:** independent source review, 34 focused
tests, the complete 728-parallel plus 3-serial v11 gate, and diff-check are
clean. See `review-2026-08-16T16-04-32Z.md`; W3 may close satisfying.
6. Run focused coverage and `just test-v11`, then return for review before the
   next immutable v11 distribution.
