"""Descriptor-pinned private context storage; never a generic extra mount.

Only the context owner publishes generations. A runtime receives a new working
copy, not a writable generation. This first slice supports the manager UID only;
other runtime ownership needs a qualified normalization profile before launch.
"""

import contextlib
import json
import os
import stat
from dataclasses import dataclass

from ..contracts import canonical_text, digest, digest_of_bytes
from . import intake, workspaces
from . import provider_context as context
from .store import manager_signature

STORAGE_KIND = "provider-context.storage"
STORAGE_ID = "provider-context-storage"
CREDENTIAL_PATH = ".claude/.credentials.json"
CREDENTIAL_TARGET = "/run/baton/credentials/claude"
_DIR_FLAGS = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC
_FILE_FLAGS = os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC


def _pin(fd):
    info = os.fstat(fd)
    return [info.st_dev, info.st_ino]


def _open_absolute(path):
    if type(path) is not str or not path.startswith("/") or path != os.path.normpath(path):
        context._refuse("storage path is not canonical and absolute")
    fd = os.open("/", _DIR_FLAGS)
    pins = [_pin(fd)]
    try:
        for part in path.split("/")[1:]:
            if not part:
                continue
            child = os.open(part, _DIR_FLAGS, dir_fd=fd)
            os.close(fd)
            fd = child
            pins.append(_pin(fd))
        return fd, pins
    except OSError:
        os.close(fd)
        context._refuse("directory ancestry is inaccessible or replaced")


def _private(fd, *, writable=False):
    info = os.fstat(fd)
    if info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) & 0o077 or not info.st_mode & stat.S_IRUSR or (writable and not info.st_mode & stat.S_IWUSR):
        context._refuse("protected custody owner or mode changed")


@dataclass(frozen=True)
class ContextStorage:
    """A private locator, always re-adopted against its committed owner record."""
    path: str
    pins: tuple


@dataclass(frozen=True)
class ContextDelivery:
    context_id: str
    use_id: str
    attempt_id: str
    home: str
    invocation: str
    digest: str


def configure_context_storage(control, path, *, excluded_roots, runtime_uid):
    if type(runtime_uid) is not int or runtime_uid != os.getuid():
        context._refuse("runtime custody normalization profile is unavailable")
    if type(excluded_roots) is not list or not excluded_roots:
        context._refuse("storage exclusion roots must be explicit")
    fd, pins = _open_absolute(path)
    try:
        _private(fd, writable=True)
        excluded = []
        fixed_roots = list(excluded_roots) + [workspaces.configured_workspace_storage(control).place]
        for root in dict.fromkeys(fixed_roots):
            other, other_pins = _open_absolute(root)
            os.close(other)
            if pins[:len(other_pins)] == other_pins or other_pins[:len(pins)] == pins:
                context._refuse("context storage overlaps an excluded root")
            excluded.append({"path": root, "pins": other_pins})
        held = {"path": path, "pins": pins, "excluded": excluded, "runtime_uid": runtime_uid}
        control.transact(STORAGE_ID, STORAGE_KIND, manager_signature(STORAGE_KIND, held), lambda connection: held)
    finally:
        os.close(fd)
    return ContextStorage(path, tuple(tuple(one) for one in pins))


def configured_context_storage(control):
    row = control.operation_record(STORAGE_ID)
    if row is None or row["kind"] != STORAGE_KIND or row["state"] != "committed":
        context._refuse("protected context storage is not configured")
    held = context._document(json.loads(row["result"]), ("path", "pins", "excluded", "runtime_uid"))
    if row["signature"] != manager_signature(STORAGE_KIND, held):
        context._refuse("storage journal disagrees")
    fd, pins = _open_absolute(held["path"])
    try:
        _private(fd, writable=True)
        if pins != held["pins"] or held["runtime_uid"] != os.getuid():
            context._refuse("protected storage object changed")
    finally:
        os.close(fd)
    return ContextStorage(held["path"], tuple(tuple(one) for one in pins))


@contextlib.contextmanager
def _storage(control, storage):
    fixed = configured_context_storage(control)
    if type(storage) is not ContextStorage or storage != fixed:
        context._refuse("storage capability disagrees with its owner")
    fd, pins = _open_absolute(fixed.path)
    try:
        if tuple(tuple(one) for one in pins) != fixed.pins:
            context._refuse("storage changed during adoption")
        _private(fd, writable=True)
        yield fd
    finally:
        os.close(fd)


def _directory(parent, name, *, create=False):
    if type(name) is not str or name in ("", ".", "..") or "/" in name:
        context._refuse("invalid custody component")
    try:
        if create:
            try:
                os.mkdir(name, 0o700, dir_fd=parent)
                os.fsync(parent)
            except FileExistsError:
                pass
        fd = os.open(name, _DIR_FLAGS, dir_fd=parent)
    except OSError:
        context._refuse("custody directory is inaccessible or replaced")
    try:
        _private(fd)
        return fd
    except BaseException:
        os.close(fd)
        raise


@contextlib.contextmanager
def _directories(parent, names, *, create=False):
    handles = []
    try:
        current = parent
        for name in names:
            current = _directory(current, name, create=create)
            handles.append(current)
        yield current
    finally:
        for handle in reversed(handles):
            os.close(handle)


def _read(parent, name, limit, *, immutable=False):
    try:
        fd = os.open(name, _FILE_FLAGS, dir_fd=parent)
    except OSError:
        context._refuse("custody file is inaccessible or replaced")
    try:
        info = os.fstat(fd)
        if immutable and stat.S_IMODE(info.st_mode) != 0o400:
            context._refuse("published metadata file is not immutable")
        if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) & 0o077 or not info.st_mode & stat.S_IRUSR or info.st_size > limit:
            context._refuse("custody file type, ownership or size is invalid")
        chunks = []
        remaining = limit + 1
        while remaining:
            part = os.read(fd, min(65536, remaining))
            if not part:
                break
            chunks.append(part); remaining -= len(part)
        body = b"".join(chunks)
        after = os.fstat(fd)
        if len(body) > limit or len(body) != info.st_size or (info.st_mtime_ns, info.st_ctime_ns, info.st_size) != (after.st_mtime_ns, after.st_ctime_ns, after.st_size):
            context._refuse("custody file changed while measured")
        return body
    finally:
        os.close(fd)


def _write(parent, name, body, *, immutable=False, recover=False):
    try:
        fd = os.open(name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC, 0o600, dir_fd=parent)
    except FileExistsError:
        info = os.stat(name, dir_fd=parent, follow_symlinks=False)
        existing = _read(parent, name, len(body))
        if not recover:
            if existing != body:
                context._refuse("existing custody file differs")
            return
        # Only journal-pinned, uncommitted staging may complete a write. A
        # complete immutable file is adopted; a mutable exact prefix is resumed
        # without truncation. Foreign bytes and immutable partial files refuse.
        mode = stat.S_IMODE(info.st_mode)
        if existing == body and mode == 0o400:
            fd = os.open(name, _FILE_FLAGS, dir_fd=parent)
            try:
                if _pin(fd) != [info.st_dev, info.st_ino]:
                    context._refuse("staged file changed before synchronization")
                os.fsync(fd)
            finally:
                os.close(fd)
            os.fsync(parent)
            return
        if mode != 0o600 or not body.startswith(existing):
            context._refuse("existing custody file differs")
        fd = os.open(name, os.O_WRONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC, dir_fd=parent)
        after = os.fstat(fd)
        if (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns) != (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns):
            os.close(fd)
            context._refuse("staged file changed before recovery")
        os.lseek(fd, len(existing), os.SEEK_SET)
        body = body[len(existing):]
    try:
        view = memoryview(body)
        while view:
            amount = os.write(fd, view)
            if amount <= 0:
                context._refuse("custody write made no progress")
            view = view[amount:]
        if immutable:
            os.fchmod(fd, 0o400)
        os.fsync(fd)
    finally:
        os.close(fd)
    os.fsync(parent)


def _state(home, profile, *, snapshot=False, immutable=False):
    """Inspect types before opening any content; unknown files are never read."""
    allowed = set(profile["state_paths"])
    entries = []
    count = 0
    total = 0
    def walk(parent, prefix, depth):
        nonlocal count, total
        if immutable and stat.S_IMODE(os.fstat(parent).st_mode) != 0o500:
            context._refuse("published state directory is writable")
        if depth > 16:
            context._refuse("context directory depth exceeds its bound")
        # Limit enumeration itself; never list an unbounded worker tree.
        with os.scandir(parent) as listing:
            names = []
            for entry in listing:
                count += 1
                if count > profile["max_entries"]:
                    context._refuse("context entry ceiling exceeded")
                names.append(entry.name)
        for name in sorted(names):
            path = prefix + name
            info = os.stat(name, dir_fd=parent, follow_symlinks=False)
            if path == CREDENTIAL_PATH:
                if snapshot:
                    context._refuse("credential slot entered a generation")
                if not stat.S_ISLNK(info.st_mode) or os.readlink(name, dir_fd=parent) != CREDENTIAL_TARGET:
                    context._refuse("volatile credential slot was substituted")
                continue
            if stat.S_ISDIR(info.st_mode):
                if snapshot and not any(one.startswith(path + "/") for one in allowed):
                    context._refuse("generation contains an unlisted directory")
                child = _directory(parent, name)
                try:
                    if _pin(child) != [info.st_dev, info.st_ino]:
                        context._refuse("context directory replaced during traversal")
                    walk(child, path + "/", depth + 1)
                finally:
                    os.close(child)
            elif not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
                context._refuse("context contains a link or special file")
            elif path in allowed:
                if immutable and stat.S_IMODE(info.st_mode) != 0o400:
                    context._refuse("published state file is writable")
                body = _read(parent, name, profile["max_bytes"] - total)
                total += len(body)
                entries.append((path, body))
            elif snapshot:
                context._refuse("generation contains an unlisted file")
    walk(home, "", 0)
    if set(path for path, body in entries) != allowed:
        context._refuse("required provider state is missing")
    return entries


def _manifest(entries):
    files = [{"path": path, "bytes": len(body), "digest": digest_of_bytes(body)} for path, body in entries]
    return {"entries": files, "bytes": sum(one["bytes"] for one in files), "count": len(files)}


def _copy(parent, entries, *, immutable=False, recover=False):
    for path, body in entries:
        parts = path.split("/")
        with _directories(parent, parts[:-1], create=True) as target:
            _write(target, parts[-1], body, immutable=immutable, recover=recover)
    os.fsync(parent)


def _delivery(control, storage, admitted, pins):
    value = {"context_id": admitted["context_id"], "use_id": admitted["use_id"], "attempt_id": admitted["payload"]["attempt_id"], "pins": pins, "admission_digest": digest(admitted)}
    root = os.path.join(storage.path, admitted["context_id"], "uses", admitted["use_id"])
    return ContextDelivery(value["context_id"], value["use_id"], value["attempt_id"], os.path.join(root, "home"), os.path.join(root, "invocation"), digest(value))


def materialize_context_use(control, storage, *, attempt_id):
    chain, admitted = context._use(control, attempt_id)
    if control.operation_record(context._id("context-discard", admitted["use_id"]) + "-intent") is not None:
        context._refuse("context use is being discarded")
    prior = next((one for one in chain if one["use_id"] == admitted["use_id"] and one["action"] == "deliver"), None)
    if prior is not None:
        return adopt_context_use(control, storage, attempt_id=attempt_id)
    if chain[-1] != admitted:
        context._refuse("context use cannot be materialized")
    profile = context.context_profile_of(control, admitted["payload"]["profile_digest"])
    storage_pins = [list(one) for one in configured_context_storage(control).pins]
    for key in ("repo_pin", "source_pin"):
        other = admitted["payload"][key]
        if storage_pins[:len(other)] == other or other[:len(storage_pins)] == storage_pins:
            context._refuse("context storage overlaps its admitted source or line")
    with _storage(control, storage) as root:
        with _directories(root, [admitted["context_id"]], create=True) as owner:
            entries = []
            if admitted["payload"]["generation"]:
                previous = next(one for one in reversed(chain) if one["action"] == "finalize")
                entries = _generation(owner, str(admitted["payload"]["generation"]), profile, previous["payload"], use_id=previous["use_id"])
            with _directories(owner, ["uses", admitted["use_id"]], create=True) as use:
                _write(use, "identity", canonical_text({"admission_digest": digest(admitted)}).encode())
                with _directories(use, ["home"], create=True) as home:
                    _copy(home, entries)
                    pins = {"use": _pin(use), "home": _pin(home), "owner": _pin(owner)}
                # The invocation witness is per-use. It is never copied from state.
                delivery = _delivery(control, storage, admitted, pins)
    context._transition(control, action="deliver", context_id=admitted["context_id"], use_id=admitted["use_id"], expected_revision=admitted["revision"], payload={"delivery_digest": delivery.digest, "pins": pins})
    return delivery


def adopt_context_use(control, storage, *, attempt_id):
    chain, admitted = context._use(control, attempt_id)
    delivered = next((one for one in chain if one["use_id"] == admitted["use_id"] and one["action"] == "deliver"), None)
    if delivered is None:
        context._refuse("context delivery has no committed pins")
    pins = delivered["payload"]["pins"]
    with _storage(control, storage) as root:
        with _directories(root, [admitted["context_id"]]) as owner:
            with _directories(owner, ["uses", admitted["use_id"]]) as use:
                with _directories(use, ["home"]) as home:
                    if {"use": _pin(use), "home": _pin(home), "owner": _pin(owner)} != pins or _read(use, "identity", 1024) != canonical_text({"admission_digest": digest(admitted)}).encode():
                        context._refuse("original use roots were replaced")
    delivery = _delivery(control, storage, admitted, pins)
    if delivery.digest != delivered["payload"]["delivery_digest"]:
        context._refuse("delivery digest disagrees")
    return delivery


def _generation(owner, number, profile, expected, *, use_id, finish_publication=False):
    with _directories(owner, ["generations", number]) as generation:
        if set(os.listdir(generation)) != {"identity", "manifest", "state"}:
            context._refuse("generation contains an unlisted entry")
        identity = canonical_text({"use_id": use_id, "exclusion_digest": expected["exclusion_digest"]}).encode()
        if _read(generation, "identity", 1024, immutable=True) != identity:
            context._refuse("generation identity disagrees with its original use and exclusion")
        body = _read(generation, "manifest", 1024 * 1024, immutable=True)
        with _directories(generation, ["state"]) as state:
            pins = {"owner": _pin(owner), "generation": _pin(generation), "state": _pin(state)}
            if expected["generation_pins"] != pins:
                context._refuse("committed generation objects were replaced")
            entries = _state(state, profile, snapshot=True, immutable=True)
        manifest = _manifest(entries)
        if body != canonical_text(manifest).encode() or digest(manifest) != expected["manifest_digest"]:
            context._refuse("committed generation is damaged")
        if finish_publication:
            os.fchmod(generation, 0o500)
            os.fsync(generation)
        elif stat.S_IMODE(os.fstat(generation).st_mode) != 0o500:
            context._refuse("published generation directory is writable")
        return entries


def validate_generation(control, storage, context_id, expected):
    chain = context._history(control, context_id)
    finalized = next((one for one in chain if one["action"] == "finalize" and one["payload"] == expected), None)
    if finalized is None:
        context._refuse("generation has no matching committed finalization")
    admitted = next(one for one in chain if one["action"] == "admit" and one["use_id"] == finalized["use_id"])
    profile = context.context_profile_of(control, admitted["payload"]["profile_digest"])
    with _storage(control, storage) as root:
        with _directories(root, [context_id]) as owner:
            _generation(owner, str(expected["generation"]), profile, expected, use_id=admitted["use_id"])


def seal_generation(control, storage, *, attempt_id, exclusion):
    """Only positive owner cleanup allows reading the formerly mutable state."""
    chain, admitted = context._use(control, attempt_id)
    profile = context.context_profile_of(control, admitted["payload"]["profile_digest"])
    actual = intake.cleanup_of(control, attempt_id=attempt_id, retention_policy_digest=profile["retention_policy_digest"])
    if actual is None or actual != exclusion or actual["state"] != "absent" or actual["cleanup"] not in ("complete", "retained"):
        context._refuse("generation has no owner-proved runtime exclusion")
    delivery = adopt_context_use(control, storage, attempt_id=attempt_id)
    number = admitted["payload"]["generation"] + 1
    operation = context._operation("finalize", admitted["context_id"], admitted["use_id"], admitted["revision"] + 1)
    with _storage(control, storage) as root:
        with _directories(root, [admitted["context_id"]]) as owner:
            delivered = next(one for one in chain if one["action"] == "deliver" and one["use_id"] == admitted["use_id"])
            pins = delivered["payload"]["pins"]
            with _directories(owner, ["uses", admitted["use_id"]]) as use:
                with _directories(use, ["home"]) as home:
                    if {"owner": _pin(owner), "use": _pin(use), "home": _pin(home)} != pins:
                        context._refuse("use root changed before state measurement")
                    entries = _state(home, profile)
            manifest = _manifest(entries)
            expected = {"generation": number, "manifest_digest": digest(manifest), "exclusion_digest": digest(actual)}
            identity = {"use_id": admitted["use_id"], "exclusion_digest": digest(actual)}
            staging_kind = "provider-context.staging"
            staging_id = operation + "-staging"
            operands = dict(identity, generation=number, manifest_digest=digest(manifest), delivery_digest=delivery.digest, source_pins=pins)
            recorded = control.operation_record(staging_id)
            held = None
            if recorded is not None:
                if recorded["kind"] != staging_kind or recorded["state"] != "committed":
                    context._refuse("staging has no committed owner")
                held = context._document(json.loads(recorded["result"]), (*operands, "generation_pins"))
                if recorded["signature"] != manager_signature(staging_kind, held) or any(held[key] != value for key, value in operands.items()):
                    context._refuse("staging owner facts changed")
            with _directories(owner, ["generations"], create=True) as generations:
                if str(number) in os.listdir(generations):
                    if held is None:
                        context._refuse("published generation has no original staging pins")
                    expected["generation_pins"] = held["generation_pins"]
                    _generation(owner, str(number), profile, expected, use_id=admitted["use_id"], finish_publication=True)
                    return expected
                # Commit staging object pins and immutable source/exclusion facts
                # before the first file write. Only that operation can resume
                # mutable prefix files. An unowned nonempty directory refuses.
                with _directories(owner, ["staging"], create=True) as staging:
                    with _directories(staging, [operation], create=True) as staged:
                        if held is None and set(os.listdir(staged)) - {"state"}:
                            context._refuse("unowned staging is not empty")
                        with _directories(staged, ["state"], create=True) as state:
                            if held is None and os.listdir(state):
                                context._refuse("unowned staging state is not empty")
                            generation_pins = {"owner": _pin(owner), "generation": _pin(staged), "state": _pin(state)}
                            proposed = dict(operands, generation_pins=generation_pins)
                            if held is not None and held != proposed:
                                context._refuse("original staging objects were replaced")
                            control.transact(staging_id, staging_kind, manager_signature(staging_kind, proposed), lambda connection: proposed)
                            expected["generation_pins"] = generation_pins
                            _write(staged, "identity", canonical_text(identity).encode(), immutable=True, recover=True)
                            _copy(state, entries, immutable=True, recover=True)
                            if _manifest(_state(state, profile, snapshot=True)) != manifest:
                                context._refuse("staged generation disagrees")
                        _write(staged, "manifest", canonical_text(manifest).encode(), immutable=True, recover=True)
                        if set(os.listdir(staged)) != {"identity", "state", "manifest"}:
                            context._refuse("staging contains an unlisted entry")
                        _freeze_directories(staged, freeze_root=False)
                        os.fsync(staged)
                    os.rename(operation, str(number), src_dir_fd=staging, dst_dir_fd=generations)
                    with _directories(generations, [str(number)]) as published:
                        os.fchmod(published, 0o500)
                        os.fsync(published)
                    os.fsync(staging); os.fsync(generations)
    return expected



def _freeze_directories(parent, *, freeze_root=True):
    # This walks only owner-created bounded staging, after the bounded state
    # measurement. Files already have their immutable custody modes.
    with os.scandir(parent) as listing:
        for entry in listing:
            if entry.is_dir(follow_symlinks=False):
                child = _directory(parent, entry.name)
                try:
                    _freeze_directories(child)
                finally:
                    os.close(child)
    if freeze_root:
        os.fchmod(parent, 0o500)
    os.fsync(parent)


def discard_context_use(control, storage, *, attempt_id):
    """Dispose only a finalized old use after independently proving exclusion.

    Published generations remain retained. Unknown and admitted roots are never
    deleted. The invocation witness is private evidence and survives disposal.
    """
    chain, admitted = context._use(control, attempt_id)
    finalized = next((row for row in chain if row["use_id"] == admitted["use_id"] and row["action"] == "finalize"), None)
    if finalized is None:
        context._refuse("only an excluded finalized use may be discarded")
    profile = context.context_profile_of(control, admitted["payload"]["profile_digest"])
    cleanup = intake.cleanup_of(control, attempt_id=attempt_id, retention_policy_digest=profile["retention_policy_digest"])
    if cleanup is None or cleanup["state"] != "absent" or digest(cleanup) != finalized["payload"]["exclusion_digest"]:
        context._refuse("use disposal has no matching exclusion")
    validate_generation(control, storage, admitted["context_id"], finalized["payload"])
    delivered = next(row for row in chain if row["use_id"] == admitted["use_id"] and row["action"] == "deliver")
    operands = {"use_id": admitted["use_id"], "delivery_digest": delivered["payload"]["delivery_digest"], "exclusion_digest": digest(cleanup), "generation_digest": finalized["payload"]["manifest_digest"]}
    kind = "provider-context.discard-use"
    operation = context._id("context-discard", admitted["use_id"])
    signature = manager_signature(kind, operands)
    control.transact(operation + "-intent", kind + ".intent", manager_signature(kind + ".intent", operands), lambda connection: operands)
    def discard(connection):
        with _storage(control, storage) as root:
            with _directories(root, [admitted["context_id"]]) as owner:
                with _directories(owner, ["uses", admitted["use_id"]]) as use:
                    with _directories(use, ["home"]) as home:
                        if {"owner": _pin(owner), "use": _pin(use), "home": _pin(home)} != delivered["payload"]["pins"]:
                            context._refuse("discarded use root was replaced")
                        _clear_owned(home, profile["max_entries"], "")
        return dict(operands, discarded=True)
    return control.transact(operation, kind, signature, discard)


def _clear_owned(parent, remaining, prefix):
    _private(parent, writable=True)
    with os.scandir(parent) as listing:
        names = []
        for entry in listing:
            if len(names) >= remaining:
                context._refuse("disposal entry bound exceeded")
            names.append(entry.name)
    remaining -= len(names)
    for name in names:
        info = os.stat(name, dir_fd=parent, follow_symlinks=False)
        if stat.S_ISDIR(info.st_mode):
            child = _directory(parent, name)
            try:
                if _pin(child) != [info.st_dev, info.st_ino]:
                    context._refuse("disposal directory was replaced")
                remaining = _clear_owned(child, remaining, prefix + name + "/")
                if os.stat(name, dir_fd=parent, follow_symlinks=False).st_ino != info.st_ino:
                    context._refuse("disposal directory changed before removal")
                os.rmdir(name, dir_fd=parent)
            finally:
                os.close(child)
        elif stat.S_ISREG(info.st_mode) and info.st_nlink == 1:
            os.unlink(name, dir_fd=parent)
        elif prefix + name == CREDENTIAL_PATH and stat.S_ISLNK(info.st_mode) and os.readlink(name, dir_fd=parent) == CREDENTIAL_TARGET:
            os.unlink(name, dir_fd=parent)
        else:
            context._refuse("disposal encountered a foreign object")
    os.fsync(parent)
    return remaining


@dataclass(frozen=True)
class ContextMount:
    """Owner-bound exact-use capability, never a caller-nominated mount path."""
    control: object
    storage: ContextStorage
    delivery: ContextDelivery

    def boundary(self):
        actual = adopt_context_use(self.control, self.storage, attempt_id=self.delivery.attempt_id)
        if actual != self.delivery:
            context._refuse("context mount original delivery changed")
        return (os.path.dirname(actual.home), "/run/baton/context", True)


def context_mount_of(control, storage, *, attempt_id):
    return ContextMount(control, storage, adopt_context_use(control, storage, attempt_id=attempt_id))


def read_context_receipt(control, *, attempt_id, artifact_id, workspace_storage):
    """Read the original accepted custody file; never fetch a supplied URL."""
    from . import output, manifests
    frozen = output.frozen_output_of(control, attempt_id)
    collected = intake.intake_receipt_of(control, attempt_id)
    if frozen is None or collected is None or collected["custody"] != "accepted" or any(frozen[key] != collected[key] for key in ("result_id", "manifest_digest")):
        context._refuse("receipt custody is not accepted")
    held = manifests.load_manifest(control, frozen["manifest_digest"], "resultManifest")
    candidates = [one for one in held["outputs"] if one["name"] == "provider-context-receipt" and one["status"] == "present" and one["artifact"] and one["artifact"]["artifact_id"] == artifact_id]
    if len(candidates) != 1:
        context._refuse("retained receipt artifact is not original")
    candidate = candidates[0]
    entries = candidate["content_manifest"]["entries"]
    if len(entries) != 1 or entries[0]["path"] != "receipt.json" or entries[0]["bytes"] > 16384:
        context._refuse("retained receipt is not one bounded file")
    artifacts = [one for one in collected["artifacts"] if one["artifact_id"] == artifact_id]
    root_path = os.path.join(workspace_storage, "custody", attempt_id, "provider-context-receipt")
    if len(artifacts) != 1 or artifacts[0]["custody_locator"] != "file://" + root_path:
        context._refuse("retained receipt locator disagrees with owned custody")
    fd, pins = _open_absolute(root_path)
    try:
        receipt = os.open("receipt.json", _FILE_FLAGS, dir_fd=fd)
        try:
            before = os.fstat(receipt)
            if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1 or before.st_uid != os.getuid() or before.st_size > 16384 or before.st_mode & 0o222:
                context._refuse("retained receipt type, owner, mode or size disagrees")
            body = bytearray()
            while len(body) <= 16384:
                part = os.read(receipt, 16385-len(body))
                if not part:
                    break
                body.extend(part)
            after = os.fstat(receipt)
            if (before.st_size, before.st_mtime_ns, before.st_ctime_ns) != (after.st_size, after.st_mtime_ns, after.st_ctime_ns):
                context._refuse("retained receipt changed while read")
            body = bytes(body)
        finally:
            os.close(receipt)
    finally:
        os.close(fd)
    if len(body) != entries[0]["bytes"] or digest_of_bytes(body) != entries[0]["content_digest"]:
        context._refuse("retained receipt sealed bytes disagree")
    return body
