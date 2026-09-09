"""What actually happens to the sidecars in the reviewer's race case?"""
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

from baton_v12.authority import Authority
from baton_v12.authority import store

UUID = "0123456789abcdef0123456789abcdef"


def identities(path):
    held = {}
    for one in ("-wal", "-shm"):
        try:
            status = os.lstat(path + one)
        except OSError:
            continue
        held[one] = [status.st_dev, status.st_ino, status.st_size]
    return held


with tempfile.TemporaryDirectory(prefix="w126880-race-") as root:
    path = str(Path(root) / "authority.sqlite3")
    serving = Authority.create(path, authority_uuid=UUID)
    seen = {"at_create": identities(path)}
    real_connect = store.sqlite3.connect

    def connect(*arguments, **operands):
        seen["before_dispose"] = identities(path)
        serving.dispose()
        seen["after_dispose"] = identities(path)
        answer = real_connect(*arguments, **operands)
        seen["after_connect"] = identities(path)
        return answer

    with patch.object(store.sqlite3, "connect", side_effect=connect):
        reader = Authority.open_readonly(path, expected_authority_uuid=UUID)
    seen["after_open"] = identities(path)
    reader.dispose()
    seen["after_dispose_reader"] = identities(path)
    print(json.dumps(seen, indent=2))
