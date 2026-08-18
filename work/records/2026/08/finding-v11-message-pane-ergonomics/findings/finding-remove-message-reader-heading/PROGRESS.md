# Progress

**Implemented and handed to `baton.feat` for independent review on
2026-08-18 by `baton.claude`.** Presentation only: no projection field, no
public CLI operand, no schema change.

## Revalidation against the tree

Every claim in PLAN.md's revalidation held. `_render_message_region()` painted
`reader_label` on its own row in both layouts and started `_paint_reader()` one
row lower; `_paint_reader()` already produced the whole canonical block, so
nothing had to be reconstructed.

## What changed

- `_paint_reader()` gained `focused=` and paints the `»`/space marker itself,
  on its first row — the metadata row, or the explicit `(no message selected)`
  text. The block wraps at `cell_width - 1` so the marker column is reserved
  rather than taken from content.
- Wide layout: the reader now starts on the SAME row as the Message-index
  heading and keeps every row it had (`top, region`, previously
  `top + 1, region - 1`). Clipping, `reader_skip`, the `(cont.)` disclosure and
  the footer are all derived from that span, so they followed the recovered row
  with no separate adjustment.
- Stacked layout: `reader_top = top + 1 + index_rows` — the reader begins
  immediately below the index, with no label row between them. The index bound
  relaxed from `region - 3` to `region - 2` for the same reason.
- W176's comment claimed the reader heading "names the selected message exactly
  once". It no longer exists; the comment now records why this pane paints one
  label and not two.

## Two things worth the reviewer's attention

**The marker costs one column, everywhere.** The reader block is inset by one
column at all widths, focused or not, because a marker that appears only on
focus would shift the whole block on every `Ctrl-W`. The alternative —
insetting only row 0 — keeps the body flush but puts a one-column seam between
the metadata and the body it heads. The uniform inset was chosen for a coherent
block; it is a real cost and is named here rather than buried.

**One break-sweep could not be made red, and the code was changed rather than
the claim.** `format_message()` reserves a column internally (`width - 3` under
a two-space indent), and `addnstr` clamps to the cell, so removing the
`cell_width - 1` reserve changes no pixel. I briefly added a defensive clip of
every reader row and then reverted it: it too changed nothing observable, and
dead code presented as a fix is worse than none. The reserve stays, with a
comment saying why it is stated at the paint site instead of borrowed from
another function's margin.

## Regressions

`tests/work/test_w30_reader_heading.py` (16 tests):

- the heading is absent at wide and narrow width, and after a resize;
- the reader's metadata shares the index heading's row (wide);
- **the recovered row is pinned by geometry, not by a sample line**: with a
  body longer than the pane, the reader paints every row from its first through
  the last row above the footer, and its body lines number one fewer than that
  span. Run at 110×24, 110×14, 60×24 and 60×14, so both layouts and the
  short-terminal case are covered;
- focus walks Threads → index → reader and the marker moves with it; the two
  markers are distinguished by column, since both panes now share a row;
- the marker does not displace metadata or shift its column;
- the reader never bleeds past its cell, with the longest metadata the handle
  grammar permits (6 cells of team, 6 of member) and an unbroken 300-character
  body token, checked in both focus states;
- the `(cont.)` scroll tag respects the same reserved column;
- empty selection still states `(no message selected)`;
- the index heading, its counts and the reversed selection row survive, and
  selection still moves the reader.

## Break-sweeps

| Reintroduced defect | Result |
| --- | --- |
| Wide reader heading restored, reader pushed down a row | 5 red |
| Narrow reader heading restored | 1 red |
| Reader focus marker dropped | 1 red |
| Reader painted 3 columns left, into the index cell | 3 red |
| Wide reader shortened by one row (the recovered row given back) | 2 red |
| Narrow reader started one row lower | 2 red |
| `format_message` wrap reserve removed | **green — see above** |

The last two sweeps first came back green and the tests were rewritten until
they did not: the geometry check replaced a sample-line check, and a narrow
assertion that walked up to the heading by construction (so could never fail)
was replaced by a contiguity check between the index and the reader.

## Superseded expectations updated

PLAN.md rules that existing `Message M…` expectations are superseded by this
Work. Updated, each with the reason recorded at the assertion:

- `test_w176_pane_labels.py` — 5 assertions, including a `reader_id()` helper
  that now reads `#N` from the metadata instead of parsing the heading;
- `test_tui.py` — the heading and its `Msgs —` variant are now asserted ABSENT;
- `test_w71_navigation.py` — reader focus is `»#`, not `»Message M`;
- `test_w8_message_format.py` — the marker column is stripped before the block's
  own indentation is checked, so the Refs/body separation rules are unchanged
  rather than loosened.

Event reader headings were not touched.

## Gate

`just test-v11`: 1213 passed, 3 failed. **None of the three is this Work.** All
three fail identically with W30 reverted:

- `test_w47_event_phase_intervals.py::test_an_accept_created_provider_opens_its_first_episode`
- `test_w47_event_phase_intervals.py::test_a_blocking_request_ends_active_and_opens_waiting`
- `test_w26_command_history.py::test_an_overwidth_reverse_query_keeps_its_live_tail_visible`

W47 and W26 are both queued and unclaimed on `baton.impl`. The W26 one is the
round-2 review defect recorded in that Work's own PLAN. The W47 ones are real
gaps in W47's own scope and are reported on that Work; both are the same defect
class — a transition that moves the phase without recording it, which is
exactly what W47's replay cannot reconstruct:

- `accept …create=` writes no `phase_now` for the provider Work it creates, so
  an accept-created Work has no scheduler history at all;
- a blocking `request` moves the Work to `waiting` and releases the claim in its
  own transaction, and records no `phase_now` either — so the projection still
  shows the claim's `active` episode open while the Work is in fact `waiting`.

Both are being taken under W47, not smuggled in here.
