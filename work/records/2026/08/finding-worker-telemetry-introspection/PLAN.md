# Plan: normalize worker telemetry and introspection

1. [done 2026-08-29] Record the confirmed provider-neutral telemetry boundary,
   ACP and Codex native mappings, explicit unknown semantics, and the
   non-authoritative relationship to workflow state.
2. [done 2026-08-29; W39649] Bind the finding to one independently scheduled
   Baton Work and link it from the v12 M4 roadmap.
3. [research baseline recorded 2026-08-29; revalidate at implementation]
   Revalidate the shipped ACP version and each certified provider's stable
   capability surface. The current baseline is ACP SDK 1.3.0's stable
   `usage_update`/`available_commands_update` and the installed Codex App
   Server's non-experimental generated schema; separate stable members from
   drafts and provider extensions.
4. [pending; blocked on item 3] Define one bounded normalized telemetry
   document with per-field provenance, observation time, freshness/staleness,
   explicit unknowns, and secret rejection.
5. [pending; blocked on item 4] Implement the ACP mapping for stable usage and
   advertised-command updates; keep provider `/status` behind correlated
   `inquire` and out of authoritative structured state.
6. [pending; blocked on item 4] Implement the Codex App Server driver over
   JSONL stdio using a version-owned generated schema and structured thread,
   usage, account, quota, model, and turn-failure surfaces.
7. [pending; blocked on item 4] Define the minimum honest fallback for other
   native-control and CLI-only agents. Unavailable fields remain unknown; do
   not scrape terminal presentation.
8. [pending; blocked on items 5–7] Add replay, restart, stale-update,
   sparse-delta merge/refetch, unsupported-capability, account-identity and
   free-form-error redaction, schema-drift, auth-loss, quota-limit,
   provider-loss, and probe-versus-inquire conformance.
9. [pending; later UX cut] Expose the normalized snapshot on the v12 Teams and
   worker-detail surfaces with last-observed time and an explicit refresh
   action. Do not turn telemetry into implicit scheduling authority.
