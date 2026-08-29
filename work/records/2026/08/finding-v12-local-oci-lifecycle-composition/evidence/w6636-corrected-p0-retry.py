"""W6636 review reproduction, re-run against the CORRECTION.

This is the reviewer's own `w6636-review-p0-retry.py` with the assertions the
required corrections invert, and nothing else. Their file is kept exactly as
produced.

Run from v12/python with:

    env PYTHONPATH=src:. python3 -B ../../work/records/2026/08/finding-v12-local-oci-lifecycle-composition/evidence/w6636-corrected-p0-retry.py

WHY IT CANNOT BE RUN UNCHANGED. Their file asserts the two defects as
expectations: `destroyed_with == []` on the cleanup retry, and
`execution_runtime == "start-requested"` after a failed reconciliation. Both
are what the corrections remove, so their script raises where it asserted.

WHAT IS MEASURED IS UNCHANGED, and both measurements are about a manager that
stops half way:

  a pending cleanup must RE-ENTER provider teardown rather than skip the
  adapter because the runtime axis already moved; and

  every exit from refused-start settlement must leave an ENDING rather than
  the `start-requested` the settlement exists to remove.

The extra probes are the parts the two named cases do not reach on their own:
the adapter CALL COUNT across three rounds, which is what the submitted retry
case failed to assert and is exactly why it passed through the bypass; and the
capability and fault boundaries, which reach the same stranded state by paths
that are not refusals from `adapter.start`.

Exit 0 means every one holds.
"""

from baton_v12.contracts import ContractRefusal
from baton_v12.worker_manager import (authorize_cleanup, observe,
                                      request_runtime_start)
from tests.manager.test_attempts import (
    ATTEMPT,
    Adapter,
    TheRuntimeStateIsObservedAndNeverInferred,
)
from tests.manager.test_intake import (Custodian, RETENTION,
                                       TheDeliveryProvidersMustEndBeforeCleanupIsClean)


# EVERY PROVIDER ANSWERS ON EVERY DESTROY. The member contract is closed --
# an omission is refused rather than read as "no such provider" -- so an
# attempt with no credential says `not-delivered` out loud.
NO_CREDENTIAL = {"lifecycle_state": "not-delivered"}
STUCK = {"state": "absent", "why": "gone",
         "credentials": NO_CREDENTIAL,
         "launch": {"lifecycle_state": "unresolved",
                    "why": "the launch root is still present"}}
DONE = {"state": "absent", "why": "gone",
        "credentials": NO_CREDENTIAL,
        "launch": {"lifecycle_state": "torn-down"}}


def cleanup_case():
    case = TheDeliveryProvidersMustEndBeforeCleanupIsClean(
        methodName="test_a_destroyed_runtime_is_still_asked_about")
    case.setUp()
    return case


def start_case():
    case = TheRuntimeStateIsObservedAndNeverInferred(
        methodName="test_the_four_observations_stay_four_answers")
    case.setUp()
    return case


def a_pending_cleanup_re_enters_provider_teardown():
    """THE ADAPTER CALL COUNT IS THE MEASUREMENT.

    The first destroy truthfully moves `execution_runtime` to `destroyed`
    while the launch provider reports `unresolved`. `_destroyed` used to
    short-circuit on that axis and answer a synthetic `absent` with NO
    provider endings -- and the endings are optional, so the retry recorded
    `complete` having asked nobody anything.
    """
    case = cleanup_case()
    try:
        case.retained_ready("discard-after-intake")
        case.ended()
        calls = []
        for _round in (1, 2):
            adapter = Custodian(destroyed=dict(STUCK))
            answer = authorize_cleanup(case.store, case.port, adapter,
                                       attempt_id=ATTEMPT,
                                       retention_policy_digest=RETENTION)
            calls.append(len(adapter.destroyed_with))
            assert "cleanup" not in answer, answer
            assert case.attempt_axis("execution_runtime") == "destroyed"
            assert case.attempt_axis("cleanup") == "pending"
        print("provider retry adapter calls per round:", calls)
        assert calls == [1, 1], "a pending cleanup skipped the teardown"

        finished = Custodian(destroyed=dict(DONE))
        settled = authorize_cleanup(case.store, case.port, finished,
                                    attempt_id=ATTEMPT,
                                    retention_policy_digest=RETENTION)
        print("third round ->", settled["cleanup"],
              "after", len(finished.destroyed_with), "call")
        assert len(finished.destroyed_with) == 1
        assert settled["cleanup"] == "complete"
        assert case.attempt_axis("cleanup") == "complete"
        return True
    finally:
        case.doCleanups()


def a_destroyed_runtime_is_still_asked_about():
    """The narrow fact underneath it. An identity the engine no longer has is
    safe to ask about: `destroy` is `rm --force` then an inspection, and a
    gone identity answers `absent`."""
    case = cleanup_case()
    try:
        case.retained_ready("discard-after-intake")
        case.ended()
        observe(case.store, attempt_id=ATTEMPT, axis="execution_runtime",
                value="destroyed")
        adapter = Custodian()
        authorize_cleanup(case.store, case.port, adapter, attempt_id=ATTEMPT,
                          retention_policy_digest=RETENTION)
        print("already-destroyed runtime, adapter calls:",
              len(adapter.destroyed_with))
        assert len(adapter.destroyed_with) == 1
        return True
    finally:
        case.doCleanups()


def refused(case, failure=None):
    inputs, _given, _assignment = case.delivered()
    adapter = Adapter()
    adapter.start_failure = failure or ContractRefusal(
        "policy", "denied", "the engine refused to start this runtime")
    return adapter, inputs


def every_exit_from_a_failed_start_leaves_an_ending():
    """Three ways to reach the settlement knowing nothing, and none of them
    may leave `start-requested`."""
    walked = {}

    class Blind(Adapter):
        def list(self, operands):
            raise ContractRefusal("unavailable", "transport",
                                  "the engine could not be reached")

    class Narrow(Adapter):
        list = None

    for name, build in (
            ("listing unavailable", Blind),
            ("list capability absent", Narrow),
            ("start faults rather than refuses", None)):
        case = start_case()
        try:
            if build is None:
                _adapter, inputs = refused(
                    case, RuntimeError("the driver fell over"))
                broken = Adapter()
                broken.start_failure = RuntimeError("the driver fell over")
                broken.listing = []
                expected = RuntimeError
            else:
                template, inputs = refused(case)
                broken = build()
                broken.start_failure = template.start_failure
                expected = ContractRefusal
            try:
                request_runtime_start(case.store, broken, attempt_id=ATTEMPT,
                                      inputs=inputs)
            except expected:
                pass
            else:
                raise AssertionError(f"{name}: nothing was raised")
            axis = case.row()["execution_runtime"]
            walked[name] = axis
            assert axis != "start-requested", (name, axis)
            assert axis == "uncertain", (name, axis)
        finally:
            case.doCleanups()
    print("failed-start endings:", walked)
    return True


def a_settlement_never_overwrites_a_truer_observation():
    """`uncertain` is written ONLY from `start-requested`. Closing one hole
    must not open the opposite one."""
    case = start_case()
    try:
        adapter, inputs = refused(case)
        adapter.listing = [{"runtime_id": adapter.runtime_id,
                            "labels": case.labels()}]
        try:
            request_runtime_start(case.store, adapter, attempt_id=ATTEMPT,
                                  inputs=inputs)
        except ContractRefusal:
            pass
        row = case.row()
        print("a runtime the failed start created ->",
              row["execution_runtime"], row["runtime_id"])
        assert row["execution_runtime"] == "running"
        assert row["runtime_id"] == adapter.runtime_id
        return True
    finally:
        case.doCleanups()


if __name__ == "__main__":
    ok = [a_pending_cleanup_re_enters_provider_teardown(),
          a_destroyed_runtime_is_still_asked_about(),
          every_exit_from_a_failed_start_leaves_an_ending(),
          a_settlement_never_overwrites_a_truer_observation()]
    print("OK" if all(ok) else "UNSAFE")
    raise SystemExit(0 if all(ok) else 1)
