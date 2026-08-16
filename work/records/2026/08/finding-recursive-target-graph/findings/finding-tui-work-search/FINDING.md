# Finding: the v11 TUI needs Work search

## Observed

As the Work table grows, cursor navigation and project filters alone do not
provide a quick way to locate a known or partially remembered item.

## Confirmed request — 2026-08-16

**Confirmed by Slawomir during the v11 cutover** (relayed at the W92 cutover
in v10 message `80bbe48807979662b97be8a3f8f1d6c5`). `/` starts a search for
Work items in the TUI. This feature is explicitly deferred until after the
fresh post-schema authority is established; it is not part of the current
release or W92 cutover gate. It is recreated in the fresh schema-15
authority as `parked` Work so the request survives the trial retirement
without becoming release scope.

The later design pass must decide the exact searchable fields, interaction
with active filters and the two-level containment window, result navigation,
accept/cancel behavior, and whether matching is incremental. Search is a
read-only navigation aid: it must not mutate Work, mark Messages seen, or
invent state outside the canonical JSON projection.

No implementation semantics beyond the `/` entry key and Work-item scope are
confirmed yet.

## Pin provenance — 2026-08-16

Two pins of this request were created concurrently during the W92 cutover: a
top-level `work/records/2026/08/finding-tui-work-search/` (reviewer) and this
umbrella child (implementer). Per the reviewer's resolution (v10
`c3d2e3bae72f12a61aa9387025258f2e`), THIS child is the canonical record; the
top-level duplicate's richer details were absorbed above and the duplicate
was removed. The recreated parked Work binds to the umbrella record and its
body names this child path.

## Revalidation and implementation boundary — 2026-08-16

Slawomir directed the reviewer to finish research and hand this Work to the
implementer after the fresh schema-15 authority was established. The current
TUI confirms that filters and the two-level Work window cannot replace search:
they intentionally omit deeper Work and do not locate a partially remembered
title or selector.

Search is a canonical, read-only Work projection, not a client-side scan of
whatever rows happen to be painted. Add JSON `search query=...` and have `/`
consume that same projection. Its scope is every Work owned by the viewer's
team, including nested Work beyond the current two-level window. This retains
the team-noise boundary; cross-team navigation remains available through
explicit links rather than turning search into a global catalog.

Matching is deliberately small and predictable:

- case-folded substring matching on the Work title;
- case-insensitive exact/prefix matching on canonical and authority-local Work
  identifiers (`7ba67cb8-W47`, `W47`); and
- no Message-body, Thread-subject, route, category or dossier-content search.
  Those facts already have dedicated navigation/filter surfaces or belong to
  a future indexed-search feature.

The active Work filter narrows the result set with the same normalized AND
semantics used by `home` and `tree`. Closed Work follows the console's existing
closed-visibility rule: hidden by default, included when `z` exposes closed
Work or an explicit `status=closed` filter selects it. Search never changes or
clears the filter.

`/` is valid from the Work table. It opens a one-line query bar; typing is
pure client state and performs no authority reads. Enter submits one canonical
search and opens a flat result table with stable Work IDs and ordinary row
facts. `j`/`k` (and arrows) move through results, Enter opens that Work's normal
detail view, `/` starts a replacement query, and Esc returns to the exact prior
Work window, filter, path and selected Work. An empty query refuses locally;
no matches produce an explicit empty result view that Esc can leave.

The ordinary two-second refresh reruns an accepted search through the same
cache invalidation path and anchors selection by Work ID. Keystrokes do not
refresh it. A selected Work that stops matching moves selection
deterministically to the nearest remaining result; an empty refreshed result
stays an honest empty search. Search never marks Messages seen, changes New,
writes an event, or probes a bound filesystem path.

JSON returns the normalized query, canonical row objects, the active filter,
and `snapshot_seq` from one read snapshot. Results use stable creation order;
the first version is bounded and paged by an explicit stable continuation
cursor rather than silently truncating. The TUI footer names result count/page
and the `j/k Enter / Esc` controls. Exact paging vocabulary may reuse the
repository's existing `after`/`limit` convention, but no internal cursor is
presented as a Work identity.
