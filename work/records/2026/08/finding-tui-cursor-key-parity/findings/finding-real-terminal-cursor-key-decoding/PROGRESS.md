# Progress

## Step 1 — the stated cause is wrong; the defect is real (2026-08-18)

The finding says the runner "calls `screen.getch()` but does not enable
keypad translation". It does. `curses.wrapper` calls `stdscr.keypad(1)`
before `run()` executes, so translation has been on the whole time and
adding it changes nothing — I wrote that fix first and measured no
difference, which is what sent me looking further.

The real cause is one layer down, and it explains the symptom better.
`keypad(1)` emits `smkx`, asking the terminal for APPLICATION cursor
mode. xterm's terminfo then expects the SS3 forms:

    kcud1=\EOB   kcuu1=\EOA   kcub1=\EOD   kcuf1=\EOC

Measured against the live console, that is exactly the split:

    j then j          -> W4     (baseline)
    j then ESC O B    -> W4     application mode: already worked
    j then ESC [ B    -> W3     normal mode: DID NOTHING

So cursor keys worked from terminals that honour `smkx` and did nothing
from terminals left in NORMAL cursor mode (DECCKM off) — which send
`ESC [ B` and, since ncurses asked for the other spelling, get handed a
bare 27 followed by two ordinary characters. Vi keys were unaffected,
and the unit tests inject `curses.KEY_*` directly, so neither surface
could see it.

## Step 2 — the correction

`curses.define_key` would be the tidy fix and is absent from this build,
so `run()` decodes the normal-mode forms itself: on a bare 27 it peeks
once, briefly, for `[` or `O` plus a cursor final and returns the
matching `curses.KEY_*`.

Anything that is not a cursor sequence is pushed back with `ungetch`, so
an escape introducing some other sequence reaches the reader exactly as
before. A genuine bare Esc costs one expired short read and returns 27
unchanged.

`set_escdelay` is also set, to the same 25ms, when the operator has not
chosen a value. That is a real improvement rather than a formality: with
keypad on, ncurses' default is a FULL SECOND before it will call a lone
ESC a bare Esc, so cancelling has been sluggish in production all along.
An explicit `ESCDELAY` is never overridden.

## Step 3 — acceptance

`tests/work/test_w25_real_cursor_keys.py`, 7 checks, all driving RAW
byte sequences through a real PTY against the PACKAGED artifact. A test
that calls `handle(curses.KEY_DOWN)` cannot fail for this defect; only a
terminal can, which is the whole point of the finding.

- up/down equivalence with `k`/`j` in BOTH spellings — normal and
  application — proven by opening detail, which names the exact Work;
- the left/right boundary: `u` re-roots the window and a raw LEFT pops
  back out, compared against the untouched top-level screen;
- bare Esc still cancels the command bar, in one session so the two
  screens differ only by the Esc between them;
- cursor navigation writes nothing to the authority.

Break-sweep: removing the decoder reds the two normal-mode cases and
leaves the application-mode ones green — the precise shape of the
original defect.

While writing these I hit two harness traps worth recording: a script
ending inside the command bar makes `qy` bar TEXT rather than a quit, and
indexing screens from the END returns the state after the teardown Esc
rather than the state under test. Both are now handled explicitly in the
helper.

## Evidence

- Gate: **1079 passed** + 12 serial + acp 36/36 on 32 cores.
- Whitespace check clean.

## Step 4 — review round 1 (2026-08-18)

**Refresh independence, through the path the fix added.** The reviewer's
point is precise: the existing continuous-input test uses `j`/`k`, which
never enters the ESC peek, so acceptance item 3 was unproven for the only
code this Work changed. Every raw cursor sequence now costs a short
blocking read for the byte after ESC, and the refresh deadline is
wall-clock — so a stream of them must neither postpone nor starve it.

The new case drives raw sequences every 0.3s against a 0.5s refresh on
the packaged artifact, while an external participant commits a Work
mid-session. It asserts the row APPEARS rather than merely being
present: absent from the opening screen, on screen by the end. Without
that first half it would pass even if the refresh never ran at all.

Break-sweep: making input reset the deadline reds it.

**Test provenance.** The module docstring still stated the superseded
cause — that the runner never enabled keypad translation — in the very
file whose subject is that the diagnosis was wrong. It now carries the
measured cause, names `curses.wrapper`'s `keypad(1)`, explains the
application-versus-normal cursor-mode split, and points at the dated
amendment in `FINDING.md`.

That is the third time this session I have left prose asserting a rule
the same change had just retired. The pattern is consistent enough to
name: I correct the code and the assertions, and the surrounding
narrative keeps the old claim because nothing fails when it is wrong.

### Evidence

- Focused: 8 passed.
- Gate: **1082 passed** + 13 serial + acp 36/36 on 32 cores.
- Whitespace check clean.
