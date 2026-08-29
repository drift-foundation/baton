"""W6636 re-review: a fault-created runtime is left unnamed.

Run from ``v12/python`` with::

    PYTHONPATH=src:. python3 -B ../../work/records/2026/08/finding-v12-local-oci-lifecycle-composition/evidence/w6636-review-fault-created-runtime.py

Exit zero means the adapter fault was re-raised after recording ``uncertain``
without reconciling and attaching the runtime the failed start created.
"""

from baton_v12.worker_manager import request_runtime_start
from tests.manager.test_attempts import (
    ATTEMPT, Adapter, ARefusedStartIsSettledRatherThanStranded)


def main():
    case = ARefusedStartIsSettledRatherThanStranded("runTest")
    case.setUp()
    try:
        inputs, _given, _assignment = case.delivered()
        adapter = Adapter()
        adapter.start_failure = RuntimeError(
            "the driver failed after creating the runtime")
        adapter.listing = [{"runtime_id": "runtime-1",
                            "labels": case.labels()}]
        try:
            request_runtime_start(case.store, adapter, attempt_id=ATTEMPT,
                                  inputs=inputs)
        except RuntimeError as fault:
            print("start fault:", fault)
        else:
            raise AssertionError("the adapter fault did not cross")
        row = case.row()
        assert adapter.observed == [], adapter.observed
        assert row["runtime_id"] is None, row
        assert row["execution_runtime"] == "uncertain", row
        print("exact observations:", len(adapter.observed))
        print("durable runtime id:", row["runtime_id"])
        print("durable runtime axis:", row["execution_runtime"])
        print("REPRODUCED")
        return 0
    finally:
        case.doCleanups()


if __name__ == "__main__":
    raise SystemExit(main())
