# Progress

Implementer-owned.

## Revalidation against the current tree — 2026-08-19

Both observations hold exactly as written.

`COLUMNS` carried `("AGENT", 5)` beside `HANDLER`, and `_row_view` filled
it from `agent_cell(row["agent"])` — `work`, `input`, `retry`, `off`,
`unkn`. Every cell was a runtime STATE; the header was the only part of
it that named an agent, and `Handler` one column left already named the
participant.

`_render_teams` measured each column's content, computed
`used = id_width + sum(size + 1 …)` — and never read `used` again. The
surplus was simply discarded. `_team_cells` also cut `Session` to twelve
characters plus an ellipsis, inside the cell builder, so the width was
decided before the layout knew whether it had eighty columns or two
hundred. A 200-column terminal showed the same twelve-character prefix
as an 80-column one.

The W93 authority model is untouched by any of this: the projection
field is still `agent`, the runtime lease and its vocabularies do not
move, and Teams still separates the adapter family from what it is
doing.

## What changed

**Jobs says `Run`.** A presentation rename: `COLUMNS`, `DROP_ORDER` and
the row cell key. `agent_cell()` keeps its name because it is named for
the projection field it reads, which has not moved, and its docstring
now says so.

**The Teams table is sized after the cells exist.** `_team_cells`
returns the WHOLE session locator. `team_layout(width, id_natural,
natural)` is a pure function beside the renderer, because every
acceptance case in this finding is a statement about widths and a
statement about widths should be testable without a screen. It runs
three passes, in this order and for this reason:

1. **Fit at floors.** Dropping is decided against the narrowest each
   column may be drawn, never against what it would like. Deciding it
   against the grown widths was my first attempt and it was wrong in a
   visible way: one 36-character locator deleted the whole `Session`
   column from an 80-column terminal that could have shown a 33-
   character prefix.
2. **Keep somebody.** If the floors do not fit, the identity shrinks,
   and at `TEAM_ID_FLOOR` the remaining columns go instead. A row that
   cannot say who it describes says nothing.
3. **Spend the surplus.** Categorical columns grow to their content up
   to a cap; everything left goes to `Session`. Nothing else grows —
   stretching a four-letter vocabulary adds width without adding
   information, and the finding asks for the surplus to go where it is
   USEFUL, not to be spread evenly.

`TEAM_DROP_ORDER` is `Session, Role, Since, Work, Agent`. `Session`
goes first because the Member detail block below the table carries it
in full, so it is the one column whose loss costs an operator nothing
they cannot recover with one keystroke — and it is by far the widest.
The participant identity and `State` are never dropped while anything
can be drawn at all.

`_fit` abbreviates with `…` whenever a value cannot fit, at every
width and for every column including the identity, because an
identifier that is silently cut reads as a different, shorter
identifier.

## A reading I had to make

The ruling says surplus width should go to "useful identity/diagnostic
text, including the participant/display identity and session locator".
I read that as: do not truncate those fields while space is unused. The
participant identity already sizes to its content and now stays that
way at any width that can hold it; the session locator takes the
remaining room. I did NOT add a `display` column — the acceptance
boundary asks for a complete session locator and for long identities to
survive, and adding a column nobody asked for is a bigger change than
the finding describes. Flagged here rather than decided silently.

Space beyond what every column naturally needs is left blank rather
than padded into the categorical columns. The defect was truncating
while space went unused; spreading four-letter cells across a
200-column terminal would not fix it.

## Superseded assertions edited

The finding supersedes the Jobs `Agent` header and the always-
abbreviated Teams `Session` example in
`work/records/2026/08/finding-agent-runtime-state/`. Three assertions
pinned those:

- W93's `test_the_jobs_table_paints_agent_beside_handler` became
  `test_the_jobs_table_paints_the_runner_state_beside_handler`, now
  also asserting the superseded header does NOT survive beside the new
  one;
- `test_tui`'s narrow-layout case asked for `"AGENT"` in
  `visible_columns(..., claimed=True)` and asks for `"RUN"`;
- W93's `test_member_details_expose_the_full_session_and_provenance`
  still passes unchanged — the detail block always carried the full
  locator, and now the table can too.

## Verification

- `tests/work/test_w137_runtime_tables.py` — new, **212 passed**
  (194 of them the per-width sweep): the rename with its JSON parity
  and drop-order consistency, Teams keeping its own `Agent`/`State`
  split, a wide terminal showing the complete locator, an exact fit
  showing everything and nothing more, every width from 6 to 200
  fitting inside the screen and preserving column order, the ruled
  drop order verified by shrinking 400 columns down to 5 and checking
  no column ever comes BACK, the identity and `State` surviving
  longest, visible truncation, a resize returning the identical table,
  a member with no session reading `-`, a long identity kept whole,
  selection and member detail unchanged, the documentation, and TWO
  real terminals — 180 columns showing the whole locator and 72
  showing an ellipsised one with no line past the edge.
- W93 **91 passed**, `test_tui` **31 passed**, W25 **36 passed**.
- The complete v11 gate, `just test-v11`, exits 0 on this tree.

## Boundary with W110

W110's tab-grammar corrections are in the same uncommitted tree; the
two Works cannot be physically separated without a Git operation, which
my role forbids. The file-and-symbol boundary is written out in
`work/records/2026/08/finding-consistent-tui-tab-grammar/PROGRESS.md`
so each review can read its own slice precisely.
