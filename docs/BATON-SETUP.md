# Setting up this Baton coordination home

`baton init` wrote one strict-JSON configuration for you to edit:

`baton.json` — the generation-one authority configuration. It is
deliberately INCOMPLETE: add your teams (participants, roles, routes,
kinds) and, if you use repository dossiers, the `roots` catalog. Each
root declares its explicit absolute `base` path right here — baton.json
is the single root config; there is no separate machine-local resolver
file and no filesystem inference. Do not add comments; the file must
stay strict JSON.

EVERY declared role must carry a non-empty `instructions` string. This is
not advice for agent-backed roles: a configuration with any uninstructed role
is incomplete and is refused at acceptance, because an agent launched into
such a role would fall back to whatever prompt an operator remembered — the
one-off prompt this configuration exists to retire.

That text is durable accepted configuration. It is owned by the ROLE and
inherited by every member launched in it; it is never copied into member
entries, so correcting one role's text corrects every session started from it.

Write each role's instructions to cover both halves of the bootstrap
contract:

- the role's authority, responsibilities, exclusions, and handoff boundary;
- the required reading — repository policy and any operating or
  role-specific document the agent needs before its first assignment.

Read directives are instruction text, so they may name repository-relative
files, configured-root references such as `myroot:AGENTS.md`, or other
deployment material. The agent, not the launcher, reads and applies what they
name; a file it cannot read is reported as an operational finding rather than
silently dropped.

A launcher resolves the text through:

    baton --config baton.json --participant team.member instructions role=ROLE

`role=` is always required, even when the participant holds exactly one role.
Inferring it would mean that giving that participant a second role later
silently changed the persona of every session launched for them. An unheld
role refuses rather than starting an agent with a persona it was not given.

When the configuration is complete, activate the authority:

    baton --participant team.member activate directory=.

Activation runs the one authoritative validation and creates the
unique SQLite database only if the document passes; a refusal leaves
nothing behind, so edit and retry freely. After activation, members
open the instance with `--config baton.json --participant team.member`.
After a later `regen` changes role instructions, restart or resume each
launcher so it applies the newly accepted generation. Existing sessions are
not retroactively rewritten; a manually prompted bootstrap session remains a
bootstrap until it is relaunched through the configured path.

## Run the local v11 backend set

The repository lifecycle recipes supervise the Codex app-server, generic
dispatcher, one isolated context and runtime publisher for every configured
Codex participant, v11 readiness producers for the background participants
that consume routed Work, and the configured ACP clients as separate
processes. A human-attached prompt context is a dispatcher target so its
runtime is visible, but it has no readiness producer. Start with the strict
example manifest:

    cp conf/infra.example.json /absolute/path/to/mailbox/infra.json
    cp conf/codex-event-bridge.template.json /absolute/path/to/mailbox/
    cp conf/acp-{claude,gemini}.template.json /absolute/path/to/mailbox/

Replace every deployment placeholder in the manifest and three templates;
leave lifecycle-owned `{{context.*}}`, `{{render.*}}`, and `{{start.id}}`
references intact. Commands are argument arrays rather than shell strings,
paths are absolute, dependencies are explicit, and each readiness consumer
has a unique participant. Nothing is inferred from the checkout, current
release, running processes, or `baton.json`.

**Manifest version 2 adds the control identity.** A version-2 document
carries one `control` block naming the canonical Baton binary, config and
participant the lifecycle manager uses for `drain`, `resume` and `dispatch`:

    "version": 2,
    "control": {
      "binary": "/absolute/path/to/v11-release/bin/baton",
      "config": "/absolute/path/to/mailbox/baton.json",
      "participant": "baton.slaw"
    }

The identity is NAMED, never inferred from a service's argv: two services may
run different participants against different configs, and the act this
authorizes suspends the whole deployment. The named participant must hold the
accepted-configuration `dispatch` capability — the authority checks that in
its own transaction, so granting it is a configuration change with its own
accepted generation, not a manifest edit. A version-1 manifest stays valid and
simply has no drain, resume or dispatch-status commands; the manager refuses
them with an actionable message rather than guessing an identity.

See "Maintenance: draining managed dispatch" in `docs/EFFECTIVE-BATON.md` for
the operator sequence, including why plain `stop` is unchanged and
`stop-drained` is the graceful one.

The version-1 manifest accepts global `startTimeoutSeconds` and
`stopTimeoutSeconds` defaults plus a non-empty `services` array. Each service
has a unique `name` and `command`, with optional `after`, `cwd`, `env`,
`requires`, `participant`, and per-service timeouts. Readiness is one of:

- `{"type": "process", "stableMilliseconds": 1000}` for a child that must
  remain alive for a stable interval;
- `{"type": "http", "url": "http://127.0.0.1:PORT/PATH", "expectedStatus": 200}`
  for an explicit loopback probe; or
- `{"type": "unix_socket", "path": "/absolute/path/to/socket"}`, which
  proves a CONNECTION — and, with the optional pair below, an ANSWER.

A connection is the complete health contract for some services and a
half-truth for others. The Codex dispatcher starts listening before its
configured targets resume and keeps listening when one cannot load at all,
so a socket probe reported it healthy while Work queued behind a target
nothing would drain. It already knows better, and can be asked:

    "readiness": {
      "type": "unix_socket",
      "path": "/absolute/path/to/runtime/codex-events.sock",
      "request": {"control": "status"},
      "expect": {"ready": true}
    }

`request` and `expect` are configured together or not at all — a request with
nothing to assert proves no more than the connection did. The controller
sends one newline-delimited JSON line and reads one back, bounded; `expect`
matches required TOP-LEVEL reply fields, and the reply may carry any number
of diagnostic fields beside them. This version matches fields and grows no
expression language.

The dispatcher's own `ready` is true only when EVERY configured target is
connected, loaded in a reusable `idle` or `active` app-server status, and free
of a delivery fence. `systemError` is loaded but terminally non-deliverable;
an unrecognized future status fails closed too. That is the intended policy:
a target configured in a managed dispatcher is required by that deployment,
so there is no `any` or named-subset form. An optional target is omitted rather
than tolerated.

A terminal turn whose status refresh cannot be read is reported as transient
`status: unknown` with a `statusRefreshFailure` diagnostic. Runtime publication
is `retrying`, lifecycle health is false, and queued readiness remains retained
while the dispatcher rereads the configured thread with bounded backoff. An
authoritative reusable status clears that transient fence; an authoritative
terminal status becomes the sticky terminal failure above. The read error
alone is never diagnosed as `systemError`.

A malformed, oversized, truncated, late or mismatched reply is "not ready
yet", exactly as an absent socket is. A target slow to resume therefore holds
startup until the service's existing `startTimeoutSeconds` and then fails
through the ordinary rollback; a target that becomes unloadable or enters
`systemError` after a successful start makes later `just status` unhealthy,
and Baton kills or restarts nothing on its own.

Unknown keys, duplicate names or participants, dependency cycles, non-absolute
paths, missing required files, and non-private lifecycle files refuse before
launch.

### Fresh agent contexts

An agent's execution context — a Codex Thread, an ACP session — is
replaceable runtime state, not deployment configuration. The stable identity
is the Baton participant; the context behind it is minted by the start that
uses it, and a later start mints another. Carrying one across a restart
carries obsolete paths baked into its instructions, conversational
assumptions that no longer match the tree, and possibly an old writer that
still believes it holds work.

The mapping is one-to-one in both directions. One participant names one live
execution context, and one context runs as one participant. Do not attach a
human TUI to a managed background participant's thread: the foreground and
background contexts would then share claims and runtime identity even though
only the managed context publishes `Run`. Give the interactive context its
own participant, role, lifecycle context and dispatcher target. The dispatcher
then publishes runtime for that exact target, while omission of a readiness
service keeps routed Work away from it. `conf/infra.example.json` demonstrates
this with `baton.prompt` beside the managed `baton.codex` reviewer.

So the manifest declares CONTEXTS beside its services:

    "contexts": [
      {
        "name": "tuner",
        "participant": "baton.tuner",
        "after": ["codex-app-server"],
        "command": ["/absolute/path/to/codex-event-bridge",
                    "--start-thread", "--endpoint", "ws://127.0.0.1:4500",
                    "--cwd", "/absolute/path/to/workspace",
                    "--baton", "/absolute/path/to/bin/baton",
                    "--baton-config", "/absolute/path/to/baton.json",
                    "--participant", "baton.tuner", "--role", "tuner"],
        "timeoutSeconds": 120
      }
    ]

A context is not a service: it is a short-lived command that runs once its
`after` services are ready, must exit 0, and must print one JSON object
containing at least `threadId`. There is no pid to own and nothing to stop —
what it leaves behind is a locator.

Services reach that locator with `{{context.NAME.FIELD}}` in `command`,
`cwd`, `env` values, or `requires`. `{{start.id}}` is this start's own
identifier, available in the same places.

Not every agent has a locator to mint. An ACP participant has a state
DIRECTORY, and its bridge refuses a `new` session when a selection is already
there and resumes one when configured to `load` — neither of which may be
weakened. Giving each start its own `stateDir` through `{{start.id}}` gets a
genuinely fresh session with both rules intact: absence is exactly what `new`
requires, and the previous start's selection stays where it was, as history. A component that reads a config FILE
renders one instead:

    "renders": [{"name": "dispatcher",
                 "template": "/absolute/path/to/dispatcher.json.tmpl"}]

The template is the operator's and is never written to; the result is written
under `MAILBOX/run/context/NAME.json` at mode 0600, with the same
substitution applied, and the service names it with `{{render.NAME}}`.

The rules the controller enforces:

- a placeholder naming a context or render this start does not have refuses
  at load, before anything launches — INCLUDING one inside a render
  template, which is read and checked at load like any other part of the
  service's configuration, and which the start then renders from the body it
  validated rather than reading the file a second time;
- a render cannot be built from another render;
- a render nothing references refuses too — a file written for nobody is a
  configuration mistake, not a feature;
- every start begins with an EMPTY context map and clears what a previous
  start rendered, so nothing can be inherited by accident;
- a context that cannot mint — a non-zero exit, unreadable output, or no
  `threadId` — fails the start rather than falling back on an older locator;
- a failed start that rolls back completely removes its rendered files, so
  the next start cannot read a locator this one abandoned.

Minted locators are recorded in `MAILBOX/run/infra-state.json` under
`contexts`. Operators do not edit durable deployment JSON to rotate them.

### Proving a restart against real backends

The repository's own tests prove this against stand-in agents. Against real
ones, the check is two starts and four comparisons:

    just start   /absolute/path/to/mailbox
    jq -r '.startId, .contexts[].threadId' /absolute/path/to/mailbox/run/infra-state.json
    "$BATON" --config .../baton.json --participant baton.tuner wait timeout=0
    just stop    /absolute/path/to/mailbox

    just start   /absolute/path/to/mailbox
    jq -r '.startId, .contexts[].threadId' /absolute/path/to/mailbox/run/infra-state.json
    "$BATON" --config .../baton.json --participant baton.tuner wait timeout=0

What must CHANGE between the two: the start id, every minted `threadId`, and
the `stateDir` in both `MAILBOX/run/context/claude-acp.json` and
`MAILBOX/run/context/gemini-acp.json`. What must NOT: the participant
addresses, and the actionable Work each `wait` returns — an agent's position
comes from Baton, not from the context it happens to be running in.

Also compare `baton runtime` with `infra-state.json`: every configured context
must have a unique participant and thread id, and each participant's runtime
session must name that same thread. A dedicated interactive prompt appears in
both inventories but has no readiness service and no routed Work. If either a
participant names two contexts or one context is published for two
participants, stop the deployment rather than offering more Work.

What must still be THERE afterwards: the previous start's ACP selection, under
its own start id. A restart replaces the context an agent works in; it does
not erase what the last one did.

From the repository root:

    just start /absolute/path/to/mailbox
    just status /absolute/path/to/mailbox
    just stop /absolute/path/to/mailbox

Start is idempotent only when the complete owned set is healthy. Status names
every configured service, PID, state, and log and exits nonzero for a stopped,
partial, stale, changed, or unhealthy set. Stop sends `SIGTERM` in reverse
dependency order only after the recorded process start identity and argv still
match; it refuses unknown ownership and never force-kills a child.

Logs append beneath `MAILBOX/log/`; private lifecycle state lives beneath
`MAILBOX/run/`. The controller never launches a TUI and never adopts a process
started by hand. Low-level component commands and topology details remain in
[CODEX-APP-SERVER-EVENT-CONNECTIVITY.md](CODEX-APP-SERVER-EVENT-CONNECTIVITY.md).
