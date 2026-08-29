"""W26284 review reproductions, re-run against the CORRECTION.

This is the reviewer's own `w26284-review-reproductions.py` with ONE change
per probe, and each change is one the required correction forced rather than a
weakening of what it asked.

FIRST PROBE. The reviewer's version catches `OSError` around `materialize`,
because the old code propagated the provider's own failure after silently
forgetting every bearer. The correction makes an unprovable cleanup its own
ending -- `policy/credential-lifetime` -- so the probe now has to catch that
too. What it MEASURES is unchanged and is the whole point: with the root still
present, the bearer must still be live.

SECOND PROBE is unchanged in substance. It asserts that no argv reaching the
engine carries a live bearer, and the correction moved the §13 sweep to the
one place every vector passes through, so the count it prints is now zero.

Exit 0 means both safety properties hold.
"""


import os
import pathlib
import tempfile


ROOT = pathlib.Path(__file__).resolve().parents[6]
import sys
sys.path.insert(0, str(ROOT / "v12" / "python" / "src"))

from baton_v12.contracts import (ContractRefusal, forget_secret, live_secret)
from baton_v12.worker_manager import credentials, oci


BEARER = "w26284-review-bearer-value"
PROFILE = {
    "api": {"provider": "vault", "reference": "kv/api"},
    "signing": {"provider": "vault", "reference": "kv/signing"},
}
DIGEST = "sha256:" + "a" * 64
IDENTITY = {
    "image_digest": "sha256:" + "b" * 64,
    "profile_digest": DIGEST,
    "policy_digest": "sha256:" + "c" * 64,
    "adapter_digest": "sha256:" + "d" * 64,
}


def unresolved_materialization_cleanup(home):
    """A cleanup that cannot prove absence must retain registration."""
    holder = credentials.CredentialHome(home)
    resolution = credentials.resolved_delivery(
        ("api", "signing"), profile=PROFILE)
    original = credentials._discard
    credentials._discard = lambda root: False
    calls = 0

    def provider(_provider, _reference):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise OSError("provider failed after the first file")
        return BEARER

    try:
        try:
            holder.materialize(
                resolution, attempt_id="attempt-1",
                credential_provider=provider)
        except (OSError, ContractRefusal):
            # BOTH, because the correction turned an unprovable cleanup into
            # its own refusal. The measurement below is what decides safety.
            pass
        root = holder.volatile_root("attempt-1")
        safe = os.path.lexists(root) and live_secret(BEARER)
        print("materialization cleanup:",
              f"root_present={os.path.lexists(root)}",
              f"bearer_live={live_secret(BEARER)}")
        return safe
    finally:
        credentials._discard = original
        original(holder.volatile_root("attempt-1"))
        while live_secret(BEARER):
            forget_secret(BEARER)


def candidate_label_before_sweep(home):
    """No engine command may receive a live bearer before the §13 sweep."""
    inputs = os.path.join(home, "inputs")
    workspace = os.path.join(home, "workspace")
    os.makedirs(inputs)
    os.makedirs(workspace)
    holder = credentials.CredentialHome(home)
    delivery = holder.materialize(
        credentials.resolved_delivery(("api",), profile=PROFILE),
        attempt_id=BEARER,
        credential_provider=lambda _provider, _reference: BEARER)
    calls = []

    class Engine:
        def __call__(self, argv):
            calls.append(tuple(argv))
            if "ps" in argv:
                return {"status": 0, "stdout": "", "stderr": ""}
            return {"status": 0, "stdout": "runtime-1\n", "stderr": ""}

    built = oci.OciAdapter(
        "docker", Engine(), identity=IDENTITY,
        assignment_roots={"inputs": inputs, "workspace": workspace},
        posture="execution", credential_delivery=delivery)
    labels = {
        "runtime_attempt_id": BEARER,
        "authority_uuid": "0123456789abcdef0123456789abcdef",
        "work_id": "01234567-W1",
        "participant": "baton.claude",
        "generation": 1,
        "profile_digest": IDENTITY["profile_digest"],
        "policy_digest": IDENTITY["policy_digest"],
        "adapter_digest": IDENTITY["adapter_digest"],
    }
    try:
        try:
            built.start({"labels": labels,
                         "operation_id": "runtime.start:review"})
        except ContractRefusal:
            pass
        leaked = [argv for argv in calls if BEARER in " ".join(argv)]
        print("pre-sweep engine calls:", len(calls),
              "calls containing bearer:", len(leaked))
        return not leaked
    finally:
        if os.path.lexists(delivery.root):
            credentials._discard(delivery.root)
        while live_secret(BEARER):
            forget_secret(BEARER)


def main():
    with tempfile.TemporaryDirectory(prefix="w26284-review-") as home:
        first = unresolved_materialization_cleanup(os.path.join(home, "one"))
        os.makedirs(os.path.join(home, "two"))
        second = candidate_label_before_sweep(os.path.join(home, "two"))
    if first and second:
        print("OK")
        return 0
    print("UNSAFE")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
