# Progress

Implementer-owned.

## The mandatory gate ran first, and it did not reproduce

Plan step 1 is explicit, and so is the acceptance boundary: the
implementer records a successful reproduction of the required pause
through a real terminal/PTY, or names the exact input-state transition
that delays an immediate second key — and "failure to reproduce returns
the Work for more evidence; it does not authorize a speculative timing
fix."

**I could not reproduce it, so I have changed nothing.**

The probe is kept at `evidence/chord-probe.py` in this dossier and runs
from the repository root. It builds a throwaway authority, opens Work
detail on a real pty, and reads the focused pane from the `»` marker
the detail view already paints — a TEXT cue, so the answer survives a
replay that keeps no attributes. Every case writes the whole chord in
ONE write, with no pause between the bytes:

```text
ctrl-w j (one write)                 ['Threads', 'Messages', 'Messages']
ctrl-w j then ctrl-w k, one write    ['Threads', 'Threads', 'Threads']
ctrl-w DOWN csi (one write)          ['Threads', 'Messages', 'Messages']
ctrl-w DOWN ss3 (one write)          ['Threads', 'Messages', 'Messages']
ctrl-w j x3 rapid                    ['Threads', 'Messages', 'Messages']
everything in ONE write with open    ['Messages', 'Messages']
```

Each row is the focused pane after each scripted step. Reading them:

- `\x17j` written as one burst moves focus exactly once;
- both cursor-key spellings work inside the chord — `ESC [ B` and
  `ESC O B` — so escape decoding is not eating the second key;
- `\x17j\x17k` ending on `Threads` is CORRECT, not a failure: down to
  the index, then up again;
- `\x17j\x17l\x17h` ends on the index, which is the geometric map
  behaving;
- `\r\x17j` — opening the detail view AND the whole chord in a single
  write — still moves once, which is the fastest input this harness can
  produce.

Two further cases, run separately and also passing: `Ctrl-W`, a 2.6 s
pause (longer than the 2 s refresh deadline), then `j`; and `Ctrl-W`,
120 ms, then `j`. So the refresh cadence does not clear a pending
prefix either — I checked `tick()` and the render path for that
specifically, and neither touches `ctrl_w_pending`.

`Ctrl-W l` from Threads legitimately does nothing: W76's geometric map
puts Threads ABOVE both message panes, so "right" from there is an
unmapped edge and stays put. If that is what felt broken, the finding
is about the MAP rather than about timing, and that is a different
decision.

## What would settle it

I am not asking for the report to be repeated — I am asking for the
things this harness cannot see:

1. the terminal emulator and `TERM`, and whether a multiplexer (tmux,
   screen) or a terminal keyboard protocol (kitty, fixterms) sits
   between the keyboard and the console;
2. whether `Ctrl-W` reaches the console at all in that setup — a
   multiplexer prefix or a terminal binding would swallow it before
   Baton sees anything, which looks exactly like "the chord needs a
   pause" from the outside;
3. the failing SECOND key specifically: `j`/`k` alone, or the arrow
   forms too;
4. whether the same session shows it in Events (a two-pane map) as well
   as Messages (three panes).

An `asciinema` capture, or the raw bytes from `showkey -a` / `cat -v`
while typing the chord, would answer all four at once.

## The other half of the finding

The ruling also adds `Tab`/`Shift-Tab` pane cycling in detail view, and
that decision does not depend on the timing evidence. I have NOT
implemented it either, for one reason worth stating rather than
guessing at:

> "Keep `[` / `]` as the only navigation between top-level and nested
> tabs."

W110 kept `Tab`/`Shift-Tab` as compatibility ALIASES for top-level tab
movement, and its suite pins them. Read strictly, the sentence above
retires those aliases everywhere; read narrowly, it only means Tab is
reassigned inside detail view where panes exist, and the top-level
alias survives because there are no panes there to cycle.

Those two readings produce different products and different tests, and
the difference is exactly the kind of thing this Work's own gate exists
to stop me deciding by preference. So: which is it — does `Tab` stop
moving top-level tabs everywhere, or only inside Work detail?

## Nothing was changed

No product file, no test, and no documentation was edited in this
round. The dossier gained this record and the probe beside it, so the
next implementer starts from evidence rather than from the same
experiment.


## Round 2 — the scope ruling answered both questions

The approver dropped the `Ctrl-W` timing half from this Work and
pinned the answer to the question I returned it with: `[` / `]` are
the EXCLUSIVE tab-switching keys. So the strict reading won, W110's
compatibility aliases are retired, and the remaining deliverable is
the secondary pane gesture.

That is the whole of what I implemented. `Ctrl-W` and its geometric
map are untouched — the evidence above stands as evidence, not as a
diagnosis, and this Work no longer claims to fix or disprove the live
observation.

## What changed

**`Tab`/`Shift-Tab` no longer switch top-level tabs.** One key cannot
mean "next tab" and "next pane" without meaning neither, which is why
the ruling made `[`/`]` exclusive rather than adding a third gesture.

**In Work detail they cycle pane focus**, forward and backward, with
wrap, over the panes that tab actually paints — three in Messages,
two in Events. The Events cycle deliberately has no Threads stop: the
Threads list is a Messages-tab region, and offering a stop that is not
on screen would be worse than offering none.

**Text entry keeps its own Tab.** The command bar, the batch buffer
and the search line all claim every key before this branch is reached,
so completion is still completion. That needed no new code and it is
asserted rather than assumed.

**The footer says `Tab/Ctrl-W panes`** — both gestures in ONE cell,
because the acceptance boundary asks for discoverability without an
extra permanent row. An operator who does not use Vim window commands
now sees that Tab works; one who does needs nothing new.

## Superseded assertions edited

- W110's `test_tab_and_shift_tab_remain_aliases` and
  `test_the_alias_and_the_canonical_key_agree` pinned exactly what
  this ruling retires. The first became
  `test_tab_no_longer_switches_tabs` — same file, opposite assertion,
  with the reason written down; the second is gone, because "the alias
  agrees with the canonical key" has no meaning once there is no alias.
- W25's cycle case asserted the three-tab cycle THROUGH Tab. The cycle
  is what it was always about and is unchanged; it now drives `]`/`[`.
- Six suites walked to a tab with `view.handle(TAB)` in a `while` loop.
  Those became `]`, and four real-terminal scripts that sent `\t` now
  send `]`. Left alone, the first of those loops would have spun
  forever — which is how I found them.

## Verification

- `tests/work/test_w1151_pane_focus.py` — new, **20 passed**: the
  cycle forward, backward, and as inverses; the Events pair; Tab and
  the chord reaching the SAME states, because they are alternatives
  and not two models; the aliases gone; `[`/`]` still switching both
  levels and never moving focus; a pane key never moving a tab;
  command-bar completion, the search entry and the batch buffer
  keeping their Tab; focus movement changing no selection and writing
  nothing; the same logical states at 120, 90, 60 and 40 columns; the
  footer naming both gestures on the row it already had; the guide;
  and a REAL terminal where Tab, Tab, Shift-Tab move the `»` marker to
  three distinct positions and back.

  The pty case reads the marker as a POSITION rather than as the
  heading beside it — at this width the index and the reader share one
  composed row, so the headings do not tell them apart and the
  position does. Asserting on the text would have passed while proving
  less than it claimed.
- The complete v11 gate, `just test-v11`, exits 0 on this tree:
  **2548 passed** (parallel), **40 passed** (serial), both bridge
  suites green.


## Response to the round-2 review

**Accepted: a pane gesture must consume a pending chord.** I put the
Tab branch ahead of the `ctrl_w_pending` branch and left the flag
armed, so `Ctrl-W`, Tab, `j` made that later `j` finish the OLD chord
instead of acting in the pane Tab had just selected. The two gestures
are alternatives; using one cannot leave the other half-entered.

Tab and Shift-Tab now clear the pending prefix before cycling. Vim
answers `Ctrl-W Tab` by cycling windows, which is what this does with
or without the prefix — so the fix is one line and no new rule.

The reviewer's regression passes unedited, and I checked it in the
other direction: removing the clear fails both parametrisations and
nothing else.

- `tests/work/test_w1151_pane_focus.py` — **22 passed** (20 mine, 2
  the reviewer's).
- The complete v11 gate exits 0 after the round: **2558 passed**
  (parallel), **40 passed** (serial), both bridge suites green.
