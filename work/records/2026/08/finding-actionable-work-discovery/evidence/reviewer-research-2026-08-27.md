# Reviewer research — 2026-08-27

## Current implementation map

**Observed:** `src/baton_work/projection.py::tree` returns only three containment levels. Its `deeper` field says that children were omitted, while `active_trails` pierces the bound only for actively claimed Work. A queued, unclaimed actionable descendant below the cap therefore has no row or locator.

**Observed:** `participant_actions` already resolves the current selected Route and emits Work actions in `WORK_ORDER`, but its Work branch also redelivers the viewer's own claimed Work for restart recovery. That is intentionally broader than W26328's queued/unclaimed count.

**Observed:** `_first_actionable` implements the unclaimed pickup-pool predicate and returns only one diagnostic locator. No public projection returns the complete pool, its unique count, or containment roll-ups.

**Observed:** `src/baton_work/tui/app.py::actionable_work` is broader again: bold Title includes the viewer's current claim and directed `@` obligations, including blocked Work. It cannot source the new `Mine` field.

**Observed:** `search` reaches nested Work but requires a non-empty title/id query and is restricted to Work owned by the viewer's team. `tree` filters remain bounded and preserve containment rather than flattening. Neither answers “show every Work this participant may claim.”

**Observed:** `Console` already has id-stable selection, a bounded browser-shaped navigation stack, cached one-snapshot reads, and search paging/restoration patterns suitable for the new view.

## Focused baseline

Command:

```text
./.venv/bin/python3 -m pytest -q \
  tests/work/test_w81_personal_bold.py::test_the_actionability_matrix \
  tests/work/test_w81_personal_bold.py::test_a_directed_obligation_is_independently_actionable \
  tests/work/test_w2938_participant_pickup.py::test_ten_jobs_make_one_obligation_not_ten \
  tests/work/test_w2938_participant_pickup.py::test_every_idle_eligible_member_evaluates_its_own_interval \
  tests/work/test_w2938_participant_pickup.py::test_the_winner_of_the_race_removes_it_from_the_others_pool \
  tests/work/test_w2938_participant_pickup.py::test_no_job_row_or_work_detail_carries_the_cue \
  tests/work/test_w155_three_level_tree.py::test_a_deeper_chain_still_stops_at_three \
  tests/work/test_w155_three_level_tree.py::test_the_window_reads_do_not_grow_with_the_tree
```

Result: `8 passed in 0.11s`.

This establishes the current three-level bound, broad bold-title semantics, participant-owned pickup obligation, and shared-route race before W26328 changes presentation.

## Proposed exact projection

One authority helper should derive the participant's **claimable Work set** from current facts:

- `status == open`;
- `ready == true`;
- `phase == queued`;
- no Handler; and
- the exact current Route, including an explicitly selected alternate, resolves to the viewer's `team.member`.

The helper scans all Work whose Route resolves to the participant, not only Work owned by the participant's team. Planned `Next`, directed obligations, trials, pokes, runtime refreshes, the viewer's own held claim, and member pickup/capacity state are excluded.

Within the same read transaction, gather the containment parent map once and derive:

- `actionable_for_viewer`: the unique size of the claimable set;
- `viewer_actionable`: whether a projected row itself belongs to it; and
- `actionable_descendants`: the number of distinct claimable containment descendants below that row, excluding the row itself and ignoring the visual depth/filter bound.

The derivation must be bounded by a fixed number of statements, not one recursive read per displayed row. Ordinary `tree` rows and `active_trails` rows both receive the two row facts. Filtered-out and depth-omitted descendants still count.

Add a paged read verb `actionable-work` returning every match in canonical `WORK_ORDER`. Each row carries the ordinary structured Work facts plus the complete root-first `breadcrumb` array in the existing `{id, title}` shape. The result also carries `actionable_for_viewer`, an opaque `next_after` continuation, and `snapshot_seq`. Default page size is 100, accepted range 1..500. Each page is one current snapshot; clients treat the cursor as opaque, and a deliberate refresh restarts at the first page rather than pretending to continue an old snapshot.

The additive tree/home row and summary fields plus the new read verb require projection `12.7`, not a database schema change.

## Proposed exact TUI contract

- The global tab label always spells the exact count, including zero: `[Jobs 0]`, `[Jobs 6]`.
- Ordinary Jobs trees carry a textual `Mine` column. Its exact values are blank, `me`, `+N`, or `me+N`. `N` is decimal and never truncated.
- `Mine` is a mandatory structural column on any table that draws Work rows. Its width is the maximum of the heading and visible values; lower-priority informational columns drop first. If Id, minimum Title, and whole Mine still cannot fit, use the existing explicit terminal-too-narrow refusal.
- Existing bold Title remains unchanged and broader. A viewer-held claim or blocked directed obligation may be bold while `Mine` is blank.
- Pressing `m` from the ordinary Jobs tree opens the flattened view named `Awaiting me`; the canonical CLI spelling is `actionable-work`. `m` is a locator mnemonic only—the shared Route does not assign ownership.
- Each flattened entry renders its Id and complete breadcrumb. Breadcrumb text uses the existing ` > ` separator and soft-wraps beneath its own start column; it is never silently clipped. Endpoint/Via may appear only as whole responsive columns and drop before Id or breadcrumb content.
- `j`/`k`, `n`/`p`, Enter, `c`, and Esc/Left follow the existing Jobs/search conventions. Enter activates the selected Work; one Back restores the same Awaiting-me page, selection id, and continuation state. A successful claim refreshes the view and removes the now-claimed row.
- An empty view says `(no work awaiting you)` rather than showing an unqualified empty table.
- At widths too narrow for the active global tab label beside the participant identity, the existing `fitted_tabs` rule applies: omit the label whole, never render a plausible partial count.

## Compatibility with W2938

W2938's participant pickup contract remains authoritative: ten queued Jobs create one participant-level pickup obligation, and pickup lateness stays only on Teams. W26328 supersedes only the earlier horizontal statement that Jobs gains “no replacement” after removing `New`, because `Mine` adds a distinct availability locator. It does not restore `Claim`, `Pickup`, `pending`, `late`, or `overdue` on Work rows and must not read `member_pickup`.

## Regression matrix

- zero/one/many claimable Work; exact queued predicate; blocked, parked, terminal, and claimed exclusions;
- current default/alternate/unresolved Route changes and planned-Next exclusion;
- two handlers see the same shared opportunity until one atomic claim removes it from both lists;
- a busy participant still sees queued availability while owing no pickup, proving the projections are distinct;
- deep fourth-and-later descendants, filtered descendants, active-trail rows, cross-team ownership, and unique ancestor roll-up;
- snapshot injection between internal reads, plus a statement-count bound independent of visible/deep Work count;
- stable canonical ordering, multi-page traversal, complete breadcrumbs, refresh, and selection by Work id;
- `[Jobs 0]` and multi-digit totals; all four Mine spellings; multi-digit natural width; explicit too-narrow behavior;
- Awaiting-me open/back restoration, paging, claim removal, and shared-route wording;
- W81 bold cases remain unchanged while their new Mine facts remain deliberately different;
- W2938 one-participant pickup tests remain green and no Work row gains pickup vocabulary;
- JSON/TUI parity, help/CLI grammar, packaged console, documentation, and projection-version checks.
