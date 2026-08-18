# Finding: decode cursor keys on a real v11 terminal

Parent: `work/records/2026/08/finding-tui-cursor-key-parity/`

## Observed — 2026-08-18

In the deployed v11 TUI, Slawomir pressed terminal cursor keys and they did not
move the selection. Vi navigation continued to work.

## Confirmed diagnosis

The v11 handlers contain cursor-key aliases throughout
`src/baton_work/tui/app.py`, and pure tests inject `curses.KEY_*` constants
directly. The real runner calls `screen.getch()` but does not enable keypad
translation. A terminal sends escape sequences for cursor keys, so accepting
only the already-translated constants does not establish real-terminal
support.

The parent finding's statement that no implementation gap appeared is
superseded only in that respect. The cursor/vi parity contract remains
authoritative.

## Required correction

- Enable the curses input mode needed to translate terminal cursor sequences
  before the first input read, without changing the timer-driven refresh
  contract.
- Prove up/down movement and at least one left/right navigation boundary by
  sending raw ANSI cursor sequences through a real packaged PTY. Tests that
  call `Console.handle(curses.KEY_*)` are necessary but not sufficient.
- Preserve bare-Esc behavior and the existing short escape delay; cursor
  decoding must not make cancellation or exit feel delayed.
- Keep navigation observation-only: cursor input must not advance authority or
  seen state.

## Acceptance

1. Raw `ESC [ A/B/C/D` cursor sequences reach the same visible transitions as
   `k/j/l/h` in a packaged v11 console.
2. Bare Esc remains independently observable and keeps its established
   behavior.
3. Timer refresh continues independently of keystrokes.
4. Focused PTY regressions and the v11 gate pass.

## Amendment — 2026-08-18 (measured during implementation)

The "Confirmed diagnosis" above is wrong in one clause, and correcting
it matters because the wrong clause implies a fix that changes nothing.

> The real runner calls `screen.getch()` but does not enable keypad
> translation.

It does. `curses.wrapper` calls `stdscr.keypad(1)` before `run()`
executes, and `cli.py` launches the console through `curses.wrapper`.
Keypad translation has been on since the console shipped; adding it is a
no-op, which is what the first attempt at this fix measured.

**The actual cause.** `keypad(1)` emits `smkx`, which asks the terminal
for APPLICATION cursor mode, and xterm's terminfo then expects the SS3
spellings (`kcud1` is `ESC O B`). A terminal left in NORMAL cursor mode
sends the CSI spellings (`ESC [ B`) instead. Because ncurses asked for
the other mode, those arrive as a bare 27 followed by two ordinary
characters and match nothing. Measured against the live console:

    j then j          -> W4     baseline
    j then ESC O B    -> W4     application mode: already worked
    j then ESC [ B    -> W3     normal mode: did nothing

So the contract held for terminals that honour `smkx` and failed for
those that do not — which is consistent with the observation that vi
navigation kept working, and with why synthetic `curses.KEY_*` tests
could not see it.

Everything else in this finding stands, including the required
correction's substance: the fix is at the input boundary, it must not
delay bare Esc, and only raw sequences through a real PTY can prove it.
