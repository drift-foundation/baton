# Maintenance entry active-claim race

Status: **implemented for protocol 7; protocol-6 fallback explicitly
deferred**.

During a protocol migration the preflight scan and `maintenance-enter` are
separate operations. A claim can be created between them. If maintenance entry
accepts that claim, `reply` and `close` are gated afterward, so the holder loses
the normal path to drain it.

The operation that closes the maintenance gate must check
for active claims inside the same write transaction and refuse with
`EXIT_RACE`, leaving the instance ungated. Protocol 7 now provides that
guarantee, on the move-entry path as well as plain maintenance entry — the
same ceremony closes both, and a refused move binds no `moves` row.
`test_maintenance_entry_refuses_active_claims_atomically` and the four
related adversarial regressions pass.

The preserved protocol-6 executable does not provide the same entry-time
check. Slawomir explicitly deferred that fallback work on 2026-08-07: the live
authority is already protocol 7, the protocol-6 executable is retained for
read-only access to the retired archive, and an in-place protocol-6 cutover is
not the current operational path. This limitation remains recorded here; it
does not block the protocol-7 release.

Before any protocol-6 in-place cutover is promoted back to a live operational
path, its source-side maintenance entry must gain the same atomic refusal or
the migration contract must be revised explicitly.
