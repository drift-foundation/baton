# Human console — implementation plan and sequencing

The NORMATIVE contract is `FINDING.md`. This file records how it is being
built, in what order, and which choices were made where more than one was
defensible. `TRIAL.md` records what actually happened, including defects found
and the deliberate-break checks.

Baton traffic is coordination only. If these three files and the code
disagree with a mailbox message, these files win.

## Stage sequencing (Slawomir's ordering, three separate commits)

1. **This stage.** Protocol 9, `baton_core` + `baton_tui`, with the released
   CLI source, artifact, builder and distribution byte-frozen. Reviewed, then
   committed.
2. **CLI-to-core adoption.** Only after that commit, on a NEW branch in a new
   work folder. Still protocol 9, no behaviour change, parity proven against
   the frozen oracle, landed separately.
3. **Protocol 10.** Only after adoption lands, and it is now an UMBRELLA
   rather than a single rename: `part_name`, general multipart/references
   authoring, append-only claim progress with `working`/`blocked`, message
   priority and its queue-order consequences, durable per-participant
   dismissal, and scoped/multi-recipient audiences. One boundary on purpose --
   the inventory is finished before the bump so cutover is not immediately
   followed by needing protocol 11. See
   `work/finding-protocol-10-umbrella/FINDING.md`.

Why this order, recorded because it was contested: `filename` lives in the
SCHEMA TEXT, which exists in two copies today (the frozen oracle `baton_v6.py`
and `baton_core/_impl.py`). Renaming it means either duplicating a breaking
change across two implementations, which is ruled out, or changing the
hash-pinned oracle. Stage 2 removes the duplication so stage 3 writes the
rename once. Adoption is also the LAST honest use of the differential parity
harness: once the core speaks protocol 10 and the CLI speaks 9 they are
supposed to disagree, and every divergence would have to be allowlisted until
the allowlist is the test.

## Architecture, and why

- **Pure state model, pure renderer, thin curses driver.** The whole screen is
  assertable as data, which is what makes ~1500 tests possible without a
  terminal. The only part needing a real terminal is the loop, and it is the
  only part excluded from coverage.
- **`render` is observation-only.** Resize is an explicit `layout_for` +
  `set_viewport` from the driver. Drawing the same model at a different size
  must not move the model.
- **All widths are DISPLAY CELLS, never characters.** Character arithmetic
  pushed the divider off its column on any row containing a wide glyph, back
  when the divider had a column. The rule outlived the layout: it is now what
  keeps a wide subject from pushing a list row past the terminal edge.
- **The 40/60 split divides HEIGHT, in one helper.** Stacked, both panes are
  the full terminal width, so there is no pane-width helper at all — a
  leftover one would be a second authority still describing columns, and
  something would eventually ask it. Pinned structurally.
- **Footer height is read from one helper** by everything that divides the
  screen. A footer that changes height while the body arithmetic does not is
  how a row goes missing or gets drawn twice.
- **Actions bind to the OPENED item, never the cursor.** Bound to the cursor,
  a reply typed while reading one message was delivered to a different sender.

## Choices where more than one answer was defensible

- **Picker capacity is MEASURED, not estimated.** Entries are laid out for
  real and counted until the pane fills, from the same helper that draws them.
  A fixed reserve offered letters it could not draw. The blank separator rows
  were removed because at 40x8 they were the difference between drawing one
  recipient with its page footer and drawing a letter nobody could read.
- **Read-only content elides an oversized token; editable text never does.**
  Hiding characters someone is typing is a worse fault than hiding characters
  they are reading. Picker addresses are exempt too: two accounts differing
  only in their tail would render identically.
- **The part-header mark is recorded by the code that DRAWS the row**, never
  found by searching the text. A sender can put the marker glyph at the start
  of a line and would otherwise paint a fake selection.
- **SENT ordering is pinned as a total order**, not against `scan`. See
  FINDING §3.
- **`subprocess` is allowed in `editor.py` only.** The packaging guard that
  banned it outright was narrowed to its real intent -- no module may run the
  baton CLI -- rather than deleted. Verified in both directions.
- **The recipient picker is MODAL and owns the body.** It replaced the detail
  pane when the detail pane was the full body height. Stacked it is 60% of it,
  and at 40x8 that cannot hold a prompt, one recipient and the page footer --
  so a picker confined to it would offer a letter it could not draw, which is
  exactly the fault measured capacity exists to prevent. Choosing a recipient
  is also not a moment when the list behind the choice is being read. Verified
  by putting it back: two sizes fail immediately.
- **Presentation order is the console's; delivery order is the protocol's.**
  MESSAGES is newest-first by `(created_ts, id)` descending while `claim` and
  `wait` stay FIFO. The core returns the ascending total order as a stable
  base and says so; which end goes at the top is the consumer's decision. The
  two must remain exact reverses, which is what the tie-break agreement buys.
- **Anything that compares "which came first" uses the total order, never a
  list position.** Position meant "older" only while the list was
  oldest-first; the same-sender warning read `rows[:cursor]` and would have
  inverted itself silently, in the direction that never warns when it should.
- **The cursor follows the ROW, not the index.** Newest-first inserts
  arrivals at the top, so every existing row shifts down. This is the
  wrong-target bug arriving through the poll rather than through a keystroke,
  and it is preserved by identity in MESSAGES and in the Sent filter.
- **A thread sorts by its NEWEST member, not by its root.** Answering an old
  message has to bring the conversation back up; by the root's timestamp the
  reply you just sent would be near the bottom, which is the failure unified
  MESSAGES was built to fix. Within a thread the order flips to oldest-first,
  because an indented child that precedes its parent is not a child.
- **The reply indent lives in the SUBJECT column only.** Indenting the whole
  row would move the date and party columns on reply rows alone, and every
  list row lining up is a property pinned one round earlier.
- **Part selection follows the pane; reading does not.** `[`/`]` scroll the
  newly marked header into view, because a 60% pane puts the later parts of a
  multipart message below the fold and a mark nobody can see is not a cursor.
  Only on the keystroke that MOVED it: doing it on every redraw would take a
  reader's `J`/`K` position away from them. Both directions are pinned --
  following only the line after the header fixed the downward case and broke
  the upward one.

## Test conventions that are part of the contract

- **Every fix is verified by removing it** and watching its pin fail. Three
  faults were caught this way that green tests had missed: a part-mark that
  marked every leaf, an ellipsis pin satisfied by the inbox column's own
  ellipsis, and footer pins anchored to the constant that produced them.
- **Literals specified by a human are pinned BY VALUE in the test**, not
  imported from the constant under test.
- **Tests never call private methods.** An AST guard enforces it: a test that
  supplies behaviour the model lacks is testing itself.
- **The documents are pinned too.** `test_docs_consistency.py` asserts that
  no file here presents a superseded rule as current, that no cross-reference
  points at a removed section, and that a decision is never recorded as both
  open and closed. Review found FINDING ruling that no automatic prefix is
  added, in one section, while its key map still described `r` as editing a
  prefixed subject line -- a stale key map is a specification of the
  superseded behaviour sitting beside the rule that superseded it, with
  nothing to say which wins.

  (This paragraph originally quoted the prefix literally and tripped its own
  check. Rewording it was the right fix: widening the rule to allow the
  literal here would have widened it everywhere.)
  The check is STRUCTURAL, not a phrase list: a phrase list would have to be
  extended every time the prose was reworded, making it a test of the wording
  rather than of the property.
- **The checked document set is NAMED, not globbed.** `materialize` projects
  mailbox messages into the finding folder, so a `*.md` glob swept them into
  the consistency checks: the suite's test count moved by two per projection
  with no code change, and the checks were wrong for those files anyway --
  a projection is a byte-exact copy of an immutable message, so a rule it
  presents as current cannot be corrected in place. The store is the authority
  for projections; FINDING, PLAN and TRIAL are the record this file is about.
- **Model assertions are not screen assertions.** Notices rendered
  `(no retained bytes)` for their entire life while a test asserted the model
  held the right bytes. If a property is about what the human sees, assert on
  the rendered screen.

## Ledger

**This section is the restart-safe operational state.** The normative
contracts live in `FINDING.md` and the chronological evidence in `TRIAL.md`;
this is what is where, and what is owed.

States, used strictly:

| State | Means |
|---|---|
| `done/pinned` | implemented AND covered by regressions that fail when the fix is removed |
| `in progress` | started, not yet pinned |
| `ruled/pending` | decided by Slawomir, not yet implemented |
| `user trial` | needs Slawomir at a real terminal; no agent can close it |
| `deferred` | protocol 10, deliberately not started |

**Reviewer approval is separate from `done/pinned` and is not recorded here.**
A Baton request never moves an item on its own: the evidence does.

### Console behaviour

| Item | State |
|---|---|
| Send confirmation, one-row bracketed literal | done/pinned |
| Subject-only shorthand, directed and notice | done/pinned |
| INBOX / Sent filter, badges, read-only boundary | done/pinned |
| Reply to a notice as a new directed message | done/pinned |
| External editor: config, argv safety, temp file | done/pinned |
| Notice body actually rendering | done/pinned |
| No-inline-body model (FINDING §5) | done/pinned |
| MESSAGES unified activity (FINDING §3b) | done/pinned |
| Subject caret editing (R5) | done/pinned |
| Stacked layout (R7) | done/pinned |
| One list-viewport authority (R1) | done/pinned |
| History view removed (R2) | done/pinned |
| Outbound `[Q]`/`[P]` lifecycle in MESSAGES (R3) | done/pinned |
| MESSAGES newest-first, by total order (C3, ruled) | done/pinned |
| Reply thread grouping and indent (ruled) | done/pinned |
| Reply indent capped at three levels, `…↪` past it (ruled) | done/pinned |
| External LICENSE leaf unreachable — live trial R10 | done/pinned |
| `r`/`R` reply pair and `Ctrl+r` refresh (ruled; pair later REVERSED) | done/pinned |
| Subject-mode `Ctrl+u` kill-left (ruled) | done/pinned |
| `?` modal shortcut help (ruled) | done/pinned |
| Follow-ups: answered rows are never a dead end (ruled) | done/pinned |
| Follow-up messages carry `kind=follow_up` (ruled) | done/pinned |
| Follow-up relation presented as "in reference to" (ruled) | done/pinned |
| Post-send routing: an outbound row previewed as a delivery (trial) | done/pinned |
| Seen notices retained in MESSAGES as history (trial) | done/pinned |
| Retained seen notice badge is `[✓]`, `[S]` fallback (ruled) | done/pinned |
| Sent `[N]` is a row kind, not a receipt state (ruled) | done/pinned |

Each of the ruled items above carries its regressions and its
deliberate-break table in `TRIAL.md`, under the round that landed it.

### Review outcome — CURRENT

**The consolidated gate has not run on the release candidate.** The terminal
trial happened and produced a further run of rulings — obligation glyphs, the
`r`/`R` swap, the root-picker attachment workflow, key notation — each
reviewed and corrected since. What remains before the candidate can be handed
to Slawomir:

1. the reviewer authorises the consolidated gate;
2. one fresh-cache full suite, distribution and frozen-CLI checks, a
   deterministic `bin/baton-tui` rebuild and the packaged PTY flow;
3. the handoff names which build the hash belongs to.

Delivered behaviour is the ZIPAPP. Slawomir trials `bin/baton-tui`, so a
source tree that passes is not a candidate until it is built, and any artifact
older than the latest correction must not be put in front of him as though it
were.

The screenshot is done; he captured it himself after the trial.

#### Historical — the pre-trial approval

Approved for human trial on an independently verified snapshot: 1661 passed,
`git diff --check` clean, `bin/baton-tui`
`c7a721341c69bc7dc86495716c78bbb4c52e499d98d62683d50c92b81122235d` reproduced
byte-identically by a temp rebuild, frozen `bin/baton`
`a23461ae7577422f5c4ade86eae370926b2dc41bc93ecd7732c29b2785374566`, protocol 9
unchanged. Every review finding open AT THAT POINT was closed.

That artifact is long superseded and is recorded here as the state the trial
began from, not as an approval of anything shippable now. No agent staged or
committed anything, then or since.

### Announcements

**The implementer does not announce readiness.** After reviewer approval,
`baton.reviewer` publishes the readiness notice to Slawomir. Recorded because
I got it wrong: Slawomir had asked for a notice "when the TUI is ready for
human testing", and I sent one while two ledger items were still open — the
condition was false, so the notice was premature even though it named those
two items itself.

I then expired it, which was a second mistake: review had already told
Slawomir to disregard it, and ruled afterwards that it should stay live as an
honest intermediate status. `expire` is terminal, so that ruling cannot be
carried out. The information survives as DIRECTED durable traffic in the
consolidated status message instead, which does not depend on a broadcast
landing. Recorded because the lesson is the smaller one: when a correction
arrives, apply the correction — do not invent a remedy on top of it.

### Reopened: trial slice — Tab pane focus

| Item | State |
|---|---|
| Tab toggles focus between LIST and DETAIL (ruled) | done/pinned |
| Vim navigation routed through focus (ruled) | done/pinned |
| Uppercase `J`/`K` detail scroll SUPERSEDED and removed (ruled) | done/pinned |
| `> MESSAGES`/`> SENT` and `> DETAIL` ASCII focus labels (ruled) | done/pinned |
| Context-sensitive action legend (ruled) | done/pinned |
| ONE affordance source driving dispatch AND the legend (ruled) | done/pinned |
| `h`/`l` scroll DETAIL sideways; `[`/`]` own parts (ruled) | done/pinned |

Focus is pure UI state: no claim, receipt, disposition, publication,
transition, core read or filesystem write, and it preserves the selected row,
action target, both offsets, selected part, draft and status. `i`/`o` return
focus to the list. `h`/`l` and `[`/`]` are explicitly NOT broadened in this
slice.

The focus value is LIST, not literally MESSAGES: the top marker follows the
ACTIVE list label, so it reads `> MESSAGES` in the primary view and `> SENT`
in the Sent filter. Only the named navigation keys route through focus —
Enter, `r`, `R`, `c`, `h`, `l`, `v`, `m` keep their existing semantics, and
focus is NOT a new action target: the selected/opened item remains the target
model. The detail label interrupts the edge-to-edge rule, which this ruling
supersedes so focus is visible.

### Reopened by the live trial — a second UX round

| Item | State |
|---|---|
| Poll dies after Vim / after Esc (tool bug) | done/pinned |
| Claim-and-open on highlight (MAJOR supersession) | done/pinned |
| Information ownership: one owner per fact | done/pinned |
| Header cleanup: drop the redundant `baton` label | done/pinned |
| List cleanup: one-cell status glyphs, no brackets | done/pinned |
| Detail cleanup: no tutorial/action hints in the body pane | done/pinned |
| Compose: remove the `new message (...)` heading line entirely | done/pinned |
| Detail cleanup: badge glossary moves to help and README | done/pinned |
| Compose cleanup: no background claim prompt, no duplicate hints | done/pinned |
| R5 clarification: modal affordances gate dispatch too | done/pinned |
| Ordinary footer removed; one status row (supersedes the legend) | done/pinned |
| Passive poll no longer writes mailbox state to status | done/pinned |
| Batch 2: chrome stays fixed while body content pans | done/pinned |
| Batch 2: content marking reaches every detail shape (R1) | done/pinned |
| Batch 2: a fresh `R` that gives nothing back restores the original | done/pinned |
| Batch 2: an unchanged successful editor is no edit (R2) | done/pinned |

**Claim-and-open on highlight reverses this console's founding rule** that
selection is always observational — FINDING's OBSERVE/COMMIT split. Slawomir
accepted the tradeoff explicitly and the consequence is stated in the ruling:
moving across pending directed rows may leave several unresolved claims, and
none may ever be auto-closed. Notices are NOT included; polling stays
observational; selection resolves by identity so a reordering poll can never
claim a different row.

### Not code, and not closable from here

| Item | State |
|---|---|
| Fresh README screenshot (`assets/artwork/baton-tui.png`) | done — Slawomir captured it after the trial |
| Trial: a successful send returns focus to the LIST | done/pinned |
| Trial: an empty body row advertises `Ctrl+e to edit` | done/pinned |
| Trial: attachments choose a root, then a relative path | done/pinned |
| Trial: glyphs answer what the reader owes | done/pinned |
| Trial: `r` opens the editor, `R` is the quick subject | done/pinned |
| Trial: Ctrl chords lower-case, case implies Shift | done/pinned |
| Staging and the commit | Slawomir's alone |

The screenshot is CURRENT. Slawomir captured it from his own terminal after
the trial, and it shows the stacked layout, the one-cell obligation glyphs,
threaded replies and the single status row. The README no longer carries the
stale-image warning, because there is nothing stale about it.

(It was stale in three ways — side-by-side columns, oldest-first order, flat
replies — and no agent could close it, because the capture had to come from a
real terminal. That is the record of why it stayed open, not a current
warning.)

The tree is prepared and verified; `git diff --check` is clean, the full suite
passes, and the frozen CLI artifact, manifest, oracle and builder are
byte-identical. Staging, the commit and its message are Slawomir's.

### Deferred to protocol 10

| Item | State |
|---|---|
| `x` per-participant dismissal via an authority row (FINDING §11) | deferred |
| CLI adoption of `baton_core` | deferred (stage 2) |
| `filename` → `part_name` | deferred |
| General multipart / references authoring | deferred |
| Append-only claim progress; blocked progress and priority | deferred |
| Scoped and multi-recipient audiences | deferred |

Nothing from the umbrella is started, by instruction. The inventory is in
`work/finding-protocol-10-umbrella/FINDING.md`, deliberately being finished
before the bump so cutover is not immediately followed by needing protocol 11.

## Verification state, for recovery after a crash

    just test          recorded with the round, in TRIAL.md
    git diff --check   clean
    bin/baton          a23461ae7577422f5c4ade86eae370926b2dc41bc93ecd7732c29b2785374566
                       (frozen, with DISTRIBUTION.json, baton_v6.py, build_zipapp.py)

The current TUI artifact hash and test count are recorded with the round that
produced them in `TRIAL.md`, rather than duplicated here where they would go
stale the moment a round lands. `bin/baton-tui` is deterministic: rebuilding
twice produces identical bytes.

The README quick example is executed end to end against a temporary instance
each round, and `doctor` reports it clean.

## Resolved decisions that were escalated

1. **Reply subject — RULED and closed.** The original subject is copied
   exactly; no `Re:` is ever added. Supersedes the single-prefix rule that was
   implemented first. One function, `InboxState.reply_subject`.
2. **Reply act — RULED and closed.** Both reply keys — `r` into the editor
   and `R` for the quick subject — are claim-completing dispositions on a
   directed message; on a notice either is a new directed send. Both paths and
   both kinds are pinned by table counts and by claim state, and the choice is
   driven by what is OPEN rather than by the cursor. (`e` was the editor key
   when this was ruled and is unbound now; see the key map.)

## Key map

| Key | Action |
|---|---|
| `r` | reply or follow-up — starts it AND opens the external editor, in one action |
| `R` | the quick one — edits a copy of the original subject, unprefixed, which becomes the content |
| `Ctrl+r` | manual refresh; the two-second poll is unchanged |
| `Ctrl+u` | typing modes: kill to the start of the line (browse: page up) |
| `Ctrl+e` | body editor from within a typing mode |
| `v` | read an external part's file into the detail pane |
| `?` | the modal shortcut list; `?`/`q`/Esc closes it |

Ruled by Slawomir from the terminal trial. The reply people actually write is
a body in their editor and the subject-only one is rare, so the EASIER key
serves the common action: lowercase `r` opens the editor, shifted `R` is the
quick subject line. This REVERSES an earlier pairing, and the earlier reasoning
— that shifted `r` should be the bigger act — is superseded by watching the
console in use.

The browse `e` binding is REMOVED rather than kept as an undiscoverable alias.
Manual refresh is `Ctrl+r` because `g` is the `gg` prefix and both plain-letter
`r` spellings are reply keys.

Inside the quick-reply subject editor every browse letter is ordinary text:
the text modes are a separate key table, so no special case is needed. One was
written and then deleted, because removing it changed no test -- which is the
definition of dead code that looks load-bearing.
