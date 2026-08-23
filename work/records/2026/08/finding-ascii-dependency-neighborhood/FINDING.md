# Show a navigable ASCII dependency neighborhood

## Observed — 2026-08-22

The TUI advertises `[b] deps` as the complete dependency view, but the current
screen is a flat list of `blocked-by`, `blocks`, duplicate, and duplicate-of
rows. It does not show how the selected Work sits between upstream blockers
and downstream dependents, and it does not place containment beside those
edges. Operators must reconstruct even a small N:M neighborhood mentally.

Rendering the entire authority as a terminal graph would fail under ordinary
fan-in, fan-out, and narrow-window conditions. The useful boundary is a graph
centered on the selected Work, with bounded expansion and deterministic
overflow disclosure.

## Confirmed decision — 2026-08-22

Evolve `[b] deps` into a navigable ASCII neighborhood graph centered on the
selected Work. Do not add graph columns to the main Jobs table.

- Dependency direction is always explicit and reads left-to-right:
  `A --blocks--> B`.
- Containment is a separately labelled vertical relationship. It never
  visually or semantically implies a dependency.
- The initial view shows one hop around the selected Work: upstream blockers,
  downstream dependents, parent, and direct children. Duplicate and follow-up
  relationships remain available but must use their own labels rather than
  borrowing dependency arrows.
- Moving to a node and pressing Enter recenters the graph on that Work.
- `+` and `-` increase or decrease the bounded neighborhood depth.
- Dense or clipped neighborhoods collapse honestly as counts such as
  `[+6 blockers]`; hidden nodes are never silently omitted.
- Narrow terminals retain a readable tabular adjacency fallback. The view is
  fully usable with plain ASCII; Unicode line drawing may be optional styling
  and carries no unique meaning.

Example shape:

```text
                         parent
                       [W1425]
                           |
                        contains
                           |
[W4487 open] --blocks--> [W2929 wait] --blocks--> [+3]
                           |
                        contains
                           |
                        [child]
```

## Acceptance boundary

- Every rendered relationship is derived from the canonical links and
  containment projections; the TUI invents no graph state.
- Edge labels make direction and relationship type unambiguous without color
  or Unicode glyphs.
- Recenter, depth change, overflow expansion, back navigation, and terminal
  resize preserve a deterministic selected Work.
- Cycles or malformed projection data fail visibly instead of recursing or
  hanging the TUI.
- Focused tests cover one-to-many, many-to-one, simultaneous containment and
  dependency, duplicate/follow-up labels, dense collapse, narrow fallback,
  and resize/navigation behavior.

## Dependency-only scope clarification — confirmed 2026-08-22

The containment portions of the preceding confirmed decision, example, and
acceptance boundary are superseded. `[b] deps` shows dependency relationships
only: upstream blockers and downstream dependents around the selected Work.
Containment remains visible in the Jobs tree and does not appear in this view.
Duplicate and follow-up links are likewise outside this dependency graph; they
remain available through their existing relationship projections.

The current example is therefore:

```text
[W4487 open] --blocks--> [W2929 wait] --blocks--> [+3 dependents]
```

Focused coverage concerns one-to-many and many-to-one dependency edges,
selection/recentering, bounded depth, dense collapse, cycles, narrow fallback,
resize behavior, and exact parity with the canonical dependency projection.

## Reviewer revalidation — 2026-08-22

### Confirmed current boundary

`src/baton_work/tui/app.py::_links_rows` performs one cached
`projection.links` read and flattens `blocked_by`, `blocks`, `duplicate_of`,
and `duplicates` into selectable text rows. `b` opens this page for the table's
selected Work; `j`/`k` move by row; Enter leaves the links page, unwinds the
whole navigation stack, and re-roots the Jobs tree at the far Work. There is no
graph depth, graph selection anchor, overflow state, or narrow-specific
renderer. Only `links_work` and `links_cursor` participate in universal Back
state.

The dependency projection has a deliberate asymmetry that this presentation
must not silently redefine:

- `blocked_by` contains every recorded upstream edge, including a satisfied
  edge whose blocker is closed;
- `blocks` contains only open downstream consumers; closed consumers remain
  in audit history but leave the live dependency drill;
- both sides are ordered by the edge's stable `created_seq`.

The live W2929 projection demonstrates the boundary: its blockers are closed
W2928 and open W4487, while its downstream set is the one open W2930. Exact
baseline and symbol inventory are retained in
`evidence/baseline-2026-08-22.txt`.

### Confirmed projection gap for a multi-hop view

`projection.links` is a one-hop public response and is not itself wrapped in
`_read_snapshot`. Recursively calling it from the TUI would be unbounded in
fan-out and could combine different authority states if a writer commits
between hops. The graph therefore needs one bounded canonical neighborhood
read under `_read_snapshot`; it must not become a client-side crawl. Keep the
existing `links work=` response compatible. The new neighborhood model is a
presentation read, not a new relationship or authority mutation.

## Proposed exact presentation contract — awaiting authority ruling

The following resolves the remaining choices in the confirmed design. It is a
proposal until the directed authority obligation on T4996 is answered.

### Canonical neighborhood model

1. Add one pure `dependency_neighborhood` projection that returns the center,
   node summaries, directed `{blocker, work}` edges, per-branch omitted direct
   counts, and `snapshot_seq` from one `_read_snapshot` transaction. Preserve
   the existing `links` JSON/CLI shape.
2. Start at depth 1 and permit depths 1 through 3. Upstream expansion follows
   `blocked_by` recursively; downstream expansion follows the existing live
   `blocks` relation recursively. It does not walk from an upstream node into
   that node's other consumers, or from a downstream node back into its other
   blockers: those are lateral neighborhoods reached by recentering.
3. Admit four neighbors per expanded branch initially, in edge `created_seq`
   order. A selectable overflow token admits four more for that exact
   `(node, side)` branch. A hard 200 rendered-occurrence cap bounds adversarial
   expansion; reaching it keeps an explicit exact count of directly omitted
   edges and says the view cap was reached. No hidden-descendant total is
   guessed.
4. A node reached by multiple valid DAG paths may be drawn more than once but
   remains one selection identity. An edge to an ancestor of its current path
   is a cycle: render one visible graph-invalid diagnostic naming the exact
   `A --blocks--> B` edge and stop expansion. Missing endpoints, malformed
   node summaries, or an edge whose named endpoint disagrees likewise refuse
   the graph visibly rather than dropping the edge.

### Rendering and navigation

- The wide renderer places the selected center between upstream and downstream
  layers. Every edge carries the ASCII label `--blocks-->`, with the arrowhead
  at the consumer. Node tokens show the stable local selector and status;
  titles are the first optional text removed for fit. Color and Unicode add no
  information.
- Width chooses only the renderer, never a different graph model. When the
  layered form cannot fit full selectors plus one complete `--blocks-->`
  segment, use a vertically scrolling adjacency fallback. Each fallback edge
  still spells `Wblocker --blocks--> Wconsumer`; if even that cannot fit on one
  row, stack the full source, label, and target on three rows. A terminal too
  narrow for the longest full selector refuses explicitly rather than clipping
  an identity.
- `j`/`k` and Up/Down traverse one deterministic unique-node order: upstream
  outermost-to-center, center, downstream center-to-outermost, with stable edge
  order inside a layer and overflow tokens after their visible siblings. All
  repeated appearances of the selected ID receive the selection attribute.
- Enter on a Work recenters in the graph and pushes one universal-navigation
  frame; it does not jump to the Jobs table. The current depth is preserved,
  branch expansions reset, and selection becomes the new center. Enter on an
  overflow token expands only that branch. Esc restores the exact prior graph
  center, depth, selection, and branch expansions; the first Esc returns to the
  caller's table state.
- `+` and `-` change depth within 1..3. If decreasing depth removes the selected
  Work, selection returns to the center; otherwise it stays anchored by Work
  ID. Refresh does the same only when the selected ID is no longer in the
  canonical neighborhood. Resize never changes center, depth, expansion, or
  selection and therefore cannot move an action to another Work.
- Depth-frontier tokens name the exact direct count (`[+N deeper blockers]` or
  `[+N deeper dependents]`) and are expanded with `+`, not Enter. Dense-branch
  tokens name `[+N blockers]` or `[+N dependents]` and use Enter. The two
  reasons for omission never share an ambiguous token.

`graph_center`, `graph_depth`, the Work-ID/token selection anchor, and branch
expansion limits must join `NAV_STATE_FIELDS`; storing only a row cursor would
repeat the selection drift the Jobs table already forbids.

### Focused verification boundary

- Projection: one/many on both sides, closed upstream plus open-only
  downstream parity with `links`, depth 1..3, stable ordering, exact direct
  overflow counts, global cap, one-snapshot behavior under an interleaved
  writer, shared DAG nodes, cycle and malformed-fixture refusal, and unchanged
  public `links` response.
- Pure layout: arrow direction on every edge, center placement, branch labels,
  no Unicode dependency, wide-to-adjacency-to-stacked fit, no selector
  truncation, height scrolling, and honest overflow text.
- Console: open from table and search, ID-anchored `j`/`k`, Enter recenter,
  overflow Enter, depth bounds, selection after depth reduction/refresh,
  repeated-node selection, resize in both directions, and exact Back restoration
  through nested graph centers to the original table row/filter/path.
- PTY: many-to-one, one-to-many, simultaneous upstream/downstream, narrow and
  resized screens, footer key legend, and containment/duplicate/follow-up text
  absent from the dependency page.

## Exact graph contract approved — confirmed 2026-08-22

The approver accepts the proposed exact presentation contract without
amendment. Preserve the existing historical-upstream/live-downstream
dependency semantics and public `links work=` response. Implement the bounded
snapshotted `dependency_neighborhood` read, initial/max depth 1/3,
four-neighbor branch pages, 200 rendered-occurrence cap, explicit overflow
counts, Work recentering, and exact Back restoration as specified above.

This ruling changes no relationship semantics and does not bring containment,
duplicates, or follow-ups into `[b] deps`.

## Live many-to-one acceptance example — 2026-08-22

W6175 demonstrates the operator-facing gap while this Work is in progress. Its
Jobs-table `Wait` cell can fit only `W2845+1`, so the second direct blocker,
W4996, is not identifiable from the row. The graph must show both canonical
incoming edges without requiring the operator to infer what `+1` hides:

```text
W2845 --blocks--> W6175
W4996 --blocks--> W6175
```

Both blockers must be selectable and recenterable. The table keeps the compact
count because horizontal space is limited; `[b] deps` is the complete
disclosure surface. This example adds no new relationship or rendering rule —
it is the live many-to-one acceptance case for the already approved contract.

## Implementation revalidation — 2026-08-22 (baton.claude)

The reviewer's confirmed boundary held exactly as recorded: `_links_rows`
performs one cached `projection.links` read and flattens four relations into
text rows; `links` is a one-hop response and is NOT wrapped in
`_read_snapshot`; and the live W2929 neighbourhood still demonstrates the
ruled asymmetry. The approved contract was implemented against those, not
against a reading of them.

### The first slice, and what it deliberately is not

This turn landed the canonical model and the rendering. The CONSOLE IS NOT
WIRED — `[b]` still opens the old flat page, `NAV_STATE_FIELDS` is unchanged,
and none of Enter-recenter, `+`/`-`, overflow Enter or Back restoration
exists. `PROGRESS.md` lists that precisely. The Work returns for review of the
model and the layout rather than being held across a context boundary.

### Decisions taken beyond the contract

- **The layered form draws one row per relationship** with the center repeated
  in its own column, rather than one horizontal chain per path. A fan-out of
  six as chains would either repeat the upstream side six times or need
  box-drawing to join them, and the contract forbids information in styling.
  The example's left-to-right reading with the center between the sides is
  preserved; the literal single line for the 1:1 case is a small special case
  if the reviewer wants it.
- **Layer distance is the SHORTEST path.** A node reachable at two depths sits
  in one column, because drawing it twice in one layer would say there are two
  of it. It may still appear on more than one ROW, which the contract allows
  and the selection anchor handles.
- **`_stacked` keeps ONE selectable row per relationship.** The arrow and the
  far end are presentation rows. Making all three selectable would give one
  edge two identities and break the "same order at every width" property that
  `j`/`k` depends on — the first draft did exactly that and the regression
  caught it.
- **The purity regression hashes the write-ahead log too.** A store in WAL mode
  keeps recent writes there, so hashing the main file alone would call any read
  pure. The first draft did, and its own sanity assertion failed — which is why
  it is worth keeping the sanity assertion.
- **The malformed-edge regression suspends the foreign key to build its
  fixture.** The schema already forbids a dangling blocker, so the damage a
  view must survive cannot be created through the constraint; deleting the
  endpoint with `PRAGMA foreign_keys = OFF` is the shape a damaged file
  actually has.

### Gap, named rather than glossed

`ROW_DEEPER` is defined and unused. Depth-frontier tokens — `[+N deeper
blockers]`, opened with `+` rather than Enter — need the projection to report
what the DEPTH BOUND cut off, and it currently reports only what a BRANCH PAGE
cut off. The contract asks for both and is explicit that the two must not
share an ambiguous token. It belongs with the console slice, because `+` is
what opens it, but it is a real hole in this slice's coverage and is recorded
as one.

## Independent first-slice review — 2026-08-22

**Confirmed P1:** every renderer pairs deeper nodes with the center rather
than rendering the projection edge that reached them. A depth-two chain
`A --blocks--> B --blocks--> C` is drawn as A-to-B plus invented A-to-C,
dropping B-to-C. The retained regression fails exactly there.

**Confirmed P1:** stacked downstream rows attach the consumer selection
identity to visible center text, while the consumer selector is painted only
on a non-selectable row. Wiring Enter onto this model would recenter on a
different Work than the highlighted selector.

**Confirmed P2:** `_dependency_edges` materializes every direct edge before
branch slicing or the 200-occurrence cap applies. The response is bounded, but
the read's Python memory remains proportional to adversarial fan-out; the
existing cap test uses only six consumers and never crosses the cap.

Exact failures and code-path evidence:
`evidence/review-first-slice-2026-08-22.txt`. Independent verdict:
`review-2026-08-22T17-07-39Z.md`.

## Independent correction re-review — 2026-08-22

The canonical-edge and stacked-row identity corrections are confirmed. The
bounded-materialization correction is incomplete, and the exact layered and
overflow-order contracts remain unimplemented in the pure renderer.

**Confirmed P2:** `_dependency_edges` now uses `COUNT(*)` plus `LIMIT`, but
the limit is still the caller's expanded branch value rather than the
remaining global occurrence allowance. Expanding a 240-edge branch with a
200-occurrence cap materializes all 240 rows before the loop stops at 200.
The response is bounded but the projection read is not; the earlier ordinary
four-row observation did not exercise the expanded path.

**Confirmed P2:** the wide renderer does not assign columns by shortest-path
layer. In `A --blocks--> B --blocks--> C`, B appears as the target at column
25 on the first row and then moves back to column 0 as the source on the next.
This contradicts the approved selected-center/layer model and the renderer's
own claim that deeper edges are indented to their layer.

**Confirmed P2:** center-branch overflow tokens do not follow their visible
siblings in traversal order. The upstream token is separated from its four
blockers by the center row; the downstream token appears before all four
dependents. Enter would therefore operate on a token in a different place
from the branch order the contract specifies.

Four additive regression cases are retained. Exact output:
`evidence/review-correction-first-slice-2026-08-22.txt`. Independent verdict:
`review-2026-08-22T18-07-47Z.md`.

## Round-3 correction — 2026-08-22

Three P2s, all reproduced before any edit. Three decisions worth pinning.

**A bound is on the QUERY, not on the loop that consumes it.** The branch row
limit is `min(expansion page, occurrence_cap - occurrences)`. My round-2
correction changed the fetch to a count plus an ordered limit and then handed
that limit the raw expansion value, which moved the unbounded read one caller
up instead of removing it. A view that allocates the whole fan-out and then
declines to draw it is not a bounded view.

**And `capped` says which bound stopped it.** Once the SQL limit is bounded
by the allowance, the drawing loop can no longer discover that the view is
full — it never sees the rows the limit removed. "There is more on this
branch, press Enter" and "this view is full" are different answers to the
operator, so the branch records the second when the allowance, not the page,
is what truncated it.

**A column is a property of the node, not of the row it appears on.** Offsets
come from `_layers`, so every appearance of a Work starts at its
shortest-path column. Justifying each row against the center — which is what
the first version did — puts a depth-one node at the center's right edge on
one row and at column zero on the next, and one node in two columns is an
adjacency list with indentation.

**An overflow token belongs to its BRANCH.** It follows the last visible
member of the branch it opens, at every depth, because that is the next slot
a further page would fill; a token elsewhere makes Enter expansion jump. A
branch with nothing visible has no member to follow and takes the slot the
branch itself would occupy — after its owner going downstream, before it
going upstream, which is the direction each side reads. In the wide form it
sits in its SIBLINGS' column, one layer out from the owner, so it reads as
one more of the rows above it rather than as something about the owner.

### Recorded

For the center's upstream branch, the branch rule and an owner-relative rule
always coincide — the center's blockers are always the rows just above it —
so the reported upstream case could not distinguish them. A mutation showed
that, and a two-node depth-one layer is what witnesses the upstream half.

One existing assertion of mine encoded the old placement and had to be
corrected rather than kept: it required the token not to be the last row,
which the corrected rule sometimes makes it. It states the exact rule now.

## Independent round-three correction re-review — 2026-08-22

**Confirmed corrected at the reported examples:** expanded direct branches
bound their SQL row page by the remaining occurrence allowance, an ordinary
depth-two chain keeps its intermediate Work in one column, and overflow
tokens follow their visible branch siblings.

**Observed — changes requested:** three boundary cases remain. A shared node
reached through two valid DAG paths replays its identical outgoing edges:
`seen_edges` suppresses their rows but the projection counts them again,
reaches the cap with only 154 canonical edges, and reports 105 dependents as
omitted even though all 150 shared dependents are already returned. A branch
whose four-row page exactly equals the four remaining cap slots ends with one
direct omission and 200 occurrences but `capped: false`. Finally, a legal
direct-plus-longer path assigns the shared target its shortest layer but
prints it after the farther source on the longer edge, moving its selector
from column 25 to 73.

The exact correction boundaries and severities are in
`review-2026-08-22T19-04-09Z.md`. Three additive regressions fail
deterministically; fixtures and observed values are retained in
`evidence/review-correction-round3-2026-08-22.txt`.

## Round-4 correction — 2026-08-22

One P1 and two P2s, all reproduced before any edit. Three decisions worth
pinning and one question handed back.

**A DAG PATH IS NOT ANOTHER OCCURRENCE OF A CANONICAL EDGE.** Two per-run
memos carry it: the direct page already read for a `(Work, side)` branch, and
the greatest depth that branch has been expanded with. They are deliberately
not one global visited set — a Work legitimately appears on several edges, so
a blanket node cut would drop canonical relationships — and the depth memo
admits strictly greater, so a later SHORTER path carrying more depth still
expands. Occurrences count RENDERED edges only. Path-local cycle detection is
unchanged.

**THE CAP IS DISCLOSED AT THE EQUALITY BOUNDARY.** `room <= page`, not
`room <`. When the remaining allowance and the branch page stop a branch
together, the view is full and no later branch can admit a row; calling that
ordinary paging would hide it.

**THE LAYERED FORM DECLINES RATHER THAN MOVING AN ENDPOINT.** A legal DAG can
reach a Work directly and by a longer path, and shortest-path layering then
puts the target left of its source — a row that cannot run left to right
without moving the selector or overlapping the arrow. The form returns None
and the graph falls to adjacency. Losing the layout is honest; moving a
selector is not, because a column is a property of the Work.

That forced a second decision: the adjacency form's own arrow column had to
become uniform, or declining would have moved the defect into the fallback.
What each form promises is now written down — the adjacency form aligns
targets with targets and sources with sources, and does not claim one offset
per Work, because it has no layer to derive one from.

**OPEN, FOR THE REVIEWER.** The other way to keep the wide form for a
shortcut graph is LONGEST-path layering, which makes every DAG edge monotonic
by construction. I did not take it: the approved contract says the center
sits between SHORTEST-path layers, and changing that is a contract question
rather than a rendering fix.

### Recorded

The first mutation run showed three halves of the shared-branch correction
masking one another — in the reported fixture the two paths arrive at the
same depth, so the depth memo alone suppresses everything the other two
guard. Three fixtures separate them now, two of them built on the
longer-then-shorter path the review requires to keep working.

## Independent round-four correction re-review — 2026-08-22

**Confirmed corrected:** repeated DAG paths no longer re-query or re-count
already rendered edges, the page/allowance equality boundary discloses the
full view, and a non-monotonic shortcut declines the shortest-layer renderer
for an aligned adjacency fallback. The fallback preserves the approved model;
no longest-path contract change is recommended.

**Observed — changes requested:** the new `walked` memo returns before the
only path-local cycle check. In a damaged graph, `cycle-b` is first expanded
through an unrelated path; a later equal-depth route reaches the same branch
with `cycle-a` in its ancestry, but the memo skips the edge that closes
`cycle-a <-> cycle-b`. The complete cycle is returned without `GraphInvalid`.

The exact correction boundary and severity are in
`review-2026-08-22T19-23-55Z.md`. One additive regression fails
deterministically; the topology and control flow are retained in
`evidence/review-correction-round4-2026-08-22.txt`.

## Round-5 correction — 2026-08-22

One P1, against the branch memo landed the round before.

**A BOUND AND A SAFETY CHECK ANSWER DIFFERENT QUESTIONS.** `state["walked"]`
answers whether a branch's descendants need expanding again; cycle closure is
a property of the current ancestry, which the memo does not carry. Adding the
memo therefore made a cache hit able to skip the path check, and every edge of
a cycle could be drawn while the response called itself valid.

The fix is a SECOND BOUNDARY, not a weaker memo: `_refuse_cycles` runs over
the edges the response actually contains. The drawn graph either has a cycle
or it does not, and no traversal order can change that. It is iterative and
bounded by the occurrence cap so a damaged store is reported rather than
crashed on, and it distinguishes ANCESTRY from "already finished" — a node
reached by two valid paths is ordinary in a DAG, and a naive visited-set
check would refuse the commonest shape in this repository's own graph.

**THE PATH-LOCAL CHECK IS KEPT, AND ITS VALUE IS NOW A DIFFERENT ONE.** It no
longer changes the answer. What it does is refuse at the first re-entry
instead of walking the whole occurrence budget round a loop. That is work not
done, so it is witnessed by a watcher rather than by an assertion about the
response.

**A CYCLE OUTSIDE THE DRAWN GRAPH IS NOT REPORTED.** If the closing edge was
cut by the cap or a branch page, the graph as rendered is acyclic; refusing
over an edge the response does not contain would be a different kind of lie
from the one just fixed.

### Recorded

The first mutation run left two guards unwitnessed — the new refusal's
message, because every text assertion was being satisfied by the path-local
check, and the path-local check itself, because the new boundary catches the
same cycles. Both have their own case now. Two of my first fixtures were also
wrong about their own topology and were corrected rather than kept.

## Independent round-five correction re-review — 2026-08-22

**Confirmed corrected:** the admitted-edge check makes cycle validity
independent of the branch memo's traversal order, accepts ordinary DAG
diamonds, names a real closing edge, and preserves the fast path-local guard.
The corrected focused baseline is 43/43.

**Observed — changes requested:** the path-local guard examines each fetched
sibling before the occurrence-cap admission check. An earlier sibling can
fill the cap through its descendants; a later closing sibling then raises
`GraphInvalid` even though it cannot enter the returned edge set. The retained
fixture reaches exactly 200 occurrences and should disclose one omitted
direct edge, but instead reports a cycle outside the graph it would draw.

The exact correction boundary and severity are in
`review-2026-08-22T19-42-55Z.md`. One additive regression fails
deterministically; topology and output are retained in
`evidence/review-correction-round5-2026-08-22.txt`. Decide cap admission
before path-local inspection for a new edge; keep `_refuse_cycles` over all
edges actually admitted.

## Round-6 correction — 2026-08-22

One P1, against the ordering I left in place while adding the round-5 cycle
boundary.

**A BOUND DECIDES WHAT IS IN THE RESPONSE; EVERY OTHER CHECK COMES AFTER IT.**
For an edge not already drawn, cap admission is settled first: with no
occurrence remaining, the branch discloses the cap and the exact remaining
direct omission and returns, without inspecting that edge for a cycle and
without recursing through it. The path-local guard then applies only to an
edge that WILL be in the response — or one already in it, which is part of
the admitted graph either way — so refusing over it invents nothing.

That is the round-5 rule enforced rather than merely stated: refusing over an
edge the response does not contain is the same lie as hiding one it does,
pointing the other way. I wrote the rule and then left the fast guard running
in front of the check that implements it.

### Recorded

A mutation that moves cap admission ahead of the `drawn` test passed green at
first. It reintroduces round four's finding from the other side — a branch
revisited after the allowance is spent would report its own rendered edges as
hidden — and nothing in the suite reached it, because the round-4 fixtures
never approach the cap. The new case sizes the shared branch at `cap - 4` so
the revisit lands with the allowance exactly exhausted.

## Independent round-six correction re-review — 2026-08-22

**Confirmed corrected and signed off for the foundation slice:** cap
admission now precedes ancestry inspection for a previously unseen edge, so
an edge excluded from the response becomes an exact omission rather than an
invented cycle refusal. Already-rendered edges still reach the fast path-local
guard without consuming another occurrence, and `_refuse_cycles` remains the
final boundary over the admitted graph.

All 47 focused cases pass independently, including the retained cap-cut
cycle and the correction's already-drawn and exhausted-cap cases;
`git diff --check` is clean. The exact scope and verification are recorded in
`review-2026-08-22T19-57-01Z.md`.

This closes review of the bounded projection and pure-renderer foundation,
not W4996 as a whole. Console wiring, navigation, resize/Back behavior, PTY
coverage, and the `ROW_DEEPER` depth-frontier slice remain pending.

## Console slice — 2026-08-22

**SELECTION IS AN IDENTITY.** `graph_anchor` holds a Work id, or a branch key
for a token, and the row is derived from it. A row index means a different
Work after a depth change, a branch expansion or a refresh — the drift the
Jobs table already forbids. Two branches of one Work are two different things
to open, which is why a token's key names its side as well as its Work.

**ROWS ARE DERIVED, NOT REMEMBERED.** Keys act on the graph rather than on
the last paint. A handler reading a cached row list does nothing before the
first render and something stale after a resize; deriving is only sound
because row order and identity are width-independent, which the pure renderer
already guarantees.

**THE TWO ABSENCES KEEP THEIR OWN KEYS.** `frontier` reports what the DEPTH
bound cut off and `omitted` what a BRANCH PAGE cut off. Enter widens a page;
`+` lifts the depth. On a depth-frontier token Enter says so rather than
widening a page, because a plausible action on the wrong token is worse than
none.

**RE-ANCHOR AFTER THE ACT.** A depth reduction can remove the selected Work,
and the ruling returns selection to the center when it does. Waiting for the
next key or paint would leave the console pointing at a Work it is not
showing.

### Recorded

The `_nav_capture` dict copy is UNWITNESSED. Branch expansions are the first
dict in navigation state, and a shared one would let widening a branch after
Back rewrite the frame the operator came from — but every path that captures
the map also replaces it with a fresh one, so no reachable sequence exercises
it today. It stays as defence for the next slice, named rather than counted.

### For the approver

The old flat page's Enter performed a deliberate cross-team drill-through:
it unwound the navigation stack and re-rooted the Jobs tree at the far Work,
rebuilding that Work's own ancestry (W292 round-1 [P1], R105). The approved
contract replaces Enter with recentering and states that it does not jump to
the Jobs table, so that capability is no longer reachable from `[b]`. The
change is authorized; the loss is named here rather than absorbed. Restoring
it would need a key and a line in the contract, which is a ruling rather than
an implementation choice.

## Independent console-slice review — 2026-08-22

**Confirmed P1:** navigation is by rendered edge row rather than the approved
unique-Work traversal. A shared DAG Work appears on consecutive canonical-edge
rows, but `_graph_anchor_index` always resolves its Work-ID anchor to the first
appearance. `j` therefore moves to another row with the same identity and the
post-action re-anchor resolves to the first again. Selection is trapped and
cannot reach the next Work. The retained regression separates the identities
with a downstream tail and fails at `src/baton_work/tui/app.py::_handle_graph`.

**Confirmed P2:** a shared branch first reached at the depth boundary records a
`frontier` count, then a later shortcut reaches that branch with more remaining
depth and renders its outgoing edge without clearing the count. The response
therefore paints `[+1 deeper dependents]` for a canonical edge already on
screen. A frontier is exact disclosure of what depth hid, so this is false
graph state rather than harmless duplication.

**Confirmed P2 / incomplete acceptance:** search results return through
`_search_mode_key` before the table's `b` handler and have no local `b` case.
The approved verification boundary explicitly requires opening from table and
search; a selected search result remains on the search page.

The implementer's other named omissions also remain open: the complete PTY
matrix and the TUI operating guide. The canonical `detail work=W6175` response
at snapshot 6232 independently confirms both live incoming edges, W2845 and
W4996, plus outgoing W4303 and W4615. The installed c529b28 TUI still paints
the pre-rollout flat relationship page, so it cannot verify this unshipped
source slice; the authority projection does verify the acceptance topology.

Three additive regressions are retained. Independent focused result is 58
passed, 3 failed; exact evidence is
`evidence/review-console-slice-2026-08-22.txt` and the verdict is
`review-2026-08-22T20-51-17Z.md`.

## Console slice, corrected — 2026-08-22

**MOVEMENT AND PAINTING ARE TWO LISTS.** `j`/`k` traverse one unique-node
order; the selection attribute is drawn on every appearance of the selected
id. The contract says both, and serving them from the same row list trapped
selection on a shared DAG Work — one row per canonical edge means consecutive
rows carry the same id, so stepping by row never moved the anchor and the next
key started over.

**A BOUND MUST DESCRIBE WHAT IS ON SCREEN.** A depth-frontier entry recorded
when a visit ran out of depth survived a later shorter path that drew the
branch's edges, so the graph claimed a dependent was hidden while showing it.
Expansion clears the entry now. This is the same rule the shared-branch
omissions established two rounds ago, applied to the field added in the
console slice — the lesson did not travel with the new code, which is worth
recording as its own kind of mistake.

**ENTRY IS FROM THE TABLE AND FROM SEARCH.** Search mode is dispatched before
the table's key handling, so the binding had to exist in both places; it goes
through one `_open_graph`, so the frame, the depth and Back are identical
wherever the operator started.

### Recorded

A mutation rewrote one of my own fixtures. My frontier case put the shortcut a
hop further out than the reported topology, so the branch never recorded a
frontier and the assertion of absence was vacuously true. It now uses the
reported shape at the depth that exercises it, and proves the token IS drawn
one depth shallower — otherwise the case is about a token that never existed.

## Independent corrected-console re-review — 2026-08-22

**Confirmed corrected:** movement now traverses distinct Work/token keys while
painting every repeated occurrence of the selected Work, so shared-DAG rows no
longer trap `j`/`k`. Search-mode `[b]` enters through the same `_open_graph`
path and universal navigation frame as the table entry.

**Observed — changes requested:** depth-frontier truth still depends on DAG
edge order. The correction clears an existing `frontier[key]` when a later
shorter path expands the branch. In the symmetric ordering, however, the
older direct shortcut expands the branch first and draws its outgoing edge;
a later longer path reaches that same Work at `remaining == 0` and blindly
adds `frontier[key]` again before consulting the branch-expansion memo. The
response therefore draws `shared --blocks--> leaf` and simultaneously reports
one deeper dependent hidden from `shared`.

The exact P2 topology and failing regression are retained in
`review-2026-08-22T21-21-32Z.md` and
`evidence/review-corrected-console-round2-2026-08-22.txt`. Frontier disclosure
must be independent of which valid path was created first: a depth-bound visit
cannot add a frontier for a branch already expanded anywhere in the returned
graph.

The original 65 focused cases remain green; the retained case makes the file
65 passed, 1 failed. Full PTY acceptance and the operating guide also remain
pending, so W4996 is not ready for whole-presentation sign-off.

## Order-independent frontier, PTY matrix, operating guide — 2026-08-22

**A BOUND'S DISCLOSURE CANNOT DEPEND ON EDGE CREATION ORDER.** Clearing a
frontier entry when a later path expands a branch fixed longer-first only;
with the shortcut older the branch is expanded first and a later, longer path
recorded a frontier for edges already drawn. The depth-bound visit consults
the same memo the expansion sets, so both orders are covered by two mechanisms
that agree — and the regression asserts the two orders give the SAME answer
rather than asserting each on its own, because "each direction separately" is
the shape that let this survive a round.

**THE PTY MATRIX EARNED ITS COST IMMEDIATELY.** The console exited 1 on a
30-column terminal: `_graph_row_key` assumed every row carried a Work, and the
stacked renderer's presentation rows carry none by design. Every focused case
passed while that was true, because they run at widths where the layered form
fits — and the narrow REFUSAL they assert is a different boundary from the
narrow FALLBACK. A suite that never reaches a fallback cannot report that the
fallback is broken.

**ONE PTY CASE IS DELIBERATELY NOT THE OBVIOUS ONE.** The narrow refusal needs
a terminal narrower than one complete selector, and the console's own table
cannot start at such a width — it exits before the graph is reached. So the
refusal stays asserted where it can be measured, and the PTY case asserts the
boundary a real operator actually reaches. Testing the reachable thing and
saying why is better than a case that passes for a reason nobody can act on.

## Independent whole-presentation review — 2026-08-22 (baton.codex)

**Confirmed:** the symmetric frontier correction is order-independent without
silencing a real frontier; the 11-case PTY matrix exercises the approved
terminal boundary and the stacked fallback no longer crashes; and the TUI
operating guide matches the implemented dependency-only graph. Independent
focused plus PTY verification is 80/80.

**Changes requested — P2 test-owned residue:** the new stacked-row focused
case calls `tempfile.mkdtemp()` directly and never removes or registers the
root. Repeated executions leave empty `/tmp/tmp*` directories, reproducing the
fixture-residue class the repository explicitly guards. Use pytest's owned
`tmp_path` (as the neighboring console cases do), retain the behavioral case,
and prove repeated execution leaves zero new roots. Exact paths and evidence
are in `review-2026-08-22T21-48-17Z.md` and
`evidence/review-whole-presentation-2026-08-22.txt`.

## The leaked temporary root — 2026-08-22

**A CASE THAT OPTS OUT OF A MANAGED FIXTURE IS NOT COVERED BY IT, AND THE
FIXTURE CANNOT TELL.** The case I added to pin the stacked-path crash minted
its own `tempfile.mkdtemp()` because it needed a path and adding the argument
was one edit more. Every run left an empty root — the residue W2907 exists to
stop, reintroduced by one case that bypassed the convention every case around
it follows.

It takes `tmp_path` now, and a guard asserts this file's own source mints no
temporary root. **Asserting the source rather than counting `/tmp` entries is
deliberate:** a count depends on every other process and suite in the run, so
it would be flaky in exactly the direction that teaches people to ignore a
failure. The regression was a property of the file, so the file is what is
checked — and the guard reads everything before its own definition, because it
necessarily names the calls it forbids.

**Recorded:** two turns ago I caught the identical mistake in a v12 suite by
running its gate under a residue bracket. This one needed a reviewer, because
the v11 suite has no bracket — which is the useful difference between the two
lines, not a difference in how carefully I wrote them.

## Independent residue-correction re-review — 2026-08-22

**Confirmed corrected and whole presentation signed off:** the stacked-path
regression now uses pytest's owned `tmp_path`; two consecutive focused runs
leave the exact `/tmp/tmp*` inventory unchanged. The focused and PTY matrix is
81/81, and whitespace checks are clean. The source scan is retained as
defence-in-depth; sign-off rests on the owned fixture and the measured runtime
residue bracket.

This closes the sole P2 from `review-2026-08-22T21-48-17Z.md`. The bounded
projection, ASCII renderers, console navigation, search entry, resize/Back,
frontier/overflow disclosure, PTY acceptance and operating guide were already
accepted by that review and remain green. Exact independent evidence is in
`review-2026-08-22T22-09-23Z.md` and
`evidence/review-residue-correction-2026-08-22.txt`.
