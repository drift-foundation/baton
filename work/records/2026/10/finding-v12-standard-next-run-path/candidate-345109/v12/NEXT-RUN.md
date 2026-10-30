# Managed next-run candidate

The managed path installs a protected launcher and finite identity pool once,
then accepts routine task input through `client.py prepare`, `check`, `start`,
`status` and `recover`. Preparation creates Work, stores and configuration through
their existing owners. This candidate requires independent acceptance and separate
human integration/installation selection; the existing installed entry is unchanged.

`tools.next_run` remains an operator-only composition helper with preprovisioned
slots. It is not the privileged managed interface and no sudo rule should point
to it. The managed path below supplies automatic allocation and retained recovery.

Focused deterministic verification (from the selected source's `v12/python`,
with `src` and that directory on PYTHONPATH):

```
python3 -m unittest tests.tools.test_next_run tests.tools.test_next_run_managed tests.tools.test_next_run_recovery tests.tools.test_next_run_flow tests.manager.test_authoring_enforcement
```

The joined tests require the existing disk-backed fixture root selection
`BATON_V12_DISK_ROOT`; tmpfs is rejected by the real workspace boundary. An optional
`BATON_NEXT_RUN_FLOW_EVIDENCE` names a new JSON artifact destination. The tests
retain original failure records, and label simulated boundaries as described below.

## Trusted installation and automatic allocation candidate

The additional `tools.next_run_managed` installer and fixed `next_run_entry.py`
replace preprovisioned slot inputs for the managed path. They remain unaccepted
candidate code; no host installation has occurred. The operator installation
input is `baton.managed-next-run-installation/1`, with caller_uid, capacity2..64,
explicit supplementary groups, one base/compose template, credential_sources and
source_digest. It contains no precreated run Work, store or slot inventory.
The template retains existing composer runtime/image/profile/participant/base
selections; runtime store paths, authority UUID, Work, principals, output roots,
execution uid/group and credential registry are derived for each allocation.

Installation holds source/runtime/vector bytes, compares their inventory digest
(`payload_digest(source_payload(template['compose']))`) with reviewed source_digest,
then publishes root-protected executable files and configuration. It creates the
identity pool and private credential copies once, validates and publishes a narrow
sudoers entry, and publishes readiness last. Existing destinations/accounts/rules
refuse; a partial installation is preserved, never silently overwritten. An
operator must run the installer from a reviewed root-protected source copy; the
installer itself must not be loaded as root from a mutable author checkout.

After independent acceptance and separate human integration/installation selection,
the operator invocation from that protected source is:

```
/usr/bin/python3 -I -B -c 'import sys;sys.path[:0]=["/ROOT-PROTECTED-SOURCE/src","/ROOT-PROTECTED-SOURCE"];from tools.next_run_managed import main;raise SystemExit(main())' install --inputs /REVIEWED-INPUTS.json --sha256 INPUTS-SHA256
```

These are explicit placeholders for separately reviewed installation operands,
not a ready-to-execute host deployment procedure. No root installation is
selected by this candidate or its tests.

Routine managed commands after that installation:

```
/opt/baton-next-run/client.py prepare < task.json
/opt/baton-next-run/client.py check RUN
/opt/baton-next-run/client.py start RUN
/opt/baton-next-run/client.py status RUN
```

Prepare accepts `baton.next-run-input/1`: run_id, instructions, files (relative
selected source paths), base, verification argv and integer limits with provider,
verification, total and cleanup. Base must equal the installed accepted base;
total reserves provider plus verification plus cleanup. Context is fresh, one
invocation, no automatic retry. Existing limits are never rewritten. It automatically
reserves an unused execution identity and creates a private operational root.
The real bootstrap API creates the authority, Work, routes and scoped grants;
real composition binds task/configuration/runtime and actual installed sources.
Only operational files become execution-uid-owned. Configuration and executable
bytes remain root-owned, separately from private outputs. The output includes
commands pointing exclusively to the installed entry, not mutable Python modules.
The managed entry accepts no root/config/interpreter argument or caller-supplied
Python search path and validates installed custody before importing product code.

Start validates selected bytes/custody and the Work, prepares missing parents,
validates image identity, then records durable exclusive consumption before
exec. It drops groups/gid/uid, confines writes with Linux Landlock ABI3 or later,
and replaces itself with the existing enforcement controller. No privileged
waiting process executes task code. The authority read runs under that execution
identity too: SQLite read-only opening may create WAL sidecars, which must not
be stranded with root ownership. An unknown consumed dispatch remains held;
status reports receipts without opening operational stores.

This milestone intentionally never recycles an identity. Capacity exhaustion
refuses without creating accounts or resetting evidence. Positive cessation/
fencing and fresh-allocation continuation are described below. This finite
retained pool does not promise unlimited service or automatic capacity expansion. The older operator-only `next_run` path is not a privileged entry.

Additional deterministic suite: `tests.tools.test_next_run_managed`. It uses real
bootstrap/Authority, composition, filesystem publication and an isolated process
loading installed bytes. Account/chown/sudoers operations are simulated through
Host; dispatch and engine checks are substituted. A separate unprivileged child
executes real Landlock and proves writes outside its allowed directory fail.
This is not actual root installation, live provider or full kernel UID-separation
acceptance. Root source and runtime must also satisfy the closed regular-file
packaging rule; runtime symlinks are explicitly refused rather than followed.

## Fixed admission and fresh child imports

The managed sudo rule admits exactly `/opt/baton-next-run/entry.py request`.
There are no argument wildcards and no per-run sudoers edits. The unprivileged
client above sends a bounded JSON object on stdin: prepare carries action/task;
check, start and status carry action/run. The protected entry validates that
shape independently, rejects duplicate members, extra operands, path traversal,
unknown actions and requests over1MiB. The client cannot supply privileged code,
configuration, interpreter or import-root operands. Direct entry argument forms
such as `entry.py start RUN` are not part of the installed admission interface.

The controller's initial isolated interpreter receives explicit installed import
roots. Its fresh manager subprocess inherits a newly constructed environment with
PYTHONPATH naming only installed code/src and code; no caller PYTHONPATH or
PYTHONHOME is propagated. Its cwd is protected installed code. Tests exercise the
real Process class launching a fresh `-m tools.authoring_enforcement --help`, and
a fresh child verifies the exact supervisor/controller/helper hashes and import
locations under that same environment. Removing the roots reproduces the original
baton_v12 import failure. These import-only checks execute no manager workload.

Admission evidence combines real selected visudo parsing, the same literal
argument-matching mechanism established by prior managed-entry acceptance, and
actual request parser/broker tests. Actual client transports to sudo are inspected
at the subprocess boundary; no new live sudo policy is installed or executed.
This managed test environment rejects sudo itself at its setuid ownership check.
Do not describe these fixtures as a fresh privileged authorization receipt.


## Consumed-failure continuation

After a failed consumed run, submit the next task through the same fixed entry:

```
/opt/baton-next-run/client.py recover OLD-RUN < new-task.json
```

Recovery prepares a fresh run; use the returned commands to check and start it.
It never replays the old consumed selection, overwrites an old receipt, reuses
an account, or launches as a side effect of recovery. The root broker holds
admission closed, checks that the old exclusive uid has no remaining processes,
and runs installed owner readers under that uid and its write confinement.
Every attempt in the isolated control store is inspected, including attempts
not linked to a Job episode. Each must have a returned workspace token and an
exact runtime currently observed absent. An empty attempt inventory can prove
a failure before runtime admission. A durable controller halt is recorded and
a root-owned recovery receipt binds these observations and the old consumption
to the new task. No writable workload outcome is accepted as cessation proof.

Live processes, inspection errors, outstanding/missing tokens, ambiguous runtime
identities and running or merely stopped containers refuse fresh allocation.
The command does not forcibly stop a live run. Existing controller cleanup and
runtime owners must establish cessation first; uncertainty stays held. A selected
host must expose complete process identities to its root broker and preserve
exclusive non-login, never-recycled execution uids.

A repeated identical request returns the one prepared receipt, including after
the fresh run has started, without dispatching again. Changing its task refuses.
Interruption after the recovery intent resumes through the same `recover OLD-RUN`
request and identical input. A reservation with no allocation effects resumes
its exact reserved identity after binding and process checks. If allocation,
bootstrap or packet publication already began, recovery never overwrites that
partial state or retries its stores. It proves the target was never admitted
(no prepared or consumed receipt under the broker lock), checks process absence,
and binds its exact retained tree and reservation in an immutable continuation
record. It then prepares a fresh `continuation-...` run with another identity
from the installed pool. The returned receipt and commands name that actual run;
`recovery_from` retains the original consumed run and `continuation_of` names the
interrupted allocation. The original task instructions, files, base and limits
are unchanged; the fresh run identity is the only substituted input.

Repeating recovery after restart or a lost response follows that recorded chain
and returns the same prepared receipt without launching. The old partial root
is preserved and permanently excluded from start. Changed reservation/allocation
bindings, retained-tree drift, special/linked nodes, process uncertainty or any
execution-admission evidence hold recovery. No identity is recycled. As with
ordinary allocation, the finite installed pool can exhaust; repeated failures
consume its remaining identities and then report a capacity hold, never silently
provision accounts or reclaim old ones. Legacy partial reservations lacking the
new exact allocation binding refuse; no existing installation migration is
claimed. Complete receipt replay remains supported.

Reservation, allocation and continuation/receipt publication is atomic and
non-replacing. A broker request applies a restrictive preparation umask while
holding the lock. Tests interrupt the real bootstrap and packet writers and
ownership/publication boundaries, retaining all prior bytes, then verify fresh
attribution, restart/reply replay, uncertainty/drift refusal and once-only start.
These remain simulated privilege/engine observations, not live deployment proof.

Focused evidence adds tests.tools.test_next_run_recovery with real attempt/token
owners and a fake engine. The managed tests exercise real bootstrap and stores,
installed recovery imports, intent/response interruption and attribution, with
privileged host effects simulated. These boundary tests alone do not establish substantive-work latency; the joined
owner proof below measures that separately. No live installation or provider
acceptance is implied.

Initial preparation interruptions use the same supported `prepare` request and
identical task input. A bound reservation with no effects resumes; a partial
allocation follows an immutable continuation to a fresh identity just as a
recovery preparation does. `recovery_from` is null for this initial path;
`continuation_of` records the interrupted allocation. A changed task, live or
unknown processes, admitted execution, unbound legacy partials, and retained-byte
drift still hold. Repeating an ordinary completed preparation refuses and directs
the caller to check/start/status; repeating an interrupted preparation follows its
recorded continuation and returns the actual prepared run. Always use the returned
run identity and commands. No manual account or store repair is part of this path.

The joined test `tests.tools.test_next_run_flow` installs once, runs two distinct
input-only tasks, injects a controller child-launch failure after consumption, and
uses the supported recovery request for a fresh successful task. It exercises the
real bootstrap, Authority, controller and fresh child, scheduler, worker adapter,
verification command, result sealing/intake/retention and shutdown receipts.
Engine, provider, privileged host effects and Git commands are explicit simulated
boundaries. The provider edits real task-dependent source and the adapter runs the
actual verification command. The clock starts before input assembly; the recovery
clock includes the failed start and recovery assembly. This evidence cannot prove
live-provider latency, real Git transport, installed sudo authorization or kernel
uid isolation. Candidate review remains separate from a completed implementation
Job. The fixture records that distinction instead of manufacturing review receipts.
