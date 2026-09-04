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
`baton.v12.single-worker-deployment/2` and exactly these members:

| Member | Required value |
|---|---|
| `schema` | `baton.v12.single-worker-deployment/2` |
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
| `input_source`, `input_manifest` | Absolute already-staged source directory and its complete frozen `inputManifest` document, whose one source destination is exactly `source` |
| `task_document` | Absolute path to the frozen JSON workload document this profile's input manifest declares as its `human_contract` artifact |
| `launch_contract`, `launch_role` | The immutable worker launch contract and `implementation` role |

Schema `/2` supersedes `/1` and there is no fallback: `/2` adds a required
member, which makes it a new contract rather than a compatible reading of the
old one, and a configuration that named no task would start the certified
worker over an input root it refuses before doing any provider work.

Unknown or missing members refuse. Before an offer exists, the factory checks
the complete input manifest, relates its Authority, assignment contract,
policy, profile and image to the configured values, measures `input_source`,
validates the credential mapping and OCI posture, opens Authority against the
expected UUID, and proves the configured participant resolves to the
configured principal and Work.

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
      --incarnation submit-20260903-01 \
      submit --document /etc/baton/bootstrap-job.json

    BATON_V12_SINGLE_WORKER_CONFIG=/etc/baton/single-worker.json \
    PYTHONPATH=src:. python3 -m tools.job_manager \
      --store /var/lib/baton/v12/jobs.sqlite3 \
      --incarnation manager-20260903-01 \
      serve --control /var/lib/baton/v12/worker-control.sqlite3 \
      --operations tools.single_worker:factory --interval 5

Ordinary status is a separate read-only command and needs no Authority or
factory capability:

    PYTHONPATH=src:. python3 -m tools.job_manager \
      --store /var/lib/baton/v12/jobs.sqlite3 \
      --incarnation status-20260903-01 \
      status --control /var/lib/baton/v12/worker-control.sqlite3

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
