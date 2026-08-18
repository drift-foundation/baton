# Finding: one command must own the local v11 infrastructure lifecycle

## Observed — 2026-08-18

The first v11-only cutover requires four separately launched foreground
processes:

1. the Codex app server;
2. the generic Codex event dispatcher;
3. the v11 Codex readiness producer; and
4. the Claude ACP readiness client and agent session.

The operator must remember their ordering, exact release/config paths, log
destinations, duplicate-consumer rule, and shutdown order. The cutover itself
demonstrated the failure mode: restarting the old convenience supervisor also
restarted every retired v10 consumer.

## Confirmed direction — 2026-08-18

Provide a repository-level first iteration with exactly these operator verbs:

```text
just start MAILBOX
just stop MAILBOX
just status MAILBOX
```

`MAILBOX` is the v11 coordination-home directory, such as the stable
`/home/sl/baton-v11` locator. The recipes are the initial UX, not a claim that
Just is the final installed product interface.

- `start` brings up the configured backend set, including the Codex app
  server/dispatcher/readiness path and the Claude ACP client. It never starts a
  TUI and never infers a release, authority, participant, repository, agent,
  thread, credential, or policy path.
- `stop` stops only processes previously started and identified by this
  mailbox's lifecycle state, in reverse dependency order. It refuses an
  unknown or PID-reused process rather than killing it.
- `status` reports every configured service, PID, health/state, and log path.
  It exits successfully only when the complete configured set is healthy; a
  stopped, partial, stale, or contradictory set is visible and nonzero.
- Logs live beneath `MAILBOX/log/`, one append-only stream per named service.
  Private lifecycle metadata lives beneath `MAILBOX/run/`; both directories
  are created with private permissions. A coordination-home cutover must stop
  the old set before repointing its stable locator.

## Configuration boundary

The mailbox owns an explicit `infra.json` manifest. Commands are argument
arrays, not shell strings. Each service has a unique short name, exact command,
optional working directory/environment, dependency order, and an explicit
readiness check where one exists. The first checked-in example describes:

- Codex app-server readiness by its configured loopback endpoint;
- generic dispatcher readiness by its configured Unix event socket;
- one `codex-baton-bridge` for `baton.codex`; and
- one deployed `acp-baton-bridge` using the deployment-owned Claude load
  configuration.

This manifest is deployment configuration, not Baton protocol state. The
prototype must not bake the current `fc613e3`, `/home/sl`, thread id, or Claude
policy paths into code or a generic repository recipe. Bootstrapping an
`infra.json` from `baton init` is possible follow-up Work, not required here.

## Lifecycle semantics

- Start is idempotent for a completely healthy owned set: it reports already
  running and creates no duplicate readiness producer or agent session.
- A partial/stale/tampered set refuses startup by name. The operator uses
  `status` and then the bounded `stop`; start does not silently adopt or kill
  unrelated processes.
- Startup is dependency ordered. If a newly started child fails readiness,
  only processes started by that invocation are rolled back in reverse order,
  and the failing service log is named.
- Stop sends a normal termination signal, waits a bounded interval, and
  reports a process that did not exit. It does not escalate to a stronger
  signal automatically.
- PID identity includes the recorded process start identity plus exact
  configured argv; `kill -0` alone is insufficient because PID reuse must fail
  closed.
- Logs append across restarts and include a launch boundary. Lifecycle state is
  written atomically so interruption cannot manufacture ownership.

## Acceptance

Automated tests use temporary mailboxes and fake long-lived services. They
cover complete start/status/stop, repeated start/stop, dependency ordering,
startup rollback, child crash, stale PID, PID reuse/argv mismatch, malformed
manifest, missing executable/config, duplicate service/participant, private
directory modes, log capture, reverse shutdown, and refusal to signal an
unowned process. No test touches the live v11 authority or current services.

A final manual smoke uses the real deployment manifest, confirms all four
services healthy through `just status`, proves v11 readiness, then stops and
restarts the set once without resurrecting any v10 path.

## Revalidation — 2026-08-18 (operator smoke ordering)

The live smoke must follow W101's deployment/configuration step; it is unsafe
to stop the current manually launched set first. The running dispatcher and
Claude ACP bridge were loaded before W101's universal explicit-role launch
contract:

- `tools/codex-event-bridge/config.json` still uses participant-only targets,
  while the reviewed dispatcher now requires each instructed target to carry
  `identity: {participant, role}` and an explicit `roleInstructions` source;
- the deployed Claude `load.json` names `baton.claude` but no `baton.role`,
  while the reviewed ACP launcher now refuses a missing explicit role;
- the live `fc613e3` Baton validator predates role `instructions` and therefore
  cannot accept the complete four-role config W101 requires.

Consequently the safe sequence is: deploy the reviewed candidate; add and
accept all role instructions; update every launcher config with its explicit
role; prepare `infra.json`; then stop the manually launched services and prove
`start/status/stop/restart`. Stopping first would turn a smoke test into an
unrecoverable configuration mismatch rather than testing W20.

## Interaction with active W4

W4 is currently removing the retired v10 stack and editing the Just/config
surfaces this feature will extend. This Work is therefore blocked on W4 and
must be revalidated against the post-removal tree before implementation. Do
not overlap edits merely to keep the pipeline busy.

## Revalidation — 2026-08-18 (implementation start)

W4 closed satisfying and removed the retired supervisor, its generic recipe,
and stack-only configuration. The retained backend set is exactly the four
services pinned above. W6 then documented their independent manual launch as
the truthful interim state. This Work now explicitly supersedes that interim
NORMAL-OPERATION guidance with `just start|stop|status MAILBOX`; the services
remain separate child processes with explicit commands and health checks, and
their low-level manual commands remain troubleshooting interfaces.

The controller is repository tooling, not Baton authority/application code.
Its strict version-1 manifest uses an ordered service array with unique names,
absolute command/cwd/required-file paths, string environment overrides,
explicit dependency names, optional unique participant identities, and one of
`process`, loopback `http`, or absolute `unix_socket` readiness. Unknown keys,
cycles, missing executables/resources, duplicate names/participants, and
non-private lifecycle state refuse by name.

Owned process identity records both the configured argv and the observed
`/proc` argv plus Linux process start ticks. Status and stop compare all three
before trusting a PID. The state also binds the exact manifest digest; start
never adopts a changed, partial, stale, or externally launched set. Stop uses
the recorded state and launch order, so a later manifest edit cannot redirect
signals.

The official Codex app-server documentation confirms that the loopback
WebSocket listener also serves HTTP health probes. The example may therefore
use its `/readyz` endpoint; the controller does not infer that endpoint from a
Codex command.

## Implementation evidence — 2026-08-18

The repository now provides the three exact Just recipes backed by
`tools/infra.py`, a strict generic `conf/infra.example.json`, shipped example
packaging, and operator guidance in the setup, Codex topology, bridge, and
top-level documents. The controller uses a mailbox lock, private append-only
logs, atomic fsynced state replacement, explicit dependency ordering, and
Linux pidfds. Opening the pidfd before rechecking `/proc` closes the PID-reuse
race between identity validation and `SIGTERM`; an unavailable pidfd refuses
rather than falling back to an unsafe numeric-PID signal.

Ordinary `SIGINT`, `SIGTERM`, or `SIGHUP` received during startup is converted
into a recorded failure and reverse rollback. This closes the spawn-to-state
interruption gap without manufacturing ownership. A child that ignores
`SIGTERM` remains recorded and visible; neither rollback nor normal stop
force-kills it.

Focused acceptance has 20 passing fake-service cases, including HTTP and Unix
readiness, exact ordering, append-across-restart logs, partial and interrupted
startup, rollback, crash/stale state, PID/argv mismatch, no-force timeout,
malformed/tampered inputs, unsafe permissions, refusal to adopt pre-existing
readiness, and validation of the checked-in four-service example. The complete
`just test-v11` gate passes 1,359 ordinary tests, 32 serial tests, and all 40
ACP tests. The retained Codex event bridge passes all 42 tests. `py_compile`,
`just --list`, and `git diff --check` also pass.

The acceptance-pinned live four-service stop/start remains a human operation:
the automated suite touched only temporary mailboxes and fake processes, and
this implementation did not signal, reconfigure, or adopt the running v11
deployment.
