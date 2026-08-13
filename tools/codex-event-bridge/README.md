# Codex event bridge

This local MVP routes external events to multiple isolated persistent Codex
threads through `codex app-server`. Each target has an independent queue and
state machine, so a busy thread does not block unrelated targets.

The durable architecture and unresolved approval-routing gate are documented
in [`../../docs/CODEX-APP-SERVER-EVENT-CONNECTIVITY.md`](../../docs/CODEX-APP-SERVER-EVENT-CONNECTIVITY.md).

## Requirements

- Linux
- Node.js 22 or newer; no npm packages are required
- Codex with `app-server`, `--remote`, and schema generation support
- `inotifywait` only for the optional watcher example

This tree was developed against `codex-cli 0.147.0`. App-server and its
WebSocket transport are experimental. Regenerate and review schemas whenever
Codex changes.

## 1. Inspect Codex and generate schemas

From this directory:

```bash
codex --version
codex app-server --help
codex --help

mkdir -p .codex-app-server-schema
codex app-server generate-json-schema --out .codex-app-server-schema
codex app-server generate-ts --out .codex-app-server-schema
```

The bridge refuses to start if its required methods or fields are absent from
that generated schema directory.

## 2. Start app-server (low-level development)

```bash
codex app-server --listen ws://127.0.0.1:4500
```

Keep the listener on loopback. The current config validator rejects non-local
endpoints. Normal Baton operation uses the supervised stack below instead; it
starts every configured app-server itself.

## 3. Connect the normal TUI

In another terminal:

```bash
codex --remote ws://127.0.0.1:4500
```

Create or resume the conversation for one logical agent and enter a distinctive
message. Repeat in separate TUI clients for additional isolated agents.

List recent thread IDs without resuming them:

```bash
bin/codex-event-bridge \
    --endpoint ws://127.0.0.1:4500 \
    --list-threads
```

Match the working directory and preview to the intended TUI conversation. Put
each selected ID into a copy of `config.example.json`. A server/thread pair may
belong to only one target.

## 4. Verify one protocol turn

Before starting the daemon, verify initialization, resume, `turn/start`, and
`turn/completed` for one configured target:

```bash
bin/codex-event-bridge \
    --config ./config.json \
    --once \
    --target driftquery \
    --message 'External event test. Respond that you received it.'
```

The same operation can be configured entirely on the command line for a single
target:

```bash
bin/codex-event-bridge \
    --endpoint ws://127.0.0.1:4500 \
    --target driftquery \
    --thread '<THREAD_ID>' \
    --once
```

## 5. Start the bridge

```bash
bin/codex-event-bridge --config ./config.json
```

Use `--debug` only when full protocol traffic is needed; event contents and
other sensitive payloads can appear in debug logs.

The bridge logs server connection, every resumed target, queueing, turn starts,
turn completions, overload backoff, and reconnect reconciliation. Its Unix
socket is created with mode `0600`.

## Start every Codex/Baton session with one command

For normal operation, maintain one machine-level configuration and run one
supervisor for it. Configure one unique Baton participant and one unique
persistent Codex thread for every logical agent; individual repositories must
not start competing bridges or pollers:

```json
{
  "baton": {
    "binary": "/absolute/path/to/bin/baton",
    "config": "/absolute/path/to/mailbox/baton.json"
  },
  "servers": {
    "local": { "endpoint": "ws://127.0.0.1:4500" }
  },
  "targets": {
    "baton-reviewer": {
      "server": "local",
      "threadId": "<BATON_REVIEWER_THREAD_ID>",
      "participant": "baton.reviewer"
    },
    "lang-reviewer": {
      "server": "local",
      "threadId": "<LANG_REVIEWER_THREAD_ID>",
      "participant": "lang.reviewer"
    }
  },
  "eventSocket": "/run/user/1000/codex-events.sock"
}
```

Then run from the repository root:

```bash
just codex-baton /absolute/path/to/config.json
```

That foreground supervisor starts the app-server, shared dispatcher, and one
read-only Baton poller per target. Each poller forwards only its participant's
readiness to its mapped thread. A busy thread queues only its own events; other
threads continue independently. Duplicate participant or thread assignments
fail before startup. Pollers start only after every configured thread has
successfully resumed. If an older per-session Codex backend still owns a
thread, startup names the unavailable target and stops the partial stack. If
any child process exits, the supervisor stops the whole stack rather than
leaving a partially wired deployment behind.

Close old per-session TUIs before the first shared launch. Once the stack is
ready, connect any number of TUIs with `codex resume --remote ENDPOINT
THREAD_ID`, using the configured thread belonging to that logical agent. Stop
the complete stack with `Ctrl-C`. The manual app-server and bridge commands
above remain useful for protocol development and focused troubleshooting.

For example:

```bash
codex resume --remote ws://127.0.0.1:4500 <BATON_REVIEWER_THREAD_ID>
codex resume --remote ws://127.0.0.1:4500 <LANG_REVIEWER_THREAD_ID>
```

Do not omit `--remote` after migration. A plain `codex resume THREAD_ID`
starts an isolated backend and prevents the shared bridge from acquiring that
thread's active-writer lock.

## 6. Send events

With a message flag:

```bash
bin/codex-event send \
    --target driftquery \
    --source test \
    --type external-test \
    --message 'This event came from outside the TUI. Acknowledge it and report pwd.'
```

Or through stdin:

```bash
echo 'build failed: planner.rs:418' |
    bin/codex-event send \
        --target driftquery \
        --source build \
        --type build-failed
```

Use `--socket PATH` or `CODEX_EVENT_SOCKET` if the daemon socket is not the
default `$XDG_RUNTIME_DIR/codex-events.sock`.

External fields are labelled as untrusted data in the Codex input. They cannot
override standing user, developer, or repository instructions.

Baton readiness is deliberately terse: trusted local readiness from the user's
Baton process appears as one `[BATON READY]` line containing the exact message
ID or notice readiness. It contains no mailbox body. The bridge omits the
duplicated `wait` JSON and generic event-evaluation paragraph for these
wakeups. Other external event types retain the full safety and evidence
envelope.

## 7. Command integration

`run-and-notify` runs a command directly without a shell, preserves its exit
status, streams output to the terminal, and includes only a bounded output tail
in a failure event:

```bash
bin/run-and-notify --target driftquery -- cargo test
```

Successful commands are silent by default. Add `--notify-success` to emit a
`build-succeeded` event. Change the retained tail with
`--max-output-bytes BYTES`.

The optional `inotifywait` demonstration watches one build-result file rather
than every editor save:

```bash
examples/watch-build-result /tmp/my-project-build-result driftquery ./bin/codex-event
```

Writing a line beginning with `FAILED` to that file emits a `build-failed`
event.

## 8. Same-thread and isolation acceptance

For one target, enter this through its TUI:

```text
Remember the marker ALPHA-917 for this session.
```

Then send:

```bash
bin/codex-event send \
    --target driftquery \
    --source acceptance \
    --type continuity-test \
    --message 'What marker did I give you earlier?'
```

The answer must contain `ALPHA-917` and appear in that target's TUI. Also verify
its working directory, instruction sources, model, sandbox, approval policy,
and approval reviewer rather than assuming all settings were inherited.

Before relying on the dispatcher, perform the five-target gate from the
architecture document: simultaneous events for A/B/C, an interactive turn for
D, and no activity for E. No context, notification, cwd, instruction, or
approval state may cross targets.

Approval requests remain a hard gate. The bridge logs them but never answers or
approves them. Verify experimentally whether a TUI can act on approvals for a
bridge-originated turn before using events that may require approval.

## Verification

Run the sandboxed unit suite:

```bash
npm test
```

With a foreground app-server already listening on port 4500, the manual local
integration suites are:

```bash
npm run test:unix-socket
npm run test:app-server -- ws://127.0.0.1:4500
npm run test:dispatcher -- ws://127.0.0.1:4500
```

The app-server tests create persistent threads because another connection
cannot resume an ephemeral or zero-turn thread in the tested build. They seed
the rollouts, exercise peer subscriptions and concurrent dispatch, and delete
only their recorded test thread IDs afterward.

## Troubleshooting

`cannot connect to Codex app-server`
: Confirm the server is running and `/readyz` responds. Confirm both server and
  client use `ws://127.0.0.1:4500`.

`installed app-server schema is incompatible`
: Regenerate both schema forms with the installed Codex executable. Review the
  changed generated types and update only `CodexClient` for protocol changes.

`thread/resume` fails
: Re-run `--list-threads`, confirm the thread exists and is not archived, and
  confirm required MCP servers initialize successfully.

Event stays queued
: The target may be active, unavailable, reconciling an ambiguous delivery, or
  under server overload backoff. Check the target-prefixed daemon logs.

Event appears in the wrong conversation
: Stop the bridge and correct the target's thread ID. Do not assign one
  server/thread pair to multiple targets.

Turn waits for approval
: This is expected until approval ownership is validated. Do not weaken the
  sandbox or enable automatic approval as a workaround.
