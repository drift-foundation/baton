# Plan

**Review status — 2026-08-16:** changes requested in
`review-2026-08-16T14-31-54Z.md`. The layout is accepted; first-personal-new
selection must seek across bounded Message pages rather than inspecting only
the first page.

**Review round 2 — 2026-08-16:** later-page personal-new selection is fixed,
but the all-seen fallback still selects the oldest first-page Message. See
`review-2026-08-16T14-40-03Z.md`; retain the last page and select its newest
Message when the bounded seek finds no personal-new content.

**Review round 3 — 2026-08-16:** signed off in
`review-2026-08-16T14-44-51Z.md`. Both bounded-entry fallbacks pass, the full
W14 reader contract remains intact, and the independent v11 gate is green.

**Status — 2026-08-16:** queued after W2 closed satisfying. Confirmed live UX
defect; ready for `baton.claude`, returning to `baton.codex` for review.

1. Revalidate W71/W8 paging, Thread selection, explicit-seen, resize, and
   narrow-terminal contracts against the current projection-4.1 TUI.
2. Add a stable Message-index selection model keyed by existing message seq;
   preserve selection across refresh, paging, and resize where the Message
   remains present.
3. Render Threads above a wide index/reader split; render index above reader
   at narrow widths. Keep one selected body and its separate `Refs` readable.
4. Extend visible `Ctrl-W` help/navigation across Threads, Message index, and
   reader. Keep selection read-only and bound `s` to the selected Message's
   inclusive cursor extent.
5. Cover multiple Threads, multiple new/seen Messages, long bodies and refs,
   continuation, refresh, resize, narrow fallback, source/package parity, and
   refusal to mark later unseen Messages.
6. Run focused PTY coverage and `just test-v11`, then return for independent
   review and live human acceptance.
