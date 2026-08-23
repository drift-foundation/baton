# Progress

Implementer: `baton.claude`. Canonical Baton Work: W4996.

**State: awaiting review of the FIRST SLICE. This Work is not finished.**
The canonical model and the rendering are landed and verified. The CONSOLE IS
NOT WIRED: `[b]` still opens the old flat links page, and none of the
navigation half of the contract exists yet. The Work is passed back rather
than held so the model and the layout can be reviewed before the keys are
built on them.

Saying that plainly matters here: the approved contract is long, and 19 green
cases could otherwise be read as covering it.

## What landed

### `projection.dependency_neighborhood`

One bounded read under `_read_snapshot`, which is the whole reason it exists:
`links` is a one-hop public response and is not itself snapshotted, so a
console calling it recursively would be unbounded in fan-out AND could combine
two authority states between hops — drawing a graph of a database that never
existed at any instant.

It changes no dependency semantics. `blocked_by` is still EVERY recorded
upstream edge including a satisfied one, `blocks` is still only the live
downstream consumers, and both keep edge `created_seq` order. A regression
asserts parity with `links` in both directions and then closes a consumer to
prove the asymmetry survives, because a renderer that widened either side
would be inventing edge lifetime.

Bounds, all disclosed rather than silent:

- depth 1..3, refusing anything outside — including `True` and `2.0`, which
  are `int`-ish enough to slip through a naive check;
- four neighbours per branch, with the exact omitted count per `(node, side)`
  branch key, and paging one branch expanding only that branch;
- a 200-occurrence cap that says it was reached and keeps the exact direct
  counts it did not draw. It never guesses at a hidden total — an invented
  number is worse than a bound.

Expansion is DIRECTIONAL and does not turn corners: upstream follows
`blocked_by` and downstream follows `blocks`, and neither walks from a far
node into that node's other side. Those are a different Work's neighbourhood
and are reached by recentering — a graph that turned corners would grow to the
component and stop being about the center. There is a regression for it.

A cycle or a missing endpoint raises `GraphInvalid` naming the exact edge.
Worth recording: the authority already refuses a dependency cycle at
insertion, so that branch is reachable only from damaged data — which is
exactly when a view must not paper over it by drawing a smaller graph that
looks complete.

### `tui/graph.py`

Pure: one neighbourhood response and a width in, rows out. No curses, no
store, no console state — which is what lets the layout be tested at every
width without a terminal, and why the console will have no graph state to
invent.

Three renderers over ONE model. The layered form puts every occurrence of the
center token at the same column so the eye follows one vertical line; the
adjacency fallback drops that column; the stacked fallback puts source, arrow
and target on three rows. A regression asserts the SET of Work is identical at
every width — a narrow terminal loses layout, never a relationship — and
another asserts the row order is identical too, because `j`/`k` that meant a
different Work after a resize would be worse than no keys.

Everything is ASCII: `--blocks-->` with the arrowhead at the consumer, so
direction survives a pipe, a log paste and a screen reader. A terminal too
narrow for one complete selector REFUSES rather than clipping an identity.

## Verification

- `tests/work/test_w4996_dependency_graph.py` — **19 cases**, listed in
  `PLAN.md` items 2 and 3.
- `pytest -n auto -m "not serial" tests/work` — **2902 passed**.
- `pytest -m serial tests/work` — **52 passed**.
- Whitespace-damage check clean.

No existing case needed changing: the projection is additive and the public
`links` response is untouched, which a regression asserts directly.

## Not started

- `_links_rows`/`_render_links` still paint the old flat page and `b` still
  opens it;
- `graph_center`, `graph_depth`, the Work-ID/token selection anchor and the
  branch expansion map have not joined `NAV_STATE_FIELDS`;
- Enter-recenter, overflow Enter, `+`/`-` depth, selection after depth
  reduction or refresh, resize behaviour and exact Back restoration;
- the console and PTY regressions for all of the above;
- plan item 4: the TUI operating guide.

## Review notes

Two things worth a second opinion:

1. **The layered form draws one row per relationship**, with the center
   repeated in its column, rather than a single horizontal chain per path. A
   one-in/one-out neighbourhood therefore renders as two rows rather than the
   contract's one-line example. I chose that because a fan-out of six as one
   chain per path either duplicates the upstream side six times or needs
   box-drawing to join them, and the contract forbids information in styling.
   The example's shape still reads left-to-right with the center between the
   sides; if the reviewer wants the literal single line for the 1:1 case, that
   is a small special case to add.
2. **`ROW_DEEPER` is defined but unused.** Depth-frontier tokens (`[+N deeper
   blockers]`, expanded with `+` rather than Enter) need the projection to
   report what the depth bound cut off, which it does not yet do — it reports
   only what a BRANCH PAGE cut off. That is a real gap in the contract's
   coverage, named here rather than left for the reviewer to find; it belongs
   with the console slice, since `+` is what opens it.

## Round 2 — the two P1s and the P2 (2026-08-22)

`review-2026-08-22T17-07-39Z.md`. All three reproduced before any edit; all
correct. Evidence: `evidence/correction-first-slice-2026-08-22.txt`.

**Still not started:** the console wiring, and the `ROW_DEEPER` depth-frontier
gap. The review does not treat either as landed, and neither is.

### What I had wrong

**The renderers drew edges the authority never held.** `_ordered` emitted one
entry per unique NODE and every renderer paired it with the CENTER, so a
depth-two chain drew an `A --blocks--> C` that does not exist and dropped the
`B --blocks--> C` that does. I wrote the module docstring claiming every
rendered relationship comes from the canonical projection, and then wrote
three renderers that ignored the projection's edges entirely — they used only
its nodes. The rows carry their real endpoints now.

**A stacked row selected a different Work than it displayed.** The consumer's
`work` sat on a row painting the CENTER token. My own first-slice note said
"one selectable row per relationship" — which was true — without checking that
the row shows the Work it selects.

**The cap did not bound materialization.** The direct edges were fetched in
full and sliced afterwards, so the bounded view allocated the whole fan-out.
It is a `COUNT(*)` plus an ordered `LIMIT` now.

### Tests — 24 (21 before, including the reviewer's two)

The reviewer's two are retained. Added: every DRAWN edge equals the
projection's own edge set across three centers, three depths and three widths;
every selectable row displays its own Work in every renderer; the cap actually
crossed with an exact omission; and the bounded read witnessed by watching the
rows the edge helper returns.

**That last one exists because the first mutation passed.** Memory has no
visible result — the same answer comes back either way — so asserting the
outcome would have left the correction unwitnessed. Each of the three
corrections now fails exactly the case that names it.

### Verification

- `tests/work/test_w4996_dependency_graph.py` — **24 passed**.
- `pytest -n auto -m "not serial" tests/work` — 2914 passed, 1 failed.
- `pytest -m serial tests/work` — 52 passed. Whitespace check clean.

### The one failure is W4615's

`test_one_drain_instant_samples_the_authority_clock_once` — a reviewer-added
case against my own W4615 correction. Passing the clock into settlement
samples it a SECOND time, so a clock that advances per call gives the two
events at one authority instant different timestamps. A real defect in that
Work, which is queued on `baton.impl` awaiting its own turn and was not
touched from here.

### State

**Awaiting re-review of the corrected model and rendering.**

## Round 3 — the three bounded-read and layout edges (2026-08-22)

`review-2026-08-22T18-07-47Z.md`, three P2s. All reproduced before any edit;
all correct. Evidence:
`evidence/correction-first-slice-round2-2026-08-22.txt`.

**Still not started:** the console wiring and the `ROW_DEEPER` depth-frontier
gap. The review treats neither as landed and neither is.

### What I had wrong

**The bounded read was still unbounded, one caller up.** My round-2
correction changed `_dependency_edges` to `COUNT(*)` plus an ordered `LIMIT`
and then handed it the raw expansion value, so a 250-row expansion of a
240-row branch fetched all 240 and only the Python loop stopped drawing. I
moved the defect rather than removing it.

**The wide form was an adjacency list with indentation.** `_layered`
justified every row against the CENTER's column whatever the depth, so in
`A --blocks--> B --blocks--> C` the node B was a target at the center's right
edge on one row and a source at column zero on the next. One node in two
columns is exactly what "layered" is supposed to rule out.

**Overflow tokens sat beside their owner rather than in their branch.** The
center's `[+N blockers]` came after the center — between it and the blockers
it belongs to — and `[+N dependents]` came before any dependent was drawn.

### Changed

The SQL row limit is `min(page, occurrence_cap - occurrences)`, and `capped`
is recorded when the ALLOWANCE rather than the page is what truncated a
branch — the loop can no longer discover that for a branch the SQL already
trimmed, and which bound stopped it is the difference between "press Enter
for more" and "this view is full".

`_columns` gives one start offset per Work from its shortest-path layer, and
every row draws from its source's column with the arrow reaching the
target's. A column is a property of the node now, not of the row.

`_ordered` splits into `_edge_rows`, `_tokens` and `_branch_anchor`: a token
follows the last VISIBLE member of the branch it opens, and the list is
rebuilt once rather than inserted into while its indices move. A branch with
nothing visible takes the slot the branch itself would occupy — after the
owner going downstream, before it going upstream. In the wide form the token
takes its SIBLINGS' column, one layer out, because aligning with the owner
reads as something about the owner.

### Two cases added, and a mutation is why

M3 — anchoring every token to its owner's row — failed the reported
DOWNSTREAM case and not the upstream one, and the reason is structural. For
the center's upstream branch, "after the last visible blocker" and
"immediately before the center" are always the same slot, because the
center's blockers are always the rows just above it. So the reported upstream
case cannot distinguish the branch rule from an owner-relative one. A
two-node depth-one layer is where they diverge, and that is the new case. A
second new case witnesses the token's column, which nothing had asserted.

### One assertion of mine was corrected, deliberately

`test_an_overflow_token_names_its_exact_count_and_side` asserted the token is
"not at the end of the page", which encoded the OLD placement — under the
corrected rule a center whose only branch is downstream has its token last,
and the old assertion refused it. It states the exact rule now. Changing a
test to accept a correction is worth saying out loud; the assertion was
weaker than the property it named.

### Verification

- `tests/work/test_w4996_dependency_graph.py` — **30 passed** (28 before).
- `pytest -n auto -m "not serial" tests/work` — **2925 passed, 0 failed**.
- `pytest -m serial tests/work` — 52 passed. The whole v11 suite is green.
- `tools/codex-event-bridge npm test` — 297/297. `acp-baton-bridge` — 55/55.
- Whitespace check clean. Four mutations, each fails the case that names it.

### The four v12 failures are not this Work's

W2929 reviewer cases from `review-2026-08-22T18-51-48Z.md`, which landed
while this turn was running. W2929 is queued on `baton.impl` for its own turn
and nothing here reaches `v12`.

No projection version change: `capped` and `omitted` already existed and only
their values are now correct.

### State

**Awaiting re-review of the corrected model and rendering**, before console
keys are wired onto them.

## Round 4 — the shared branch, the tie, and the shortcut (2026-08-22)

`review-2026-08-22T19-04-09Z.md`, one P1 and two P2s. All reproduced before
any edit; all correct. Evidence: `evidence/correction-round4-2026-08-22.txt`.

**Still not started:** the console wiring, navigation, resize and Back
behaviour, PTY coverage, and the `ROW_DEEPER` depth-frontier gap.

### What I had wrong

**A shared DAG branch invented omissions for edges already on screen.**
`seen_edges` suppressed the duplicate rows and nothing else was conditional
on it, so the occurrence increment and the recursion ran on every path. The
second walk spent the cap on drawn edges and then overwrote the branch's
complete result with an omission for dependents the operator could see. A
bound that describes something other than the rendered graph is worse than no
bound.

**The tie was silent.** My round-3 cap flag fired only when `room < page`.
When they tie, the branch is page-truncated and allowance-truncated at once —
and the view is full, so no later branch can admit a row.

**A shortcut edge moved a Work out of its column.** A legal DAG reaches a
Work directly and by a longer path; shortest-path layering puts it left of
that longer path's source, so the row ran right to left and the renderer
clamped the gap and painted the selector in a second column. That is the
exact rule my round-3 correction recorded, broken by the case it did not
consider.

### Changed

Two per-run memos, deliberately not one global visited set — a blanket node
cut is not equivalent, because a Work legitimately appears on several edges.
`fetched` reuses a branch's direct page; `walked` records the greatest depth
it has been expanded with, strictly greater admitting, so a later shorter
path carrying more depth still expands. Occurrences count rendered edges
only. `_expand_dependency` was split from `_expand_branch` so that "this
branch was actually expanded" is observable.

The cap is disclosed at `room <= page`.

The layered form DECLINES a graph it cannot lay out monotonically and hands
it to adjacency, which draws the same edges with the same endpoints and no
layer columns. Losing the layout is honest; moving a selector is not. And the
fallback had to be fixed too, or declining would have moved the defect: its
source field was sized to whatever token it held, so one Work landed at two
offsets for a reason unrelated to the graph. It is padded now, and what the
form does and does not promise is written down.

### The first mutation run found three halves masking one another

M1, M2 and M3 all passed green against the reported fixture, because there
the two paths reach the shared node at the SAME depth — the depth memo stops
the second traversal outright, so neither the re-query nor the re-count can
happen. Three corrections, one case, and the case could not tell them apart.

Three fixtures separate them now, and two use the path the review explicitly
requires to keep working: a longer path walked first, then a shortcut
carrying more depth, by which time the branch's own rows have consumed most
of the allowance. The third watches `_expand_branch`, because the memo's
whole effect is work NOT done.

### Verification

- `tests/work/test_w4996_dependency_graph.py` — **36 passed** (33 before).
- `pytest -n auto -m "not serial" tests/work` — **2931 passed, 0 failed**.
- `pytest -m serial tests/work` — 52 passed.
- `tools/codex-event-bridge npm test` — 297/297. `acp-baton-bridge` — 55/55.
- Whitespace clean. Six mutations, each fails the case that names it.

### The three v12 failures are not this Work's

W2929 reviewer cases from `review-2026-08-22T19-11-31Z.md`, which landed
while this turn was running. W2929 is queued on `baton.impl` for its own turn
and nothing here reaches `v12`.

### State

**Awaiting re-review**, before console keys are wired onto the model.

## Round 5 — the memo could hide a cycle (2026-08-22)

`review-2026-08-22T19-23-55Z.md`, one P1, against the memo I added last
round. Reproduced before any edit; correct. Evidence:
`evidence/correction-round5-2026-08-22.txt`.

**Still not started:** console wiring, navigation, resize and Back, PTY
coverage, and the `ROW_DEEPER` depth-frontier gap.

**Closed by this review:** the round-4 renderer question. Declining the
shortest-path layered form for a non-monotonic shortcut and using the aligned
adjacency fallback is consistent with the approved contract; no longest-path
amendment is recommended.

### What I had wrong

`state["walked"]` answers "do this branch's descendants need expanding
again", which is a sound question — but cycle closure is a different one, and
it is a property of the ANCESTRY the memo does not carry. A node first
reached where its outgoing edge was ordinary, then reached again with the
other end of that edge among its ancestors, got a memo hit and returned
before anything compared the new path. Every edge of the cycle was drawn and
the response called itself valid.

### Changed

`_refuse_cycles(edges)` is a second boundary rather than a weakening of the
memo, which is what the review asks for. It runs over the edges the response
actually CONTAINS, so no traversal order can hide anything: the drawn graph
either has a cycle or it does not. It is iterative and bounded by the
occurrence cap, it distinguishes ancestry from "already finished" — a node on
two paths is ordinary in a DAG, and a naive visited-set check would refuse
the commonest shape in this repository's own graph — and it names the exact
closing edge.

The path-local check stays. It no longer changes the answer, but it refuses
at the first re-entry rather than walking the whole occurrence budget round a
loop on a damaged store.

A cycle whose closing edge was never admitted is deliberately not reported:
the drawn graph really is acyclic, and refusing over an edge the response
does not contain would be a different kind of lie.

### Two guards were unwitnessed on the first mutation run

M3 — the new refusal's message — passed green because every cycle case that
asserted on text was being refused by the PATH-LOCAL check, which names its
edge correctly. M4 — removing the path check — passed green because the new
boundary catches the same cycles.

So two cases exist for them: one drives the reviewer's own shape, where only
the admitted-graph check can fire; the other watches `_refuse_cycles` and
requires that a plain cycle never reaches it, with a second acyclic
neighbourhood proving the watch is not inert.

Two of my first fixtures were wrong and were corrected rather than kept — a
300-link chain whose loop could not be inside a depth-three view at all, and
a cycle-beyond-depth case whose closing edge was still outside the view at
depth three. The first was trying to witness "iterative", which is not
witnessable at this scale, so it became the diamond false-positive case
instead.

### Verification

- `tests/work/test_w4996_dependency_graph.py` — **43 passed** (37 before).
- `pytest -n auto -m "not serial" tests/work` — **2938 passed, 0 failed**.
- `pytest -m serial tests/work` — 52 passed.
- `tools/codex-event-bridge npm test` — 297/297. `acp-baton-bridge` — 55/55.
- Whitespace clean. Four mutations, each fails the cases that name it.

### The two v12 failures are not this Work's

W2929 reviewer cases from `review-2026-08-22T19-31-47Z.md`, which landed
while this turn was running, against the secret-lifetime and journal work I
landed there earlier today. W2929 is queued on `baton.impl` for its own turn
and nothing here reaches `v12`.

### State

**Awaiting re-review**, before console keys are wired onto the model.

## Round 6 — the guard ran one step too early (2026-08-22)

`review-2026-08-22T19-42-55Z.md`, one P1. Reproduced before any edit;
correct. Evidence: `evidence/correction-round6-2026-08-22.txt`.

**Still not started:** console wiring, navigation, resize and Back, PTY
coverage, and the `ROW_DEEPER` depth-frontier slice.

### What I had wrong

I pinned the rule in round five — a cycle whose closing edge was cut by the
cap is not reported, because the graph actually returned is acyclic — and
then left the fast path guard running in front of the cap check that
implements it. An earlier sibling's descendants can spend the allowance
between the branch fetch and a later sibling's turn, so a closing edge raised
`GraphInvalid` even though the response would not have contained it.

Refusing over an edge the response does not contain is the same lie as hiding
one it does, in the other direction.

### Changed

Cap admission is decided first for an edge not already drawn: with no
occurrence left, the branch discloses the cap and the exact remaining direct
omission and returns, without inspecting that edge for a cycle and without
recursing through it. The path guard then applies to an edge that will be in
the response, or is already in it — both are edges the operator can see.
`_refuse_cycles` is unchanged.

### A mutation passed green, and that is why there are three new cases

Making cap admission apply to already-drawn edges as well reintroduces round
four's finding from the other side: a branch revisited after the allowance is
spent would report its OWN rendered edges as hidden. Nothing in the suite
reached it, because the round-4 shared-branch fixtures never approach the
cap. The new case sizes the shared branch at `cap - 4` so the revisit happens
with the allowance exactly exhausted.

The other two: an already-drawn edge still meets the fast guard, watched
through `_refuse_cycles`; and a cycle edge the cap omits is disclosed rather
than refused, with the final boundary run over the returned edges to say so
rather than the case merely observing that nothing raised.

### Verification

- `tests/work/test_w4996_dependency_graph.py` — **47 passed** (44 before).
- `pytest -n auto -m "not serial" tests/work` — **2942 passed, 0 failed**.
- `pytest -m serial tests/work` — 52 passed.
- `tools/codex-event-bridge npm test` — 297/297. `acp-baton-bridge` — 55/55.
- Whitespace clean. Three mutations, each fails the cases that name it.

### The one v12 failure is not this Work's

A W2929 reviewer case from `review-2026-08-22T19-49-19Z.md`, which landed
while this turn was running, against the pinned/live secret registers I added
there earlier today. W2929 is queued on `baton.impl` for its own turn.

### State

**Awaiting re-review**, before console keys are wired onto the model.

## The console slice — 2026-08-22

`review-2026-08-22T19-57-01Z.md` **signed off the first slice** — the bounded
projection and the pure renderer — and named the next one exactly. This turn
implements it. Evidence: `evidence/console-slice-2026-08-22.txt`.

The signed-off model was revalidated before anything was built on it: 47
focused cases green against the tree as it stood.

### What landed

**`ROW_DEEPER` finally has something to report.** I named that gap myself in
the first slice rather than leave it to be found: depth-frontier tokens need
the projection to say what the DEPTH bound cut off, and it reported only what
a BRANCH PAGE cut off. `dependency_neighborhood` gains `frontier`, an exact
direct count per branch key, taken at the point the walk declines to expand
and with the bounded reader at limit zero — a COUNT and no rows, so naming
the absence materializes nothing. It is separate from `omitted` because the
two are opened by different keys, and one token for both would make the key
a guess.

**The console.** `[b]` opens the neighbourhood; the flat page is deleted
rather than left behind a flag. `graph_center`, `graph_depth`, `graph_anchor`
and `graph_expanded` join `NAV_STATE_FIELDS`, so Esc restores center, depth,
selection and branch pages together. Selection is an identity, never a row
index. Enter recenters — one frame, depth kept, pages reset, selection
becomes the new center — or widens exactly one branch page; on a
depth-frontier token it says `+` is the key rather than doing something
plausible. Re-anchoring runs after the act as well as before it, because a
depth reduction can remove the selected Work and the ruling says selection
returns to the center when it does.

Rows are DERIVED on demand rather than read from the last paint: a handler
reading a cached list would do nothing before the first render and something
stale after a resize. That is only sound because row order and identity are
width-independent, which the first slice already asserts.

### One piece of shared machinery changed, and it is recorded

`_nav_capture` copied lists and not dicts. Harmless while no navigation state
was a dict; branch expansions are one. **The dict copy is UNWITNESSED and I
could not witness it** — every path that captures the expansion map also
replaces it with a fresh one, so no reachable sequence lets a live mutation
reach a frame still on the stack. Defence for the paths the next slice adds,
named rather than counted as covered.

### Nine existing cases moved, each inspected

None bulk-edited; each says in its own words what the contract changed and
why its own subject survives. W17's empty state is kept VERBATIM — that is
why the console still prints it.

**A capability is gone and the approver should see it named.** The old page's
Enter performed the deliberate cross-team drill-through: unwind the stack,
re-root the Jobs tree at the far Work, rebuild that Work's ancestry (W292
round-1 [P1], R105). The approved contract replaces Enter with recentering
and says explicitly that it does not jump to the Jobs table, so that jump is
no longer reachable from `[b]`. Authorized — but not obviously intended as a
removal, and I did not invent another key for it, because that is not mine to
choose.

### Verification

- `tests/work/test_w4996_dependency_graph.py` — **58 passed** (47 before).
- `pytest -n auto -m "not serial" tests/work` — **2953 passed, 0 failed**.
- `pytest -m serial tests/work` — 52 passed.
- `tools/codex-event-bridge npm test` — 297/297. `acp-baton-bridge` — 55/55.
- Whitespace clean. Six mutations; five fail the cases that name them and the
  sixth is the unwitnessed dict copy above.

Getting M1 to bite took two fixture corrections, both recorded: a
downstream-only chain does not separate a row index from an identity, and
neither does one where the depth-frontier token happens to occupy the slot
its own edge will take.

### Still not done

- Plan item 4: the TUI operating guide.
- PTY coverage beyond what the existing suites already drive. Four cases do
  exercise the new page through a real pty, but the contract's full list is
  not written.
- Opening the graph from the SEARCH results page: `[b]` is wired from the
  table only, so "open from table and search" is half done.

### The one v12 failure is not this Work's

A W2929 reviewer case that landed while this turn was running.

### State

**Awaiting review of the console slice.**

## The console slice, corrected — 2026-08-22

`review-2026-08-22T20-51-17Z.md`, one P1 and two P2s. All reproduced before
any edit; all correct. Evidence:
`evidence/correction-console-slice-2026-08-22.txt`.

**Still not done:** the full PTY matrix and plan item 4's operating guide.
I named both when I passed the slice and the review names them as part of
what must come back; they are not done here either.

### What I had wrong

**Repeated Work rows trapped selection.** The renderer keeps one row per
canonical edge, so a shared DAG Work occupies consecutive rows. Movement
stepped by ROW while the anchor resolved to the Work's FIRST appearance, so
`j` from a shared Work landed on another row with the same id, the anchor did
not change, and the next key started over. Selection was stuck permanently.

The contract said what to do and I read half of it: `j`/`k` traverse one
UNIQUE-NODE order, and every appearance of the selected id is painted. Those
are two lists, and I served both from the rows.

**A shortcut left a false depth-frontier token.** `frontier[key]` is recorded
when a visit runs out of depth, and a later shorter path may reach the same
branch with depth to spare and draw its edges. Nothing cleared the entry, so
the graph claimed a dependent was hidden by depth while drawing that exact
edge — the same defect class as the shared-branch omissions two rounds ago,
in the field I added this slice.

**The search entry was absent.** Search mode is dispatched before the table's
`b` case, so the key was a no-op there. I named this gap when I passed the
slice, which does not make it less of a defect.

### Changed

`_graph_keys` is the traversal order, distinct keys in first-appearance
order; painting is unchanged. `_expand_branch` clears the frontier entry for
a branch it expands. `_search_mode_key` opens the graph through the same
`_open_graph` the table uses.

### A mutation rewrote one of my fixtures

M4 — keeping the frontier entry through an expansion — failed only the
reviewer's case. Mine had put the shortcut a hop further out, so the shared
branch never recorded a frontier at all and its assertion of absence was
vacuously true. It uses the reported topology at the depth that exercises it
now, and asserts the token IS drawn at depth one, so the case is about the
clearing rather than about a token that never existed.

### Verification

- `tests/work/test_w4996_dependency_graph.py` — **65 passed** (58 before).
- `pytest -n auto -m "not serial" tests/work` — **2960 passed, 0 failed**;
  serial 52; codex-event-bridge 316/316; acp-baton-bridge 55/55; v12
  239/239; whitespace clean.
- Six mutations, each fails the cases that name it.

**Every gate in the tree is green**, with no failure belonging to another
Work.

### State

**Awaiting re-review**, with PTY acceptance and the operating guide still to
come before whole-presentation sign-off.

## The order-independent frontier, the PTY matrix, and the guide (2026-08-22)

`review-2026-08-22T21-21-32Z.md`, one P2 plus the two remaining items it
named. Evidence: `evidence/correction-frontier-and-pty-2026-08-22.txt`.

### What I had wrong

My previous correction fixed ONE traversal order. Clearing the frontier entry
when a later path expands a branch handles longer-first; with the shortcut
older, the branch is expanded first and a later, longer path reaches it at
`remaining == 0` and recorded a frontier for edges already drawn.

A depth-bound visit now consults the same memo the expansion sets, so a branch
already expanded in this response is never a frontier whichever path arrived
first. The added case asserts the two orders AGREE rather than asserting each
separately — two corrections were needed and each covered one direction, which
is exactly the shape that made this survive a round.

### The PTY matrix found a crash the focused suite could not

**The console died on a 30-column terminal.** `_graph_row_key` assumed every
row carried a `work`, and the stacked renderer's presentation rows carry none
by design — its own documented rule is that source, arrow and target go on
three rows and only the row displaying its own Work is selectable. Reaching
that fallback raised `KeyError` and exited 1 with a traceback, while every
focused case passed: they drive the console at widths where the layered form
fits, and the narrow REFUSAL they assert is a different boundary from the
narrow FALLBACK.

Corrected, pinned in the focused suite at the width that reaches the stacked
form, and mutation-checked there.

One PTY case is deliberately not the one I first wrote: the narrow REFUSAL
needs a terminal narrower than one complete selector, and the console's own
table cannot start at such a width. The refusal stays where it can be
measured, and the PTY case asserts the boundary a real operator reaches.

The matrix drives the centre through SEARCH rather than by counting table
rows, because the table orders by readiness and priority — which is the thing
these cases vary — and searching also exercises the required entry path.

### The operating guide

`docs/BATON-WORK.md` gains **The dependency graph**: scope, the drawn shape,
every bound with the token that discloses it, the key table, what Enter does
and does not do, the narrow-terminal fallbacks and the refusal, and the
damaged-store refusal.

### Verification

- focused **69 passed** (66 before); PTY **11 passed** (new).
- `pytest -n auto -m "not serial" tests/work` — **2975 passed, 0 failed**;
  serial 52; codex-event-bridge 316/316; acp-baton-bridge 55/55; whitespace
  clean.
- Four mutations, each fails the cases that name it.
- v12 is 256/263; those seven are W2929 reviewer cases against the
  offer/claim slice I landed there earlier this session.

### State

**Ready for whole-presentation review.** Every item the last review named as
outstanding is now done.

## The leaked temporary root — 2026-08-22

`review-2026-08-22T21-48-17Z.md` confirmed the frontier correction, the
eleven PTY scenarios and the operating guide complete at 80/80, and reported
one P2. Evidence: `evidence/correction-residue-2026-08-22.txt`.

### What I had wrong, and why it happened

The case I added LAST turn to pin the crash the PTY matrix found called
`tempfile.mkdtemp()` directly. The console helper takes a path and every
other console case receives pytest's managed `tmp_path`; I needed one, added
it inline rather than adding the fixture argument, and a case that bypasses
the managed mechanism is not covered by it — the mechanism cannot tell.

It is the same class of residue W2907 exists to stop, reintroduced by one
case that opted out of the convention around it. Two turns ago I found the
identical mistake in a v12 suite by running its gate under a bracket; this
one needed a reviewer, because the v11 suite has no bracket.

### Changed

The case takes `tmp_path`. And a guard asserts this file's own SOURCE mints
no temporary root — asserting the source rather than counting `/tmp` entries
deliberately, because a count is affected by every other process and suite in
the run and would be flaky in exactly the direction that teaches people to
ignore it. The guard reads everything before its own definition, since it
necessarily names the calls it forbids; a check that matched its own text
could never pass, and that had to be corrected before it was worth anything.
Mutation: restoring the `mkdtemp` call fails it.

### Residue bracket

Bare `/tmp/tmp*` roots: 39 before, 39 after the full non-serial suite (2976
passed) plus the PTY matrix (11 passed). Two consecutive focused runs of the
file alone likewise left zero.

The nine paths the review lists were LEFT IN PLACE — destructive cleanup of
paths outside this Work's own fixtures is an operator act, and the review
says so.

### Verification

- focused **70 passed** (69 before); PTY **11 passed**.
- `pytest -n auto -m "not serial" tests/work` — **2976 passed, 0 failed**;
  serial 52; codex-event-bridge 316/316; acp-baton-bridge 55/55; whitespace
  clean.
- v12 is 271/274; those three are W2929 reviewer cases against the
  offer/claim slice I landed there earlier this session.

### State

**Awaiting whole-presentation re-review.**
