# Plan

**Status — signed off by `baton.codex` on 2026-08-18. See
`review-2026-08-18T14-43-33Z.md`.** All four steps are done:
the heading is gone in both layouts, focus rides the metadata row, the
recovered row is used by the reader (and pinned by geometry at four
terminal sizes), and the PTY coverage step 4 asks for is in
`tests/work/test_w30_reader_heading.py`.

**Original status — implementation-ready and handed to `baton.impl` on
2026-08-18.**
W29 is independently signed off and closed satisfying. Presentation-only; no
projection or database schema change. The Events reader is outside this Work.

## Revalidation — 2026-08-18

- `_render_message_region()` still spends one complete row on
  `reader_label` in both wide and stacked layouts, then calls `_paint_reader()`
  one row lower. `_paint_reader()` already produces the canonical metadata,
  body, and separated references, so no content reconstruction is needed.
- The selected Message remains identified by the reversed index row. Reader
  pane focus moves to the first reader row: prefix that metadata (or the
  explicit empty-reader text) with the established `»` focus marker and use a
  leading space otherwise. Bold alone is insufficient because unseen metadata
  already uses bold.
- Wide layout gives the reader the heading row plus every existing reader row.
  Stacked layout removes only the reader heading and starts the reader directly
  after the index region. Recompute clipping against those gained rows rather
  than hiding one extra body/reference line.
- Existing `Message M…` expectations are specifically superseded by this
  confirmed Work and may be updated; Event reader headings are not.

1. Remove `reader_label` and paint the reader one row earlier in wide and
   narrow layouts while preserving the Message-index heading.
2. Carry reader focus on the metadata row and preserve the empty-reader state.
3. Recalculate clipping, scroll offsets, footer placement, and minimum-height
   behavior using the recovered row.
4. Add wide/narrow/short PTY coverage for focus movement, empty selection,
   long metadata, body/reference separation, scrolling, and resize.
