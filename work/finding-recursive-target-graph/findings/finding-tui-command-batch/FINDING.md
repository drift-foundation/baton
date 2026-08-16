# Finding: the v11 TUI cannot stage and run a batch of commands

## Observed

The second v11 trial required many repetitive dependency commands to assemble
one release gate. The one-line `:` command bar executes on Enter, so a human
cannot paste, inspect, and launch several commands together. Folding multiline
editing into that same interaction would conflict with its contextual-help and
Enter-to-execute behavior.

## Confirmed decision — 2026-08-15

**Confirmed by Slawomir during the second v11 trial.** The TUI has two distinct
command interactions:

- `:` opens the assisted one-line command bar; Enter executes one command.
- `::` opens a multiline **batch** buffer; Enter adds a line and `Ctrl-G`
  performs **Go**.

Batch lines use the same accepted `verb key=value ...` operation grammar as
the CLI and one-line command bar. Multiline paste stages the commands without
executing them. A visible legend names Go and cancellation so execution is
never triggered by a pasted newline.

Go first parses and statically validates every non-empty line. If any line is
syntactically invalid, nothing executes and the invalid line remains available
for correction. Once syntax is clean, commands execute sequentially in written
order and stop at the first authority refusal. The UI clearly distinguishes
completed, failed, and unrun lines and retains failed/unrun input for editing.

A batch is not one atomic authority transaction. If command five refuses,
commands one through four may already be committed and must never be described
as rolled back. Implementation review must provide safe per-command retry
identity and interruption behavior consistent with WS-5; the convenience may
not turn uncertain execution into duplicate mutations.

This is a batch command list, not a scripting language. It initially has no
variables, control flow, shell expansion, file execution, or recursive
includes. Context assistance for the current batch line may reuse the shared
command specification, but preserving the rich one-line assist is why the two
modes remain separate.

The batch feature depends on the key/value operation grammar. It is queued for
the next immutable revision and does not modify the current trial in place.
