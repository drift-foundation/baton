# Plan — Show a navigable ASCII dependency neighborhood

1. [done 2026-08-22] Revalidated the current `[b] deps` projection and
   navigation paths. Pinned a bounded one-snapshot neighborhood model,
   deterministic selected-centered ASCII layout, adjacency/stacked narrow
   fallback, overflow grammar, depth bounds, and ID-anchored navigation without
   changing authority semantics. Evidence: `evidence/baseline-2026-08-22.txt`.
1a. [done 2026-08-22] Confirmed the proposed exact contract in
    `FINDING.md`: existing historical-upstream/live-downstream semantics,
    depth 1..3, four-neighbor branch pages, 200-occurrence hard cap, overflow
    Enter, recenter-in-graph, and exact Back restoration.
2. [partially landed 2026-08-22] Implement the dependency-only ASCII graph
   with explicit `blocks` direction, recentering, bounded depth controls, and
   honest overflow groups. Containment, duplicates and follow-ups stay outside
   this view.
   LANDED: the canonical model and the rendering.
   `projection.dependency_neighborhood` — one bounded read under
   `_read_snapshot`, exact `links` parity including the ruled
   historical-upstream/live-downstream asymmetry, directional expansion that
   does not turn corners, depth 1..3, four-neighbour branch pages with exact
   per-branch omitted counts, the 200-occurrence cap disclosed rather than
   silent, and visible refusal for a cycle or a missing endpoint. The public
   `links` response is unchanged. `tui/graph.py` — a PURE renderer: the
   layered form with the center in one column, the adjacency fallback, the
   stacked fallback, one deterministic row order at every width, a refusal
   when one complete selector will not fit, and overflow tokens naming their
   exact count and side.
   NOT LANDED: the console wiring. `_links_rows`/`_render_links` still paint
   the old flat page; `b` has not moved to the graph; `graph_center`,
   `graph_depth`, the selection anchor and branch expansions have not joined
   `NAV_STATE_FIELDS`; Enter-recenter, `+`/`-`, overflow Enter and exact Back
   restoration are not implemented.
3. [partially landed 2026-08-22] Add focused rendering, resize, navigation,
   dense-graph, cycle, and projection-parity regressions.
   LANDED: 19 cases in `tests/work/test_w4996_dependency_graph.py` covering
   the projection (parity both directions, the closed-consumer/closed-blocker
   asymmetry, one-to-many and many-to-one, no corner-turning, depth bounds and
   refusals, branch paging per branch, the cap constant, a shared DAG node,
   malformed-edge refusal, read purity including the write-ahead log, and the
   unchanged public `links`) and the pure layout (ASCII-only direction, the
   center column, width choosing the renderer and never the graph, the
   too-narrow refusal, identical row order at every width, overflow token
   text/count/side, the footer, and a lone Work).
   NOT LANDED: console navigation and PTY cases, because the console is not
   wired yet.
3a. [changes requested 2026-08-22] First-slice review found three defects:
    deeper renderers drop canonical non-center edges and invent direct center
    edges; stacked downstream selection metadata targets a different Work
    from the selector painted on its row; and the 200-occurrence cap applies
    only after every direct edge has been materialized. Two additive renderer
    regressions are retained. Exact result:
    `evidence/review-first-slice-2026-08-22.txt`.
3b. [pending] Correct the first-slice edge/selection defects, make direct-edge
    materialization bounded while preserving exact omitted counts, add a real
    over-cap regression, and return for independent re-review before console
    keys are wired onto the model.
3a. [done 2026-08-22] Correct the first-slice review: renderers now draw the
   projection's OWN edges at every depth rather than pairing every node with
   the center; every selectable row displays the token for its own Work in
   every renderer; and the branch is read with a `COUNT(*)` plus an ordered
   `LIMIT` rather than fetched in full and sliced. Each independently
   mutation-checked — the bounded read needed a regression that watches the
   rows the helper returns, because memory has no visible result. 24 focused
   cases. Evidence: `evidence/correction-first-slice-2026-08-22.txt`.
3c. [changes requested 2026-08-22] Correction re-review confirms the exact
   edge and selectable-row fixes, but finds that an expanded branch still
   materializes beyond the remaining occurrence cap, depth-two wide rows do
   not keep a node in its shortest-path layer column, and center-branch
   overflow tokens do not follow their visible siblings. Four additive cases
   are retained. Verdict: `review-2026-08-22T18-07-47Z.md`.
3d. [pending] Bound every branch query by both its expansion page and the
   remaining global occurrence allowance; make wide layout columns derive
   from shortest-path layers; and place each overflow token immediately after
   the visible siblings of the exact branch it expands. Return for re-review
   before console keys are wired onto the model.
3e. [done 2026-08-22] All three closed. The branch query's SQL row limit is
   now `min(expansion page, occurrence_cap - occurrences)` — the round-2
   count-plus-LIMIT change had moved the unbounded read one caller up rather
   than removing it — and `capped` is recorded when the ALLOWANCE, not the
   page, is what truncated a branch, because the loop can no longer discover
   that for a branch the SQL already trimmed. `_columns` derives one start
   offset per Work from its shortest-path layer, so a node's column is a
   property of the node and not of the row it appears on. Overflow tokens are
   placed by their BRANCH: `_branch_anchor` finds the last visible member and
   the list is rebuilt once, with an empty branch taking the slot the branch
   itself would occupy; in the wide form the token sits in its SIBLINGS'
   column, one layer out from its owner. Four mutations, each independent.
   Two cases added because M3 failed only the downstream reported case — for
   the center's upstream branch the branch rule and an owner-relative rule
   always coincide, so a two-node depth-one layer is what witnesses it — and
   one existing assertion of mine was corrected because it encoded the old
   placement. 30 focused cases, 2925 + 52 pytest with the whole v11 suite
   green, 297 Node, 55 ACP; the four v12 failures are W2929's new reviewer
   cases and were not touched from here.
   Evidence: `evidence/correction-first-slice-round2-2026-08-22.txt`.
3f. [changes requested 2026-08-22; round-three correction re-review] Close
   the three boundaries in `review-2026-08-22T19-04-09Z.md`: do not count or
   re-omit canonical edges already rendered through another valid DAG path;
   disclose the global cap when page and remaining allowance tie at a full
   view with direct omissions; and keep a shortcut target in its one recorded
   wide column or use an honest fallback when the graph cannot be layered
   monotonically. Retain all three additive regressions and return the model
   and renderer for re-review before console keys are wired onto them.
3g. [done 2026-08-22] Round-4 correction. A shared DAG branch no longer
   invents omissions: two per-run memos — the direct page already read for a
   `(Work, side)` branch, and the greatest depth it has been expanded with —
   stop a second path from re-querying with less room and labelling rendered
   edges hidden, while a later SHORTER path carrying more depth is still
   admitted and path-local cycle detection is untouched. Occurrences count
   RENDERED edges only. The cap is disclosed when `room <= page`, so the
   equality boundary — page-truncated and allowance-truncated at once, with
   the view full — is not reported as ordinary paging. The layered form
   DECLINES a graph it cannot lay out monotonically rather than moving an
   endpoint, and the adjacency fallback it hands to now keeps one arrow
   column, since a ragged one reproduced the same defect. Six mutations, each
   independent; the first run found three halves masking one another, so
   three fixtures were built to separate them. 36 focused cases; 2931 + 52
   pytest with the whole v11 suite green; 297 Node; 55 ACP.
   Evidence: `evidence/correction-round4-2026-08-22.txt`.
   OPEN FOR THE REVIEWER: longest-path layering would make every DAG edge
   monotonic and keep the wide form for a shortcut graph, but the approved
   contract says shortest-path layers, so that is a contract question rather
   than a rendering fix and was not taken.
3h. [changes requested 2026-08-22; round-four correction re-review] Close the
   memo-hidden cycle boundary in `review-2026-08-22T19-23-55Z.md`: a cached
   branch expansion cannot answer the path-dependent cycle question for a
   different ancestry. Preserve the bounded shared-branch correction while
   making every cycle in the admitted graph fail visibly with its exact edge.
   Retain the additive damaged-store regression and return for re-review.
3i. [pending] Wire the console: `[b]` opens the graph, the navigation state
   fields, Enter-recenter, overflow Enter, `+`/`-` depth, selection after
   depth reduction and resize, exact Back restoration, and the console and
   PTY regressions for all of it. Include the live W6175 many-to-one shape:
   its compact `Wait` cell says `W2845+1`, while `[b] deps` must expose and
   select both `W2845 --blocks--> W6175` and
   `W4996 --blocks--> W6175`. The `ROW_DEEPER` depth-frontier gap belongs with
   this slice, since `+` is what opens it.
3h. [done 2026-08-22] Round-5 correction. The branch memo could hide a
   cycle: it answers "do this branch's descendants need expanding again",
   while cycle closure is a property of the ANCESTRY it does not carry, so a
   node reached first where its edge was ordinary and again with the other
   end among its ancestors returned on a memo hit before any path comparison.
   `_refuse_cycles` is a second boundary over the edges the response actually
   CONTAINS — iterative, bounded by the occurrence cap, distinguishing
   ancestry from "already finished" so an ordinary diamond is not refused,
   and naming the exact closing edge. The path-local check stays: it no
   longer changes the answer but refuses at the first re-entry instead of
   walking the budget round a loop. A cycle whose closing edge was not
   admitted is deliberately NOT reported. Four mutations; two guards were
   unwitnessed on the first run and two cases were written for them. 43
   focused cases; 2938 + 52 pytest with the whole v11 suite green; 297 Node;
   55 ACP. Evidence: `evidence/correction-round5-2026-08-22.txt`.
   CLOSED BY THIS REVIEW: the round-4 renderer question. Declining the
   shortest-path layered form for a non-monotonic shortcut and using the
   aligned adjacency fallback is consistent with the approved contract, and
   no longest-path amendment is recommended.
3j. [changes requested 2026-08-22; round-five correction re-review] Close the
   cap-order boundary in `review-2026-08-22T19-42-55Z.md`: a direct page can
   be fetched before an earlier sibling's descendants consume the remaining
   allowance, so decide whether a new later edge can enter the response before
   applying the path-local cycle guard to it. A closing edge cut by the cap is
   not part of the drawn graph and must become an exact omission, not a graph
   refusal. Retain the additive regression and the final admitted-edge cycle
   boundary. Return the model for re-review; console item 3i remains pending.
3i. [done 2026-08-22] Round-6 correction. The fast path-local guard ran one
   step too early: an earlier sibling's descendants can spend the allowance
   between the branch fetch and a later sibling's turn, and the loop tested
   `far in path` before testing whether that edge could still enter the
   response — so a closing edge raised although the cap would have omitted it
   and the admitted graph was acyclic. That contradicted the round-5 rule I
   had just pinned. Cap admission is decided FIRST for an edge not already
   drawn: no occurrence left means disclose the cap and the exact remaining
   omission and return, without inspecting or recursing through that edge.
   The path guard then applies only to an edge that WILL be in the response,
   or is already in it, so refusing over it invents nothing;
   `_refuse_cycles` is unchanged. Three mutations; M2 passed green at first,
   so a fifth case was built at exactly `cap - 4` to catch a revisited branch
   reporting its own rendered edges as hidden. 47 focused cases; 2942 + 52
   pytest with the whole v11 suite green; 297 Node; 55 ACP.
   Evidence: `evidence/correction-round6-2026-08-22.txt`.
3k. [done 2026-08-22; round-six correction re-review] Sign off the bounded
   projection and pure-renderer foundation. The cap-cut closing edge is now
   omitted rather than inspected, already-rendered edges retain the fast
   guard without spending another occurrence, and the final admitted-graph
   boundary is unchanged. Independent focused verification is 47/47 and
   `git diff --check` is clean. Review:
   `review-2026-08-22T19-57-01Z.md`. This sign-off deliberately excludes the
   still-pending console/navigation/PTY and `ROW_DEEPER` slice in item 3i.
3j. [signed off 2026-08-22] Independent re-review confirmed the bounded
   projection and pure-renderer FIRST SLICE. Cap admission before the
   ancestry test closes the round-five finding without weakening either
   cycle boundary or reintroducing shared-branch false omissions; 47/47
   verified independently. Review: `review-2026-08-22T19-57-01Z.md`. Not
   whole-Work sign-off — the console slice was named as next.
3k. [done 2026-08-22; SECOND SLICE] The console. `[b]` opens the dependency
   neighbourhood and the flat page is deleted. `graph_center`,
   `graph_depth`, `graph_anchor` and `graph_expanded` join
   `NAV_STATE_FIELDS`, so Esc restores the exact prior graph; selection is
   an IDENTITY (a Work id, or a branch key for a token) and never a row
   index. `j`/`k` move by row, Enter recenters or widens exactly one branch
   page, a depth-frontier token says `+` is its key rather than doing
   something plausible, `+`/`-` move depth inside 1..3, a depth reduction
   that removes the selection returns it to the center, and a resize moves
   nothing. Rows are DERIVED on demand, so a key does not depend on having
   painted first. `ROW_DEEPER` finally has something to report: the
   projection gains `frontier`, the exact direct count the DEPTH bound cut
   off, taken at limit zero so it materializes nothing. Six mutations; the
   `_nav_capture` dict copy is recorded as UNWITNESSED. Nine existing cases
   moved, each inspected and each saying why its own subject survives.
   58 focused cases; 2953 + 52 pytest with the whole v11 suite green; 297
   Node; 55 ACP. Evidence: `evidence/console-slice-2026-08-22.txt`.
   FOR THE APPROVER: the old page's cross-team drill-through — Enter
   unwinding the stack and re-rooting the Jobs tree at the far Work (W292
   round-1 P1, R105) — is no longer reachable from `[b]`, because the
   approved contract replaces Enter with recentering and says it does not
   jump to the Jobs table. Authorized, but the capability's loss is named
   rather than absorbed; if it should survive it needs a key and a line in
   the contract.
3l. [pending] PTY coverage beyond what the existing suites drive, opening the
   graph from the SEARCH results page, and plan item 4's operating guide.
3m. [changes requested 2026-08-22; independent console-slice review] Make
   `j`/`k` traverse unique Work/token identities so a repeated shared-DAG Work
   cannot trap selection; remove a branch's depth-frontier disclosure once a
   shorter path actually expands that branch; and wire `[b]` from a selected
   search result with exact Back restoration. Retain all three additive
   regressions. Then complete the named PTY matrix and operating guide before
   returning the whole presentation for review. Verdict:
   `review-2026-08-22T20-51-17Z.md`.
3m. [changes requested 2026-08-22] Console-slice review: repeated Work rows
   trap keyboard selection (movement stepped by row while the anchor resolved
   to the first appearance); a shortcut leaves a false depth-frontier token
   because expansion never clears the entry a depth-bound visit recorded; and
   the approved SEARCH entry path is absent. Review:
   `review-2026-08-22T20-51-17Z.md`.
3n. [done 2026-08-22] All three closed. `_graph_keys` is the traversal order —
   every DISTINCT selectable key once, in first-appearance order — while
   painting still highlights every appearance; the contract always said both
   and I served them from one list. `_expand_branch` clears `frontier[key]`
   when it expands the branch, so a bound never describes something other
   than what is on screen. `_search_mode_key` opens the graph through the same
   `_open_graph` the table uses, so the frame, depth and Back behaviour are
   identical. Six mutations; M4's first run failed only the reported case, so
   my frontier fixture was rewritten — it had put the shortcut a hop further
   out and asserted absence vacuously. 65 focused cases (58 before); 2960 + 52
   pytest, 316 Node, 55 ACP, 239 v12 — every gate in the tree green.
   Evidence: `evidence/correction-console-slice-2026-08-22.txt`.
3o. [pending] The full PTY matrix and plan item 4's operating guide, for
   whole-presentation sign-off.
3p. [changes requested 2026-08-22; corrected-console re-review] Make frontier
   disclosure path-order independent. A branch expanded through an older
   shortcut must not regain a depth-frontier entry when a later longer path
   reaches the same Work at the depth bound. Retain the additive symmetric
   DAG regression in `review-2026-08-22T21-21-32Z.md`; focused result is
   65 passed, 1 failed. Then complete item 3o before returning the whole
   presentation for review.
3p. [done 2026-08-22] Frontier disclosure is INDEPENDENT of edge creation
   order: a depth-bound visit consults the same memo the expansion sets, so a
   branch already expanded in this response is never recorded as a frontier
   whichever path arrived first. The later-expansion pop stays, so both
   orders are covered by two mechanisms that agree. Four mutations.
3q. [done 2026-08-22] The PTY matrix —
   `tests/work/test_w4996_dependency_graph_pty.py`, 11 cases: many-to-one,
   one-to-many, both sides, the absent containment/duplicate text, the empty
   state, the footer legend and its depth, a narrow terminal keeping every
   relationship, a resize in both directions, the stacked fallback, and
   Enter-recenter with Esc back. IT FOUND A CRASH: the console exited 1 on a
   30-column terminal because `_graph_row_key` assumed every row carried a
   Work, while the stacked renderer's presentation rows carry none by design.
   Every focused case passed while that was true.
4. [done 2026-08-22] The TUI operating guide. `docs/BATON-WORK.md` gains
   **The dependency graph**: scope, the drawn shape, every bound with the
   token that discloses it, the key table, Enter's exact meaning, the
   narrow-terminal fallbacks and refusal, and the damaged-store refusal; the
   two sentences that described the flat page now point at it.
   Evidence: `evidence/correction-frontier-and-pty-2026-08-22.txt`.
   69 focused + 11 PTY; 2975 + 52 pytest, 316 Node, 55 ACP, whitespace clean.
5. [changes requested 2026-08-22] Whole-presentation behavior and docs are
   accepted: symmetric frontier, PTY matrix and operating guide independently
   pass 80/80. Before sign-off, replace or register the unowned
   `tempfile.mkdtemp()` root in the new stacked-row focused regression and
   prove repeated execution leaves zero new test-owned roots. Review:
   `review-2026-08-22T21-48-17Z.md`; evidence:
   `evidence/review-whole-presentation-2026-08-22.txt`.
3r. [done 2026-08-22] The one P2 is closed: the case I added last turn to
   pin the stacked-path crash called `tempfile.mkdtemp()` and nothing owned
   the result, so every run left an empty root. It takes pytest's `tmp_path`
   now, like every other console case, and a guard asserts this file's own
   source mints no temporary root of its own — asserting the SOURCE rather
   than counting `/tmp`, because a count depends on every other process in
   the run. Residue bracket across the full non-serial suite and the PTY
   matrix: zero new roots. The nine paths the review lists were left in
   place, since destructive cleanup outside this Work's fixtures is an
   operator act.
   Evidence: `evidence/correction-residue-2026-08-22.txt`.
5a. [signed off 2026-08-22] Independent re-review confirms the stacked-path
   case uses pytest's owned `tmp_path`; two consecutive focused executions
   leave the exact `/tmp/tmp*` inventory unchanged. Focused plus PTY is 81/81
   and whitespace checks are clean. This closes the only outstanding P2 and
   signs off W4996's whole presentation. Review:
   `review-2026-08-22T22-09-23Z.md`; evidence:
   `evidence/review-residue-correction-2026-08-22.txt`.
# superseded by item 4 above:
4. [pending] Update the TUI operating guide and independently review the
   presentation before deployment.
