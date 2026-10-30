# Next-run preparation candidate

This candidate implements reusable task composition, preflight-before-consumption
and retained recovery. It is incomplete and must not be installed as the managed
privileged execution boundary. `next_run install` captures preprovisioned operator
slots; it does not yet provision accounts, credentials, narrow admission or Work
authority through bootstrap. The existing installed managed-entry is unchanged.

The supported development entry is `python3 -m tools.next_run`, with the selected
source's `v12/python` and `v12/python/src` on PYTHONPATH. Commands:

* `install --installation ABSOLUTE-ROOT --inputs INSTALLATION.json` captures one
  configuration containing `schema: baton.next-run-installation/1` and `slots`.
  Each slot names `base` and the existing composer's nonroutine `compose` inputs.
  Runtime/source bytes are inventoried. Slots cannot share Work or Job/control
  stores. Installation performs no provider/engine operation or authority grant.
* `prepare --installation ROOT --slot SLOT --inputs TASK.json` consumes schema
  `baton.next-run-input/1`, `run_id`, `instructions`, `files` (relative selected
  source paths), `base`, `verification` argv and integer `limits` with `provider`,
  `verification`, `total`, `cleanup`. Base must equal the accepted slot base;
  total reserves provider plus verification plus cleanup. Context is fresh,
  one invocation, no automatic retry. Existing limits are never rewritten.
* Generated `commands.json` supplies authoritative `start`, `status`, `recover`
  and environment operands. Start routes through `tools.authoring_enforcement`.
  Preparation alone never starts it. Source, imported packages, controller,
  shutdown helper, task and configuration digests are checked before dispatch.
* `start --installation ROOT --run RUN` revalidates selected bytes, creates and
  validates prerequisite directories, checks image identity, then fsyncs an
  exclusive consumption record before entering the enforcement controller.
  Invalid preflight leaves the run unconsumed so the same start can be repeated
  after its prerequisite is restored. Uncertain dispatch remains consumed.
* `status --installation ROOT --run RUN` is read-only and reports retained
  receipts, never missing evidence as successful work. `recover` leaves consumed
  runs held, without replay. For a never-consumed partial preparation it records
  recovery and releases only its slot reservation, retaining all run bytes and
  permanently reserving the old run identity; prepare a new identity in that slot.

A consumed slot is not automatically recycled. Cessation evidence and a trusted
fresh-run allocation protocol remain required before this can be a complete
install-once service. Public command inputs are not an authorization mechanism;
this draft assumes a trusted operator-owned environment. It cannot replace the
root-protected managed entry or provide isolation against a caller who can mutate
its Python source/configuration. No sudo rule should point to this draft.

Focused deterministic verification:

```
python3 -m unittest tests.tools.test_next_run tests.manager.test_authoring_enforcement
```

The new suite exercises real composition, manifest/configuration validation,
source binding, filesystem preflight and durable admission. Image inspection and
controller dispatch are substituted in launcher tests. Existing enforcement
checks exercise its real guard/store owners with fake engine boundaries. No
engine/provider/Git mutation is executed. Two distinct generated tasks reaching
mocked dispatch do not prove substantive agent work or the <=60-second target.
Complete one-time privileged installation and real-owner deterministic end-to-end
startup/recovery evidence are outstanding; independent candidate acceptance and
human integration remain separate.

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

Prepare takes the previous `baton.next-run-input/1` task shape. It automatically
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
retained pool alone is not complete install-once recovery acceptance. The two complete substantive-work flows and <=60s measurement
remain owed. The older operator-only `next_run` path is not a privileged entry.

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
Interruption after the recovery receipt but before allocation can resume under
the same broker lock. Interruption after preparation but before its reply also
replays safely. A partial reservation or allocation remains held without
consuming another identity; it is not silently adopted or rebuilt. This last
case currently requires a separately designed continuation for the retained
partial allocation and is not claimed as fully automatic recovery.

Focused evidence adds tests.tools.test_next_run_recovery with real attempt/token
owners and a fake engine. The managed tests exercise real bootstrap and stores,
installed recovery imports, intent/response interruption and attribution, with
privileged host effects simulated. No new installation, live engine/provider,
complete substantive-task flow or <=60s joined acceptance is implied.
