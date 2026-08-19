# Progress

## 2026-08-19 UTC — `baton.claude` (implementer)

PLAN steps 3 and 4: the client-local editor round trip for a missing required
prose operand, ruled 2026-08-18 and approved by Slawomir. Client-local
presentation and grammar metadata only — no schema, no verb, no projection
change, and no authority read or write anywhere before submission.

## Revalidation against the current tree

- `Console.execute()` is still the single point where "the operator submitted
  this text" is true, and it still calls `_remember(line)` FIRST. That
  placement already implements the ruling's "history stores the surrounding
  command without generated prose" — the prose is authored after the
  remembering, so nothing had to be added to keep it out.
- `cli.analyze_partial` is still the grammar-owned partial analyzer that the
  assistance line and Tab completion consume, and it already applies form
  conditions "exactly as the parser enforces them". That is the metadata
  source the finding asks for, so no second analyzer was written.
- `_run_line` still routes through `cli.main`, so an authored value reaches
  the canonical path with the same grammar and the same refusals.
- The console holds no screen reference, which decided how the terminal is
  handed over (below).

## What changed

**Grammar metadata.** `_key()` gains `prose=`. It is metadata and nothing
else: parsing, refusals and generated help are untouched, and no caller is
obliged to act on it. Marked operands: `body`, `comment`, `observation`,
`rationale`, `reason` — 17 sites across the grammar.

Not marked, and each for a reason: `evidence` is documented as "where the
evidence lives", a locator rather than prose; `poke-answer explanation` is
documented as "a short human explanation" and that verb is answered by
runners, for whom an editor round trip would be actively wrong. Both are
one word away if the reviewer disagrees — which is the point of putting the
decision in the grammar instead of a verb list.

**`cli.missing_prose_operand(buffer)`** answers which required prose operand a
line is still missing. Pure, grammar-owned, beside `analyze_partial` and
`complete_partial` rather than in the TUI, so the console never reaches into
spec internals.

**`prose_template()` and `strip_prose_template()`** are module-level and pure,
so the byte-preservation rules are assertable without a terminal, an editor or
a store.

**`Console._author_prose()`** performs the round trip; `_prose_refused()` hands
the draft back.

## Three decisions the ruling did not make

**1. The editor opens only when prose is the LAST thing missing.** This is the
one I most want reviewed.

The approved contract says saving "supplies that one missing value and resumes
the same canonical command execution path". That promise cannot be kept when
something else is also missing: `close work=W2` needs `outcome=` too, so
authoring a paragraph there ends in a refusal anyway, with the operator's
prose spent on a line that was never going to run. The ordinary
missing-operand refusal names everything at once and is the better answer.

The evidence that this is right rather than merely convenient: it is what
makes the change strictly ADDITIVE. Two W26 reverse-search tests use `close
work=W2` as history filler and started failing when the editor opened on a
line that also lacked `outcome=`; under this rule they pass untouched, because
that command's behaviour did not change at all.

An unresolved exactly-one form (`heading`) and an unmet conditional (`notes`)
are the same situation under other names, and are excluded the same way.

**2. Terminal hand-over uses `curses.endwin()` and the render that follows.**
The console holds no screen reference, and the run loop already calls
`console.render(screen)` after every key — whose final `screen.refresh()` is
exactly what restores curses after `endwin()`. So the editor gets the terminal
without the Console learning about the screen, and outside curses the
`curses.error` is caught and ignored, which is what lets the whole suite run
in-process with no PTY.

**3. The refusal is shown BESIDE the restored draft, not on the status row.**
"Cancelling returns to the intact command draft" means the bar reopens holding
the command — and the status row is drawn only when the bar is closed, so a
refusal put there would be invisible. `command_note` is a one-shot line
rendered where the assistance hint goes, retired by the next keystroke exactly
as the status row is in navigation.

## The removal rule, and why it is positional

`strip_prose_template` removes the leading contiguous run of comment lines,
one blank separator if it survived, and one trailing newline. Everything else
is preserved byte for byte.

It is deliberately POSITIONAL rather than a match against the block that was
generated. A rule that only removed lines it still recognised would leak
instructional text the moment an operator edited one of them, and
"instructional text can never leak into the submitted body" is the acceptance
boundary that outranks every other consideration here. The cost — a `#` line
the operator puts at the very TOP goes with the block — is stated in the
template itself, and a `#` line anywhere else is content, which is the
ruling's own distinction.

## Safety properties, each pinned

- **`EDITOR` only, split without a shell.** Resolving `VISUAL` too, or falling
  back to a guess, would mean Baton sometimes choosing an editor the operator
  never configured. Handing the value to a shell would make the environment a
  command-injection surface for a feature whose whole job is to open a text
  file. A test puts `$(...)` and `;` in `EDITOR` and asserts they arrive at
  the editor as literal argument text.
- **Mode 0600, explicitly**, not by relying on `mkstemp`'s default — the draft
  holds whatever the operator is about to say. Asserted by the fake editor
  stat'ing its own argument.
- **The draft is removed in a `finally`**, asserted by capturing the path the
  editor was given and checking it afterwards.
- **The authored value is appended as an argv TOKEN**, never spliced into a
  command string, so there is no second round of shell quoting for a body with
  quotes, newlines or Unicode to survive.

## Regressions — `tests/work/test_w36_editor_backed_prose.py`, 46 tests

A deterministic fake editor: a generated script, no terminal, no interaction,
recording the exact argv it received so argument safety is observable rather
than argued. An autouse fixture removes any inherited `EDITOR`, so a developer's
own editor can never make one of these pass by accident.

Covered: the grammar's answer for sixteen lines including the conditional
`phase to=parked` case and the "prose is not the last thing missing" case;
prose as metadata with no per-verb enumeration; the template naming operation,
field, context, save and cancel; eleven authored bodies round-tripping byte
for byte (quotes, newlines, leading and trailing blank lines, Unicode, comment
characters, 5000 characters); the leading-run rule; the successful path
reaching the authority exactly; a supplied operand never invoking the editor;
argv safety; file mode and cleanup; unset, malformed, unlaunchable, nonzero
exit, unchanged template and whitespace-only body each keeping the draft; the
restored draft being immediately editable and the note retiring on the next
key; history keeping the command without the prose; recall opening a fresh
editor; and the authority hashed FROM INSIDE the running editor to prove
nothing committed before submission.

One test defect worth recording, because it would have made three purity
assertions vacuous: the first cut hashed only the database file. The authority
runs in WAL mode and this suite keeps its own connection open, so no
checkpoint happens and a commit never reaches that file — "nothing changed"
could not fail. The digest now covers the database and its `-wal`, and
deliberately not `-shm`, which ordinary reads rewrite.

## Break-sweeps

Each defect reintroduced alone against the 46-test suite.

| Reintroduced defect | Result |
| --- | --- |
| The instructional block is not removed | 19 red |
| Only still-recognised block lines are removed (the leak) | 19 red |
| `EDITOR` is run through a shell | 3 red |
| A nonzero editor exit submits anyway | 1 red |
| An empty body submits anyway | 2 red |
| The draft is lost on refusal | 7 red |
| History keeps the generated prose | 2 red |
| The draft file is world-readable | 1 red |
| The draft file is left behind | 1 red |
| The editor opens when more than prose is missing | 2 red |
| Prose-ness comes from a hard-coded verb list | 4 red |

## One existing test retargeted

`test_tui_packaged.py`'s scenario step 7 — "a refused command surfaces the
PUBLIC refusal in the console" — used `close work=… outcome=satisfying`, which
under W36 is exactly the line that now offers an editor instead of refusing.
With `EDITOR` unset in the test environment the bar stayed open holding the
draft, the trailing `qy` was typed into it as literal text, and the console
never exited.

`outcome=` is dropped so the command still refuses at the parser, which is
what that step is about, and the refusal still names `rationale`. The
assertion is unchanged. This is the same class of adjustment W7 needed and for
the same reason: the step's subject was never the particular command.

## Gate

`just test-v11`: **1891 passed**, serial **40 passed**, ACP **42/42**.
`tools/codex-event-bridge`: **45 passed**. The whitespace check is clean.

## Not done

- **The `::` batch buffer is untouched.** Its lines are submitted together
  through `_batch_go`, and pausing a batch to open an editor mid-run is a
  different interaction with its own cancellation questions. The finding is
  about Enter on the one-line bar.
- **Nothing deployed.** The running set at `/home/sl/baton-v11` is release
  `7bea055` and was not restarted.

## 2026-08-19 UTC — `baton.claude` (implementer), second pass

Changes requested by `review-2026-08-19T03-36-08Z.md`: a foreground-editor
interruption escaped the round trip, terminated the TUI, and lost the command
draft. One correction; everything else in that review was accepted and is
unchanged.

The review is right, and the failure mode is worse than the words suggest.
`_command_key()` closes the bar BEFORE calling `execute()`, so by the time the
editor is running there is no draft anywhere but a local variable. A
`KeyboardInterrupt` escaping from there does not merely abandon the edit — it
unwinds through `handle()` and the run loop with the operator's command still
in a stack frame.

## The correction

`_author_prose()` now catches `KeyboardInterrupt` and turns it into the same
safe cancellation every other failure of the round trip already produced: the
private draft is removed by the existing `finally`, the intact command and its
caret go back into the bar, the note says editing was interrupted, and nothing
reaches the authority.

Two things about the shape of it:

**It covers the whole interaction, not only the wait.** The review reduces the
case to `subprocess.run` raising, and that is where a SIGINT almost always
lands — a terminal signal reaches the whole foreground GROUP, so Baton gets it
alongside the editor it is waiting on. But an interrupt arriving a moment
later, while the authored text is being read back, escapes by exactly the same
route and tears the console down just as completely. Catching it only around
the wait would leave that window open, so the handler spans the write, the
launch and the read-back.

**`KeyboardInterrupt` is a `BaseException`.** It is named explicitly or it is
not caught at all — no `except Exception` anywhere would have covered this,
which is part of why the original round trip looked complete.

While in that block I also moved `os.fchmod` inside the `with` that owns the
descriptor `mkstemp` returns. Previously a failure between `mkstemp` and
`fdopen` — including an interrupt — leaked the descriptor. The mode is
unchanged and still explicit.

## Regressions added

`test_an_interrupted_editor_restores_the_draft_and_cleans_up` came with the
review and now passes. Two more, because the correction is wider than the case
that was reported and the wider part deserves its own evidence:

- `test_an_interrupt_during_the_read_back_is_also_a_safe_cancellation` —
  interrupts the read rather than the wait, and asserts the same three
  properties: draft kept, authority untouched, private file gone.
- `test_the_draft_descriptor_is_closed_on_every_path` — counts the process's
  own open descriptors across five refused round trips.

Suite is now 49 tests.

## Break-sweep

Reintroducing the defect — the handler catches something a `KeyboardInterrupt`
is not — reproduces exactly what the review observed: **pytest is itself
interrupted**, exits 2, and 40 of 49 tests complete. That is the sweep's whole
point here. The escape does not fail a test; it takes down whatever is running
the code, which in production is the console.

## Gate

`just test-v11`: **1910 passed**, serial **40 passed**, ACP **42/42**.
`tools/codex-event-bridge`: **45 passed**. The whitespace check is clean.

This also clears the one red the W73 handoff reported: that failure was this
regression, added by this review, and the tree is now green with both Works'
changes in it.

## State

Awaiting re-review at PLAN step 5. Nothing deployed: the running set at
`/home/sl/baton-v11` is release `7bea055` and was not restarted.
