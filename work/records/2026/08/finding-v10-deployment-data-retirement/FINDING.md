# Finding: retire v10 deployments, configuration, and mailbox data

## Context

Child of W99. Once v11-only operation is certified, remove the deployed v10 executables/aliases, readiness processes, configuration references, and mailbox data selected by Slawomir's explicit inventory approval. This is the destructive operational track; filing it does not authorize deletion.

## Boundary

- Enumerate exact processes and filesystem targets before mutation.
- Stop and verify every v10 consumer before touching data.
- Leave no alias, service, monitor, or configuration that can restart v10.
- Report what was removed and whether recovery is possible; never broaden a failed cleanup.

## Live inventory — 2026-08-17

**Confirmed:** v10 is still operational and W102 is not yet a deletion task.
The process tree rooted in the operator-run command
`just codex-baton /home/sl/baton/conf/codex-event-bridge.json` currently owns:

- the Codex app server listening at `ws://127.0.0.1:4500`, including the
  `baton.reviewer` session used to perform this review;
- the generic Codex event-socket bridge;
- ten `baton_source.mjs` consumers for `lang.reviewer`,
  `lang_testing.reviewer`, `build.reviewer`, `mariadb.reviewer`,
  `net_tls.reviewer`, `dq.reviewer`, `web.reviewer`,
  `workflows.reviewer`, `pushcoin.reviewer`, and `baton.reviewer`; and
- recurring v10 `wait` children executing
  `/home/sl/baton/app/baton-cli/v10/v10.2.0/bin/baton` against
  `/home/sl/baton/mailbox/v10/baton.json`.

The v11 TUI, Codex readiness producer, and ACP bridge run in parallel from
`/home/sl/opt/baton/v11/...` against `/home/sl/baton-v11/baton.json`; those
paths are outside the candidate retirement root.

**Confirmed target topology:** `/home/sl/baton` contains 55 regular files, 31
directories, and two symlinks. The symlinks are the bounded release aliases
`app/baton-cli/v10/latest -> v10.2.0` and
`app/baton-tui/v10/latest -> v10.2.0`; neither the root nor a top-level target
is a symlink. The root contains only:

- `app/`: deployed v10.2.0 CLI/TUI releases and legacy CLI/TUI copies;
- `conf/codex-event-bridge.json`: the live ten-target v10 stack config;
- `mailbox/`: live `v10`, stale `legacy`, and protocol-9/protocol-10 archive
  mailbox/configuration data; and
- `operations/`: two deployment operation receipts.

No user systemd unit or crontab entry names Baton or Codex. A targeted scan of
current user configuration found no independent restart reference to the v10
deployment or mailbox. The terminal-owned stack above is the known restart
and liveness authority.

## Sequencing correction — 2026-08-17

W102 must complete its controlled stack replacement and v10 shutdown before
W101 removes repository runtime or monitor paths. W101's live process imports
`tools/codex-event-bridge/src/stack.mjs`, `main.mjs`, and `baton_source.mjs` in
addition to the deployed v10 CLI. Removing those paths first would damage the
running coordination channel and could strand the app-server session used to
finish the cutover.

The cutover therefore needs a human-controlled disconnect/reconnect window:
record the current Codex session identity and v11 bridge command, stop the old
combined stack, start a standalone app server, reconnect the session, restart
only the v11 readiness producer, and verify human/Codex/ACP coordination.
Only after that proof may the approved `/home/sl/baton` targets be removed and
W101 begin executable-source removal.

Mailbox deletion is not recoverable unless Slawomir deliberately preserves a
copy first. The deployed binaries/configuration can be reconstructed from
repository history, but that is not a reason to retain an executable fallback.

## Approved live cutover gate — 2026-08-17

Slawomir approved destroying the v10 mailbox/history without an archive, the
shutdown/reconnect window, and deletion of the validated `/home/sl/baton` tree
after reconnection.

The immediately preceding host inventory found the original combined stack
still live: `just codex-baton /home/sl/baton/conf/codex-event-bridge.json`
owns the app server, generic dispatcher, ten v10 `baton_source.mjs` consumers,
and their v10 `wait` children. The current Codex session is
`019ff3f9-30a4-7f60-8b84-f482f8f687b0`; its target is `baton-reviewer` and
event socket is `/home/sl/.local/run/codex-events.sock`. The v11 human TUI and
Claude ACP bridge are independent of `/home/sl/baton`.

The disconnect window therefore belongs to the human operator, not an agent
about to terminate its own transport:

1. Stop the existing v11 Codex readiness producer so only one can return.
2. Stop the foreground combined `just codex-baton` stack.
3. Start `just codex-app-server` from the Baton checkout.
4. Start the generic dispatcher with
   `tools/codex-event-bridge/bin/codex-event-bridge --config
   tools/codex-event-bridge/config.json`.
5. Resume the exact session with `codex resume --remote
   ws://127.0.0.1:4500 019ff3f9-30a4-7f60-8b84-f482f8f687b0`.
6. Start exactly one v11 readiness producer using the exact deployed v11
   `bin/baton`, `/home/sl/baton-v11/baton.json`, participant `baton.codex`,
   target `baton-reviewer`, and the event socket above.

After the resumed reviewer verifies the host process table contains no v10
consumer, it re-enumerates `/home/sl/baton` against the approved inventory and
may perform the bounded deletion. Any unexpected process, path, link, owner,
mount, or failed removal aborts rather than broadening the operation.
