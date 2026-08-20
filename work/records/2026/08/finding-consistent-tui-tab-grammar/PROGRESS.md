# Progress

Implementer-owned.

## Revalidation against the current tree — 2026-08-19

The finding's diagnosis holds exactly as written. Before this change:

- `top_tab_segments()` bracketed only the ACTIVE top-level label and
  padded the others with spaces, so the bracket meant "selected";
- `_tab_bar()` did the same for Work detail's Messages/Events, so the
  bracket meant "selected" there too — but both tabs were reachable
  with `[`/`]`, which the top level refused to use;
- `handle()` bound `Tab`/`KEY_BTAB` to the top-level cycle with a
  comment explaining that `[`/`]` were deliberately withheld;
- the Teams and Inbox footers advertised `Tab switches tab` while the
  Work-detail footer advertised `[/] tabs`.

Two input modes matter for the ruling and both already behave: the
command bar, the batch buffer and the search entry claim every key at
the top of `handle()`, so a typed `[` was never a navigation key and
still is not. `Ctrl-W` pane movement lives inside `_handle_detail` and
is untouched.

One thing the finding does not say but the tree does: `A_REVERSE` is
already the console's selection weight everywhere else — Inbox rows,
Teams rows, table rows, thread and message lists. So the active tab now
carries the same weight every other selected thing carries, rather than
a cue invented for tabs.

## What changed

**One grammar, both levels.** `top_tab_segments()` and the new
`detail_tab_segments()` bracket every label. The active one is painted
`A_REVERSE`; the Inbox urgency weight stays `A_BOLD` and the two
compose, so an operator sitting in Teams still sees that Inbox is owed
something, and a quiet Inbox does not look urgent merely for being
selected. Both bars are painted label by label for that reason — a
single string could only weight all of them or none.

**One pair of keys.** `[` and `]` move to the previous/next tab at the
level the operator is in. The whole of the context separation is one
guard: the top-level branch declines while `mode == "detail"`, so
`_handle_detail` keeps its own tabs and `]` there never escapes
upward. `Tab`/`Shift-Tab` remain aliases — they are what the previous
grammar's muscle memory reaches for, and removing a working gesture
costs something and buys nothing.

**Narrow widths.** `visible_tab_segments(width)` drops labels WHOLE,
from whichever end is not the active tab, and returns nothing at all
rather than a truncated `[Inbo`. The acceptance boundary asks for both
halves: no partial bracket, and never lose the tab the keys act in.

**What the console says.** The Teams and Inbox footers now advertise
`[/] tabs`, the same hint Work detail has always shown, including the
empty-view footers that were easy to miss.

## Superseded assertions edited, and why

The finding explicitly supersedes W25's top-level navigation and
rendering rule, so two of its tests asserted the old rule and could not
both survive. This is the case where a rename would not do — the
ruling replaces the behaviour they pin:

- `test_the_selected_tab_is_distinct_without_colour` became
  `test_every_tab_is_bracketed_and_the_active_one_is_highlighted`. The
  information W25 was protecting is not dropped: it moved to the paint,
  and the replacement asserts the paint rather than assuming it. W25's
  `AttrScreen` gained `reverse_text()` beside `bold_text()` for that.
- `test_the_detail_tab_keys_are_not_the_top_level_ones` became
  `test_the_bracket_keys_move_the_top_level_tabs_too`, pointing at
  `test_w110_tab_grammar` for the separation that DOES survive.

W123's two tab-bar tests asserted that the inactive label carried no
brackets. The finding shows `[Messages] [Events]` verbatim, so those
move too; their fake screen also had to start recording attributes,
because the active cue is now a weight and a fake that drops it cannot
see the thing this Work adds. Nothing else in either suite changed.

W25's honest concern — that a terminal ignoring weight loses the active
cue — is a real cost of the ruling and is recorded here rather than
worked around. The finding answers it directly: brackets identify
controls as tabs, and they do not by themselves identify which tab is
active.

## Verification

- `tests/work/test_w110_tab_grammar.py` — new, **27 passed**: both bars
  bracketed with exactly one highlighted, `[`/`]` wrapping at both
  levels, every tab reachable from every tab, Work-detail keys never
  reaching the top level and the top level taking them back on Esc,
  pane focus untouched by tab movement, both aliases, `[`/`]` literal
  in the command bar, the search entry and the `::` batch buffer,
  narrow widths from 1 to 40 columns painting no partial label and
  never losing the active tab, both footers, the operator
  documentation, and a REAL terminal driving `]` three times to wrap
  the top level and once more inside Work detail without disturbing it.
- W25 **36 passed**, W123 **32 passed**, and the TUI suites they sit
  beside (`test_tui`, `test_w71_navigation`, `test_w74_header`,
  `test_w17_poke_visibility`) green.
- The complete v11 gate, `just test-v11`, exits 0: **2176 passed**
  (parallel), **40 passed** (serial), both bridge suites green.
- After the review round (R1/R2): the focused suite is **31 passed**,
  including both additive review regressions unedited, and the gate
  exits 0 at **2392 passed** (parallel) / **40 passed** (serial) with
  W137's suite in the tree beside it.


## Response to review `review-2026-08-19T20-22-46Z.md`

**R1 — the identity could overwrite a label into a partial tab.**
Accepted, and the test I wrote was part of the defect: it asserted the
paint CALLS rather than the composed row, so it accepted a whole
`[Jobs]` that the identity later half-erased. `visible_tab_segments`
decided against `width - 1` while `_render_header` right-aligns the
participant over that same span.

The budget is now the room the labels actually have — `_tab_budget()`
reserves the identity and one separating space — so the decision is
made where the constraint is. The identity's own guarantee is
untouched: it is still painted last and still overdraws, because "no
width may clip away who the operator is signed in as" is the reason
that ordering exists. Your regression asserts the final cells and
passes unedited.

**R2 — a narrow detail bar could show only the inactive tab.**
Accepted. The detail bar had its own left-to-right loop that stopped at
the first label too wide; at width 13 with Events active it painted
`[Messages]` and nothing else — advertising a tab the screen did not
show and losing the one it did.

Both bars now call one `fitted_tabs(segments, active, budget)`. Two
copies of a rule is how the second copy ends up not being the rule, and
this Work is about exactly that: one grammar, applied at both levels.

**R3 — a W137 change was present without a W137 claim.** The factual
finding was correct at the time you read the tree, and I record it
rather than explaining it away. W137 has since been assigned to me and
is CLAIMED (seq 180); every W137 edit in the tree was made after that
claim succeeded, not before.

What I cannot do is hand you a working tree containing only W110. The
two Works share one uncommitted tree and separating them is a Git
operation, which my role forbids. So the boundary is stated instead of
performed, and it is clean:

- **W110** owns `top_tab_segments`, `detail_tab_segments`, `_tab_bar`,
  `fitted_tabs`, `visible_tab_segments`, `_tab_budget`, the `[`/`]`
  branch in `handle()`, the `[/] tabs` footer hints, the tab paragraphs
  in `docs/BATON-WORK.md`, and `tests/work/test_w110_tab_grammar.py`.
- **W137** owns the `COLUMNS`/`DROP_ORDER` rename to `RUN`,
  `TEAM_COLUMNS`, `TEAM_DROP_ORDER`, `TEAM_ID_FLOOR`, `_fit`,
  `team_layout`, the `_team_cells` session change, the `_render_teams`
  measurement, the runtime-column paragraph in `docs/BATON-WORK.md`,
  and `tests/work/test_w137_runtime_tables.py`.

W137 is being returned for its own independent review in the same
session, so nothing here is carried forward unreviewed.
