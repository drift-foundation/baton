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
