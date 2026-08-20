# Progress

Implementer-owned.

## Revalidation against the current tree — 2026-08-20

`_event_lines` builds the header, `roles:`, any related Works, the
claim interval, the typed payload labels, the refs, and then appends
`"  payload:"` immediately followed by the indented JSON. The finding's
description matches it exactly: the label is there, the gap is not.

Nothing else needed to change. `soft_wrap`'s W48 docstring already
promises that "an empty logical line stays one empty visual line rather
than vanishing", which is precisely the property a blank separator
needs, and the reader's scroll/clip accounting works on wrapped lines
without caring what any of them contain.

## What changed

One line: `lines.append("")` before the `payload:` label, with the
reason beside it — spacing rather than a rule, because a horizontal
line would spend width the reader needs and depend on glyphs some
terminals draw badly.

## Verification

- `tests/work/test_w1207_event_separator.py` — new, **15 passed**: one
  blank row immediately before the label on an ordinary Event; the
  same on a metadata-rich one where a claim interval and a typed
  `comment` label sit between the header and the payload; the same on
  every kind this authority can produce in one run; the payload block
  itself still parsing back to the projection's own object,
  two-space-indented and sorted; the separator surviving all six
  falsy-and-absent payload spellings W48 keeps distinct; the wrapped
  form at six widths; the scrolled reader still reporting its clipping
  and its `(cont.)` marker; nothing written; and the projection
  unchanged.
- Removing the line fails **10** of those 15, which I checked rather
  than assumed.
- The complete v11 gate, `just test-v11`, exits 0 on this tree:
  **2573 passed** (parallel), **40 passed** (serial), both bridge
  suites green.

## One thing the tests deliberately do NOT assert

My first wrapping case counted every blank row in the wrapped block and
required exactly one. It failed at 12 and 24 columns — and the cause is
not this separator. `soft_wrap` gives a continuation the line's own
indent plus two, so a deeply indented JSON line in a very narrow pane
can leave an empty first piece: at width 12 a six-space-indented
payload line wraps to `'      '` followed by eight-space-indented
pieces.

That is `soft_wrap`'s pre-existing behaviour under W48 and predates
this Work. The acceptance boundary asks that narrow wrapping not
multiply or erase the LOGICAL separator, so the case now asserts
exactly that: the block holds one logical blank, that blank wraps to
exactly one visual row, and the row directly above `payload:` is blank
at every width. A test that counted blanks would have been measuring
the wrapper instead, and would have failed for a reason this Work does
not own.

I am recording the narrow-width wrapper behaviour rather than fixing
it: it is a separate presentation question about deeply indented JSON
in a pane too narrow to hold its indent, and nothing in this finding
rules on it.
