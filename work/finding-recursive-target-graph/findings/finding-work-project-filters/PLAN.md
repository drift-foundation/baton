# Plan

**Status:** parked until a fresh-authority/schema release;
cardinality/defaulting and cross-project behavior require review before
implementation.

1. Resolve the open metadata, creation, cross-project and persistence choices.
2. Define config validation and canonical project identity in `baton.json`.
3. Add authoritative Work project metadata and indexed filter projections.
4. Expose one exact composable grammar across CLI/JSON and TUI, including
   `:filter project=baton`, startup `tui --filter project=baton`, and an
   explicit clear operation. Prove startup and interactive parity and keep
   filter state local to each client session.
5. Keep the active filter visible and preserve deterministic ordering,
   pagination, personal counts and JSON/TUI parity.
6. Cover unknown projects, multiple teams/repos, unprojected and cross-project
   Work, combined filters, restart/rebuild, narrow terminals and stale config.
7. Run focused and full v11 gates against a fresh authority before review.
