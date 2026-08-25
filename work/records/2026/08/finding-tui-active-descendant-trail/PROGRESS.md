# Implementer progress — active descendant trails

Created 2026-08-24 by `baton.claude` on claiming W6814.

## Delivered: PLAN item 4, the projection half

`tree.active_trails` — every actively claimed Work the bounded three-level
window HIDES, with the visible ancestor it belongs under — derived **inside the
tree's existing read snapshot**, with `rows`, `summary`, `filter` and
`snapshot_seq` unchanged. `tests/work/test_w6814_active_trails.py`, **12 cases,
all passing**.

Both approved rulings are implemented:

- **Additive projection-minor.** `PROJECTION_VERSION` advances 12.4 → 12.5, and
  the six suites asserting the old minor are migrated with it. A consumer that
  ignores the new member reads exactly what it read before.
- **One trail per hidden canonical claim, even when it has children.**

## Review corrections — 2026-08-25

**All three P1s corrected**; details below are kept as history.

**[P1] A deep filter match now keeps its structural context.** Hidden claims
and their ancestry are derived **before** the filter decides what to keep, and
a hidden claim that matches retains its bounded ancestors with
`filter_match: false`. The anchor is the deepest retained row. My own
`test_a_handler_filter_finds_the_claim_the_window_hides` asserted `rows == []`,
enshrining the opposite of the confirmed ruling; corrected under the review's
case-specific approval.

**[P1] Trail rows carry their canonical claim facts.** `_claimed_ats`,
`_handoffs` and `_first_open_blockers` are batched across all trail endpoints
in one read each, reusing the **same sampled `now`** the window used.

**[P1] Ordering is the full containment order** — the whole root-to-endpoint
sibling path, from the same canonical order the window itself uses.

## Delivered: PLAN items 5, 6 and 7 — the renderer and navigation half

Claimed again 2026-08-25 after releasing rather than handing back a second
projection-only cut. **Complete and verified.**

**Item 5 — the presentation stream.** `tree_stream` (module level, so it is
testable without a terminal) produces the PHYSICAL display order: ordinary
Work rows, and after each anchor's whole ordinary subtree one elision entry
followed by that anchor's active Work rows. Only Work entries are selectable,
which is what keeps the cursor, the viewport anchor, the Id/cue budgets and
every key on exact Work ids while the elision still costs a physical line.
`_render_table` paints the marker at the Title column with the Id column left
empty and dim, so it cannot be read as a Work row; the scroll window is
computed over stream lines and anchored on the selected Work's line, and the
selection attribute is decided by identity rather than by row index — the two
counts are no longer the same number.

Insertion is after the anchor's whole subtree rather than immediately after
the anchor row: a group painted between a parent and its own visible children
would read as another child of that parent. Groups flush deepest-first, so
nested anchors stay inside their branch.

**Item 6 — activation, root-scoped tabs, bounded history.** Enter reads
`progress.children` — the same number the `▸N` disclosure draws — so a Job
with children becomes the contextual root and one without opens its detail.
`u` survives as the explicit re-root, which is the only way to root at a
childless Job. The contextual Work page carries `[Jobs] [Messages] [Events]`
scoped to its ROOT Work; `_show_tab` never reads the highlighted row, so
moving the cursor cannot re-aim Messages. Tab moves record no history.

The navigation stack became interaction history: one entry per explicit
navigation, coalescing a move to the page you are already on, bounded at
`NAV_HISTORY_LIMIT = 64` with the oldest ordinary entry evicted — and
`nav_caller` held beside the stack so the last Back always lands on the page
the walk started from, which is what stops eviction from stranding the
operator. `nav_segments` is now derived separately and expands each Work page
to its containment ancestry, so the trail still names every level while one
Enter costs one Esc.

**Item 7 — acceptance.** `tests/work/test_w6814_active_descendant_trail.py`,
**40 cases**: the live W5/W6631 shape, several claims under one anchor and
under different anchors, the claimed non-leaf, ordinary-visible
deduplication, ancestor Handler isolation, claim-fact and Run-state parity,
`⋮`/ASCII fallback (including an unknown encoding), long titles, every width
from 40 to 110, resize, the handler-filter counterexample, selected-row
scrolling under a short viewport, the closed-row reveal, activation on both
branches and on a trail row, `u` on a childless Job, re-root recomputation,
the three tabs and their scoping, and the whole history model including
64-entry eviction with caller preservation and a restart reset. Four of them
drive a real PTY: the live shape, activation and Back, the root-scoped tabs,
and a live SIGWINCH in both directions.

## Superseded expectations, updated in place rather than deleted

Each edit names the ruling that superseded it, and each keeps the property the
original case existed to protect:

- `test_w71_navigation` — `test_enter_opens_details_never_drills` is now
  `test_enter_activates_what_the_selected_work_actually_holds` and asserts
  BOTH branches; `test_unfold_re_roots_and_esc_returns` is one Esc.
- `test_w292_breadcrumb_navigation` —
  `test_direct_grandchild_entry_pops_one_work_segment_per_back` became
  `..._is_one_action_and_one_back` and now asserts the other half too (two
  explicit entries are two Backs); the `the root · detail` second segment
  became the root-scoped tab case.
- `test_w110`, `test_w123`, `test_w2597` — the two-tab cycle became three.
- `test_w25_real_cursor_keys`, `test_tui`, `test_parity` — cases that used
  Enter merely to REACH a detail view now use a gesture that reaches it from
  any row.
- `test_parity`'s row parser breaks on the footer's stable `Enter ` prefix
  rather than on one wording of the help text.

## Verification

    just test-v11
    # 3,032 passed (parallel), 52 passed (serial), ACP: 55 pass / 0 fail

Focused: `test_w6814_active_descendant_trail` 40/40,
`test_w6814_active_trails` 12/12, projection + parity beside them.

## Not done, and named rather than rounded up

- **The v12 TUI adoption note (PLAN item 8's second half).** Not written as a
  new v12 document. The durable statement already exists in this record's
  FINDING — "the same concept belongs in the eventual v12 TUI even if its
  renderer is independently implemented" — and `v12/PLAN.md` is the v12 worker
  manager's implementation notes, not a TUI plan. Inventing a v12 TUI planning
  document to hold one sentence would put the concept somewhere nobody reads
  it, and the review is explicit that v12 is not changed here. If the reviewer
  wants it recorded inside the v12 subtree instead, say where and it is one
  edit.
- **PLAN item 9, the rollout gate.** Unchanged and still after terminal
  closure: request the managed dispatch drain, wait for live claims to clear,
  then commit and deploy. Not started, and not this Work's to start.
- **The `↳` containment marker keeps its unconditional Unicode spelling.**
  The fallback ruling was about the elision; extending it to `↳` is a
  separate change and is recorded as a clarification in FINDING.md rather
  than done quietly here.

## Review correction — 2026-08-25

**[P1] An active filter overwrote the contextual Work tab row.** Two
independent rules wrote to one hard-coded screen row. W5 says an active filter
is ALWAYS disclosed; W6814 says a contextual Work page always shows which of
its three tabs it is on. I painted the tab row at `table_top` and advanced it,
and then painted the filter clauses at a literal row `1` and reset `table_top`
to a literal `2` — so on a re-rooted page whose filter survived the re-root the
clause text landed on top of the tabs, leaving `filter: status=open [Events]`:
one disclosure destroyed and the other made misleading.

Every row above the table is now allocated from one running cursor, so the
order is breadcrumb, tabs, filter, table header and each row is the whole row.
The literals were the defect, not the arithmetic — which is why the correction
is a cursor rather than a bigger constant.

Beside the reviewer's additive case I added three more, because the review asks
for properties the single case does not pin: the stable ORDER of the four rows
(and that neither overpaints the other), that the table's viewport budget
beneath them is unchanged — every window row and its elision group still
painted — and that W5's narrow-width horizontal viewporting of the clause line
survives the extra row.

    just test-v11
    # 3,036 passed (parallel), 52 passed (serial), ACP: 55 pass / 0 fail

All three phases entered this time; the review's run stopped at the failing
regression before its serial and ACP phases.

## State

**Awaiting final review.**
