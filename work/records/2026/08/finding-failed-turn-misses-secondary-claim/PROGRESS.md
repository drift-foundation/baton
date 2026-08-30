# Progress: failed managed turn misses a secondary claim

2026-08-29 — Finding recorded from live W39357 evidence. No implementation has
started. Exact operator recovery is pending; the canonical claim is preserved.

## 2026-08-29 — `baton.tuner`

Implemented the bounded W39868 correction in
`tools/codex-event-bridge/src/event_bridge.mjs`. Failed-turn reconciliation
now treats a different canonical live claim as `secondary`, fences on that
claim's exact Work, assignment episode, and action key, and reports only an
empty participant claim slot as released. W4303's exact-original,
uncorrelated, unreadable, durable-fence, and explicit-recovery paths remain in
place.

Extended `tools/codex-event-bridge/test/failed_turn_settlement.test.mjs` with
the W39770/W39357 shape and secondary-claim coverage across ordinary and early
completion, reconnect, retained readiness, later-episode correlation,
dispatcher restart, incident payload, and duplicate completion.

Verification passed:

- Codex event bridge: 421 tests passed.
- Complete v11 parallel gate: 3,323 tests passed.
- Serial/soak v11 gate: 54 tests passed.
- ACP bridge gate: 89 tests passed.
- Final `git diff --check` passed.

No live claim, authority, incident, rendered configuration, installed release,
or managed service was mutated. The implementation is awaiting independent
review; exact W39357 recovery and deployment remain separate operator actions.

2026-08-29 — W39868 now binds the dossier and routes any implementation through
`baton.tune` to `baton.tuner`, preserving `baton.claude` for v12. Immediate
W39357 recovery remains pending and separate.
