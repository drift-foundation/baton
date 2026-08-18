# Finding: support cursor keys wherever the v11 TUI supports vi navigation

## Context

The v11 TUI deliberately supports vi-style navigation. Some users prefer the
terminal cursor keys, and requiring them to learn `h`/`j`/`k`/`l` merely to
move through an otherwise conventional terminal interface is unnecessary.

## Observed — 2026-08-17

The current implementation already accepts cursor keys in the main Work tree,
search results, dependency neighbors, Thread and Message selection, readers,
Events, batch-line selection, and `Ctrl-W` geometric pane movement. The focused
geometric-navigation regressions, however, exercise only `h`/`j`/`k`/`l`.
That makes cursor-key parity an incidental implementation property rather than
a protected user contract.

## Confirmed decision — 2026-08-17

- Cursor keys are first-class aliases for vi navigation throughout the TUI.
  Up/down mirror `k`/`j`; left/right mirror `h`/`l` wherever those directions
  are meaningful in the current mode.
- A cursor-key alias has exactly the same boundary behavior as its vi key. It
  must not introduce a second navigation model, mutate authority state, mark a
  Message seen, or trigger an otherwise unrelated action.
- Existing conventional aliases remain: for example, left/Esc may leave a
  detail or re-rooted view where that is already the established leftward
  action. Right is not invented as Enter in modes where `l` has no meaning.
- Help text names both choices compactly; it must not imply vi keys are the
  only supported navigation.

## Acceptance

1. A focused matrix proves cursor/vi equivalence for every directional
   `Ctrl-W` pane edge, including unmapped edges.
2. Focused coverage proves up/down parity in each independently navigable list
   and reader, and left/right parity in every mode that exposes `h`/`l`.
3. Navigation remains observation-only: authority sequence and personal seen
   cursors do not advance.
4. The v11 operator documentation advertises cursor-key parity without adding
   a second set of semantics.

## Regression found in live trial — 2026-08-18

The earlier conclusion that no implementation gap existed is **superseded for
real terminals**. Slawomir reported that cursor keys do not move in the
deployed v11 TUI. The handlers do accept synthetic `curses.KEY_UP`,
`KEY_DOWN`, `KEY_LEFT`, and `KEY_RIGHT` values, which is why the focused model
tests passed, but `baton_work.tui.app.run()` never enables keypad translation
on its curses screen. The acceptance evidence therefore proved dispatch after
translation, not that a terminal escape sequence reaches that dispatch.

The child finding
`findings/finding-real-terminal-cursor-key-decoding/FINDING.md` owns the
correction and the missing packaged-PTY evidence. The cursor/vi parity ruling
itself is unchanged.
