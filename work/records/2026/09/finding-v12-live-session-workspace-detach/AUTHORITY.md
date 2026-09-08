# Bounded controller authority request — W106673

## Current disposition — 2026-09-07

Owner approved PREPARATION of a minimal dossier-local experiment runner by tuner,
independent review by Codex, then a separate exact privileged invocation by
Slawomir. No permanent service/install or privileged execution is approved now.
The request below remains mechanism evidence; any implication that installing a
general controller is required is superseded. Select and report the exact existing
fixture image/group and execution boundary for operator review. First use only
the deterministic resident, no provider/credentials/network. See FINDING's owner
response to obligation 106736 for the authoritative bounded preparation scope.

Prepared 2026-09-07 by baton.tuner. This document requests authority; it does
not grant it. No mount, namespace-entry, privileged-container or agent-session
operation has been attempted.

## Observed blocker

`evidence/preflight.json` records the current managed execution context:
effective, permitted, bounding and ambient capabilities are zero;
no-new-privileges and seccomp are enabled. Tools exist, but their installation
does not grant mount authority. Separately permitted standalone Docker reads
report a reachable daemon with AppArmor/built-in seccomp and no experiment
container (`evidence/direct-docker-preflight.json`). The same reads from the
Python preflight subprocess are denied Docker socket access; those failures
remain in `preflight.json`. An authorized standalone read is not authority for
an arbitrary Python controller to drive the daemon.
Repository `worker_manager/oci.py:RESTRICTIONS` likewise drops all worker
capabilities, preserves uid/gid 65532:65532 and enables no-new-privileges.

Ordinary unmount requires CAP_SYS_ADMIN. Entering an existing mount namespace
requires CAP_SYS_ADMIN and CAP_SYS_CHROOT in the caller's user namespace, plus
CAP_SYS_ADMIN in the namespace's owning user namespace. Reading a different
process's root is also subject to a ptrace access check. See
[umount(2)](https://man7.org/linux/man-pages/man2/umount.2.html),
[setns(2)](https://man7.org/linux/man-pages/man2/setns.2.html), and
[proc_pid_root(5)](https://man7.org/linux/man-pages/man5/proc_pid_root.5.html).

An unprivileged nested namespace is not an equivalent proof: it changes a
different mount view and inherited mounts can be locked against individual
unmount. We must operate on the actual resident's namespace and inspect its
propagation/ownership arrangement. See
[mount_namespaces(7)](https://man7.org/linux/man-pages/man7/mount_namespaces.7.html).

## Requested execution boundary

Provide an operator-owned host controller, executed outside the managed
sandbox, restricted to one registered disposable experiment at a time. The
controller alone holds mount/namespace authority; neither resident nor agent
receives CAP_SYS_ADMIN, a Docker socket, a host PID namespace, or a host mount.
No `docker --privileged`, `docker exec --privileged`, broad sudo shell, daemon
configuration change, or production adapter change is requested.

The operator must approve/install the helper's exact implementation and its
direct invocation and Docker access before execution. This is a mechanism proposal for that
review, not a ready privileged executable. Needed host privileges are namespace
entry and mount operations as specified above, plus visibility of the exact
worker PID's namespace/root under host ptrace policy (e.g. operator-managed
CAP_SYS_PTRACE where required). Do not grant those capabilities to this agent
context or a worker. Missing permission is a refusal, not an invitation to
add capabilities or disable LSM/seccomp controls until it works.

The controller's closed operations are `inspect`, `attach`, `detach`,
`reconcile`, and `shutdown`. Inputs identify the registered run, expected
assignment generation and prior receipt. There is no arbitrary command,
filesystem path, PID or mount target operand. Register and pin before use:

- full container ID, experiment label `baton.experiment=W106673`, unique run
  nonce, immutable image digest, init PID plus process start time/pidfd;
- target mount namespace identity and its owning user namespace;
- disposable workspace device/inode and fixture path under a fresh
  `/tmp/baton-w106673-<nonce>/` root; exact configured workspace group;
- assignment generation, monotonically ordered operation ID, and resident
  script digest; controller state/receipts outside worker-visible mounts.

The operator creates/owns the registry; a worker-authored manifest must not
choose what the privileged helper enters or unmounts. Full identity checks
precede every operation and teardown; PID/name reuse is insufficient.

## Minimal topology and mechanism to implement after approval

Use one existing immutable Python-capable image, no rebuild. The deterministic
resident is `evidence/resident.py`, mounted read-only outside `/output`. Its
cwd, stdio control, logs and tmpfs scratch remain outside `/output`. Workspace
defaults follow the accepted development-line policy: files 0664, directories
02775, executables 0775; no credentials in the fixture. Provision the dedicated
group explicitly rather than using the current unset test-group environment.

The resident runs unprivileged with all capabilities dropped, no-new-privileges,
default Docker seccomp/AppArmor, read-only root, no network and no credentials.
Its one writable fixture mount is `/output`. Only bounded scratch is otherwise
writable. No second workspace mount or ancestor mount may provide an alias.
The backing mountpoint exposed when detached must be on read-only root and
contain no result data. Stop if the image cannot provide that topology without
an image change; do not add writable underlay as a substitute for revocation.

`attach`: the host controller opens the registered source, proves its pin,
enters only the registered worker mount namespace, and binds it at fixed
`/output` through a helper-held source descriptor. The source descriptor is
never passed to the resident. Resolve target within the pinned container root,
not the helper's host root. Prove private mount propagation and one exact
workspace mount, close all temporary descriptors, then record the new mount
identity and generation. The feasibility of descriptor-based reattachment
across this namespace boundary is part of the OS experiment, not assumed success.

`detach`: after the fixture's completion declaration, verify the exact current
mount/generation and private propagation. Release the helper's own references
inside `/output` before calling `umount2('/output', 0)` in that same namespace;
otherwise the helper itself would create a busy false negative. No lazy,
forced or retry-with-stronger-flags variant is allowed. A successful syscall is
followed by target namespace mount-table verification and resident access
probes; only then durably record a revocation receipt. Verify the worker cannot
create a namespace retaining an alias or remount the source under its actual
capability/seccomp posture. Unproven alternate access keeps consumption closed.

`reconcile`: after a missing acknowledgment/controller restart, default both
consumption and reassignment to denied. Inspect the registered live process,
mount namespace and exact generation. Only complete current evidence can
produce a reconciled receipt. An absent pathname alone is not enough. On any
identity mismatch, inaccessible namespace, stale evidence or incomplete
reconciliation, use the confirmed-shutdown fallback instead of guessing.

`shutdown`: stop only the fully identified experiment container. Confirm it is
not running, its recorded init process is gone, and no surviving experiment
worker/mount namespace holds writable access before allowing consumption.
A stop request or timeout is not confirmation. Preserve resources/evidence and
keep both gates denied when cleanup cannot be confirmed. Teardown never acts
on unrelated containers or host/source/canonical mounts.

## Exact acceptance after authority is installed

Start with one deterministic resident and no provider call. Write round one,
declare completion with handles closed, detach, prove access absent, consume
the same stable bytes, reattach, then write round two. Compare container ID,
resident PID/start time, fixture nonce and workspace device/inode throughout.
Mount ID may change on reattach; it must be freshly recorded, never assumed
equal to the old attachment.

Use fresh identified fixtures for open-file and workspace-cwd busy cases. The
resident has explicit false-completion commands for them. After EBUSY, record
the protocol violation and require confirmed shutdown; releasing the handle
and proceeding with a second unmount is not the approved fallback.

Inject controller interruption before detach and after syscall success but
before receipt publication. Also omit detach and submit old/duplicate receipts
against a new generation. Every case must demonstrate zero consumption and
zero new writer admission until exact reconciliation or confirmed shutdown.
Controller state simulation alone is not evidence of kernel revocation.

Measure monotonic completion-to-consumer-ready and correction-request-to-first-
write intervals against one equivalent stop/start sequence over the same fixture
and image. Report startup/session costs separately; no image rebuild or copy
enters either timing. A single comparison is an observation, not a general
performance claim.

Only after the OS path passes: one authorized real Claude session, two turns,
same live agent process/session across review and reattachment. The operator
must name the exact existing runtime image, network/provider and separate
credential-delivery authority. No credential search, provider call or cached-
transcript substitute is authorized by this request. If the session cannot
release its cwd/descriptors, report the failure and keep stop-before-consume.

## Operator decision requested

Approve this bounded controller design and identify its implementation/install
owner, exact callable helper and execution policy; name the existing fixture
image and dedicated workspace group. Alternatively retain the existing
shutdown model and return the experiment as blocked. No production adoption is
requested. Real-session credential/runtime authority remains a later explicit
checkpoint after the OS mechanism passes.

## Concrete runner replaces the earlier service proposal — 2026-09-07

RUNNER.md now owns the exact proposed operator invocation and execution boundary;
evidence/host_runner.py and resident.py are prepared candidate bytes.
The earlier requests to install a controller, expose separate callable operations
or create a general registry service are superseded. This is one disposable
script with fixed scenarios and retained fixture state, no permanent service.
Slawomir alone executes it after independent byte/invocation review and a separate
execution checkpoint. Descriptor-based reattachment is specified in RUNNER.md;
ordinary umount2(flags=0) and all uncertainty/shutdown gates remain mandatory.
The real-Claude credential/runtime checkpoint is still separate and pending.
