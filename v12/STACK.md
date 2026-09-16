# Running the persistent v12 stack beside v11

W183883. Four recipes in `v12/justfile` start, stop, inspect and watch a
persistent v12 scheduler that runs **alongside** a running v11. They share no
service, store, configuration or port with v11, and none of them submits a Job,
calls a provider or touches version control.

**An installed deployment is standalone: its own directory is the interface.**
Bootstrap takes two operands and builds the distribution itself; after that,
nothing but the destination is needed.

```sh
cd v12
just setup                                   # ONE TIME: the build environment
just bootstrap inputs.json /srv/baton-v12    # ONE TIME: builds and installs

cd /srv/baton-v12
just start          # the scheduler and its snapshot publisher
just status         # process health, snapshot freshness, Jobs
just monitor        # the read-only view; Ctrl-C to leave it
just stop           # only the processes this deployment owns
just repository     # what its repositories actually are, read-only
just identity       # what this build IS, in full
```

Ask any installed command what it is, with nothing else available at all:

```sh
/srv/baton-v12/distro/baton-v12-stack --version
baton 12.0.0 (3c0dd082, dirty)
```

The application version lives in one module (`baton_v12.version`) and the
package metadata reads it. The commit and the dirty flag beside it are
**captured when the bundle is packaged** and travel inside it, so `--version`
answers on a host with neither this checkout nor a repository tool, and later
edits here cannot change what an installed build reports. A build made where
the repository could not be read says `source commit unknown` — never a clean
tree it could not observe. Dirty builds are allowed: the commit identifies
their **base**, and the artifact manifest identifies the bytes.

Every installed command also answers `--version` — `baton 12.0.0 (3c0dd082)` —
from a captured stamp that needs neither this checkout nor a repository tool.

The destination carries its **own justfile**, so the same deployment is
addressed from anywhere without changing directory:

```sh
just --justfile /srv/baton-v12/justfile status
```

Every path in it is resolved from that file's own directory, never from where
you ran it. Beneath the simpler interface nothing was loosened: each recipe
still passes `--instance`, so the command still verifies the whole runtime
before deriving a path and still refuses to drive an instance that is not its
own.

From the checkout, the same four take at most a destination and dispatch to
that deployed interface — `just status /srv/baton-v12` — and the command
underneath is the same program:

```sh
/srv/baton-v12/distro/baton-v12-stack status --instance /srv/baton-v12/instance.json
```

**Where the runtime check lives, and what it cannot reach.** The command
verifies its own instance — the whole one-folder manifest — before anything is
derived, so a changed library, a changed frozen asset or an unbound extra file
is refused. A self-contained deployment cannot prove its own *launcher's* bytes
before that launcher runs; nothing inside it is outside it. That one check
belongs to the build (`just test-packaging`, against the real bundle) or to
something you run from outside the deployment.

**Running from this checkout instead** is the older form, kept for developing on
the stack itself. It takes no instance path, reads four exported operands, and
is what the rest of this document describes after the installation sections:

```sh
cd v12
just setup                          # ONE TIME: the dedicated Python environment
just bootstrap inputs.json          # ONE TIME: the deployment itself, in place
just test-bootstrap                 # check the setup helper itself
just start      # the scheduler and its snapshot publisher
just status     # the environment, process health, snapshot freshness, Jobs
just monitor    # the read-only view; Ctrl-C to leave it
just stop       # only the processes this stack owns
```

### Which Python is which

There are two, and they never meet:

* **The build/development environment** — `just setup` creates it outside the
  checkout (`$XDG_STATE_HOME/baton-v12-venv`), with `python/requirements.lock`
  installed under `--require-hashes`. It is what `just build` builds *with*,
  what `just test-*` runs the suites under, and what the older source-run form
  of `just start` executes. **No installed deployment uses it.**
* **The installed runtime** — `distro/` beside the instance: the application,
  the interpreter, the dependency libraries and the frozen package resources,
  all copied there by `just bootstrap`. That is what a started deployment runs,
  which is why work can continue in this checkout — and in that virtual
  environment — while Jobs run.

Deleting or rebuilding the virtual environment does not touch a running
deployment; rebuilding the bundle does not change an installed one either,
because an instance records the digest of the runtime it was prepared with and
refuses a different one. Nothing here upgrades a deployment in place.

### Which lock is which

Also two, and also unrelated:

* **`<destination>/.bootstrap.lock`** is held by `just bootstrap` across
  custody, copy and publication while it *installs*. It coordinates bootstraps
  that both take it, and nothing else; the selector is published exclusively so
  the last step is safe regardless.
* **`<destination>/state/…` admission**, held by `just start`, is what keeps
  two *starts* of an already-installed instance from spawning two schedulers.

A bootstrap and a start never contend for the same lock, because installing and
running are different operations on different files.

## `just setup` — the prepared Python environment

**Run this first, once.** It is deliberately a separate command:
`start`/`stop`/`status`/`monitor` *use* the environment it prepares and install
nothing. A command that installed dependencies as a side effect of starting a
scheduler is one you cannot reason about.

```sh
cd v12
just setup                          # uses python3
just setup /usr/bin/python3.13      # or name the interpreter, POSITIONALLY
```

The interpreter is a **positional** argument. `just setup PY=/usr/bin/python3.13`
does not work and is not a variable override: `just` forwards the whole
`PY=/usr/bin/python3.13` string as the path, and setup then refuses a path that
does not exist — which is a broken remedy handed to exactly the operator whose
default Python was too old.

What it does, and each part is a rule rather than a convenience:

- **A dedicated virtual environment**, created with `python3 -m venv`. Not the
  system interpreter's site packages.
- **Held to the declared minimum.** `python/pyproject.toml` says
  `requires-python = ">=3.13"`, and that file is read rather than restated here.
  An older interpreter is refused and nothing is built.
- **Locked dependencies with their hashes enforced.** It installs
  `python/requirements.lock` with `--require-hashes`, so pip refuses any
  artifact whose SHA-256 is not the one this distribution pins, wherever the
  index found it. This matters concretely: the ambient interpreter on a
  development machine resolved `jsonschema` 4.19.2 while the lock pins 4.26.0,
  and a green run against the wrong validator is exactly what this prevents.
- **No activation, ever.** Every recipe resolves the interpreter's absolute path
  and runs it directly, and the stack's own children inherit it — so the
  manager and publisher run under the same environment without anyone
  remembering to `source` anything.
- **No ambient fallback.** If the environment is missing, `start`, `stop`,
  `status` and `monitor` refuse and name `just setup`. They never quietly run
  against whatever the machine happens to have.

**Where it lives.** `${XDG_STATE_HOME:-~/.local/state}/baton-v12-venv`, outside
the checkout — downloaded distributions do not belong in the working tree.
`BATON_V12_VENV` moves it.

**Repeating it is safe.** A prepared environment is re-verified and left alone;
one installed from an older lock is reinstalled. Anything else at that path — a
directory this setup did not create, one built somewhere else and moved here, or
one whose interpreter is too old — is **refused with its path named and is never
deleted**. It also never touches the stack's runtime state: `just setup` and
`just start` own different directories.

**If the index is unreachable**, setup fails and prints the exact command, so it
can be run wherever the artifacts are available:

```sh
<env>/bin/pip install --no-cache-dir --disable-pip-version-check \
    --require-hashes --ignore-installed -r v12/python/requirements.lock
```

`just install` in this same justfile is the **Node proof's** dependency step and
is unrelated to any of the above.

## `just bootstrap` — the deployment itself

`just setup` prepares the interpreter. **This prepares the deployment**: the
Authority this stack serves under, the Works its Jobs are bound to, the routes
and capability grants those Works need, the external state layout, and the
stage-execution configuration document the manager composes from.

```sh
cd v12
just bootstrap /path/to/inputs.json /srv/baton-v12
```

**Two operands: the input document and a fresh absolute destination.** The
command builds the one-folder runtime from the current source itself — there is
no separate build step to remember and no third operand to get right.

Naming a prebuilt distribution is an **optional development form**, for when you
want to install exactly the bundle you just built rather than a fresh one:

```sh
just build                                  # produces python/build/out/distro/
just bootstrap /path/to/inputs.json /srv/baton-v12 python/build/out/distro
```

Both paths are resolved **where you typed them**, not relative to `v12/python`
where the recipe body runs.

**Without a destination** — `just bootstrap /path/to/inputs.json` — it composes
the deployment where the input document's `state_root` says and installs
nothing: no runtime, no selector, no deployed justfile. That is the older form,
kept for developing on the stack itself.

Installing copies the one-folder runtime to `/srv/baton-v12/distro/`, composes the
deployment beside it, and writes **one** `/srv/baton-v12/instance.json` plus a
**`/srv/baton-v12/justfile`** — the deployed interface every command below uses.
Everything else under that destination is DERIVED from it — `db/` for the
stores, `repo/` for the repositories, `workers/<worker_id>/storage` for each
worker's mutable storage, `logs/`, `state/` and `deployment-state/` — so no two
documents can disagree about where this deployment's state is.

A destination is **prepared once**. An existing runtime or selector there is
refused, never replaced; an owned path that is a link out of the destination is
refused before anything is created; a destination inside this checkout is
refused outright, because the whole point is that work can continue here while
Jobs run.

Two bootstraps preparing the same destination serialize on
`<destination>/.bootstrap.lock`. **That lock coordinates bootstraps that both
take it, and nothing else**: it is not a defence against anything else writing
into the destination, which is why the selector is published *exclusively* --
created under a name that cannot be replaced, from a temporary this attempt
owns. Whichever attempt gets there first owns the instance, and the other is
told rather than overwriting it. An entry the bootstrap did not create is never
followed, truncated, reused or removed.

### The lifecycle, from the destination

An installed deployment is operated from its own directory and needs nothing
else — no operand, no exported variable, no prepared virtual environment, not
this checkout at all:

```sh
cd /srv/baton-v12
just start
just status
just monitor 3        # 3s between refreshes
just stop
just repository       # what this deployment's repositories actually are
just identity         # what this build IS
```

The same deployment from anywhere, without changing directory:

```sh
just --justfile /srv/baton-v12/justfile status
```

From this checkout, the wrappers take the **destination directory** — not its
`instance.json` — and dispatch to that deployed justfile:

```sh
cd v12
just status /srv/baton-v12
```

Only the bundled command underneath takes a selector:

```sh
/srv/baton-v12/distro/baton-v12-stack status --instance /srv/baton-v12/instance.json
```

### The repositories this deployment works in

**The two-operand bootstrap prepares them, from this checkout.** Do not
pre-clone anything, and do not name a source in the input document: the source
is the repository that contains the `v12/justfile` you are running — found from
the distribution itself, not from the directory you happen to be standing in.

```sh
just bootstrap /path/to/inputs.json /srv/baton-v12          # prepares them
```

Options go in the fourth operand, after an empty third — `just` binds bare
positionals in order and has no option forwarding, so an option written
straight after the destination would be taken as the distribution path. The
recipe refuses that rather than acting on it:

```sh
just bootstrap /path/to/inputs.json /srv/baton-v12 "" "--no-repositories"
just bootstrap /path/to/inputs.json /srv/baton-v12 "" "--repository-source /other/checkout"
```

or call the helper directly, where the options are ordinary options. The
operands are relative to `v12/python`, which is where that `cd` leaves you --
`build/out/distro`, not `python/build/out/distro`, which is the path the
recipe uses because the recipe resolves it from `v12/`:

```sh
cd v12/python && PYTHONPATH=src:. "$(python3 -m tools.environment interpreter)" \
    -m tools.bootstrap \
    --inputs /path/to/inputs.json --destination /srv/baton-v12 \
    --distro build/out/distro --no-repositories
```

The interpreter is the prepared one, as everywhere else here: the code comes
from the checkout through `PYTHONPATH` and the dependencies come from the
environment `just setup` made. Ambient `python3` has neither.

An input document that still carries `repository_source` is refused by name
with that said, rather than quietly ignored.

It creates three roles under the destination, each an independent `--no-local`
clone with its own object store:

| Role | Path | What it is |
| --- | --- | --- |
| `integration_target` | `<destination>/repo/target.git` | where a reconciled result is imported |
| `integration_workspace` | `<destination>/repo/workspace` | integration's own preparation area |
| each worker's `nominated_source` | `<destination>/repo/source-<worker_id>` | what that worker's Jobs work in |

Then it **proves** them before the deployment is composed: each must identify
itself as a repository, no two may be one repository or one directory, none may
borrow objects from elsewhere, and the target must already hold every Job's
`line_declared_base` and the configured `integration_target_reference`.

The source is the **installer's** business: it never appears in the
configuration the manager reads, and a deployed instance never needs the
checkout it was installed from to exist.

**What a clone carries, and what it does not.** The prepared repositories hold
the commits your checkout has — not the edits you have not committed. A build
from a dirty tree says `dirty` in its version, and the repositories it prepares
still contain the committed base. If you want uncommitted work in a
deployment's repositories, that is a separate decision about repository copying
and it has not been made here.

**Leave the three paths out of your input and they are derived** as above. Name
them and they must be exactly those paths — an input that asks for preparation
*and* names something else is refused, before anything is created, with both
sides shown. Each worker's `workspace_storage` is derived as
`<destination>/workers/<worker_id>/storage` when absent and must resolve inside
the destination when you name one; two workers of the same deployment sharing a
path inside it is your business and is left alone. Your credential registry
(`credential_sources`) is yours and is never moved.

**With `"" "--no-repositories"`, nothing is cloned** and the install says so.
That is a valid state — the deployment starts, schedules and never reconciles —
and it is what a freshly installed instance without those selections is in. It
is not a prepared integration, and nothing reports it as one.

Ask the deployment what is actually there, read-only and without running a
repository tool:

```sh
cd /srv/baton-v12 && just repository
```

That prints the workspace and the target — each with whether it is inside this
instance, whether it exists, whether it carries a repository layout and the
`HEAD` it holds — plus the configured reference and every declared base, and it
says explicitly when a workspace is not a repository yet and what that costs.

A deployment reconciles only when `integration_target`,
`integration_workspace` and `integration_observer` are **all three**
configured. Those first two the bootstrap can prepare; the observer
participant, the import reference and each Job's immutable base are yours to
choose.

The selector is validated before anything is derived from it: it must be read
from the destination it names, and every path it carries must be the one that
destination derives and must resolve inside it. **And the runtime is verified before
anything is derived from the selector**: the command digests its whole bundle
and refuses if it is not the one this instance was prepared with, so a changed
library, a changed frozen asset or an unbound extra file in the distro is
refused. What no self-contained deployment can check is its own launcher's bytes
before that launcher runs — nothing inside it is outside it — and that one check
belongs to the build (`just test-packaging`) or to something you run from
outside the deployment. A frozen command also refuses to drive an instance that
is not its own. `just monitor` reads the snapshot the
publisher writes, so leaving the monitor does not stop scheduling — that is
`just stop`.

The older form — no instance path, four exported operands, run from this
checkout — still works exactly as it did, and the rest of this document
describes it.

It selects **nothing**. You supply one `baton.v12.stack-bootstrap/1` document
naming this deployment's production selections; everything derivable is derived,
and a selection that is missing is refused **by name** rather than filled in
with a fixture. It submits no Job and executes nothing.

**Nothing durable happens until every check has passed** — the input document,
the derived identities, the emitted configuration under the *manager's own*
rules, this root's existing record, and the checkout boundary. The configuration
it would write is handed to `stage_execution.held_configuration`, the same
validator the manager uses, so a worker document missing its adapter, profile,
credentials, workload, workspace or launch members is refused by name **before**
an Authority exists — not discovered afterwards.

**The input document is closed.** A member nothing reads is refused rather than
accepted and quietly dropped: the two are indistinguishable to you until the
deployment behaves differently from what you asked for. The supported optional
selections are `integration_target`, `integration_target_reference`,
`integration_workspace`, `integration_observer`, `integration_instructions`,
`integration_preparation` and `result_judgment_workers`.

**Present means present.** A selection you supply travels verbatim, including
one the validator will reject — an explicit `null` is refused in the consumer's
own words rather than quietly dropped and defaulted, which would turn an invalid
request of yours into a different valid one. An absent member stays absent, and
that is a different thing from an explicit `false`.

### What it derives, so you do not name it

Principals (`Authority.principal_of` — never spelled twice), each Job's Work,
the `impl`/`rview`/`integration` route handlers, the `verify`/`review`/
`approve`/`integrate` grants in each Work's own scope, the whole layout under
one `state_root`, the configuration document, and the four exports below.

It writes `baton.v12.stage-execution-deployment/1` only when there is one Job
**and** one worker per role, because `/1` permits exactly one worker per role;
anything larger is `/2` with `job_bindings`. Within a binding the implementation and review Work
IDs are **the same Work** — the review-cycle provider keys one line by one
`(authority, work)` pair, so a deployment with two Works there could never
attach its review — which is why the input names `work_id` once.

### What you must name

```json
{
  "schema": "baton.v12.stack-bootstrap/1",
  "state_root": "/var/lib/baton-v12/deployment",
  "authority_uuid": "<32 lowercase hex>",
  "checkpoint_profile": "…",
  "integration_profile": {"profile_kind": "…", "profile_version": 1,
                          "integrator_participant": "baton.…",
                          "instructions_digest": "sha256:…"},
  "retention_policy_digest": "sha256:…", "retention_disposition": "retain",
  "pool_generation": 1, "policy_generation": 1,
  "receipt_participants": {"verification": "baton.…", "review": "baton.…",
                           "approval": "baton.…"},
  "workers": [{"worker_id": "impl-a", "role": "implementation",
               "participant": "baton.…", "deployment": { … }}],
  "jobs": [{"job_id": "job-a", "work_id": "…", "line_declared_base": "…",
            "canonical_target_id": "…", "source_worker_id": "impl-a"}]
}
```

Each worker's `deployment` is the single-worker launch document
`v12/python/DEPLOYMENT.md` specifies — its image digest, adapter identity,
profile and policy digests, credential registry, slots and profile, nominated
source, task document, input manifest and workspace capacity. The bootstrap
carries it through verbatim and adds only `participant`, `principal`,
`authority_store`, `authority_uuid` and `launch_role`.

**Implementation and review may share neither participant nor principal.**
Independence is the whole reason a review exists, and a deployment that could
never produce one is refused before anything is opened.

### Repeating it

Safe, and idempotent. An Authority that already exists is reused; a Work already
bound as the document binds it is left alone.

It keeps its own record, `bootstrap.json`, beside the configuration, written in
one shape whichever variant is emitted — so a deployment prepared as `/2` and
repeated as `/1` is still comparable Job by Job. A binding that **changed** — a
different Work, declared base, canonical target, producer or Authority — is
refused, and so is a Job that simply **stops being named**: a Job that is no
longer mentioned is not thereby unconfigured, since its Work, its grants and
whatever it has already produced are all still there.

That record has to be **evidence**, not just a recognizable file. Its whole
shape is validated — the Authority it names, a non-empty set of bindings, and
every binding carrying its Work, declared base, canonical target and producer —
because a record that does not say what is bound cannot say that something
changed. And the configuration beside it is read and **related to it**: a
`deployment.json` that is missing, corrupt, or that binds anything the record
does not, means the state here is unknown.

Any of that — a corrupt or incomplete record, a configuration that cannot be
read, or the two disagreeing — refuses the repeat **before the Authority is even
opened**. Unknown state is not proven-absent state, and nothing here overwrites
what it cannot identify. Both documents are published atomically, so an
interrupted write cannot turn a known configuration into partial JSON.

No migration feature is offered: if you mean a different deployment, give it its
own `state_root`.

### `just test-bootstrap` — checking the helper itself

```sh
cd v12
just test-bootstrap                            # uses /var/tmp
just test-bootstrap /srv/scratch               # or name the root, POSITIONALLY
BATON_V12_STACK_TEST_ROOT=/srv/scratch \
    just test-bootstrap                        # or export it once
```

**Precedence is your own order**: an explicit operand, then an exported
`BATON_V12_STACK_TEST_ROOT`, then `/var/tmp`. A root you select explicitly is
**never silently passed over** — if it is unwritable, inside the checkout, or on
a memory filesystem, you are told by name rather than quietly given another one.

It runs `tests.tools.test_bootstrap` under the prepared interpreter, bounded by
`timeout --kill-after=10s 180s`, and **its exit status means something**: a
failing case and a timed-out run both reach you as a failure.

`ROOT` is where the fixtures put their disk-backed material. It defaults to
`/var/tmp` and needs to be **real storage outside the checkout** — the accepted
validator refuses a configured mutable root inside the working tree, and the
workspace boundary refuses one on a memory filesystem, so a host whose `/tmp` is
a tmpfs cannot be used. Nothing is installed; if the prepared environment is
missing it says `just setup`, like every other recipe here.

### What is still yours to choose

`bootstrap` refuses, by name, anything it cannot derive. The full list — image
digest, adapter identity, profile and policy digests, credential slots and
profile, per-Job workload material, target repository and line, workspace gid,
retention policy — is in
`work/records/2026/09/finding-v12-stack-launcher/DEPLOYMENT-INPUTS-185653.md`,
with what the accepted code actually requires for each.

### Capacity, stated rather than implied

`bootstrap` reports what is **configured**: workers by role, the Jobs, each
Job's producer, and the distinct canonical targets. Each Job binds one producer,
one Work, one declared base and one target, and Jobs sharing a target are
serialized at integration. A producer count is not a promise that arbitrary
Jobs traverse review and integration at once.

## The four operands `just start` reads, when it is run from this checkout

**These are the older form's operands.** An installed instance carries all four
in its own selector and needs none of them exported.

`just bootstrap` prints these ready to paste. They are listed here because
`just start` reads them from the environment, and because **nothing is defaulted
into the checkout** — an external state root exists precisely to keep runtime
state out of the tree, and a defaulted store would put it straight back.
`just start` refuses and names every missing one at once rather than making you
discover them one run at a time.

```sh
# Where the Job store lives. Absolute, outside the checkout.
export BATON_V12_JOB_STORE="$HOME/.local/share/baton-v12/jobs"

# The Worker Manager control store. Absolute, outside the checkout.
export BATON_V12_CONTROL_STORE="$HOME/.local/share/baton-v12/control"

# The Authority this Job store belongs to: 32 lowercase hex characters.
# It namespaces every episode identity the store derives, is persisted on
# first open, and a later open naming a different one refuses.
export BATON_V12_AUTHORITY_UUID="<32 lowercase hex>"

# The stage-execution deployment document: which workers exist, under which
# roles, with which profiles. This is the fixed worker configuration.
export BATON_V12_STAGE_EXECUTION_CONFIG="$HOME/.config/baton-v12/deployment.json"

# Optional. Where this stack keeps its own process records, published
# snapshot and logs. Defaults to $XDG_STATE_HOME/baton-v12-stack.
export BATON_V12_STACK_ROOT="$HOME/.local/state/baton-v12-stack"
```

The deployment document's schema, its roles and its per-worker requirements are
`v12/python/DEPLOYMENT.md`'s, not this launcher's. This launcher validates that
the file is named and exists; the deployment validates what is in it, and a
document it refuses is a refusal you will see in `manager.log` — and, since the
correction below, in the output of `just start` itself.

### What a valid deployment document has to name

Stated here so the gap is visible rather than deferred to a manual. The closed
member list is `stage_execution`'s own (`_MEMBERS`), and every one of these is
required:

| Member | What produces it |
| --- | --- |
| `authority_store`, `authority_uuid` | a v12 Authority store holding every configured participant, with `verify` / `review` / `approve` / `integrate` granted in the bound Work's scope, and a route handler for each worker's outgoing route |
| `integration_store`, `state_root` | created by the composition on first start; both must be absolute and **outside the checkout** |
| `workers` | exactly one per `implementation` / `review` / `integration` role, each a complete single-worker launch document (image, profile, participant, principal, credential slots) |
| `job_work_id`, `review_work_id`, `canonical_target_id`, `line_declared_base` | the Work, target and line this deployment is bound to |
| `checkpoint_profile`, `integration_profile`, `retention_policy_digest`, `retention_disposition`, `receipt_participants`, `pool_generation`, `policy_generation` | deployment policy, digest-bound |

Two things are worth knowing before you build one:

- **Composition needs no engine and no provider.** Opening the Authority,
  minting and authorizing the five sessions, certifying each worker's profile
  and activating the pool all happen with no container started and no provider
  called. That is what makes an empty configured stack a real, checkable idle
  state rather than a hopeful one.
- **A relocated deployment is a fresh one.** The control store records the
  workspace storage it was configured with, and moving the storage is refused
  rather than reconfigured — every attempt already allocated under the first
  store would become unfindable.

### The runtime prerequisite

`baton_v12` lives under `v12/python/src`, because `pyproject.toml` declares
`package-dir = {"" = "src"}`. Every child needs that on `PYTHONPATH`:

```sh
cd v12/python && PYTHONPATH=src:. "$(python3 -m tools.environment interpreter)" \
    -m tools.job_manager --help
```

The recipes set it, and `tools/stack.py` builds it **absolutely** for the
manager, the publisher and the publisher's own `job_manager status` subprocess.
An operator's own `PYTHONPATH` is kept, after it. This is stated because the
first cut of these recipes omitted it: the manager died on
`ModuleNotFoundError: No module named 'baton_v12'`, `monitor` could not have
started either, and `start` reported success anyway.

The **code** comes from the checkout through `PYTHONPATH`; the **dependencies**
come from the prepared environment. That split is deliberate: `just setup`
installs `requirements.lock`, not this distribution, so what runs is the tree
you are looking at, resolved against the pinned validator.

**A missing configuration is not an idle stack.** `start` refuses when the
document is absent rather than reporting a comfortable idle, because a stack
with no worker configuration cannot serve anything and saying otherwise would
hide the gap.

## What `start` actually runs

Two processes, both owned by this stack:

| Process | What it is |
| --- | --- |
| `manager` | `job_manager serve` over your stores, with `tools.stage_execution:factory` — the accepted scheduler, not a stand-in |
| `publisher` | writes `status.json` under the state root every few seconds, atomically |

The publisher exists because the viewer reads a **document**, and
`JOB-VIEWER.md` requires atomic snapshot publication for refresh. It belongs to
`start` rather than to `monitor` so that **quitting the monitor cannot stop
scheduling** — the monitor only ever reads a file.

**Starting selects no work.** No Job is submitted, and an empty configured stack
is a valid idle state.

`start` is repeatable: a second `just start` reports the processes already
running rather than starting a second manager. It is also **safe to run
concurrently**: one exclusive lock (`$BATON_V12_STACK_ROOT/lifecycle.lock`)
covers the whole ownership transition, so two starts cannot both spawn, and a
stop cannot interleave with a start. A lifecycle operation that cannot get in
within 30s refuses and changes nothing. The lock is a kernel lock rather than a
file you have to clean up: killing a start releases it.

### `start` waits for the stack to actually come up

It does not report success because the kernel forked something. Before it
prints `ready:`, **three** things must hold:

- every owned process is still running;
- every manager **this start spawned** has printed its own serving
  acknowledgement, naming this start's incarnation; and
- the publisher has written a status snapshot **during this start**, valid and
  freshly observed.

**Why the acknowledgement is separate from the snapshot.** The publisher runs
`job_manager status --observe tools.stage_execution:observing_factory`, and
`observation_from` builds a reader out of a held configuration — it composes no
deployment. `operations_from`, which the *manager* runs, opens the Authority,
mints and authorizes five sessions, runs three worker preflights, opens the
integration store and activates the pool. So a manager that never got there —
delayed, stopped, or still opening the Authority — coexists perfectly happily
with a publisher reading a valid empty store. A snapshot is evidence about the
observer. Only the serving loop can speak for the serving loop, so it says so
itself, once, on stderr, after initialization:

```
serving initialization complete: incarnation='v12-stack-...' operations='tools.stage_execution:factory'
```

That line lands in `manager.log`, and `start` requires one naming **this**
start's incarnation, written after this start opened the log — so neither
another manager's line nor a previous run's can answer for it.

**A manager that was already running is checked too, not assumed.** An earlier
start does not necessarily prove anything: it may have been interrupted while
its manager was still opening the Authority, or it may have unwound and
deliberately *retained* a live process it could not stop. So a live manager is
reused only when its acknowledgement holds for that identity **now**. If it does
not, `start` waits for it — bounded — and then refuses. It is never killed and
never duplicated: this start did not admit it, so the refusal names it and tells
you to `just stop` and `just start` rather than taking it away. `just status`
reports the same fact as a `serving` line at any time.

One consequence worth knowing: the acknowledgement lives in `manager.log` and
nowhere else, deliberately — a cached copy would be a second place the truth
could live. If you truncate or delete that log, the evidence is gone, and the
next `start` will wait and then refuse rather than assume. `just stop` and
`just start` recovers.

So an import failure, a refused operand, a deployment document the composition
rejects, a manager that never initializes, or any early exit produces a
**non-zero** `just start` carrying the child's own last words from its log. A
stale snapshot from a previous run does not count, and neither does a document
copied into place: it must be fresh by its own `observed_at`. If the wait times
out, the stack is unwound: processes this start put up are stopped, and a record
is cleared **only for a process positively established as gone** — one still
running, or one whose visibility was lost, keeps its record so `just stop` can
still find it.

Every failed admission unwinds, not only a refused one. If the publisher fails
to spawn after the manager was admitted, the manager is taken back and the
original error reaches you unchanged — and one process that cannot be taken back
never stops the others being accounted for.

### When ownership cannot be established

If a record is unreadable, or `/proc` cannot be read for the pid it names,
`start` **refuses and starts nothing**. It does not replace the process and it
does not signal a pid it cannot identify — a record you cannot read may name a
manager that is running right now, and starting a second one over it is exactly
how the first becomes unstoppable.

Recovery is yours to perform, and the refusal names the two paths you need: the
retained record and the process's log. Once you have established that nothing is
running, remove the record. Nothing here removes it for you.

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

### What counts as a readable snapshot

Before anything reads Jobs or episodes out of the published document, it is
validated the way the viewer validates one: the status schema, a canonical
observation, a readable `observed_at`, and the nested shape of jobs, stages and
episodes. Anything else is reported `unreadable` — never walked, and never
counted as zero. Two ages are reported because they answer different questions:

```
snapshot   fresh (observed 1.2s ago, written 0.4s ago)
```

`observed` is how old the **manager's reading of the store** is; `written` is
how old the file is. A document copied into place is new by the second measure
and old by the first, and the first is the one that says whether this describes
the world now.

**Pid reuse is handled rather than hoped about.** Every record stores the
process's own start time from `/proc`, and a process is signalled only when the
pid *and* that start time both still match. A recorded pid that now belongs to
something else — including anything of v11's — is reported as stale and is never
signalled.

## Reading `just status`

```
manager    running pid 12345
publisher  running pid 12346
snapshot   fresh (observed 1.2s ago, written 0.4s ago)
jobs       0 observed (canonical=True)
serving    acknowledged
runtime    0 open episode(s), 0 with a recorded runtime, observed 1.2s ago
```

`serving` is a **separate fact from `running`**: a manager process can exist
without its deployment having composed, so the two are reported separately and
an unacknowledged manager says so.

Each line distinguishes states that are easy to conflate:

- **`absent`** — no record at all; nobody started this.
- **`stale`** — a record naming a process that is not there. Different from
  absent, and worth noticing.
- **`unknown`** — there is a record, or a pid, and we could not establish who
  owns it. Not absence, and not a licence to start over it. `just status`
  prints the record's path beside it.
- **snapshot `absent`** vs **`stale`** — nobody has published yet, versus the
  publisher has stopped refreshing.
- **jobs `absent` / `unreadable`** — "nobody looked" and "we looked and could
  not tell". **Neither is reported as an empty pipeline**, because zero Jobs is
  a fact and these two are not.

## Logs

`$BATON_V12_STACK_ROOT/manager.log` and `publisher.log`. If `start` fails, it
quotes the tail of the relevant log in its own refusal; the file is the rest of
the evidence. The publisher also writes the reason a `status` read was refused
to its log, which is where a deployment that does not compose becomes visible.

## Boundaries

This launcher does not migrate a backlog, does not copy v11 Work, and is not a
competing coordination authority: **v11 remains the project's Work coordination
home**. Any v12 local execution authority is separate and explicitly named by
`BATON_V12_AUTHORITY_UUID`.

It performs no version-control operation, starts no disposable proof run, and
does not touch v11 services, stores or configuration. `just proof` and
`just state-clean` above it remain the Node proof's, and are unrelated to these.
