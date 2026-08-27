# W24755 design baseline — 2026-08-27

## Repository observations

- `src/baton_work/projection.py::tree` is one snapshot but deliberately team-
  scoped and three containment levels. Its `deeper` member discloses hidden
  descendants; it is not a complete graph source.
- `projection.dependency_neighborhood` is one snapshot but dependency-only,
  directional, depth 1..3, four direct neighbours per branch and capped at 200
  rendered occurrences. It is a bounded operator view, not an export.
- `projection.links` exposes all four relationship families one hop at a time,
  but repeated calls have independent snapshots. Its `blocks` side also hides
  closed consumers intentionally, while `blocked_by` retains recorded
  blockers. A full current export cannot be assembled from it.
- Canonical current relation sources are `edges(work, blocker,
  via_obligation, created_seq)` plus `work.parent`, `work.follow_up_of` and
  `work.duplicate_of`. All endpoint columns are foreign keys.
- `_read_snapshot` is reentrant `BEGIN ... ROLLBACK`; existing `home`, `tree`
  and dependency projections demonstrate the required token discipline.
- The CLI currently emits a sorted JSON envelope for every ordinary command.
  A raw DOT path therefore has to be explicit and must carry authority,
  protocol, projection and snapshot identity inside DOT graph attributes.

## Existing behavior baseline

Focused verification:

```text
tests/work/test_projection.py::test_links_expose_the_fan_in_deliberately
tests/work/test_terminal_outcomes.py::test_duplicate_link_rules_are_exact
tests/work/test_ws2_close.py::test_follow_up_targets_closed_work_only_and_gates_nothing
tests/work/test_w71_navigation.py::test_a_mid_read_commit_cannot_produce_a_mixed_tree
tests/work/test_w4996_dependency_graph.py::test_the_public_links_response_is_unchanged
tests/work/test_w4996_dependency_graph.py::test_every_edge_spells_its_direction_without_unicode_or_colour

6 passed in 0.06s
```

## DOT facts revalidated from the primary specification

- DOT directed graphs use `digraph` and `->`.
- `strict` forbids parallel edges: a later edge with the same tail/head refers
  to the existing edge and applies attributes to it. W24755 must use a
  non-`strict` `digraph`, because the same two Works may hold more than one
  typed relationship.
- Quoted identifiers permit escaped quotes. DOT assumes UTF-8 by default.
- Graphviz label values are `escString`s: sequences such as `\N`, `\G`, `\E`,
  `\T`, `\H`, `\L`, `\n`, `\l` and `\r` have renderer meaning. User titles
  containing those bytes must have their backslashes protected before they
  enter `label`.
- Attribute names and values are extensible strings, so `baton_*` metadata is
  portable DOT even when a layout engine does not interpret it.

Primary references:

- <https://graphviz.org/doc/info/lang.html>
- <https://www.graphviz.org/docs/attr-types/escString/>

## Proposed implementation boundary

- Projection: `src/baton_work/projection.py::work_graph`, one `_read_snapshot`,
  constant statement count, complete arrays, no client crawl.
- Renderer: new pure `src/baton_work/dot.py::render_work_graph_dot(envelope)`;
  no authority handle, filesystem access, subprocess or Graphviz import.
- CLI: `work-graph format=json|dot status=all|open|closed [team=HANDLE]`.
  JSON remains the default. DOT is raw stdout only when explicitly selected.
- Projection minor: bump `jsonapi.PROJECTION_VERSION` from 12.5 to 12.6.

No repository implementation was changed during this design pass.
