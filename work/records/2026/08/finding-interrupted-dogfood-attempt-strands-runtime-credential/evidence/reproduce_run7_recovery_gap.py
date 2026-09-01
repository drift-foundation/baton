"""Drive the run7 restart gap against an offline copy, without engine acts.

The script uses the dogfood retry capability builder and credential component
but performs no authority transition, Docker command, output acceptance or
credential read. The copied volatile credential root is already absent.
"""

import json
import os
import pathlib
import sys


ATTEMPT = "attempt-w51487-run7"
ORIGINAL = "/tmp/w51487/run7"


def _remap(value, copied):
    if isinstance(value, str) and (value == ORIGINAL or value.startswith(ORIGINAL + "/")):
        return copied + value[len(ORIGINAL):]
    if isinstance(value, list):
        return [_remap(one, copied) for one in value]
    if isinstance(value, dict):
        return {key: _remap(one, copied) for key, one in value.items()}
    return value


def main(argv):
    if len(argv) != 1:
        raise SystemExit("usage: reproduce_run7_recovery_gap.py OFFLINE_RUN7_COPY")
    copied = os.path.abspath(argv[0])
    if copied == ORIGINAL or not copied.startswith("/tmp/w55758-run7-copy."):
        raise SystemExit("refusing anything but a /tmp/w55758-run7-copy.* fixture")

    repository = pathlib.Path(__file__).resolve().parents[6]
    sys.path.insert(0, str(repository / "v12/python/src"))
    sys.path.insert(0, str(repository / "v12/python/tools"))
    import dogfood_operator
    from baton_v12.contracts import ContractRefusal
    from baton_v12.worker_manager import ControlStore, configured_workspace_group
    from baton_v12.worker_manager.credentials import CredentialHome

    given = _remap(json.loads(
        (pathlib.Path(copied) / "grants.json").read_text(encoding="utf-8")), copied)
    assignment_home = CredentialHome(os.path.join(given["storage"], ATTEMPT))
    record = _remap(assignment_home.read_state(ATTEMPT), copied)
    runtime_id = record["runtime_id"]

    store = ControlStore.open(given["control_store"],
                              incarnation="w55758-adoption-repro",
                              clock=dogfood_operator._now)
    try:
        group = configured_workspace_group(store)
        try:
            assignment_home.adopt(record, attempt_id=ATTEMPT,
                                  runtime_id=runtime_id,
                                  workspace_group=group)
        except ContractRefusal as refused:
            adoption = {"accepted": False, "category": refused.category,
                        "code": refused.code, "message": refused.message}
        else:
            adoption = {"accepted": True}
    finally:
        store.close()

    built = dogfood_operator._for_retry({"runtime_id": runtime_id}, given)
    try:
        adapter = built["adapter"]
        retry = {
            "credential_delivery_adopted": adapter.credential_delivery is not None,
            "launch_delivery_adopted": adapter.launch_delivery is not None,
            "positive_absence_credential_ending": adapter._torn_down(
                {"state": "absent", "why": "offline fixture"})["lifecycle_state"],
        }
    finally:
        for closing in built.get("closing", ()):
            closing()

    print(json.dumps({"attempt_id": ATTEMPT,
                      "assignment_record_adoption": adoption,
                      "narrow_retry_builder": retry},
                     indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
