# Plan

1. [done 2026-08-27] Confirm the unique participant-actionable total, complete
   descendant roll-up, textual `Mine` cue, and flattened “Awaiting me” view.
2. [done 2026-08-27] Revalidated Jobs/tree bounds, exact selected-Route
   resolution, shared handlers, pickup separation, tab grammar, navigation
   history, paging and projection ownership. Recorded the focused baseline,
   implementation map, proposed response, flattened view, `m` key,
   `actionable-work` command, zero/narrow behavior and regressions in
   `evidence/reviewer-research-2026-08-27.md`.
3. [done 2026-08-27] Approved projection 12.7, `[Jobs 0]`, all-team
   `actionable-work`, complete wrapped breadcrumbs, opaque 100-row paging, `m`
   navigation, and the explicit W2938 supersession boundary. Narrowed the
   mandatory whole `Mine` column to the ordinary Jobs containment tree; it is
   not repeated in specialized Work tables where it is redundant or costly.
4. [done 2026-08-27] Add the authority projection, Jobs header total,
   subtree cue, flattened view, navigation and adversarial deep/shared-route
   regressions under the approved scope.
5. [then review] Independently verify unique counting, omitted-depth roll-up,
   snapshot consistency, routing changes and separation from Inbox/Teams.

## 2026-08-27 — implementation

- [done] 4a. The authority half: `_claimable`, `_actionable_rollup` and
  `actionable_work` in `projection.py`; `viewer_actionable` and
  `actionable_descendants` on tree and active-trail rows;
  `actionable_for_viewer` on the tree response; projection 12.7; the
  `actionable-work` verb; the `EFFECTIVE-BATON.md` section. Measured by
  removal: 12 mutations, 10 caught, 2 expected-unseen and named.
- [done] 4b. The console half: `[Jobs N]` always spelled including
  `[Jobs 0]`; the mandatory, never-clipped `Mine` column on the ordinary
  containment tree and nowhere else; `m` opening the flattened all-team
  `Awaiting me` page with complete wrapped breadcrumbs, 100-row paging,
  claim, and Enter/Back restoring page and row. Measured by removal:
  **21 of 21 caught, none expected-unseen.**
- [done] 4c. Regressions: `tests/work/test_w26328_actionable_discovery.py`
  (authority) and `tests/work/test_w26328_actionable_console.py` (console),
  including a real-terminal case; parity now compares the drawn `Mine` cell
  against the projection's own facts.
- [next review] 5. Independent verification of unique counting, omitted-depth
  roll-up, snapshot consistency, routing changes and the separation from
  Inbox/Teams.

### For review

- [judgement] The count is the team-wide total at EVERY root, including a
  re-rooted page. Scoping it to the current root is a different contract.
- [measured] The `Awaiting me` page's independence from `z` and the Jobs
  filter IS mutation-measured: a filter injected into `mine_rows` is caught by
  four cases. Recorded because I expected it to be unmeasurable and it was
  not — the mutation is the honest test of that, not my reading of the code.

## 2026-08-28 — independent review changes requested

- [required] Replace the positional actionable-work offset with an opaque,
  stable continuation over canonical `WORK_ORDER`, and keep the TUI/CLI as
  token pass-through clients. Add a regression where an earlier page member is
  claimed or rerouted before the next page; every still-actionable later Work
  must remain discoverable exactly once.
- [required] Correct the too-narrow diagnostic to include the mandatory Mine
  allocation and prove that widening to the stated minimum admits the table.
- [verify] Re-run the 64 focused cases, affected console/projection suites,
  CLI/JSON boundary tests, and pagination mutation measurement before returning
  for independent review.

## 2026-08-28 — implementation of the reviewed corrections

- [done] P1a. The continuation is a POSITION. `projection.py` names the two
  rank expressions the canonical order is built from once, publishes them as
  `WORK_ORDER_KEY` columns, and walks `WORK_ORDER_TOTAL` — the canonical
  order refined with the identity so it decides every pair, which is what a
  cursor requires. `actionable_work` skips rows at or before the cursor's
  position instead of slicing an offset, and reads one row past the page to
  decide whether a continuation exists.
- [done] P1b. The token is OPAQUE. `_cursor`/`_cursor_position` encode and
  refuse it; the CLI declares `after=` a string with no default and the help
  says to pass it back unchanged; the TUI holds `mine_after` as `str | None`
  and never reads, increments or invents one; `EFFECTIVE-BATON.md` replaces
  the `after=25` example and states the pass-through rule.
- [done] P2. The too-narrow refusal states a SUFFICIENT width. `layout_minimum`
  derives it from `layout_fits`' own expression against the same lead the
  failing judgment used, so the mandatory `Mine` allocation and the wait cue
  are counted and the number is exact rather than merely larger.
- [done] Regressions: `TestTheContinuationIsAPositionAndNeverAnOffset` and
  `TestTheContinuationIsOpaque` (authority),
  `TestTheTooNarrowRefusalStatesASufficientWidth` (console), and
  `evidence/w26328-corrected-pagination.py` beside the reviewer's own file.
- [next review] 5. Independent verification, unchanged.

## 2026-08-28 — independent re-review changes requested

- [verified] Keyset continuation preserves later Work across earlier claim and
  reroute removal; earlier insertion does not repeat; the width correction is
  sufficient. Focused authority/console gate: 84 green.
- [required] Bind a decoded cursor to its named Work and current total-order
  position inside the read snapshot. Refuse nonexistent/impossible/moved
  positions rather than accepting an invented boundary that can hide every
  actionable row. Preserve ordinary removed-from-actionable continuation when
  the row still exists and its order position is unchanged.
- [required] Add well-shaped nonexistent-position and changed-rank regressions,
  plus a mutation that removes the binding check. See
  `review-2026-08-28T11-07-40Z.md`.

## 2026-08-28 — implementation of the re-reviewed binding

- [done] P1. `_cursor_bound` proves, inside the read snapshot, that the token's
  named Work exists and that its current total-order position is the one the
  token names. Refusal directs the client to refresh. The lookup is over `work`
  so a row that merely stopped being actionable stays a valid cursor.
- [done] Regressions: `TestTheContinuationIsBoundToThisAuthority` — a
  well-shaped invented position, a real Work at a wrong position, a cursor row
  whose rank changed, a claimed cursor row that must still continue, a closed
  one that must still continue, and a blocking one whose claim does move it.
- [done] Four mutations added, including the one the review named and one that
  writes the binding against the actionable set.
- [done] `EFFECTIVE-BATON.md` states the binding and the ordinary refresh
  refusal.
- [next review] 5. Independent verification, unchanged.

## 2026-08-28 — independent third review changes requested

- [verified] The row/current-position binding fixes invented and moved cursor
  positions while preserving same-view claim/reroute continuation. Focused 90,
  corrected evidence, and 244 affected compatibility cases are green.
- [required] Bind the continuation to the participant-relative view that
  produced it. A real token returned to another participant on a disjoint
  Route must refuse rather than hide this viewer's actionable Work.
- [required] Preserve the whole-`work` row binding; add the two-disjoint-Route
  regression and a mutation removing only view binding; update help/guide to
  state same-participant reuse; then return for independent review.

## 2026-08-28 — implementation of the participant-view binding

- [done] P1. The continuation carries the resolved viewer under a bumped `w2`
  scheme; `_cursor_view` compares it before the row-position check and refuses
  cross-view reuse without offering a refresh that could not help.
- [done] Regressions: `TestTheContinuationIsBoundToItsParticipantView` over two
  disjoint Routes, plus a scheme-tag case at this build's exact arity, plus
  `evidence/w26328-corrected-cross-view.py`.
- [done] Four mutations added, including the one the review named and one that
  reverts the scheme bump.
- [done] `EFFECTIVE-BATON.md` and the CLI help state that a continuation is
  valid only for the participant view that produced it.
- [done 2026-08-28] 5. Independent verification accepted the participant-view
  binding and rechecked the earlier row-position, keyset, width and TUI/CLI
  boundaries. Focused 96, corrected evidence and 191 affected compatibility
  cases are green; see `review-2026-08-28T12-43-41Z.md`.
