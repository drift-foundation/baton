"""Independent W26294 reproductions for stale-running and unreachable absence."""

from baton_v12.contracts import ContractRefusal
from baton_v12.worker_manager import reconcile_runtime, request_runtime_start
from tests.manager.test_attempts import (
    ATTEMPT,
    Adapter,
    TheRuntimeStateIsObservedAndNeverInferred,
)


def fresh_case():
    case = TheRuntimeStateIsObservedAndNeverInferred(
        methodName="test_the_four_observations_stay_four_answers")
    case.setUp()
    return case


def observation_failure_leaves_stale_running():
    case = fresh_case()
    try:
        inputs, _given, _assignment = case.delivered()
        adapter = Adapter()
        request_runtime_start(case.store, adapter, attempt_id=ATTEMPT,
                              inputs=inputs)
        assert case.row()["execution_runtime"] == "running"

        adapter.observation = ContractRefusal(
            "unavailable", "transport", "the observer failed")
        try:
            reconcile_runtime(case.store, adapter, attempt_id=ATTEMPT)
        except ContractRefusal:
            pass
        else:  # pragma: no cover - this is evidence against the current tree
            raise AssertionError("the injected observation failure was lost")

        actual = case.row()["execution_runtime"]
        print("observation failure leaves execution_runtime =", actual)
        assert actual == "running"
    finally:
        case.tearDown()


def a_known_removed_runtime_is_never_observed_absent():
    case = fresh_case()
    try:
        inputs, _given, _assignment = case.delivered()
        adapter = Adapter()
        request_runtime_start(case.store, adapter, attempt_id=ATTEMPT,
                              inputs=inputs)
        assert adapter.observed == [adapter.runtime_id]

        # This is the real post-removal shape: an all-containers listing no
        # longer contains the runtime, while the attempt still records its
        # exact immutable runtime identity. The adapter could prove absence by
        # inspecting that ID, but reconciliation does not ask it.
        adapter.listing = []
        adapter.observation = {
            "state": "absent", "why": "no such runtime", "mounts": None}
        answer = reconcile_runtime(case.store, adapter, attempt_id=ATTEMPT)

        print("zero-listing decision =", answer["decision"])
        print("zero-listing execution_runtime =",
              case.row()["execution_runtime"])
        print("observe calls =", adapter.observed)
        assert answer["decision"] == "uncertain"
        assert case.row()["execution_runtime"] == "uncertain"
        assert adapter.observed == [adapter.runtime_id]
    finally:
        case.tearDown()


if __name__ == "__main__":
    observation_failure_leaves_stale_running()
    a_known_removed_runtime_is_never_observed_absent()
