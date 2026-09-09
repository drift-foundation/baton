"""Only public store entry points, against disposable probe-owned files."""
import json
import os
from pathlib import Path
import tempfile

from baton_v12.authority import Authority
from baton_v12.integration import IntegrationStore, entries_of

answer = {"euid": os.geteuid()}
with tempfile.TemporaryDirectory(prefix="w122060-read-open-") as root:
    answer["disposable_root"] = root
    authority_path = os.path.join(root, "authority.db")
    identity = "0000000a000000000000000000000000"
    owner = Authority.create(authority_path, authority_uuid=identity)
    owner.dispose()
    os.chmod(authority_path, 0o444)
    os.chmod(root, 0o555)
    try:
        try:
            reader = Authority.open(authority_path, expected_authority_uuid=identity)
        except Exception as error:
            answer["authority_readonly_open"] = {"exception": type(error).__name__, "message": str(error)}
        else:
            answer["authority_readonly_open"] = {"opened": True, "authority_uuid": reader.authority_uuid}
            reader.dispose()
    finally:
        os.chmod(root, 0o755)
        os.chmod(authority_path, 0o644)
    coordinator_path = os.path.join(root, "coordinator.db")
    answer["coordinator_existed_before_open"] = os.path.exists(coordinator_path)
    coordinator = IntegrationStore.open(coordinator_path, incarnation="read-open-probe", clock=lambda: "2026-09-09T00:00:00.000Z")
    try:
        answer["coordinator_exists_after_open"] = os.path.exists(coordinator_path)
        answer["coordinator_bytes_after_open"] = os.path.getsize(coordinator_path)
        answer["public_entries"] = entries_of(coordinator, "target-1")
    finally:
        coordinator.close()
Path(__file__).with_name("probe.json").write_text(json.dumps(answer, indent=2) + "\n")
print(json.dumps(answer, indent=2))
