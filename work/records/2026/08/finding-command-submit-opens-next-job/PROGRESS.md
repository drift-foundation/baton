# Progress

Implementer-owned. Work `W1568`, claimed by `baton.claude` 2026-08-19.

## 2026-08-19 — reproduced and diagnosed

Reproduced on a real pty with `repro_pty.py`. One Return from a terminal in
NEW LINE mode arrives as `CR LF`; ncurses' default `nl()` translates the `CR`
to `LF`, so the console reads two identical Enter keys. The first submits the
command, the second falls through to the Jobs Enter branch and opens Work
detail. Bare `CR` and bare `LF` submissions never reproduce it, and the pair
reproduces for read-only, mutating, refused and local commands alike.

Cause and correction pinned in `FINDING.md` under "Confirmed cause" and
"Confirmed decision", both dated 2026-08-19 and written before the code
changed.

## 2026-08-19 — implemented

`src/baton_work/tui/app.py`:

- `run()` selects `curses.nonl()` before the first read, so `CR` survives as
  `13` and stays distinguishable from `LF`. Every Enter branch in the console
  already accepted `10`, `13` and `curses.KEY_ENTER`, so no handler changed.
- New `_absorb_paired_linefeed()` collapses a `CR` immediately followed by an
  `LF` into one Enter, using the existing `ESCAPE_PEEK_MS` peek and pushing
  anything else back untouched.
- The loop's inline decode moved into a new `_read_key()` alongside the
  existing `_decode_normal_mode_cursor()`, so the terminal-spelling boundary is
  one named function the regressions can drive directly instead of restating.

No handler, no mode and no view semantics were touched. The command bar, the
`::` batch buffer, the search input and Work-detail entry all keep their
established behaviour; they simply stop seeing a doubled newline.

## 2026-08-19 — regressions

`tests/work/test_w1568_command_submit_enter.py`, 21 cases in two layers.

Real packaged PTY, following the W25 precedent (`test_w25_real_cursor_keys.py`)
that a terminal is the only thing that can fail for a terminal defect:

- a `CR LF` submission stays in Jobs for a read-only, a mutating, a refused and
  a local command — and each command is asserted to have actually RUN, so a fix
  that swallowed the submission itself could not pass;
- the view survives the refresh a projection-changing command causes, waiting
  past the 2s timer deadline with no further input;
- a later deliberate Enter still opens exactly the then-selected Job;
- all three Return spellings (`CR`, `LF`, `CR LF`) submit exactly once;
- two deliberate Returns stay two Returns, counted in the batch buffer where
  each Return opens a visible line — the pair collapses, the intent does not;
- bare Esc still cancels the bar promptly (W25's contract, re-proved because
  `nonl()` moves a bit on the same termios word).

In process, driving the real `_read_key`: the pair decodes to one Enter, two
Returns to two, a bare `LF` is untouched, anything following a Return is handed
on, the escape decode still runs — and `mode`/`detail_work` stay at Jobs across
a success, a mutation and a refusal. One test feeds the two bare `10`s that `nl()`
used to deliver and shows detail opening: the defect as a property, and the
argument for why no handler could have fixed it.

Confirmed non-vacuous: with the two lines of correction reverted, 12 of the 21
fail, including every case the acceptance boundary names.

## 2026-08-19 — verification

- `tests/work/test_w1568_command_submit_enter.py` — 21 passed.
- Focused TUI/PTY suites (`test_tui`, `test_tui_packaged`,
  `test_w35_command_cursor_editing`, `test_w25_real_cursor_keys`, `test_w19`,
  `test_w26`) — 119 passed.
- Full v11 gate, parallel portion (`-m "not serial" tests/work`) — 2609 passed.
- Full v11 gate, serial portion (`-m serial tests/work`) — 51 passed.
- ACP bridge acceptance (`just test-acp`) — 55 passed, 0 failed.

The complete `just test-v11` gate is green.

## Unrelated tree state

`work/records/2026/08/finding-teams-member-detail-table/FINDING.md` carries an
uncommitted 2026-08-20 supersession that this Work did not write and has not
touched. Noted so review does not read it as part of this change.

## State

Awaiting independent review.
