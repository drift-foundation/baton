# Finding: v11 TUI quits immediately on `q`

## Observed

The first human v11 TUI trial exits immediately when `q` is pressed in normal
navigation mode. This makes an accidental keystroke terminate the console and
differs from the accepted v10 interaction.

## Confirmed correction

In normal TUI navigation mode, `q` always opens one bottom-line confirmation:

`Exit? y/N`

`y` or `Y` exits. `n`, `N`, or `Esc` cancels and returns to the unchanged
view. Other keys do not confirm. The prompt is one row at narrow and wide
terminal sizes, never duplicated, and quitting or cancelling performs no
authority mutation or implicit seen transition.

This applies to the navigation command, not literal `q` typed into a command
bar or another text-entry context. The immutable `6d1b944` trial remains
unchanged; include the correction in the next v11 distribution.

The live trial tracks this as v11 Work `26de18dd-W40` with prototype Thread
`26de18dd-D40`.

## Pre-cutover audit — 2026-08-16

**Confirmed by source inspection.** Normal navigation still returns from the
TUI immediately when `q` is pressed (`src/baton_work/tui/app.py`), and packaged
PTY helpers still use a bare `q` as the expected exit path. The correction is
therefore not implemented. It is a client interaction/test change only,
requires no authority/schema revision, and must be completed before the fresh
cutover rather than recreated as open Work afterward.
