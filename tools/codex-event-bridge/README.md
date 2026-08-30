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
3. one `codex-baton-bridge` readiness producer per managed Baton participant
   that consumes routed Work;
4. one configured ACP readiness client and agent session;
5. remote TUI clients attached only to dedicated interactive contexts, never
   to a managed background participant's thread.

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

All six operands are required, and `--role` is one of them: it is a field of
the launcher contract below, so it fails here with the other three rather than
indirectly inside the instruction reader.

The command resolves the participant's role instructions through the public
Baton CLI before creating anything, starts the thread with those instructions
AND its launcher contract, records one no-tool bootstrap turn so the thread has
a durable rollout, and then reopens a SECOND connection and resumes the thread
to prove it. Only after that does it print JSON containing the thread ID,
selected role, and accepted configuration generation.

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

### The Baton launcher contract

Every managed context is given its executable, config, participant and role
EXPLICITLY, and may not infer any of them from a repository path, a deployment
symlink, remembered history, another participant, or a filesystem search
(W12229, `work/records/2026/08/finding-shared-mailbox-team-onboarding/findings/
finding-pc-central-runner-stack/findings/finding-codex-launcher-contract/`).

ONE SOURCE, and the carriers differ per family because their transports do:

- a **Codex** context receives a labelled block appended to its
  `developerInstructions`, on `thread/start` and on every `thread/resume`;
- an **ACP** context receives the SAME block in every readiness prompt, and
  the same four values as real environment variables in its own isolated agent
  process — `BATON_BIN`, `BATON_CONFIG`, `BATON_PARTICIPANT`, `BATON_ROLE`,
  derived from that one source rather than supplied beside it.

**W12229 established the ACP environment carrier and W14828 superseded its
SUFFICIENCY.** After a healthy restart the rendered runtime context held the
correct four values, the prompt named none of them, the operator template
spelled none of them, and the fresh model went looking — found a persistent
participant file still pinned to a retired deployment, and made its first
`claim` through an executable that refused the live authority. Environment
delivery remains useful and must agree; it is no longer the model's only
locator. The prompt carrier is what stops a fresh context rediscovering a
stale file, and an `agent.env` entry that disagrees with the accepted `baton`
section refuses startup by key rather than being resolved in favour of either
side.

The Codex carrier is developer instructions because the generated app-server
contract offers nothing better: `thread/start` and `thread/resume` expose
`developerInstructions` and no per-thread environment map, the generic
per-thread `config` override is the one W415 ruled out, and ONE app-server
process hosts every target — so process environment would cross participant
boundaries even if a launcher could set it after start. The labels make the
two families' vocabulary agree; for a Codex context they are instruction text,
not a claim that the shared process has participant-specific environment.

The block carries exactly those four values. Not `identity.actionOwner`, not
`roleInstructions.execPolicyFile`, not configuration contents, not credentials,
and nothing from the ambient environment. Values are JSON-quoted so a space or
a quote in a path is data rather than syntax, and a blank or missing field
refuses rather than rendering a contract with a hole in it.

It is composed from the configured source and the participant and role the
instruction read ALREADY PROVED, so a restart or a configuration refresh
rebuilds it from current configuration rather than from what an old thread
remembers. The renderer is SHARED by both families: the instruction reader
they both use still returns accepted role prose ALONE, and each family
composes the block beside that prose in the carrier its own transport has.
That is the property which lets one rendering serve two adapters instead of
two renderings drifting apart.

Role prose that happens to name a deployment's paths is configuration content,
not an adapter guarantee. W12181 is the counterexample this exists for: a fresh
`pc.plan` context was reached repeatedly and could not claim, because its role
text did not carry the values and nothing else supplied them.

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

Start exactly one producer for each managed participant that consumes routed
Work:

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
exit after at least one event is accepted by the dispatcher — that proves the
TRANSPORT path and deliberately not the claim loop, because acceptance of one
event is not claim acknowledgement.

The producer repeatedly invokes:

```text
BATON --config PATH --participant TEAM.MEMBER wait timeout=SECONDS
```

It validates the protocol-11 participant-action envelope and forwards one
compact event per actionable key. It is read-only: it never claims Work,
responds to obligations, advances a cursor, or mutates the authority.

It is level-triggered against CANONICAL state. An obligation, trial, poke or
refresh request is suppressed while present, forgotten when it disappears, and
delivered again when it returns. A ready unclaimed Work is an OFFER, and the
exact successful atomic `claim` is what clears it (W11910,
`work/records/2026/08/finding-readiness-offer-cleared-before-claim/`): an
accepted event is transport acknowledgement, and the managed turn it schedules
may end without claiming anything. So the offer stays armed while canonical
state reports `ready && unclaimed` and is re-forwarded under a bounded
exponential retry (from `--retry-ms`, capped at 60s); `claimed:true` for that
key acknowledges it; unclaimed offers wait while the participant holds any
claim; at most one unclaimed Work is admitted per poll in canonical order; a
Work first seen already claimed is forwarded once as restart recovery — and a
recovery wake whose delivery FAILED stays eligible, because the claim it was
going to recover cannot acknowledge a wake nobody received; and a key that
stops being actionable withdraws the retained offer.

The dispatcher retains the exact v11 event id for the whole
queued/starting/ambiguous/active lifetime, independently of `dedupWindowMs`,
and refuses a producer retry of a delivery it is still holding with
`reason: "in-flight"`. It releases that identity on withdrawal or terminal
settlement, so a later bounded retry becomes a new turn. `dedupWindowMs` is a
short fingerprint timer that a model turn routinely outlives; it never decided
this, and a generic event from any other source keeps exactly its old rule.

ONE UNCLAIMED WORK BECOMES A TURN AT A TIME, and the dispatcher is where that
is decided. This producer marks an event presented as soon as the socket
accepts it — before the turn starts — so unlike the ACP bridge it cannot know
the head offer's claim-slot outcome, and its rotation can forward a second
unclaimed Work while the first is still running. The pre-turn revalidation each
delivery already performs therefore answers a second question from the same
canonical read: if the participant already holds a claim, the unclaimed
delivery is HELD at the queue head and re-asked every `claimSlotRetryMs`
(default 15s) rather than spending a model turn against an occupied slot. It is
held and never dropped — a dropped offer would need a new episode to come back,
which is this Work's own defect one layer down — and a CLAIMED Work's own
recovery delivery is never held, because it is the claim. Asking the authority
rather than tracking it locally is deliberate: a claim taken by an interactive
turn, another adapter, or an operator at a terminal is invisible to this
dispatcher and exactly as occupying.

Run one readiness path per participant. Two producers see the same action set
and can create duplicate turns; they do not divide work between themselves.
An interactive prompt participant still has a dispatcher target so its exact
context receives role instructions and publishes runtime state, but it has no
readiness producer and is not a routable handler.

## 8. Attach TUIs to dedicated interactive contexts

```bash
codex resume --remote ws://127.0.0.1:4500 <PROMPT_THREAD_ID>
```

The TUI is the interactive peer on its prompt thread. Do not attach it to a
managed background participant's thread: two execution contexts would then
share one participant identity while only the managed target publishes
runtime. The prompt context has no readiness producer. Closing the TUI does
not stop the dispatcher or any managed readiness producer.

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

`Target reports unknown / statusRefreshFailure`
: The dispatcher could not read the configured thread's authoritative status
  after a turn ended, so cached pre-turn state is not trusted. Runtime reports
  `retrying`, `control: status` reports `ready: false`, and queued readiness
  identities remain retained while bounded status rereads continue. An
  authoritative `idle` makes the target reusable again; `systemError` or an
  unrecognized loaded status promotes it to the sticky terminal failure below.
  A transient read error alone does not require a managed restart.

`Target reports systemError / Work is retained but never delivered`
: The configured app-server context is terminally non-deliverable. The
  `terminalFailure` row in `control: status` names the participant, configured
  session, failed turn when known, provider status, current queued-action
  count, and remedy. The dispatcher publishes `failed(internal)`, reports
  `ready: false`, and retains the exact queued readiness identities without
  retrying them into that context. **Stop and start the managed stack** to mint,
  bootstrap, prove, and render a fresh context. Restarting the dispatcher alone
  resumes the same configured thread and is not recovery. A failed turn whose
  thread returns to `idle` is different: after claim settlement it remains
  reusable and drains normally. The app-server's official status model is
  documented in [Codex App Server](https://developers.openai.com/codex/app-server#read-a-stored-thread-without-resuming).

`Target reports tainted / Work is retained but never delivered`
: An unexpected approval request quarantines that managed context for the rest
  of the managed-stack start, because an interrupted turn can leave its intent
  in the persistent context and the next Work delivered there would resume it.
  The `tainted` row in `control: status` names the cause, safe category, the
  approval's turn id, and the Work it was serving. Repair the deployment or
  execution-policy mismatch it reports, then **stop and start the managed
  stack** — a full start mints a fresh context, and Baton's level-triggered
  readiness re-offers the retained Work to it. Restarting the dispatcher alone
  resumes the same configured thread and does not clear the quarantine: the
  fence is persisted under `quarantineDir` (default `.codex-quarantine` beside
  the event socket) and restored at startup. If the row reports
  `tainted.durable: false` the marker could not be written, so the fence is
  process-local — repair the directory and stop/start the stack rather than
  relaunching the dispatcher. A marker that exists but cannot be parsed — or
  whose recorded instant is one the restore could not format — fails closed:
  its bytes are copied to a sibling `.damaged` file and the context loads
  unknown-but-tainted rather than clean, and rather than aborting startup for
  the healthy targets beside it. A restored marker's Work correlation is
  republished only when the record proves one: `exact`, with the turn id whose
  match made it exact, and with locator text already in the trimmed, non-blank
  form the live path stores. Anything else is filed uncorrelated. The turn id
  itself is opaque and is accepted exactly as the live binding accepts it —
  any non-empty string, verbatim — because the origin was proven by equality
  against that stored value.
