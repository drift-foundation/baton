# Finding: the Message reader repeats the selected identity in its own row

## Observed

The wide split paints:

```text
Messages (n)                         Message M20
M23 baton.slaw 13:23 seen            #20 baton.codex 2026-08-18 13:21:37
```

The selected index row is already highlighted and the reader metadata already
names `#20`. The `Message M20` row therefore repeats selection and reduces the
body viewport.

## Confirmed decision — 2026-08-18

Remove the standalone reader heading. The reader starts with its canonical
`#N author timestamp` metadata in the row beside the Message-index heading at
wide widths, gaining one body row. In the narrow stacked layout, metadata
starts immediately after the index region without an intervening `Message M…`
label.

Pane focus must remain visible but does not justify another row. When the
reader has focus, its metadata row carries the established focus marker or
attribute; when no Message is selected, the existing explicit empty-reader
text occupies that position. Message metadata, body, and references remain
separate, and the selected index row remains the content-selection cue.
