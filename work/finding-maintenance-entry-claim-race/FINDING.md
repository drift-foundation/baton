# Maintenance entry active-claim race

Status: **implemented for protocol 7; the protocol-6 fallback is moot.**

The deferred protocol-6 entry-time check no longer has anything to guard: the
in-place 6 → 7 migration path was removed from the tool, so there is no
supported cutover that enters maintenance through a protocol-6 executable. The
protocol-7 guarantee below is the whole contract.

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

## Historical: the protocol-6 fallback gap

Recorded for the reasoning, not as outstanding work.

While an in-place 6 → 7 cutover still existed, it entered maintenance through
the protocol-6 executable, which had no such entry-time check — so on that one
path the preflight scan was the only guard. Slawomir deferred closing it on
2026-08-07 rather than cut a protocol-6 release for a path that was about to
stop being operational.

It then stopped existing: the in-place migration was removed from the tool
altogether. There is no supported cutover that enters maintenance through a
protocol-6 executable, so there is nothing left to defer and nothing to do
before some future cutover. Should a migration path ever be reintroduced, its
source-side maintenance entry needs this same atomic refusal from the start —
that is the lesson worth carrying, and the whole of what remains here.
