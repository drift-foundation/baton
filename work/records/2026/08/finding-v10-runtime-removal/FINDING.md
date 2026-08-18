# Finding: remove the retired v10 runtime

## Context

Child of W99 (`Retire v10 code and data without fallback`). After the v11 messaging gate closes, remove repository runtime code and tests whose only purpose is to implement or operate protocol 10. Preserve historical evidence and release records that cannot execute as a fallback.

## Boundary

- Inventory exact modules, commands, build inputs, tests, and compatibility paths before removal.
- Refuse removal while any active build, deployment, monitor, or documented launch path imports them.
- Keep v11 behavior and its complete gate green after the v10-only surface disappears.

## Revalidated inventory — 2026-08-17

### Remove under W101

These are executable protocol-10 implementation or machinery whose only
product is the retired runtime:

- `src/baton_core/`, `src/baton_tui/`, and `compat/`;
- `tests/core/`, `tests/tui/`, `tests/packaging/`, and
  `tests/candidate.py`;
- `tools/build_release.py`, `tools/build_zipapp.py`, `tools/build_tui.py`,
  `tools/deploy.py`, `tools/migration_guide.py`, `tools/publish_guide.py`, and
  `tools/retire_release.py`;
- tracked v10 build/config artifacts `dist/`, `schema/config-schema.json`, and
  `examples/baton.json`;
- v10-only Just recipes: the old `build`, `test`, `deploy`, alias/resolve,
  migration-guide publication, release verification, and `codex-baton` stack
  entry points. Do not silently rebind those generic names in this removal;
  the surviving explicit v11 recipes remain honest until a later release-flow
  ruling names their final operator vocabulary;
- the v10 Codex readiness monitor/stack:
  `tools/codex-event-bridge/src/baton_source.mjs`, `src/stack.mjs`,
  `bin/baton-codex-monitor`, `bin/codex-baton-stack`, and their focused tests.
  Remove the stack-only `baton` and target-participant configuration fields
  while preserving the generic event-bridge configuration.

`tests/conftest.py` remains for v11 source discovery and serial-marker
registration, but its retired candidate-build explanation is removed.

### Retain under W101

- `src/baton_work/`, `tests/work/`, `tmpl/`, `conf/baton.example.json`, the ACP
  examples, `tools/deploy_work.py`, and `tools/requirements-dev.txt`;
- the generic `tools/codex-event-bridge` app-server/event-socket transport and
  its v11 `codex-baton-bridge` producer. In particular,
  `codex_baton_bridge.mjs`, `config.mjs`, and `send_event.mjs` are packaged by
  `tools/deploy_work.py` and cannot be removed;
- `tools/acp-baton-bridge/` and its tests;
- v10 historical findings, review evidence, release records, and prose.
  W103/W104 decide which current public/operator documents are rewritten or
  retired; W101 does not erase history;
- everything under the live external deployment and mailbox roots. W102 alone
  owns `/home/sl/baton` deployment/data cleanup, and that later destructive
  operation remains human-controlled.

### Confirmed isolation

`baton_work` is a restart, not an extension: its source imports neither
`baton_core` nor `baton_tui`, and `tests/work/test_boundaries.py` enforces the
first half. `tools/deploy_work.py` packages `src/baton_work` directly and reads
none of the v10 catalog, builders, manifests, or deployment tree. The retained
ACP bridge likewise consumes the v11 CLI/JSON contract rather than v10 core
code.

The Codex tool needs surgical cleanup rather than wholesale removal. Its
generic app-server and Unix-socket transport are model plumbing still used by
v11; only `baton_source.mjs` and `stack.mjs` implement the retired v10 wait
grammar/channel envelope.

## Superseding execution order — 2026-08-17

The earlier statement that W101 was implementation-ready after its inventory
is superseded for execution ordering. W102's live audit found the current
combined stack still importing `stack.mjs`, `main.mjs`, `baton_source.mjs`, and
the deployed v10 CLI while also owning the app server for the reviewing Codex
session. W101 must not remove or rewrite those live paths until W102 has
completed the controlled standalone-app-server/v11-readiness cutover and
verified that every v10 consumer is gone.

## Acceptance additions

- No executable source, build recipe, test collector, or current tool config
  imports or invokes a removed v10 path.
- `just test-v11` (including ACP), the retained Codex bridge test suite, and
  v11 deployment/package tests pass after removal.
- A scratch v11 distribution contains `baton_work` and the approved bridges,
  and contains no `baton_core`, `baton_tui`, v10 manifest, or v10 monitor.
- A source/build/tool scan may still find v10 in explicitly historical records
  queued for W103 review, but never in an executable fallback path.
