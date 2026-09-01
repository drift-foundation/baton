# Deploying the v12 Worker Manager

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
