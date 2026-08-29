"""Independent W6636 review reproductions for the resumed P0 round.

Run from ``v12/python`` with::

    PYTHONPATH=src:. python3 -B ../../work/records/2026/08/finding-v12-local-oci-lifecycle-composition/evidence/w6636-review-p0-retry.py

Exit zero means both unsafe durable states were reproduced. This is defect
evidence, not a positive acceptance probe.
"""

from baton_v12.contracts import ContractRefusal
from baton_v12.worker_manager import authorize_cleanup, request_runtime_start
from tests.manager.test_attempts import (
    ATTEMPT, Adapter, ARefusedStartIsSettledRatherThanStranded)
from tests.manager.test_intake import (
    Custodian, RETENTION, TheDeliveryProvidersMustEndBeforeCleanupIsClean)


def provider_retry_bypasses_teardown():
    case = TheDeliveryProvidersMustEndBeforeCleanupIsClean("runTest")
    case.setUp()
    try:
        case.retained_ready("discard-after-intake")
        case.ended()
        ending = {
            "state": "absent",
            "why": "the exact runtime is absent",
            "launch": {"lifecycle_state": "unresolved",
                       "why": "the launch root is still present"},
        }
        first_adapter = Custodian(destroyed=ending)
        first = authorize_cleanup(
            case.store, case.port, first_adapter, attempt_id=ATTEMPT,
            retention_policy_digest=RETENTION)
        assert "cleanup" not in first, first

        second_adapter = Custodian(destroyed=ending)
        second = authorize_cleanup(
            case.store, case.port, second_adapter, attempt_id=ATTEMPT,
            retention_policy_digest=RETENTION)
        assert second_adapter.destroyed_with == [], second_adapter.destroyed_with
        assert second["cleanup"] == "complete", second
        assert case.attempt_axis("cleanup") == "complete"
        print("provider retry adapter calls:",
              len(second_adapter.destroyed_with))
        print("provider retry cleanup:", second["cleanup"])
    finally:
        case.doCleanups()


def failed_reconciliation_leaves_start_requested():
    case = ARefusedStartIsSettledRatherThanStranded("runTest")
    case.setUp()
    try:
        source, inputs = case.refused()

        class Blind(Adapter):
            def list(self, operands):
                raise ContractRefusal(
                    "unavailable", "transport",
                    "the engine could not be reached")

        adapter = Blind()
        adapter.start_failure = source.start_failure
        try:
            request_runtime_start(case.store, adapter, attempt_id=ATTEMPT,
                                  inputs=inputs)
        except ContractRefusal as refusal:
            print("start refusal:", refusal.code)
        else:
            raise AssertionError("the refused start unexpectedly succeeded")
        row = case.row()
        assert row["execution_runtime"] == "start-requested", row
        assert row["runtime_id"] is None, row
        print("failed-reconciliation runtime axis:",
              row["execution_runtime"])
    finally:
        case.doCleanups()


if __name__ == "__main__":
    provider_retry_bypasses_teardown()
    failed_reconciliation_leaves_start_requested()
    print("REPRODUCED")
