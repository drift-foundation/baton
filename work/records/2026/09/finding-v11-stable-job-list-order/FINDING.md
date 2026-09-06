# Finding: V11 Jobs lose their visual position when runtime state changes

Ledger Work: W103313

## Observation — 2026-09-06

W103076 and W103077 are high-priority siblings under the same parent. W103076
was created first. After W103076 became active, it stopped satisfying the
derived `blocking` predicate while queued W103077 still satisfied it. The
shared blocker-first order consequently moved W103077 above W103076 in the
human Jobs list.

The ordering is deterministic, but it is not useful interaction design. A
state transition moves rows underneath the cursor and makes their prior
visual position unreliable. The blocker preference was designed to improve
machine pickup, not to make an interactive list continually reshuffle.

## Confirmed decision — 2026-09-06

Human-facing Jobs lists use a stable structural order:

1. Dependency and containment structure determines where Work belongs in the
   displayed hierarchy.
2. Explicit priority may deliberately order peers within that structure.
3. `created_seq`, followed by the durable Work ID only as a total-order
   fallback, orders otherwise equal siblings.
4. Transient scheduling and runtime facts do not reorder visible peers. This
   includes `blocking`, readiness, phase, claim/Handler, pickup state,
   heartbeat, and message activity.
5. Specifically, W103076 remains before W103077 through implementation,
   review, correction, blocking, parking, and resumption because they share a
   structural position and priority and W103076 was created first.
6. A filter may add or remove a row, and closing Work may remove it from the
   default open view. If the row is shown again, its relative structural order
   is restored rather than derived from its latest state.
7. Machine readiness may retain blocker-first scheduling. Human presentation
   and machine pickup must use separate named orderings rather than one shared
   `WORK_ORDER` contract.

Future filters may hide parked or blocked Work. They are outside this bounded
correction and do not justify state-driven reordering.

## Acceptance boundary

- `home`, `children`, and every displayed `tree` sibling level follow the
  stable human ordering.
- State transitions alone cannot invert two visible equal-priority siblings.
- W103076/W103077 is represented by a regression in which the earlier sibling
  is active and the later sibling is a ready unclaimed blocker.
- Participant readiness retains its scheduling-oriented blocker preference.
- The TUI keeps selection keyed to Work identity while projection refreshes,
  so a refresh neither changes the selected Work nor moves its row because of
  runtime state alone.
- Search keeps its existing stable paging contract.

## Independent review — 2026-09-06

**Observed:** `src/baton_work/projection.py` has one shared `WORK_ORDER`
fragment. It currently supplies all six human display reads (`home`,
`children`, the root and descendant reads in `tree`, and the two reads that
place hidden active claims) as well as three machine scheduling reads
(`participant_actions`, `_first_actionable`, and `actionable_work`). The
`actionable_work` continuation also binds and compares the blocker rank through
`WORK_ORDER_KEY` and `WORK_ORDER_TOTAL`.

**Confirmed:** the split must occur at those consumers, not in the blocker
predicate. The display order is explicit priority, `created_seq`, then Work ID.
The dispatch order remains explicit priority, the existing binary blocker
rank, `created_seq`, then Work ID where a total keyset order is required.
`participant_actions`, `_first_actionable`, `actionable_work`, its cursor
binding, and its cursor encoding retain the dispatch order and current
rank-change refusal behavior.

**Observed:** `search` has its own `created_seq` continuation and does not use
`WORK_ORDER`; it is outside the correction. The TUI consumes `tree` without an
independent sort and `_render_table` reanchors `selected_id` by durable Work ID
on each render. No TUI implementation change is needed. The regression must
nevertheless exercise that seam: select the earlier sibling, change runtime
state so the later sibling becomes the ready unclaimed blocker, refresh, and
prove both the selected identity and sibling position remain stable.

**Confirmed implementation boundary:**

- `src/baton_work/projection.py`
- `tests/work/test_w7_blocker_preference.py`

The existing W7 suite owns the now-superseded assertion that human and machine
surfaces share one order, so this Work explicitly authorizes correcting its
descriptions and expected behavior within this boundary. No schema, command,
JSON shape, TUI implementation, search, or actionable-work cursor-format change
is scheduled.

## Legacy TUI regression scope — 2026-09-06

**Observed:** the complete v11 gate passes 3,338 tests and fails only
`tests/work/test_tui.py::test_the_focused_facts_and_collapse_come_from_the_projection`.
The test's fixture creates the live Work, closed Work, and blocker in that
order, but its navigation comment and keystrokes assume W7's superseded human
blocker-first ordering. Under the confirmed display order, initial selection
is already the live Work; `j` moves to the blocker. With closed rows revealed,
one `j` reaches the closed Work; the former two reach the blocker.

**Confirmed:** add `tests/work/test_tui.py` to the frozen path set only to
remove the first `j`, remove one of the two later `j` keystrokes, and update
the adjacent stale ordering explanation. Its canonical-fact, collapse,
revision, gate, outcome, and rationale assertions are unchanged. No fixture,
production TUI, or other test change is authorized.

## Final independent review — 2026-09-06

**Confirmed:** the candidate separates stable human display order from
blocker-first machine dispatch at every scheduled consumer, preserves search
and actionable-work cursor semantics, and keeps refreshed TUI selection
anchored to Work identity. The legacy TUI regression contains exactly the
approved keystroke and adjacent-comment correction; its fixture and assertions
are unchanged.

The three candidate paths match the reviewed digests recorded in
`review-2026-09-06T17-34-12Z.md`. The focused 20-test review run and the full
v11 gate pass. No finding remains; W103313 is independently signed off.
