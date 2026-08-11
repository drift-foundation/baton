# Console human-trial package

Everything Slawomir needs to use the console, and the evidence that using it
cannot disturb the agent channel.

## Run it

    /home/sl/src/baton-tui-trial/bin/baton-tui \
      --config /home/sl/src/baton-tui-trial/baton.json \
      --participant human.slawomir

A self-contained deployment outside this repository: its own executable, its
own config, its own SQLite authority, its own projection directory. Deliberately
NOT the live protocol-9 instance — SELECTING a directed row in a console
claims a real message, and the trial exists so every key can be pressed
without consequence. (This said "pressing Enter", which was true before
claim-on-highlight and understates the exposure now: moving the cursor is
enough.)

## Keys

    j k  ↑ ↓     select          a directed message is CLAIMED and opened
    gg  G        first / last row
    Ctrl+u Ctrl+d  page the pane (PgUp/PgDn also work)
    Tab          move focus      between the list and the detail pane
    Enter        open a notice   marks an unseen broadcast seen and reads it
    r            reply           opens your external editor, one action
    R            quick reply     edits the inherited subject line, no editor
    c            close           terminal disposition
    h l  [ ]     pan / parts     sideways in the body; brackets select a part
    v            read a part     shows an external file's text in the pane
    m            materialize     writes the selected part to projections/
    n            new message     pick a recipient by letter, then subject/attach
    N            notice          subject / body
    Ctrl+r       refresh now     (it also polls every 2s)
    Esc          leave detail    back to the list; Enter is the way in
    ?            help            the modal shortcut list
    q            quit            always asks `Exit? y/N`; only y/Y exits

Vim browse bindings throughout. `g` is the `gg` prefix and does nothing on its
own, which is why manual refresh cannot live there; it is `Ctrl+r`, because
both plain-letter `r` spellings are reply keys. Every one of these letters is
literal text in reply and compose modes -- no browse chord can fire while
typing, and an abandoned `g` cannot combine with a later keystroke.

The status column says who owns the next action while an item is live —
`•` inbound and unopened, `○` opened and owed by you, `▷` sent and not picked
up, `▶` picked up by them, `!` an unseen notice — and what became of it once
it is done: one `✓`, whether you replied, closed it, or saw a notice. Which
of those it was is in the detail pane, exactly.

(This table said `r` was the quick reply and `R` the editor, with `^R` for
refresh, until the terminal trial reversed the pair and ruled the notation.
The rounds below are chronological, so the earlier entries describe the console
as it was then; THIS section is the current one.)

## What is seeded

Four directed messages and one notice, each chosen to exercise one thing:

| Subject | Shows |
|---|---|
| Plain message | the ordinary claim / reply / close loop |
| Multipart | `[0]`, `[1]` container with `[1.0]`/`[1.1]`, `[2]` binary |
| Attachment | an external pinned part beside an inline note |
| Hostile text | a real `ESC[2J` and a `\r` overwrite, neutralised |
| A broadcast | a notice: `!` marker, never claimable, seen once on open |

Projections land in `baton-tui-trial/projections/`. The pinned evidence file is
`baton-tui-trial/evidence/EVIDENCE.md` — edit it and reopen the attachment
message to see a broken pin fail closed.

## Isolation evidence

The console shares `baton_core` as SOURCE with nothing that ships today. The
agent CLI is untouched, and that is a test rather than a promise.

    CLI archive members      ['__main__.py', 'baton_v6.py']
    CLI contains TUI/curses  False
    CLI contains core        False
    TUI contains the oracle  False
    baton_v6.py imports core False

Frozen and unchanged:

    bin/baton          a23461ae7577422f5c4ade86eae370926b2dc41bc93ecd7732c29b2785374566
    DISTRIBUTION.json  fecab1081df3e2b34e40793db0d298a7be265ec0312b6a3c731cad38f70113a6
    baton_v6.py        6d9ffe8c8021bc692b3b474a8dc18cb468c5ce3b7a67d16e3cb838124e0f2671
    build_zipapp.py    711abdf58df1ce9ae440f27b1def64315b2e85c59935e0c31b651c2d2e0c1d30

Trial artifact:

    bin/baton-tui      8273567aa44c13a1658b743ca333548795413076b7596a42590066c130d6d50d
    tui 0.1.0   core api 1   protocol 9   manifest DISTRIBUTION-TUI.json

`build_tui.py` is a separate builder rather than an option on
`build_zipapp.py`: the surest way to keep something unchanged is for the code
that changes it never to run. Pinned that building the trial leaves the CLI,
its manifest and the oracle byte-identical, and that the build is
deterministic.

## Last differential gate, recorded read-only

Oracle `baton_v6.py` at
`6d9ffe8c8021bc692b3b474a8dc18cb468c5ce3b7a67d16e3cb838124e0f2671`, hash-pinned
by `test_oracle_stays_frozen`. The differential harness passes: the core and
the frozen CLI agree on every observable behaviour except two recorded,
justified additions (`created_ts` on claimed scan rows; a manifest `address` on
delivered parts), each additive only.

**This record does not authorize CLI adoption.** The core is an importable
library; whether the CLI ever uses it is a separate decision for Slawomir after
the trial.

## Results

1170 tests: protocol suite, core API, differential parity, hostile-input corpus,
screen model, renderer, key mapping, real-PTY integration, packaging isolation.
`git diff --check` clean.

## Known limits, stated

- The PTY smoke cannot catch oversized lines: `addnstr` clips and the driver
  swallows `curses.error`. Verified by deliberately breaking the width clamp
  and watching the PTY tests still pass. Width is proven by the pure renderer
  tests in display cells.
- The "terminal too small" notice is proven at every size by the pure tests but
  is flaky to assert over a real PTY under pytest, so it is documented rather
  than pinned. A flaky test trains people to rerun until green.
- `m` on an external part refuses: it is already a file, and copying it into a
  projection would duplicate the thing the pin exists to avoid.

## Deferred to pre-commit cleanup — now APPLIED

Recorded during the trial and deliberately not applied at the time, because
changing the source would have made the artifact Slawomir was exercising
differ from the one that was approved.

**`baton_core/__init__.py` opening paragraph was inaccurate.** It said the
`baton` CLI and `baton-tui` "are thin front ends over this package", and that
no behaviour exists in both. Neither was true: the released CLI is still built
from `baton_v6.py`, and the core is a byte-copy of it, so behaviour
deliberately exists in both for the duration of the parity interval. The same
file explained that correctly further down, which made the opening worse than
vague -- it contradicted its own body.

Rewritten for this commit: the TUI is named as the current consumer; the
duplication is stated explicitly as the frozen parity interval, with why fixes
must land in one copy only; and CLI adoption is described as an approved but
SEPARATE later stage that nothing in the package assumes.

## Trial defect fixed — relaunch required

Reported: the panes drew but no row looked selected.

Two causes, both real:

- **No highlight was ever requested.** The renderer emitted a `>` marker and
  the driver applied no terminal attribute. The selected row now carries a
  `selected` style which the driver draws as full-row reverse video, padded to
  the pane width so the stripe does not stop raggedly at the text. The `>`
  marker stays as a colour-independent fallback.
- **Arrow keys did nothing at all.** `getch()` returned raw `27, 91, 66`
  instead of `KEY_DOWN`: keypad translation was not happening, and for this
  terminfo the down key is `ESC O B` rather than `ESC [ B` anyway. The driver
  now decodes the sequences itself, accepting both forms, so arrows no longer
  depend on the terminal database. `ESCDELAY` is set to 25ms so a bare ESC
  does not stall for a second.

`j`/`k` were unaffected and continue to work.

Pinned: pure style tests (exactly one styled row, it follows the cursor,
marker retained, selection distinct from notice/claimed state, none when the
selection is off-screen), escape-sequence decoding for both arrow forms, and a
real-PTY assertion that reverse video appears and the highlighted TEXT changes
after an arrow key. All three were verified to fail when the fix is removed.

    new trial artifact  f75906e52397254694746b70348f9d08e9fb6079274b22dc47f7172c69946864

**Relaunch to pick it up** — a running console keeps the old code.

### Divider, folded into the same rebuild

Reported: the vertical pane separator appeared as disconnected dashes. It is
now U+2502 BOX DRAWINGS LIGHT VERTICAL, which joins between rows, with an
ASCII `|` fallback chosen at startup from the terminal encoding — a
box-drawing character on a non-UTF-8 terminal is worse than the bar it
replaced.

Writing the "same column on every row" pin exposed a REAL bug behind the
reported one: padding used character count, so an inbox row containing wide
characters occupied more cells than its budget and pushed the divider
rightwards on that row alone. Padding is now by display cells everywhere,
including the highlighted row the driver pads itself.

### Note recorded during the trial (no rebuild)

`pending_prefix` has **no clock**. A `g` stays a pending prefix until the next
keystroke: a non-`g` clears it, a second `g` completes `gg`. That is ordinary
Vim-style chord behaviour and is deliberate — a timer would make the same two
keystrokes mean different things depending on typing speed. Nothing in the code
or docs claims it times out; recorded so nobody later describes it that way.

## Trial round 3

- **Detail text wraps** instead of clipping. Clipping and wrapping are not
  interchangeable: once a tail is cut it cannot be scrolled to, so the end of
  every long line simply did not exist. Bodies, notices, headers, drafts and
  compose values all wrap by display cell, preserving explicit newlines and
  breaking tokens wider than the pane.
- **Panes are 40% inbox / 60% detail**, from a single `pane_widths` helper used
  by render, the detail line count, the caret and the selection styling. It
  was four copies of `max(24, columns // 2 - 1)`, which have to agree exactly
  or the divider lands in one column while the caret believes another.
- **`n` opens a recipient picker** sourced from the validated participant
  registry through a new read-only core API. A letter selects; the chosen
  address is then read-only, so there is no keystroke path back to a typed
  recipient. Typing an address is a typo caught only at send time, by which
  point the message is written.

## Trial round 3, corrections

Three review findings and one trial defect, all fixed and pinned. Every pin
below was verified to FAIL with its fix removed.

- **The picker pages by what FITS, not by the alphabet.** Capacity used to be
  `detail_height - 3`, a guessed reserve; the renderer now measures its own
  overhead (the prompt AFTER wrapping at this width, the blank line, the
  footer) and reports capacity through `set_viewport`. At 40x8 the wrapping
  prompt left no room for even one entry, so the prompt is now short --
  `send to:` -- and the full hint stays in the status bar, which is present
  anyway. Pinned that no letter is selectable unless it is drawn, at every
  size from the minimum upward, and at the real 21-recipient/100x24 case.

- **Wrapping reconstructs the original exactly.** The wrap was losing and
  duplicating characters at break points. It now satisfies
  `"".join(wrapped) == original` modulo the inserted breaks, across 12 corpora
  x 6 widths, and indentation stays with the line it belongs to. The break
  rule is explicit: only a space that FOLLOWS content is a break opportunity,
  so leading indentation cannot be silently eaten.

- **A growing draft cannot scroll its own caret off screen.** Reply and
  compose have no scroll keys -- every printable key is text -- so the model
  follows the caret after each keystroke instead of the human chasing it.
  Pinned at 100x24, 80x24, 61x20 and 40x10 that the line being typed stays
  inside the window, that the last characters typed are actually DRAWN, and
  that browse-mode `J`/`K` scrolling is not taken over by the same mechanism.

- **The selection highlight stops at the divider.** Reported: the stripe ran
  the whole terminal row, styling the divider and the detail row beside it, so
  it read as a full-screen band rather than "this row, in this list". The span
  is now `[0, inbox_width)`, derived from the same `pane_widths` helper that
  places the divider, so the two cannot drift apart. Drawing the row needed an
  exact cell-boundary split (`split_cells`), because slicing by CHARACTER put
  a wide character one cell past the seam -- the same class of fault that
  pushed the divider off its column in round 2. A wide character straddling
  the boundary goes to the tail, never the head. Pinned in three places: the
  span arithmetic at seven widths, the seam landing exactly on the drawn
  divider including wide-character inbox text, and a real-PTY assertion that
  no reverse-video run contains the divider or exceeds the pane width.

### Unrenderable media types, decided

Slawomir's ruling is recorded in
`work/finding-tui-markdown-rendering/FINDING.md`: a type this console cannot
render offers **show raw** when the envelope declared it text-based, and
**save to file** otherwise. This also settles the escalated `text/html`
question without a separate ruling -- no HTML renderer exists here, so
`text/html` is unrenderable-but-text-based and gets the raw view. A
tag-stripping half-renderer is rejected: it discards structure the sender
declared as meaningful. Decision only; no console code implements Markdown or
HTML rendering yet.

### `just test` now runs what it says

The recipe was documented as "the complete reusable test suite" and ran only
`test_baton_v6.py`. A test command that silently covers a third of the suite
is worse than an honest partial one, because it is trusted. It now runs the
protocol suite, core parity, core API, the four TUI suites, the real-PTY
suite and packaging isolation: **1299 tests**. `just build-tui` was added
beside `just build` so the console has a named build path that never invokes
the CLI builder.

    new trial artifact  1d88a4cfb8ebfc3365e1b806e9694741b89c516042fd4129ff095799c5005d83

Deterministic on rebuild. `bin/baton`, `DISTRIBUTION.json`, `baton_v6.py` and
`build_zipapp.py` are byte-identical to before this round.

**Relaunch to pick it up** -- a running console keeps the old code.

## Trial round 3, re-review corrections

The re-review confirmed the common 100x24 behaviour and rejected two claimed
EDGE guarantees. Both reproductions were exact; both are now fixed with the
real live-registry addresses pinned, not short fixture names.

- **The picker now pages by measured layout.** The previous version wrapped
  the prompt and then subtracted a fixed `1 + 2`, assuming every entry and the
  footer occupy one row each. At 40 columns a real address wraps to two rows,
  so letters `c`, `d`, `e` were offered and never drawn -- and the footer that
  would have said so was pushed off the pane. The entries are now laid out for
  real and counted until the pane is full, from the SAME helper that draws
  them; the footer is reserved only when there will be one, which needs a
  second pass because the count decides it. The two blank separator rows are
  gone: at 40x8 they were the difference between drawing one recipient with
  its page position and drawing a letter the human can press but cannot read.

- **Resize follows the caret with no keystroke.** Following happened only at
  the end of `step`, so a resize moved the viewport without moving the offset:
  after narrowing, a draft's tail and caret were off-screen and stayed there
  until one more character was typed. Layout and following are now one helper
  used by both the keystroke path and the redraw path, so a resize cannot
  follow a different rule from a keypress. Pinned narrowing AND widening.

- **Overlong unbroken content is elided, not fractured** (Slawomir's ruling).
  Read-only detail content and headers wrap at whitespace; a token wider than
  the whole pane shows its fitting prefix and U+2026. Editable text keeps the
  lossless wrap -- hiding characters someone is typing is a worse fault than
  hiding characters they are reading -- and picker addresses keep it too,
  because two accounts differing only in their tail would render identically.

- **The selected part header is visibly marked.** U+25B8 plus bold+underline,
  deliberately NOT the inbox row's reverse video: the two cursors mean
  different things -- which message Enter opens, and which part `m` writes
  out -- and a human who cannot tell them apart has two cursors that look like
  one. The mark moves with `h`/`l`, covers header rows only, and vanishes when
  the header scrolls out of the pane.

- **Part headers show the advisory filename**, beside address, media type and
  disposition: `[1] image/png  attachment  diagram.png`. The filename is a
  label, never a path; `m` keeps its own generated destination.

### What the deliberate-break checks caught this round

Three of these fixes were verified by removing them and watching the pins
fail. Two of those checks found real faults that the passing tests had not:

- The first part-mark implementation recorded EVERY leaf's header, so every
  part looked selected. The test passed because it only asserted that marked
  rows are headers and content rows are not. It now asserts exactly one part
  is marked.
- The first ellipsis pin searched the whole screen for U+2026 -- but the inbox
  column truncates with `fit`, which also emits U+2026, so the assertion held
  whether or not the detail pane elided anything. It is now scoped to the
  detail pane and also asserts the token was not fractured.

A third fault was found while writing the pins rather than by running them:
`layout_for` called without recipients returned a capacity computed from an
empty list, silently resetting a correct capacity to 1. It now omits the key
instead, and `set_viewport` treats an absent capacity as "leave it alone".

- **Part headers say "part name", not "filename"** (Slawomir): a part is not
  a file, and the recipient decides what to do when materializing it. The name
  is rendered directly, with no `filename:` label. The wire field is still
  `filename` at protocol 9; renaming it is protocol-10 work, reported as a
  boundary question rather than started.

    protocol-9 build  e61a814673cf6694d583cca496f30d4de18e27439dbe1286c0de3284b0111284
    just test         1368 passed

Deterministic on rebuild. `bin/baton`, `DISTRIBUTION.json`, `baton_v6.py` and
`build_zipapp.py` byte-identical.

## Staging, and a supersession that was itself superseded

Recorded because the intermediate state is confusing to read otherwise, and a
document that quietly loses a reversal is worse than one that shows it.

Briefly, this protocol-9 console was marked superseded, on the expectation
that `part_name` would be folded in and the review would verify one combined
protocol-10 artifact. Slawomir then corrected the order. **This protocol-9 TUI
+ `baton_core` work is the current deliverable again**, to be brought to
reviewed commit readiness on its own.

Three stages, landed separately:

1. **This work.** Protocol 9, TUI + core, with the CLI source, artifact,
   builder and distribution untouched. Reviewed, then committed.
2. **CLI-to-core adoption.** Only after that commit, in a NEW work folder and
   branch. Still protocol 9, no behaviour change, parity proven against the
   frozen oracle, landed separately.
3. **Protocol 10 `part_name`.** Only after adoption lands.

Why the rename cannot simply be done now, which is what forced the staging:
`filename` lives in the SCHEMA TEXT, and that text exists in two copies today
(the frozen oracle `baton_v6.py` and `baton_core/_impl.py`). Renaming it means
either duplicating a breaking change across two implementations -- ruled out
-- or changing the hash-pinned oracle. Stage 2 removes the duplication first,
so stage 3 writes the rename once.

TUI wording is already "part name" (stage 1, display only). The protocol-9
field remains `filename`. No adoption or rename work exists in this tree.

## Pre-commit trial defect: an attachment IS content

Slawomir found this while exercising compose after approval.

Protocol 9 requires a message to have content, and the console read "content"
as "a body". But an external attachment is itself a content leaf, so a message
carrying only an attachment is valid and the console was refusing it -- the
front end had invented a rule the authority it fronts does not have.

Fixed, with the boundaries stated rather than left to the code:

- **Attachment with no body sends the external leaf ALONE.** Adding an empty
  inline text part to satisfy a content check would put a part on the wire
  that the sender never wrote. Pinned that exactly one leaf exists and that it
  is the external one -- the tempting wrong fix passes a "did it send?" test.
- **Neither body nor attachment is still refused.** A subject alone is not
  content: it is metadata describing content that does not exist. Pinned that
  nothing is written on refusal.
- **A whitespace-only body is content.** The emptiness test used `strip()`,
  so a body of spaces or newlines was silently discarded. The store accepts
  those bytes; indentation and blank lines are content in Markdown, which is
  what the body is declared as. The same `strip()` was on the REPLY path and
  is corrected there too -- it is the same defect, and fixing only the
  reported half would have left it live.
- **Notices still require a body**, because they expose no attachment field.
  Pinned, so the attachment rule cannot leak into a flow with no attachment.
- **Compose buffers survive every failed send** -- no recipient, no content,
  and a store-side rejection such as a missing attachment path. Retyping a
  message because the console threw it away is the kind of small betrayal
  that stops people using a tool.

Both the old rule and the tempting wrong fix were applied deliberately and
watched to fail.

### Addendum: the one-line subject quick send

Slawomir wants a quick one-line message to cost as few keystrokes as
possible. Compose already opens focused on the subject and Enter already sends
from any field; what was missing is that a subject alone was refused, so the
fastest message still required a Tab and a retype of the same words.

Subject-only composition is now protocol-9 shorthand: when the subject is
non-empty and both body and attachment are empty, the subject text becomes the
single inline `text/markdown` content part AS WELL AS the subject.

The boundaries, each pinned:

- **The content part carries the subject TEXT**, not a zero-byte placeholder.
  An empty leaf would make the message unreadable to anything that renders
  content rather than headers.
- **A body suppresses the shorthand.** An explicit body is what the sender
  wrote and the subject is a summary of it; substituting one for the other
  would silently discard the message.
- **An attachment suppresses it too.** Subject plus attachment stays
  attachment-only; synthesizing an inline duplicate of the subject would put a
  second leaf on the wire the sender did not write.
- **Truly empty is still refused** -- no subject, no body, no attachment.
- Shift+Enter is deliberately NOT a path: it is not portable across curses
  over SSH, so plain Enter has to be sufficient on its own.

The shorthand is invisible unless it is stated, so both the compose prompt and
the status bar say "Enter sends from any field — a subject alone is enough".
Writing that pin exposed a soft test of my own: it searched the WHOLE SCREEN
for the phrase, which the status bar satisfied, so deleting the prompt hint
left it green. It now checks the detail pane and the status bar separately,
and whitespace-insensitively, because the hint wraps at the pane width and
`render` rstrips each row.

Two earlier tests asserted "a subject alone is refused", which this decision
supersedes. They now pin the narrower rule that survived -- truly contentless
is refused -- rather than the rule they replaced.

### Addendum: Enter arms the send, `y` publishes it

The shorthand above created the hazard this fixes. Compose opens focused on
the subject and a subject alone is now enough, so Enter had become a
ONE-keystroke publish reachable from a field a newcomer is still filling in --
and Enter is the key people press to mean "next field".

Enter now ARMS a confirmation in reply, compose and notice alike. The quick
path is still two strokes, Enter then `y`, but the second one cannot be
pressed by reflex.

- `Send? Y/n` -- conventional shell semantics, YES as the default, so `y`,
  `Y` or a second Enter publishes. The fast path is Enter, Enter.
- `n`/`N`/Esc returns to the SAME draft, the SAME field, buffers untouched. A
  cancelled send that cost the human their message would be worse than no
  confirmation at all.
- An earlier rule made a second Enter INERT, so a reflex keystroke could
  neither publish nor cancel. Slawomir superseded it in favour of the
  conventional default. What still holds, and is what the confirmation is
  for, is that the FIRST Enter cannot publish: the reflex now lands on a
  question that names what is about to happen, with the draft still on screen
  behind it. Pinned separately from the confirm rule, so the correction cannot
  quietly take the guarantee with it.
- **Printable keys are swallowed too.** While confirming, `q` is not quit, `c`
  is not close, and letters do not reach the draft they are no longer editing.
- A send the authority REFUSES returns to the draft rather than leaving the
  human in a dead confirmation.
- The draft stays drawn behind the question: a confirmation over a blank pane
  asks someone to approve something they can no longer see. The footer becomes
  ONE row and that row IS the whole footer, to Slawomir's literal target:

      Send now? [Y/n]   Enter or y = send   n or Esc = keep editing

  No severity prefix, no separate status row, no context row, no duplicate in
  the detail pane. The row the second footer line used to occupy goes to the
  PANES rather than disappearing, so the screen is still exactly `lines` rows
  and the draft gains a line -- the question is small and what you are about
  to send is not.

  Footer height is now read from one helper by everything that divides the
  screen up. A footer that changes height while the body arithmetic does not
  is how a row goes missing or gets drawn twice; removing that coupling fails
  the row-count pin immediately.

Every prompt now says Enter REVIEWS the send.

Nine existing driver tests pressed one Enter and expected an immediate
publish. They go through a `_send` helper that presses Enter then `y` -- and
that helper ASSERTS the confirmation was armed, so a regression which
publishes on the first Enter fails there rather than being absorbed by a
helper that just presses both keys.

All four failure modes were introduced deliberately and each fails its pin:
publishing on the first Enter, letting Enter confirm, letting printable keys
through, and discarding the draft on decline.

### Verified on a real terminal

Both confirmation properties are now pinned through a real PTY, not only
through the model and renderer:

- `n`, pick a recipient, type a subject, Enter, Enter -- and a message with
  that subject lands in the queue. Nothing else is typed: no `y`, no Tab, no
  body.
- The armed state paints `Send? Y/n` and does NOT paint `SEND THIS?` or
  `keep editing` anywhere.

Restoring the two-row footer fails the second immediately. **SUPERSEDED
2026-08-10:** the quit confirmation is ONE row now, like every other
mode. It asks with nothing owed as well, where the second row would have
said "0", and the outstanding count it recited is already on the header
and in the list. The statements below about a two-row footer describe the
shape this trial ran against and are kept as history, not as the current
contract.

The first PTY attempt drained output between keystrokes and returned empty
strings for repaints that had plainly happened. The transcript is accumulated
throughout instead; a single window of it is not a reliable artifact.

**A rationale I had to withdraw.** I wrote that this test proves Enter arrives
as CR rather than the LF the model tests send. It does not: removing
`ENTER_CR` from the confirm mapping leaves the test green, because the line
discipline maps CR to LF before curses sees it. `ENTER_CR` stays in the
mapping for a console run in raw mode, but nothing pins it and the docstring
no longer claims otherwise. Checking the break is what caught the claim.

### A pin that policed itself

Worth recording, because it looked thorough and was not. Every assertion on
the confirmation footer compared the rendered row against
`render.CONFIRM_SEND_FOOTER` -- the same constant that produced it. Editing
the constant moved both sides of the assertion, so the text could drift
freely: deleting the brackets from the literal passed EVERY pin in the suite,
including the PTY ones.

The literal is now written out in the tests as well, in one place in the
driver suite and one in the PTY suite, with a third pin asserting the shipped
constant equals that literal. Dropping the brackets now fails three tests.

A constant is the right way to stop a string drifting between two production
call sites. It is the wrong way to pin a value someone else specified.

### What a curses transcript cannot prove

The review asked for "exactly one footer row" to be asserted on a real
terminal. It cannot be, and the reason is worth recording rather than working
around.

A second footer row would be the context line at row 23. Curses repaints only
CHANGED cells, and row 23 already reads `acting on: ...` before the send is
armed -- so with the two-row footer deliberately restored, nothing is written
to row 23 at all and the transcript is byte-identical either way. The
assertion passed with the fault present, which makes it worse than no
assertion: it would have reported a regression as fixed.

So the property lives where it can be stated exactly: the pure renderer, at
8/12/24/40 lines, across reply, compose and notice, asserting one footer row
AND exactly `lines` rows total AND one more body row than the ordinary footer
leaves. The PTY test pins what only a terminal can show -- that the full
literal reaches the screen, on the bottom row.

Three assertions were written and discarded before this one, each verified by
deliberately restoring the two-row footer and watching them pass.

## SENT view — outbound history, authority-backed

Slawomir reopened the stage for this. The console could show what you sent by
remembering it, and that list would be wrong twice: empty after a restart, and
frozen at "pending" forever. The whole value of a sent view is watching
pending become claimed, so the state comes from the same rows that decide it.

- **`i` and `o` switch ONE full-height pane.** Not a split: the left pane is
  40% of a terminal already, and halving it would make both lists unreadable
  to save one keystroke. INBOX stays the default and keeps its actionable
  semantics and FIFO order. (Both details were later superseded: R7 stacked
  the panes, and Slawomir ruled MESSAGES newest-first. Noted here rather than
  rewritten, because this entry records what was true at the time -- but a
  stale sentence in a history file still reads as a specification unless it
  says otherwise.)
- **SENT is newest-first**, with the id as a tiebreak so the order is TOTAL.
  Pinned as that property rather than against `scan`'s pending order, which
  sorts by `created_ts` alone -- two messages sent inside the same second come
  back from it in whatever order SQLite happens to produce, so comparing
  against it would make the test pass or fail on timing.
- **Badges**: `[Q]` queued, `[P]` picked up, `[R]` replied, `[C]` closed,
  `[E]` expired, `[X]` quarantined, `[N]` notice. A notice gets its OWN badge
  rather than borrowing a directed state -- it has no claim, so `pending` and
  `claimed` would both be lies. What it has is receipts and a lifetime, and
  those are what its row shows. A legend sits in the detail pane, and the
  badge table is pinned to cover every state the schema permits, so a state
  the authority can produce never renders as `[?]`.
- **Nothing in SENT writes.** No claim, no receipt, no transition, no audit
  row. Pinned by counting every table a delivery touches before and after
  switching views and opening every row.
- **Enter opens your own copy, read-only.** Owner-checked in the CORE, not
  merely hidden by the view, and external pins are revalidated exactly as
  delivery revalidates them: the sender is the last person who should be shown
  bytes that no longer match what the recipient will get.
- **Each view keeps its own cursor and scroll.** Switching back lands where
  you were, or the switch costs more than it saves.
- **After sending, the console stays in INBOX** -- the next action is almost
  never about the thing just sent -- and the status bar keeps
  `Sent: <subject> to <recipient> — o to view` until the next event.
- **Retention stays authoritative.** A collected notice disappears from SENT
  too; this is a view, not an archive, and no content is duplicated into a
  UI-owned store.

New core API, read-only and narrow: `list_sent`, `open_sent`,
`open_sent_notice`. No SQLite reaches the TUI. Protocol 9, the schema, the
frozen CLI and the distribution are all unchanged.

Four failure modes were introduced deliberately and each fails its pin:
routing the sent open through the claim path, serving history from process
memory, skipping the owner check, and skipping pin revalidation.

## Replying to a notice, and a defect it exposed

`r` on an opened broadcast now composes a NEW DIRECTED message to the notice's
author. It cannot be a disposition: a broadcast has no claim to complete, and
`messages.responds_to` references a message -- pretending otherwise would mean
lying to the schema. The notice's receipt is left exactly as the explicit open
set it.

- The author is taken from the notice, with no picker: the human said "reply
  to this", which answers both who and about what. Asking them to pick the
  author from a list would be asking a question whose answer is on screen.
- The subject is copied EXACTLY -- not prefixed, not summarised. The author
  identifies their broadcast by that line, and an automatic prefix is noise in
  a long thread that is already identified structurally. Directed replies
  inherit the same way.
- The caret starts in the SUBJECT. (This bullet said BODY when it was written;
  the no-inline-body model, recorded further down, moved the quick reply to
  the subject line. Corrected rather than left, because a stale sentence in a
  history file still reads as a specification.)
- The original stays on screen while the draft is edited, and through the
  confirmation. Declining restores the draft AND the context.
- It appears in SENT immediately as a `[Q]` row and tracks `[P]`/`[R]`/`[C]`
  from the authority afterwards.

### The defect this exposed: notices never showed their body

Writing "the original must stay visible" is what caught it. Opening a notice
rendered its headers and then `(no retained bytes)` -- for every notice, since
the console shipped.

`mark_notice_seen` returns the RAW part rows, which carry `body` bytes. The
renderer speaks the typed envelope, which carries `text` and `encoding`. Given
the raw shape it correctly concluded there were no retained bytes, and said
so. The console has been showing people the headline of every announcement and
none of the announcement.

It now goes through `notice_delivery`, the same envelope builder delivery
uses. Pinned by content: the rendered pane contains the notice's actual text.

Worth naming why no test caught it: the notice tests asserted on the MODEL --
`detail["notice"]["parts"][0]["body"] == b"body\n"` -- which was true. Nothing
asserted that the body reached the SCREEN. Verifying observable output is not
the same as verifying behaviour, and here the model was right and the output
was empty.

### One existing test changed, declared

`test_reply_cannot_land_on_a_claim_the_human_is_not_looking_at` -- the test
that caught the wrong-recipient bug -- asserted `begin_reply() is False` on a
notice. That is now False by design. The safety property it exists for is
unchanged, so the assertion was made STRONGER rather than removed: the reply
must bind to the notice's author and specifically NOT to the unrelated claimed
message under the cursor.

## External body editor (Ctrl-E), and the notice shorthand

**Notice subject-only shorthand approved and applied.** A notice with a
subject and no body publishes the subject text as its single content part,
exactly as directed compose does. A zero-byte part is never published, and a
notice with neither subject nor body is still refused. The test that asserted
"a notice always needs a body" now pins the new rule and records what it used
to assert.

**Ctrl-E opens an external editor for the body.** Inline typing stays the
default -- a one-line answer should not cost an editor launch.

Three things make this security-relevant rather than a convenience:

- **The text is hostile.** It arrived from another participant. The default
  invocation is `vim -n --cmd 'set nomodeline'`: a modeline is a line INSIDE
  the text that configures the editor, and this text is not ours. A
  user-supplied vim invocation is left exactly as configured -- that is their
  trust boundary, and second-guessing it would be worse.
- **The editor command is configuration.** Precedence is `--editor`,
  `BATON_EDITOR`, `VISUAL`, `EDITOR`, then `vim`, parsed with `shlex` and run
  as argv. Never a shell: a configured editor may have arguments, and may not
  have a pipeline, a redirect, a substitution or a second command. `--` is
  appended only for editors we know treat it as end-of-options; otherwise the
  path is simply the last argv item. The setting is TUI-only -- a UI
  preference in the authority config is one every agent carries and none can
  use.
- **The draft is a temporary file.** 0600, created private, checked on return
  to be the same regular file by device and inode, size-bounded, and removed
  whether the edit succeeded or failed. A symlink or a replaced file is
  refused rather than imported: refusing costs one retry, accepting would
  import a file we never wrote. No authority or storage path is ever handed to
  an editor.

**Importing is not publishing.** Save-and-quit is muscle memory; sending to
another person is a decision. The editor returns to the same draft and the
ordinary Enter then `Send now? [Y/n]` still stands. Every failure -- missing
editor, nonzero exit, signal, unreadable or replaced file -- leaves the draft
exactly as it was, because a half-imported body is worse than no import.

**Seeding.** A reply with an EMPTY draft opens on a conventional editable
quote: `On <date>, <author> wrote:` with every line prefixed `> `, and room to
write above it. A draft that already has content is opened exactly as it
stands -- silently re-seeding over words someone wrote would destroy them, and
they would not find out until the editor opened. Binary parts are never quoted
into a draft; the original stays on screen for context either way.

Round-tripping is byte-exact: whitespace, tabs, newlines, absent final
newlines and non-ASCII all survive, pinned per case. An editor round trip that
quietly normalised them would rewrite the human's message.

Five failure modes introduced deliberately, each failing its pin: running
through a shell, skipping the inode and regular-file checks, enabling
modelines, re-seeding over an existing draft, and letting the editor's exit
publish.

## The reply subject, decided after two reversals

Recorded because the sequence is confusing to read back otherwise, and the
final rule is the opposite of one that was implemented and pinned.

1. Inherit the subject unchanged, no prefix — implemented, pinned with an
   assertion that the subject did not start with `Re:`.
2. Seed `Re: ` exactly once, case-insensitively non-stacking — superseded (1),
   implemented, and the old assertion rewritten.
3. **Copy the original EXACTLY, no prefix ever** — Slawomir's final ruling,
   which is (1) again with a stated rationale.

The rationale is the part worth keeping: `[R]` in SENT already exposes replied
state, and `responds_to`/`thread_id` carry the relationship. A prefix is
decorative redundancy, and in a long thread it is subject churn — the same
words drifting by one prefix per hop. A human who wants one can type it,
because the quick-reply line is editable, and that deliberateness is the whole
difference.

The behaviour lived in one function throughout, which is why three reversals
cost one line each plus their pins. That was not luck: putting a
one-line-looking rule behind a named function is what made it cheap to change
its mind about.

## R2: four functional defects found in review

All four were real, and none had a test. Recorded with what let each survive.

- **Notices still had an inline body field.** `NOTICE_FIELDS` kept `body`
  while `COMPOSE_EDITABLE` had dropped it. The no-inline-body pin exercised
  DIRECTED compose only, so the rule held in one flow and not the other. A
  contract that says "anywhere" needs a test per place.
- **A new composition could quote an unrelated message.** `begin_compose`
  leaves the previously opened item in `detail`, and the editor seed fell back
  to quoting whatever was there. Open a message, press `n`, press Ctrl-E, and
  another participant's words were in your new message. Fixed with an explicit
  `compose_is_reply` flag: quoting requires a reply context, not merely a
  detail pane with something in it.
- **Switching to SENT left the inbox claim armed.** `select_view` did not
  clear `opened`, so `r`, `e`, `c` or `m` could reach a hidden claim while a
  sent row was displayed. This is the wrong-target bug from round one wearing
  a different hat, and the lesson is the same: the target must follow what is
  DISPLAYED. The UI target is dropped on switch; the authority claim is not
  touched, because viewing must never mutate it -- pinned in both directions.
- **`G` used the inbox row count in both views.** With differing counts it
  stopped short of the last sent row. Pinned with counts that differ, which is
  the only shape that catches it.

Each was verified by reintroducing it. The view-switch fix fails four pins
when removed -- one per effectful key -- which is the shape that says the
guard is about the CLASS of action rather than one key.

## R3: six more, and two of them were mine to have caught

- **The selection stripe used inbox state in both views.** Empty inbox plus a
  non-empty sent list meant no row was highlighted at all. The styling was
  split from the pane it describes, which is the same shape as every other
  view bug this round.
- **History was capped at 200 with no indication.** Durable subjects sat in
  the authority, unreachable, while the view called itself history. Removed
  the default cap: retention and gc already bound how much exists, and a
  second silent bound only hides what they kept.
- **The console rewrote subjects.** The core rejects leading and trailing
  whitespace ON PURPOSE -- silent sanitization misrepresents what the sender
  wrote -- and the TUI was calling `strip()` before passing it. That hid a
  refusal the human was entitled to see and sent something they did not type.
  My own "preserved exactly" test asserted `original.strip()`, which is the
  part I should have caught: a test that encodes the bug agrees with it
  forever.
- **The temp file had a check/read race.** `lstat(path)` then `open(path)` is
  two lookups of one name at two instants. Now opened once, `fstat`-ed, and
  read from that descriptor, with `O_NOFOLLOW`.

  Worth recording how the pin got there. My first attempt simulated a swap
  after `os.open` returned -- and passed against the vulnerable
  implementation, because that is the wrong window. The pin now asserts the
  ABSENCE of the second lookup: after the editor returns, the draft path is
  opened once and never stat-ed by name. That fails immediately when the
  lstat is restored.
- **An empty body from the editor silently sent the subject instead.** The
  quick path is valid; choosing the full path and getting nothing back is not
  a reason to send a different message. It refuses and keeps the draft.
- Stale behaviour text in `_begin_notice_reply` and `send_reply` corrected.

## R7: the stacked layout

The console was two side-by-side columns: a 40%-wide list beside a 60%-wide
detail pane, with a vertical `│` between them. It is now stacked — a
full-width list above a full-width detail pane, separated by ONE continuous
horizontal `─` rule with an ASCII `-` fallback.

Why, recorded because it reverses a layout that had a lot of pins on it: the
two things a console shows are a one-line subject and a Markdown body, and
both want WIDTH. Splitting the terminal gave each of them a little over half
of what it needed, so subjects truncated at 40% and bodies wrapped at 60%
while two thirds of the screen was the other pane's margin. Height is the
cheaper axis to divide, because a list scrolls and a body scrolls and a
truncated line does neither.

Everything derived from the old geometry was recomputed rather than adapted:

- **`pane_widths` is gone, `pane_heights` replaces it.** The 40/60 ratio now
  divides the body HEIGHT after reserving the one-row rule. There is no
  pane-width helper at all — a leftover one would be a second authority still
  describing columns. Pinned structurally, so re-adding one fails a test
  rather than merely being unused.
- **Wrapping, the detail line count, paging, scrolling, caret placement,
  part-header marks and resize** all take the terminal width and the stacked
  row offsets. The caret is placed by its ROW below the rule where it used to
  be placed by a column past the divider.
- **The selection highlight covers the whole row**, because a stacked list row
  IS the whole row. What the span still guarantees is what it always
  guaranteed: one row, of one list. Never the rule, never a detail row.
- **The minimum terminal is unchanged at 40x8** and still draws every region:
  a header, a list row, the rule, a detail row and the two-row footer. Pinned,
  because a minimum the layout cannot actually draw is not a minimum.
- **The single-row status bar and the `Send now? [Y/n]` confirmation footer
  are untouched**, including the rule that the row the second footer line
  would have taken goes to the panes. The old pin counted body rows by
  counting rows containing the divider, which stacked would count one; it
  counts the rows between the header and the footer instead.

### Two consequences that needed a decision, not an adaptation

- **The recipient picker became MODAL and owns the body.** It replaced the
  detail pane, which used to be the whole body height; at 40x8 the stacked
  detail pane is two rows and cannot hold a prompt, one recipient and its page
  footer. Confined to it, the picker would have offered a letter it could not
  draw — the exact fault the measured-capacity work fixed. Choosing a
  recipient is also not a moment when the list behind the choice is being
  read. Verified by putting it back inside the detail pane: two supported
  sizes fail immediately, one on undrawn letters and one on the dropped page
  footer.
- **`[`/`]` now scroll the selected part header into view.** A 60% detail pane
  puts the later parts of a multipart message below the fold, and a mark
  nobody can see is not a cursor. Only on the keystroke that moves it — doing
  it on every redraw would take a reader's `J`/`K` scroll position away from
  them, which is pinned separately. The first implementation followed the line
  AFTER the header (so it could not come to rest on the "... N more lines"
  row) and that broke moving upward; it follows the header and then the line
  after it, which is correct in both directions.

`follow_input` became `follow_line` for that second caller: a helper that says
"input" while scrolling to a part header is a comment that lies at the call
site.

### One latent bug found while restructuring

`_detail_lines` filled the part-header `marks` list from the message content
and THEN returned the picker's lines when the picker was open, so a picker row
could be styled as a part header. The picker check moved to the top of the
function. It was cosmetic and nothing reported it; it is recorded because the
mark is supposed to come from the code that drew the row, and that was the one
path where it did not.

### Deliberate-break checks

Every new pin was verified by removing its fix and watching it fail:

| Break | What fails |
|---|---|
| picker confined to the detail pane again | undrawn letters at 40x8 and 100x8, and the dropped page footer |
| part-header following removed | later parts selectable but never marked, in three tests |
| list pane drawn at 40% width again | both-panes-full-width, the stacked minimum, and the date thresholds |
| the rule drawn as one cell instead of a full row | the rule pins and every wrapped-detail width pin |
| date/party thresholds reverted to their column values | the degradation pin: the date became unconditional |
| a `pane_widths` helper re-added | the structural no-column-helper pin |

### Results

    just test          1560 passed
    git diff --check   clean
    protocol-9 build   8b00ff314b3a66b291809ef749e1df955f11e9e5bda4153a6ea7715944b9f24d

Deterministic on rebuild. `bin/baton`, `DISTRIBUTION.json`, `baton_v6.py` and
`build_zipapp.py` byte-identical. The README quick example was executed end to
end against a temporary instance — handoff, wait, reply, receive, notice,
inline send — and `doctor` reports the instance clean.

**Relaunch to pick it up** — a running console keeps the old code.

### The README screenshot is stale

`assets/artwork/baton-tui.png` still shows the side-by-side columns. It is the
one thing in this round that documentation cannot fix from here: a fresh
capture has to come from a real terminal, which means Slawomir's live trial.
Until then the README says so in prose beside the image rather than letting the
picture quietly contradict the text.

## R7 re-review: four corrections, three real

The review returned four corrections against the R7 handoff. Three reproduced
and are fixed; one did not exist.

### R1 — one viewport authority for the list

Reproduced exactly as reported. `layout_for` reserved the overflow-indicator
row unconditionally (`inbox_height = top_lines - 1`) while `_inbox_pane`
reserved it only when the list actually overflowed. At exactly-capacity the
model scrolled against the smaller height, moving to the last row set the top
to 1, and row 0 left the screen with no `... above` to say it had.

`list_capacity(row_count, pane_lines)` is now the single authority: an
overflowing list spends its last row on the indicator, a list that fits does
not, and the model, the two list panes and the selection styling all ask it.
`layout_for` reports the PANE HEIGHT and stops second-guessing it.

Writing the pins exposed a SECOND half of the same bug, which the report did
not cover and which the first fix did not touch. The top was clamped only to
`row_count - 1`, so it stayed wherever a smaller pane had pushed it: widen the
terminal until the list fits again and the pane still started at row 7,
drawing one message and silently omitting the seven above it. `list_top` is
the other half of the authority — you can never scroll past the point where
the last row sits at the bottom of the pane.

Pinned at capacity-2, -1, exactly, +1 and +4, at every cursor position, in
MESSAGES and in the Sent filter, plus first/last navigation at eight heights
and a resize sweep across the boundary. The property asserted is the honest
one: the selected row is always DRAWN, and if any row is off screen the pane
says so.

One pin needed care. The exact-fit case is masked by the renderer's own clamp,
so a test that only reads the drawn rows passes with the model still wrong —
verified. `test_an_exactly_fitting_list_never_scrolls` asserts on `view_top`
instead, and fails immediately when the unconditional reservation is restored.

A second care point: the tests originally assumed rows came back in send
order. Same-second sends tie and order by id, so that made them tests of
SQLite's ordering. Subjects are read from the model now.

### R2 — the superseded History view is gone

Removed end to end: `VIEW_HISTORY`, `VIEW_HISTORY_KEY`, the driver dispatch,
the state rows/cursor/top/refresh/open helpers, `selected_history`, the
history branches in `preview` and `_detail_lines`, `_history_row_lines`, and
`Store.list_received` in the core — which existed only to populate it and had
no other consumer. `open_received` stays: the unified MESSAGES list needs it
for handled inbound rows, owner-checked on the recipient.

**No tests were removed, because there were none.** Nothing in the suite
referenced `VIEW_HISTORY`, `list_received` or any history row, which is the
whole point of the finding: no key emitted its event, so it was unreachable
and untested drift that could not be caught disagreeing with the list that
superseded it. The removal is green with nothing else touched.

It is now pinned structurally — no module may carry a HISTORY name, the model
may not carry those attributes, and the core may not carry `list_received`
while keeping `open_received` — plus a key-map pin that `h`/`l`/`[`/`]`/`H`/`L`
remain part navigation, so a future History cannot quietly take `h` back.

### R3 — outbound rows keep their lifecycle in MESSAGES

Reproduced. Every `pending`/`claimed` row went through `_status_glyph`
regardless of direction, so a delegated message showed a blank or a `*`. Those
are inbound notation: a blank means "waiting for ME" and `*` means "claimed by
ME", so borrowing them for someone else's queue reports the wrong person's
obligation. `[Q]`/`[P]` are the only spelling that says whose.

Outbound directed rows now render through `sent_badge` for every state.
Inbound notation and action semantics are unchanged and pinned separately, so
the badge cannot leak the other way.

That made a latent alignment fault common rather than rare: a 1-cell glyph
beside a 3-cell badge shifted the date and sender two cells on alternating
rows. Both list panes now draw the status column at one width, `GLYPH_WIDTH`,
and the subject budget was corrected to match. Pinned by asserting the date
column starts at the same cell on an inbound row, an outbound row and a
notice.

### R4 — does not reproduce

The report says `_delivery_lines` contains
`content = message.get("content") or {}` twice consecutively. It appears once,
at one call site, and a scan of `baton_tui/` and `baton_core/` for any
consecutive duplicated assignment finds none. Nothing was changed. Reported
back rather than silently ignored, in case the reviewer was reading a
different revision.

### Deliberate-break checks

| Break | What fails |
|---|---|
| reserve the indicator row unconditionally again | the exact-fit no-scroll pin |
| drop the `list_top` clamp | the resize-across-the-boundary pin |
| outbound rows back through the inbound notation | the queued/picked-up pin |
| drop the common glyph width | the column-alignment pin |
| a History constant put back | the structural no-History pin |

### Results

    just test          1578 passed
    git diff --check   clean
    protocol-9 build   b4ec0a4a9dc6462b37d93f74276edf2c352a5aa86d48772346bc5e6b79c07de6

Deterministic on rebuild. `bin/baton`, `DISTRIBUTION.json`, `baton_v6.py` and
`build_zipapp.py` byte-identical. The README screenshot is still stale and
still needs a real-terminal capture from the trial.

## Final cleanup: two pins made real, and the newest-first ruling

### C1 — the no-History pin was vacuous

Fair catch, and the worse kind of test failure: `test_there_is_no_history_view`
asserted `not hasattr(InboxState, "history_rows")`, but `history_rows`,
`history_cursor` and `history_top` were created in `__init__` and never
existed on the class. The assertion was already true before the removal, so it
reported a guarantee it had never checked.

It now instantiates the model and asserts all three are absent from the
instance and from `vars(instance)`, keeping the module, class and core checks
beside it. Verified by restoring one field to `__init__` and watching it fail.

This is the same shape as the footer pins that compared the screen against the
constant that produced them: an assertion that cannot fail is worse than an
absent one, because it is counted as coverage.

### C2 — the last active column comment

`_inbox_pane` still described the Sent filter as "the SAME pane at FULL
height" on a pane that was "narrow already". Rewritten for the stacked layout:
the same TOP list pane, full terminal width, about 40% of the body height.
Superseded discussion in this file and in FINDING stays as history.

### C3 — RULED by Slawomir: MESSAGES is newest-first

> the order of messages should be new-at-top

MESSAGES is retained activity, so oldest-first meant scrolling past the entire
history to reach new work, at a cost that grows forever. It is now sorted by
the total order `(created_ts, id)` DESCENDING, the same ordering discipline
the Sent filter already used.

**Presentation only.** `claim` and `wait` are untouched and still take the
oldest pending message; the console never used them to populate the list. The
core's `list_messages` still returns the ascending total order, and its
docstring now says that this is a stable base rather than a presentation
decision — which end goes at the top is the consumer's.

Three things had to change with it, and two of them were silent hazards rather
than mechanical edits:

- **The same-sender warning compared by POSITION.** `self.rows[:self.cursor]`
  meant "older" only while the list was oldest-first. Under the ruling those
  are the rows NEWER than the selection, so the warning would have inverted
  itself — and in the direction that never fires when it should, which is the
  half nobody notices. It compares `(created_ts, id)` now. It is also
  restricted to inbound rows on both sides: an outbound `pending` row is
  someone else's queue, and warning about "skipping" it was meaningless.
- **The cursor followed the INDEX.** An arrival now lands at the top and
  shifts every row down, so a numeric cursor points at a different message and
  the next Enter claims something nobody chose. That is the wrong-target bug
  from round one, arriving through the poll instead of through a keystroke.
  Selection is preserved by ROW IDENTITY across a refresh, in MESSAGES and in
  the Sent filter — the Sent one reads its previous row directly rather than
  through `selected_sent`, which answers only while Sent is the active view
  and the poll runs in both.
- **Ties.** Baton stamps to the second, so messages sent within one second tie
  and order by id. Two of the new pins needed a real second of separation to
  guarantee the arrival sorted ABOVE the selection; tied, they landed below
  and proved nothing. Both were verified to fail with the fix removed only
  after that change — before it, the sent-cursor pin passed against the
  broken implementation.

Two existing tests described the superseded order and were rewritten:

- `test_inbox_order_matches_what_claim_would_deliver` →
  `test_messages_is_the_exact_reverse_of_what_claim_would_deliver`. The
  property it was really about — the console and the core break ties on `id`
  identically — is unchanged and is what it now asserts, plus that the newest
  row is the one `claim` would take last.
- `test_skipping_a_senders_earlier_message_warns_but_allows` — the row that
  skips something is the head of the list now, not the row below it. It pins
  both directions: the newer row warns, the oldest pending row does not.

### Deliberate-break checks

| Break | What fails |
|---|---|
| a former history field restored to `__init__` | the no-History instance pin |
| sort ascending again | five ordering pins, including the reverse-of-delivery one |
| cursor restored by index instead of identity | the arrival-at-the-top pin |
| the warning compared by list position again | the same-sender warning pin |
| the Sent cursor restored by index | the Sent-filter identity pin |

### Results

    just test          1586 passed
    git diff --check   clean
    protocol-9 build   975c3f8027a83257c50145dec42ca5a61ab538cb6abadc7aa16e5ef8fbb085c9

Deterministic on rebuild. `bin/baton`, `DISTRIBUTION.json`, `baton_v6.py` and
`build_zipapp.py` byte-identical. The README screenshot is still stale, and is
now stale in two ways: it shows columns AND oldest-first.

## Editorial reconciliation, and why the test count moved on its own

Two stale comments and a test count that disagreed between two machines. The
count turned out to be the interesting one.

- `test_enter_claims_exactly_the_selected_row_not_the_oldest` said "FIFO is
  the default ORDER". It now says what is true: authority delivery is FIFO,
  human selection is not restricted by it, and MESSAGES is presented
  newest-first so the head of the list is not even the message `wait` would
  take.
- A driver comment said the Sent view uses the "FULL height" pane. It is the
  same list pane, about 40% of the body height, showing one list at a time.

### The count

Review measured 1588; this tree reported 1586. Neither was wrong, and no test
was flaky: **`test_docs_consistency.py` globbed `*.md` in the finding folder,
and `materialize` projects mailbox messages into exactly that folder.** Each
projection added two parametrized cases, so the suite total moved by two every
time a durable response was projected — with no code change at all.

That is worse than an accounting nuisance. A suite whose count depends on how
much mail has been filed is a suite people reconcile by hand once and stop
trusting afterwards. And the checks were wrong for those files: a projection
is a byte-exact copy of an immutable message, so a rule it presents as current
cannot be corrected in place — only superseded elsewhere. History records what
was true when it was written, which is why TRIAL's own historical entries say
so in place rather than being rewritten.

The checked set is now the three durable documents by NAME, with a pin that it
does not move with projections. The store remains the authority for
projections.

    just test          1583 passed
    git diff --check   clean
    protocol-9 build   975c3f8027a83257c50145dec42ca5a61ab538cb6abadc7aa16e5ef8fbb085c9
                       (unchanged: this round touched tests and documents only)

1583 rather than 1588 because five collected cases were the globbed
projections, not because anything was removed: 1588 - (3 projections x 2
parametrized cases) + 1 new pin = 1583.

## RULED: a reply is an indented child of what it answers

Reported by Slawomir through review: the outbound reply appeared as a flat
sibling immediately above its received parent. Newest-first put it there,
where it reads as two unrelated messages that happen to share a subject — and
the row a human looks at to see whether something was answered is the row of
the thing they answered.

A reply is now an indented child, marked `↪` (U+21AA, with `->` where the
terminal cannot encode it) and indented two cells per level.

Two orders, deliberately different, and the choice mattered:

- **Threads sort newest-first by their most recent member**, not by their
  root. By the root's own timestamp, answering an old message would leave the
  reply you just sent near the bottom of the list — which is the "I sent it
  and it vanished" failure unified MESSAGES was built to fix, wearing a new
  hat. Pinned by answering an old thread and asserting it comes back above a
  newer unrelated message.
- **Within a thread it is oldest-first under the parent**, because that is the
  order the conversation happened in, and an indented child that precedes its
  parent is not a child.

Presentation only. Badges, direction, actionability and authority order are
untouched: the parent still turns `[R]`, the reply is still an outbound `[Q]`,
and `claim`/`wait` are unaffected. `list_messages` now reports `responds_to`
— the schema's own column, reported rather than derived, additive and
read-only, under "richer stable inbox rows".

Two boundaries decided rather than left to the code:

- **`responds_to` is followed only within the VISIBLE set.** A reply whose
  parent has been collected is a root; indenting it under nothing would show a
  relationship that is not on the screen. Pinned, and verified by removing the
  membership test.
- **The indent lives in the SUBJECT column and nowhere else.** Indenting the
  whole row would move the date and party columns on reply rows alone, and
  every list row lining up is a property pinned one round earlier. The pin
  asserts the marker is present and indented AND that the date column has not
  moved.

A self-referencing row is treated as a root rather than walked. The schema
should never produce one; a loop would hang the walk instead of failing
visibly, which is the wrong way for an impossible case to behave.

### Deliberate-break checks

| Break | What fails |
|---|---|
| flat newest-first list again | three threading pins |
| threads sorted by their root instead of their newest member | the answered-thread-returns-to-the-top pin |
| the indent kept, the `↪` marker dropped | the marker pin |
| `responds_to` followed outside the visible set | the orphaned-reply pin |

### Results

    just test          1589 passed
    git diff --check   clean
    protocol-9 build   092c2be4aeacb1eceee5a2396e44852181dc059f78fbb5072986d554dc5982ee

Deterministic on rebuild. `bin/baton`, `DISTRIBUTION.json`, `baton_v6.py` and
`build_zipapp.py` byte-identical.

## Trial R10: "cannot see the license part.. I can only view part[0]"

Slawomir, using the console against a real multipart message: an inline
Markdown leaf beside an external LICENSE leaf.

Reproduced immediately, and the reported symptom was not the defect. Both part
headers WERE reachable and `[`/`]` did move the mark. What the human saw on
the external row was:

    [1] text/plain; charset=utf-8  attachment  LICENSE  (no retained bytes)

`(no retained bytes)` belongs to a SCRUBBED transient body, where the manifest
outlived the payload. An external leaf has bytes — in a configured root,
hash-pinned, verified at claim time — it simply does not carry them in the
envelope. The console told the human the part was empty, so they concluded it
could not be viewed, which was the only conclusion available.

And they were half right: there was no way to read it. `m` refuses on an
external part, deliberately and correctly — it is already a file, and copying
it into a projection would duplicate the thing the pin exists to avoid — so
the console offered a header, a false statement that it was empty, and no key.

Three fixes, together:

- **The header says what an external part IS.** Size, the pinned
  `root:path`, and that the pin verified. `storage` distinguishes it from a
  scrubbed body, which is what the two messages needed all along.
- **`v` reads a text part into the pane.** Through a new read-only core call,
  `read_claimed_external_part`: owner-checked, gated on an active claim like
  every other path that returns content, pin REVALIDATED before a byte is
  read, bounded to 1 MiB for display and explicit when it truncates. The path
  is the pinned root id and relative path resolved by the same component-wise
  no-follow walk that pinned it — never the advisory `filename`. Non-text
  media and non-UTF-8 bytes are refused with the location, not wrapped into
  the terminal.
- **The bytes are cached for DISPLAY only**, keyed by manifest address and
  dropped whenever the detail pane changes. Keyed by address alone and kept,
  message A's licence would redraw under message B's part 1.

`v` was verified unbound before taking it.

### One thing found while fixing it

A wrapped part header repeated the selection marker on every continuation row,
so a header long enough to wrap looked like several selected parts. The
external header is long enough to wrap at 100 columns, which is how it
surfaced. The mark is now applied to the first row only; the indents are the
same display width, so continuations still line up.

### Deliberate-break checks

| Break | What fails |
|---|---|
| an external part described as empty again | the not-empty pin and the read pin |
| `v` unbound | three read pins |
| pin revalidation skipped before reading | the broken-pin pin |
| the display cache kept across a move | the never-under-another-message pin |

### What was NOT changed, and why

`m` still refuses on an external part. The reviewer's regression asks that
"materialize targets the selected external part", and it does: the refusal
names part `1`, the one the human selected, rather than silently writing part
0. The rule itself is the core's and is right.

### Results

    just test          1596 passed
    git diff --check   clean
    protocol-9 build   742159a98d03d50008e4c827fcdbc3e8475fa4e74934013312ce789978a52541

Deterministic on rebuild. `bin/baton`, `DISTRIBUTION.json`, `baton_v6.py` and
`build_zipapp.py` byte-identical.

**Relaunch to pick it up** — a running console keeps the old code.

## UX ruling round: keys, Ctrl-U, help, and the indent bound

Four rulings arrived while R10 was in flight, plus a process correction. All
four are implemented and pinned; each was verified by removing the fix.

### `r` quick, `R` full editor reply, `Ctrl-R` refresh

Shifted `r` for the bigger version of the same act. Browse `e` is REMOVED
rather than kept as an alias — a second spelling nobody is told about is a key
only its author can press — and manual refresh moved to `Ctrl-R` because `R`
was taken and `g` is the `gg` prefix.

Four existing tests named the old keys and were rewritten, declared in the
handoff: the refresh test, the editor test, the letter-is-literal test (now
checking `R`, the letter that would break if the table leaked), and the
effectful-key sweep's parametrization.

### `Ctrl-U` kills to the start of the line

In every typing mode; browse `Ctrl-U` still pages. One model method on the
shared buffer helpers, so it applies to every editable field rather than the
one flow it was reported against. Pinned at caret 0, mid-line and end, in
quick reply, directed compose and notice compose.

`test_no_browse_chord_fires_while_typing` asserted that control keys leave the
draft untouched. Ctrl-U is now an editing key there, so the chord stays in the
parametrization — its browse meaning must still not fire, which is what the
test is about — and the draft assertion became per-key.

### `?` opens the modal shortcut list

A modal view over the whole body with its own scroll, so the reader's detail
position is exactly where they left it. `?`, `q` or Esc closes it; `q` does
not quit, because it is the key people press to dismiss a full-screen thing.

**The content is generated from the key table**, in `keys.HELP_SECTIONS`,
sitting beside the mapping it describes. A help screen maintained separately
is wrong within a month, and wrong help is worse than none because it is
believed. The structural pin caught `open_help` itself missing while it was
being written.

Two of the pins needed care. Small-terminal reachability was first driven at
the test helper's default size while being drawn at another, which proved
nothing about either; it now drives at the size under test. And the
literal-`?`-while-typing pin assumed the caret was at the end of the draft,
which it was not.

### Reply indentation is capped at three levels

Past the bound the indent stops and the marker becomes `…↪` (`...->` as the
fallback), so three levels and nine do not look identical. `thread_prefix` is
the one place the bound lives.

Presentation-only, and pinned as such: no row hidden or collapsed, grouping
and ordering unchanged, parent-before-child unchanged, badges and direction
unchanged, `responds_to` untouched, and the date and party columns asserted
not to move because a row is deep.

### The PLAN ledger

Process correction from review: PLAN said every implementation item was done
and omitted the rulings that arrived afterwards. It is now one consolidated
ledger with explicit states — `done/pinned`, `in progress`, `ruled/pending`,
`user trial`, `deferred` — split into console behaviour, what is not code and
cannot be closed from here, and the protocol-10 deferrals. `done/pinned`
requires implementation AND regressions that fail when the fix is removed; a
Baton request never moves an item on its own, and reviewer approval is
separate and deliberately not recorded there.

Writing it tripped the documents' own cross-reference check, which read "see
TRIAL's most recent round" as a pointer to a section named TRIAL. Reworded —
the check was right that the sentence pointed at nothing.

The per-round test count and artifact hash now live with the round that
produced them here, rather than being duplicated in PLAN where they went stale
the moment a round landed.

### Deliberate-break checks

| Break | What fails |
|---|---|
| `e` rebound to the full reply | the removed-shortcut pin and the legend pin |
| `R` mapped back to refresh | the editor-from-browse pin |
| Ctrl-U left as page-up in typing modes | the three caret-position pins |
| `?` mapped in the text tables | the literal-while-typing pin |
| a binding added without a help entry | the structural help-coverage pin |
| the indent uncapped | the level pin |
| the shallow marker used past the bound | six pins, including every width |

### Results

    just test          1625 passed
    git diff --check   clean
    protocol-9 build   11942b1c3775c570e83f127582845cad296539bd1192897670b3378939f95a6e

Deterministic on rebuild. `bin/baton`, `DISTRIBUTION.json`, `baton_v6.py` and
`build_zipapp.py` byte-identical.

## Blocking trial: selecting an outbound row reported an error

Reported from the live console: a full editor reply published successfully,
and the console then said

    [ERR] message '25b7...' is addressed to 'baton.reviewer', not
    'human.slawomir' — nothing shown for this row

**Reproduced against the current tree** — it was NOT already fixed by the
threaded build, so there is no "which newer pin would have caught it" to
report. What the threading DID do was mask the reported sequence: the cursor
is restored by identity and the child sorts directly under its parent, so
after a send the selection stays on the parent and the error does not fire on
that keystroke. Move onto the outbound row and it fires immediately. The bug
was never about sending; it was about selecting.

`preview()` routed EVERY message row through `store.preview_message`, which is
owner-checked on the RECIPIENT — correctly, because it is the delivery
preview. Unified MESSAGES put outbound rows in that list, and preview kept
asking the recipient's question about them.

The owner check is not weakened; it was right, and it is what exposed this.
The console stopped asking it the wrong question: an outbound row previews
from the row itself, exactly as the Sent filter does — everything shown came
back with `list_messages`, so no core call is made and selecting cannot fail.
`Enter` still opens the real copy through `open_sent`, owner-checked on the
SENDER.

Pinned: selecting an outbound row never errors and never blanks the pane; a
full editor reply publishes exactly once, resolves its claim with exactly one
disposition and leaves no error; the new child is selectable, opens through
the outbound path, shows the sent body, and creates no second claim or
disposition; the quick path has the same guarantees, because fixing one reply
path and assuming the other is how notices went a whole release without ever
showing their body; and whatever is selected after a send is a row the console
can actually draw.

Break check: routing outbound previews back through `preview_message` fails
three of those pins.

Also from the trial, and NOT a defect: `Ctrl-U` did nothing because the
running console predates that slice, and the indentation cap was absent for
the same reason — the trial artifact was `742159a9`, built before both.
Relaunching picks them up.

### Results

    just test          1630 passed
    git diff --check   clean
    protocol-9 build   e1016efbf817459129ee351009152444372fb52f09f605bcfa62172645537edb  bin/baton-tui

## Follow-ups: an answered conversation is not a dead end

Three rulings, implemented together because they describe one act.

`r`/`R` on a handled inbound row or an outbound row now start a FOLLOW-UP: a
fresh directed message linked by `responds_to` to the selected one, to the
other party, with the subject inherited, `kind="follow_up"` and the thread
inherited when there is one. The screen says `Answered   r quick follow-up   R
full follow-up` (or `Sent  …`) where it used to say "ALREADY ANSWERED — read
only" and "YOUR SENT COPY — read only".

The safety boundary is unchanged and is where it always was. `claim_id` is
None on a follow-up target, and every disposition path keys off exactly that:
`_held_claim_id` returns None, so `c`, reply-as-disposition and materialize
refuse as before. `kind` is descriptive and is never asked a safety question.

Three existing tests asserted the superseded behaviour and were rewritten,
each declaring what it used to say:

- `test_a_handled_message_opens_read_only_and_is_owner_checked` asserted
  `opened is None`. It now asserts the target exists AND carries no claim —
  the property that actually mattered.
- `test_outbound_rows_are_never_actionable` →
  `test_outbound_rows_carry_no_disposition`, asserting zero dispositions and
  zero authority writes rather than zero affordances.
- `test_opening_an_outbound_row_shows_the_sent_copy_read_only` →
  `..._with_guidance`, which now asserts "read only" is NOT on the screen.

Pinned: the guidance line and the retained `[R]`; a follow-up as a new linked
message with `kind=follow_up` and no claim, disposition or receipt, and no
transition on the ORIGINAL; thread inheritance and its absence; an ordinary
`n` never acquiring a linkage; siblings from the same parent all at depth 1;
following up on a child nesting one deeper; the recipient being the other
party in both directions; the original's manifest hash unchanged afterwards;
and `In reference to:` reaching the detail pane.

One pin was wrong when first written and is worth recording: it asserted the
TOTAL transition count did not move. Publishing any message writes a
transition, so a follow-up moves it legitimately. Scoped to the original
message's transitions, which is the claim actually being made.

### Deliberate-break checks

| Break | What fails |
|---|---|
| follow-up sent without `responds_to`/`thread_id` | five linkage and threading pins |
| no follow-up target on a resolved or outbound row | nine pins across state and driver |

### Results

    just test          1639 passed
    git diff --check   clean
    protocol-9 build   1f633c0e843a878c950f85dc6b615c4e0f5644e0989c1209348d80ba8e6e4ae5

Deterministic on rebuild. `bin/baton`, `DISTRIBUTION.json`, `baton_v6.py` and
`build_zipapp.py` byte-identical. Not announced for human trial: one ledger
item — retained seen notices — is still open, and readiness is the reviewer's
to publish.

## Retained notices, and a badge that took three tries

A seen notice now stays in MESSAGES as history. It used to leave the list the
instant it was opened — `refresh` called the unseen-only `list_notices` — so a
human watched an announcement disappear while reading it.

`list_notices` is untouched, for its at-most-once consumers. MESSAGES uses an
additive read-only `list_notice_activity`: every unexpired notice LEFT JOINed
to this participant's receipt, metadata only, no write lock.

**The badge took three rulings and the first two are recorded as superseded so
no stale current rule remains.** `[N]` was proposed, then rejected because `N`
reads as *new* — the opposite state — on the one row where that matters most.
`[S]` was ruled next, then refined: `[✓]` says the receipt exists without
reading as New or Sent, with `[S]` as the fallback where the terminal cannot
encode it. The fallback is now ONE decision covering every optional glyph —
reply arrow, deep-reply arrow and check mark — because a terminal that cannot
encode one cannot encode the others, and deciding them separately is how a
screen ends up with a Unicode arrow beside an ASCII ellipsis. Both spellings
are three display cells, so no column moves with the choice.

The rest, as specified: Enter on an unseen notice still commits exactly one
receipt and returns the body atomically; Enter on a seen row is not a content
path and the screen SAYS the content is not redelivered — the absence of a
write is not enough on its own, because a row that looks one keystroke away
from the announcement is a row that will be pressed. A body read earlier in
the session stays on screen; after a restart the metadata is there and the
body is not.

**The superseded assertion, declared.** `test_notice_opens_once_and_is_not_
redelivered` asserted `all(r["row_type"] != "notice" ...)` — that the row
disappeared. That was the unseen-queue behaviour. It now asserts the row is
KEPT with state `seen`, and keeps the property that actually matters: exactly
one receipt, no redelivery. One driver test also named `list_notices` in a
failure-injection set and now names the method the console calls.

### Deliberate-break checks

| Break | What fails |
|---|---|
| unseen-only listing again | five retention pins |
| reopening a seen notice made a content path again | three pins |
| a seen notice keeping the attention marker | the badge pin |

### Results

    just test          1649 passed
    git diff --check   clean
    protocol-9 build   536bb511d616b171ceb69825c7d15d0dc4e7a21fccbf8dd8777f4308584dc966

Deterministic on rebuild. `bin/baton`, `DISTRIBUTION.json`, `baton_v6.py` and
`build_zipapp.py` byte-identical. **Every ledger item is now done/pinned**
except the README screenshot, which needs a real terminal. Not announced:
readiness is the reviewer's to publish.

### The two notice notations, ruled apart

I raised the ambiguity rather than resolving it quietly: after `[✓]` landed,
the legend carried both `[N]` and a seen mark, and a reader could reasonably
ask what separates them. Ruled: `[N]` in the Sent filter is a row KIND — this
row is a notice — and `!`/`[✓]` in MESSAGES are STATES, where it stands with
you.

The hazard named in the ruling is the one now pinned: `[N]` must not vary with
whether anyone has seen the broadcast, because that would be an aggregate over
all recipients and the row does not claim to show one. The regression sees the
notice as another participant, refreshes, and asserts the authored row's badge
has not moved.

    just test          1651 passed
    protocol-9 build   bb06bd13080c2f84ae890ef5099998c421fefb4ba193667c493d0ef463603f82

## Review: stale on-screen guidance, and the editor path unpinned

Two findings, and the first is the more serious kind.

**`begin_reply` told the human "e for the editor"** after `e` was unbound and
`R` took the action. That is not a stale comment — it is live guidance in the
status bar, so it sent someone pressing a key that does nothing. Corrected to
`R`, along with the method's docstring (which also still described the
two-branch model from before follow-ups existed) and the driver's EDIT_BODY
comment. `map_key(e, BROWSE) == IGNORE` is unchanged and still pinned.

Its regression asserts the guidance names `R` AND that the key it names is the
one actually bound — a message that names a live key is the property, not the
particular sentence.

**The `R` follow-up path had no driver pin.** The quick path was covered and
the editor path was not, on either kind of handled row. Now pinned for handled
inbound and handled outbound: one keystroke opens the editor, the edited body
is imported, the confirmation publishes exactly one `kind=follow_up` linked to
the row, the recipient is the other party, no disposition is written, and the
editor's bytes reach the wire.

| Break | What fails |
|---|---|
| the stale `e` guidance restored | the guidance pin |
| no follow-up branch in `begin_reply` | both `R` follow-up pins |

    just test          1654 passed
    git diff --check   clean
    protocol-9 build   489813337e390c86a82b49f717bb10ffed53b70d7baecc4a04b6b57aa97b4273  bin/baton-tui

## Review: the new core API's own contract was unpinned

Fair, and the sharper version of a fault this repo has hit before: the
console's tests CONSUME `list_notice_activity` and would have passed while it
leaked `body`, `text`, `base64`, an attachment path or manifest data, because
they never look at those keys. `list_notices` had the recursive
`assert_no_delivery_content` sweep; its history sibling did not.

Pinned at the core boundary now, over BOTH an unseen row and a seen one —
the seen path being the one with a receipt to be tempted by — plus: both rows
still listed after one is seen; `list_notices` still unseen-only; `seen_ts`
independent per participant; repeated listing writing nothing across every
table an observation must not touch; and expiry removing the row.

`_revalidate_action_target` said a notice normally LEAVES the list and named
`list_notices`. True of the unseen-only listing, false now. Rewritten to what
the branch actually is: the defensive case where TTL, `expire` or gc takes the
row away underneath someone who is reading it.

The reported duplication in `test_a_response_can_still_be_started_from_a_seen_
row` was a `state` binding that was assigned and never used — the test builds
a fresh model on purpose, which is the point of it. Removed and the intent
stated.

| Break | What fails |
|---|---|
| a `body` leaked into activity rows | the content sweep |
| activity narrowed to unseen-only | two retention pins |

    just test          1659 passed
    git diff --check   clean
    protocol-9 build   c7a721341c69bc7dc86495716c78bbb4c52e499d98d62683d50c92b81122235d

### The other half of the `R` follow-up path

Review was right that the success paths were pinned and the failure path was
not. Now parametrized over handled inbound and handled outbound: `R` begins
the correctly linked, pre-addressed follow-up, the editor returns failure, and
then — nothing published, nothing written to any table, a VISIBLE failure
status, and the follow-up context still standing: linkage, recipient and
inherited subject all intact, with no partial body. The test then retries
through Ctrl-E and publishes, because "the human can retry" is the actual
requirement rather than "the draft object still exists".

Break check: clearing the follow-up context on a failed edit fails both
parameters.

    just test          1661 passed
    git diff --check   clean
    protocol-9 build   c7a721341c69bc7dc86495716c78bbb4c52e499d98d62683d50c92b81122235d
                       (unchanged: this round added tests only)

### A pin that would have passed while doing nothing

Review caught it, and it is the exact class this repo keeps writing down. The
cancel/retry test finished with `COUNT(*) FROM messages WHERE responds_to =
mid >= 1` — but on the handled-inbound fixture the original REPLY is itself
linked to `mid`, so that was already true BEFORE the retry. The retry could
have published nothing and the parameter would still have gone green.

It now brackets the retry over `kind=follow_up AND responds_to=mid`: zero
before, exactly one after, addressed to the other party, with `second attempt`
asserted to reach the wire. And it presses `K.CTRL_E` rather than a raw
`ord("\x05")`, so the key it exercises is the one the map defines.

Break check: removing the retry keystrokes now fails both parameters. It did
not before.

    just test          1661 passed
    protocol-9 build   c7a721341c69bc7dc86495716c78bbb4c52e499d98d62683d50c92b81122235d

## Approved for human trial

Independent review approved build
`c7a721341c69bc7dc86495716c78bbb4c52e499d98d62683d50c92b81122235d` on a stable
snapshot it verified itself: 1661 passed, `git diff --check` clean, a temp
rebuild byte-identical to both the artifact and `DISTRIBUTION-TUI.json`, the
frozen `bin/baton` at `a23461ae…` unchanged, protocol 9 unchanged. Every
review finding across every round is closed.

What is left is not code and not an agent's to close: Slawomir's real-terminal
trial, and the replacement for `assets/artwork/baton-tui.png`, which is stale
in three ways — it still shows the side-by-side columns, oldest-first
ordering, and flat replies.

Git state is untouched. Staging, the commit and its message are Slawomir's.

## Trial slice: pane focus and a footer that tells the truth

Two rulings, implemented together because the legend's navigation wording is
the focus state.

`Tab` toggles LIST/DETAIL focus and the navigation keys follow it — `j`/`k`,
arrows, page keys and `gg`/`G`, all of them, so there is no per-key special
case. `J`/`K` are gone from dispatch, footer and help, pinned unbound, with no
alias. Both pane labels are always drawn and exactly one carries `> `, which
is ASCII and width-stable so toggling moves nothing.

The R7 edge-to-edge rule is superseded: it carries the `DETAIL` label now,
because a focus nobody can see is a focus that does not exist. Several pins
asserted the old shape and were rewritten and declared.

**The footer is composed from `state.affordances()`, the same query key
dispatch consults.** The reported defect — an opened notice advertising `c
close` when a notice has no claim to consume — was not a missing case; it was
a fixed string. Two predicates would have drifted apart within weeks, which is
the shape of the two pane heights that hid a message and the four copies of
the pane width before them. With one, the matrix property is checkable: the
sweep asserts, over every row kind in both opened and unopened states, that
what the footer offers is exactly what dispatch accepts.

Refusals explain themselves from the same conditions, so gating did not cost
the specific messages `m` and `v` used to give.

### A conflict in the ruling, resolved and reported

"List navigation never changes detail offset" cannot be taken literally:
moving to another message resets the offset, because a scroll position belongs
to the thing being read — pinned since round three. Implemented as "list
navigation never SCROLLS the detail", with the existing reset intact, and
raised in the handoff rather than silently chosen.

### A flake I wrote and then removed

The list-focus test pressed `j` from a row that same-second tie-ordering could
place at either end of the list, so it passed or failed on a hash. It now
moves in whichever direction has somewhere to go. A flaky test is worse than
no test: it trains people to rerun until green.

### Deliberate-break checks

| Break | What fails |
|---|---|
| footer back to a fixed string | 10 tests |
| navigation ignoring focus | 9 tests |
| the marker on neither label | the both-labels pin |
| dispatch no longer consulting affordances | the matrix pin |

### Results

    just test          1685 passed
    git diff --check   clean
    protocol-9 build   658bb50159bed6aaab418224fd13f942f6ca1665ae6294195d4e55088b73f55d

Deterministic on rebuild. `bin/baton`, `DISTRIBUTION.json`, `baton_v6.py` and
`build_zipapp.py` byte-identical.

### Review: three affordance gaps, all real

Reviewer accepted the detail-offset interpretation — changing the selected row
resets the new row's offset while list navigation never scrolls the current
detail — so that is no longer an open conflict. Recorded here as accepted.

Three gaps, each reproduced as described:

- **`open` read the wrong list.** It tested the MESSAGES selection while SENT
  was on screen, so an empty inbox hid Enter from a selectable sent row and
  dispatch refused a valid read-only operation. Now from the active view, with
  both asymmetric cases pinned so the fix cannot invert.
- **`R` bypassed the shared reply affordance.** The footer grouped `r reply  R
  editor` under one affordance while only `r` was gated, so `R` stayed
  dispatchable when both forms were hidden and refused through a SECOND
  predicate inside `begin_reply` — exactly the drift one query exists to
  prevent. `EDIT_BODY` now answers to `reply`, the dispatch gate covers every
  event in the affordance map rather than a hand-listed subset, and both forms
  are pinned to move together for a live claim, a notice reply and a
  follow-up.
- **Non-browse modes drew the browse footer.** HELP advertised `n new` and
  `^R refresh`; the picker advertised open/reply/close from the row behind it.
  Each mode now has its own legend in `keys.MODE_LEGENDS`, beside the table
  that decides its keys and carrying the KEY CODES — so a test asserts every
  advertised chord actually dispatches in that mode, rather than trusting
  prose.

One label changed for a reason worth recording: the help legend said `Esc
close`, which contains `c close`. My own test caught it as a substring
collision, but a human skimming the row would make the same mistake, and help
closes nothing. It reads `Esc dismiss`.

| Break | What fails |
|---|---|
| `open` reading the inbox selection again | 2 tests |
| `EDIT_BODY` ungated again | 4 tests |
| the browse footer drawn in every mode | 5 tests |

    just test          1702 passed
    git diff --check   clean
    protocol-9 build   72f0efd4835e24e52bef71d4e6233822ee00ae99ae965265580cbe8cd017cbb4

### R4: the context line contradicted the legend beside it

`action_target_description` keyed off `row_type`, and a follow-up target is
message-shaped with `claim_id` None. So on a handled inbound or outbound row
the console said three things about one row: the legend correctly hid `c
close`, the status correctly offered a follow-up, and the context line said
`owed: reply or close`. The false one was the one naming an obligation that
does not exist — and it was the exact close cue this slice exists to remove.

It derives from CLAIM AUTHORITY now. An active claim still says what is owed;
a notice keeps its explicit nothing-owed wording; a follow-up target says
`in reference to <id>`, which is what the keys actually act on.

Pinned in both directions, because removing a false statement must not remove
the true one: handled inbound and outbound footers contain no close-is-owed
claim, an active claim still does and loses it after `c`, and a sweep across
every row kind asserts the legend and the context line never disagree about
close — cross-checked against the affordance query, so all three sources of
that one fact are the same fact.

Break check: keying the description off the shape again fails three tests.

    just test          1707 passed
    git diff --check   clean
    protocol-9 build   b8a68dae3ec9f561a0790bad074dfb59e265bbcbd5d7ba912e8fe3419d990cea

### R5: a mapped key that changes nothing is not an affordance

The modal legends advertised `Tab next field` in a notice whose fields are
exactly `("subject",)`, and `Tab next page` in a one-page picker. Both keys
are live and both move modulo one, so the footer promised a change neither
could make — the same defect as `c close` on a notice, in smaller form.

Modal entries carry a CONDITION now, and the state answers it:
`picker_paging` when there is more than one page, `more_fields` when there is
more than one editable field. Directed compose keeps `Tab` because it has
fields to move between, and the pin presses it to prove the advertised key
does something.

**The limit is stated so it is not broadened later**, and pinned: movement is
not hidden merely because the cursor sits at a boundary. `j` at the last row
still means something, because the list can move. This rule is only for
controls with no other state to reach at all.

Break check: advertising the conditional controls unconditionally fails four
tests.

    just test          1712 passed
    git diff --check   clean
    protocol-9 build   b88fda541ed42768a54738bbb3f6b0656ffc8a8578687c32651cb62d97f9c985

### R6: `v` was offered for parts it could never display

The affordance required an active claim and external storage, while the
action rejected anything not `text/...`. So an external PNG or PDF advertised
`v read`, dispatch accepted it, and the console then opened the file, hashed
it to verify the pin, and reported that it is not text — an offered action
refusing for a reason the console already knew.

The declared type is on the part, so it is decidable from the manifest without
touching the file. `_is_displayable_text` is the one predicate: the offer is
made from it and the action re-checks what came back with it, so the two
cannot disagree.

The refusal now distinguishes the three cases — no claim, inline bytes already
on screen, and an external part whose type is not displayable — and the last
one names the path, because the file is still there and that is what the human
wants next.

Pinned: external text offers `v` and it works; external `image/png`,
`application/pdf` and `application/octet-stream` do not offer it, dispatch is
gated, and nothing is read; the binary external state is in the footer matrix;
and one rule decides both the offer and the action across four media types.

One fixture fault found while writing it: the helper selected the newest row
positionally, and same-second ties order by id, so it opened an earlier
message's part and compared it against this call's expectation. It selects by
id now.

Break check: offering `v` for any external part again fails five tests.

    just test          1718 passed
    git diff --check   clean
    protocol-9 build   319b5bbc62b9074c831e96f70236bd290483e6fd72d7e7d3b9e3e17d60b1d22b

## `h`/`l` scroll the detail sideways; brackets own parts

Once DETAIL focus existed, Vim `h`/`l` not moving within the focused pane was
a contradiction in the model rather than a preference. They scroll sideways
one display cell now, the arrows do the same, `[`/`]` are the only part
navigation, and `H`/`L` are removed rather than aliased.

The wrap layer gained `wrap_overflow`: whitespace wrapping with an oversized
token left WHOLE, so there is a tail to scroll to. Ordinary prose still wraps
and gains no overflow. The elision ruling is not reversed — the ellipsis is
now the hidden-content indicator on whichever side is hidden, and headers and
structural chrome keep eliding, because shifting a label off screen because
one body line is long would make the pane unreadable to fix a line.

Availability comes from the same affordance query: DETAIL focus plus actual
overflow, measured from the rendered detail at the current width.

Three things worth recording beyond the ruling:

- **The clamp had to account for the left indicator.** `widest - pane` left
  the final cell permanently unreachable; a scroll that cannot reach the end
  of its own content is barely better than truncation. It is
  `widest - pane + 1`.
- **The reset moved onto `detail_row`'s setter.** In `preview` it fired on
  every poll, so the pane snapped back to column zero every couple of seconds
  while someone was reading. Every path that changes what the pane describes
  goes through that one assignment.
- **`Ctrl-R` was closing the opened message.** The explicit refresh
  re-previewed unconditionally, replacing an opened delivery with its
  metadata — so it discarded the content view AND the offset with it. It now
  re-previews only when a preview is what is showing, exactly as the poll
  path already did. Found because the offset had to survive `Ctrl-R`; the
  bigger fault was underneath.

| Break | What fails |
|---|---|
| content eliding again instead of overflowing | 4 tests |
| `h`/`l` back to part navigation | 4 tests |
| no reset when the message changes | the persistence matrix |

    just test          1730 passed
    git diff --check   clean
    protocol-9 build   07fabffe0041e0bd96d3b4c0cb5eb918c3c9b05d9c4095675b6e8b07d1d740fb

## Live trial: the poll stopped after Vim

Reported: compose a message, write the body in Vim, return — and an inbound
reply never appeared until `Ctrl-R` was pressed. Not delivery loss; the
wakeup died.

Both suspected paths were real, and the second is the subtler one:

- `curses_editor` suspended and resumed the screen but never restored the
  input timeout, so after any external edit `getch` blocked forever;
- `_read_key` restored itself with `nodelay(False)`, which is BLOCKING mode —
  not the finite delay it replaced. So every bare Esc and every decoded arrow
  also killed the poll.

The timeout is a LOOP INVARIANT now: re-armed before every blocking read, on
editor return, and after every escape-decoding detour. `arm_poll` is the one
place it is set.

Pinned on the mode transitions themselves, with a fake window, because the
defect is about which mode `getch` is left in — invisible to the model tests
and expensive to catch over a PTY. Four pins: arming sets a finite timeout;
bare Esc, a decoded arrow and an unknown sequence each leave a finite timeout
rather than blocking; and the configured interval is what gets re-applied, so
re-arming cannot become a spin.

Break check: restoring `nodelay(False)` fails four of them.

### And another flake of mine, caught by the full run

The offset-persistence test moved to "the row below" to prove the reset, and
same-second ties can put the fixture row last — so `move` was a no-op that
reset nothing. It passed in isolation and failed in the suite. Fixed to move
in whichever direction exists. That is the second time this shape has bitten
in one session; both are now written down.

    just test          1735 passed
    git diff --check   clean
    protocol-9 build   0f22d53aa740f38c37482d824626c831ee3792236f470358c3a8d1d75fd14572

## Batch 1: claim-and-open on highlight

The founding rule of this console was that selection is observational and
`Enter` is the only act that takes ownership. Slawomir reversed it for
directed messages. FINDING §16 carries the new contract and the old bullet in
"Pinned TUI interaction" now points at it as superseded, so nobody reads the
original and thinks it still holds.

`select_row` is the commit path and `preview` stays observational — that split
is what keeps the poll honest, and it is the one thing most worth protecting:
a poll that committed would claim the entire mailbox by itself. The break
check for it fails 561 tests, which is a fair measure of how much of this
console assumes polling is safe.

Six existing pins asserted the superseded rule and were rewritten, each
recording what it used to say:

- browsing the whole inbox claiming nothing → it now claims one per directed
  row and still zero broadcasts, and repeated passes claim nothing new;
- navigation keys never changing the authority → they never consume a
  broadcast and never dispose of anything, which is the half that was never
  on the table;
- navigating away dropping the action target → the target now FOLLOWS the
  selection, and the property that survives is that the target and the
  displayed row can never be different rows;
- `gg`/`G` claiming nothing → they claim only the destination, asserted by
  comparing the claimed set against the two rows visited;
- a failed PREVIEW never describing another row → the failure mode moved to a
  failed CLAIM, and the fail-closed rule is asserted there instead;
- four PTY tests that pressed `q` and expected an exit — the console now
  claims the row it starts on, so quitting asks. Exercising that confirmation
  is exercising the protection the ruling depends on.

New pins cover startup claiming, the poll claiming/seeing/stealing nothing, a
reordering poll unable to redirect a claim, notices staying explicit, `Enter`
retiring once the row is open, DETAIL navigation committing nothing, the
accumulation being real and nothing auto-resolved, and handled/outbound rows
staying observational.

| Break | What fails |
|---|---|
| selection back to observational | 7 tests |
| highlighting a notice consumes it | 4 tests |
| the poll commits too | 561 tests |

    just test          1743 passed
    git diff --check   clean
    protocol-9 build   3e7a97caae1051c218ab0da64a2d84969f27fcc2649a133258a78a0b339a929a

### Batch 1 review: three corrections

- **A view switch bypassed the commit path.** `i`/`o` still called `preview`,
  preserving the old "switching writes nothing" rule — so arriving in an empty
  MESSAGES, letting a pending message land, and pressing `i` left the row
  highlighted and unclaimed. The extra-Enter ceremony the ruling removed,
  reachable by a different door. A view switch establishes its destination's
  highlighted row like startup does, and goes through `select_row`, which
  decides per ROW: a broadcast stays explicit and sent/handled/outbound rows
  open observationally.
- **Live guidance still stated the opposite contract**, which is safety
  semantics and not polish. Corrected in README, `?` help, the module
  contract, `move`, `open_selected`, the TRIAL key table, the core-enhancement
  invariant list, and the `v`/`m` refusals — those told the human to press
  Enter to claim, which is no longer the normal path and could never help on
  an unclaimable row. They name what is missing now: a claim you hold.
- **An old Enter pin had gone vacuous.** It moved the cursor and THEN called
  `open_selected`, asserting the claim afterwards — but the move now does the
  claiming, so the call proved nothing while the name still said it did. It
  brackets the selection transition itself now, asserts exactly the row landed
  on was added, and additionally proves a subsequent Enter does not claim
  again.

| Break | What fails |
|---|---|
| the view switch back to `preview` | the empty-MESSAGES arrival pin |
| selection back to observational | 3 state pins, including the rewritten one |

    focused tests     940 passed
    git diff --check  clean

Full suite and rebuild deferred to the pre-commit gate, per the reviewer's
cadence ruling.

### Batch 1 R2 residuals

Four live statements of the superseded contract survived the first pass, and
two of them were mine to have caught: the `?` help entry for `Enter` and the
TRIAL key table were edited in a script that asserted partway through and
never wrote, so I reported them corrected when they were not. Verified
individually this time.

- `state.py`'s module docstring used "moving the cursor creates no claim" as
  its example of a checkable safety property. The example is now the rule that
  survived: the POLL creates no claim.
- `test_tui_state.py` called "observation never claims" the most important
  property. Selection is a commit now, so the property is named precisely —
  the poll never claims, and a broadcast is never consumed by being looked at
  — with a note that a test file asserting the opposite of its code is worse
  than no docstring.
- `?` help described `Enter` as the thing that claims a message. A directed
  row was claimed when it was selected, so that sends the human looking for a
  step that already happened. It describes what Enter is still for: marking an
  unseen notice seen and reading it.
- TRIAL's trial-package intro warned that pressing Enter claims a real
  message. That understated the exposure rather than merely being stale —
  moving the cursor is enough now — so it says SELECTING, with the old
  wording recorded.

A grep for the old phrasings across the console, its tests, README and the
finding documents now returns only the explicit supersession note in FINDING
and the corrected sentence itself.

    focused tests     940 passed
    git diff --check  clean

### Batch 2 — two correctness items

Authorised in `1a0de387` ("Batch 1 approved; proceed with Batch 2"), which
also set the cadence: targeted tests only, no product decision outstanding.

**Chrome no longer pans.** Sideways movement used to slide every produced
line, so panning to read the tail of one long body line carried the `From:`,
`Subject:`, `State:` and part headers off the left edge — the human lost which
message they were in and which part they were on in order to fix a single
line. `_note_pannable` now records which produced indices are CONTENT as they
are produced, and only those slide; `detail_overflow` measures the same set,
so a long header cannot advertise a key that would do nothing to it.

**A fresh `R` that gives nothing back restores the original.** `R` from browse
is ONE action — start the reply and open the editor — so if the editor is
cancelled, exits unchanged, is missing, or is killed, the action did nothing
and the human is left reading the message they were reading. `Ctrl-E` from
inside a composition is unchanged: there the draft is the human's own and
survives whatever the editor did. `abandon_fresh_reply` deliberately does not
touch the status, because the editor's own explanation of what went wrong is
the thing worth showing.

One pin of mine was superseded by this, and it was mine:
`test_a_cancelled_editor_publishes_nothing_and_keeps_the_follow_up` asserted
the follow-up context SURVIVED a cancelled fresh `R` so the human could retry
through `Ctrl-E`. The new rule is better — there is no human-authored draft to
lose, since the "draft" was only the subject the console seeded — and retry is
pressing `R` again. The docstring records the reversal rather than quietly
rewriting the assertion.

**A pin I wrote for this round was vacuous, and the break check is what
caught it.** `test_a_long_header_offers_no_sideways_movement` asserted that a
250-character subject offers no sideways movement. It passed with the overflow
measurement deliberately broken to include chrome — because the renderer elides
every chrome line to the pane width long before anything measures it, so the
two measurements are indistinguishable on that fixture. Replaced with
`test_no_chrome_line_is_ever_wider_than_the_pane`, which asserts the property
that actually makes freezing chrome safe: a frozen line that ran past the edge
would be permanently unreadable, so chrome must arrive already fitted. That one
fails when the part-header fitting is removed.

| deliberate break | what failed |
|---|---|
| pan every produced line, not only content | both chrome/content pins |
| measure overflow over all lines | (nothing — this is what exposed the vacuous pin) |
| stop fitting part headers to the width | the replacement chrome-width pin |
| drop `abandon_fresh_reply` from dispatch | all three fresh-`R` cases |

    full suite        1755 passed
    git diff --check  clean

Behavioural note observed while verifying, worth stating rather than fixing
silently: a short content line panned right renders as a bare `…`, because its
text really is off to the left. It is consistent with the model — the marker
says "there is text to the left of this window" — but it looks like an empty
line with a stray glyph, and it may read badly in the next trial.

### Batch 2 R1/R2 — both corrections were real, and one was live

Review `f36228d0` returned changes_requested on both items. Both criticisms
held, and neither was reachable from the tests I had written.

**R1: semantic panning stopped at the active directed delivery.**
`_detail_lines` threaded `pannable` into `_delivery_lines` only. An opened
notice, a handled inbound copy, an outbound copy and a sent notice all
reported zero body overflow and could not reveal an oversized token at all.
Threaded through `_notice_lines` and `_sent_content_lines`, and so through the
`_rendered_parts` recursion, which carries the marking into nested multipart
while leaving the container label and every nested part header fixed.

Writing the pins found a SIXTH shape the review had not named: `sent_notice`
is its own detail key with its own branch, reached only from the Sent view.
It was missed by the same threading and is fixed with the rest.

**R2: a real Vim `:q!` was still treated as a successful edit.** This is the
live failure the whole item exists to fix, and my correction did not reach it.
`edit_body_externally` returned false only when the result was `None` — the
failure path. `:q!` exits ZERO and leaves the file untouched, so `edit_text`
returns the seed it had just written, the state imported it, and the human was
left in the provisional reply they never typed. Identical bytes are now no
edit, whatever the exit status said.

My parametrized test labelled its cases "cancel, unchanged, missing, non-zero,
killed" while every one of them supplied `outcome=None`. The name claimed a
coverage the body did not have — the same class of error as the vacuous pin
earlier in this batch, and worse, because the id string is what a reader
trusts. It now carries a real unchanged-success case, and the raw fact is
pinned once at its source in `test_tui_editor.py` with a no-op successful
runner.

One consequence, stated because it is a behaviour change and not only a fix:
saving a seeded quote verbatim is also no edit. That is intended — an
unmodified quote is not an answer — but a human who opens `R`, reads the
quote, and saves it unchanged now gets "editor returned no changes" and their
original view back.

| deliberate break | what failed |
|---|---|
| revert the threading to delivery only | 5 of the 6 shape pins |
| stop forwarding through the container recursion | the nested-multipart pin |
| treat an unchanged result as an edit | all 4 restoration pins |

The short-content `…` at a large offset stays as it is: accepted for the next
trial, and the correction is explicitly not widened around it.

### Batch 3 — the noise sweep

One cohesive pass over seven rulings, against Slawomir's stated acceptance
rule: if the same fact or instruction appears in two layers, name its single
owner and remove the duplicate; never replace removed text with a differently
worded reminder; never remove the state a human needs to decide or act.

**Header.** The literal `baton` is gone from both header forms. Both now open
with the participant address.

**List.** Every status glyph is one display cell: `Q P R C E X` for outbound
lifecycle, `N` for an authored notice, `!`/`✓` (`S` in fallback) for notice
receipt, blank/`*`/`x` unchanged inbound, `?` unknown. `GLYPH_WIDTH` is 1, so
the two recovered cells go to the subject. Alignment, not punctuation, marks
the column boundary.

**Detail.** The three `Enter: ...` preview prompts, the quick-reply tutorial
sentence, the `new message (...)` heading with its whole parenthetical, the
Sent badge glossary, the "Enter opens your own copy, read only" sentence,
`(Ctrl-E to edit)`, `'m' to materialize` and `(press v to read it here)` are
all removed. The `FOLLOW_UP_*` headings say `Answered` and `Sent` — state —
instead of listing the follow-up keys.

**Status.** No longer restates the mode legend: starting a reply says what
started, composing says what is being composed and to whom.

**Compose.** A genuinely fresh compose or notice OWNS the detail pane. Mode
alone cannot decide that — a follow-up is a composition too and must keep the
message it answers on screen — so `_fresh_composition` reads the explicit
reply context, and both directions are pinned.

**Where it went instead.** `?` help gained a Lifecycle section that
distinguishes claiming, recording a notice receipt, and reopening, plus a full
List notation section; the send shorthand ("from ANY field, and a subject
alone is enough") moved there too. The README gained the same notation as a
table. `test_help_and_readme_own_the_notation_the_panes_gave_up` asserts both
owners are complete, because removing an explanation is only safe if its one
owner carries it.

The sweep itself is pinned by a parametrized test over twelve instruction
phrases, checked across preview, opened message, notice, reply, compose and
notice-compose — swept rather than fixed one literal at a time, because
fixing only what was reported leaves the same sentence in the next pane.

| deliberate break | what failed |
|---|---|
| put one `Enter: claim and open` prompt back | the sweep and the relocation pin |
| brackets back on one badge | the one-cell column pin |
| weaken one help entry | the help/README ownership pin |
| draw the row behind a fresh compose | the compose-owns-the-pane pin |
| hide the original for a follow-up too | the follow-up-keeps-context pin |

**A second vacuous pin of mine, caught the same way.** The first version of
`test_a_fresh_compose_owns_the_pane` asserted the unrelated message's BODY was
not behind the form. It passed with the fix disabled — a preview never renders
content, so that text was never on screen. It asserts the metadata block now,
and fails when the fix is removed.

    full suite        1784 passed
    git diff --check  clean

**One PTY test is FLAKY, and it is not the product.**
`test_the_whole_legend_is_visible_on_one_row_at_a_wide_terminal` asserts the
confirmation legend is painted on row 24 by matching `\x1b[24;<col>H` in the
transcript. Curses addresses that row two ways depending on what it painted
immediately before: `\x1b[24;3H` (CUP) or `\x1b[24d` (VPA). Five consecutive
runs of the SAME build produced three CUP and two VPA, so it is curses
optimising a redraw, not a behaviour that changed. Both spellings are row 24,
and every other assertion in the test -- the full literal, the single
question, the arming keystroke -- passes either way.

Not fixed here: it is an existing test and the edit is not one this batch was
authorised for. Referred to the reviewer with the measurement.

### Batch 3 R1–R4 — the footer itself goes

The sweep had removed the DUPLICATES of the ordinary hints. The ruling is
broader: the ordinary bottom hints go away altogether.

**The footer is one row.** `_footer_height` returns 1 everywhere except the
quit confirmation, which still needs two — the question and the reason it is
being asked are different facts and claims are about to be abandoned. The
reclaimed row goes to the panes. The send confirmation keeps its exact
pinned literal.

**Removed as render-only machinery**, once nothing displayed it: the
`_CONTEXTUAL`/`_GLOBAL` label tables, `legend_actions`, and
`state.action_target_description`. What they were composed FROM is untouched,
because it was never presentation — `affordances()`, `modal_affordances()`
and `unavailable_reason` are the single query dispatch consults, and
`keys.MODE_LEGENDS` still carries each modal control's key codes so a test can
assert every documented chord really dispatches.

**The status bar stopped restating the footer** in three more places: the
quick reply, the compose, and the recipient picker each said what started
instead of listing keys.

**The passive poll writes nothing.** The `N new: senders` line was a third
copy of mailbox state the header counts and the newest-first list shows, and
it was written by a timer over whatever the human's last action had reported.
The pin asserts a real outcome — the claim taken by moving — survives an
arrival poll while the row and the count appear.

**R5 is finished, as dispatch rather than display.** `_MODAL_AFFORDANCE` maps
`PICK_PAGE`/`NEXT_FIELD`/`PREV_FIELD` to the modal conditions, and `_allowed`
consults `modal_affordances()` for them. A one-page picker and a one-field
notice now refuse with a reason instead of dispatching a transition that
reaches nothing; multi-page and multi-field cases still work. Boundary
movement is deliberately NOT included: `j` on the last row still means
something.

**R4, authorised:** the PTY row-24 assertion accepts CUP and VPA. Six
consecutive runs pass where it previously failed about half the time.

Thirty-five tests asserted the old footer. None was deleted. The helper they
share now reads the affordance query instead of the screen — the labels
survive only as test-local wording, and a new parametrized pin sweeps
twenty-seven catalogue phrases across every mode and both focus states to
prove none of it is rendered. The four that asserted the target clause were
re-pointed at the facts that survived it: `affordances()["close"]`,
`unavailable_reason`, `follow_up_context` and the header's unresolved count.

| deliberate break | what failed |
|---|---|
| footer back to two ordinary rows | the one-row geometry pin |
| a reworded hint on the empty status row | the catalogue sweep and the blank-row pin |
| poll writes an arrival status again | both poll-purity pins |
| modal gate off | the one-page picker and one-field notice pins |

### The reclaimed row, and a stale-bytecode episode

Review caught that only the RENDERER had been told the footer shrank.
`layout_for` and `picker_capacity` still subtracted three rows, so the model's
viewport stayed one row smaller than the screen: the reclaimed row drew, and
nothing could scroll to it. There is now one authority — `ORDINARY_FOOTER_ROWS`
and `ordinary_body_lines(lines)` — used by the model layout, the modal picker
measurement and the renderer alike, and pinned by comparing what the model was
told against what is actually drawn at 12/20/24/40 lines.

Test helpers carrying `[:-2]` or `lines - 3` were the same fault in the
fixtures: they silently dropped a real pane row, so a cleanup or panning
assertion could pass while ignoring the bottom of what the human sees. All of
them derive the boundary now, and a new pin uses a fixture whose content
actually reaches that row — the existing fixtures leave it blank, which is
exactly why the wrong slice went unnoticed.

**A stale `__pycache__` made a test lie for several minutes.** After the helper
edit, `test_the_pane_helpers_reach_the_bottom_row_of_the_pane` failed while
`inspect.getsource` showed the corrected helper and an inline copy of its body
passed. The loaded module was compiled bytecode that no longer matched the
file. Deleting `__pycache__` resolved it and the suite is green.

Recorded rather than swept up, because the failure mode is nasty in exactly
this situation: heavy editing of test modules, then trusting a suite count.
The safe habit is to clear the caches before a result is reported as evidence.

    full suite        1820 passed
    git diff --check  clean

### Consolidated pre-trial gate

    fresh-cache full suite      1820 passed
    git diff --check            clean
    distribution/boundary       50 passed
      (packaging isolation, docs consistency, core API, core parity)

    bin/baton      a23461ae7577422f5c4ade86eae370926b2dc41bc93ecd7732c29b2785374566
                   BYTE-IDENTICAL — the frozen agent CLI is untouched
    bin/baton-tui  3e7a97ca… -> 94de5d893d2df639f24c78d80f7a0c39a3c3454b62698ad4e3e695d60af267ce
    rebuild twice  94de5d89… both times — deterministic
    DISTRIBUTION-TUI.json  one field moved, `artifact_sha256`, tracking the
                   rebuild. That is the manifest doing its job.

The packaged executable was driven on a real 100x30 PTY against an ISOLATED
temporary instance — never the live mailbox. Launch, list navigation, Tab
focus and detail scrolling, opening a message, `?` help and scrolling it, the
recipient picker and cancelling it, then quit through the unresolved-claim
confirmation. No traceback, exit status 0.

Two behaviours worth recording from that run, both correct: the console starts
on the NOTICE row and takes no claim, because broadcasts stay explicit; moving
down to the directed row claims it, and the badge changes to `*` on the same
keystroke.

### The screenshot — stale again after header simplification

Slawomir replaced `assets/artwork/baton-tui.png` from his own terminal after
the earlier trial. That capture was authoritative for its candidate, but a
later ruled change made it stale again: the top line now begins
`Messages: N retained, M awaiting your reply/close` (with the one focus marker
when focused), the lower rule has no `DETAIL` label, and the participant
identity moved to the right side of that rule.

The rule deliberately carries one divider cell after the identity. A packaged
terminal may decline to draw the rightmost cell of a full-width row; without
that shield it drew `acme.implemente`, a different and nonexistent participant
address. At narrow widths the identity disappears whole rather than becoming
a lie.

A fresh capture from a real terminal is outstanding and cannot be produced by
an agent. The existing image remains historical evidence of the earlier
candidate, not a depiction of the current UI.

    sha256  38b99ab92c99e430ffc3b31cfc226e68ce83428327683e868460d8e12a47539f
    bytes   237235

### Trial finding — a successful send returns focus to the list

Slawomir's rule from the terminal trial: the send finished that piece of work,
so the natural next action is another message. On success — directed compose,
notice, claim-resolving reply quick or full, and follow-up — pane focus
returns to LIST. The selected row identity, the visible detail and the success
status are untouched, no jump to the sent row, no switch to SENT, and no extra
authority read or write: it is one assignment inside a path that had already
finished its work.

Every positive pin starts with DETAIL focused, or it would assert what was
already true. The negative side is pinned too, and matters more: a failed
send, a declined confirmation, and a cancelled draft all leave focus and draft
exactly as they were. Placing the assignment before the failure branch — so
the focus moved whatever happened — fails the failed-send pin.

| deliberate break | what failed |
|---|---|
| drop the assignment | the successful-reply pin |
| move focus before the failure branch | the failed-send pin |

### Trial finding — the empty body row advertises the key

`body:    (none)` becomes `body:    Ctrl+E to edit`. Slawomir's ruling from the
terminal: the empty state should offer the action available, and a row with no
body has no state of its own to report.

This is a deliberate, ruled EXCEPTION to the batch-3 rule that keys live only
on the footer and in `?` help. It is recorded as one in the sweep's phrase
list rather than left to look like an oversight — and it happens not to trip
the sweep by spelling alone, `Ctrl+E` against the swept `Ctrl-E`, which is
exactly why it is written down. What the sweep still forbids is the removed
`(Ctrl-E to edit)` hint sitting beside a body that already has content.

The boundary is pinned in both directions: an empty body names the key, a
populated one reports `3 lines, 13 characters` and mentions no key at all.

| deliberate break | what failed |
|---|---|
| revert the label to `(none)` | both empty-body pins |
| add the label to the populated row too | both empty-body pins |

### Trial finding — attachments: choose a root, then a path inside it

The ruling moved three times during the trial (absolute-only, then a hybrid,
then this) and only the last is in force: the `attach` field is replaced by a
CHOSEN root and a path relative to it. `root_id:relative/path` is a
serialization, and asking a human to type it is asking them to do the
adapter's job.

**Core** gained one additive read-only method, `list_roots()` — the configured
roots with their absolute base directories, deterministic order, the same
shape and reasoning as `list_participants`.

**State** splits `attach` into `attach_root` (chosen, never typed, so it is
not in `COMPOSE_EDITABLE`) and `attach_path` (typed, relative). `MODE_PICK_ROOT`
is its own mode reusing the recipient picker's conventions through the SAME key
table — letters select, Tab pages, Esc cancels — because two tables would let
them drift apart for no reason the human could see.

**The locator exists in exactly one place**, `attachment_locator()`, built at
the boundary for the core call. Compose and send review show `root:` and
`path:` on separate rows, and a pin asserts the collapsed form never appears
on either screen.

**Refusals** are computed by `attachment_error()` and each names what is wrong:
no root chosen, empty path, an absolute path in the relative field, Baton's own
locator typed into it, a path outside the root, a missing file, a directory,
an unreadable file. Symlinks are resolved on BOTH sides before the containment
test — a prefix test on the unresolved path accepts a link inside the root that
points out of it, and the deliberate break confirms it.

**Preflight is not authority, and that is pinned.** Core still verifies and
hash-pins at publication. `test_preflight_is_not_authority` passes preflight,
deletes the file, sends, and asserts no message was published and the draft
survived. Without that boundary the console's earlier look would quietly
become a second, weaker source of truth.

**Enter on the EMPTY attach path opens the picker** rather than reviewing the
send — otherwise the picker sits behind "Enter from any field reviews" and is
unreachable. Once a root is chosen, Enter reviews as before. Both directions
are pinned, and `?` help documents the workflow.

Multiple attachments stay out of this slice by ruling; the field remains one.

| deliberate break | what failed |
|---|---|
| Enter reviews instead of opening the picker | the picker-route and modal-legend pins |
| skip preflight at send | four refusal cases |
| containment tested without resolving symlinks | the outside-root refusal |
| collapse root and path into a locator on screen | the leak pin |

    fresh-cache full suite      1843 passed
    git diff --check            clean

### Root-picker review — five corrections, and two claims that were not true

**R3 is the one worth reading first.** The handoff said the symlink deliberate
break and every refusal were pinned. Neither was true. The break I ran removed
`realpath` and the case that failed was `../outside.md` — a `..` case, not a
symlink one — and I reported it as symlink coverage. There was no `os.symlink`
anywhere in the suite, and no unreadable-file case, though the refusal list
named both. Same class as the vacuous pins earlier in this work, one step
worse: the earlier ones were tests that could not fail, this was a claim about
tests that did not exist.

Now pinned: a LEAF symlink that stays inside the root and points at a regular
file — the case a `realpath` check accepts and core refuses — an INTERMEDIATE
symlink one component up, an unreadable regular file, and a fifo for the
special-file half of the contract that only had its directory half.

**R1** — preflight ran only inside `send_compose`, so a bad path reached
`Send? Y/n` and the refusal arrived after the human had answered it. It now
runs in `arm_send`, which refuses, keeps the caret on the path field and never
enters the confirmation. The check inside `send_compose` stays: the file can
change between review and confirmation. Core checks a third time because core
is the authority.

**R2** — preflight used `join` + `realpath`, which accepts `./file`,
`sub//file`, `sub/../file` and in-root symlinks that core always refuses. It
now mirrors core: clean relative components, then a component-wise walk with
`O_DIRECTORY|O_NOFOLLOW`, exactly as `_resolve_attachment` does. A preflight
that predicts a different answer from the authority is worse than none.

One accuracy detail: a symlink-to-directory refused by `O_NOFOLLOW` reports
ENOTDIR on Linux, so the errno alone would tell the human a folder "is not a
directory". `lstat` on the same descriptor says what it actually is.

**R4** — `":" in head` treated every colon as Baton serialization, and checked
existence against the process CWD, so `notes:2026.md` was refused or not
depending on where the console was started. It is diagnosed only when the
prefix names a CONFIGURED root; otherwise a colon is a filename character,
which is what core thinks.

**R5** — both the locator and the validator called `.strip()` on the typed
path, so a draft showing ` report.md ` would publish `report.md`: a different
file from the one on screen. The path is now used exactly as typed, and
leading or trailing whitespace is refused by name — whitespace is invisible,
so the refusal has to say it is there. The root id is still normalised,
because it is picker-owned rather than typed.

**The preflight-is-not-authority pin was rebuilt too.** With preflight now
mirroring core, a path that passes one and fails the other is hard to
construct on purpose — which is the point, and which is why the old test could
no longer prove what it claimed. It is now two: a file that VANISHES between
review and confirmation is not published and the draft survives; and a store
whose `send` refuses proves the console asks the authority at all and survives
its answer.

| deliberate break | what failed |
|---|---|
| preflight only at send, not at arm | ten refusal cases |
| clean-path rules relaxed to realpath | four syntax cases |
| `.strip()` the typed path | the exactly-as-typed pin |
| every colon means serialization | the colon-filename pin |

The packaging guard caught the correction itself: mirroring core's errno
handling meant importing `errno`, and `test_the_tui_depends_only_on_the_stdlib_and_the_core`
refused it. The guard was right — a new import into the console is a decision,
and this one was only for message strings. The diagnosis comes from `lstat` on
the same descriptor and from `FileNotFoundError`/`NotADirectoryError` instead,
which is also more portable than the errno it replaced.

### Trial finding — the status column answers what YOU owe

Slawomir's model: people think in todo lists, not in store state machines. The
inbound glyph answers one question — does someone wait on me, and if so have I
read it and answered?

    •  addressed to me, not opened
    ○  opened and mine; a reply or close is still owed
    ✓  I replied; nothing owed here
    C  I closed it without replying
    !  a notice I have not seen        ✓  one I have
    x  content withheld; its parts failed their pins

A blank and `*` are superseded. The blank said "waiting for me" by saying
nothing at all, which is the least visible mark on the screen for the state
that most demands attention. The inbound `R` is superseded too: what matters
to a human is that they answered, not that the store recorded a response
disposition. `C` stays a letter deliberately — closing without replying
completes the obligation but is not the same act, and one tick for both would
hide a choice they made.

Outbound rows are unchanged — `Q` and `P` answer what the OTHER side has done
— and `pending` reading `•` inbound and `Q` outbound is the point of the
ruling rather than an inconsistency in it. The exact protocol state stays in
the detail pane; header counts still count real obligations.

Ten pins, every one read off the DRAWN row rather than from the helper.

### Trial finding — `r` opens the editor, `R` is the quick subject line

Reversed from what shipped. The reply people actually write is a body in their
editor; the subject-only one is rare, so the easier key serves the common act.
`Ctrl-E` still promotes a quick draft to the editor.

The swap touched 78 keystrokes across the driver tests and both PTY reply
scripts. Test NAMES were renamed with it — `test_a_fresh_R_...` describing a
lowercase `r` would be a comment that lies at the call site, which is the
thing this suite keeps catching in other people's code.

`?` help and the README carry the new mapping, and a pin asserts the OLD
wording is absent rather than merely joined by the new.

The packaged PTY smoke now drives lowercase `r` with a real editor script
through a real terminal: curses suspends, the editor writes, the bytes are
imported, and the panes are drawn again with `draft imported` in the status
row. That round trip is the one thing the in-process tests cannot exercise,
because they inject the editor and never leave curses.

| deliberate break | what failed |
|---|---|
| inbound falls back to the store's badge | the replied-and-cleared pin |
| one tick for replied and closed alike | the visibly-different pin |
| swap the keys back | five mapping pins |
| restore the old help wording | the mapping-once pin |

### Trial notation — how a key is SPELLED where a human reads it

Two clarifications, applied together: a Ctrl chord takes a LOWER-case letter,
because Shift is not part of the gesture and a capital implies it is; and
letter case alone says Shift, so `r` and `R` are written as themselves and
`Shift+r` never appears. Named keys keep `Enter`, `Esc`, `Tab`, `PgUp`, `PgDn`.

`^E`, `Ctrl-E` and `Ctrl+E` are gone from `?` help, every modal legend, the
rendered screen and the README. The CONSTANTS are untouched — `CTRL_E` is
code, and churning it to match a presentation rule is how a rename becomes a
diff nobody can review.

Swept by a pin across all four surfaces at once, so the notation cannot drift
back in one of them while the others stay right, plus a pin that the chords
still dispatch: the spelling changed, the bindings did not.

Stale claims about the OLD `r`/`R` pairing were removed with it —
`test_uppercase_R_opens_the_editor...` became
`test_the_editor_key_does_not_go_through_the_quick_reply_first`, its sibling
likewise, and the `keys.py` comment saying `R` was taken by the full reply.
A test name that describes the opposite of what it presses is the same defect
as a footer advertising a key that refuses.

| deliberate break | what failed |
|---|---|
| one capital control letter in a legend | the notation sweep |
| a spelled-out `Shift+r` | the sweep and the shifted-letter pin |

### Notation re-review — five narrow residues, and a stale-bytecode trap

**One was functional, not cosmetic.** The mass `r`/`R` swap turned
`_press(state, store, ord("r"))  # a refresh is not a move` into a line that
opens the EDITOR. The comment and the test name still claimed refresh, so it
could have passed while refresh regressed. It presses `K.CTRL_R` now.

**The four-surface sweep was three.** Its docstring said it covered the
rendered screen and it did not — it read `?` help, the modal legend tables and
the README, all of which are source data. A drift that only reached the drawn
output would have passed. It now renders four real screens (opened message,
reply, help, compose) and sweeps those too. Same overclaim shape as the
symlink coverage earlier: the sentence was ahead of the assertion.

Two holes in the regex went with it: the README was exempt from the caret
check, and a hyphenated lower-case `Ctrl-e` slipped through a pattern that
only looked for capitals. Both break-checked.

The remaining old-pairing headings and the two `Ctrl+E` rows in PLAN are
corrected.

**A stale `__pycache__` bit for the second time, and the mechanism is now
clear.** A deliberate break and its restore happen within the same second, and
`Ctrl-e` and `Ctrl+e` are the same length — so the source's (mtime, size) can
match what the `.pyc` written during the broken run recorded, and Python keeps
the broken bytecode. Four tests failed against a source tree that was already
correct.

The habit that prevents it: clear the caches after a break check, not only
before reporting a suite count.

### The recovery contract must not contradict the shipped keys

Review found the PLAN still teaching the superseded mapping in its NORMATIVE
sections: the key table, the prose under it, and the resolved reply-act
decision. Those are recovery instructions — what someone picking this up cold
would follow — so a stale one is worse than a stale comment. Corrected to the
final contract: `r` into the editor, `R` the quick subject, `Ctrl+r` refresh,
`Ctrl+u` kill-left, `Ctrl+e` promotion, browse `e` absent.

Where the OLD reasoning is worth keeping it is now explicitly labelled as
history rather than deleted — the ruling that moved refresh off a plain letter
still holds, and its reason is unchanged even though the sentence that carried
it named `R` as the full reply.

Two live test comments still inverted the pair, and the PLAN said the
screenshot was both captured and stale in adjacent paragraphs. Both fixed.

### Delivered behaviour is the zipapp, not the source

Slawomir trials `bin/baton-tui`. Ruled: every handoff asking for his review
must carry a NEWLY REBUILT artifact containing exactly that candidate, and
source-only behaviour is not delivered behaviour.

That makes the current artifact — built before the notation sweep and the
recovery-contract corrections — stale for trial purposes, and it is not to be
put in front of him as though it were the candidate. The rebuild waits for the
consolidated gate the reviewer authorises, and the handoff says which build
the hash belongs to.

### Consolidated release-candidate gate

    fresh-cache full suite            1875 passed
    git diff --check                  clean
    packaging + core boundary         50 passed
    bin/baton-tui, two builds         f3b38cde… both times — deterministic
    DISTRIBUTION-TUI.json             artifact_sha256 matches that build
    bin/baton                         a23461ae… BYTE-IDENTICAL to its pin
    DISTRIBUTION.json                 unchanged, matches

The packaged smoke ran the REBUILT zipapp on a real 110x34 terminal against an
isolated instance, seeded so every obligation state exists at once. Read off
the drawn screen before any keystroke:

    • Unopened one      ✓ Answered one      C Closed one
    Q Sent out          ! Broadcast         ↪ threaded reply

Then the cursor moved onto the unopened row and it became `○` on that
keystroke — claim-on-highlight, visible. `r` suspended curses, ran a real
editor, imported its bytes and returned to a redrawn console with
`draft imported` in the status row. No traceback, exit 0.

The header read `0 awaiting your reply/close` at startup, because the row it
landed on was already answered — the count follows real obligations rather
than the cursor.

### Ruling — completion is direction-independent

Superseding the glyph set from a few rounds earlier. The column now answers
two different questions depending on where the item is:

    LIVE, and direction matters — who owns the next action?
      •  inbound, not opened by me      ▷  outbound, not picked up yet
      ○  inbound, opened and owed       ▶  outbound, they own it now
      !  a notice I have not seen

    TERMINAL, and direction does not — what became of it?
      ✓  answered by a reply, whichever side answered
      C  closed without a reply
      ✓  a notice I have seen

`R` is gone from the human vocabulary entirely. A completed inbound row and a
completed outbound row in equivalent states now render the same `✓`: the party
column already says who acted, and the terminal glyph repeating it was the
duplication this column exists to remove.

The structural consequence is bigger than the characters. The messages pane
had a `direction == "out"` branch that reached a DIFFERENT function, which is
how the two sides came to disagree about one fact — the outbound side reported
the store's word while the inbound side reported the human's. There is one
dispatch now, and it reads direction off the row, so the disagreement is not
expressible.

`Q`/`P` survive only as the non-UTF-8 fallback for `▷`/`▶`, with `D` as the
direction-independent completed fallback. **The two live inbound fallbacks are
mine and were not ruled** — `*` for unopened because it is the loudest ASCII
mark and unopened is the state that most wants attention, `o` for opened
because it is the same shape as `○`. Flagged as unruled in the handoff rather
than presented as decided.

Held, not implemented: `C`. A hold arrived saying Slawomir is considering ONE
checkmark for replied, closed and seen. `C` stays exactly as it is until that
is ruled.

| deliberate break | what failed |
|---|---|
| completion depends on direction again | the same-store-state pin |
| outbound live states borrow the inbound marks | three direction pins |

**The ruling's threading broke the packaged console, and only the PTY tests
saw it.** `status` reached `render` and `_inbox_pane` but not `render_styled`,
which is the renderer the DRIVER calls. Every in-process test passed — they
call `render` — while the console died on a `TypeError` at its first draw.

`test_every_marker_the_driver_passes_reaches_both_renderers` now asserts that
whatever `markers_for` produces, both renderers accept and agree on, and it
derives the list from the marker dict rather than keeping its own copy: a
marker added to one signature and not the other is precisely the failure. It
fails when `status` is removed from `render_styled` again.

Worth stating plainly: a suite of 1875 tests passed on a console that could
not start. The eleven that caught it were the ones that run the real thing.

### The `C` hold resolved — ONE terminal mark

Ruled after the hold: `✓` covers replied, closed, and a notice seen. `C` is
removed from the human vocabulary alongside `R`.

I had argued for keeping `C` distinct — closing without a reply completes the
obligation but is not the same act, and one tick for both hides a choice
someone made. The ruling is better on the question the LIST actually answers:
is anything still owed. That answer is identical, and a one-cell column is the
wrong place to carry a second fact.

What made it safe is that the fact is not lost. The detail pane keeps the
exact state and outcome, and the pin asserts BOTH halves — a closed row marks
`✓`, and opening it still shows `closed`. Collapsing a glyph is only sound
while what it collapsed remains recoverable somewhere a human can reach.

| deliberate break | what failed |
|---|---|
| closed gets its own mark again | the one-terminal-mark pin |

### README — what Baton is, before the picture

Ruled: the value proposition goes immediately after the opening paragraph and
before the screenshot. No Internet connection or coordination service, fully
offline, completely sandboxable, participants coordinating as PEERS through a
shared SQLite mailbox — with no privileged coordinator, daemon or always-on
server.

The wording is deliberately "coordinate as peers" rather than peer-to-peer:
the peers are symmetric, but they talk through the mailbox rather than over a
network to each other.

The HTML comment under the screenshot calling it stale and side-by-side is
removed. It contradicted both the image itself and the PLAN's record of it,
which is the same one-fact-one-owner rule the console lives by.

### SENT had its own table, and that is how two views disagreed

Review caught that the ruling had only reached MESSAGES. SENT still drew from
`SENT_BADGES`, so ONE message read `✓` in one view and `R` in the other — two
answers to one question, which is the defect the whole obligation vocabulary
exists to prevent, reproduced inside the fix for it.

Both panes call `_status_glyph` now. `list_sent` rows are shaped differently —
`row_kind`, and no `direction`, because everything there is outbound by
definition — so they are NORMALISED at the boundary rather than teaching the
glyph function a second row shape.

`SENT_BADGES` keeps only `expired` and `quarantined`: the four states a human
has an obligation about are answered by the shared function, and what remains
are the states that are their own answer. An AUTHORED notice keeps `N`,
because `!`/`✓` say whether I have seen someone ELSE's broadcast and neither
is a fact about one I published.

`test_the_two_views_never_disagree_about_one_row` sweeps every outbound state
and compares what each view DRAWS, not what a helper returns.

| deliberate break | what failed |
|---|---|
| SENT gets its own badge table back | the two-views pin |

### The SENT DETAIL heading, and a regression I caused

Review rejected the candidate, correctly. The SENT LIST was unified and its
DETAIL was not: `_sent_row_lines` still called the old badge helper, and
because the same change that fixed the list removed the ordinary states from
that table, opening any normal sent message drew `?`.

That is a regression I introduced while fixing the thing above it, and my own
two-view test did not catch it because it compares LIST rows. The packaged PTY
switched to SENT without opening anything, so it missed it too. Both gaps were
named in the review before I saw them.

The regression was written FIRST and shown to fail against the shipped source,
per the gate: four parametrized cases over pending, claimed, completed and
closed, asserting the heading and that no `?`, `R ` or `C ` survives, plus that
the exact `State:` prose below it is untouched.

`sent_status_glyph` is now the one place an outbound row's glyph is decided,
for the list and the heading alike. `sent_badge` is RENAMED to
`exceptional_badge`: while it was named for a view it kept being reached for
as that view's status machine, which is how two views came to disagree in the
first place. It answers expiry, quarantine and the authored notice — the
states that are their own answer — and nothing a human has an obligation
about.

The packaged PTY now OPENS a SENT row, two of them, and asserts no `?` in the
heading.

| deliberate break | what failed |
|---|---|
| the heading calls the old helper again | three of the four heading cases, and the PTY |

The reviewer also asked me to remove a duplicated consecutive
`target = row.get("to_participant") or ""` in `_sent_pane`. There is only one
occurrence in the current source; it is not present to remove, and saying so
is better than reporting a deletion that did not happen.

### The `?` heading was real in the source and unreachable in the console

Review rejected the packaged proof twice, both times correctly. The first
version replayed the whole transcript AFTER returning to MESSAGES, so its
matches could come from the list; it passed against a zipapp whose SENT detail
still drew `?`. The obvious repair — per-step replay — is unreliable here,
because the harness can miss part of the startup paint and a cumulative replay
of the first steps has holes.

Chasing it properly produced the finding: **`_sent_row_lines` cannot be
reached in the packaged console.** `preview` runs only while nothing is open
(`state.detail is None or "preview" in state.detail`), and selecting a row
always opens it, so from `o` onwards the SENT pane shows the opened copy.
Sitting through several poll cycles in SENT produced the opened copy every
time.

So the `?` defect was real IN THE SOURCE and invisible to a user. The fix
stands — a render path that draws `?` for every ordinary row is wrong whether
or not anything reaches it today — but no packaged PTY test can distinguish
the builds, and I will not manufacture one that appears to.

The packaged test asserts what the console actually shows: the SENT LIST
carrying `✓` and `▷` with no `?`, `R` or `C`. The heading is pinned at source
level by four parametrized cases, which is the only honest place for it.

That leaves a question for review rather than for me: `_sent_row_lines` is
dead for a non-empty sent list. Dead render code that looks load-bearing is
its own defect, and deleting it is a behaviour decision, not a tidy-up.

### Consolidated gate — release candidate

    fresh-cache full suite      1882 passed
    git diff --check            clean
    packaging + core boundary   50 passed
    bin/baton-tui, two builds   3ef94453c3d7f64827f02b837413a33dce3960d447df3cdcf46aa94e8792b292
                                identical both times — deterministic
    DISTRIBUTION-TUI.json       matches that build
    bin/baton                   a23461ae7577422f5c4ade86eae370926b2dc41bc93ecd7732c29b2785374566
                                BYTE-IDENTICAL to its pin
    packaged PTY + boundary     on the rebuilt artifact

One flake surfaced and was fixed rather than re-run until green: the packaged
SENT test raced the redraw after the view switch, and used bare `next(...)`
so it failed with `StopIteration` instead of saying what was missing. It has a
generous settle and explicit assertions now, and matches on the leading word
of a subject because `_replay` leaves the tail of a longer earlier write when
a shorter one overwrites it — `Waiting outbound` can appear on the grid as
`Waitingd outbound`. The glyph column, which is what the test is about, is
unaffected by that.
