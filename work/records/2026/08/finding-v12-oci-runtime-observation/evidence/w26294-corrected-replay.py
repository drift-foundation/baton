"""W26294 re-review replay reproduction, re-run against the CORRECTION.

This is the reviewer's own `w26294-review-replay-reproduction.py` with the two
assertions the required correction inverts, and nothing else. Their file is
kept exactly as produced.

Run from v12/python with:

    env PYTHONPATH=src:. python3 -B ../../work/records/2026/08/finding-v12-oci-runtime-observation/evidence/w26294-corrected-replay.py

WHY IT CANNOT BE RUN UNCHANGED. Their file asserts the DEFECT as an
expectation: `assert "why" not in answer` after a `running` attachment is
followed by a failed observation, and `assert "why" in answer` after a failed
attachment is followed by a `running` one. Both are the stale replay stated as
a requirement, so on the corrected tree they fail -- which is the correction
landing.

WHAT IS MEASURED IS UNCHANGED, and it is the measurement that decides whether
a reader can trust the document: the reason must ride EXACTLY when the current
observation is inconclusive, in both directions, on the second pass as on the
first.

The third probe is the part the two directions do not reach on their own: the
STABLE members must survive a replay untouched while the moving ones move, so
this walks four passes over one attachment and checks the whole document each
time rather than the two members the review named.

Exit 0 means every one holds.
"""

from baton_v12.contracts import ContractRefusal
from baton_v12.worker_manager import reconcile_runtime, request_runtime_start
from tests.manager.test_attempts import (
    ATTEMPT,
    Adapter,
    TheRuntimeStateIsObservedAndNeverInferred,
)


FAILED = ContractRefusal("unavailable", "transport", "the observer failed")
RUNNING = {"state": "running", "why": "it is up", "mounts": None}
QUIESCENT = {"state": "quiescent", "why": "it exited 0", "mounts": None}


def fresh_case():
    case = TheRuntimeStateIsObservedAndNeverInferred(
        methodName="test_the_four_observations_stay_four_answers")
    case.setUp()
    return case


def a_later_failure_carries_its_own_reason():
    """First `running`, then a failed observation.

    The attachment replays the first pass's document, whose `observed` was
    `running` and which therefore carried no reason. Refreshing `observed`
    alone answered `uncertain` with nothing to explain it.
    """
    case = fresh_case()
    try:
        inputs, _given, _assignment = case.delivered()
        adapter = Adapter()
        first = request_runtime_start(case.store, adapter, attempt_id=ATTEMPT,
                                      inputs=inputs)
        assert first["observed"] == "running" and "why" not in first
        adapter.observation = FAILED
        answer = reconcile_runtime(case.store, adapter, attempt_id=ATTEMPT)
        print("running -> uncertain:", answer)
        assert answer["observed"] == "uncertain"
        assert "why" in answer, "the inconclusive answer explains nothing"
        assert "the observer failed" in answer["why"]
        return True
    finally:
        case.doCleanups()


def a_later_success_carries_no_stale_reason():
    """First a failed observation, then `running`.

    The opposite direction, and the more dangerous one: the answer said the
    runtime is UP while still carrying the prose of the failure that could not
    see it.
    """
    case = fresh_case()
    try:
        inputs, _given, _assignment = case.delivered()
        adapter = Adapter()
        adapter.observation = FAILED
        first = request_runtime_start(case.store, adapter, attempt_id=ATTEMPT,
                                      inputs=inputs)
        assert first["observed"] == "uncertain" and "why" in first
        adapter.observation = RUNNING
        answer = reconcile_runtime(case.store, adapter, attempt_id=ATTEMPT)
        print("uncertain -> running:", answer)
        assert answer["observed"] == "running"
        assert "why" not in answer, \
            "a conclusive answer carries a previous failure's reason"
        return True
    finally:
        case.doCleanups()


def the_stable_members_survive_every_replay():
    """Four passes over ONE attachment.

    The two directions above check the member that was wrong. This checks the
    whole document: the identity and the decision are what the effectively-once
    attachment is authoritative about and must NOT move, while `observed` and
    `why` must follow the current observation on every pass.
    """
    case = fresh_case()
    try:
        inputs, _given, _assignment = case.delivered()
        adapter = Adapter()
        first = request_runtime_start(case.store, adapter, attempt_id=ATTEMPT,
                                      inputs=inputs)
        fixed = first["runtime_id"]
        walked = []
        for observation, expected in ((FAILED, "uncertain"),
                                      (RUNNING, "running"),
                                      (QUIESCENT, "quiescent"),
                                      (FAILED, "uncertain")):
            adapter.observation = observation
            answer = reconcile_runtime(case.store, adapter,
                                       attempt_id=ATTEMPT)
            walked.append(answer["observed"])
            assert answer["attempt_id"] == ATTEMPT
            assert answer["decision"] == "attached"
            assert answer["runtime_id"] == fixed, \
                "the fixed identity moved"
            assert answer["observed"] == expected
            assert ("why" in answer) == (expected == "uncertain"), answer
            # And the durable axis agrees with what was answered, on every
            # pass -- the document and the record are one act.
            assert case.row()["execution_runtime"] == expected
        print("four passes ->", walked, "identity", fixed)
        return True
    finally:
        case.doCleanups()


if __name__ == "__main__":
    ok = [a_later_failure_carries_its_own_reason(),
          a_later_success_carries_no_stale_reason(),
          the_stable_members_survive_every_replay()]
    print("OK" if all(ok) else "UNSAFE")
    raise SystemExit(0 if all(ok) else 1)
