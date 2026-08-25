# Plan: surface active descendant Jobs beneath visible roll-ups

1. Revalidate the live W5/W6631 reproduction and the existing three-level and
   deeper-child disclosure rules. Identify the exact tree/projection fields and
   renderer/navigation paths; do not infer activity from messages or timers.
2. Define one active-descendant trail model derived from
   exact active claimed Work, Handler and runtime state. Preserve the first three
   containment levels, deterministic ordering, no duplication of ordinarily
   rendered leaves and row-local parent semantics.
3. Render one `⋮` (`...` fallback) elision plus the exact active leaf rows under
   each applicable visible ancestor. Make the leaf rows navigate to exact Work
   without treating the elision as authority Work.
4. Make an opened non-leaf Job the contextual tree root, recompute the
   three-level/elision window relative to it, and preserve the prior root via
   breadcrumb and Back/`Esc`. Present root-scoped `[Jobs] [Messages] [Events]`
   tabs, restore tab/row state on Back, and default leaves to `Messages`.
   Record one history entry per explicit Enter, never one per skipped
   containment ancestor. Bound ordinary session history at 64 entries, coalesce
   duplicates, exclude local interaction changes and preserve the caller as a
   final escape target.
5. Add focused virtual-screen and real-terminal coverage for one and multiple
   active claims, including a claimed non-leaf, deep/collapsed containment, one-click deep-entry Back
   restoration, explicit multi-step entry, duplicate coalescing, 64-entry
   eviction, caller preservation, restart reset, resize, filters, long titles
   and navigation. Verify the bounded additive projection-minor change and that
   no protocol semantic or SQLite schema change is required.
6. Return the bounded change for independent review and retain the interaction
   concept in the v12 TUI adoption plan.

## Revalidated implementation plan — 2026-08-24

Status: **approved and implementation-ready**. The live reproduction and the
additive projection-minor correction are confirmed.

1. [done — research] Reproduce W2/W3/W5 hiding active W6631 and trace
   `projection.tree`, `projection.runtime`/`teams`, `breadcrumb`, the TUI row
   painter, id-anchored navigation and canonical filter path.
2. [done — decision] Add an additive projection-minor `active_trails` member to
   `tree`, preserving one-snapshot JSON/TUI parity, projection-owned filtering
   and complete filtered trail behavior.
3. [done — decision] Treat every hidden canonical claim as a trail endpoint,
   even when the claimed Work contains children.
4. [implementation] Derive hidden active trails in the tree's
   read snapshot; preserve ordinary `rows`, canonical filtering, full
   containment ordering, no duplication and unbounded-by-count underlying
   results. Advance the additive projection minor and document the field.
5. [implementation] Add a presentation stream of selectable Work rows and
   non-selectable elision lines. Insert each group after its nearest visible
   ancestor's ordinary subtree; reserve marker/title structure before
   truncation; anchor cursor, scrolling and Enter/`u`/`d` to exact Work ids.
6. [implementation] Apply the confirmed activation supersession from one
   canonical `progress.children` fact: activating a non-leaf re-roots with the
   existing breadcrumb/Back state machinery; activating a leaf opens detail.
   Update the W71-era docs/tests so both rules do not remain authoritative.
7. [verification] Cover one trail, multiple same-anchor and different-anchor
   trails, an active claimed non-leaf, active/filter match with otherwise empty
   bounded rows, inactive and queued omissions, ordinary-visible
   deduplication, ordering, long/narrow/resize/scroll, re-root/Back restoration,
   closed-row visibility, `⋮`/ASCII fallback and exact activation in projection,
   virtual-screen, parity and real-PTY tests.
8. [review] Return implementation and focused/full verification for independent
   review; record the v12 TUI adoption note without changing v12 here.
9. [rollout gate] After satisfying review and terminal closure, request managed
   dispatch drain and wait for all live claims to clear before committing and
   deploying the TUI bundle. Do not drain while this Work is still awaiting its
   implementation claim.

## Projection review correction — 2026-08-25

Status: **changes requested** in
`review-2026-08-25T00-10-58Z.md`; the renderer/navigation half remains pending.

1. [required] When a hidden active Work matches the filter, retain its bounded
   ancestors as `filter_match: false` structural context and anchor the trail
   to the deepest returned ancestor. Correct the existing empty-rows assertion,
   which conflicts with the approved clarification.
2. [required] Batch and preserve canonical claim, heartbeat and handoff facts
   for trail Work rows and reuse one sampled instant for the trail window.
3. [required] Sort concurrent trails by their complete canonical containment
   path, not by the endpoint Work's global priority/order alone; use the
   existing multi-handler fixture to cover same- and different-anchor groups.
4. [required] Make the three additive reviewer cases green, then complete
   original PLAN items 5–7 without another projection-only handoff.
5. [verification] Run focused projection/filter/parity, virtual-screen,
   real-PTY and full `just test-v11` gates before returning for review.

## Projection correction re-review — 2026-08-25

Status: **projection accepted; Work remains changes-requested**.

1. [done] The three projection regressions pass; focused projection/parity is
   30/30.
2. [required] Implement original items 5 and 6 in the TUI: grouped physical
   elision lines, selectable exact Work rows, Work-id cursor/scroll anchors,
   conditional non-leaf re-root versus leaf detail, root-scoped tabs, and the
   bounded 64-entry explicit-navigation history.
3. [required] Add original item 7's virtual-screen and real-PTY acceptance,
   including Unicode/ASCII marker behavior, narrow/resize/scroll, filtering,
   exact activation and Back restoration.
4. [verification] Run focused TUI/PTY/parity and full `just test-v11`; do not
   return another projection-only cut.

## Renderer and navigation cut — 2026-08-25

Status: **implemented and verified; awaiting independent review**.

1. [done] Item 5 — the presentation stream. `tree_stream` interleaves
   non-selectable elision lines with selectable Work rows; the Jobs table
   budgets the elision as a physical line while cursor, viewport anchor,
   Id/cue widths and every key stay on exact Work ids. One elision per anchor
   group, inserted after that anchor's whole ordinary subtree.
2. [done] Item 6 — the activation supersession and the navigation model.
   Enter activates from `progress.children` (non-leaf re-roots, leaf opens
   detail); `u` remains the explicit re-root; the contextual Work page carries
   root-scoped `[Jobs] [Messages] [Events]`; the Back stack is explicit
   navigation actions bounded at 64 with duplicate coalescing and a preserved
   caller, while the breadcrumb keeps naming the containment path.
3. [done] Item 7 — acceptance. `tests/work/test_w6814_active_descendant_trail.py`
   is 40 cases: virtual-screen structure, marker fallback, long titles,
   narrow width, resize, filters, scrolling, closed-row reveal, activation,
   root-scoped tabs, bounded history, and four real-PTY cases.
4. [done] Superseded W292/W71/W110/W123/W2597 expectations updated in place
   with the ruling that superseded each, and the operator documentation in
   `docs/BATON-WORK.md` rewritten for all three changes.
5. [done] Full gate: `just test-v11` — 3,032 parallel, 52 serial, 55 ACP, all
   passing.
6. [next] Independent review of this cut. Item 9's rollout gate (drain, then
   commit and deploy the TUI bundle) is unchanged and still follows terminal
   closure.

## Renderer review correction — 2026-08-25

Status: **changes requested** in
`review-2026-08-25T04-07-45Z.md`.

1. [accepted] Active-trail grouping and selection, conditional activation,
   contextual Work tabs, bounded explicit-action history, projection parity
   and the recorded implementation clarifications.
2. [required] Allocate the contextual tab row and active-filter clause row as
   separate physical lines; neither may overwrite the other before the table.
3. [required] Make the additive filter-plus-context regression green, then run
   the focused W6814/navigation/parity set and complete `just test-v11`
   parallel, serial and ACP gates.
4. [pending] Return for final independent review; terminal closure still
   precedes the separate W7203 drain/deploy gate.

## Renderer review correction — 2026-08-25

Status: **corrected and verified; awaiting final review.**

1. [done] Review [P1]: the rows above the Jobs table are allocated from ONE
   running cursor. The filter branch painted at a literal row 1 and reset the
   cursor to a literal 2, so on a re-rooted page whose filter survived the
   re-root the clause text overpainted the contextual tab row. Both rows are
   required — W5 always discloses an active filter, W6814 always discloses
   which local tab a contextual page is on — and neither may overpaint the
   other.
2. [done] The reviewer's additive case is green, with three further
   regressions beside it: the stable order breadcrumb → tabs → filter →
   table header, the table's viewport budget beneath them (every window row
   and its elision group still painted), and W5's narrow-width horizontal
   viewporting of the clause line with the tab row present.
3. [done] Full gate: `just test-v11` — 3,036 parallel, 52 serial, 55 ACP, all
   passing, all three phases entered.

## Final independent review — 2026-08-25

Status: **signed off; W6814 may close satisfying.**

1. [done] Inspected the one-cursor correction and its additive regressions;
   tabs, filter disclosure and table header retain distinct physical rows,
   narrow clause viewporting survives, and the active-trail stream remains
   present beneath them.
2. [done] Expanded focused W6814/projection/navigation/parity verification:
   103 passed.
3. [done] Complete `just test-v11`: 3,036 parallel, 52 serial and 55 ACP,
   all passing.
4. [done] Independent sign-off recorded in
   `review-2026-08-25T05-30-30Z.md`. Rollout remains separately owned by W7203.
