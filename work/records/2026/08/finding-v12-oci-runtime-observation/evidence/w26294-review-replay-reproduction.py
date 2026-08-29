"""Reproduce W26294's effectively-once attachment explanation replay.

Run from v12/python with:

    env PYTHONPATH=src:. python3 -B ../../work/records/2026/08/finding-v12-oci-runtime-observation/evidence/w26294-review-replay-reproduction.py

The current correction refreshes ``observed`` after replaying the original
``runtime.attached`` document, but does not rebuild its optional ``why``.
"""

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


def reason_missing_after_running_becomes_uncertain():
    case = fresh_case()
    try:
        inputs, _given, _assignment = case.delivered()
        adapter = Adapter()
        request_runtime_start(case.store, adapter, attempt_id=ATTEMPT,
                              inputs=inputs)
        adapter.observation = ContractRefusal(
            "unavailable", "transport", "the current observer failed")
        answer = reconcile_runtime(case.store, adapter, attempt_id=ATTEMPT)
        print("running -> uncertain:", answer)
        assert answer["observed"] == "uncertain"
        assert "why" not in answer
    finally:
        case.tearDown()


def stale_reason_after_uncertain_becomes_running():
    case = fresh_case()
    try:
        inputs, _given, _assignment = case.delivered()
        adapter = Adapter()
        adapter.observation = ContractRefusal(
            "unavailable", "transport", "the original observer failed")
        first = request_runtime_start(case.store, adapter, attempt_id=ATTEMPT,
                                      inputs=inputs)
        assert first["observed"] == "uncertain" and "why" in first
        adapter.observation = {"state": "running", "why": "it is up",
                               "mounts": None}
        answer = reconcile_runtime(case.store, adapter, attempt_id=ATTEMPT)
        print("uncertain -> running:", answer)
        assert answer["observed"] == "running"
        assert "why" in answer
    finally:
        case.tearDown()


if __name__ == "__main__":
    reason_missing_after_running_becomes_uncertain()
    stale_reason_after_uncertain_becomes_running()
