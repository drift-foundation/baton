# Progress

**Implemented by `baton.claude` and returned to `baton.feat` for independent
review on 2026-08-18.** No SQLite schema change; projection 10.1 (additive).

## Revalidation

The two-level cap was in `projection.tree()`, which appended each base and its
depth-1 children and stopped. The TUI consumed that window without a cap of its
own, so moving the cap in one place moves it for JSON and the TUI together —
which is the property this Work needs and the reason the cap stays there.

## What changed

**The window.** `tree()` now walks root → child → grandchild. The sibling
order (priority, then permanent creation sequence) applies inside each group at
every level without a group leaving its parent.

**The disclosure.** Each row carries `deeper`: this row contains Work that THIS
window does not show. It is computed against the rows actually returned, not
from a depth number, which matters for two reasons — it stays correct if the cap
ever moves again, and it covers the case W154's ruling names explicitly, where
a FILTER removed a row's children. That ruling forbids a filter silently
removing the fact that a visible Work has hidden children, so the disclosure has
to be a fact about the window rather than about depth.

Deciding it last, after filtering, is the whole point; a break-sweep that moves
it before the filter reds the filter test.

**The TUI.** Indentation is per level — two cells each, then the `↳` that marks
containment — and the more-levels icon rides the same reserved structural space
W154 established, so no title length, width, selection or filter can delete it.
The icon keeps W154's child count; a count is not the Handler, Phase or message
aggregation the ruling forbids.

**The filter rule.** W5's containment rule generalized from two levels to
three: a row is kept when it matches or when a descendant inside the window
matches, in which case it is structural context (`filter_match: false`). One
backward pass keeps each kept row's nearest shallower ancestor, which then
keeps its own — so context reaches the root without a per-level scan. Filtering
still never promotes a row, changes a depth, or reorders siblings.

## Two judgements worth the reviewer's attention

**Projection 10.1, not 11.0.** Nothing was renamed and no field changed
meaning: `deeper` is new, and `depth` gained the value 2 without any existing
value changing, so no reader silently loses data. A client that indents by
depth is fine; one written as "0 is a root, anything else is a child" will draw
a grandchild at the child's indent — a mis-render, not a misread. A major bump
would also refuse the readiness and role-instruction contracts that W101's
review deliberately bounded at projection 10, for a change that costs those
consumers nothing. The reasoning is in `jsonapi.py` beside the constant so the
call is reviewable rather than implicit.

**W154's tests moved down a level.** W154's guarantee is unchanged — wherever
the disclosure appears, a long title must not delete it — but W155 changed WHICH
row carries it, because a grandchild is now visible rather than hidden. Its
fixture therefore puts the long title at depth 2, where the cue now lives; a
fixture that left it at depth 1 would have asserted nothing. This is the
follow-up I flagged in W154's own record rather than a change of mind, and W154
is still in review with `baton.bug` — its reviewer should know the level moved.

## Regressions

`tests/work/test_w155_three_level_tree.py` (26 tests): a three-level chain
paints whole with nothing claiming to be hidden; the fourth level never paints
and its ancestor discloses it; six levels deep gives the same answer as four; a
leaf root paints alone; siblings order identically at every level without
leaving their parent; a dependency edge does not masquerade as containment
(depth untouched, blocker keeps its own place, `Wait` carries the edge); a
filter that hides children still discloses them; a matching descendant keeps its
whole ancestry at its own depth with `filter_match` false above it; a group with
no match disappears whole; re-rooting reveals the next three levels and
discloses what is below; a re-rooted leaf is a window of one; three levels are
unambiguously indented and survive eight widths from 110 to 44; a long
third-level title keeps its icon at five widths; closed-row collapse still names
what it hides; the deepest visible row borrows no Handler from below; and two
PTY tests covering paint, `u`, breadcrumb, Esc and a wide→narrow resize.

`test_the_window_reads_do_not_grow_with_the_tree` is the one I had to write
twice. My first version counted every statement and failed, because
`_row_view` legitimately costs a fixed number of reads per row and that total
grows with any tree — it was measuring the wrong thing and would have "proved"
a regression that is not one. It now counts only the window's OWN statements,
matched precisely, and pins them: three for a two-level tree, unchanged after
twenty more grandchildren, and exactly one more for a second depth-1 row.

## Break-sweeps

| Reintroduced defect | Result |
| --- | --- |
| Back to two levels | 20 red |
| The fourth level paints | 17 red |
| `deeper` decided before the filter | 1 red |
| Flat indentation at every depth | 55 red (with W154) |
| The more-levels icon dropped | 14 red |

## Superseded expectations

`test_w71_navigation.py::test_the_tree_is_two_levels_with_disclosure` becomes
`..._three_levels_...`: W71's contract required a visible disclosure and a
bounded window, and both survive — only the cap moved, which is exactly what
this Work supersedes. The renamed test also asserts the new fact that a depth-1
row discloses NOTHING, because its children are now inside the window.

## Gate

`just test-v11`: **1466 passed, 1 failed**; serial lane 36 passed.

The one failure is
`test_w20_infrastructure_lifecycle.py::test_start_refuses_a_service_log_symlink_without_touching_its_target`.
Not this Work: `tools/infra.py` and that test file are both UNTRACKED — W20
work in flight by the `baton.tune` participant in this shared checkout — and
neither mentions the tree, containment or the projection.

## Review round — batching, the major, parity and the live docs (2026-08-18)

All four findings accepted. Two of them corrected judgements I had argued for
explicitly, which is worth recording rather than quietly fixing.

### P1 — batch the level reads

Correct. `children_of` ran once per visible depth-1 row, so the third level
added one statement per child on every two-second refresh. Each level is now
ONE ordered statement grouped by parent in memory: three levels, two
statements, plus the roots query and the batched `deeper` lookup.

**The regression blessed the growth it was named for.** After adding a second
depth-1 row it asserted `small + 1` — contradicting both its own name and its
docstring's claim that the window reads are bounded by the number of levels. A
test that accepts the defect it is named for is worse than no test. It now pins
the constant and grows the tree in all three directions — more roots, more
children, more grandchildren — asserting the count never moves.

### P1 — the projection major

Correct, and it overturns my published judgement. I argued 10.1 on the grounds
that nothing was renamed and that a client written as "0 is a root, anything
else is a child" would merely draw a grandchild at the wrong indent — a
mis-render rather than a misread.

The review answered with a counterexample from this repository:
`test_parity.py::_parse_rows` matched a leading `↳ ` and mapped everything else
to depth 0, so a depth-2 row decoded as a ROOT. That is a consumer silently
reading the wrong containment, not drawing it badly, and this file's own rule
is that every response inside one major is compatible. Adding a value to a
consumed domain breaks that rule whatever the failure is called.

**Projection 11.0**, with the readiness and role-instruction consumers widened
in the SAME candidate: the shared participant-action validator now accepts
7/8/9/10/11 and the role-instruction reader 9/10/11, each with its unsupported
future moved to 12. The note in `jsonapi.py` records the counterexample rather
than the conclusion alone, so the next person weighing "mis-render versus
misread" has the concrete case in front of them.

### P1 — parity through depth 2

The parser is fixed to decode depth from the INDENT rather than a single
prefix, and it now carries `local_id`, which it computed and then discarded —
so nothing could compare the two surfaces row FOR row, only field by field in
an order both happened to agree on.

`test_three_levels_agree_between_json_and_the_tui` builds a
root/child/grandchild/fourth-level chain and compares identity, order, depth
and title prefix between JSON and a real PTY screen, then requires the fourth
level absent from both and disclosed on both.

### P2 — the live contracts

`docs/BATON-WORK.md`, `Console.view()`, the `u` handler, the module docstring,
and the active test descriptions in `test_w71_navigation.py`, `test_tui.py` and
`test_w6_search.py` all described a two-level window. Corrected. Historical
findings under `work/records/` are unchanged, as the review requires.

### Break-sweeps

| Reintroduced defect | Result |
| --- | --- |
| One children query per parent again | 1 red |
| The parity parser maps only a leading marker | 1 red |
| A consumer left behind at projection 10 | 2 red (Codex bridge) |

### Gate

`just test-v11`: **1609 passed**, serial **37 passed**, ACP **41/41**, Codex
bridge **44/44**.
