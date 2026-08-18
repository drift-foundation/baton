# Progress

**Implemented by `baton.claude` and returned to `baton.feat` for independent
review on 2026-08-18.** Presentation only: no authority, projection or schema
change.

## Revalidation

`_paint_index` built one string — `M<seq>`, `team.member`, `HH:MM`, then
`new`/`seen` — so each row's later fields began wherever that row's author
handle ended. Reproduced before changing anything, with `lang.ada` and
`lang.grace` on the same page.

## What changed

The index is a fixed-column table declared as DATA:

    MESSAGE_COLUMNS   = (("From", 13), ("Time", 5), ("St", 4))
    MESSAGE_DROP_ORDER = ("Time", "St", "From")

Visual order is `Id From Time St`. Priority is deliberately different — Id,
From, St, then Time — so width pressure removes the clock before it removes the
viewer's own new/seen fact, exactly as pinned. `Id` is not in the table because
its width is computed per page.

- **`Id`** is the longest visible `M<seq>` on the bounded page, never narrower
  than its own heading, shared by every row in that paint. Computed from the
  page rather than a constant so a sequence crossing a decimal boundary widens
  the column instead of clipping the one field every operation is typed from.
- **`From`** is 13 cells because a configured handle is at most six display
  cells and the address is `team.member`. The compact vocabulary is the
  authority for that, not this renderer.
- Each cell is clipped inside its own allocation, so no overflow can move a
  later field.
- One compact header, underlined, names the fields.

Selection reverse-video, personal-new bold, newest-first order, the scroll that
keeps the selection painted, paging, and the reader are untouched.

## The header's row comes out of the allocation, not the listing

Adding a header row to the narrow stack silently dropped the last visible
Message: the index's row budget had not changed, so the header ate a listing
row. The narrow allocation now includes it. The failing expectation was W8's
"the narrow stack keeps two regions" — a pre-existing test asserting that two
Messages are both listed — and it was right, so the allocation moved rather
than the test.

## The seam W228 will use

The finding requires "a clean column-layout seam" for the future
viewer-relative action cue without implementing or inferring obligation state.
That is why the column set is a tuple rather than a format string: adding a
column should be one entry plus a drop-order position.
`test_the_column_set_is_data_not_a_format_string` proves it by subclassing
`Console` with an extra `Do` column and checking it is both laid out and
dropped at its declared priority — without touching the painter. A companion
test asserts this Work ships no such cue.

## Regressions

`tests/work/test_w49_message_index_columns.py` (28 tests): the header names
the fields; every row shares the same offsets with mixed-length handles; a
maximum-width configured address does not move the clock; `Id` never clips its
selector and is shared across a page mixing two- and three-digit sequences;
responsive omission at eight widths from 34 down to 6, dropping whole fields in
reverse priority; a dropped field leaves nothing partial; the selection survives
the narrowest layout; empty, exactly-filling, header-only and overflowing pages;
newest-first; `St` proved viewer-relative by two viewers disagreeing; `Time`
proved to be the event time; bold and reverse attributes; the W228 seam; and a
real-terminal test that the columns align and survive a resize.

## Break-sweeps

| Reintroduced defect | Result |
| --- | --- |
| The original concatenated row | 4 red |
| A fixed `Id` width that clips the selector | 3 red |
| Drop `St` before `Time` | 4 red |
| Cells not clipped to their allocation | **green — then 1 red** |
| The header eats a listing row again | 1 red (W8's own test) |

The clipping sweep came back green, and the reason is worth recording: with
handles capped at six cells, `From` can never overflow 13, so the clip is
unreachable through the configured grammar. Rather than leave a guard nothing
exercises — or delete a guard that is correct — the painter is now handed a
message that breaks the promise, because the alignment must be a property of
the LAYOUT and not of an upstream limit. If the handle cap ever moves, the
index should lose characters from one cell instead of losing its columns.

## Gate

`just test-v11`: **1605 passed**, serial **37 passed**, ACP **41/41**.
