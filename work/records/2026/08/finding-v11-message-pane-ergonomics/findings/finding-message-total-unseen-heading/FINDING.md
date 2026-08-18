# Finding: Messages (n) reports only the painted page

## Observed

`_render_message_region()` currently formats `Messages ({len(messages)})`.
The loaded `messages` array is one bounded page, so `Messages (10)` can mean
"ten painted rows" while the selected Topic actually contains many more.
Operators cannot reconcile the heading with the conversation or see how many
remain personally unseen.

## Confirmed decision — 2026-08-18

Render `Messages (total/unseen)`:

- `total` is the count of all Messages in the selected Topic at the projection
  snapshot, independent of page size and current page;
- `unseen` is the current participant's count above their Topic seen cursor,
  also across the entire Topic;
- examples are `Messages (0/0)`, `Messages (12/3)`, and
  `Messages (12/0)`; and
- the separate `(n: older)` continuation remains when an older page exists.

The canonical Topic read already returns whole-Topic `new`; it must also return
an explicit whole-Topic total. Clients must not infer total from page length,
sequence numbers, or cursor presence. Marking Messages seen changes the second
number only; adding a Message changes total and may change unseen according to
the viewer's cursor.
