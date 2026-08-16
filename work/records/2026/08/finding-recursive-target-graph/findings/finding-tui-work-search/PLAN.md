# Plan

**Status — 2026-08-16:** parked until the fresh post-schema v11 authority is
established. Do not add this feature to the current release; the W92 cutover
script recreates it as `parked` Work in the fresh authority.

1. Revalidate the request against the post-cutover TUI and canonical tree and
   filter projections.
2. Rule the searchable fields, scope, result ordering, navigation, and
   accept/cancel behavior before implementation.
3. Add JSON/projection support only if agents need a new canonical search
   surface; do not make TUI-only derived authority claims.
4. Cover empty/no-match, exact and partial matches, filters, hierarchy,
   refresh races, narrow terminals, and read-only/seen-state invariants.
