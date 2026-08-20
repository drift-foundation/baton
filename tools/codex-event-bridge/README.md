# Codex event bridge

This local integration routes external events to isolated, persistent Codex
threads through `codex app-server`. Each configured target owns an independent
queue and state machine, so a busy thread does not block unrelated targets.

The post-v10 topology and safety boundaries are documented in
[`../../docs/CODEX-APP-SERVER-EVENT-CONNECTIVITY.md`](../../docs/CODEX-APP-SERVER-EVENT-CONNECTIVITY.md).

## Requirements

- Linux
- Node.js 22 or newer; the Codex bridge itself has no npm dependencies
- Codex with `app-server`, `--remote`, and schema generation support
- A protocol-11 Baton executable/configuration for Baton readiness
- `inotifywait` only for the optional watcher example

App-server and its WebSocket transport are experimental. Regenerate and review
the installed schemas whenever Codex changes.

## Process model

Normal repository operation uses the mailbox-local lifecycle recipes to
supervise this configured backend set:

1. one loopback Codex app-server;
2. one generic `codex-event-bridge` dispatcher for its configuration;
3. one `codex-baton-bridge` readiness producer per Baton participant;
4. one configured ACP readiness client and agent session;
5. any number of remote TUI clients attached to the configured threads.

The dispatcher does not spawn readiness producers, and readiness producers do
not spawn app-server or the dispatcher. Their target and socket arguments are
the explicit wiring between them.

Copy `../../conf/infra.example.json` to `MAILBOX/infra.json`, replace every
placeholder with an absolute deployment path, then run from the repository
root:

```bash
just start /absolute/path/to/mailbox
just status /absolute/path/to/mailbox
just stop /absolute/path/to/mailbox
```

The strict manifest is the entire launch contract. The recipes infer no
release, authority, participant, thread, socket, credential, or policy path.
Logs append in `MAILBOX/log/`; private atomic ownership state lives in
`MAILBOX/run/`. Start is idempotent only for the complete healthy owned set,
status is nonzero for any partial or unhealthy set, and stop signals only
recorded matching process identities in reverse dependency order. The
controller never starts a TUI, adopts a manually launched process, or
escalates beyond `SIGTERM`.

The component commands below remain useful for bootstrap, troubleshooting,
and acceptance testing. Stop manually launched components before switching to
the lifecycle recipes.

## 1. Generate and inspect Codex schemas

From this directory:

```bash
codex --version
codex app-server --help
codex --help

mkdir -p .codex-app-server-schema
codex app-server generate-json-schema --out .codex-app-server-schema
codex app-server generate-ts --out .codex-app-server-schema
```

The bridge refuses startup if the generated schema directory lacks a method or
field it consumes.

## 2. Start app-server manually

```bash
codex app-server --listen ws://127.0.0.1:4500
```

Keep the listener on loopback. The validator rejects non-loopback endpoints.
From the repository root, `just codex-app-server` starts this process only.

Check the TUI connection in another terminal:

```bash
codex --remote ws://127.0.0.1:4500
```

## 3. Create participant threads with durable instructions

Create each persistent thread through the bridge bootstrap:

```bash
bin/codex-event-bridge \
    --start-thread \
    --endpoint ws://127.0.0.1:4500 \
    --cwd /absolute/path/to/workspace \
    --baton /absolute/path/to/bin/baton \
    --baton-config /absolute/path/to/baton.json \
    --participant team.member \
    --role role
```

The command resolves the participant's role instructions through the public
Baton CLI before creating anything, starts the thread with those instructions,
records one no-tool bootstrap turn so the thread has a durable rollout, and
then reopens a SECOND connection and resumes the thread to prove it. Only
after that does it print JSON containing the thread ID, selected role, and
accepted configuration generation.

That order is the point. `thread/start` alone returns an id with no rollout
behind it: the bootstrap client can read it, and nobody else can. A thread
created without the first turn cannot be resumed by the dispatcher, or by any
second client a moment later — so the command now refuses rather than printing
a locator that a deployment would record and a dispatcher could never load.
Any failure to persist or to resume is an error naming the thread id, and
nothing is written to stdout.

What this guarantees is the HANDOFF, within one app-server lifetime: the
bootstrap client disconnects and the dispatcher resumes the same thread. It is
deliberately not a promise that the id survives a restart of the stack —
managed starts create fresh agent contexts, so treat a bootstrapped id as
belonging to the start that produced it. `--role` is required, even for a participant who
holds exactly one role: inferring it would mean that giving that participant a
second role later silently changed the persona of every session started here.
A missing or unheld role refuses before thread creation.

List recent IDs without resuming them:

```bash
bin/codex-event-bridge \
    --endpoint ws://127.0.0.1:4500 \
    --list-threads
```

## 4. Configure the dispatcher

Under the lifecycle controller you do not maintain thread ids here at all:
copy `../../conf/codex-event-bridge.template.json` instead, leave its
`{{context.NAME.threadId}}` placeholders alone, and let `just start` render
it — see "Fresh agent contexts" in `docs/BATON-SETUP.md`. The manual form
below is for driving the dispatcher without the controller.

Copy `config.example.json` and replace every placeholder. The relevant shape
is:

```json
{
  "roleInstructions": {
    "binary": "/absolute/path/to/bin/baton",
    "config": "/absolute/path/to/baton.json"
  },
  "servers": {
    "local": { "endpoint": "ws://127.0.0.1:4500" }
  },
  "targets": {
    "baton-tuner": {
      "server": "local",
      "threadId": "<BATON_TUNER_THREAD_ID>",
      "identity": {
        "participant": "baton.tuner",
        "role": "tuner"
      }
    }
  },
  "eventSocket": "/run/user/1000/codex-events.sock"
}
```

Every server/thread pair and every `identity.participant` must be unique.
Different role selections do not make two targets for one participant safe.
When `roleInstructions` is present, every target needs an identity. On every
dispatcher startup, the bridge resolves the accepted text again and supplies
it as `developerInstructions` while resuming each target.

## 5. Verify one protocol turn

Before starting the long-running dispatcher, verify initialization, resume,
`turn/start`, and `turn/completed` for one target:

```bash
bin/codex-event-bridge \
    --config ./config.json \
    --once \
    --target baton-tuner \
    --message 'External event test. Respond that you received it.'
```

For a single target without role-instruction resolution, the low-level
shorthand is:

```bash
bin/codex-event-bridge \
    --endpoint ws://127.0.0.1:4500 \
    --target scratch \
    --thread '<THREAD_ID>' \
    --once
```

## 6. Start the generic dispatcher

```bash
bin/codex-event-bridge --config ./config.json
```

The bridge logs connections, resumed targets, queueing, turn starts,
completions, backoff, and reconnect reconciliation. Its Unix socket is created
with mode `0600`. Use `--debug` only when full protocol traffic is needed;
event contents and other sensitive payloads may appear in debug logs.

## 7. Start Baton readiness producers

Start exactly one producer for each participant:

```bash
bin/codex-baton-bridge \
    --baton /absolute/path/to/bin/baton \
    --config /absolute/path/to/baton.json \
    --participant baton.tuner \
    --target baton-tuner \
    --socket /run/user/1000/codex-events.sock
```

`--target` and `--socket` must match the dispatcher configuration. Optional
`--wait-timeout` and `--retry-ms` control this producer only. Use `--once` to
exit after at least one event is accepted by the dispatcher.

The producer repeatedly invokes:

```text
BATON --config PATH --participant TEAM.MEMBER wait timeout=SECONDS
```

It validates the protocol-11 participant-action envelope and forwards one
compact event per unseen action key. It is read-only and level-triggered: it
never claims Work, responds to obligations, advances a cursor, or mutates the
authority. A key is suppressed while present, forgotten when it disappears,
and delivered again when a new assignment episode makes it actionable.

Run one readiness path per participant. Two producers see the same action set
and can create duplicate turns; they do not divide work between themselves.

## 8. Attach TUIs

```bash
codex resume --remote ws://127.0.0.1:4500 <BATON_TUNER_THREAD_ID>
```

The TUI is an interactive peer on the same thread. It does not own the
dispatcher or readiness producer. Closing it does not stop those processes.

## Send generic events

With a message flag:

```bash
bin/codex-event send \
    --target baton-tuner \
    --source test \
    --type external-test \
    --message 'This event came from outside the TUI. Acknowledge it and report pwd.'
```

Or through stdin:

```bash
echo 'build failed: planner.rs:418' |
    bin/codex-event send \
        --target baton-tuner \
        --source build \
        --type build-failed
```

Use `--socket PATH` or `CODEX_EVENT_SOCKET` when the dispatcher socket differs
from `$XDG_RUNTIME_DIR/codex-events.sock`.

Generic event fields are labelled as untrusted data in the Codex input and
cannot override standing user, developer, repository, sandbox, or approval
instructions. Baton readiness uses a separate trusted local event type and
contains only the action locator and standing-policy cue, never a discussion
body.

## Command integration

`run-and-notify` runs a command directly without a shell, preserves its exit
status, streams output to the terminal, and includes only a bounded output tail
in a failure event:

```bash
bin/run-and-notify --target baton-tuner -- cargo test
```

Successful commands are silent by default. Add `--notify-success` to emit a
success event or `--max-output-bytes BYTES` to change the retained tail.

The optional watcher demonstrates one build-result file rather than every
editor save:

```bash
examples/watch-build-result /tmp/build-result baton-tuner ./bin/codex-event
```

Writing a line beginning with `FAILED` emits a `build-failed` event.

## Same-thread and isolation acceptance

For one target, enter a unique marker through its TUI, then send a generic
event asking for that marker. The response must contain the marker and appear
in the same TUI. Also verify cwd, instruction sources, model, sandbox, approval
policy, and reviewer rather than assuming every setting was inherited.

Before relying on a multi-target dispatcher, perform the five-target gate from
the architecture document: simultaneous events for A/B/C, an interactive turn
for D, and no activity for E. No context, notification, cwd, instruction,
approval state, or output may cross targets.

Approval requests remain a hard gate. The bridge logs server requests but
never answers or approves them. Verify how the attached TUI receives approvals
for bridge-originated turns before using events that may require approval.

## Verification

Run the sandboxed unit suite:

```bash
npm test
```

With a foreground app-server listening on port 4500, the manual local
integration suites are:

```bash
npm run test:unix-socket
npm run test:app-server -- ws://127.0.0.1:4500
npm run test:dispatcher -- ws://127.0.0.1:4500
```

The integration tests create persistent threads, seed their rollouts, exercise
peer subscriptions and concurrent dispatch, and delete only their recorded
test thread IDs afterward.

## Troubleshooting

`cannot connect to Codex app-server`
: Confirm the listener is running and `/readyz` responds. Confirm both server
  and client use the configured loopback endpoint.

`installed app-server schema is incompatible`
: Regenerate both schema forms with the installed Codex executable. Review the
  changed generated types before changing `CodexClient`.

`Baton instructions refused`
: Confirm the dispatcher and bootstrap use the canonical Baton binary and
  accepted config, that every target names both `identity.participant` and
  `identity.role`, and that each participant holds the role its target
  selects. There is no inferred role to fall back on.

`thread/resume` fails
: Re-run `--list-threads`, confirm the thread exists and is not archived, and
  confirm required MCP servers initialize successfully.

`Event stays queued`
: The target may be active, unavailable, reconciling ambiguous delivery, or
  under server overload backoff. Check target-prefixed dispatcher logs.

`Readiness never arrives`
: Confirm the readiness producer is running, its Baton paths identify the
  accepted authority, and its target/socket match the dispatcher.

`Event appears in the wrong conversation`
: Stop the dispatcher and correct the target thread ID. Never assign a
  server/thread pair or Baton participant to multiple targets.

`Turn waits for approval`
: This is expected until approval ownership is validated. Do not weaken the
  sandbox or enable automatic approval as a workaround.
