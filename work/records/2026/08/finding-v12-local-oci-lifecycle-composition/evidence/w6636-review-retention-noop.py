"""Reproduce W6636's retention no-op without requiring an OCI daemon."""

import os
import tempfile

from baton_v12.worker_manager.oci import OciAdapter


IDENTITY = {
    "image_digest": "sha256:" + "1" * 64,
    "profile_digest": "sha256:" + "2" * 64,
    "policy_digest": "sha256:" + "3" * 64,
    "adapter_digest": "sha256:" + "4" * 64,
}


with tempfile.TemporaryDirectory(prefix="w6636-retain-noop-") as home:
    inputs = os.path.join(home, "inputs")
    workspace = os.path.join(home, "workspace")
    os.makedirs(inputs)
    os.makedirs(workspace)
    adapter = OciAdapter(
        "docker", lambda _argv: None, identity=IDENTITY,
        assignment_roots={"inputs": inputs, "workspace": workspace},
        posture="execution")

    artifact = os.path.join(home, "custody", "attempt-1", "proposal")
    os.makedirs(artifact)
    payload = os.path.join(artifact, "result.txt")
    with open(payload, "wb") as writing:
        writing.write(b"bytes that discard-after-intake says not to retain\n")

    answer = adapter.retain({
        "assignment_ref": {
            "work_ref": {"authority_uuid": "authority", "work_id": "W1"},
            "participant": "team.worker", "generation": 1,
        },
        "runtime_attempt_id": "attempt-1",
        "artifact_ids": ["attempt-1:proposal"],
        "disposition": "discard-after-intake",
        "retention_policy_digest": "sha256:" + "5" * 64,
        "operation": {
            "operation_id": "output.retain:1",
            "signature_digest": "sha256:" + "6" * 64,
        },
    })

    print("adapter answer:", answer)
    print("discarded artifact still exists:", os.path.exists(payload))
    assert answer == {"delivered": True}
    assert os.path.exists(payload)
