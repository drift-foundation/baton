# Immutable task source excerpts

Captured 2026-09-28; reference material, not permission to execute commands.

## v12/DESIGN.md lines 263–291

**TOK-7.** Every writer capable of affecting the resource must be accounted for,
including task subprocesses, maintenance work and delayed helpers.

**Initial preparation exception — owner 2026-09-27.** The single Host manager may
prepare a fresh private attempt before job-container handoff: allocate its
directories, create source mountpoints, publish task/input/assignment files and
set initial permissions. No maintenance container is required for this phase.
Preparation requires exclusive ownership and current claim/eligibility; no job
container may access the resources until preparation completes, the host durably
records it and revalidates their identity before task admission. All external I/O
remains outside DB transactions (DB-1). Interrupted or timed-out preparation MUST
NOT permit launch or reuse while any host writer can still complete. Restart
reconciles partial state and uncertain writers; deadline expiry alone does not
prove cessation. After handoff, this exception grants no host mutation authority.

Other governed workspace, context, input/output and artifact-custody filesystem
mutations MUST run in token-bound Docker executions. This includes subsequent
checkpoint freeze, copying into retained custody, deletion and reset. Host
filesystem helpers are not an alternative enforcement mechanism for those
effects. Stopping the agent container cannot prove an unrelated host writer
stopped. The September 26 blanket container-only rule is superseded solely for
initial preparation; later cleanup, recovery and custody rules remain in force.

The host remains responsible for authorizing these operations, validating
correlated evidence and committing its own authoritative receipt. That is
custody ownership, not permission to execute a deletion/copy on the host. A
trusted maintenance container carries out the selected resource mutation under
its own exact operation/token/runtime binding and narrowly scoped mounts; it
does not receive the producer's credentials, authority database or general host

## v12/DESIGN.md lines 361–414

**HOST-1.** Before writable execution: validate selected contract/profile, declared
inputs and resource policy; reserve eligible capacity; settle the canonical claim;
prepare fresh private resources on the host under TOK-7 initial-preparation
ownership; durably record completion and prove no preparation writer remains;
then admit the task token, validate/bind delivery and launch one exact task
execution. Task admission rechecks prepared resource/checkpoint identity;
preparation is not an irrevocable entitlement to a later grant. An expired offer
or lost claim authorizes no new preparation or task launch.

For operations still requiring maintenance execution under TOK-7, confirm the
exact maintenance container and its writers stopped and settle the operation
before conflicting task admission. Conflicting maintenance and task tokens MUST
NOT coexist. Maintenance has its own operation/token/runtime identity and derives
scope from the selected lifecycle act without fabricating a second task claim.
A maintenance container is not a pre-claim model/consent container. The previous
requirement for a separate maintenance execution for initial preparation is
superseded by the September 27 owner selection.

**HOST-2.** Host orchestration is persistent and recoverable. A restart reconciles
the recorded attempt, token, launch operation, engine object, command receipt and
custody state. It does not redispatch because its process-local map is empty. A
healthy execution may be reattached only with exact matching evidence and current
permission; an expired execution must follow TOK-6.

**HOST-3.** Docker operations use closed trusted configuration and exact object
identity. The selected final image is digest-pinned; mutable tags and container
names are not durable identity. Launch records bind platform, image, adapter,
profile, mounts, network, effective limits and trusted execution identity.

**HOST-4.** Each execution is confined: no privileged container, host PID/device
access, host Docker socket, writable authority DB, writable canonical repository,
or sibling writable workspace. Input/credential mounts are read-only. Drop
unneeded capabilities and apply declared process, memory, CPU and network policy.
Broad freedom inside the container does not imply host-root authority.

**HOST-5.** A trusted configured host/container UID/GID arrangement is permitted.
Validate its declared structure and report actual access failures; do not invent
mandatory startup probe containers or recursive permission normalization. Shared
UID/GID is an access arrangement, not the isolation boundary.

**Owner clarification, 2026-09-28 UTC (September 27 local):** jobs must create
files with the configured shared group and modes sufficient for required host
access. For the selected v12 completion/recovery path, inaccessible files are an
explicit permission error: preserve the workspace and report the affected
operation. Do not start a maintenance/custody helper to normalize permissions,
or substitute automatic host chmod/chown or privileged access. Automatic
permission repair is deferred and is not a v12 delivery prerequisite. This
supersedes mandatory result-then-workspace normalization and repair-generation
sequencing in earlier execution plans. The accessible path must progress without
normalization receipts or maintenance-container launches; missing access must
never be reported as successful collection or cleanup. Retain exact producer
shutdown, writer cessation, exclusive ownership, identity checks and durable
honest outcomes. This does not waive retained-result evidence requirements or
select automatic retention copies, deletion or reset. Rules governing future

## v12/python/tools/attempt_logs_command.py lines 1–46

"""W198667 — the operator's own view of one attempt's raw output.

THE ACCEPTANCE THIS ANSWERS, in the review's words: a deferred or failed attempt
exposes its evidence "without direct store or Docker inspection". So this reads
a directory and nothing else. It opens no Authority, no Job store, no control
store and no engine; it starts nothing and it writes nothing. A log room is
readable whether its container is running, stopped or long gone, which is the
whole reason the delivery is a manager-owned directory rather than something
asked of an engine after the fact.

    baton-v12-stack logs --logs <launch-home>/logs --attempt <id> locators
    baton-v12-stack logs --logs <launch-home>/logs --attempt <id> \\
                         read --stream provider.stderr
    baton-v12-stack logs --logs <launch-home>/logs --attempt <id> \\
                         follow --stream provider.stdout
    baton-v12-stack logs --logs <launch-home>/logs --attempt <id> \\
                         follow --stream provider.stdout --once --from-byte 4096

THE OPERAND ORDER IS THE ONE ARGPARSE ACCEPTS, and it was wrong here. Review
2026-09-18T02-31-51Z [5]: `--logs` and `--attempt` are registered on the PARENT
parser, so they come BEFORE the subcommand -- the earlier examples put them
after it and would have been refused by the very program they documented. The
copyable forms above are exercised by
`tests/tools/test_attempt_logs_command.py`.

REACHED THROUGH THE DEPLOYED COMMAND, because an operator reading evidence
after an incident has the installed bundle rather than a checkout. This module
is not on an installed package path and no console script could reach it; the
bundle's own `logs` subcommand is the supported invocation, the same surface
`status` and `monitor` are reached by.

`--logs` IS THE DELIVERY ROOT, which is `<launch_home>/logs` for a deployment
laid out by `worker_manager.launch`. It is an operand rather than something
derived from a deployment document, because an operator reading evidence after
an incident may have the directory and not the configuration -- and because a
reader that opened a deployment document would be a reader that could be
pointed at a store.

MISSING IS NOT EMPTY, and this surface says which. Every answer carries the
honest capture state, the writer's own word where there is one, and `declaration`
saying whether that word was readable at all -- so "nobody has said anything"
and "the writer said nothing" are distinguishable at a glance.
"""

import argparse
import json

## v12/STACK.md lines 893–935

## What `stop` does and does not do

It signals only the processes this stack owns, waits, and escalates to `KILL`
only after a grace period. **Stores, logs and evidence are retained** — stopping
is not cleaning up.

A repeated `just stop` is not an error; it reports `not running`.

If a process will not die, or a record's ownership cannot be established, `stop`
says so, **leaves the record in place** so a later stop can find it again, and
**exits non-zero**. It does not report success it did not achieve, and a caller
acting on the exit status is not told a stack was stopped that was not.

### `stop` stops supervisors, and says what that does not settle

The manager is a supervisor. Attempts it opened live in runtimes it does not
own, and a manager that had to be `KILL`ed cannot have reconciled anything on
its way out. So supervisor exit is **not** evidence that execution finished, and
it is not evidence that a restart is safe.

Every `stop` therefore prints a runtime line, read from the last published
snapshot:

```
runtime   2 open episode(s), 1 with a recorded runtime, as of 3.1s ago
          stopping a supervisor does not stop a runtime, and this is the last
          RECORDED answer rather than a fresh one
```

and, when that snapshot is absent, unreadable or **stale**:

```
runtime   unknown: the last snapshot is 412.0s old, so what is still executing
          was NOT resolved here
```

`unknown` is the honest answer there, not zero: a stale document describes a
world the manager has since moved on from.

A `stop` also reports `unresolved` — and exits non-zero — when a process it
signalled can no longer be *seen*. Losing visibility is not the same as
watching something exit, so the record stays and the stack is not called
stopped.
