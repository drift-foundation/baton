# Finding: make message panes spatial and newest-first

## Observation — 2026-08-17

The live v11 Work-detail screen exposes Threads, a Message index, and one
selected body, but the oldest Message appears first, pane focus is visually
ambiguous, and reaching Threads from the body requires stepping through the
Message index. The intended three-pane model exists but its navigation does
not behave like three independent panels.

## Confirmed decision

- Display the newest Message at the top of the Message index while preserving
  canonical sequence, paging identity, and explicit seen semantics.
- Mark exactly one focused pane visibly in its heading; a row selection alone
  does not identify pane focus.
- Navigate geometrically with `Ctrl-W` plus direction across Threads, Message
  index, and reader. From the body, one upward window move reaches Threads;
  the Message index is not a mandatory intermediate stop.
- Preserve wide index/reader splitting, narrow stacking, body/Refs separation,
  refresh-stable selection, and read-only navigation.

No authority schema change is required.

## Acceptance boundary

- Empty, one-message, multi-message, and multi-page Threads enter with the
  newest relevant Message visible first.
- The active pane marker follows every directional move, refresh, resize, and
  layout transition and never leaves zero or two panes apparently focused.
- Wide and narrow geometries each have deterministic directional neighbors.
- Moving focus or selection never advances seen state; `s` advances only
  through the selected canonical Message.
- Long bodies and references remain scrollable independently of index and
  Thread selection.
- Source and packaged PTY behavior agree.
