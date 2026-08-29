# Make breadcrumbs focusable and navigable

## Confirmed 2026-08-27

Breadcrumbs explain the current hierarchical location but cannot be focused
or used to navigate directly to an ancestor. Operators must leave the page and
reconstruct navigation even though every target level is already displayed.

## Decision

Treat the breadcrumb as a focusable navigation region. On focus, selection
starts at the current/deepest crumb. `h`/`l` and Left/Right move between
crumbs; Enter navigates directly to the selected location. Enter on the
already-current crumb is a no-op. Down enters the page's tabs/body, Up may
return to the breadcrumb, and Tab/Shift-Tab includes it in the ordinary region
cycle.

Long breadcrumbs use a horizontal viewport that keeps the selected crumb
visible without truncating its identity. A textual footer such as
`breadcrumb 3/5: W3` communicates selection independently of colour or
highlighting.

Hierarchy and browser-style navigation history remain separate. Navigating
from a deep Work to an ancestor is one new navigation step. Esc/Back returns
to the previously viewed page in one step, even when that page is several
containment levels deeper; it does not walk the hierarchy level by level.

The behavior is a generic breadcrumb contract, not a Work-only shortcut. Its
implementation must revalidate and preserve the existing breadcrumb-scoped
detail and Back-history decisions rather than silently replacing them.

## Open implementation details

Reviewer research must inventory every page that exposes breadcrumbs, resolve
spatial Up/Down behavior where a page has no secondary tabs, define viewport
markers and empty/single-crumb behavior, and confirm no existing local key
binding is stolen while the breadcrumb lacks focus.

## Reviewer specification — 2026-08-27

The implementation inventory, focused baseline, proposed focus graph,
structured targets, viewport, and regressions are recorded in
`evidence/reviewer-research-2026-08-27.md`.

**Observed pages:** contextual Work Jobs/Messages/Events, search, dependency
graph, and pokes currently expose breadcrumbs. W26328's proposed Awaiting-me
view must join the same generic path. Top-level Jobs/Teams/Inbox do not.

**Confirmed architectural constraint:** current `nav` is browser history but
also feeds breadcrumb text. A direct ancestor jump must retain the deeper page
for one-step Back while resetting the displayed location. It cannot be
implemented by repeated pops or by blindly appending the ancestor to the old
path; use a structured current-location/reset boundary while keeping the
existing bounded history.

**Proposed focus graph:** include breadcrumb in Tab/Shift-Tab cycles for every
breadcrumb page. Extend Work-detail `Ctrl-W` geometry only between breadcrumb
and the top pane. Boundary Up may enter breadcrumb; Down returns to the prior
body focus. While focused, `h`/`l` and Left/Right move crumbs, Enter jumps, and
Esc alone retains Back. Unfocused and text/modal key ownership is unchanged.

**Proposed navigation:** Work-to-Work jumps preserve the current local tab;
other Work jumps land on Jobs. Page crumbs restore exact captured search,
graph, poke, or Awaiting-me state. Jobs restores the exact top-level caller.
Every non-current jump records one new history step and one Back restores the
deeper page and its selected crumb.

**Proposed viewport:** paint whole crumb tokens in a contiguous window with
standalone `…` markers on omitted sides. Fall back from an overlong Work title
to its exact `W…` selector, never a sliced identity. While focused, the footer
begins `breadcrumb I/N: SELECTOR`; an impossible width says
`(breadcrumb too narrow)`.

**Confirmed implementation boundary:** this is client-only TUI/navigation
state over existing `{id, title}` ancestry. It requires no schema, protocol,
projection-version, or workflow mutation.

**Open for approver:** confirm the proposed focus graph, same-tab Work jumps,
page restoration, Left-versus-Esc rule, compact selectors, `…` markers, and
narrow/footer behavior before implementation.

## Approver ruling — 2026-08-27

Approved without amendment. Implement the structured location-reset model,
breadcrumb participation in Tab/Shift-Tab and the bounded Work-detail Ctrl-W
graph, boundary Up/Down behavior, same-tab Work-to-Work jumps, exact page-state
restoration, focused Left-versus-Esc distinction, whole-token `…` viewport,
compact exact selectors and textual narrow/footer behavior exactly as specified
above and in `evidence/reviewer-research-2026-08-27.md`.

The existing 64-step browser-history bound remains unchanged. Direct ancestor
navigation is one new history action; one Esc restores the prior deeper page.
This remains client-only TUI state with no protocol, schema, projection or
workflow mutation.

## Tuner implementation — 2026-08-28 UTC

**Revalidated:** the approved client-only boundary still matches the current
tree. The existing navigation stack remained browser history, but its frames
also remained the sole input to the displayed breadcrumb; an ancestor jump
could therefore not retain the deeper frame for Back without painting that
deeper location. The implementation separates a captured structural
`location` list from the unchanged bounded history and restores both through
the existing navigation-state boundary.

Breadcrumbs now expose structured Work and page targets, participate in every
approved focus cycle, keep a stable selected key, navigate with both horizontal
key pairs, and restore the prior body focus on Down. Work-detail Tab cycles and
Ctrl-W geometry include the breadcrumb; first-row Up joins it on the single-body
pages. Direct Work jumps preserve Jobs/Messages/Events, while captured page
crumbs restore their exact search/graph/poke/Awaiting-me state. The current
crumb remains a no-op and every other jump adds exactly one Back step.

The header derives a maximal contiguous whole-token viewport around selection.
Standalone `…` markers name omitted sides, overlong labels fall back to exact
selectors, and the focused footer reports `breadcrumb I/N: SELECTOR` before
optional help clauses. Operator documentation now distinguishes crumb selection
from browser Back and teaches the expanded focus graph.

Focused regressions live in
`tests/work/test_w26331_focusable_breadcrumb.py`; approved compatibility changes
also update W292, W1151 and W4996 expectations where a page suffix becomes its
own selectable crumb or the breadcrumb becomes a real focus stop. Verification
is retained in `evidence/w26331-2026-08-28-tuner.txt`. No protocol, schema,
projection or workflow code changed.

## Tuner review correction — 2026-08-28 UTC

**Revalidated:** the independent review's three findings are defects inside
the approved generic breadcrumb contract, not new scope. Work crumb keys now
include their stable location-frame and ancestry positions, so repeated Work
occurrences produced by graph recentering remain independently selectable and
navigable across repaint, resize and Back restoration. Focused Up/k is consumed
at the breadcrumb's upper boundary and cannot mutate a hidden body selection.

Viewport choice, right-edge reservation, paint columns and footer fitting now
use the TUI's existing terminal-cell metric. Wide labels fall back to their
exact compact selector, combining sequences remain whole, and dispatch, filter
and participant units retain their reserved region. Requested repeated-graph,
all-single-body/dual-Up, wide-character and combining-character regressions are
in `tests/work/test_w26331_focusable_breadcrumb.py`; complete correction
verification is appended to
`evidence/w26331-2026-08-28-tuner.txt`.

## Progress ownership ruling — confirmed 2026-08-28 UTC

The prior repository rule reserving `PROGRESS.md` to `baton.claude` is
superseded. Progress belongs to the participant that actually makes the
implementation change under the authorized Work claim. This includes a tuner,
reviewer, approver, prompt participant, or another Handler when that
participant is the change author. Across serial claim episodes, each actual
change author may append an attributable account but may not rewrite another
author's history. A participant that only reviews or discusses the change
still does not write progress.

W26331 was explicitly assigned to and implemented by `baton.tuner`; requiring
Claude to reconstruct that work would create false authorship. The tuner is
therefore the required writer of this dossier's missing `PROGRESS.md`. Once
that truthful record is present, the independent application sign-off is
sufficient for satisfying closure.
