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

## Implementation boundary pin — 2026-08-16 (baton.impl, pre-implementation)

Pinned before coding, per T19. Everything below derives from standing
rulings (the confirmed decision above, WS-5 operation identity, the W13
shared grammar, the W14 assist/caret contract); no new product choice is
exposed, so no blocker is returned.

**Two interactions, one entry rule.** `:` opens the one-line assisted bar,
unchanged. A second `:` as the FIRST keystroke of an empty bar (i.e. `::`)
converts it into the batch buffer. The bar's behavior is not modified in
any other way.

**Staging is pure view state.** Typing, pasting, editing, and navigating
the batch buffer open no authority transaction, mark nothing seen, and
change no authority bytes (PTY byte-identity proof). Enter is only ever
a newline in the batch; a pasted newline can never execute. A visible
legend names Go (`Ctrl-G`) and cancellation (`Esc`).

**Preflight before any execution.** Go first passes EVERY non-empty,
not-yet-completed line through the session-identity guard (the fixed
`--config`/`--participant` refusal, verbatim from the one-line bar) and
THE shared parser (`cli._parse_invocation` — grammar, closed values,
form conditions), all static, before any authority access. Any refusal
marks its line failed with the public refusal text and NOTHING executes;
every line stays editable.

**Per-line operation identity (deterministic, per slot).** At each Go,
every MUTATING line (`cli.MUTATIONS` by parsed verb) that does not carry
an explicit `op-id=` is assigned a generated identity `batch-<uuid hex>`,
conforming to the WS-5 R82 id grammar. Identity is per LINE SLOT, not per
text: two identical lines in one batch are two commands and get two
identities — a batch is a list, never a set. A line's generated identity
is retained while its text is unchanged and DISCARDED on any edit (WS-5
fingerprints the typed input; reusing an identity across an edit would
refuse as an identity conflict, and an edited line IS a new command). An
explicit `op-id=` is never overwritten, injected twice, or stripped.
Non-mutating lines receive no identity — the operation semantics refuse
`op-id=` on pure reads, and the batch does not launder that refusal.

**Sequential stop, honest state.** Once preflight is clean, lines execute
strictly in written order through the SAME public CLI entry as the
one-line bar. The first nonzero exit stops the batch: earlier lines are
`completed` (committed — never described as rolled back), the stopping
line is `failed` carrying the public refusal, every later line is
`unrun`. Empty lines are skipped. Each line renders its state; a
successful mutating line schedules the ONE coalesced refresh.

**Retry.** A later Go executes only non-completed lines, in order.
`completed` lines are never re-executed by the batch. An UNEDITED
failed/unrun mutating line retries under its SAME retained identity, so
WS-5 effectively-once replays any committed result instead of duplicating
the mutation; an edited line runs as a new command under a new identity.

**Interruption.** Execution is synchronous and sequential in-process; the
keyboard cannot interrupt a running batch — there is no partial-line
uncertainty to represent. Process death discards the staged buffer AND
its generated identities: cross-session retry safety therefore requires
explicit per-line `op-id=`, exactly as at the CLI. The batch never claims
stronger recovery than the surface it drives.

**Retained buffer and cancellation.** Failed and unrun lines stay in the
buffer, editable, with their states and notes. Editing any line (including
a completed one) returns it to staged. `Esc` over a buffer holding any
text asks a one-row `Discard batch? y/N` confirmation (n/Esc returns to
the buffer unchanged); a batch whose lines are all completed (or empty)
closes without confirmation — there is nothing left to lose.

**No scripting.** No variables, control flow, shell expansion, file
execution, or includes. Current-line assistance MAY render through the
same shared analyzer, read-only, exactly as the one-line bar; the two
modes stay separate interactions.
