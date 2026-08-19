# Progress

## 2026-08-19 UTC — `baton.claude` (implementer)

PLAN steps 3 and 4: the non-modal editable `:` line ruled on 2026-08-18 and
approved by Slawomir. Presentation state only — no schema, no verb, no
projection change, and no authority read or write anywhere on the editing
path.

## Revalidation against the current tree

The finding's diagnosis still held exactly. `Console.command` was a bare
string; `_command_key()` handled history Up/Down, Tab, Enter, Esc, suffix
Backspace (`self.command[:-1]`) and printable append (`self.command +=`) and
had no caret at all. The renderer had two branches — fits, or an end-anchored
`"<" + tail` — and put the caret at the end of the buffer in both, which is
the defect stated in rendering terms.

Three facts the plan did not name that shaped the work:

1. **The bar had ten places that assigned `self.command`.** A caret is only
   meaningful relative to a particular buffer, so ten independent assignment
   sites is ten chances for the two to disagree. Everything now goes through
   one `_set_command(text, caret=None)`, and `caret=None` means the end —
   which is what every whole-buffer replacement wants.
2. **W25's terminal skew applies to Home and End too.** `keypad(1)` asks for
   application cursor mode, so a terminal in normal mode sends `ESC [ H`/
   `ESC [ F` and ncurses hands them through as a bare Esc plus two ordinary
   characters. Shipping the ruled contract without decoding those would leave
   two of its keys reachable from one kind of terminal and invisible from the
   other — precisely the defect W25 exists to have found once. `ESC [ 3 ~` is
   decoded for the same reason, and more urgently: Delete has no control-byte
   alternate the way Home and End have Ctrl-A and Ctrl-E.
3. **The renderer measured `len()`, not display cells.** With an
   append-only caret that never showed, because the caret was always at the
   end of what had just been drawn. With a movable caret it becomes a
   one-column drift per wide character, and every later keystroke then lands
   somewhere the operator was not pointing.

## What changed

- `Console.command_caret` — an index into the buffer's CHARACTERS, `0..len`.
- `_set_command()` — the one assignment, so buffer and caret cannot drift.
- `_command_key()` — Left/Right by one character, Home/End and Ctrl-A/Ctrl-E
  to the ends, Backspace before the caret, Delete under it, printable input
  inserted at it. Esc is handled before any of them and keeps its existing
  visible meaning; `h`, `l`, `i` and `a` fall through to the printable branch
  and stay literal text.
- `command_window(typed, caret, avail)` — a module-level PURE function
  returning the visible slice and the caret's screen column. No remembered
  scroll offset, so a resize cannot strand the caret: the next render simply
  recomputes it, and any width is testable without a terminal.
- `_cell_width`/`_cells` — the wcwidth rules `authority.cell_width` uses for a
  canonical handle. Deliberately not that function: it answers a VALIDATION
  question and returns `-1` to refuse a control character, while rendering
  must produce a number for whatever is in the buffer. The rules are shared;
  the answers cannot be.
- `_CURSOR_FINALS` gains `H`/`F`, and a new `_TILDE_FINALS` handles the
  `ESC [ n ~` forms including Delete, with the same push-back discipline W25
  established so a sequence that is not one of these is handed on untouched.

Composition, each with the caret it should have: a recalled entry, an adopted
reverse-search match and a seeded `say` draft all arrive with the caret at the
end; the reverse-search draft and the history draft are restored with the
caret they were left with, because a draft restored with the caret moved is
not the draft that was left; and the `say` seed removal carries the caret
across its own splice rather than throwing the operator to the end.

## Two defects my own tests caught, both worth recording

**Tab spliced its completion into the wrong place.** `_complete_command`
applies a completion by TYPING the remaining characters — deliberately, so
the `say` and `filter` seeds still fire. Once typing inserted at the caret,
completing `det` with the caret at Home produced `adet`. `complete_partial`
analyses the buffer's LAST token, which is not the token an interior caret is
in, so there is no correct place to splice its result. Tab now declines when
the caret is not at the end — the same conservatism the function already
applies to an ambiguous candidate or an open quote. A repeated Tab never
chooses for the operator, and that now includes never choosing WHERE.

**The `>` marker landed on the caret's own column.** The first cut reserved
cells for `<` and for the caret but not for `>`, so on a 44-column terminal
with the caret mid-line the marker was drawn exactly where the caret stood —
a marker covering the very character it stands in for, which is the one thing
the markers must not do. The reservation is now decided before measuring.
Only the real-terminal test could see this; every pure-state assertion about
the same window passed.

## Regressions — `tests/work/test_w35_command_cursor_editing.py`, 28 tests

Pure-state and real-terminal, as the acceptance boundary asks.

Pure state: the reported defect reduced (recall, walk back ten characters,
Delete and retype an operand); Backspace before the caret rather than at the
end; insertion at the beginning, middle and end; Home/End agreeing with
Ctrl-A/Ctrl-E; `h`/`l`/`i`/`a` staying literal; Esc cancelling with no history
entry and no authority bytes touched; both caret boundaries clamped with the
edge deletions as no-ops; an empty buffer surviving every editing key; Enter
submitting the whole line rather than the part before the caret; an INTERIOR
edit never reaching back into history, and the same entry re-recalled
unchanged; the draft and its caret restored past the newest entry; completion,
reverse-search adoption and cancellation, and `say`-seed removal each carrying
the right caret; the viewport swept across every caret position at every width
from 4 to 79; resize recomputing from the same buffer; and wide characters
keeping the caret on its own cell in both measurement and movement.

Real terminal (PTY, raw bytes a terminal actually sends): interior editing via
`ESC [ D` and `ESC [ 3 ~` with the visible caret asserted mid-line; `ESC [ H`/
`ESC [ F` reaching the bar; Ctrl-A/Ctrl-E needing no decoding at all; and a
44-column terminal keeping an interior caret visible with the `<` marker
present and the character under the caret being the right one.

## Break-sweeps

Each defect reintroduced alone against the 28-test suite.

| Reintroduced defect | Result |
| --- | --- |
| Insertion appends at the end (the reported defect) | 8 red |
| Backspace removes the last character (the reported defect) | 2 red |
| Left/Right do not move the caret | 11 red |
| A recalled entry does not reset the caret | 2 red |
| The caret column is counted in characters, not cells | 1 red |
| The `>` marker is allowed onto the caret's column | 1 red |
| Completion splices at an interior caret | 1 red |
| Delete does nothing | 2 red |
| Home/End raw sequences left undecoded | 1 red |

The last one reds only the real-terminal test, which is the W25 lesson
restated: a key `handle()` understands can still be invisible from a terminal.

## Gate

`just test-v11`: **1842 passed**, serial **40 passed**, ACP **42/42**.
`tools/codex-event-bridge`: **45 passed**. The whitespace check is clean.

One existing boundary test earned its keep during this work:
`test_the_tui_imports_only_the_shared_surfaces` bans the substring `INSERT`
anywhere in the TUI, and a comment of mine used the word in caps. Reworded;
no behaviour involved, and the ban did exactly its job.

## Not done, and why

- **The `::` batch buffer is untouched.** The finding is about the one-line
  `:` bar; the multiline batch editor is W19's own surface with its own
  line cursor. Extending caret editing to it is a separate decision, not a
  silent side effect of this one.
- **Keyboard input is still ASCII (`32..126`), unchanged.** The wide-character
  work here is about measuring and moving correctly through whatever is IN the
  buffer — seeded text, recalled text — because that is what the acceptance
  boundary asks for. Accepting non-ASCII keystrokes needs `get_wch` and is a
  different change with its own risks.
- **Nothing deployed.** The running set at `/home/sl/baton-v11` is release
  `7bea055` and was not restarted or activated.
