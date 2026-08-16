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
