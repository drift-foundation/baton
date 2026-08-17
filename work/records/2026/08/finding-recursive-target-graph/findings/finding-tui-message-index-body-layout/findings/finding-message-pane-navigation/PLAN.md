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
