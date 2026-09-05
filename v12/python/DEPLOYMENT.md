# Deploying the v12 Worker Manager

## Running the persistent manager with one implementation worker

W76207 supplies the first production operations factory for the persistent Job
Manager: `tools.single_worker:factory`. It is intentionally one worker, one
implementation Work, one profile and one image. Worker selection, capacity,
review and integration belong to later Work and are not hidden defaults here.

Create a new Job store for this first runnable bootstrap. Stores populated by a
pre-W76207 build retain their already-recorded episode identities for audit and
restart integrity; those old identities predate the worker contract's bounded
`opaqueId` grammar and are not rewritten. Every episode created by this build
uses a deterministic contract-valid identity and is restartable from its row.

The factory reads the absolute path in `BATON_V12_SINGLE_WORKER_CONFIG`. That
environment variable contains a path only. In particular, neither the offer
bearer nor provider credential bytes are configuration or environment values.
The bearer exists for the immediate offer-accept call and is then discarded;
credentials are read lazily from the invoking user's private source registry.

The configuration is one JSON object with schema
`baton.v12.single-worker-deployment/4` and exactly these members:

| Member | Required value |
|---|---|
| `schema` | `baton.v12.single-worker-deployment/4` |
| `authority_store`, `authority_uuid` | Absolute Authority store path and its exact 32-character UUID |
| `participant`, `principal` | The one endpoint and the principal Authority resolves it to |
| `profile_name`, `profile_digest` | The one certified implementation runtime profile |
| `policy_digest` | The Job and input manifest's exact policy digest |
| `adapter_name`, `adapter_digest` | The deployment's fixed OCI adapter identity |
| `engine`, `image_digest`, `network` | `docker` or `podman`, an immutable image digest, and the approved network name |
| `workspace_storage`, `workspace_group` | Absolute persistent storage and the provisioned non-authority gid described below |
| `launch_home`, `credential_home` | Absolute persistent launch state and manager-private credential homes |
| `credential_sources` | Absolute private user registry described below; the public production factory refuses `null` |
| `credential_slots`, `credential_profile` | Closed logical slot names and the trusted provider/reference mapping for them |
| `nominated_source` | Absolute source directory, mounted read-only and never copied, walked or hashed — see "The source/workspace boundary" below |
| `workspace_capacity` | `{"max_bytes": …}`, the capacity this assignment declares its writable workspace needs, proved against the filesystem's free bytes before launch and enforced on nothing afterwards; must exceed the runtime's whole bounded scratch |
| `input_manifest` | The complete frozen `inputManifest` document, whose one source destination is exactly `source`, whose `content_manifest` for it is the empty tree, and whose `consumption` declares `baton.source-boundary/1` |
| `task_document` | Absolute path to the frozen JSON workload document this profile's input manifest declares as its `human_contract` artifact |
| `launch_contract`, `launch_role` | The immutable worker launch contract and `implementation` role |
| `review_route` | The Route an answered, frozen, collected candidate's assignment is passed to |
| `retention_policy_digest`, `retention_disposition` | The policy every intaken artifact is decided under, and one of `retain`, `quarantine`, `discard-after-intake` |

Each version supersedes the last and there is no fallback: adding a required
member to a closed, version-named document is a new contract rather than a
compatible reading of the old one. `/2` added the frozen task, without which
the certified worker refuses its input root before doing any provider work.
`/3` adds the three members the ending needs — a deployment that could freeze,
collect and retain a result without saying where the Work goes would be
choosing a destination nobody named. `/4` (W71917) replaces `input_source`
with `nominated_source` and adds `workspace_capacity`.

**`/4` renames the source member rather than redefining it, and the rename is
the point.** `input_source` named an already-staged directory this deployment
MEASURED and COPIED into the input root. `nominated_source` names a directory
it validates and MOUNTS read-only and never reads. Those are different
statements about the same host path — one is material the manager took custody
of, the other is material it agreed not to touch — and a member that quietly
changed meaning under one name is how a deployment ends up believing a copy
happened. A `/3` document naming `input_source` is refused by the closed member
set, not read as a nomination.

Unknown or missing members refuse. Before an offer exists, the factory checks
the complete input manifest, relates its Authority, assignment contract,
policy, profile and image to the configured values, validates the nominated
source and the declared workspace capacity, validates the credential mapping and
OCI posture, opens Authority against the expected UUID, and proves the
configured participant resolves to the configured principal and Work.

It no longer measures the source. `/3` walked the whole nominated tree here
with `workspaces.directory_manifest` and compared the result against the
manifest's declared content — a full open-read-and-digest of every file,
performed by a manager that is ruled not to walk, copy, snapshot, enumerate or
hash the source at all. It could not have kept its promise either: the tree it
measured was the tree before the container started, and nothing bound those
bytes to the ones the engine later mounted.

### The workload document, and why it is configuration rather than payload

The certified worker reads two things this manager fixes: the frozen task at
`/input/task.json` and the source tree at `/input/source`. They are separate
immutable inputs — the source is what the agent edits, the task is what it was
asked to do — and neither is ever an environment value.

For this production profile the task document **is** the input manifest's
`human_contract` artifact, and that relationship is what makes the delivery
digest-bound rather than path-trusting. The artifact must declare
`application/json`, a width no greater than the worker's 1 MiB read ceiling,
and the byte count and SHA-256 digest of the configured file. The artifact's
locator stays provenance and is never read as a host path; `task_document`
names the local materialization.

During static validation — before Authority is opened and before any offer or
attempt root exists — the factory opens `task_document` once with `O_NOFOLLOW`,
proves it is an ordinary file, reads at most the ceiling, and holds those exact
bytes. Missing, linked, non-regular, oversized, byte-count-mismatched and
digest-mismatched material all refuse there, where there is nothing yet to
leave behind. The held bytes are what every later composition publishes, so
changing the configured path afterwards cannot change what is delivered.

When an attempt's input root is composed, those bytes are installed as the
read-only ordinary file `task.json` before the source is copied and before the
protocol pair freezes the root. A root that already carries a `task.json` this
composition did not write is refused rather than replaced. On restart, adopting
an already-composed root re-proves the installed document — no-follow, ordinary,
read-only, exact bytes — because the generic manifest reader deliberately reads
only the two protocol documents and says nothing about the workload material
beside them.

### The durable file exchange, and why production has no pipe

The Job Manager's process lifetime is not the container's. Production
manager-to-worker commands and worker-to-manager receipts, state changes and
terminal outcomes are durable files in one attempt-private exchange, so a
manager restart destroys no protocol state, makes no healthy container
unknowable, and never replays an uncertain write.

The exchange is a third delivery, created before the runtime starts, inside the
same attempt-private launch root under `launch_home`. It cannot live under
either assignment root: `inputs` is frozen before the start, so a later command
could not be published there, and anything under `workspace` is also reachable
through the worker's writable `/output` mount, so the worker could rename or
replace the very command addressed to it. The root itself stays mode `0555`,
which is what stops the container moving either namespace — that is a
permission of the parent.

| Host, under `<launch_home>/<attempt-id>/` | Container | Mode | Written by |
|---|---|---|---|
| `launch.json` | `/run/baton/launch.json` | `0444`, read-only bind | the manager |
| `command/` | `/run/baton/exchange/command` | `0755`, read-only bind | the manager |
| `events/` | `/run/baton/exchange/events` | `02770` in the workspace group, writable bind | the worker |

The launch document selects the transport, and nothing else does. A production
launch is `baton.worker-launch/2` and carries a fifth member,
`transport: "baton.worker-exchange/1"`. `baton.worker-launch/1` remains the
explicitly allowed diagnostic and test transport that `worker_entry.converse`
speaks to; a worker that chose the file exchange because it found the
directories mounted would be a worker with two live contracts and no version.

**The manager publishes one command sequence per attempt, after the container
is up.** The document is closed, canonical, and atomically published under a
filename derived from its own sequence identity; it names the exact attempt,
the launched session, and the ordered operations `describe` then `work` with
their stable attempt-derived operation identities. Two managers racing the same
attempt compose identical bytes under an identical name, so the second adopts
the first's document; a different document under that name refuses rather than
replacing a command the worker may already have receipted.

**The worker publishes its receipt before it dispatches the provider**, and
that receipt is the durable replay fence. Rescanning the command namespace, a
manager restart during the turn, and a re-entry of the worker process after a
crash all find it, and none of them starts a second provider turn. A worker
that finds its receipt with no terminal result publishes nothing further and
exits non-zero: it cannot know whether the provider a previous incarnation
started is still running, so claiming loss would be claiming an observation it
does not have.

Every worker-written document is untrusted input. The manager bounds and
no-follow opens it, closes its member set, and holds its session, attempt,
sequence and command digest against the command it authored itself. A terminal
document claiming `answered` is a claim: `/output/output.json`, a positive
observation of the exact runtime, and the existing freeze and intake gates are
what settle it.

**Nothing credential-capable crosses.** The exchange carries the receipt, the
per-operation state events and one terminal document, and the terminal carries
only the completed operation names, a bounded fault code from the worker's own
closed set, the worker disposition when there is one, and the digest of the
completion envelope already published under the existing `/output` contract.
No recap, prompt, source excerpt, tool input or output, and no provider stdout
or stderr. Manager-minted safe progress logs and their read/follow surface
remain W61599's; this deployment creates no `result/logs` sink.

### Status says what is actually happening

Status is now `baton.v12.job-status/3`, and a stage carries its canonical
exchange projection beside its runtime. A runtime identity alone is no longer
rendered as active work — that was the defect. The vocabulary gained three
words:

| State | What it means |
|---|---|
| `starting` | The container is up and this control plane has not commanded it, or holds no exchange read at all |
| `waiting` | The command sequence is published and the worker has not accepted it |
| `running` / `reviewing` / `integrating` | The worker published its pre-dispatch receipt, so a provider turn is owned |
| `answering` | A correlated `answered` terminal exists and the output is not frozen yet |
| `completed` / `changes-requested` | From the frozen result's disposition, unchanged |
| `exceptional` | A faulted or lost exchange, unreadable worker material, or a recorded start or preparation failure |

A stage's `exchange` member is `null` when this control plane holds no exchange
read — "nobody looked", which is deliberately not the same answer as an
exchange that has been read and carries no command.

Publishing the command and driving the ending are level-triggered, exactly as
the launch is: both are derived from canonical state on every tick, including
the first tick after a restart, and neither writes a Job-store receipt. The
durable command file and each ending substep's own journalled operation are the
records.

On one correlated `answered` terminal the deployment drives the already-ruled
successful ending in this fixed order: positively quiesce and reconcile the
exact runtime, record the worker's disposition, freeze the declared output,
collect it and record the intake receipt, decide every artifact's retention
under `retention_policy_digest`, pass the exact assignment generation to
`review_route`, and only then authorize runtime cleanup. `authorize_cleanup`
refuses while the assignment is live, so cleanup before the pass is not an
option; ending the assignment before intake could quarantine the result if the
collection raced that ending.

A faulted, lost or incomplete exchange is **reported and contained**. This
slice adds no automatic abandonment, retry or pool policy: the stage projects
`exceptional`, every other stage stays observable, and ending a started attempt
on purpose remains W44716's `abandon_attempt` under a decision nobody has made
here.

The manager never parses the task's provider-specific schema. The worker owns
that vocabulary; this deployment treats the document as digest-bound content. The runtime composer receives only the
restricted participant-bound Authority port—not the Authority store path,
bootstrap object, principal lookup or credential-source registry. A direct
test or embedding may inject a credential-provider capability through the
Python construction seam; that seam is why the schema accepts `null`, but the
public `module:factory` deployment does not.

Submit a Job document once, then start the service. The Job and control stores,
all three homes, source, config and Authority store are outside the checkout.
Use a fresh incarnation value for every manager process start:

    cd /opt/baton/v12/python
    PYTHONPATH=src:. python3 -m tools.job_manager \
      --store /var/lib/baton/v12/jobs.sqlite3 \
      --authority-uuid 0123456789abcdef0123456789abcdef \
      --incarnation submit-20260903-01 \
      submit --document /etc/baton/bootstrap-job.json

    BATON_V12_SINGLE_WORKER_CONFIG=/etc/baton/single-worker.json \
    PYTHONPATH=src:. python3 -m tools.job_manager \
      --store /var/lib/baton/v12/jobs.sqlite3 \
      --authority-uuid 0123456789abcdef0123456789abcdef \
      --incarnation manager-20260903-01 \
      serve --control /var/lib/baton/v12/worker-control.sqlite3 \
      --operations tools.single_worker:factory --interval 5

Ordinary status is a separate read-only command and needs no Authority or
factory capability:

    PYTHONPATH=src:. python3 -m tools.job_manager \
      --store /var/lib/baton/v12/jobs.sqlite3 \
      --authority-uuid 0123456789abcdef0123456789abcdef \
      --incarnation status-20260903-01 \
      status --control /var/lib/baton/v12/worker-control.sqlite3

### Three different freshnesses, and which command gives you which

W85500 added a second way to run `status`, so there are now three surfaces and
it is worth being explicit about what each one can and cannot know.

**The serving loop reconciles.** Every `serve` tick asks the engine about each
live attempt's attached runtime BEFORE it projects anything, and records the
answer. That is the only place the runtime axis becomes fresh, because asking
means recording, and recording is a write. Until W85500 nothing asked after the
start: a worker that faulted and exited stayed projected `running` for as long
as anybody looked, while the engine reported the exact runtime gone.

**What a refresh that fails does, and what it deliberately does not do.** Each
tick's `refreshed` entry carries the state that was recorded, or `not-asked`
when the deployment supplies no refresh at all. Two failures are contained per
stage so that one damaged attempt cannot stop every other stage being observed
or progressed: malformed evidence from a deployment is reported with its
refusal category and code, and an engine invocation this deployment could not
make — a missing engine binary, or a runner that hit its deadline — is
reported `uncertain / engine-unreachable` with the failure's type name.
Nothing is recorded from an unreachable engine: the runtime axis keeps
whatever it last knew, which is the honest difference between "gone" and
"nobody could ask". Neither containment touches the exchange axis, so a
readable terminal is still projected. Anything else — a defect in the
deployment's own code — is NOT contained: it ends the tick and reaches
whoever is running the loop. A serving loop answers only its last tick's
report, so a defect quietly turned into report data would vanish on the next
successful tick.

**A dead daemon reads as `policy / denied`, not as `engine-unreachable`.**
Worth knowing before you go diagnosing one. This composition asks the engine
by running the Docker CLI, and a daemon that is not there does not stop the
CLI from running — it runs and exits non-zero, so the adapter refuses the
listing `policy / denied`, and that is the category and code the stage
carries. It is contained per stage and records nothing on the runtime axis
exactly like the malformed-evidence case above, so what you can rely on is
unchanged; what you cannot do is read `engine-unreachable` as the only shape
an absent daemon takes. Telling an unreachable daemon apart from a genuine
policy or integrity refusal would need a typed adapter failure this build
deliberately does not have.

**Status with `--observe` looks at the durable exchange.** The bare read-only
status reports `exchange: null` — not because the worker's terminal is
unreadable, but because that surface was never given a way to look. Supplying
an observation factory changes exactly that one thing:

    BATON_V12_SINGLE_WORKER_CONFIG=/etc/baton/single-worker.json \
    PYTHONPATH=src:. python3 -m tools.job_manager \
      --store /var/lib/baton/v12/jobs.sqlite3 \
      --authority-uuid 0123456789abcdef0123456789abcdef \
      --incarnation status-20260903-01 \
      status --control /var/lib/baton/v12/worker-control.sqlite3 \
      --observe tools.single_worker:observing_factory

That factory reads the immutable configuration and the already-open control
store and reconstructs this attempt's launch and exchange files. It opens no
Authority, mints no session, configures no workspace group or storage,
certifies no profile, constructs no credential home, and holds no engine. It
is deliberately NOT `tools.single_worker:factory`, which carries mint,
delivery, start, dispatch, ending and pass; `--observe` and `--operations` are
resolved separately so a read can never be handed a serving object.

**It still does not refresh the runtime, and that is on purpose.** Refreshing
means reconciling, and reconciling records what it saw — a status command that
did it would be a read that mutates. So the runtime axis in any status
document is exactly as fresh as the serving loop that last advanced the store.
If no loop is advancing it, the status is as stale as that store and says so
rather than writing. The exchange axis has no such limit: the terminal is a
file, so `--observe` reads the same bytes a restarted manager would.

**Without `--observe` nothing changes.** The default is still `exchange:
null`, which means "nobody looked" and not "nothing happened".

A worker that faults is reported `exceptional` with its typed `fault_code`,
and a fault authorises nothing: no freeze, no intake, no retention, no
Authority pass, no cleanup, no replacement attempt, no second command and no
second provider turn. The two axes stay separate — observing that a container
exited never manufactures the quiescence a successful ending requires, and an
unreadable exchange never stops the engine being asked.

### The Authority a Job store belongs to

`--authority-uuid` is required on all three commands and is the 32-lowercase-hex
Authority the Job store belongs to. It is persisted on the store's first open
and is immutable: a later open naming a different Authority refuses without
changing a byte, and an existing schema-1 or schema-2 store is pinned to the
supplied Authority in the same transaction that stamps the new schema version.

**It namespaces every episode identity the store derives.** Offer and attempt
identities are the names an OCI runtime is labelled and selected by. They used
to be derived from the stage id and the episode number alone — both local to
one Job store — so two independent Job Managers running a stage with the same
local name derived the *same* attempt identity, and a fresh Authority's very
first episode was measured colliding with a retained container belonging to
another Authority entirely. The adapter refused to adopt that container, which
is correct and unchanged; what was wrong was handing it an identity two
strangers could both produce.

It is a binding, not a capability. `submit` and read-only `status` learn only
this stable public identity: neither opens an Authority, holds a session, or
gains any mutation surface. The production `serve` factory additionally
compares the store's recorded Authority with its configuration's
`authority_uuid` **before** it configures the workspace group or storage,
certifies a profile, allocates anything, or opens the Authority — a mismatch is
a fail-closed deployment error with no partial control-store configuration.

Existing episodes are never renamed. Migration preserves every recorded offer,
attempt, receipt and operation byte, because Worker Manager journal keys and
Job receipts already reference those strings; the namespace decides what a
*new* episode is called. An already-recorded unnamespaced episode can still
meet a retained container from another Authority and will still fail closed, so
production acceptance of this correction uses fresh Job and control stores
rather than claiming that reopening an old store repairs its identities.

After a crash, run the same `serve` command with a new incarnation and the same
durable paths and configuration. The manager adopts the accepted claim,
attempt, workspace/input, credential and launch records, reconciles a requested
or running OCI identity, and does not issue a second offer, claim or runtime.
An uncertain runtime is reported `exceptional`; it is never implicit permission
to start another container.

A post-claim preparation that cannot be completed — a workspace that is not
this attempt's own, an input root carrying material but no protocol pair, a
staged source whose bytes changed, a manifest collision, a credential source
that refuses, a launch document that cannot be adopted — is recorded by the
Worker Manager as this attempt's **failed preparation**. That is its own
durable record and it is deliberately not the failed-start record: it says
this deployment's composition could not carry the attempt further, it says
nothing about whether a start act ever happened, and it authorises no removal.
The stage is then reported `exceptional` and is not asked again; every other
stage stays observable and the loop keeps serving. Nothing contradictory is
repaired: the material is left exactly as it was found, for an operator to
look at.

Before that record is written, anything the composition still holds is ended
or named, depending on which side of the start request it is on. **Before a
start**, no runtime can have received either delivery, so the credential
delivery is torn down and the launch document discarded — including one an
earlier process published and this one adopted. **After a start**, neither is
removed, because a container may hold the mount; instead the manager asks the
engine which runtime carries this attempt's whole label set and attaches the
one it identifies, so what is left running is named in its own records for an
operator to end. Nothing is stopped from here: every operation that stops a
runtime is fenced at the Authority first, and this deployment holds no
authority to fence the Work it is executing.

**The naming and the ending are one act.** The engine is asked before anything
is written, and the attachment its answer implies is committed inside the same
transaction that writes the preparation record. Neither can be left without
the other by a process that dies: an attached runtime alone would project the
stage `running`, and a record alone would project it `exceptional`, and in
both cases the loop calls this deployment no further. What an interrupted act
leaves is the stage still `claimed`, which the next process drives through the
same path from canonical state. An attachment the manager refuses — a runtime
whose observed state cannot follow the axis it holds — is rolled back on its
own and the record still stands, describing the axes as they really are.

The restart window after a published credential delivery is held to the same
rule. If the process died after the engine created the container and after the
delivery was published, restart adopts this attempt's exact launch document —
it never authors a replacement once a start has been requested, and a document
that is missing or that cannot be proved ends the stage under the naming rule
above. Otherwise it proves the live runtime through the manager's own
credential recovery before rereading any bearer: the container's identity,
labels and mounts must all agree. When they do not, that recovery fails
closed, accepts no output, stops only what it identified exactly, performs
bounded cleanup, and its whole account becomes this attempt's recorded
preparation failure. The stage is
`exceptional` and is not asked again, with the host left exactly as the
recovery left it for an operator to look at.

## The source/workspace boundary (W71917)

A production runtime receives exactly two trees of its own, and they are
different kinds of thing.

**One nominated source, mounted read-only at `/input/source`.** The manager
validates the directory the deployment nominates — absolute, canonical, its
own unaliased directory, not a symbolic link, with no linked ancestor, and
outside the manager's own workspace storage in both directions — and pins the
device and inode that validation saw. It then establishes an empty mountpoint
for it inside the assignment's input root and binds the nominated directory
over that mountpoint, read-only. Read-only is not a parameter: a worker that
could rewrite the Work it was given could answer about the rewrite.

**One manager-created, manager-custodied, disk-backed workspace, mounted
writable at `/output`.** This is the same assignment-private workspace the
manager already allocated, adopted into the configured workspace group, with
the attempt's result root inside it — with two things now proved before a
runtime starts: that it is on real storage, and that its filesystem currently
holds the declared capacity.

### What the ordinary local path does not do

It does not walk, copy, snapshot, enumerate, hash or Git-process the nominated
source. Validating it costs one `lstat` and one `fstat` whatever is inside it,
so a repository with a million objects and an empty directory are the same
act. Nothing under the nominated path is opened; the one directory descriptor
the proof takes is closed without a single directory read.

This retires the ordinary copied-source bootstrap. Snapshot providers that a
caller explicitly asks for are unaffected — the dogfood operator still stages
and snapshots exactly as it did, because that is a copy somebody requested.

### The manager is Git-agnostic

The input manifest's source descriptor declares the boundary in its
`consumption` extension, under `baton.source-boundary/1`:

    "consumption": {
      "baton.source-boundary/1": {
        "delivery": "nominated-mount",
        "workspace": "disk",
        "profile": "git"
      }
    }

`delivery` and `workspace` are the manager's own words and it validates both.
`profile` is **bounded opaque text the manager never interprets** — it does not
compare it against a list, and it never probes the nominated tree to infer one.
A descriptor carrying no declaration is a *staged* source whose content the
manager measured, and mounting over one is refused rather than silently
allowed.

What the profile word means lives in `baton_v12.source_profiles`, which the
manager does not import:

- **`git`** — the worker clones from the read-only mount into a `checkout`
  directory inside its own writable workspace, and then verifies the base
  revision the assignment declared. The clone is composed with
  `--no-hardlinks --no-local`, which is not optional: `git clone` from a path
  on the same filesystem hardlinks its object files, so without it the
  workspace's objects would be the very inodes of the read-only mount. The
  verification is `git -C <checkout> rev-parse --verify <base>^{commit}` —
  a question about the worker's own copy, asked after the clone. Abbreviated
  base revisions are refused rather than expanded, because expanding one asks
  the repository which object to verify.
- **`generic`** — the mount *is* the source root, read in place. No clone, no
  inference, and nothing copied into the workspace; the workspace is for what
  the worker produces. A generic profile that names a base revision is
  refused, because its author believed a verification would happen that this
  profile never performs.

### Scratch is bounded; the workspace capacity is declared and proved

The runtime gets bounded private scratch — `/tmp` at 64 MiB and `/dev/shm` at
16 MiB, both `noexec,nosuid,nodev` — and nothing the assignment owes may rely
on it. **Checkout, build/cache, test artifacts, output and logs go to the
disk-backed workspace.**

That rule is enforced twice rather than documented once:

- `check_disk_backed` refuses a workspace on `tmpfs`, `ramfs` or `devtmpfs`,
  read from the kernel's own `/proc/self/mountinfo` rather than inferred. A
  memory filesystem answers "how much room is left" perfectly reassuringly,
  which is exactly why free space is the wrong question to ask it.
- `workspace_capacity` refuses a declared `max_bytes` that is **not strictly
  greater than the whole scratch bound** (64 MiB + 16 MiB = 83,886,080 bytes).
  A workspace that would have fitted in the scratch beside it establishes
  nothing about the five uses that must not rely on scratch; at the floor plus
  one byte, `/tmp` cannot hold the workspace even in principle.

The declared capacity is also checked against the filesystem: a declaration
the storage cannot currently meet is refused before a runtime starts, rather
than discovered by a worker halfway through writing an output.

#### The workspace bound is admission evidence, not a running limit

**Scratch is bounded by the kernel. The workspace is not bounded at all.**
`/tmp` and `/dev/shm` are tmpfs mounts carrying a size, and a worker that
fills one is stopped by the filesystem. `/output` is an ordinary writable bind
mount, and this deployment applies no byte or entry ceiling over it while a
runtime is running: `workspace_capacity` is checked at admission, `_capacity`
proves the backing filesystem has that many bytes free at that instant, and
nothing measures the workspace afterwards.

So, stated rather than implied: **a worker can fill the workspace's backing
filesystem after it has been admitted.** Size the storage behind
`workspace_storage` for that, and do not put it on a filesystem whose
exhaustion would take something else down with it.

The check is also **not a reservation**. Two assignments admitted against the
same filesystem each prove the whole declaration separately, so admitting both
does not prove the filesystem can hold both.

W71917 ruled this the MVP contract deliberately. A live ceiling over a bind
mount needs project quotas on the backing filesystem, a per-attempt loopback
image, or a storage driver whose size option this deployment can set — each of
which needs privilege or host configuration the rootless launch was built
without. True live byte and entry ceilings are separate, parked v12 hardening.
An earlier draft of this section called the value a quota and declared a
`max_entries` beside it that reached no mount, no runtime and no sweep; both
are gone, because a limit's name over no mechanism is worse than the honest
weaker contract.

### Restart, and what refuses before a start

Restart adopts the exact manager-owned workspace: the roots are re-proved as
this attempt's own real directories at their own paths under the configured
store, the boundary is composed over them again, and the existing mountpoint
is adopted rather than created a second time.

Immediately before the engine is called — on a first run and on a restart
alike — the boundary is re-proved against what is on disk. These refuse there,
with nothing started:

- a nominated source that has become a symbolic link, acquired a linked
  ancestor, stopped being a directory, or vanished;
- a nominated source **replaced** since it was proved: the path resolves to
  the same characters and a different inode, which is what the pinned identity
  is for;
- a workspace that moved, was replaced by a link, or is no longer a directory
  of its own;
- a workspace **replaced** since it was proved, including by another real
  directory at the same pathname: like the source, it carries the device and
  inode this manager observed when it allocated it, and a runtime started over
  a replacement would write its answer into material the manager never took
  custody of;
- a source mountpoint replaced by a link or by anything the manager did not
  establish;
- a foreign workspace root — including a home whose entry is a link to another
  attempt's workspace, which is still inside manager storage and is still not
  this attempt's.

Both roots are proved once more after adoption, immediately before the runtime
binds are derived, which is the last boundary this manager owns. The engine
then resolves each bind source pathname itself, and **that final interval is
not closed**: it is an accepted residual on a trusted host, ruled deliberately
rather than overlooked. Closing it would mean handing the engine an object
rather than a pathname, which needs a daemon that can reach this manager's own
namespace and would make the recorded mount source meaningless after the
manager exits — so the restart comparison below would have to change with it.

What that means for an operator: the deployment's trust boundary includes
whoever can write the parent directories of `nominated_source` and
`workspace_storage` between the manager's last proof and the engine's start.

What a restart deliberately does **not** claim: that the material behind the
nominated path is the material an earlier incarnation saw. The manager holds
no content identity for it, because it is ruled not to take one. A worker that
needs to know which revision it received verifies that itself, inside the
container, over the tree that is really mounted.

### Cleanup never removes what the manager did not create

A mountpoint is not a symbolic link, so a removal walk with `followlinks=False`
would descend straight through a live one. Cleanup therefore refuses any
directory on a different filesystem than the tree it is removing, before an
entry inside it is touched. In the ordinary arc this never fires — the bind
lives in the container's own mount namespace and the host-side directory stays
empty — and it is there for the case that is not ordinary.

## Provisioning the workspace group

A worker runs as the fixed non-root identity `65532:65532`, which is not the
identity the manager runs as. Its workspace is a host directory the manager
creates and the worker must be able to write. The one authority that crosses
that gap is a **group both sides hold**: the manager creates the workspace in
it, and the runtime is given it as a supplementary group.

Approver ruling M34630 fixes what that group is.

**The deployment provisions it. The manager never creates or modifies a host
group.** There is no code in this component that calls `groupadd`, and adding
some would move the authority boundary the ruling draws.

It must be:

- **dedicated** — provisioned for this and nothing else, so that granting it to
  a worker grants exactly workspace write;
- **non-authority** — no file outside the manager's own workspace storage is
  owned by it, and membership in it confers nothing. Concretely: it is not a
  login group, not the manager's primary group, and not a service group such
  as the container engine's socket group;
- **nonzero** — root is refused, and the refusal is not configurable;
- **held by the manager process**, as a supplementary group. The manager
  `chgrp`s workspaces into it, which requires membership.

A worked example, run by whatever provisions the host:

    groupadd --system baton-workspace          # dedicated: nothing else uses it
    usermod -aG baton-workspace baton-manager  # the manager holds it
    # and nothing is chgrp'd into it: it owns nothing until the manager
    # allocates the first workspace.

Verify the two properties the manager cannot verify for itself:

    getent group baton-workspace               # it exists and is named
    find / -xdev -group baton-workspace        # it owns nothing yet

## Configuring it, once

The gid is recorded in the manager's own control store, by the deployment,
before the first execution workspace is allocated:

    from baton_v12.worker_manager import configure_workspace_group
    configure_workspace_group(store, gid)

This commits the operation `workspace-group.configure` to the journal and
projects it into `meta`. It is idempotent: re-affirming the same group commits
nothing new.

**Changing it is refused.** A manager already holding workspaces adopted into
one group cannot be told the group is now another one without those roots
becoming unreachable to the workers they were prepared for. A deployment that
means to change the group initializes a fresh store — the same clean-boundary
rule the schema version is under.

## Using it

Nothing else supplies a gid. Every allocation and every launch reads the
deployment's own record:

    from baton_v12.worker_manager import configured_workspace_group
    group = configured_workspace_group(store)   # a WorkspaceGroup capability
    roots = assignment_workspace(group, storage, assignment_id)
    adapter = OciAdapter(..., workspace_group=group)

`configured_workspace_group` is the only way to obtain a `WorkspaceGroup`; the
class refuses to be constructed. That is what makes "the configured group" a
fact about the deployment rather than about whoever called.

## What the group does NOT give you

**The workspace group buys ordinary group-readable collection. It does not buy
custody.**

Setgid means what the worker creates lands in the configured group, so output
the worker leaves group-readable is output the manager can read, archive and
remove. That is the whole of it. The worker chooses its own modes, and a worker
that writes mode `0600` content — or a directory it alone can enter — leaves
material that the group alone cannot make inspectable, collectable or
removable, because the manager is not the owner and the group bit is not set
for it. This Work's own
`test_an_owner_only_output_fails_closed_rather_than_widening` drives exactly
that case and requires the manager to fail closed rather than widen the mode.

Failing closed is deliberate: a manager that `chmod`ed its way in would be
taking custody the deployment never granted it, and a manager that reported
such an attempt as cleaned up would be erasing material that is still on disk.

**Unconditional manager custody — the property that holds regardless of
worker-selected modes — is NOT what the configured group buys.** Approver
ruling M36166 named the mechanism (a short-lived manager-controlled custody
helper on the exact attempt directory; umask 002 is explicitly not it) and
created **W36540** to provide it.

**That provider has landed.** W36540 and its five children are closed
satisfying, and the manager composes custody into the ended-attempt path:
`custody.normalize_directory` runs on the exact attempt directory and nothing
else, as the same uid the worker ran as. It therefore OWNS every object the
worker created, and an owner may `chmod` its own objects whatever mode they
currently carry — which is what makes the property unconditional rather than
dependent on the worker having cooperated. The helper only normalizes; the
MANAGER still performs the removal, under the containment rules that were
always on this side.

So the two boundaries stay distinct, and it is worth keeping them apart when
reading a refusal: the configured group buys ordinary group-readable
collection, and the custody helper buys reach that no mode a worker chooses
can withhold.

With the group configured, the manager:

- creates the workspace at exactly `02770` in that group — setgid, so what the
  worker creates inherits the group;
- proves the canonical root still carries that group immediately before the
  engine call, because a grant established at allocation is not a grant at
  launch;
- composes `--group-add <gid>` for **execution runtimes only**, leaving
  `--user 65532:65532` untouched. A consent runtime receives no supplementary
  group.

## Credential sources are per-user and private (W52821)

The supervised operator command reads the provider credential it delivers from
**the invoking user's own files**, named by a registry that user owns:

    python3 tools/dogfood_operator.py \
        --grants GRANTS.json --evidence OUT.json \
        --credential-sources /home/<user>/.baton/credential-sources.json

`--credential-sources` replaces the old `--credential-file`. That operand named
one file whose bytes were returned for **every** provider and **every**
reference, so the trusted profile decided what a credential was and the command
then ignored the decision. The registry selects on the exact pair instead.

### Setting one up, per user

The registry and every file it names are that user's own private material.
Nothing here is provisioned by the deployment, nothing is shared, and nothing
belongs to the workspace group:

    install -d -m 0700 ~/.baton
    install -m 0600 /dev/null ~/.baton/anthropic.token
    # ...write the credential into it with an editor that makes no backup copy

    cat > ~/.baton/credential-sources.json <<'JSON'
    {
      "schema": "baton.user-credential-sources/1",
      "sources": [
        {"provider": "anthropic",
         "reference": "op://baton/dogfood-worker",
         "path": "/home/<user>/.baton/anthropic.token"}
      ]
    }
    JSON
    chmod 0600 ~/.baton/credential-sources.json

The `provider` and `reference` of each entry are **exactly** the ones the
grants file's `credential_profile` maps the attempt's slots to. The reference
is opaque — nothing reads a meaning out of it at either end — and it is matched
whole. The reader holds both to the same shape the manager holds them to when
it reads the profile — non-empty encodable text, with no character class and
no width of its own — so a provider like `vault/team`, or a reference longer
than a few hundred characters, is whatever the profile says it is at both
ends. Verify the two properties the reader will insist on:

    stat -c '%U %a %F' ~/.baton/credential-sources.json ~/.baton/anthropic.token
    # <user> 600 regular file   (twice)

### What the reader refuses, and why you may see it

| Situation | Outcome |
|---|---|
| No entry for the exact provider **and** reference | refused — an unknown selection has no fallback: not the only entry, not a provider-only match, not a default source |
| Two entries for one provider/reference pair | refused — a pair with two sources does not say which file backs it, and the whole registry is refused whether or not that pair is the one selected |
| A final symbolic link at the registry or a source | refused — `O_NOFOLLOW`, so a link is refused as itself rather than resolved into whatever it points at |
| Not an ordinary file (directory, fifo, device) | refused at the descriptor, after the open and before any read |
| Owned by another uid | refused — a source this user does not own is one somebody else may replace |
| Any group or other permission bit | refused — mode `0600`, because this material is read by this user and delivered to nobody |
| Unreadable, absent, or wider than the manager's bearer bound | refused — a value this command cannot hold whole is not one it delivers a prefix of |
| An I/O error interrogating or reading the opened descriptor | refused — the failure's kind is named and nothing else, because an `OSError`'s own text carries the filename |
| `--credential-sources` given to `--abandon` or `--retry-handoff` | refused — both endings read no registry and open no source, so the operand is a contradiction rather than a spare word |

Each of these that is *about a selection* names it the same bounded way,
described next: one fixed label and the two values' encoded-byte widths. (The
last row is not — it is refused before either value exists, so it names the
mode and the operand and nothing else.)

### What a refusal from the reader says about your two values

No refusal from the reader names a host path, because a refusal is prose and
prose travels. **For the same reason it names neither the provider nor the
reference** — not the whole of either, and not a leading part of either.

What you get instead is one fixed label and two byte counts — here, for the
`anthropic` / `op://baton/dogfood-worker` entry set up above:

    ... a provider identity and opaque reference of 9 and 25 encoded bytes ...

That is deliberate rather than terse. Holding both values to the manager's own
shape means they carry no width of their own, so a deployment whose profile
legitimately maps a slot to a multi-kilobyte opaque reference would otherwise
have put that reference into a sentence your terminal, your ticket and your
paste buffer all keep. A leading part is no safer: the reference is opaque
precisely because nothing at either end reads a meaning out of it, so nothing
at either end can say which of its bytes are the harmless ones.

**So when you see one, compare rather than read.** The two counts are the
encoded-byte widths of exactly the pair the trusted profile resolved, in the
same unit as the registry's own 64 KiB bound. A count that does not match the
`provider` or `reference` you wrote into `credential-sources.json` is the
column to fix; two counts that both match mean the values differ somewhere
inside, and `credential_profile` in the grants file is the authority for what
they should be.

### Removing the shared `/run/baton/credentials` staging

**A deployment no longer stages credential material into a shared host
directory, and any surviving `/run/baton/credentials` staging on a host is to
be removed.** It was a place where one file, readable by whoever the directory's
mode admitted, stood in for every attempt's credential — which is the same
bypass `--credential-file` was on the command line.

On each host that ever ran the earlier arrangement:

    systemctl stop baton-manager                 # or however this host runs it
    find /run/baton/credentials -mindepth 1 -maxdepth 1 -print   # look first
    rm -rf /run/baton/credentials                # host side only
    # nothing is recreated: the manager makes its own attempt-private roots

Three things that path **still** means, and none of them is host staging:

- `/run/baton/credentials` remains the fixed **container-side** mount root,
  `credentials.CREDENTIAL_ROOT`. It is a constant of the manager's contract and
  not an operand, and each authorized slot is mounted at one entry of it.
- The host side of each mount is the manager's own **attempt-private** volatile
  root: mode `0700`, owned by the manager, one per attempt, holding one `0640`
  slot per authorized slot in the configured workspace group. It is created
  after the attempt is activated and removed, proved absent, at every ending.
- The user's own source files are read once, at materialization, and are never
  copied, staged, mounted or named anywhere the worker can see. Neither a
  bearer nor a host source path reaches a grants file, an evidence record, a
  lifecycle record or any worker-visible document.

## What it refuses, and why you may see it

| Situation | Outcome |
|---|---|
| No configuration recorded | `policy/denied` — a group inferred from what the manager happens to hold is not a grant |
| gid 0 | `integrity/schema` — root is the opposite of a dedicated non-authority group |
| A gid the process does not hold | `integrity/schema` — a group it cannot use is not one it was granted |
| Another group the process *does* hold | `integrity/schema` — usable is not configured |
| Reconfiguration to a different group | `policy/denied` — fresh store, not reconfiguration |
| `meta` and the committed operation disagree | `integrity/schema` — including a projection with no operation behind it, and an operation whose projection is gone. The two accounts are not reconciled; a disagreement this manager cannot adjudicate fails closed |
| The workspace root left the group between allocation and launch | `integrity` refusal *before* the engine is invoked |

## Verifying a deployment

The engine matrix takes the group from the environment, so a deployment can
run it against its own provisioned group:

    cd v12/python
    BATON_V12_WORKSPACE_GROUP=$(getent group baton-workspace | cut -d: -f3) \
      PYTHONPATH=src python3 -m unittest tests.manager.test_input_delivery

Unset, the fixture falls back to `os.getgid()`. That proves the mechanism and
says nothing about whether the group is dedicated or non-authority — which is
a property of a deployment and not of any code here. A malformed value is
refused rather than falling back, so a run that meant to prove a provisioned
group cannot silently report a login-group run instead.

`tests.manager.test_input_delivery` also carries the Podman half of the matrix.
It skips where Podman is absent, and a skip is a named absence rather than a
pass — but under M38837 it no longer gates this mechanism's acceptance. See
the engine section below for what is certified and what is not.

## Engines: Docker is certified, Podman is not

**Docker is the only engine this mechanism is certified on.** Approver ruling
M38837 supersedes the earlier two-engine closure gate for this slice: the
complete Docker matrix IS the certification, and Podman is a longer-term
portability certification owned by **W32391**, which is still open. Deploy on
Docker. Treat everything below as retained experimental evidence rather than
as a supported choice, and do not run a deployment on either Podman mode until
W32391 closes with compatible-engine evidence.

The measurements are kept because they were measured rather than predicted,
and because the two modes say different things.

Under **rootful** Podman the mechanism behaved exactly as it does on Docker:
`--user 65532:65532` untouched, the configured group applied as a supplementary
group, and the worker writing its workspace. That is one environment's
observation and not certification — the full case matrix behind the Docker
acceptance was not run there.

Under **rootless** Podman it does not hold. The group is still applied — the
worker really holds the gid — but the bind-mounted workspace arrives owned by
`nobody`:

    running as [65532, 65532]  groups [8291, 65532]   <- applied
    /workspace  mode 02770  gid 65534                 <- not the configured gid
    create -> PermissionError

Rootless Podman runs the container in a user namespace mapping the invoking
user's own uid/gid and its subuid/subgid range. The configured workspace group
is a *supplementary* group of the manager, so it is not in that mapping, and
the setgid group the manager established means nothing inside the container.

A rootless-Podman deployment therefore needs the configured gid mapped into
the container's user namespace (`--gidmap` / `--userns=keep-id:gid=…`). This
manager does not compose those flags: the launch vector is pinned by approver
rulings M34630 and M34916, and adding a namespace mapping to it is a change to
the ruled vector rather than a deployment detail. **W32391 owns that question
along with the rest of Podman certification; until it closes, deploy on
Docker.**

Evidence for all three: `work/records/2026/08/finding-v12-worker-workspace-
writable/evidence/w33936-podman-2026-08-29.txt`.
