# W325695 implementation packet task

Implement only descendant-compatible private verifier roots using manager-established
mount roots. Current base 14e52d80679de5e844f72324df632da5e01cf393. This is future private v12 product work, not authority
to edit host source. No retained W321528 worker patch is imported: its independent
reporting work and W321776 task /3 retain ownership. Before execution coordinator must
confirm actual worker/test overlap and rebind accepted base if either lands meanwhile.

Selected mechanism: fixed /run/baton-verifier/{home,tmp,cache,pycache}, each a separate
private rw,noexec,nosuid,nodev tmpfs mount. Parent and mountpoint scaffolding are ordinary
root-owned0755 image directories in read-only rootfs, outside all writable mounts;
no mutable ancestor. Engine initializes each mount root mode0700 and exact trusted
execution UID/GID (not hardcoded65532, not ambient login group). Provider and verifier
keep same selected runtime identity; no worker privilege, second identity/container,
host socket, or new provider access. HOME root contains no credential link; original
credential slot remains readable by this UID, so do not claim full credential isolation.

Proposed bounded partition, from existing source_boundary owner: /tmp32MiB,
/dev/shm16MiB, verifier home4MiB,tmp16MiB,cache4MiB,pycache8MiB. Aggregate scratch80MiB
unchanged, workspace floor strictly above80MiB unchanged. Existing legacy log decoy
16MiB remains separately accounted; total tmpfs96MiB, existing2GiB memory ceiling.
This redistributes old shared /tmp64MiB, not extra capacity. Publish exact per-root
limits and test ENOSPC/refusal; do not silently fall back to /tmp or candidate when
one root fills. If required focused workload cannot fit, preserve measured failure
and propose capacity adjustment instead of silently growing it. Checkout/build cache/
retained test artifacts/output/logs remain disk-backed under existing storage policy;
these mounts hold disposable ephemera only. No new cleanup of retained material.

Extend composition at existing source_boundary/OCI owners; avoid globally changing
legacy RESTRICTIONS or consent containers. An explicit versioned trusted runtime-layout
selection binds topology, image digest, adapter/policy digests and effective identity.
Use the existing digest-bound runtime-profile/adapter configuration boundary, with a
new schema/name for new semantics; never append members to frozen task /2, old result
or worker-launch documents. If a new worker-launch shape is actually unavoidable,
stop with exact conflict rather than silently extend it. Worker and manager must agree
on immutable layout identity before provider launch. New image contains fixed root
scaffolding and trusted layout marker; pinned source/image checks bind its exact bytes.
No auto-detection of arbitrary directories. Old image+new layout refuses before provider;
new image+missing/old layout refuses before provider. Existing explicitly legacy profile
remains legacy and receives no new success claim. Only new compatible pair establishes
this fix; old images may still author it in a development Job.

Worker opens and validates the selected mount roots before provider runs: ordinary
owned directories,0700,canonical expected targets,mount identity/fs type/options and
actual immutable ancestors. Retain exact object identity pins and compare before
verification. Use stable mounted pathnames in closed verifier environment, not proc-fd
aliases or realpath fallback. The mount is the path-binding boundary; lstat alone is
not proof. Reject absent/nonmount/symlink/wrong owner/mode/layout/replaced/unlinked
roots honestly. Preserve existing adversarial tests; replace descriptor-spelling
assertions only where new binding evidence covers their security outcome.
Mount-root names resist rename/removal, but nested contents remain mutable same-UID
objects: do not claim protection of every file, no ptrace claim, no secret-access claim.
Nested ordinary adapters using tempfile below TMPDIR must work with their existing
canonical checks; no blanket removal of path checks to make fixtures pass.

Lifetime: mount roots belong to exact attempt container, survive provider exit and
verifier child/grandchild descriptor closure. Individual verification completion is
not process-tree cessation. On start failure/timeout retain candidate and exact sealed
inputs, record failure honestly; keep root lifetime through the runtime teardown.
Existing manager stop/destroy/inspect exact-runtime lifecycle must confirm absence
before treating all descendants/ephemera gone. If verifier descendants outlive leader,
do not claim cleaned solely from wait(); preserve cleanup uncertainty until exact
container cessation. No retry, no arbitrary PID kill or host cleanup. Preserve safe
ordinary result text; separately authorized private log capture stays governed by its
existing policy, not copied to proposal text.

Focused deterministic checks: ordinary children/grandchildren and nested adapter;
source-boundary accounting and exact OCI vector/refusal; adversarial replacement,
missing root, mode/identity/mount mismatch; start error and timeout including surviving
descendants; no candidate/cache contamination, input preservation and safe outputs.
Add focused coverage needed for this change and run selected packet vector. Existing
prior W321528186-pass evidence belongs to its exact0add bytes outside worker; descriptor
failure40/20 remains recorded. Do not import unaccepted bytes solely to replay that
number. Joined acceptance later reruns exact updated candidate186 vector (plus new
cases) in corrected verifier environment after source ownership coordination.

No engine/provider/authentication run inside this implementation task. Simulated
mount fixtures prove composition/refusal only. Packet ENGINE-PROOF.md specifies a
separately selected no-provider kernel proof after reviewed candidate image exists.
Produce candidate promptly after focused checks; no whole-suite reassurance. Report
exact changed paths, measured tests, unresolved behavior and proposed new image/source
binding. Independent review and human Git ownership remain required. Read DESIGN
HOST-3..5,ART,REC,LIM,VER-1..5; no task /3 or verifier-view materialization work.
