# Exact deterministic runner for independent review

Prepared by baton.tuner under W106673 claim 106813. Owner response M106756
authorizes preparation only. Codex reviews these exact bytes and invocation;
Slawomir then decides the separate execution checkpoint. Do not run --run from a
managed agent context. No installation or permanent service is needed.

## Artifacts and proposed operator invocation

The runner is evidence/host_runner.py; the unprivileged payload is
evidence/resident.py. Reviewed SHA-256 values are recorded in
evidence/runner-digests.json. Recheck both against the independent review before
execution; changed bytes require renewed review. Paths stay under the existing
operator-owned dossier and must not be edited during the operator checkpoint.

After independent review and separate owner approval, the exact proposed host
command is:

    sudo -- /usr/bin/python3 /home/sl/src/baton/work/records/2026/09/finding-v12-live-session-workspace-detach/evidence/host_runner.py --run

This command is an execution proposal, not a command run during preparation.
It invokes local /usr/bin/docker at unix:///var/run/docker.sock with a minimal
environment that does not inherit Docker contexts, remote hosts, SSH or user
credential configuration. No image pull/build, provider, network, credential
search, production change or host group setup is performed.

The chosen installed local image is:
sha256:9351a9a0a697a69e156f8bd067dd5ef3f9fa9b110abbdbbda1f343c622c7adc0

Its repository digest is the reference worker recipe's existing Python base:
python@sha256:8fef26df932191825664e4957ff488c96dfe64918327634a357a55facbc994d3

Exact permitted image inspection succeeded; the image declares no volumes or
entrypoint and its default command is python3. The runner overrides the command
to execute only the staged resident. --pull=never and image-ID equality prevent
implicit acquisition or tag drift. Runtime image behavior remains untested.

The proposed fixture group is numeric 65532, matching the fixed runtime
65532:65532. It applies only to disposable root-owned fixture directories.
The local name-service query returned no group entry for 65532; no group is
created and no host membership is changed. The privileged operator acts as
the fixture consumer. This does not establish the dedicated production manager
group or solve W105706's different-uid access proof. Owner review must accept
this explicit fixture choice before execution.

## Privileged boundary

Requires an operator host Python with pidfd support and glibc wrappers for
setns, open_tree, move_mount, mount_setattr and umount2; symbols were inspected,
not called, during preparation. Requires rootful local Docker with no user
namespace remapping. Container and controller must have different mount
namespaces and the same owning user namespace. Unexpected topology refuses.

The short-lived forked controller alone requires CAP_SYS_ADMIN, CAP_SYS_CHROOT
and host process/root/namespace visibility allowed by ptrace/LSM policy. It never
changes host mount propagation or a host mount. It enters the verified worker
mount namespace, chroots through a pinned container-root descriptor, closes
target references, and operates only on /output.

Reattachment uses open_tree(OPEN_TREE_CLONE|AT_EMPTY_PATH) on the pinned fixture
source, yielding a detached bind object. mount_setattr marks that detached clone
private/nosuid/nodev; move_mount attaches it at /output after namespace entry.
This avoids assuming that the host controller's /proc/self/fd remains visible
through the container's proc PID namespace after chroot. No file descriptor is
sent to the worker. Source and target roots are fixed by the runner, not CLI
operands. Failed unattached clones are released when the controller exits;
that is not accepted as revocation of any worker-visible mount.

Revocation itself is exclusively umount2('/output', 0). No lazy or forced
unmount, worker capability, privileged container, arbitrary shell/target/PID,
or retry with stronger flags exists. See the primary syscall descriptions:
[open_tree](https://man7.org/linux/man-pages/man2/open_tree.2.html),
[move_mount](https://man7.org/linux/man-pages/man2/move_mount.2.html),
[mount_setattr](https://man7.org/linux/man-pages/man2/mount_setattr.2.html), and
[umount](https://man7.org/linux/man-pages/man2/umount.2.html).

## Disposable topology and identity

Each run creates one fresh /tmp/baton-w106673-* directory, mode 0700, printed
before runtime creation. All logs, copied resident scripts, intent records,
receipts and fixture workspaces live there. Children use fixed scenario names;
no existing directory is accepted as an external target. Workspace roots are
root:65532 mode 02775 and the resident creates files under umask 0002.

Each container is fixed uid/gid 65532:65532, cap-drop ALL, no-new-privileges,
network none, read-only root, default Docker seccomp, private bind propagation,
bounded CPU/memory/PID count and /tmp scratch. Only /output is a writable
workspace bind; /resident.py is read-only. No host directory ancestor, Docker
socket, credential mount, source checkout or host PID namespace is exposed.

Create intent is durable before Docker creation. Full returned container ID,
run nonce label, image ID, init PID/start time/pidfd, namespace device/inode,
workspace device/inode and resident session nonce are registered. Each operation
rechecks identity and container restrictions. Docker top must show only the
resident outside its awaited security-probe child. Namespace comparison follows
the proc magic link and compares the actual namespace object, not its symlink.

Mount-table checks reject workspace aliases, submount exposure and shared
propagation. The container root must be read-only and private. The resident
probes actual mount/remount and new-user-plus-mount-namespace permission in a
short-lived child; both must refuse EPERM. Cap sets must all be zero, with
no-new-privileges and seccomp active. Any unexpected success aborts. This is a
bounded deterministic posture proof, not a claim about malicious kernel exploits.

## Gates and experiment cases

A persisted detach intent closes both result consumption and writer admission
before the syscall. Only ordinary unmount success followed by exact namespace,
mount absence and resident access-denial observations creates a current
revocation receipt. Consumption checks the receipt before the only fixture
content-read site. A receipt is consumed once and cannot authorize a later
generation. Reattachment is uncertain until current topology/access is proved.

The happy fixture writes round one, declares handles closed/cwd outside output,
detaches, consumes exact bytes, reattaches and writes round two with the same
container, process, session nonce and workspace inode. It detaches and consumes
round two too. Fresh mount IDs are observed on each attachment.

Separate fixtures cover an open output file and cwd in /output after false
completion declarations. Both must produce EBUSY. This is recorded as a
protocol violation, followed by shutdown; there is no close-and-retry detach.
Omitted detach denies both gates. The controller subprocess also actually exits
before unmount and after successful unmount but before acknowledgment. The
parent records the actual namespace topology while leaving gates closed.

For both losses and other negatives the gate is reconstructed from its durable
file, deliberately discarding every prior permission. Then both denials are
checked again and the runner takes confirmed shutdown. This exercises real
helper process interruption plus fixture gate reload. It is not execution of a
production manager restart, nor a claim to reconstruct a live Docker stdio
connection after killing the outer runner.

A final equivalent stop/start fixture reuses the same workspace and image,
with a new resident nonce. Timings are monotonic completion-to-consumer and
correction-to-write observations, including diagnostic overhead. Two detach
writes and one stop/start comparison are not a general speedup claim. No real
Claude session is started; that remains a later separately authorized checkpoint.

## Failure, shutdown and retained evidence

On every failure, result.json reports failed-or-blocked and preserves evidence.
A running container is stopped only after full identity checks. Stop must yield
not-running/PID 0, the original pidfd must signal exit, and a host /proc scan
must find no surviving process in the recorded namespace. An inaccessible
namespace, identity mismatch, timeout or failed cleanup keeps gates denied.
No receipt follows an unconfirmed stop.

For a create/start failure before full process registration, automatic shutdown
cannot safely meet the full identity contract. The runner leaves the recorded
create-intent/ID and isolated resource for operator inspection. It never guesses
a PID or acts on a matching name alone. Similarly, interruption of the outer
runner leaves no resume command capable of trusting an old receipt; operator
inspection and exact cleanup remain required. No result may be consumed from
such an interrupted run.

The runner deliberately preserves all stopped containers and generated files;
it issues no docker rm, recursive filesystem removal or host cleanup. It closes
its own pipes and descriptors after confirmed stopping. The operator receives
the exact temporary root and ID/nonce event records for later cleanup. A --run
failure may leave a live identified container; it must be resolved before
treating the experiment as ended.

## Preparation validation

Command executed without Docker or privileged syscalls:

    python3 work/records/2026/09/finding-v12-live-session-workspace-detach/evidence/host_runner.py --self-test

Six focused tests passed: omitted-detach denial, actual namespace-pin identity,
restart discarding permissions, stale/duplicate receipt refusal, no consumer
read while denied, and both gates closed during partial attachment. The tests
own and clean temporary gate files only. Both scripts parse with ast.parse and
required host libc symbols exist. No successful kernel, resident-container,
cleanup, session or timing result is claimed.

Operational observations are in evidence/runner-inputs.json. Generic Docker
image listing was denied socket access and was not escalated. A separate
permitted exact image inspection resolved the existing recipe-pinned base.
The first format assumed a Volumes member and failed; an index lookup correctly
reported its absence. No deployment change or defect workaround was performed.
