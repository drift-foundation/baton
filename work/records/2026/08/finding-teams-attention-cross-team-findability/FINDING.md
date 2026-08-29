# Teams attention can point at hidden cross-team Work

Date: 2026-08-28 UTC

Baton Work: `W29146`

## Finding

**Observed:** the `baton.slaw` TUI displayed `[Teams *]`, while the default
own-team Teams table showed no overdue Baton participant. Searching Jobs for
`W12181` returned zero matches.

**Confirmed:** `W12181` is open, queued, ready and pickup-overdue on endpoint
`pc.ops`, whose resolved Handler is `pc.slaw`. The Teams projection correctly
reports that overdue participant. The TUI's `teams_need_attention()` scans
every configured team, but `team_rows()` hides non-own teams by default and
the canonical Jobs search selects only Work owned by the viewer's team.
Consequently one global star can be caused by a participant and Work that are
both absent from the destination view and unfindable through that viewer's
Jobs search.

The bold `baton.slaw` row is separate: the TUI bolds the viewer's own member
row as an identity cue even when it has no overdue pickup. It must not be read
as the reason for the tab marker.

## Impact

The marker promises actionable participant attention but does not reveal who
needs attention after navigation. An operator can reasonably conclude the
visible bold self row is at fault, while the actual overdue participant lives
in another hidden team. This becomes more confusing as one human principal
operates several configured team identities.

## Open product decision

Choose one coherent scope and make the cue lead directly to its cause:

- scope `[Teams *]` to the roster currently exposed by the destination view;
- keep global attention but automatically expose or summarize every offending
  cross-team participant when Teams opens; or
- introduce the v12 shared-principal/team-hierarchy model so one operator's
  cross-team attention has an explicit principal-level view.

Whichever model is selected, a visible attention marker must lead to at least
one visible, textually identified offending row without requiring the operator
to discover an unrelated scope toggle. Jobs search scope must be stated rather
than silently appearing global.

## Acceptance boundary

- Reproduce one overdue member in another team and no overdue member in the
  viewer's own team.
- Prove `[Teams *]` either remains absent or leads directly to the cross-team
  overdue member with its suggested Work visible.
- Keep current-viewer identity styling independent from overdue styling.
- Make team-scoped Jobs search visibly state its scope; if cross-team search is
  added, require explicit authorization and unambiguous team-qualified results.
- Cover both own-team and all-team Teams modes and refresh after the overdue
  Work is claimed, rerouted, blocked, parked or closed.

## Reviewer revalidation — 2026-08-28 UTC

### The v11 versus v12 scope is already ruled

The apparent product choice above does not need a new policy invention.
Existing confirmed v11 decisions already select the bounded correction:

- `work/records/2026/08/finding-claim-overdue-cue/FINDING.md` rules that the
  top-level Teams marker is deployment-global — it appears when **one or more
  participants** are overdue — and explicitly requires that opening Teams
  expose the responsible participant rows and their details.
- `work/records/2026/08/finding-recursive-target-graph/findings/finding-tui-work-search/FINDING.md`
  deliberately scopes Work search to the viewer's owning team and preserves
  cross-team navigation through explicit links rather than a global catalog.
- `work/records/2026/08/finding-v12-isolated-agent-workers/findings/finding-v12-team-hierarchy-shared-approvers/FINDING.md`
  owns the later principal-global Teams/Inbox model. V11 must not guess that
  two `*.slaw` participant spellings are one principal, but that future model
  does not excuse a v11 marker that points at hidden rows today.

Therefore the v11 fix keeps global attention, keeps ordinary Work search
team-scoped, and turns the already-projected suggested Work into an explicit
cross-team navigation link. V12 principal aggregation remains separate Work.

### Current code path

**Observed:** `projection.teams()` returns every configured team in one read
snapshot. Each member carries canonical `pickup`, including exact
`next_work {work, local_id, title}`. `Console.teams_need_attention()` scans that
whole cached roster, so its global star is correct.

**Observed:** `Console.team_rows()` then drops every non-viewer team whenever
`teams_own_only` is true, which is the default. `_team_selected()` preferentially
keeps the viewer's own participant selected. Entering Teams performs no
attention-aware scope or focus step, and `_handle_teams()` has no operation that
opens `pickup.next_work`. The same cached data therefore contains the cause and
then deliberately hides it.

**Observed:** `projection.search()` queries `work WHERE team = viewer_team` and
its result does not publish that scope. The CLI help calls it team-scoped, but
the TUI header renders only `search: QUERY`, which looks global. This search is
not the right place to widen authority: its owning finding explicitly retains
the team-noise boundary and names explicit cross-team links as the alternative.

**Observed live at snapshot 29163:** canonical `detail work=W12181` reported
open/queued/ready, `pickup=overdue`, team `pc`, endpoint `pc.ops`, resolved
handler `pc.slaw`; `search query=W12181` as `baton.codex` returned zero rows and
no result field naming the `baton` scope.

**Baseline:** the existing Teams, pickup and search modules are green before
the correction: 94 tests passed across
`test_w25_jobs_teams_inbox.py`, `test_w2938_participant_pickup.py`, and
`test_w6_search.py`.

## Implementation-ready v11 correction

The following mechanics implement the confirmed rulings without broadening
search or inventing principal identity.

### 1. Attention-aware own-team roster

When Teams is in its default own-team mode, `team_rows()` returns:

1. every member of the viewer's own team; plus
2. every non-own-team member whose canonical `pickup.state` is `overdue`.

Pending and ordinary cross-team members remain hidden. All overdue members are
included, not just one, so one global star never conceals another cause. The
scope line says the truth, for example `own team + 2 overdue elsewhere`; when
there are no exceptions it retains `own team`. `t` continues to toggle to the
complete `every team` roster and back to the attention-aware own-team view.

This is a presentation exception over data `teams` already exposes globally;
it changes no authority, roster projection, pickup derivation, or privacy
boundary.

### 2. Entry focus and refresh

Opening Teams while the marker is starred focuses the first overdue member in
canonical visible-row order, so the destination immediately paints one named
cause and its pickup detail. All other overdue rows remain bold and visible.
The selection highlight composes with overdue bold exactly as today.

On refresh, marker, exception rows and focus derive from the same cached Teams
snapshot. If a selected exception stops being overdue and disappears from the
default view, selection falls back first to the viewer's own participant when
present, otherwise the first visible row. No stale hidden participant remains
selected.

Current-viewer bold remains an identity cue only. It neither creates the star
nor suppresses the `Pickup` cell/detail that identifies an overdue row.

### 3. Explicit suggested-Work link

When the selected member has `pickup.next_work`, the Teams footer offers
`Enter open suggested Work`. Enter opens that canonical Work's ordinary Jobs
detail through the existing explicit-link/detail path; Back restores Teams and
its roster selection. This works for cross-team Work because direct links are
the confirmed cross-team navigation mechanism. It grants no claim, mutation,
search, or broader listing authority, and the detail's canonical available
actions remain the authority's answer for the viewer.

The displayed locator must retain the team-qualified participant beside the
Work title/selector. The Work remains a diagnostic suggestion, not the owner of
the participant pickup obligation.

### 4. State search scope explicitly

Add `team: viewer_team` to the canonical `search` result and advance the
additive projection minor from 12.7 to 12.8. The TUI consumes that field and
renders a header such as `search (team baton): QUERY — page ...`; the empty
result also names the same team. CLI help remains team-scoped and JSON now
states the scope rather than relying on caller knowledge.

Do not add an all-team search switch or reinterpret `team=` as authorization to
widen search. `pc` Work is reached from the explicit `next_work.work` link in
Teams, not by silently globalizing `/`.

### 5. Exact patch boundary

- `src/baton_work/tui/app.py`: attention-aware `team_rows`, Teams entry focus,
  deterministic vanished-exception fallback, truthful scope line/footer,
  suggested-Work Enter navigation, and team-qualified search heading.
- `src/baton_work/projection.py`: additive `team` field on the canonical search
  result; no search predicate or authorization change.
- `src/baton_work/jsonapi.py`: document and publish projection 12.8; update the
  exact version pins that protect the shipped JSON contract.
- `docs/BATON-WORK.md` and CLI/release help: explain own-team plus overdue
  exceptions, `t` all-team browsing, Enter's explicit suggested-Work link, and
  visible team-scoped search.
- Focused TUI/projection/PTY tests, preferably in a dedicated
  `test_w29146_cross_team_attention.py`, with additive cases in existing
  exhaustive registries where required.

No SQLite schema, event, transition, pickup calculation, Work-search match,
Route, readiness, Worker Manager, bridge, or v12 authority change belongs in
this correction.

## Required regression matrix

1. Viewer team has no overdue member; another team has one overdue member and
   at least one non-overdue member. Jobs shows `[Teams *]`; default Teams shows
   all own-team rows plus only the overdue foreign row.
2. Opening starred Teams focuses that foreign participant and immediately
   shows `Pickup overdue` plus its canonical suggested Work.
3. Two foreign teams overdue at once both remain visible; entry focus is
   deterministic and navigating reaches the second.
4. `t` exposes every team, and toggling back restores own-team plus all current
   overdue exceptions without losing a still-visible selection.
5. Pending foreign pickup creates neither a star nor an exception row.
6. A non-overdue viewer row remains bold as identity without being mistaken for
   the cause; overdue and selected attributes continue to compose.
7. Enter on a foreign suggested Work opens its ordinary detail; Back returns to
   the same Teams selection. A member with no suggestion advertises no Enter
   action.
8. Claiming, rerouting away, blocking, parking or closing the last suggested
   Work clears the overdue state under existing pickup rules; scheduled refresh
   clears the star/exception/focus together. If another actionable Work keeps
   the pool nonempty, the participant and its updated suggestion remain.
9. `search query=W12181` as `baton.*` remains empty for `pc` Work, but JSON
   returns `team: baton` and TUI/empty-result copy visibly says `team baton`.
10. Projection-version, JSON/CLI, narrow/wide TUI, cache/snapshot, and packaged
    PTY tests cover the changed public surface.

## Independent review — 2026-08-28 UTC

**Confirmed corrected and signed off.** The default roster now exposes every
foreign overdue cause of the deployment-global Teams marker, states the
exception scope, and focuses a cause on entry. The canonical suggested-Work
link reaches cross-team detail and Back restores Teams without changing the
Inbox handoff. Search remains team-scoped while projection 12.8 and the TUI
state that scope explicitly. Marker, rows, exception count and focus consume
one cached Teams snapshot; no authority or v12 boundary moved. See
`review-2026-08-28T13-49-33Z.md`.
