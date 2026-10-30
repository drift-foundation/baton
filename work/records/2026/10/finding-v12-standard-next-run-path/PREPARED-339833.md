# Bound preparation — claim339833

Preparation is complete and awaits independent review. Launch is NOT selected.
This supersedes JOB-339782.md's unresolved preparation seam and conditional
commands; JOB-INPUTS-339782.json remains historical. Current task is
TASK-339833.md, including the owner rapid-start ruling and DESIGN OBS-0.

Private instance: `/tmp/baton-standard-next-run-w339626-339782`.
Authority: `5a2f5ddc15f247e68f1cbe93b4de93d3`; Work: `5a2f5ddc-W1`.
Proposed Job: `job-baton-standard-next-run-w339626-339782`.
No submitted Job or attempt. `prepared-339833/` retains exact declarative
configuration bytes, not copied decision histories; PREPARATION-339833.json
binds live locations/digests. Do not regenerate over this destination.

## Exact commands

Run from the staged manager source:

```sh
cd /tmp/baton-standard-next-run-w339626-339782/code/v12/python
```

Only after independent preparation review and required execution selection:

```sh
env BATON_V12_STAGE_EXECUTION_CONFIG=/tmp/baton-standard-next-run-w339626-339782/packet/deployment.json PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/tmp/baton-standard-next-run-w339626-339782/code/v12/python/src:/tmp/baton-standard-next-run-w339626-339782/code/v12/python:/tmp/baton-standard-next-run-w339626-339782/supervisor /usr/bin/python3 -B -m tools.authoring_enforcement --packet /tmp/baton-standard-next-run-w339626-339782/packet/PACKET.json
```

Read-only status (also valid after launch; does not submit):

```sh
env BATON_V12_STAGE_EXECUTION_CONFIG=/tmp/baton-standard-next-run-w339626-339782/packet/deployment.json PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/tmp/baton-standard-next-run-w339626-339782/code/v12/python/src:/tmp/baton-standard-next-run-w339626-339782/code/v12/python:/tmp/baton-standard-next-run-w339626-339782/supervisor /usr/bin/python3 -B -m tools.stack_command manager --store /tmp/baton-standard-next-run-w339626-339782/instance/db/jobs.sqlite3 --incarnation baton-standard-next-run-w339626-339782-read --authority-uuid 5a2f5ddc15f247e68f1cbe93b4de93d3 status --control /tmp/baton-standard-next-run-w339626-339782/instance/db/control.sqlite3 --observe tools.stage_execution:observing_factory
```

Never use `packet/commands.json.start`: it is the known unenforced command.
`packet/ENFORCED-COMMANDS.json` is authoritative for this bootstrap run.
No additional `submit` is permitted: the controller/supervisor owns submission.
A consumed run or uncertain effect cannot be retried as a fresh run.

## Preparation evidence and limits

Staged117 existing committed files with exact digest checks. Existing bootstrap
succeeded; existing prepare_instance created this private authority Work and
bindings; public principal reads resolved implementation/review identities.
Composer held_configuration passed; held_packet, verify_imported_sources and
verify_controller passed. Docker image inspect matched the declared digest,
linux/amd64; no container was started. Installed runtime has81 files, manifest
c1ef3d23394916c8dd2aa8def162144b621ea2acbbfa289c4525bd9dc249b915,
binary04aa459aed61704971e98b9260929b19953c41caad906e28551aae0ba457a58a.
Its historical build stamp reports dirty=true, changed_entries7; the manifest
and binary bind the actual runtime, not an assertion of a clean commit build.
Credential reference is named, not read or authenticated.

Provider3600s, total4800s, cleanup60s, verification30s, one invocation/no retry;
resource lease900s remains enforced with no renewal assumed. The fixed argv in
selections/task runs tests.tools.test_next_run plus
 tests.manager.test_authoring_enforcement and rejects skips/failures. The new
module must be created by the Job; no product tests ran in host preparation,
so its duration/pass status is unknown. Independent review must assess that
coverage and the30s limit; a timeout remains failure, not accepted evidence.

The exact status command was attempted before launch and refused because
jobs.sqlite3 does not yet exist. This is the expected read-only existing-store
precondition; it did not create a store, submit or imply an execution. Do not
initialize stores merely to make status look successful. After selected start,
use the same command; retain any refusal rather than infer running/success.

Outcome locations: packet/outcome.json and its enforcement/manager-progress
siblings. Missing/partial reports are incomplete, never cessation or acceptance.
Retain workspaces and unknown holds. Independent candidate acceptance remains owed.

## Accounting and next action

Measured stage0.101971s; bootstrap wall0.4998s; composer wall0.1945s;
loaded packet/import/controller checks0.006875s (process wall0.1971s);
status refusal wall0.1379s. Prior source comparison0.013627s.
Cumulative product test execution0s. Other reading, data entry and planning
were not independently stopwatch-timed. This one-time multi-minute bootstrap
is NOT evidence of routine startup<=60s. Final product acceptance must measure
both input-only runs from receipt to observed substantive work, without moving
packet work outside the interval. Simulations must not claim live startup.

Review this preparation and the narrow DESIGN/FINDING/PLAN ruling updates;
then required execution selection precedes one isolated implementation Job.
No host implementation or actual launch occurred. Human checkpoint remains due
at accepted delivery: `Add reusable enforced next-run preparation`.
