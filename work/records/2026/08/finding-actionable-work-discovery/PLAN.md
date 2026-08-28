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
