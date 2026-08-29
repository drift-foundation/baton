"""W6636: the shared destroy/settlement crossing, against a REAL engine.

Run from v12/python with:

    env PYTHONPATH=src:. python3 -B ../../work/records/2026/08/finding-v12-local-oci-lifecycle-composition/evidence/w6636-settlement-crossing-probe.py

WHY A PROBE RATHER THAN A CASE. The manager reaches `_destroyed` only after an
intake receipt exists, which needs freeze and collect -- the arc this round did
not compose. What this establishes is narrower and is exactly what the unit
doubles cannot: that the document a REAL `OciAdapter.destroy` produces against
a REAL daemon is the document the corrected `intake` contract accepts.

The defect it measures is not the one the dossier pinned. The dossier said the
manager "never evaluates the two provider endings". It could not: the contract
for the destroy answer did not NAME them, and `boundaries.document` refuses an
unrecognised member rather than ignoring it -- so `authorize_cleanup` against
the real adapter refused outright, one layer above the defect described.

Exit 0 means the real adapter's answer is admitted and read.
"""

import os
import subprocess
import sys
import tempfile
import uuid

from baton_v12.contracts import ContractRefusal
from baton_v12.worker_manager import boundaries, intake, launch
from baton_v12.worker_manager.oci import EnginePort, OciAdapter

ENGINE = "docker"
MARK = "baton-w6636-probe-" + uuid.uuid4().hex[:8]


def spawn(argv):
    done = subprocess.run(argv, capture_output=True, text=True, timeout=120)
    return {"status": done.returncode, "stdout": done.stdout,
            "stderr": done.stderr}


def digest_of(text):
    return "sha256:" + ("%064x" % (abs(hash(text)) % (1 << 256)))[:64]


def main():
    reachable = spawn([ENGINE, "info"])
    if reachable["status"] != 0:
        # LOUD ABOUT WHY, because the reviewer hit exactly this and could not
        # tell the two apart: a managed shell that denies the nested socket
        # and a host with no daemon produce the same exit code and very
        # different conclusions. It still FAILS rather than skips -- a
        # required integration that quietly passes because it could not run is
        # the failure mode this campaign is built against -- but the engine's
        # own sentence is on screen to say which happened.
        print("FAIL: this process cannot reach the", ENGINE, "daemon.")
        print("  argv  :", " ".join([ENGINE, "info"]))
        print("  status:", reachable["status"])
        print("  stderr:", reachable["stderr"].strip()[:500] or "(empty)")
        print("  If a standalone `docker info` works and this does not, the")
        print("  boundary is this invocation's, not the host's.")
        return 1
    home = tempfile.mkdtemp(prefix="w6636-probe-")
    roots = {}
    for name in ("inputs", "workspace"):
        roots[name] = os.path.join(home, name)
        os.makedirs(roots[name])
    attempt = "attempt-" + uuid.uuid4().hex[:8]
    delivery = launch.materialize(
        os.path.join(home, "launch"), attempt_id=attempt,
        session="session-" + attempt,
        contract="compose the local OCI lifecycle", role="impl")
    adapter = OciAdapter(
        ENGINE, EnginePort(spawn),
        identity={"image_digest": "sha256:" + "0" * 64,
                  "profile_digest": digest_of("profile"),
                  "policy_digest": digest_of("policy"),
                  "adapter_digest": digest_of("adapter")},
        assignment_roots=dict(roots), posture="execution",
        launch_delivery=delivery)

    # A runtime identity the daemon really does not have. `destroy` runs
    # `rm --force` and then INSPECTS the exact identity, so absence here is the
    # engine's own sentence rather than a zero exit status.
    answer = adapter.destroy({
        "assignment_ref": {"authority_uuid": "0" * 32, "work_id": "x-W1",
                           "participant": "baton.claude", "generation": 1},
        "runtime_attempt_id": attempt,
        "runtime_id": MARK,
        "intake_receipt_digest": digest_of("receipt"),
        "retention_policy_digest": digest_of("retention")})
    print("real adapter answer members:", sorted(answer))
    print("  runtime state:", answer["state"])
    print("  credentials  :", answer["credentials"])
    print("  launch       :", answer["launch"])

    # 1. THE CONTRACT ADMITS IT. This is the line that refused before, and the
    #    contract is READ FROM THE MANAGER rather than restated here -- a probe
    #    that spells out the members it hopes for proves only that it can spell
    #    them, which is what the first version of this file did.
    #    The fallback is the PRE-FIX contract exactly as `_destroyed` spelled
    #    it inline, so this file run against the tree before the correction
    #    shows the refusal itself rather than a missing constant.
    required, optional = getattr(
        intake, "_DESTROY_MEMBERS", (("runtime_id", "state", "why"), ()))
    try:
        taken = boundaries.document(
            answer, "a destroy observation",
            required=required, optional=optional)
    except ContractRefusal as refusal:
        print("FAIL: the real adapter's answer is still refused:",
              refusal.message[:200])
        return 1

    # 2. AND THE MANAGER READS IT. Each ending is owned where it arrives and
    #    recognised as one of the three this build reads.
    for provider in ("credentials", "launch"):
        state = intake._provider_ending(taken[provider], provider)
        assert state in intake._PROVIDER_ENDINGS, state
    print("both endings owned and recognised")

    # 3. AND AN UNRESOLVED ROOT IS WHAT KEEPS CLEANUP OPEN. The launch root was
    #    torn down here because absence was proved, so this drives the other
    #    direction on the real document rather than on a hand-written one.
    assert intake._unsettled_providers(taken) == [], taken
    stuck = dict(taken, launch={"lifecycle_state": "unresolved",
                                "why": "the launch root is still present"})
    waiting = intake._unsettled_providers(stuck)
    assert waiting and "launch" in waiting[0], waiting
    print("an unresolved root is reported as waiting:", waiting)

    # 4. AND THE ROOT REALLY IS GONE, which is what `torn-down` claims.
    if answer["state"] == "absent":
        assert answer["launch"]["lifecycle_state"] == "torn-down", answer
        assert not os.path.exists(delivery.root), delivery.root
        print("launch root removed from disk:", delivery.root)
    print("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
