# Finding: make Work detail a breadcrumb-scoped view

## Observed — 2026-08-20

The TUI currently shows the global `[Jobs] [Teams] [Inbox]` tab row while a
selected Work's `[Messages] [Events]` row is also visible. Two simultaneous
tab rows imply two peer navigation surfaces even though Work detail is a
drill-down inside Jobs. The current location and the action of Back/Esc are
therefore unclear.

## Confirmed decision — 2026-08-20

- The global `[Jobs] [Teams] [Inbox]` tab row is visible only at the top
  level. It is not repeated inside Work detail.
- Entering Work detail replaces that row with a breadcrumb naming the complete
  navigation path, followed by the local `[Messages] [Events]` tabs.
- `[` and `]` continue to move only among the tabs at the current level.
- Back/Esc pops exactly one breadcrumb level. It does not jump unconditionally
  to Jobs. Repeated Back/Esc follows the recorded path outward until the
  top-level Jobs view is reached.
- Returning outward preserves the prior selection and view state at that
  breadcrumb level where practical.

This ruling refines, but does not replace, the shared bracket and key grammar
in `work/records/2026/08/finding-consistent-tui-tab-grammar/`. Brackets still
identify tabs and `[`/`]` still navigate the current tab set; only the
simultaneous display of global and local tab bars is removed.

## Acceptance boundary

- The top-level view shows exactly one global tab row.
- Work detail shows a location breadcrumb and exactly one local tab row; the
  global tab row is absent.
- Back/Esc pops one breadcrumb segment at a time through nested Work scopes and
  returns to the prior selection rather than resetting to the Jobs root.
- `[`/`]` cannot leak from Messages/Events into Jobs/Teams/Inbox.
- Narrow and resized terminals keep the current location and active local tab
  unambiguous.
- Focused virtual-screen and real-terminal regressions cover entry, nested
  entry, local tab movement, repeated Back/Esc, selection restoration, and
  narrow layouts.

## Current-tree revalidation — 2026-08-21

**Observed.** `Console.render()` calls `_render_header()` before
`_render_detail()`. `_render_header()` always paints
`top_tab_segments()` (`Jobs`, `Teams`, `Inbox`), while `_render_detail()`
later paints `detail_tab_segments()` (`Messages`, `Events`). The two-peer-row
ambiguity is therefore one explicit render path, not an artifact of terminal
replay.

**Observed.** The location data already exists. `projection.breadcrumb()` is
root-first and carries stable Work ids and titles; `projection.detail()` also
includes that breadcrumb. `Console.breadcrumb_text()` currently re-reads the
same ancestry for `detail_work` and joins only the titles into the global
header. The correction does not require a new authority projection or any
workflow mutation.

**Observed.** The current view state cannot implement the ruled Back model:

- `Console.path` stores only re-rooted Work ids. `u` appends an id and resets
  `cursor`/`selected_id`; Esc pops the id and resets them again, so the parent
  selection is lost.
- `_enter_detail()` records only `detail_return` (`table` or `search`) and one
  `detail_work`. `_handle_detail()` Esc switches directly to that mode; there
  is no Work-scope stack to pop.
- Search is the useful existing model for restoration: `search_saved` records
  path, cursor, stable selected id, and closed visibility, then restores the
  exact frame on Esc.

**Confirmed interaction with earlier rulings.** This finding supersedes W25,
W74 and W110 only where their tests or prose require the global tab bar to
remain visible inside Work detail. Their top-level Jobs/Teams/Inbox order,
identity placement, urgency/attention weights, and shared bracket grammar stay
current. It refines W71's Back behavior: returning from a nested scope restores
the frame below it instead of resetting that frame to row zero. W2597 remains
current: a genuinely fresh Work-detail entry starts on Messages with fresh
pane/page state. Restoring the caller's table/search selection is not carrying
the closed Work's tab or cursor into a later fresh entry.

**Implementation consequence.** A visible breadcrumb segment and a Back step
must describe the same scope. On direct entry to nested Work, initialize the
root-first Work scopes from the canonical breadcrumb so repeated Back visits
the parent Work scope one segment at a time; do not paint ancestry that one
Back immediately skips. Save client-only view state per visited frame. Frames
synthesized for unvisited ancestors use the normal fresh-detail defaults;
frames the operator actually visited restore their local tab, pane, selection,
and page state. Once the root Work scope is popped, restore the recorded caller
frame. A search caller therefore returns to its exact result window and its
next Esc still restores the prior Jobs table; an Inbox entry remains the
existing handoff into Jobs rather than returning to Inbox.

**Patch boundary.** The owning implementation is
`src/baton_work/tui/app.py`: `Console.__init__`, `breadcrumb_text`,
`_render_header`, `render`, `_enter_detail`, `_handle_detail`, the table `u`
and Back branches in `handle`, `_search_mode_key`, and `_handle_inbox` are the
state/rendering seams. `projection.breadcrumb` and `projection.detail` are
inputs, not mutation targets. Keep `_switch_tab`, the detail pane handlers,
and the `[`/`]` context guard behaviorally unchanged. Update the operator
contract in `docs/BATON-WORK.md`.

**Regression boundary.** Extend the existing W71, W74, W110, W2597, search,
and real-cursor suites rather than replacing their unrelated assertions:

- top-level paints one global tab row; detail paints a complete location row
  with no global tab labels and one local tab row with exactly one active tab;
- direct grandchild entry and nested re-entry pop one Work segment per
  Esc/Back, then restore the caller's stable selection;
- table re-root Back restores the row and view state that opened it;
- Messages/Events `[`/`]` never change the global tab, pane focus, selection,
  or authority state;
- search and Inbox entry paths reach the same Work-scope model without losing
  search's exact restoration or turning Inbox into the Back destination;
- narrow and resized screens retain the current Work segment, active local
  tab, and right-aligned participant identity as whole, unambiguous units;
- a real terminal exercises repeated bare Esc and decoded Back/Left, and the
  authority sequence proves the whole navigation flow is read-only.

## Confirmed universal scope — 2026-08-20

The Work-detail-only wording above is narrower than the confirmed navigation
model and is superseded as to scope. Breadcrumb-scoped drill-down is universal
across the TUI:

- A front page is normally a list view and shows its own top-level tabs.
- Entering any selected entity replaces that top-level tab row with a
  breadcrumb for the drilled path. Global tabs are not carried into the
  detail page.
- The detail page may expose its own local tabs beneath the breadcrumb. Those
  tabs describe views of the selected entity, not peer application areas.
- Further drill-down appends another breadcrumb segment and again shows only
  the local navigation appropriate to the new page.
- Back/Esc pops exactly one segment from this universal navigation stack and
  restores the page, selection, local tab, and pane focus at the revealed
  level where practical.

Work detail with `[Messages] [Events]` is the first concrete case, not a
special-case architecture. Jobs, Teams, Inbox, member details, message detail,
and later drillable surfaces follow the same rule whenever they have a
list-to-detail transition. The Work-specific current-tree revalidation above
remains valid evidence for the first implementation, but the implementation
must use a shared navigation model and must not encode this as a Work-only
exception.

## Shared-navigation revalidation — 2026-08-21

Plan step 4 asked what the common implementation boundary is, and whether
anything beyond Work detail drills. Answering it first is what kept this from
becoming a Work-only special case.

**Confirmed.** Every existing drill-in is a change of `Console.mode` (or of
`Console.path`) plus a bespoke way back:

| surface | in | out (before) |
| --- | --- | --- |
| Jobs table re-root | `u` appends to `path` | Esc pops `path`, resets cursor |
| Work detail | `_enter_detail` sets `detail_return` | Esc reads `detail_return` |
| search results | `/` saves `search_saved` | Esc restores that tuple |
| neighbour (links) view | `b` sets `links_work` | Esc sets `mode = "table"` |
| poke view | `p` sets `mode` | Esc sets `mode = "table"` |

Five surfaces, five ways in, five ways out, and only one of them (search) kept
enough to restore what the operator was looking at. That — not the tab row —
is why Back was unpredictable; the double tab row was the visible symptom.

**Confirmed.** Teams and Inbox have no page drill today. Their per-row detail
is an inline pane on the same page, and the Inbox `Enter` is a documented
HANDOFF into Jobs rather than a drill into a page of its own. They join the
model when they grow a list-to-detail transition, by pushing a frame; nothing
about them needs to change now, and nothing about them is excepted.

**Ruled implementation boundary.** One navigation stack, `Console.nav`, with
one push, one pop, and one captured view state. A frame is
`{kind, label, restore}`; `restore` is a snapshot of a fixed list of view
fields, so the level revealed by a Back is the level the operator left. Empty
stack means top level, which is the ONLY place the global tab row paints and
the only place `[`/`]` move it. Every surface above uses that one mechanism,
and a later drillable page joins by pushing a frame.

**Ruled: the breadcrumb starts at the page.** The first segment is the
top-level page (`Jobs`), because that is the level the last Back reaches. A
trail whose first segment nobody can navigate to would be decoration.

**Ruled: a re-root records its ancestry too.** `u` on a nested Work seeds one
frame per containment ancestor, exactly as a Work-detail entry does, and each
Back reveals one of those levels re-rooted. This is the finding's own rule —
do not paint ancestry that one Back immediately skips — applied to the other
drillable surface rather than to Work detail alone. It refines W71: one `u` on
a grandchild is now three segments out, not one.

**Confirmed unchanged.** `projection.breadcrumb` and `projection.detail` are
inputs. `_switch_tab`, the detail pane handlers, the local `[`/`]` grammar,
W2597's fresh-entry defaults and W110's bracket vocabulary are untouched.

## Superseded test expectations — 2026-08-21

Three existing cases asserted the global tab row inside a drilled view, which
is exactly what the confirmed decision removes. They were updated, not
deleted, and each keeps the property it existed for:

- `test_w71_navigation.py::test_unfold_re_roots_and_esc_returns` — still
  proves the re-root paints a real trail and that Esc returns upward; it now
  walks the recorded path one segment at a time.
- `test_w74_header.py::test_drilled_views_keep_their_real_breadcrumb` — still
  proves a drilled view names its location and keeps the identity at the right
  edge.
- `test_w110_tab_grammar.py::test_a_real_terminal_moves_both_tab_levels_with_brackets`
  — still proves `]` inside a drilled page moves that page's LOCAL tab and
  nothing else, and now proves it from the header rather than in spite of it.

Their top-level ordering, identity placement, urgency weights and bracket
grammar assertions are unchanged.

## Review round 1 — accepted corrections, 2026-08-21

`review-2026-08-21T06-28-18Z.md` recorded two blocking findings. Both were
reproduced directly and are now recorded rulings.

**[P1] A nested re-root appended the whole ancestry again.** Reproduced:
re-rooting at `root` and then at its child produced
`Jobs > root > root > child`, and the first two Backs revealed visually
identical scopes. `_seed_work_frames` pushed every canonical ancestor
unconditionally.

**Ruled.** A drill DEEPER inside a containment path the stack already records
adds only the missing descendant scopes; the existing frames and their
restoration state are preserved. Only a drill into an unrelated tree seeds the
whole ancestry, from the caller.

**Ruled: a scope is (Work, page kind), not Work alone.** A re-rooted subtree
and that Work's detail page are two different pages of the same Work, so one
never stands in for the other and only a drill of the SAME kind continues a
recorded path. Where that produces two adjacent segments for one Work — `u`
then Enter on the same row — the deeper segment names its page
(`the root > the root · detail`), because two segments reading the same title
would not say which is which. Frames therefore carry the Work id and not only
the title: two siblings may share a title, and deciding what is already on the
stack by comparing prose would put the operator in a scope they did not open.

**[P1] The linked drill-through dropped the far Work's ancestry.**
Reproduced: with a dependency pointing at a grandchild, Enter in the neighbour
view produced `Jobs > grand` instead of `Jobs > root > child > grand`, so Back
skipped the parent scopes. Opened from an already re-rooted caller it also
left that caller's frames prefixing an unrelated Work.

**Ruled.** The deliberate re-root semantics stay: Enter there moves to a Work
somewhere else. So the recorded path is UNWOUND first — the caller's ancestry
belongs to a different tree and prefixing the far Work with it would paint a
containment path that does not exist — and the far Work's own canonical
ancestry is then seeded through the same shared model every other drill uses.
Its trail and its Back agree by construction, not by a second implementation.

## Review round 2 — accepted correction, 2026-08-21

`review-2026-08-21T06-58-22Z.md` recorded one blocking finding, and it is a
regression this Work introduced rather than a pre-existing gap.

**[P1] The drilled header suppressed the active-filter disclosure.** Confirmed
by re-running the reviewer's own reproduction: with
`work_filter={"status": "open"}` the top-level header painted `Filter:1` and
every drilled header — Work detail, re-rooted table, search results — painted
none. `_render_header` returned immediately after `_render_breadcrumb`, so W5's
header tag was reachable only at the top level.

**Ruled.** W292 supersedes the global TAB ROW inside a drill and nothing else.
W5's ruling that an active filter is ALWAYS disclosed in the header is
untouched and now actually holds: every breadcrumb header paints the same tag,
from one definition shared with the top-level header so the two cannot
disagree about when it appears. Both right-edge units — the tag and the
participant identity — are reserved where the trail's room is decided, so the
trail is shortened around them rather than over them, and the separately ruled
normalized-clause line is unchanged.

Search is the case that made this urgent rather than cosmetic: results are
themselves narrowed by the active filter, so a drilled page without the
disclosure showed a reduced result set with nothing saying why.

## Review round 3 — accepted for deployment, 2026-08-21

`review-2026-08-21T07-16-52Z.md` independently verified the round-two
correction. The top-level and drilled header paths now share one filter-tag
definition; detail, re-root, and search retain the active-filter disclosure;
the breadcrumb budgets around the filter tag and identity as whole units; and
the normalized clause line remains intact. The combined W292/W71/W74/W110/W5
set passed 73/73, direct filtered rendering retained both right-edge units at
100, 72, 56, 44, and 32 columns, and `git diff --check` was clean. No further
acceptance-boundary defect was found.
