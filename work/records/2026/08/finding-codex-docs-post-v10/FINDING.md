# Finding: the Codex documents describe a stack that does not exist yet

## Context

Split out of W103 (`Rewrite public docs and architecture for v11`) at its
round-one review, which ruled that W103 "cannot close until those required
surfaces are rewritten after W101, or until an explicit separately tracked
child contract owns them and keeps this parent open."

## The blocked surface

- `docs/CODEX-APP-SERVER-EVENT-CONNECTIVITY.md`
- `tools/codex-event-bridge/README.md`

Both still present the combined `just codex-baton` protocol-10 monitor stack
as normal operation, with a stack-owned Baton configuration and
`baton-codex-monitor` vocabulary.

## Why it cannot be written yet

W103's own finding requires these documents to describe the shape that exists
AFTER W101 removes `src/baton_source.mjs`, `src/stack.mjs`,
`bin/baton-codex-monitor`, and `bin/codex-baton-stack`. Writing that prose
against today's tree would document a system nobody can run — precisely the
hybrid W103 forbids.

W101 is itself blocked by its own superseding execution order: it must not
remove those paths until W102 completes the standalone-app-server cutover and
verifies every v10 consumer is gone. As of 2026-08-17 that constraint is live
rather than theoretical — processes are running `stack.mjs` and
`baton_source.mjs` directly from the working tree, alongside the deployed v10
CLI, and they own the app server for the reviewing Codex session.

## Acceptance boundary

- Rewritten around a standalone loopback app server, the generic event
  dispatcher, and the separately launched v11 `codex-baton-bridge` readiness
  producer.
- No v10 overlap procedure, stack-owned Baton config, or
  `baton-codex-monitor`/`codex-baton-stack` vocabulary survives.
- Configuration examples validate against the post-W101 generic bridge schema.
- Covered by the same standing active-document scan the rest of the cutover
  uses, so the surfaces cannot silently regress.

## Ordering

W102 -> W101 -> this record. Nothing here may land before W101 has actually
removed the paths; a documentation change that anticipates a removal is the
same defect as one that lags it.
