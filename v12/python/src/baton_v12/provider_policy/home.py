"""Worker-side home preparation. Never copies provider state outward."""
import hashlib
import os
from pathlib import PurePosixPath
import stat
import uuid

from . import PolicyRefusal


def _parts(path):
    if type(path) is not str or not path or path.startswith("/"):
        raise PolicyRefusal("provider-owned paths must be relative")
    parts = path.split("/")
    if any(part in ("", ".", "..") for part in parts):
        raise PolicyRefusal("provider-owned path is not canonical")
    return parts


def _open_home(path):
    if not os.path.isabs(path) or os.path.normpath(path) != path:
        raise PolicyRefusal("provider home must be absolute and canonical")
    fd = os.open("/", os.O_RDONLY | os.O_DIRECTORY)
    try:
        for part in PurePosixPath(path).parts[1:]:
            below = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
            os.close(fd)
            fd = below
        state = os.fstat(fd)
        if state.st_uid != os.getuid() or stat.S_IMODE(state.st_mode) != 0o700:
            raise PolicyRefusal("provider home ownership or permissions disagree")
        return fd
    except BaseException:
        os.close(fd)
        raise


def checked_home(path):
    fd = _open_home(path)
    os.close(fd)
    return path


def _parent(fd, parts):
    here = os.dup(fd)
    try:
        for part in parts[:-1]:
            try:
                os.mkdir(part, 0o700, dir_fd=here)
                os.fsync(here)
            except FileExistsError:
                pass
            below = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=here)
            os.close(here)
            here = below
            state = os.fstat(here)
            if state.st_uid != os.getuid() or stat.S_IMODE(state.st_mode) != 0o700:
                raise PolicyRefusal("provider home child is not private")
        return here
    except BaseException:
        os.close(here)
        raise


def _overlap(left, right):
    return left == right or left.startswith(right + "/") or right.startswith(left + "/")


def prepare(path, *, credential_path, delivered, mode, managed=(), provider_paths=()):
    """Prepare one already held home using exact adapter-owned paths.

    Managed tuples are (relative path, bytes, sha256). Production selects none
    until instruction delivery is approved. Existing seeded credentials are
    never opened, compared or replaced, including when the delivery changes.
    """
    parts = _parts(credential_path)
    if mode not in ("delivered", "seeded-retained"):
        raise PolicyRefusal("unsupported provider credential mode")
    names = []
    for name, payload, expected in managed:
        _parts(name)
        if (type(payload) is not bytes or "sha256:" + hashlib.sha256(payload).hexdigest() != expected
                or any(_overlap(name, other) for other in [credential_path, *provider_paths, *names])):
            raise PolicyRefusal("managed entry digest or ownership conflicts")
        names.append(name)
    fd = _open_home(path)
    try:
        parent = _parent(fd, parts)
        try:
            leaf = parts[-1]
            try:
                state = os.stat(leaf, dir_fd=parent, follow_symlinks=False)
            except FileNotFoundError:
                state = None
            if mode == "delivered":
                if not os.path.isabs(delivered) or not os.access(delivered, os.R_OK):
                    raise PolicyRefusal("delivered credential is absent or unreadable")
                if state is None:
                    os.symlink(delivered, leaf, dir_fd=parent)
                    os.fsync(parent)
                elif not stat.S_ISLNK(state.st_mode) or os.readlink(leaf, dir_fd=parent) != delivered:
                    raise PolicyRefusal("delivered credential reference disagrees")
            elif state is not None:
                if not stat.S_ISREG(state.st_mode) or state.st_uid != os.getuid() or stat.S_IMODE(state.st_mode) & 0o077:
                    raise PolicyRefusal("retained credential is not an owned private regular file")
            else:
                seed = os.open(delivered, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
                temporary = ".seed-" + uuid.uuid4().hex
                target = None
                try:
                    if not stat.S_ISREG(os.fstat(seed).st_mode):
                        raise PolicyRefusal("credential seed is not a regular file")
                    target = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=parent)
                    while chunk := os.read(seed, 65536):
                        view = memoryview(chunk)
                        while view:
                            count = os.write(target, view)
                            if count <= 0:
                                raise OSError("credential seed write made no progress")
                            view = view[count:]
                    os.fsync(target)
                    # No replacing even if a competing entry appeared.
                    os.link(temporary, leaf, src_dir_fd=parent, dst_dir_fd=parent, follow_symlinks=False)
                    os.fsync(parent)
                finally:
                    os.close(seed)
                    if target is not None:
                        os.close(target)
                    try:
                        os.unlink(temporary, dir_fd=parent)
                        os.fsync(parent)
                    except FileNotFoundError:
                        pass
        finally:
            os.close(parent)
        for name, payload, unused in managed:
            parts = _parts(name)
            parent = _parent(fd, parts)
            temporary = ".managed-" + uuid.uuid4().hex
            try:
                target = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=parent)
                with os.fdopen(target, "wb") as output:
                    output.write(payload)
                    output.flush()
                    os.fsync(output.fileno())
                os.rename(temporary, parts[-1], src_dir_fd=parent, dst_dir_fd=parent)
                os.fsync(parent)
            finally:
                try:
                    os.unlink(temporary, dir_fd=parent)
                except FileNotFoundError:
                    pass
                os.close(parent)
    finally:
        os.close(fd)
    return path
