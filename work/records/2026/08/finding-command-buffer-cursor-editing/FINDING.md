# Finding: recalled commands cannot be edited in place

## Status

Confirmed defect reported by Slawomir during the projection-11 v11 trial on
2026-08-18. This follows the completed command-history work at
`work/records/2026/08/finding-v11-command-mode-ergonomics/`.

## Observed

Up and Down recall submitted `:` commands, but the recalled line has no
editable cursor. Printable input is appended and Backspace removes only the
last character. Correcting an operand in the middle therefore requires
deleting the entire suffix and typing it again, defeating the primary
recall-edit-resubmit workflow for command history.

Current code confirms the report. `Console.command` is only a string and
`_command_key()` has no command-caret state: it handles history Up/Down, Tab,
Enter, Esc, suffix Backspace, and printable append. The W26 regression named
"editing a recalled entry" only changes the final character, so it did not
exercise an interior edit.

## Confirmed direction

The one-line `:` command bar must be a real editable line. A command recalled
from history remains an independent draft and must support moving the visible
caret to an earlier operand, inserting there, and deleting there before
resubmission. Editing never mutates the stored history entry or touches Baton
authority state before Enter.

## Open key-map decision

"Vi-style cursor editing" needs one precise input contract because ordinary
command entry is already an insertion context: bare `h`, `l`, `i`, and `a`
must remain literal command text, while Esc currently cancels the bar. The
minimum non-modal contract would use Left/Right, Home/End, Backspace, Delete,
and optional readline controls such as `Ctrl-A`/`Ctrl-E`. A true modal vi
editor would instead need an explicit normal/insert-mode design and visible
mode state. This choice must be settled before implementation.

## 2026-08-18 key-map ruling — approved

Use a non-modal line editor. This ruling closes and supersedes the open
key-map question above:

- Left and Right move by one Unicode character; Home/End and
  `Ctrl-A`/`Ctrl-E` move to the beginning/end.
- Backspace removes the character before the caret; Delete removes the
  character under it; printable input inserts at the caret.
- Printable `h`, `l`, `i`, and `a` remain literal command text. There is no
  hidden normal mode or second cursor grammar.
- Esc retains its existing visible meaning: cancel command entry without
  execution.

The caret is explicit presentation state shared by freshly typed, recalled,
reverse-search-adopted, seeded, and completion-expanded command drafts.

## Acceptance boundary

- A recalled command can be edited at its beginning, middle, and end.
- Left/Right movement and insertion/deletion preserve Unicode-safe character
  boundaries and keep the actual caret aligned with the rendered cell.
- Horizontal viewporting keeps the caret visible on narrow terminals.
- History entries remain immutable; editing changes only the current draft.
- Completion, reverse-search adoption, contextual `say` seeding, Esc cancel,
  and Enter submission compose with the same cursor state.
- Command editing performs no authority read or mutation before submission.
- Focused pure-state and real-terminal tests cover interior edits, boundaries,
  wide characters, resize, history recall, and completion/search composition.
