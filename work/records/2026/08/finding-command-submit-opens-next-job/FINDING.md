# Command submission opens the next Job

## Observed — 2026-08-20

From the Jobs table, with a Job selected, opening the one-line command bar
with `:`, entering any command, and pressing Enter executes the command but
also opens the Messages/detail view for the next selected Job. The operator
submitted a command; they did not issue the Jobs-view Enter action.

The live report reproduces across commands rather than one verb or one
transition. A command that changes the projection may legitimately move or
refresh the selected row, but its submission must not be reinterpreted as
`Enter` on that resulting row.

## Confirmed implementation boundary

`Console.handle()` currently gives a key to `_command_key()` whenever the
command buffer is present and returns immediately. `_command_key()` clears the
buffer and executes on CR, LF, or `KEY_ENTER`. At that object-level boundary,
the submission appears consumed. The live behavior therefore needs a real
terminal/PTY reproduction before the fix is chosen: a second translated
newline, queued input around command execution, or another loop-level effect
must not be guessed from the pure handler alone.

## Required behavior

- Enter that submits a `:` command belongs only to command mode. After the
  command completes, the TUI remains in the Jobs view that launched it.
- Refresh or row-selection changes caused by the command do not open Work
  detail or Messages.
- A later, deliberate Enter in Jobs still opens the then-selected Job. The fix
  must not introduce a broad timing debounce that swallows intentional input.
- Success, refusal, replay/no-op, and storage-changing commands share this
  input boundary.
- Batch, search, editor-backed prose, and Work-detail command entry retain
  their established semantics unless the same concrete input defect is
  demonstrated there.

## Acceptance boundary

1. Capture the live key sequence through a real terminal/PTY and identify why
   one command-submission gesture reaches Jobs navigation.
2. Add a regression that submits a command while a Job is selected and proves
   `mode`, `detail_work`, and the visible view remain at Jobs after execution
   and refresh.
3. Cover at least one successful mutation and one refused or read-only command
   so the correction is not tied to projection changes.
4. Prove that a separate subsequent Enter still opens exactly the currently
   selected Job.
5. Run the focused TUI/PTY gates and the full v11 gate before independent
   review.

## Confirmed cause — 2026-08-19 (measured on a real PTY)

The "Confirmed implementation boundary" section above is right that
`Console.handle()`/`_command_key()` consume the submission correctly. The
crossover is one level below them, at the reader, and it is a terminal
spelling ncurses collapses before either method can see it.

**The reproduction.** `work/records/2026/08/finding-command-submit-opens-next-job/repro_pty.py`
drives the console on a real pty: open Jobs, press `:`, type a command, submit.
Submitting with a bare `CR` (`\r`) or a bare `LF` (`\n`) behaves correctly —
the command runs, the bar closes, and the view stays on Jobs. Submitting with
`CR LF` executes the command **and** opens Work detail on the selected Job,
which is exactly the reported symptom. Measured across read-only (`summary`),
mutating (`claim`, `classify`), refused (`bogusverb`) and local (`filter`)
commands, typed key-by-key and as one burst: the pair reproduces every time,
the singles never do. The defect is therefore a property of the SUBMISSION
GESTURE, not of any verb — which is what the live report said.

**Why one Return arrives as two Enters.** A terminal in NEW LINE mode (LNM,
`ESC [ 20 h`; xterm's `newLine` resource, PuTTY's "implicit LF in every CR",
and the equivalent "auto linefeed" setting elsewhere) transmits `CR LF` for a
single Return. `curses.wrapper` leaves ncurses in its default `nl()` mode,
which sets the tty's `ICRNL`, so the CR is translated to LF *before* the
console reads it. What the reader receives is captured directly:

    nl()   (today)      CR      -> [10]
    nl()   (today)      CRLF    -> [10, 10]
    nl()   (today)      CR CR   -> [10, 10]
    nonl()              CR      -> [13]
    nonl()              CRLF    -> [13, 10]
    nonl()              CR CR   -> [13, 13]

Under `nl()` one Return in LNM and two deliberate Returns are **byte-identical**
by the time any handler runs. `_command_key()` correctly consumes the first
`10` and closes the bar; the second `10` then reaches `handle()` with
`self.command is None` and falls through to the Jobs Enter branch, which sets
`detail_work`/`mode = "detail"`. No handler-level change can separate the two
cases, because the distinguishing byte no longer exists.

**Observed / Confirmed / Inferred.** Confirmed: the CR LF pair reproduces the
symptom, and `nonl()` preserves the distinction (both measured above).
Inferred: that the reporting terminal is in LNM. That inference is not load
bearing — under `nl()` a CR LF pair is the ONLY way one gesture can produce
two Enters, so whatever puts the terminal in that mode, the correction is the
same.

## Confirmed decision — 2026-08-19 (pinned before implementation)

The correction lives at the input boundary in `baton_work.tui.app.run()`,
the same place and the same class as
`work/records/2026/08/finding-tui-cursor-key-parity/findings/finding-real-terminal-cursor-key-decoding/`,
which decodes the normal-mode cursor sequences ncurses did not translate:

1. `run()` selects `curses.nonl()` before the first read, so `CR` survives as
   `13` and stays distinguishable from `LF`. Every Enter branch in the console
   already accepts `10`, `13` and `curses.KEY_ENTER`, so this changes no
   handler's behaviour.
2. The reader coalesces a `CR` immediately followed by an `LF` into ONE Enter,
   using the existing `ESCAPE_PEEK_MS` short peek and pushing anything else
   back untouched — the identical discipline `_decode_normal_mode_cursor` uses
   for `ESC`.

This is a DECODE of a terminal spelling, not a timing debounce, and the
distinction is what the required behaviour asks for: two deliberate Returns
arrive as `13, 13`, the peek sees a `13` rather than a `10`, pushes it back,
and both Enters are delivered. Nothing is suppressed on the basis of how
recently a command ran, so a later deliberate Enter in Jobs still opens the
selected Job.

The fix is at the reader and therefore below every mode, which is deliberate:
the batch buffer (`::`), the search input and Work-detail command entry all
insert or submit on the same newline, so a terminal in LNM doubles them all.
One coalescing reader corrects them together and keeps their established
semantics, which is what "retain their established semantics" requires.

Rejected alternative: suppressing an Enter that arrives shortly after a
command executes. It cannot distinguish the doubled gesture from a deliberate
second Return at all — it can only guess from timing — and the required
behaviour forbids exactly that.
