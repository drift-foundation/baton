# Plan

**Status — 2026-08-17:** confirmed and queued after W65 because both touch the
Work-detail TUI renderer and its state tests.

1. Revalidate current W14/W176 message paging, selection, focus, resize, and
   explicit-seen contracts against the latest TUI.
2. Implement true newest-first Message-index entry across bounded pages while
   retaining canonical sequence and stable selected-message identity.
3. Render a single active-pane heading marker and implement geometric
   `Ctrl-W` direction mapping for wide and narrow layouts.
4. Cover direct reader-to-Threads movement, horizontal lower-pane movement,
   resize remapping, refresh preservation, long content, and no seen mutation.
5. Run focused PTY tests and `just test-v11`; return for independent review
   and live human acceptance.

## Revalidation and implementation boundary — 2026-08-17

The committed client already carries three explicit focus states
(`threads`, `index`, `reader`) and paints a `»` on the selected heading. The
remaining defects are structural:

- `_handle_detail` treats panes as one linear tuple, so upward movement from
  the reader stops at the Message index rather than reaching Threads.
- `projection.thread` pages forward in canonical sequence order, and the TUI
  reverses neither the page nor the paging direction. Existing entry logic
  may walk forward through every page merely to find the first unseen or final
  Message.

Implement newest-first as a bounded pure projection/cursor path. Do not
reverse only the current forward page, and do not load an unbounded Thread to
find its tail. Message `seq` remains the stable identity and explicit `s`
still advances seen state through exactly the selected sequence. Because seen
is a monotonic sequence cursor, the newest Message is also the newest unseen
Message whenever anything is unseen; entry therefore selects the newest
Message, not the oldest unread one.

Use this deterministic logical neighbor map in both wide and narrow layouts:

- `Ctrl-W Up` from either Message pane reaches Threads directly.
- `Ctrl-W Down` from Threads reaches the Message index; from the index it
  reaches the reader.
- `Ctrl-W Left/Right` moves between Message index and reader.
- `Ctrl-W Ctrl-W` retains deterministic three-pane cycling.

Unmapped edge directions stay in the current pane. Ordinary `j/k` remains
selection/reader scrolling and never changes panes. Newest-first index
movement means down selects older Messages and up selects newer ones; paging
and its footer must name older/newest direction honestly. Focus survives
refresh by pane name, survives resize through the same logical map, and an
empty Message page still paints exactly one focused pane heading.

Focused coverage must include multiple bounded pages with descending visible
sequences, newest entry with and without unseen Messages, older/newest page
navigation, direct reader-to-Threads movement, lower-pane horizontal moves,
wide-to-narrow resize, empty pages, long reader/Refs scrolling, and proof that
all navigation leaves the seen cursor and authority bytes unchanged.
