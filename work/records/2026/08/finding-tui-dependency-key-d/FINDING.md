# Finding: use `d` for the dependency view

## Observed — 2026-08-23

The Work table and Search results open the selected Work's dependency graph
with lowercase `b`, advertised as `[b] deps`. The mnemonic is indirect: `b`
came from the earlier blocker/link presentation, while the current view shows
both prerequisites and dependents and is consistently described as
dependencies.

Lowercase `d` has no binding in the current TUI key dispatch, footer grammar,
or focused TUI tests. The dependency action has two explicit entry points in
`src/baton_work/tui/app.py`: Work-table mode and Search mode. Its graph
projection and rendering live independently of the key spelling.

## Confirmed correction — 2026-08-23

**Confirmed by Slawomir.** Replace the dependency-view key and visible label
with `[d] deps`. Remove lowercase `b`; do not retain it as an alias, hidden
compatibility binding, or deprecation path. After the change, `b` is unbound
in the affected Work-list contexts.

This supersedes only the key and label ruling in
`finding-recursive-target-graph/findings/finding-tui-dependency-key-label/`.
The dependency graph, selected-Work behavior, table and Search entry
boundaries, breadcrumb/Back behavior, empty state, JSON projections, and
protocol semantics remain unchanged.

## Acceptance boundary

- Jobs/Work-table mode opens the selected dependency graph with lowercase
  `d`.
- Search mode opens the selected result's dependency graph with lowercase
  `d`.
- Visible help/footer text says `[d] deps` wherever it advertises this action.
- Lowercase `b` does not open the graph in either context.
- Focused tests cover the positive `d` behavior and negative removed-`b`
  behavior, including packaged/PTY coverage where the current contract is
  asserted.
- No authority schema, projection, protocol, or graph-layout change is made.

## Reviewer revalidation — 2026-08-23

**Confirmed.** Lowercase `d` remains unbound throughout the live console
dispatcher. The only dependency-entry branches are
`Console._search_mode_key` and the Work-table branch in `Console.handle`, both
in `src/baton_work/tui/app.py`; each currently matches `ord("b")` and calls the
same `_open_graph` boundary. The graph handler itself has no `b` binding.

**Confirmed.** The one live on-screen advertisement is the Work-table footer
in `Console._render_table`. Search supports the action but its existing footer
does not advertise it. Change the former from `[b] deps` to `[d] deps`; do not
invent a new Search layout change as part of this key correction. The operator
guide also has three current-contract references in `docs/BATON-WORK.md` that
must say `[d] deps`.

**Confirmed test surfaces.** The current key contract is exercised by:

- `tests/work/test_w4996_dependency_graph.py` for table and Search entry plus
  exact Back restoration;
- `tests/work/test_w17_deps_label.py` for the wide/narrow real-terminal footer,
  table entry, empty state, and return;
- `tests/work/test_w4996_dependency_graph_pty.py` for real-terminal Search
  entry through its shared `OPEN_CENTER` script;
- `tests/work/test_tui.py`, `tests/work/test_parity.py`, and
  `tests/work/test_w292_breadcrumb_navigation.py` for established PTY,
  projection-parity, navigation, and breadcrumb behavior.

Related live comments/docstrings in those files, `test_w39_dependency_cue.py`,
and `test_w30_linked_route_parity.py` still describe the old key and should be
kept truthful. The packaged-artifact suite does not currently assert or use
the dependency-entry key; its coverage need not be expanded for this spelling
change. The existing PTY contracts do use the key and must move to `d`.

**Required negative regression.** Do not prove removal merely by deleting the
old positive cases. In both table and Search mode, send lowercase `b` with a
selected row and assert that the mode, navigation stack, selected identity,
and Search/table state remain unchanged and that no graph center is opened.
Keep separate positive `d` cases for both entry points. A real-terminal case
should likewise observe that `b` leaves the table visible before `d` opens the
graph; this catches an alias that an in-process test alone could miss.

**Recommended patch boundary.** Change only the dispatcher spelling, current
footer/user documentation, and key-specific tests/comments. Do not touch
`projection.dependency_neighborhood`, `tui/graph.py`, `_open_graph`, graph
navigation, or protocol commands.

**Baseline.** Before implementation, the focused current-contract selection
passed: 10 tests across W17 label PTY, W4996 table/Search entry and PTY, W292
breadcrumbs, the core TUI PTY, and JSON/TUI parity (`10 passed in 11.93s`).

## Independent implementation review — 2026-08-23 (baton.codex)

**Signed off.** Both live dependency-entry branches use `d`, `b` is absent
from the product dispatcher, the footer and current operator guide advertise
`[d] deps`, and the patch does not move graph, projection, navigation, JSON or
protocol behavior. The no-alias boundary is asserted separately in Work-table
and Search state plus a real PTY.

Independent verification passed the 13-case targeted selection and the full
nine-file dependency/TUI surface (**167 passed**); whitespace is clean. Review
and evidence: `review-2026-08-23T15-59-51Z.md` and
`evidence/review-2026-08-23.txt`.

One editorial attribution in `test_w17_deps_label.py` is left explicitly for
the already-routed tuner: W17 established the historical `b` label and W96
established `d`. It is not a behavioral or sign-off blocker.

## Tuner polish — 2026-08-23 (`baton.tuner`)

**Completed.** The first line of `test_w17_deps_label.py` now attributes the
historical change from `b links` to `[b] deps` to W17 and the subsequent move
to `[d] deps` to W96. No behavior or test assertion changed in this polish
pass. The focused two-case PTY file passes and `git diff --check` is clean.
