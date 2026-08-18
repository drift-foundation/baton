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
dispatcher, v11 Codex readiness producer, and configured Claude ACP client as
separate processes. Start with the strict example manifest:

    cp conf/infra.example.json /absolute/path/to/mailbox/infra.json

Replace every placeholder. Commands are argument arrays rather than shell
strings, paths are absolute, dependencies are explicit, and each readiness
consumer has a unique participant. Nothing is inferred from the checkout,
current release, running processes, or `baton.json`.

The version-1 manifest accepts global `startTimeoutSeconds` and
`stopTimeoutSeconds` defaults plus a non-empty `services` array. Each service
has a unique `name` and `command`, with optional `after`, `cwd`, `env`,
`requires`, `participant`, and per-service timeouts. Readiness is one of:

- `{"type": "process", "stableMilliseconds": 1000}` for a child that must
  remain alive for a stable interval;
- `{"type": "http", "url": "http://127.0.0.1:PORT/PATH", "expectedStatus": 200}`
  for an explicit loopback probe; or
- `{"type": "unix_socket", "path": "/absolute/path/to/socket"}`.

Unknown keys, duplicate names or participants, dependency cycles, non-absolute
paths, missing required files, and non-private lifecycle files refuse before
launch.

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
