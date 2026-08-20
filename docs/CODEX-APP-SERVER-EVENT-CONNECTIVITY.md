# Codex app-server event connectivity

## Purpose

One generic event dispatcher routes external events to isolated, persistent
Codex threads through one or more Codex app-server instances. Baton readiness
is one event source: a separate protocol-11 producer reads one participant's
canonical `wait` projection and forwards compact readiness events to that
participant's configured target.

For normal repository operation, one mailbox-local lifecycle controller owns
the explicitly configured backend set. App-server, the dispatcher, and each
readiness client remain separate child processes; none discovers, adopts, or
silently restarts another.

The installed Codex schemas are the executable protocol contract. The
official [Codex app-server documentation](https://developers.openai.com/codex/app-server)
describes the integration surface, loopback WebSocket listener, and remote
TUI. App-server and its WebSocket transport remain experimental.

## Post-v10 topology

```text
                         codex --remote ENDPOINT
                                  │
                                  ▼
Other local producers ─┐    Codex app-server
                       │      │    │    │
Baton wait, participant A     A    B    C persistent threads
  │                    │      ▲    ▲    ▲
  └─ codex-baton-bridge│      │    │    │
                       ▼      └────┬────┘
Baton wait, participant B   app-server protocol
  │                    │           ▲
  └─ codex-baton-bridge┴─> Unix socket 0600
                                  │
                                  ▼
                         codex-event-bridge
                      validate / dedupe / route
                       one queue per target
```

The processes have deliberately separate responsibilities:

- `codex app-server` owns conversations, turns, approvals, and authoritative
  thread state.
- `codex-event-bridge` owns the Unix socket, target mapping, event validation,
  deduplication, per-target queues, app-server connections, and configured
  thread resumes.
- One `codex-baton-bridge` process owns the sole readiness path for one Baton
  participant. It reads `wait` and emits events; it never claims Work, answers
  obligations, marks messages seen, or changes authority state.
- A remote Codex TUI is an interactive peer on the same persistent thread. It
  is not driven through keystrokes or terminal automation.

No backend process starts or silently restarts another. The lifecycle
controller starts them in declared dependency order and stops only the exact
process identities it recorded. Failure of one component remains visible and
does not imply that the others stopped.

## Normal lifecycle

Copy `conf/infra.example.json` to `MAILBOX/infra.json`, then replace every
placeholder with an absolute deployment path. The manifest is strict JSON and
is the entire launch contract; the recipes infer no release, authority,
participant, thread, socket, credential, or policy path.

```bash
just start /absolute/path/to/mailbox
just status /absolute/path/to/mailbox
just stop /absolute/path/to/mailbox
```

`start` brings up the declared services in dependency order and is idempotent
only when the complete owned set is healthy. `status` reports every service,
PID, health state, and log and succeeds only for that complete healthy set.
`stop` sends `SIGTERM` in reverse dependency order to processes whose recorded
Linux start identity and argv still match; it never adopts a process and never
escalates to a force signal.

Logs append beneath `MAILBOX/log/`. Private atomic ownership state lives
beneath `MAILBOX/run/`. A partial, stale, changed, or tampered set refuses a
new start; inspect it with `status`, correct any manifest problem, and use the
bounded `stop`. These commands never start or stop a TUI.

## Configuration model

The dispatcher uses the post-v10 schema in
`tools/codex-event-bridge/config.example.json`:

```json
{
  "roleInstructions": {
    "binary": "/absolute/path/to/bin/baton",
    "config": "/absolute/path/to/baton.json"
  },
  "servers": {
    "local": {
      "endpoint": "ws://127.0.0.1:4500"
    }
  },
  "targets": {
    "baton-tuner": {
      "server": "local",
      "threadId": "019c0000-0000-7000-8000-000000000001",
      "identity": {
        "participant": "baton.tuner",
        "role": "tuner"
      }
    }
  },
  "eventSocket": "/run/user/1000/codex-events.sock"
}
```

A target name is a local routing identifier, not a Codex or Baton identity.
Each server/thread pair belongs to one target. Each Baton participant also
belongs to one target, preserving one readiness consumer and one deterministic
thread destination. Selecting different roles does not make duplicate
participant assignments safe.

`roleInstructions` identifies the canonical Baton CLI and accepted
configuration. The dispatcher does not read `baton.json` directly. Before it
connects targets, it invokes the participant-relative `instructions` read for
each `identity` — which names both the participant and one explicit role — and
reapplies the accepted text as `developerInstructions` on every configured
thread resume. A target missing a role, or naming one its participant does not
hold, refuses before any connection. There is no inferred role: a participant
holding one role today may hold two tomorrow, and that edit must not silently
change an existing session's persona.

The removed stack-owned `baton` block and legacy target `participant` field
are not part of this schema. Readiness timing and retries belong to each
separately launched readiness producer.

## Manual startup and troubleshooting

The following low-level commands expose each component independently. Use
them for configuration, bootstrap, diagnostics, and the documented acceptance
gates. A manually launched process is deliberately not adopted by
`just start`; stop it before switching to lifecycle ownership.

### 1. Start the loopback app-server

```bash
codex app-server --listen ws://127.0.0.1:4500
```

The repository's `just codex-app-server` recipe is a low-level convenience for
this one process. It does not start the dispatcher or readiness producers.

### 2. Create this start's participant threads

Under `just start` this step is not manual: the manifest declares a CONTEXT
per Codex participant, the controller runs the bootstrap once the app-server
is ready, and the dispatcher's configuration is rendered from a template with
the minted ids substituted in. See "Fresh agent contexts" in
`docs/BATON-SETUP.md`; `conf/infra.example.json` and
`conf/codex-event-bridge.template.json` are the shipped pair.

Run it by hand only when you are driving the backend without the lifecycle
controller. Either way the thread is created through the bridge bootstrap, so
the accepted Baton role instructions are present from its first turn:

```bash
tools/codex-event-bridge/bin/codex-event-bridge \
    --start-thread \
    --endpoint ws://127.0.0.1:4500 \
    --cwd /absolute/path/to/workspace \
    --baton /absolute/path/to/bin/baton \
    --baton-config /absolute/path/to/baton.json \
    --participant baton.tuner \
    --role tuner
```

The command records one no-tool bootstrap turn and then resumes the thread on
a second connection before printing anything: `thread/start` alone leaves an
id with no durable rollout, which only the creating client can read. It prints
JSON containing the thread ID, selected role, and accepted configuration
generation, and it FAILS — printing no locator — if the thread cannot be
persisted or cannot be resumed.

That covers the handoff this start needs: the bootstrap client disconnects and
the dispatcher you launch next resumes the same thread. Put that ID and
identity into the dispatcher configuration FOR THIS START — which the
lifecycle controller does for you, into private `run/` state, when the
manifest declares the context. A bootstrapped id
belongs to the app-server lifetime that produced it — managed starts create
fresh agent contexts, so bootstrap again rather than carrying an id across a
restart. Existing manually prompted threads are bootstrap compatibility
only; deliberately recreate or resume them through this path when durable role
instructions become authoritative.

### 3. Start the generic dispatcher

```bash
tools/codex-event-bridge/bin/codex-event-bridge \
    --config /absolute/path/to/codex-event-bridge.json
```

Startup validates the configuration and generated Codex schemas, resolves all
role instructions, connects each named app-server, and resumes each configured
thread. It creates the event socket with mode `0600`.

### 4. Start one readiness producer per participant

```bash
tools/codex-event-bridge/bin/codex-baton-bridge \
    --baton /absolute/path/to/bin/baton \
    --config /absolute/path/to/baton.json \
    --participant baton.tuner \
    --target baton-tuner \
    --socket /run/user/1000/codex-events.sock
```

The target and socket must exactly match the dispatcher configuration. Start
one process for every configured participant and exactly one process for each
participant. A second producer sees the same level-triggered action set and
can manufacture duplicate Codex turns.

### 5. Attach the interactive TUI

```bash
codex resume --remote ws://127.0.0.1:4500 THREAD_ID
```

The endpoint selects app-server; the thread ID selects the logical agent.
Attaching the TUI neither starts nor owns the dispatcher or readiness
producer.

## Baton readiness flow

```text
participant-relative `wait`
        │
        ▼
validate protocol, projection, participant and typed action keys
        │
        ▼
one compact event addressed to the configured target
        │
        ▼
target FIFO -> turn/start on the persistent thread
        │
        ▼
agent re-reads detail and claims or resolves through the canonical v11 CLI
```

Readiness is an edge to re-evaluate, never authority to execute. The producer
forwards Work assignment episodes, directed obligations, and due verification
trials using stable action keys. It suppresses a key while it remains present,
forgets it when it disappears, and emits it again if a new episode makes it
actionable later. Restarting the producer deliberately rediscovers the current
set.

The resulting trusted turn input is compact, for example:

```text
[BATON READY] v11 Work W6 (...) is ready and unclaimed for baton.tuner. Act through the canonical v11 CLI (detail work=W6). Apply standing v11 Baton policy.
```

It contains locators, not discussion bodies. The awakened agent must still
perform the atomic claim or other canonical operation; the producer never does
that on its behalf.

## Generic event producers

Other local producers know only the Unix event socket and target name. A
normalized event carries its destination explicitly:

```json
{
  "target": "baton-tuner",
  "source": "build",
  "type": "build-failed",
  "summary": "planner tests failed"
}
```

These fields are untrusted data when presented to Codex. They cannot override
user, developer, repository, sandbox, or approval instructions. Baton events
are a distinct trusted local type because they are produced from the user's
canonical Baton CLI and contain no mailbox or discussion body.

## Dispatcher and per-target lifecycle

The dispatcher validates and normalizes each event, rejects unknown targets
or size/capacity violations, deduplicates within the target, and appends the
event to that target's FIFO. One busy thread does not block unrelated targets.

Each target can be unavailable, active, apparently idle, or reconciling.
App-server acceptance or rejection of `turn/start` is authoritative; local
idle state is only an optimization. If a TUI wins the race, the dispatcher
keeps the event, refreshes that target, and retries with bounded backoff.

Every queued event receives a stable `clientUserMessageId`. When a connection
drops after submission but before response, the dispatcher resumes/reads the
thread and looks for the matching persisted client ID before deciding whether
to dequeue or retry. This is a reconciliation key, not an assumption that
`turn/start` is idempotent.

Queues survive an app-server disconnect while the dispatcher process remains
alive. They are not crash-durable; restarting the dispatcher loses in-memory
events. A disconnected server pauses only its targets, while targets assigned
to other servers continue.

## Security and approval boundaries

- Keep the MVP listener on loopback. Plain WebSockets are only for localhost
  or an explicitly secured forwarding arrangement.
- The producer socket is mode `0600`; the dispatcher never replaces an
  existing non-socket path.
- Unknown targets and oversized events refuse before queueing.
- Debug logging may contain complete event and protocol payloads.
- The bridge never changes sandboxing, approval policy, reviewer, or execution
  permissions.
- Approval requests remain a human-action gate. The dispatcher never approves
  one automatically — and, since W3243, never leaves one unanswered either.
  Dispatcher-owned readiness turns are NON-INTERACTIVE execution: the request
  is explicitly DENIED with a protocol error, which no app-server can read as
  permission, and the turn is interrupted if it has not ended within
  `approvalRecoveryMs` (default 15s). Until that turn actually ends the target
  reports `deliverable: false` and the whole stack reports `ready: false`,
  with the participant, thread, turn, cause, queue depth and oldest queued age
  in `control: status`. Readiness events queued behind it are RETAINED and
  drain when the turn ends.
  Leaving the request unanswered was the defect: a target sat in
  `waiting-input(approval)` for over ten hours while 24 later readiness events
  queued behind it and the stack reported it healthy, because it was connected
  and loaded. If denial and interrupt both fail, the target stays visibly
  unhealthy and the operator restarts the managed stack, whose
  fresh-context-per-start policy supplies a clean target; the dispatcher does
  not create a replacement context, which is v12's worker supervisor's job.

Approval ownership must be tested for bridge-originated and TUI-originated
turns. If an approval is delivered only to the initiating connection, a
supported human relay is required; weakening policy is not a workaround.

## Isolation acceptance

Before relying on the topology, test one app-server, five isolated threads,
five TUIs, one dispatcher, and the required readiness producers:

1. Send simultaneous events to A, B, and C.
2. Start an interactive TUI turn for D and leave E idle.
3. Verify A/B/C run independently, D is unaffected, and E remains untouched.
4. Verify thread markers, cwd, instructions, model, sandbox, approval state,
   notifications, and output never cross targets.
5. Verify reconnect reconciliation and ambiguous-delivery handling do not
   create duplicate turns.
6. Verify both approval ownership directions remain human-actionable.

Passing this gate establishes that the local app-server can support the
configured isolated agents. It does not turn the experimental transport into
a production-supported OpenAI interface.
