# Finding: large Work lists need explicit project filters

## Observed

One team may coordinate many products and repositories. A flat team-local Work
list eventually becomes too large to scan, even with status, phase, priority,
Current and New columns. Repository roots and dossier bindings cannot safely
stand in for project identity: Work may have no dossier, span repositories, or
concern deployment and coordination rather than one source tree.

## Confirmed direction — 2026-08-15

**Confirmed by Slawomir during the second v11 trial.** Work gains explicit
canonical project metadata and clients support composable filtering. Project
identity is not inferred from filesystem paths, roots, titles, teams or
bindings. Project names are declared in `baton.json` so typos and unknown
projects fail validation rather than silently creating accidental buckets.

The TUI accepts command-mode filtering such as:

```text
:filter project=baton
```

The same filter may be supplied when launching the TUI, for example:

```text
baton ... tui --filter project=baton
```

This supports operators who keep several TUI sessions open, each starting in
a different project view. Filter selection is client-local view state: opening
or changing one TUI's filter does not mutate authority state or another
session's view. Startup and interactive filters use one grammar and produce
the same rows; they are not two subtly different query surfaces.

The active filter is always visible; an operator must not forget that rows are
being hidden. CLI/JSON expose the same canonical filter semantics so agents
can reproduce exactly the view a human sees. Filters are composable and must
eventually cover useful existing dimensions such as open/closed status,
phase, Current/me, personal New and priority without creating separate query
dialects.

## Open design questions

- whether one Work may carry one project or several explicit project labels;
- how a project is selected/defaulted at Work creation;
- the exact clear/edit grammar and whether interactively chosen filters survive
  a client restart when no startup filter was supplied;
- how cross-project Work and linked cross-team Work appear under a project
  filter;
- filter ordering, pagination and active-filter presentation on narrow
  terminals.

Project metadata is persisted authority state, so this finding is deferred to
a fresh-authority release. It must not widen the current schema-14 iteration.

## Supersession — 2026-08-16: team is the project boundary

**The confirmed 2026-08-15 project-metadata direction above is superseded.**
Slawomir ruled during the fresh v11 trial that Baton does not need a second
persisted `project` identity: the owning team is the project. Adding both would
create two overlapping partition keys and force operators to decide which one
is authoritative.

Work therefore remains owned by exactly one team, and the team's `home` view
is already implicitly scoped to that team. No `project` field, project catalog,
project default, or project-driven authority-schema change is required.

Composable filtering remains desired, but it operates on existing canonical
Work facts: team where a multi-team surface exposes more than one team, plus
status, phase, Current/handler, category, readiness, personal New, and priority
once priority exists. `team=baton` is meaningful on a cross-team surface but
redundant on `baton`'s own home view. TUI startup and interactive filters still
share one grammar, remain client-local, and visibly disclose the active filter.

## Research findings — 2026-08-16

**Confirmed against the current implementation.** `home` and the bounded
two-level `tree` are the canonical Work-list projections shared by JSON and
the TUI. Filtering must enter that shared projection boundary; filtering only
painted TUI rows would make agents and humans disagree, break summary/hidden
counts, and make later pagination incorrect. This is pure same-schema read
work.

**Proposed first filter vocabulary.** Use the existing canonical values only:

- `team=HANDLE`;
- `status=open|closed`;
- `phase=queued|research|waiting|active|review|parked` (closed Work is selected
  through `status=closed`, not an invented phase value);
- `current=TEAM.KIND|me`;
- `category=unknown|suspected-defect|confirmed-defect|limitation|duplicate|design-choice|rejection`;
- `ready=true|false`;
- `new=true|false`, meaning the viewer's personal New count is nonzero/zero;
- `priority=high|normal|low`.

Different fields compose with AND. The first version accepts at most one value
per field; it does not invent comma syntax, negation, comparisons, or an OR
language. Unknown fields, duplicate fields, malformed booleans, compact TUI
spellings, unknown teams/endpoints, and values outside a field's closed
vocabulary refuse before producing a plausible partial view.

**Proposed shared surface.** The same optional field operands appear on
`home`, `tree`, and `tui`. Examples:

```text
baton ... home status=open priority=high
baton ... tui status=open priority=high
:filter status=open priority=high
```

Interactive `:filter` with no operands clears the local filter. Replacing a
filter is atomic client-local state, not incremental hidden state; state does
not survive process restart unless supplied on launch. The canonical result
echoes its normalized active filter so JSON and the TUI disclose the same
selection.

## Open containment and presentation rulings — 2026-08-16

1. When a child matches but its parent does not, the recommended behavior is
   to retain the parent as context and mark it `filter_match: false`; matching
   rows carry `filter_match: true`. Nonmatching children disappear. This keeps
   `↳` truthful and gives JSON enough information to distinguish a match from
   context. Strictly removing the parent would create an orphaned child or
   falsely promote it to a root.
2. The TUI must always disclose that filtering is active. Recommended narrow
   behavior: the header always shows `Filter:N` (number of clauses), while a
   dedicated line shows the normalized clauses and may horizontally viewport
   them rather than silently dropping the disclosure. `:filter` with no
   operands clears; entering command mode with `filter` exposes the full
   current clauses for editing.

## Approved containment and presentation rulings — 2026-08-16

**Approved by Slawomir.** Both recommendations immediately above are now the
current contract:

1. A matching child retains its nonmatching parent as structural context.
   Canonical rows distinguish the child match (`filter_match: true`) from the
   retained parent (`filter_match: false`); unrelated nonmatching children are
   omitted. Filtering never promotes an orphaned child to a false root.
2. Active filtering is always disclosed. The header retains `Filter:N`; a
   dedicated normalized-clause line may use a horizontal viewport at narrow
   widths. Bare `:filter` clears the client-local filter, and command entry
   exposes the current clauses for editing.

These decisions resolve the two open rulings. They do not yet approve an
implementation that diverges from the proposed closed vocabulary or shared
CLI/JSON/TUI projection boundary elsewhere in this finding.

## Implementation-ready research boundary — 2026-08-16

**Revalidated against the schema-15 implementation after approval.** This is
one same-schema read feature. It adds no `project` field and mutates neither
authority nor accepted configuration.

- A shared pure filter parser owns the closed vocabulary and canonical order.
  `home`, `tree`, and `tui` accept the same optional field operands; the TUI's
  `:filter` command uses that parser too. The earlier illustrative
  `tui --filter project=baton` spelling is superseded by the repository's
  approved key-value command grammar, for example
  `tui status=open priority=high`.
- Filtering occurs inside the canonical `home`/`tree` read snapshot after row
  facts such as personal New, resolved Current handlers, readiness and
  priority are projected. JSON and TUI therefore consume the same selected
  rows and the same normalized filter disclosure. The team summary remains
  the global team summary; `Filter:N` and the normalized filter line make the
  narrower row window explicit rather than relabelling global counters as
  filtered totals.
- Within each bounded parent/child window, a matching parent is retained and
  only matching children follow it. A nonmatching parent is retained as
  `filter_match: false` when at least one child matches; those children carry
  `filter_match: true`. A parent and all its children disappear when none
  match. Filtering never promotes a child or changes depth/order.
- `current=me` means the viewer is one of the endpoint's resolved handlers;
  exact `TEAM.KIND` matches the canonical Current endpoint. `new=true` means
  the viewer's personal New count is nonzero. All other values compare to
  their canonical projected fields; compact TUI display labels are refused as
  input.
- Filter replacement is atomic client-local state. Bare `:filter` clears it;
  process restart clears an interactive filter unless launch operands specify
  it again. A successful local mutation refreshes the currently filtered
  projection through the existing single refresh scheduler without altering
  the filter.

Focused acceptance must cover every field, AND composition, unknown and
duplicate operands, invalid booleans/endpoints/compact labels, `current=me`
with eligible and ineligible viewers, personal New, parent-context retention,
re-rooted and cross-team windows, clear/replacement/restart, startup versus
interactive parity, narrow disclosure, selection stability, and unchanged
authority state.
