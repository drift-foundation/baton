"""Reviewer reproduction: missing launch refusal strands credentials.

Run from ``v12/python`` with ``PYTHONPATH=src``.  This uses the canonical OCI
start seam with a materialized credential delivery and no launch delivery.
"""

import os
import shutil
import tempfile

from baton_v12.contracts import ContractRefusal, live_secret
from baton_v12.worker_manager import credentials, documents, oci

BEARER = "w26291-review-bearer-that-must-remain-tracked"
UUID = "0123456789abcdef0123456789abcdef"
WORK = f"{UUID[:8]}-W1"
PROFILE_DIGEST = "sha256:" + "a" * 64
POLICY_DIGEST = "sha256:" + "c" * 64
ADAPTER_DIGEST = "sha256:" + "d" * 64
IDENTITY = {
    "image_digest": "sha256:" + "b" * 64,
    "profile_digest": PROFILE_DIGEST,
    "policy_digest": POLICY_DIGEST,
    "adapter_digest": ADAPTER_DIGEST,
}


def main():
    storage = tempfile.mkdtemp(prefix="w26291-review-")
    home = credentials.CredentialHome(storage)
    delivery = None
    reached = []
    try:
        inputs = os.path.join(storage, "inputs")
        workspace = os.path.join(storage, "workspace")
        os.makedirs(inputs)
        os.makedirs(workspace)
        delivery = home.materialize(
            credentials.resolved_delivery(
                ("api",),
                profile={"api": {"provider": "vault",
                                  "reference": "kv/one"}}),
            attempt_id="attempt-1",
            credential_provider=lambda provider, reference: BEARER)

        def engine(argv):
            reached.append(tuple(argv))
            return {"status": 0, "stdout": "", "stderr": ""}

        adapter = oci.OciAdapter(
            "docker", engine, identity=IDENTITY,
            assignment_roots={"inputs": inputs, "workspace": workspace},
            posture="execution", credential_delivery=delivery,
            launch_delivery=None)
        labels = documents.runtime_labels(
            runtime_attempt_id="attempt-1", authority_uuid=UUID,
            work_id=WORK, participant="baton.claude", generation=1,
            profile_digest=PROFILE_DIGEST, policy_digest=POLICY_DIGEST,
            adapter_digest=ADAPTER_DIGEST)
        try:
            adapter.start({"labels": labels, "operation_id": "op-1"})
        except ContractRefusal as refusal:
            print(f"refusal={refusal.category}/{refusal.code}")
        else:
            raise AssertionError("a start without a launch document ran")
        print(f"engine_calls={len(reached)}")
        print(f"credential_root_present={os.path.lexists(delivery.root)}")
        print(f"bearer_live={live_secret(BEARER)}")
    finally:
        if delivery is not None and os.path.lexists(delivery.root):
            home.tear_down(delivery)
        shutil.rmtree(storage, ignore_errors=True)


if __name__ == "__main__":
    main()
