"""W26294 review reproductions, re-run against the CORRECTION.

This is the reviewer's own `w26294-review-reproductions.py` with the two
assertions the required corrections inverted, and nothing else. Their file is
kept exactly as produced.

WHY IT CANNOT BE RUN UNCHANGED. The first probe asserts that the injected
observation failure PROPAGATES out of `reconcile_runtime` -- which is the
defect: a raised failure left the durable axis at whatever it said before,
including `running`. The correction makes every failed or unrecognised exact
observation a durable `uncertain`, so nothing is raised and the reviewer's
`else: raise AssertionError("the injected observation failure was lost")`
fires on correct behaviour.

The second probe asserts that a zero listing produces `uncertain` with no
second `observe` call. That is also the defect: the attempt already held the
exact immutable runtime id, and positive absence was unreachable in the
ordinary post-removal shape.

WHAT IS MEASURED IS UNCHANGED, and it is the measurement that decides safety:
after an observation failure the durable state must not be `running`, and
after a known runtime disappears from the listing the adapter must be asked
about that exact id and its answer preserved.

Exit 0 means both hold.
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


def observation_failure_is_uncertain_and_never_stale_running():
    case = fresh_case()
    try:
        inputs, _given, _assignment = case.delivered()
        adapter = Adapter()
        request_runtime_start(case.store, adapter, attempt_id=ATTEMPT,
                              inputs=inputs)
        assert case.row()["execution_runtime"] == "running"

        adapter.observation = ContractRefusal(
            "unavailable", "transport", "the observer failed")
        answer = reconcile_runtime(case.store, adapter, attempt_id=ATTEMPT)

        actual = case.row()["execution_runtime"]
        print("observation failure ->",
              f"decision={answer['decision']}",
              f"observed={answer.get('observed')}",
              f"execution_runtime={actual}")
        # THE DECISION IS ABOUT THE ATTACHMENT AND `observed` IS THE STATE,
        # which is exactly the distinction W26294 introduced: the listing
        # proved WHICH runtime this is, and the failed observation leaves WHAT
        # IT IS unknown. So `attached` beside `uncertain` is the honest pair,
        # and the durable axis is what must never still say `running`.
        assert answer["decision"] == "attached"
        assert answer.get("observed") == "uncertain"
        assert actual == "uncertain"
        assert actual != "running"
        return True
    finally:
        case.doCleanups()


def a_known_removed_runtime_is_observed_absent():
    case = fresh_case()
    try:
        inputs, _given, _assignment = case.delivered()
        adapter = Adapter()
        request_runtime_start(case.store, adapter, attempt_id=ATTEMPT,
                              inputs=inputs)
        assert adapter.observed == [adapter.runtime_id]

        # The real post-removal shape: an all-containers listing no longer
        # contains the runtime, while the attempt still records its exact
        # immutable runtime identity.
        adapter.listing = []
        adapter.observation = {
            "state": "absent", "why": "no such runtime", "mounts": None}
        answer = reconcile_runtime(case.store, adapter, attempt_id=ATTEMPT)

        print("zero listing ->",
              f"decision={answer['decision']}",
              f"observed={answer.get('observed')}",
              f"execution_runtime={case.row()['execution_runtime']}",
              f"observe_calls={adapter.observed}")
        # THE EXACT IDENTITY WAS ASKED ABOUT, which is the whole correction.
        assert adapter.observed == [adapter.runtime_id, adapter.runtime_id]
        assert answer.get("observed") == "destroyed"
        assert case.row()["execution_runtime"] == "destroyed"
        return True
    finally:
        case.doCleanups()


def an_unaskable_reconciliation_is_still_uncertain():
    """The one case that legitimately cannot ask: no identity anywhere."""
    case = fresh_case()
    try:
        case.delivered()          # the attempt exists; nothing was started
        adapter = Adapter()
        adapter.listing = []
        answer = reconcile_runtime(case.store, adapter, attempt_id=ATTEMPT)
        print("no identity ->", f"decision={answer['decision']}",
              f"execution_runtime={case.row()['execution_runtime']}",
              f"observe_calls={adapter.observed}")
        assert answer["decision"] == "uncertain"
        assert adapter.observed == []
        return True
    finally:
        case.doCleanups()


if __name__ == "__main__":
    ok = [observation_failure_is_uncertain_and_never_stale_running(),
          a_known_removed_runtime_is_observed_absent(),
          an_unaskable_reconciliation_is_still_uncertain()]
    print("OK" if all(ok) else "UNSAFE")
    raise SystemExit(0 if all(ok) else 1)
