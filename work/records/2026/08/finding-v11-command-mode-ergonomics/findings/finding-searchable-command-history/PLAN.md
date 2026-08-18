# Plan

**Current status — signed off 2026-08-18.** W78 is closed and the complete W26
focused suite, including both real-PTY proofs previously gated by W78, passes.
See `review-2026-08-18T19-47-58Z.md`.

**Status — round-2 correction implemented and returned to `baton.feat` on
2026-08-18. See PROGRESS.md.** Reverse search now viewports the query around
its actual insertion point, marks the clipped left, keeps the identity and the
no-match distinction, and derives the row from the intact stored query.

**Round-2 status — changes requested in review round 2 on 2026-08-18.**
The round-1 invisible-execution defect is fixed. See
`review-2026-08-18T14-11-11Z.md`: an over-width reverse-search query still
hides its live tail while placing the terminal caret at the right edge, so the
painted cell and actual insertion point diverge. See PROGRESS.md for the older
contradiction between the two search bullets below, resolved toward
FINDING.md's confirmed decision.

**Original status:** queued as W26 on 2026-08-18. No schema or public CLI change.

## Revalidation — 2026-08-18

- `Console.command` is currently one string or `None`; `_command_key()`
  handles Enter, Esc, Backspace and printable append only. Up/Down and
  `Ctrl-R` have no command-mode meaning, so they can be introduced without
  displacing an existing bar action.
- `execute()` owns every submitted one-line command, including local `filter`
  and refused parser/authority calls. Record a stripped, non-empty submission
  immediately before that existing path; never derive history from success
  status or authority events.
- The render footer already gives command input the whole bottom row and owns
  its visible caret/horizontal viewport. Reverse search replaces assistance on
  that row while active; it does not add a second row or change table geometry.
- `::` has separate `batch`, `batch_cursor`, and `_batch_key()` state. Its
  Up/Down line navigation remains untouched.

## Bounded implementation contract

- Keep at most 500 adjacent-deduplicated entries for this Console session,
  oldest to newest. This bound is presentation state, not protocol state.
- Opening `:` establishes one scratch draft and positions history after the
  newest entry. The first Up recalls the newest submission; Down past it
  restores the byte-exact scratch draft. Editing a recalled entry changes only
  the command buffer, never the stored history entry.
- `Ctrl-R` starts with an empty substring and the intact pre-search draft.
  Printable input narrows case-sensitively; Backspace widens; repeated
  `Ctrl-R` moves to the next older matching entry and wraps no further than the
  oldest match.
- Right accepts the displayed match into the ordinary command buffer without
  executing and leaves its caret at the end. **Tab** likewise adopts the match
  first; once W27's completion verb exists, it then performs the ordinary
  completion action, because an adopted match is an ordinary buffer. Enter
  submits the SELECTED match through the existing path — with no selected
  match it submits nothing and stays in search, because the buffer behind the
  prompt is the invisible pre-search draft. Esc cancels and restores that
  exact draft.

  **Superseded clause — 2026-08-18 (W26 implementation).** This bullet
  originally also said a printable key and Backspace "adopt the match first
  and then perform the normal editing action". That contradicted the bullet
  above it and the confirmed decision in `FINDING.md`, both of which say
  typing NARROWS the search. It is not a stylistic conflict: if printable
  input adopted, no query could ever be typed and `Ctrl-R` would collapse into
  a plain "recall newest" key. Typing narrows and Backspace widens, as ruled.
  The "recall, tweak, rerun" workflow the retired clause wanted is served by
  Right or Tab — adopt, then edit in the ordinary buffer — and that path is
  covered directly.
- A command's final expanded text enters history, including contextual
  `thread=` seeding and a parser/authority refusal. Cancelled input, an empty
  Enter, search queries, and batch lines do not.

1. Add bounded in-memory history, an independent saved draft, and explicit
   navigation/search state to the TUI application.
2. Define Up/Down, `Ctrl-R`, Enter, Esc, edit-after-recall, empty history, and
   repeated-identical submission behavior without disturbing ordinary table or
   batch key handling.
3. Render a compact reverse-search prompt while preserving the visible caret
   and horizontal viewport rules of the command-assistance bar.
4. Add pure-state and PTY regressions, including refused commands, quoted
   values, resize, cancellation, and authority-byte/read purity before Enter.
5. Include search-to-edit (Right, printable, Backspace, and the W27 Tab path),
   no-wrap oldest-match behavior, scratch restoration, 500-entry eviction,
   contextual `say` seed, multiple Console isolation, and proof that ordinary
   table and batch Up/Down behavior is unchanged.
