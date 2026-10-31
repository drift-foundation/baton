# Worker-entry Docker slice — W384944 / E384992

All five required DockerWorkerEntry cases executed and passed, zero failures/errors/
skips. One focused just test-one run:1.285s unittest body,1.515166s
command wall. Exact case IDs in ledger.json; verbose output in focused/focused.log.

## Candidate and accepted behavior

Only `v12/python/tests/manager/test_worker_entry_engine.py` changed. Candidate SHA256 `fd00cd2b53d349d6fcacea39cb569825354edb4a08af98bf196aa0b4bcad8535`; base `b927e0758e4750d87b6b35f50fb2b8490903bad9c4d036d7ae2cbbc5907c699a`.
A test-local setup accepts explicit immutable BATON_V12_WORKER_ENTRY_IMAGE, verifies
local identity/daemon and absence of image-declared volumes, then reuses the selected
artifact without inherited build. With no selection, existing setup remains.
The selecting run owns image/tag cleanup; shared Lifecycle remains untouched.

Replaced stale foreign-owner assertion with HOST-5 effective manager UID expectation,
retaining configured output group, produced directory and exact output envelope/
assignment checks. Added inspection of the actual runtime ID, image, configured User,
running state, nonprivileged/read-only root, exact three bind mounts, read-only input
and launch, writable output and exact output source. The real exec describe/work arc
establishes the container crossing; unequal UID is not its boundary. All five existing
case IDs retained, with stderr separation, foreign-session refusal, missing-runtime
loss and noninteractive-start loss assertions unchanged. Scripted provider only.

## Source/image provenance

Stable a8cbc9745d1eff51bcfb04d2fe4bb96a5ea3b12d source, all1133 manifest files verified with four allocated
test overlays. Both prior accepted integration/initial-access overlays and accepted
input-delivery correction preserved. Shared worker-entry file matched base before
same-file transfer. Before/after hashes show no run drift. K/shared product files
untouched; no moving product overlay imported.

One explicitly selected offline local build: --pull=false --network=none; pinned base
already installed. Exact base ID, command, unique task tag, worker context hashes and
build log retained. Build 0.113643s, exit0; image `sha256:dd3695db742425b98e20c5b54a02440b68557b98979cd5ab5bb9f88ad45869cf`.
No pull, package installation, image substitution, implicit second build or live model.
Prepared interpreter through just test-one; actual uid1000 and group1001 membership
rechecked, fresh disk-backed root gid1001/mode2770 and selected environment recorded.

## Resources and evidence

Five exact task containers created and confirmed absent after run; all pre-existing
container IDs preserved. Fresh root empty/removed. Unique task tag removed and all
pre-existing image IDs preserved; resource-cleanup.json states whether the built ID
pre-existed and records Docker cleanup output. No cache prune or historical cleanup.
The external supervisor adds only an evidence label to run commands. For docker exec
it records argv then execs the real CLI directly, preserving stdin/stdout/stderr and
streaming behavior; it does not buffer or simulate the transport. Build/run timeouts
1800s/600s, cleanup reserve120s; no timeout/emergency cleanup used.

## Remaining B4

Worker-entry slice ready for independent acceptance on this snapshot. K still owns
one input-delivery engine plus three non-engine frozen-parent cleanup reproductions.
Other custody/endings/adoption and pure fixture inventory remains from prior reports;
no broader test result is claimed. Independent review and joined accepted-source B4/
full-suite gates remain required. No shared helper/product or Git repository mutation.
