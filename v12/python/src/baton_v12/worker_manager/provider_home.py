"""Manager-owned Job/worker homes; never output or attempt cleanup roots.

A holder change requires positive, fresh runtime-cessation evidence. An ended
attempt or released scheduler allocation is not that evidence. This owner
stores plain identity beside the home; only home/ may enter a container.
"""
from contextlib import contextmanager
from datetime import datetime, timezone
import fcntl
import json
import os
from pathlib import Path
import stat
import uuid

from ..contracts import digest

SCHEMA = "baton.provider-home/1"
TARGET = "/run/baton/provider-home"


class HomeRefusal(ValueError):
    pass


class HomePending(HomeRefusal):
    """Retry after ordinary runtime settlement; no owner decision needed."""


def identity(authority_uuid, job_id, worker_id):
    values = {"authority_uuid": authority_uuid, "job_id": job_id,
              "worker_id": worker_id}
    if any(type(value) is not str or not value for value in values.values()):
        raise HomeRefusal("a provider home requires authority, Job and worker identity")
    return values


def location(root, bound):
    if set(bound) != {"authority_uuid", "job_id", "worker_id"}:
        raise HomeRefusal("provider home identity members disagree")
    bound = identity(**bound)
    job = {key: bound[key] for key in ("authority_uuid", "job_id")}
    return Path(root) / digest(job)[7:] / digest(bound)[7:]


def check_placement(root, excluded):
    root = os.path.abspath(root)
    for other in excluded:
        other = os.path.abspath(other)
        if os.path.commonpath((root, other)) in (root, other):
            raise HomeRefusal("provider homes overlap a protected storage family")
    return root


@contextmanager
def _directory(path, *, create=False):
    """Hold every ancestor no-follow; never repair ownership or permissions."""
    path = Path(path)
    if not path.is_absolute():
        raise HomeRefusal("provider home storage must be absolute")
    fd = os.open("/", os.O_RDONLY | os.O_DIRECTORY)
    try:
        for name in path.parts[1:]:
            if create:
                try:
                    os.mkdir(name, 0o700, dir_fd=fd)
                    os.fsync(fd)
                except FileExistsError:
                    pass
            child = os.open(name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                            dir_fd=fd)
            os.close(fd)
            fd = child
        yield fd
    finally:
        os.close(fd)


def _private(fd):
    state = os.fstat(fd)
    if state.st_uid != os.getuid() or stat.S_IMODE(state.st_mode) != 0o700:
        raise HomeRefusal("provider home directory is not owned and private")


def _read(fd, name="record.json"):
    try:
        entry = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK,
                        dir_fd=fd)
    except FileNotFoundError:
        return None
    with os.fdopen(entry, "rb") as source:
        state = os.fstat(source.fileno())
        if (not stat.S_ISREG(state.st_mode) or state.st_uid != os.getuid()
                or stat.S_IMODE(state.st_mode) != 0o600 or state.st_size > 1024 * 1024):
            raise HomeRefusal("provider home record is not an owned private regular file")
        try:
            return json.loads(source.read(1024 * 1024 + 1))
        except (ValueError, UnicodeError):
            raise HomeRefusal("provider home record is unreadable") from None


def _write(fd, record, filename="record.json"):
    name = ".record-" + uuid.uuid4().hex
    entry = os.open(name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                    0o600, dir_fd=fd)
    try:
        with os.fdopen(entry, "wb") as target:
            target.write((json.dumps(record, ensure_ascii=True, sort_keys=True,
                                     separators=(",", ":")) + "\n").encode())
            target.flush()
            os.fsync(target.fileno())
        os.rename(name, filename, src_dir_fd=fd, dst_dir_fd=fd)
        os.fsync(fd)
    finally:
        try:
            os.unlink(name, dir_fd=fd)
        except FileNotFoundError:
            pass


def _time(value):
    if type(value) is not str:
        raise ValueError("missing observation time")
    held = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if held.tzinfo is None:
        raise ValueError("unqualified observation time")
    return held


def ceased(evidence, holder):
    """Evidence belongs to this exact holder; unknown/stale always refuses."""
    if type(evidence) is not dict or evidence.get("attempt_id") != holder:
        return False
    if evidence.get("runtime") == "not-started" and evidence.get("ended_before_start") is True:
        return True
    if evidence.get("runtime") not in ("absent", "destroyed") or evidence.get("cleanup") not in ("complete", "retained"):
        return False
    try:
        return _time(evidence["observed_at"]) >= _time(evidence["last_activity_at"])
    except (ValueError, KeyError, TypeError):
        return False


def acquire(root, *, authority_uuid, job_id, worker_id, attempt_id,
            excluded=(), previous_runtime=None, now=None):
    """Record a holder before launch, returning the only mountable directory.

    `previous_runtime(holder)` must resolve the exact attempt through the
    runtime owner. A missing callback cannot authorize a different holder.
    Replays of the same holder are idempotent, including a crash before launch.
    """
    if type(attempt_id) is not str or not attempt_id:
        raise HomeRefusal("provider home holder is absent")
    bound = identity(authority_uuid, job_id, worker_id)
    root = check_placement(root, excluded)
    place = location(root, bound)
    # Root and both digest components are owned manager directories. The
    # manager never enumerates or reads provider-owned contents under home/.
    with _directory(root, create=True) as root_fd:
        _private(root_fd)
    with _directory(place.parent, create=True) as job_fd:
        _private(job_fd)
    with _directory(place, create=True) as fd:
        _private(fd)
        lock = os.dup(fd)
        try:
            fcntl.flock(lock, fcntl.LOCK_EX)
            record = _read(fd)
            try:
                home_info = os.stat("home", dir_fd=fd, follow_symlinks=False)
            except FileNotFoundError:
                home_info = None
            if home_info is not None and (not stat.S_ISDIR(home_info.st_mode) or home_info.st_uid != os.getuid() or stat.S_IMODE(home_info.st_mode) != 0o700):
                raise HomeRefusal("provider home is not an ordinary owned private directory")
            if record is None:
                if home_info is not None:
                    raise HomeRefusal("existing provider home has no identity record")
                record = {"schema": SCHEMA, "identity": bound,
                          "created_at": now or datetime.now(timezone.utc).isoformat(),
                          "holder": attempt_id, "state": "preparing"}
                _write(fd, record)
            else:
                if (type(record) is not dict or set(record) != {"schema", "identity", "created_at", "holder", "state"}
                        or record["schema"] != SCHEMA or record["identity"] != bound
                        or record["state"] not in ("preparing", "ready")
                        or type(record["holder"]) is not str or not record["holder"]):
                    raise HomeRefusal("provider home identity record disagrees")
                if home_info is None and record["state"] == "ready":
                    raise HomeRefusal("retained provider home is absent")
                if record["holder"] != attempt_id:
                    evidence = previous_runtime(record["holder"]) if previous_runtime else None
                    if not ceased(evidence, record["holder"]):
                        raise HomePending("previous provider home holder's runtime cessation is unproved")
                    record = dict(record, holder=attempt_id)
                    _write(fd, record)
            if home_info is None:
                os.mkdir("home", 0o700, dir_fd=fd)
                os.fsync(fd)
            if record["state"] == "preparing":
                _write(fd, dict(record, state="ready"))
            return {"home": str(place / "home"), "target": TARGET,
                    "identity": bound, "holder": attempt_id, "retained": True}
        finally:
            os.close(lock)


class HomeMount:
    """Revalidatable typed mount: derived identity, never an arbitrary path."""
    def __init__(self, root, *, authority_uuid, job_id, worker_id, attempt_id,
                 excluded=()):
        self.root = check_placement(root, excluded)
        self.identity = identity(authority_uuid, job_id, worker_id)
        self.attempt_id = attempt_id
        self.excluded = tuple(excluded)
        self._pins = None
        self.boundary()

    def boundary(self):
        check_placement(self.root, self.excluded)
        place = location(self.root, self.identity)
        with _directory(place) as fd:
            _private(fd)
            record = _read(fd)
            if (record is None or record.get("schema") != SCHEMA
                    or record.get("identity") != self.identity
                    or record.get("holder") != self.attempt_id
                    or record.get("state") != "ready"):
                raise HomeRefusal("provider home mount has no matching holder")
            home = os.open("home", os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                           dir_fd=fd)
            try:
                _private(home)
                parent_info, home_info = os.fstat(fd), os.fstat(home)
                pins = (parent_info.st_dev, parent_info.st_ino, home_info.st_dev, home_info.st_ino)
                if self._pins is not None and pins != self._pins:
                    raise HomeRefusal("provider home mount was replaced")
                self._pins = pins
            finally:
                os.close(home)
        return str(place / "home"), TARGET, True


    def initialize_credential(self, credential_path, initialize):
        """Only the current holder may initialize; the receipt is not mounted."""
        home, unused, writable = self.boundary()
        return initialize_credential(home, str(location(self.root, self.identity)),
                                     credential_path, initialize, validate=self.boundary)


def initialize_credential(home, state_directory, credential_path, initialize, *, validate=lambda: None):
    """Run a seed callback once, under durable intent; return None on restart.

    The caller owns the private state directory outside the mounted home and
    exclusion from live writers. No credential content is inspected here.
    Interrupted initialization requires recovery, including after a completed
    copy but before its external receipt. Never infer permission from absence.
    """
    from ..provider_policy.home import credential_state
    with _directory(state_directory) as fd:
        _private(fd)
        fcntl.flock(fd, fcntl.LOCK_EX)
        validate()
        record = _read(fd, "credential.json")
        expected = {"schema": "baton.home-credential/1", "path": credential_path, "state": "ready"}
        if record is not None:
            if record != expected or credential_state(home, credential_path) != "ready":
                raise HomeRefusal("credential recovery required: retained initialization evidence disagrees")
            return None
        if credential_state(home, credential_path) != "empty":
            raise HomeRefusal("credential recovery required: external initialization receipt is absent")
        _write(fd, dict(expected, state="initializing"), "credential.json")
        result = initialize()
        if credential_state(home, credential_path) != "ready":
            raise HomeRefusal("credential recovery required: initialization did not complete")
        _write(fd, expected, "credential.json")
        return result


def status_of(root, bound):
    """Content-free read; missing or damaged custody is unknown, never repaired."""
    answer = {"worker_id": bound["worker_id"], "holder": None, "state": "unknown"}
    if root is None:
        return answer
    try:
        with _directory(location(root, bound)) as fd:
            _private(fd)
            record = _read(fd)
        if (type(record) is dict and record.get("schema") == SCHEMA and record.get("identity") == bound
                and record.get("state") == "ready" and type(record.get("holder")) is str):
            answer.update(holder=record["holder"], state="retained (fresh invocation)")
    except (OSError, HomeRefusal):
        pass
    return answer
