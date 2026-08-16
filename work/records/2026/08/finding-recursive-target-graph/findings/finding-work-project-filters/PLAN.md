# Plan

**Status — 2026-08-16:** implementation-ready after approval and revalidation;
the live Work is claimed in research and may pass to `baton.impl`. This is a
same-schema filtering feature. The 2026-08-15 persisted project-metadata
design is superseded: team is the project boundary.

1. Add one pure, closed and deterministically ordered filter grammar over
   existing Work facts: team, status, phase, Current/handler, category,
   readiness, personal New and priority. Refuse duplicate or unknown fields,
   malformed booleans, unknown endpoints and compact display spellings.
2. Expose that exact grammar across CLI/JSON and TUI: optional operands on
   `home`, `tree` and `tui`; interactive `:filter`; and bare `:filter` to
   clear. Prove startup and interactive parity and keep filter state local to
   each client session.
3. Treat a team's home view as implicitly team-scoped; do not add redundant
   project metadata, configuration, defaults, or persisted authority state.
4. Apply filtering inside the canonical projection snapshot. Retain a
   nonmatching parent as marked context when a child matches; never promote or
   reorder children. Echo the normalized filter while leaving the explicitly
   global team summary global.
5. Keep `Filter:N` and the normalized clauses visible, including at narrow
   widths. Preserve deterministic ordering, personal counts, id-stable
   selection and the existing one-path refresh scheduler.
6. Cover every field, AND composition, invalid fields/values, eligible and
   ineligible `current=me`, personal New, multi-team/re-rooted views,
   parent-context retention, clear/replace/restart, narrow terminals, stale
   view state and unchanged authority state.
7. Run focused and full v11 gates before review; no fresh authority is needed.

**Review status — 2026-08-16 16:45Z:** changes requested in
`review-2026-08-16T16-45-54Z.md`. Canonical filtering is otherwise clean, but
an explicit `status=closed` filter is erased by the TUI's default closed-row
collapse, and current clauses are rendered only as a hint rather than exposed
in an editable command buffer. Correct both boundaries, add focused PTY and
editing regressions, then return for independent review.

**Signed off — 2026-08-16 16:51Z:** round two is accepted in
`review-2026-08-16T16-51-41Z.md`. Explicit closed filters reveal their selected
rows, current clauses seed an editable command buffer without changing bare
clear semantics, focused coverage passes, and the complete parallel plus
serial v11 gate is green. W5 may close satisfying.
