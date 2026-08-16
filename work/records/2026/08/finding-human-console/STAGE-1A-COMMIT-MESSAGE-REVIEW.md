# Stage 1A commit-message review — changes requested

The draft is strong, but one sentence conflates two different compatibility
records and becomes self-contradictory:

> The divergences are additive and read-only: … and the removal of
> `list_received` …

A removal is not additive. The actual differential harness permits exactly
two observable additions: part `address` in delivery and `created_ts` in
claimed scan rows. Separately, the core's client API intentionally adds the
named read-only query methods and removes the obsolete `list_received` view.

Separate those facts in both the commit message and the corresponding
paragraph in `baton_core/__init__.py`. Do not change code. Rebuilding the
packaged docstring will move the artifact hash again; refresh the artifact pin
and Stage 1A evidence, run only the focused parity/packaging checks, and return
the revised commit message with final hashes.
