# Finding: command mode has no searchable history

## Observed

After a command executes or refuses, opening `:` starts with an empty buffer.
The operator cannot retrieve it to change one operand and must retype or paste
the whole operation.

## Confirmed decision — 2026-08-18

The one-line `:` bar supports shell-familiar history without changing command
execution:

- Up selects the next older submitted command; Down walks toward newer entries.
- The draft present before history navigation is retained. Down past the newest
  entry restores that exact draft.
- `Ctrl-R` opens incremental reverse substring search. Typing narrows the
  result and repeated `Ctrl-R` selects the next older match. The search state
  and selected command are visibly distinct from ordinary command input.
- Enter accepts the selected text through the existing command-bar execution
  path. Esc cancels search and restores the pre-search draft without execution.
- Every non-empty submitted command enters history, including a command refused
  by parsing or authority, because correcting a refused command is a primary
  use case. Cancelled drafts do not enter history. Adjacent identical entries
  collapse to one.

The initial history is bounded and client-session-local. Persistence across TUI
restarts is not implied: that needs a separate decision about per-authority,
per-participant state location, permissions, concurrent consoles, and command
bodies retained on disk. The `::` batch keeps its existing line navigation;
batch-history ergonomics are also separate work.
