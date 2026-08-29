"""W6636 re-review: an omitted provider erases an unresolved ending.

Run from ``v12/python`` with::

    PYTHONPATH=src:. python3 -B ../../work/records/2026/08/finding-v12-local-oci-lifecycle-composition/evidence/w6636-review-provider-omission.py

Exit zero means the unsafe settlement was reproduced through public manager
operations, including a manager restart between the two destroy answers.
"""

from baton_v12.worker_manager import ControlStore, authorize_cleanup
from tests.manager.test_intake import (
    ATTEMPT, Custodian, RETENTION,
    TheDeliveryProvidersMustEndBeforeCleanupIsClean)
from tests.manager.test_offers import NOW


def main():
    case = TheDeliveryProvidersMustEndBeforeCleanupIsClean("runTest")
    case.setUp()
    try:
        case.retained_ready("discard-after-intake")
        case.ended()
        first = authorize_cleanup(
            case.store, case.port,
            Custodian(destroyed={
                "state": "absent",
                "why": "the exact runtime is absent",
                "launch": {"lifecycle_state": "unresolved",
                           "why": "the launch root is still present"},
            }),
            attempt_id=ATTEMPT, retention_policy_digest=RETENTION)
        assert "cleanup" not in first, first
        assert case.attempt_axis("cleanup") == "pending"

        case.store.close()
        case.store = ControlStore.open(
            case.path, incarnation="manager-2", clock=lambda: NOW)
        case.addCleanup(case.store.close)

        omitted = Custodian(destroyed={
            "state": "absent",
            "why": "the exact runtime is still absent",
        })
        second = authorize_cleanup(
            case.store, case.port, omitted, attempt_id=ATTEMPT,
            retention_policy_digest=RETENTION)
        assert len(omitted.destroyed_with) == 1, omitted.destroyed_with
        assert second["cleanup"] == "complete", second
        assert case.attempt_axis("cleanup") == "complete"
        print("retry adapter calls:", len(omitted.destroyed_with))
        print("provider member on retry: omitted")
        print("cleanup after restart:", second["cleanup"])
        print("REPRODUCED")
        return 0
    finally:
        case.doCleanups()


if __name__ == "__main__":
    raise SystemExit(main())
