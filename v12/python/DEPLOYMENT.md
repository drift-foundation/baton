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
material this manager cannot inspect, collect or clean up, because it is not
the owner and the group bit is not set for it. This Work's own
`test_an_owner_only_output_fails_closed_rather_than_widening` drives exactly
that case and requires the manager to fail closed rather than widen the mode.

Failing closed is deliberate: a manager that `chmod`ed its way in would be
taking custody the deployment never granted it, and a manager that reported
such an attempt as cleaned up would be erasing material that is still on disk.

**Unconditional manager custody — the property that holds regardless of
worker-selected modes — is NOT provided here.** Approver ruling M36166 named
the mechanism (a short-lived manager-controlled custody helper on the exact
attempt directory; umask 002 is explicitly not it) and created **W36540** to
provide it. Until that lands, a deployment should expect cleanup of a
worker-created tree to fail closed with the ownership named, rather than to
succeed.

The manager then:

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

`tests.manager.test_input_delivery` also carries the compatible-Podman half of
the matrix. It skips where Podman is absent; a skip is a named operational
limit and not a pass.

## Rootless Podman: the group does not reach the worker

**Measured, not predicted.** On Docker and on **rootful** Podman the mechanism
holds exactly: `--user 65532:65532` is untouched, the configured group is
applied as a supplementary group, and the worker writes its workspace.

Under **rootless** Podman it does not. The group is still applied — the worker
really holds the gid — but the bind-mounted workspace arrives owned by
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
the ruled vector rather than a deployment detail. **Until that is ruled on,
use Docker or rootful Podman.**

Evidence for all three: `work/records/2026/08/finding-v12-worker-workspace-
writable/evidence/w33936-podman-2026-08-29.txt`.
