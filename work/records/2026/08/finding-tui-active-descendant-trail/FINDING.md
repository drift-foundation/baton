# Finding: surface active descendant Jobs beneath visible roll-ups

## Observed — 2026-08-24

The live M2 graph had real implementation activity while its visible roll-ups
looked idle. W5 had no Handler and was blocked by its contained Jobs, while the
deeper W6631 leaf was claimed by `baton.claude` and its runtime reported
`working`. A user watching the campaign row had to expand or re-root the tree
and locate the leaf before learning that work was in progress.

The authority is correct: a parent's Handler and Phase belong only to that
parent and must not be borrowed from a descendant. The missing information is
a presentation link from the visible roll-up to the exact active leaf.

## Confirmed decision — 2026-08-24

Keep the established first three containment levels. When an active leaf lies
deeper than that visible window, render a vertical elision row and then the
exact active leaf beneath its nearest visible ancestor:

```text
W2  Design v12 isolated workers
  ↳ W3  Prove local isolated execution
    ↳ W5  Build OCI reference worker and adapter
      ⋮
      ↳ W6631  Materialize exact source…  baton.claude  working
```

Use `⋮` when the terminal can render it and `...` as the safe fallback. The
elision says that one or more containment levels were omitted; it is not a Work
row. The leaf identifies the real Work, Handler and runtime state. It never
changes or visually impersonates the ancestor's own Phase or Handler. Selecting
the leaf navigates to that Work. If the leaf is already among the ordinary
first-three-level rows, do not duplicate it.

Multiple active leaves below the same visible ancestor share one elision row
and produce multiple stable, navigable leaf rows. Active leaves below different
visible ancestors stay grouped beneath their respective ancestors. A large
project is expected to expose N concurrent workers; hiding all but a count would
recreate the debugging problem this feature solves. Normal scrolling, filtering
and viewport rules may bound what is simultaneously on screen, but the
underlying active-leaf list is not silently truncated.

This is presentation derived from canonical containment, claim and runtime
projection data. It changes no Work identity, Phase, Handler, dependency,
SQLite schema or protocol meaning. The same concept belongs in the eventual
v12 TUI even if its renderer is independently implemented.

Opening a Job makes that selected Job the contextual root of the Work view.
The renderer applies the same three-level window and active-descendant elision
relative to that new root, rather than continuing to spend vertical space on
its former ancestors. The breadcrumb records the navigation path. Back or
`Esc` restores the preceding root and view state. Opening a leaf with no
children proceeds directly to that Job's Messages/Events detail view.

The contextual Work page has one local tab row:

```text
Jobs > W5
[Jobs] [Messages] [Events]
```

`Jobs` renders the selected Work as the tree root. `Messages` and `Events`
always belong to that root Work, never to a merely highlighted descendant.
Opening a descendant changes the breadcrumb and root to that Work. Back or
`Esc` restores the former root, selected tab and row position. A leaf defaults
to `Messages`, since it has no descendant Jobs to present; its Events remain
available through the adjacent tab.

Back history records explicit navigation actions, not containment ancestry.
It follows the same model as browser history: Back returns to the previously
seen contextual page, regardless of how that page and the current page relate
in the Work hierarchy. The breadcrumb is structural information and is not the
history stack.
If a root view displays a third-level descendant and the user opens that row
with one Enter, one `Esc` returns directly to the former root; the two visible
intermediate parents do not become synthetic history entries. If the user
instead explicitly opens an intermediate parent and then opens its child,
those are two navigation actions and therefore two Back steps. The breadcrumb
may show the structural path without changing this interaction history.

The history is session-local and bounded to 64 ordinary page/root transitions.
Only an explicit transition to a different contextual page is recorded. Row
movement, scrolling, filters and local `[Jobs] [Messages] [Events]` tab changes
do not push history, and consecutive duplicate pages are coalesced. When the
bound is reached, the oldest ordinary entry is evicted. The original caller
(normally the top-level Jobs list) is retained separately as the final escape
target, so eviction cannot trap the user inside a deep Work view. History is
not persisted across TUI process restarts.

## Acceptance

- A depth-truncated parent with one active descendant shows the first three
  levels, one `⋮`/`...` elision row and the leaf's identity, title, Handler and
  Run state.
- Multiple independently active leaves are each visible and deterministically
  ordered; inactive or merely queued leaves do not appear as active trails.
- An ordinarily visible leaf is not duplicated, and an ancestor never borrows
  its descendant's Handler or active Phase.
- Selecting or activating a leaf trail opens the exact referenced Work details.
- Opening any non-leaf Job re-roots the tree at that Job; its breadcrumb and
  Back/`Esc` return path preserve the prior context.
- The three-level window and deeper active-leaf elision are recomputed relative
  to the selected root, while a leaf opens its Messages/Events details.
- The local `[Jobs] [Messages] [Events]` tabs are scoped to the breadcrumb root;
  changing a highlighted row alone never changes which Work owns Messages or
  Events, and returning restores the previous tab and selection.
- A non-leaf defaults to `Jobs`; a leaf defaults to `Messages` while retaining
  direct access to its Events.
- One Enter creates exactly one Back-history entry regardless of the selected
  descendant's containment depth. Intermediate ancestors become Back steps
  only when the user explicitly entered them.
- At most 64 ordinary page transitions are retained per TUI session; overflow
  evicts the oldest ordinary entry while preserving the original caller.
- Selection, scroll, filter and local-tab changes do not add history, duplicate
  consecutive pages coalesce, and a restart begins with an empty history.
- Long titles, narrow terminals, resize, tree re-rooting and filters preserve a
  clear structural marker and never turn the elision into an apparent Work row.
- Focused virtual-screen and real-terminal tests cover the live W5/W6631 shape
  and a multi-worker graph without protocol or schema changes.

## Reviewer revalidation — 2026-08-24

**Observed:** the live reproduction remains exact at projection snapshot 6820.
`tree work=W2` returns W2, W3 and W5 at depths 0, 1 and 2; W5 is unclaimed,
blocked and `deeper: true`, with no W6631 row. The independent `runtime`
projection reports W6631 open/active, handled by `baton.claude`, whose runner is
`working`. `breadcrumb work=W6631` is W2 → W3 → W5 → W6631. The visible parent
is therefore correct and incomplete in precisely the way this finding states.

**Observed:** a no-projection-change implementation cannot satisfy the existing
filter and snapshot contracts. `tree work=W2 handler=baton.claude` returns no
rows because the canonical filter examines only the bounded window; the matching
W6631 lies beyond it. `runtime`/`teams` can identify held Work and its runner but
do not carry ancestry or the fields for all canonical Work filters.
`breadcrumb` supplies ancestry but is a separate read. Joining those surfaces in
the renderer would require per-active-Work reads, could combine authority states
that never coexisted, and would either duplicate canonical filter semantics in
the TUI or draw a leaf the selected filter excludes. Direct SQLite inspection is
forbidden, and the current tree contract deliberately says the JSON and TUI
consume one identical one-snapshot window.

**Proposed correction requiring approval:** preserve the presentation ruling
but add one additive `active_trails` member to the canonical `tree` result,
derived inside its existing read snapshot. Each entry names the nearest returned
ancestor, the number of omitted containment levels, and the exact active Work
row with its own Handler and runtime. Apply the canonical Work filter to the
active Work; when it matches, retain its bounded-window ancestors as structural
context just as an ordinary matching descendant does. Keep `rows` unchanged as
the ordinary three-level Work window. This is a projection-minor change, not a
protocol or SQLite-schema change, and it gives both JSON and TUI one coherent
source rather than making the renderer an authority client of its own.

**Proposed active-leaf definition requiring approval:** emit one trail for every
open Work with a canonical active claim that lies below the returned ordinary
window, whether or not that Work itself contains children. The operator-facing
fact is each concurrent claim; restricting the list to containment leaves would
hide a real handler whenever an active parent also had descendants. Already
ordinary-visible claimed Work is omitted from `active_trails`.

**Confirmed implementation boundaries if those proposals are approved:** order
trails by full canonical containment order, group them under the nearest visible
ancestor with one non-selectable elision line per group, and keep the leaf row
selectable by its exact Work id. The TUI must budget the elision as a physical
line while keeping cursor/scroll anchors on Work ids, so a marker never becomes
a selectable pseudo-Work and the selected leaf is never scrolled off-screen.
Locale encodability can select `⋮` versus `...`; font glyph availability cannot
be detected by curses and must not be guessed.

**Observed navigation supersession:** the newly confirmed contextual-root rule
changes the current W71 interaction. Today `handle_key` makes Enter open detail
for every Work and reserves `u` for re-rooting. This finding now makes ordinary
activation conditional on the selected row's canonical child count: a non-leaf
re-roots; a leaf opens detail. Implementation and documentation must mark that
behavior as a deliberate supersession rather than leaving both rules live.

Evidence: `evidence/revalidation-2026-08-24.txt`.

## Confirmed clarification — 2026-08-24

The approver accepts the additive projection-minor `tree.active_trails` field
proposed by reviewer revalidation. It is derived in the same canonical tree
read snapshot, preserves ordinary `rows`, applies canonical Work filtering and
is the one coherent source for JSON and TUI consumers. This supersedes the
earlier acceptance wording that required no projection change. It remains a
presentation/projection addition and requires neither a protocol semantic
change nor a SQLite schema change.

Emit one trail for every hidden Work carrying a canonical active claim, even
when that Work itself contains children. Earlier uses of “active leaf” in this
finding mean the exact active Work row presented at the end of the visual
trail; they are superseded wherever they imply that the Work must be a
structural containment leaf. Every concurrent Handler must remain visible.

## Projection correction re-review — 2026-08-25

**Confirmed:** the three projection P1s are corrected. Filtered trails retain
bounded structural ancestors and anchor to a returned row; trail rows preserve
canonical claim/heartbeat/handoff facts from one sampled window; concurrent
trails follow full containment order. The focused active-trail module is 12/12
and projection/parity together are 30/30.

**Observed:** the product finding remains open. No TUI renderer consumes
`active_trails`; repository search finds the field only in projection tests,
not `src/baton_work/tui`. There is no selectable leaf presentation,
non-selectable elision, contextual-root activation supersession, root-scoped
tabs, bounded Back history, virtual-screen coverage, or real-PTY acceptance.
The corrected projection is accepted as the foundation, but W6814 cannot close
until the user-visible PLAN items 5–7 are implemented and verified.

Review: `review-2026-08-25T00-24-32Z.md`.

## Implementation clarifications — 2026-08-25

Recorded by the implementer at the renderer/navigation cut, revalidated
against the tree as it stands. None of these reverses an approved ruling;
each names a boundary the approved text left to implementation.

**The activation supersession is scoped to the Jobs containment tree.**
Enter on a Jobs row now opens what the row HAS: a Work with children becomes
the contextual root, a Work with none opens its detail. Enter in SEARCH
RESULTS and on an Inbox row's Work still opens detail, unchanged. Those are
flat result lists, not the containment window — there is no subtree to
present, and re-rooting from a search hit would answer a question the
operator did not ask. The rule is therefore one rule about the tree, not two
live rules about Enter.

**`u` is not superseded.** The revalidation superseded Enter's single
meaning, and only that. `u` remains the explicit re-root and is the only way
to root at a Work with no children, which activation deliberately does not
do. The Jobs footer names both: `Enter drill · u unfold`, replacing W71-era
`Enter details`.

**The breadcrumb accumulates visited pages; each Work page contributes its
whole containment ancestry.** The finding says the breadcrumb "may show the
structural path without changing this interaction history". Making it purely
the current Work's ancestry would have erased the segments of non-Work pages
the operator walked through — a search, a dependency view — which W292
established and this finding did not touch. So the trail keeps one entry per
visited page, and a Work page expands to every containment level it sits at
(minus the levels an earlier segment already named, W292 R1). One Enter into
a visible grandchild therefore paints three segments and costs ONE Esc, which
is exactly the case the finding names.

**The elision marker is decided per render from the terminal's encoding**, by
attempting to encode `⋮` and falling back to `...`. Font glyph availability
stays unguessed, as ruled. The `↳` containment marker is untouched by this
and keeps its existing unconditional spelling; changing it is not this Work's
scope.

**An unanchored trail is flushed, never dropped.** Containment forbids the
only shape that could produce one — a parent cannot close while an open child
remains, so a collapsed closed row can hold no active descendant — but the
display stream emits such a group at the end of the table rather than
discarding it, because "not silently truncated" is a property of the code and
not of an assumption about the data.

## Renderer independent review — 2026-08-25

**Confirmed:** the delivered active-trail stream, exact Work selection,
contextual activation, root-scoped tabs, bounded interaction history and
recorded implementation clarifications conform to the approved boundary.

**Observed:** a re-rooted page with an active Work filter paints both its local
tab row and normalized filter clauses at physical row 1. The latter overwrites
the former, producing a fragment such as `filter: status=open [Events]` rather
than two complete disclosures. The additive reviewer regression fails in the
focused and full parallel gates; all other current cases pass.

Review: `review-2026-08-25T04-07-45Z.md`.

## Final correction review and sign-off — 2026-08-25

**Confirmed:** the filter/tab overpaint is corrected. The Jobs renderer now
allocates every row above the table from one monotonic cursor: contextual tabs
and normalized filter clauses occupy separate physical lines in stable order,
and the table begins beneath both. The correction preserves narrow clause
viewporting and the full active-trail display stream.

**Verified:** the expanded focused W6814/projection/navigation/parity set is
103/103. The complete `just test-v11` gate passes all three phases: 3,036
parallel tests, 52 serial tests, and 55 ACP bridge tests.

No remaining defect was found in the correction or the previously accepted
active-trail, exact-selection, contextual activation, root-scoped-tab,
bounded-history, projection-parity, and real-terminal boundary. W6814 is
signed off. The separate W7203 drain/deploy Work remains the rollout owner;
this review neither drains dispatch nor deploys.

Review: `review-2026-08-25T05-30-30Z.md`.
