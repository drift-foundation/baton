# Progress

**Implemented by `baton.claude` and returned to `baton.bug` for independent
review on 2026-08-18.** Presentation only: no authority, projection or schema
change.

## Revalidation

The defect reproduces exactly as recorded. `_render_table` built
`"↳ " + title`, appended `f" ▸{n}"`, and only then cut the combined string to
the Title column — so the disclosure was the first thing a long title removed.

One correction to how I first read the evidence, worth stating because it
shaped the fixture: W5 must have been a CONTAINMENT CHILD, not a root. A
root's children paint inline beneath it, so a root has nothing hidden to
disclose and the cue is only ever drawn on a depth-1 row whose own children
sit outside the two-level window. My first fixture made W5 a root and proved
nothing; it now reproduces the real shape — root → W5 (long title, one child)
→ W6 (outside the window).

## What changed

`_title_cell(row, title_width)` lays out the Title column as reserved
STRUCTURE and then the truncatable title: `↳ ` for a containment child, `▸N `
for hidden deeper Work, and the title takes whatever room is left. Width,
title length, selection, filters and the other columns can now shorten the
TITLE and never the fact that something is beneath the row.

Both paints go through it. W81's actionable bold repaints the Title cell a
second time, and that repaint now draws the same cell — otherwise the row that
most wants attention would be the one that lost its disclosure.

Handler is untouched: a parent's Handler stays blank unless that parent is
itself claimed, because the cue says deeper Work exists rather than that this
row is being worked on.

## The cue's CONDITION — settled with W155

**This section replaces what it said before, which is now false.** When this
Work first landed, the cue fired for "a containment child with a non-zero
child count", and I recorded the follow-up it needed: that rule equals "has
children not visible in this window" only while the window is two levels deep,
so the three-level design in `finding-tui-three-level-work-tree/` would have to
change it to "has children outside the painted set". I deliberately left it,
because this Work's ruling is about where the symbols live and that they cannot
be truncated; changing the visibility rule in the same diff would have mixed two
decisions.

W155 has since landed and done exactly that. The projection now publishes
`deeper` — this row contains Work THIS window does not show — and
`_title_cell` reads it. So a depth-1 row whose children are painted beneath it
carries no cue, and only a row with genuinely hidden Work does.

Two consequences worth stating, because a reviewer seeing one Work without the
other would get a false picture:

- **The two Works must be read against the same tree.** They share
  `_title_cell` and the `deeper` field. On a checkout with W154 but not W155
  the cue fires on rows whose children are visible; with W155 but not W154 it
  can be truncated away. Neither is the intended behaviour, and both suites are
  run together below for that reason.
- **W154's fixtures moved down a level.** The guarantee is unchanged — wherever
  the disclosure appears, a long title must not delete it — but the row that
  CARRIES it is now the deepest visible one, so the long title sits at depth 2.
  A fixture that left it at depth 1 would assert nothing at all.

## Regressions

`tests/work/test_w154_deeper_child_cue.py` (76 tests):

- the cue survives every Title width from 6 to 60 — far below anything the
  table will actually offer, because the guarantee is structural rather than a
  consequence of roomy columns;
- a long title loses text and never the cue, with the surviving text proved to
  be a prefix of the real title;
- a leaf child carries no cue; a root carries neither symbol;
- the count is the canonical progress total and follows it when a second child
  is added; a three-digit count still leaves the cue visible at width 14;
- claimed deeper Work does not lend its Handler upward, checked in the live
  shape with the hidden Work proved absent from the window; a row that IS
  claimed still names its claimant;
- the drawn row keeps the cue at eight widths from 110 down to 44;
- the live W5/W6 shape reproduces and is fixed, with the deeper Work proved
  not to paint at this level;
- selection and a filtered view keep it, and so does the actionable bold
  repaint;
- and two PTY tests: the cue survives a wide→narrow resize on a real
  terminal, and it PRECEDES the title there rather than trailing it.

## Break-sweeps

| Reintroduced defect | Result |
| --- | --- |
| The original trailing `▸N` after the whole title | 72 red |
| The bold repaint drawing the raw title again | 1 red |

The second sweep first came back GREEN. The bold repaint only runs for
actionable Work, and every row in the fixture was `block` — gated by the very
child the cue discloses — so the second paint never happened. The case IS
reachable, because `progress.children` counts closed children too: a row whose
deeper Work is closed still discloses it (`u` still reaches it) while the row
itself is ungated, ready and therefore actionable. That test now exists and the
sweep reds.

## Superseded expectations

- `test_w71_navigation.py` — `↳ the child ▸1` becomes `↳ ▸1 the child`. W71's
  contract required a VISIBLE disclosure, which is what this Work restores;
  only the position changed.
- `test_parity.py` — the row parser reads both symbols off the front of the
  Title cell. That it now has to is the point.

## Gate

Composed with W155, as the review requires — neither Work can be judged against
a different tree depth from the other:

`tests/work/test_w154_deeper_child_cue.py` + `test_w155_three_level_tree.py`:
**99 passed** on one checkout.

`just test-v11`: **1569 passed**, serial **36 passed**, ACP **41/41**, Codex
bridge **44/44** — fully green.

### Earlier in this Work

`just test-v11` was **1445 passed, 1 failed** when this Work first returned.

That failure was
`test_w20_infrastructure_lifecycle.py::test_start_refuses_a_service_log_symlink_without_touching_its_target`
— W20's own containment regression, not this Work — and it has since been fixed
under W20.

## Review round — the cue's condition (2026-08-18)

Both findings are resolved. Neither needed new work here, but both needed
checking rather than asserting, and one exposed a stale claim in this very
file.

**P1 — the cue must read the hidden/deeper fact, not a child count.** Correct,
and already true: W155 landed the `deeper` projection field and `_title_cell`
reads it, so a depth-1 row whose children are painted beneath it carries no
cue. The review was written while W155 was still in flight, which is exactly
the composition risk it names.

It is now pinned rather than merely working. Three tests: a row with visible
children carries nothing while a row with hidden Work carries the icon; the
same row differing ONLY in `deeper` produces the icon or not; and the TUI reads
the condition from the projection rather than re-deriving it from depth — a
client computing it itself would get the filtered and re-rooted cases wrong,
because `deeper` is a fact about which rows a call returned and only the
projection knows that. Break-sweeps: reading the child count again reds 8
across the two suites, re-deriving the cap from `depth == 2` reds 3.

**P2 — the progress file.** It exists and did at review time (written 16:32Z,
four minutes before the review). Recording that as a fact rather than an
argument; if the reviewer read a cached tree, the file they wanted is the one
above.

**What the review's P1 did catch here.** This file claimed the cue's condition
was "unchanged (depth > 0 with a non-zero canonical child count)" and carried a
section describing the `deeper` rule as future work for the companion Work.
W155 had since done it, so both statements were false — the exact stale-prose
failure I have been correcting in other people's surfaces. Replaced with what
is true, including the two consequences a reviewer needs: the Works share
`_title_cell` and `deeper` and must be read against one tree, and W154's
fixtures moved to depth 2 because that is where the cue now lives.

**Composed gate, as the review requires.** W154 + W155 together on one
checkout: **102 passed**. `just test-v11`: **1573 passed**, serial **36**, ACP
**41/41**.
