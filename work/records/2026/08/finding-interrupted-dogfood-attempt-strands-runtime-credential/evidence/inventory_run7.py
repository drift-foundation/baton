"""Redacted run7 inventory through public v12 manager surfaces.

Run only against an offline copy of `/tmp/w51487/run7`, never the preserved
original. This script does not open either SQLite store itself and never opens,
reads, hashes or lists a credential slot. `ControlStore` is the manager's
public store boundary; the filesystem checks are presence checks for roots and
lifecycle records only.
"""

import datetime
import json
import os
import pathlib
import sys


ATTEMPT = "attempt-w51487-run7"
ORIGINAL = "/tmp/w51487/run7"


def _now():
    moment = datetime.datetime.now(datetime.timezone.utc)
    return moment.strftime("%Y-%m-%dT%H:%M:%S.") + f"{moment.microsecond // 1000:03d}Z"


def _under_copy(value, copied):
    if isinstance(value, str) and (value == ORIGINAL or value.startswith(ORIGINAL + "/")):
        return copied + value[len(ORIGINAL):]
    return value


def main(argv):
    if len(argv) != 1:
        raise SystemExit("usage: inventory_run7.py OFFLINE_RUN7_COPY")
    copied = os.path.abspath(argv[0])
    if copied == ORIGINAL or not copied.startswith("/tmp/w55758-run7-copy."):
        raise SystemExit("refusing anything but a /tmp/w55758-run7-copy.* fixture")

    repository = pathlib.Path(__file__).resolve().parents[6]
    sys.path.insert(0, str(repository / "v12/python/src"))
    from baton_v12.worker_manager import (ControlStore, frozen_output_of,
                                          intake_receipt_of, retentions_of,
                                          runtime_lane)
    from baton_v12.worker_manager.credentials import CredentialHome

    given = json.loads((pathlib.Path(copied) / "grants.json").read_text(encoding="utf-8"))
    given = {key: _under_copy(value, copied) for key, value in given.items()}
    store = ControlStore.open(given["control_store"],
                              incarnation="w55758-redacted-inventory",
                              clock=_now)
    try:
        runtime_id = json.loads(
            (pathlib.Path(copied) / "storage" / ATTEMPT / "credential-state"
             / f"{ATTEMPT}.json").read_text(encoding="utf-8"))["runtime_id"]
        attached = store.operation_record(f"attempt.attach:{ATTEMPT}:{runtime_id}")
        lane = runtime_lane(store, ATTEMPT)
        frozen = frozen_output_of(store, ATTEMPT)
        receipt = intake_receipt_of(store, ATTEMPT)
        retentions = retentions_of(store, ATTEMPT)
    finally:
        store.close()

    granted_home = CredentialHome(given["credential_home"])
    assignment_home = CredentialHome(os.path.join(given["storage"], ATTEMPT))
    granted_record = granted_home.read_state(ATTEMPT)
    assignment_record = assignment_home.read_state(ATTEMPT)
    result = {
        "attempt_id": ATTEMPT,
        "attach_operation": {
            "present": attached is not None,
            "kind": attached.get("kind") if attached else None,
            "state": attached.get("state") if attached else None,
        },
        "runtime_lane": dict(lane) if lane is not None else None,
        "frozen_output": frozen is not None,
        "intake_receipt": receipt is not None,
        "retention_count": len(retentions),
        "granted_credential_home": {
            "lifecycle_record": granted_record is not None,
            "volatile_root": os.path.exists(granted_home.volatile_root(ATTEMPT)),
        },
        "assignment_credential_home": {
            "lifecycle_record": assignment_record is not None,
            "lifecycle_state": (assignment_record or {}).get("lifecycle_state"),
            "runtime_id_matches": ((assignment_record or {}).get("runtime_id")
                                   == runtime_id),
            "volatile_root": os.path.exists(assignment_home.volatile_root(ATTEMPT)),
        },
        "worker_workspace_output": os.path.isfile(os.path.join(
            given["storage"], ATTEMPT, "workspace", "output.json")),
        "manager_evidence": os.path.isfile(os.path.join(copied, "evidence.json")),
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
