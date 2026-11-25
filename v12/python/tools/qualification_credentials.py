"""Explicitly selected qualification seeding; no engine or provider execution.

The configured source is resolved only by the first-initialization callback.
Existing private homes and refreshed credentials are never replaced.
"""
import json
import os
from pathlib import Path
import stat

from baton_v12.provider_policy.home import prepare, checked_home, _parts
from baton_v12.worker_manager.provider_home import initialize_credential, HomeRefusal


def _directory(path):
    if not path.is_absolute() or path != Path(os.path.realpath(path)):
        raise ValueError("qualification directory must be absolute without symlink aliases")
    for parent in (path, *path.parents):
        if os.path.lexists(parent / ".git") or ((parent / "HEAD").exists() and (parent / "objects").is_dir()):
            raise ValueError("qualification directory must be outside every repository")


def prepare_selected(selection, source_configuration):
    """Selection is not authorization by itself; the caller verifies the ruling.

    Read only explicitly selected paths, with no ambient login discovery. The
    source configuration is a private file containing reference and path, set
    once by the selected custodian; it is not needed on a retained restart.
    """
    required = ("authorization_credential_copy", "credential_source_reference",
                "credential_path_evidence", "credential_storage_mode_evidence",
                "private_retention_and_cleanup_owner", "refresh_copy_disposition")
    if any(not isinstance(selection.get(key), str) or not selection[key] for key in required):
        raise ValueError("credential copy selection is incomplete")
    if selection.get("uid") != os.getuid() or selection.get("gid") != os.getgid() or os.getuid() == 0:
        raise ValueError("qualification setup must run as the selected non-root UID:GID")
    root = Path(selection["execution_root"])
    _directory(root)
    checked_home(str(root))
    relative = selection["codex_home_relative_to_home"] + "/" + selection["credential_relative_path"]
    _parts(relative)
    instruction = selection["instruction_relative_to_home"]
    _parts(instruction)
    if relative == instruction or relative.startswith(instruction + "/") or instruction.startswith(relative + "/"):
        raise ValueError("credential/instruction paths overlap")
    live = root / "live"
    try:
        live.mkdir(mode=0o700)
    except FileExistsError:
        checked_home(str(live))
        # A partial directory is a recovery condition, not a fresh setup.
        for name in ("home", "credential-state", "workspace", "private-output"):
            checked_home(str(live / name))
        if not (live / "credential-state" / "credential.json").exists():
            raise HomeRefusal("credential recovery required: qualification initialization receipt is absent")
    else:
        for name in ("home", "credential-state", "workspace", "private-output"):
            (live / name).mkdir(mode=0o700)
        for path in (live, root):
            fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
            try:
                os.fsync(fd)
            finally:
                os.close(fd)
    home = str(live / "home")
    def initialize():
        # This callback is never entered on a retained restart. In particular,
        # an absent source configuration or source file does not break restart.
        config = Path(source_configuration)
        if not config.is_absolute() or config != Path(os.path.realpath(config)):
            raise ValueError("source configuration must be an explicit canonical path")
        fd = os.open(config, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
        with os.fdopen(fd, "rb") as stream:
            info = os.fstat(stream.fileno())
            if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) != 0o600 or info.st_size > 16384:
                raise ValueError("source configuration must be private and bounded")
            source = json.loads(stream.read(16385))
        if set(source) != {"reference", "path"} or source["reference"] != selection["credential_source_reference"]:
            raise ValueError("source reference disagrees with selection")
        path = Path(source["path"])
        if not path.is_absolute() or path != Path(os.path.realpath(path)) or path.is_relative_to(root):
            raise ValueError("source must be an explicit external file without symlink aliases")
        info = path.lstat()
        if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) != 0o600 or info.st_size > 1048576:
            raise ValueError("selected source must be a private bounded regular file")
        prepare(home, credential_path=relative, delivered=str(path), mode="seeded-retained")
    initialize_credential(home, str(live / "credential-state"), relative, initialize)
    return {"credential_lifecycle": "ready", "home": home, "source_written": False,
            "provider_called": False, "engine_called": False}
