"""W6636 re-review reproductions, re-run against the CORRECTIONS.

These are the reviewer's own `w6636-review-provider-omission.py` and
`w6636-review-fault-created-runtime.py` with the assertions the required
corrections invert, and nothing else. Their files are kept exactly as produced.

Run from v12/python with:

    env PYTHONPATH=src:. python3 -B ../../work/records/2026/08/finding-v12-local-oci-lifecycle-composition/evidence/w6636-corrected-omission-and-fault.py

WHY THEY CANNOT BE RUN UNCHANGED. Their files assert the two defects as
expectations: a cleanup that settles `complete` from an answer that OMITS a
provider whose last known ending was `unresolved`, and a start fault that
records `uncertain` with no runtime identity while `list` and `observe` would
have named the runtime immediately. Both are what the corrections remove.

ONE OF THEM ALSO STOPPED REPRODUCING FOR A REASON WORTH NAMING, and it was my
doing. The first attempt at closing the contract gave the shared `Custodian`
double a `not-delivered` default for both endings -- which meant the omission
never reached the manager at all, and the reviewer's file passed while
measuring something else entirely. A double that quietly completes what a case
named is a double that hides contract violations. It now returns exactly what
a case names, and the cases that want the defaults say so.

WHAT IS MEASURED IS UNCHANGED:

  an answer that omits a provider must not settle a cleanup that a previous
  answer said was owed, across a manager restart; and

  a start that FAULTS must reconcile exactly as one that refuses, so a runtime
  the failed start created is named and reachable by the destroy crossing.

Exit 0 means every one holds.
"""

from baton_v12.contracts import ContractRefusal
from baton_v12.worker_manager import (ControlStore, authorize_cleanup,
                                      request_runtime_start)
from tests.manager.test_attempts import (
    ATTEMPT,
    Adapter,
    TheRuntimeStateIsObservedAndNeverInferred,
)
from tests.manager.test_intake import (
    Custodian, RETENTION, TheDeliveryProvidersMustEndBeforeCleanupIsClean)
from tests.manager.test_offers import NOW


NO_CREDENTIAL = {"lifecycle_state": "not-delivered"}


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


def an_omission_cannot_erase_an_unresolved_provider():
    """The reviewer's reproduction, with the restart, inverted.

    The manager cannot remember which providers are applicable without
    inventing durable state for it, so the CONTRACT says it: every provider
    answers on every destroy, and an attempt with no such provider says
    `not-delivered` out loud. An omission is then a contract violation rather
    than a silent reading.
    """
    case = cleanup_case()
    try:
        case.retained_ready("discard-after-intake")
        case.ended()
        first = authorize_cleanup(
            case.store, case.port,
            Custodian(destroyed={
                "state": "absent", "why": "the exact runtime is absent",
                "credentials": NO_CREDENTIAL,
                "launch": {"lifecycle_state": "unresolved",
                           "why": "the launch root is still present"}}),
            attempt_id=ATTEMPT, retention_policy_digest=RETENTION)
        assert "cleanup" not in first, first
        assert case.attempt_axis("cleanup") == "pending"

        # THE RESTART IS THE POINT. What survives it has to be a property of
        # the contract rather than of one process's memory.
        case.store.close()
        case.store = ControlStore.open(case.path, incarnation="manager-2",
                                       clock=lambda: NOW)
        case.addCleanup(case.store.close)

        omitting = Custodian(destroyed={
            "state": "absent", "why": "the exact runtime is still absent"})
        try:
            authorize_cleanup(case.store, case.port, omitting,
                              attempt_id=ATTEMPT,
                              retention_policy_digest=RETENTION)
        except ContractRefusal as refusal:
            print("omitted provider after restart ->", refusal.message[:90])
        else:
            raise AssertionError("the omission settled the cleanup")
        assert case.attempt_axis("cleanup") == "pending"

        settled = authorize_cleanup(
            case.store, case.port,
            Custodian(destroyed={
                "state": "absent", "why": "gone",
                "credentials": NO_CREDENTIAL,
                "launch": {"lifecycle_state": "torn-down"}}),
            attempt_id=ATTEMPT, retention_policy_digest=RETENTION)
        print("explicit terminal ending ->", settled["cleanup"])
        assert settled["cleanup"] == "complete"
        return True
    finally:
        case.doCleanups()


def a_fault_after_creation_attaches_the_exact_runtime():
    """The other reproduction, inverted.

    A fault says LESS about the start result than a typed refusal, and that
    makes exact reconciliation more necessary rather than less: the runtime
    exists, and until it is attached nothing can name it to the destroy
    crossing.
    """
    case = start_case()
    try:
        inputs, _given, _assignment = case.delivered()
        adapter = Adapter()
        adapter.start_failure = RuntimeError(
            "the driver failed after creating the runtime")
        adapter.listing = [{"runtime_id": adapter.runtime_id,
                            "labels": case.labels()}]
        try:
            request_runtime_start(case.store, adapter, attempt_id=ATTEMPT,
                                  inputs=inputs)
        except RuntimeError as fault:
            # AND THE FAULT CROSSES UNCHANGED. This manager has no account of
            # what it was; wrapping it would replace the thing that went wrong
            # with a guess about it.
            print("fault re-raised ->", fault)
        else:
            raise AssertionError("the fault was swallowed")
        row = case.row()
        print("durable runtime id:", row["runtime_id"])
        print("durable runtime axis:", row["execution_runtime"])
        print("exact observations:", adapter.observed)
        assert row["runtime_id"] == adapter.runtime_id
        assert row["execution_runtime"] == "running"
        assert adapter.observed == [adapter.runtime_id]
        return True
    finally:
        case.doCleanups()


def a_fault_nothing_can_answer_is_still_uncertain():
    """The fallback is RETAINED. Reconciling first does not mean assuming it
    succeeds."""
    case = start_case()
    try:
        inputs, _given, _assignment = case.delivered()
        adapter = Adapter()
        adapter.start_failure = RuntimeError("the driver fell over")
        adapter.listing = []
        try:
            request_runtime_start(case.store, adapter, attempt_id=ATTEMPT,
                                  inputs=inputs)
        except RuntimeError:
            pass
        row = case.row()
        print("unanswerable fault ->", row["execution_runtime"],
              row["runtime_id"])
        assert row["execution_runtime"] == "uncertain"
        assert row["runtime_id"] is None
        return True
    finally:
        case.doCleanups()


def both_kinds_of_failure_take_one_boundary():
    """A refusal and a fault differ in what they say about WHY, and not at all
    in what this manager has to do about it. Splitting them is how the fault
    path lost its reconciliation, so the two are required to reach the same
    durable row."""
    rows = {}
    for name, failure in (
            ("refusal", ContractRefusal("policy", "denied", "declined")),
            ("fault", RuntimeError("the driver fell over"))):
        case = start_case()
        try:
            inputs, _given, _assignment = case.delivered()
            adapter = Adapter()
            adapter.start_failure = failure
            adapter.listing = [{"runtime_id": adapter.runtime_id,
                                "labels": case.labels()}]
            try:
                request_runtime_start(case.store, adapter,
                                      attempt_id=ATTEMPT, inputs=inputs)
            except type(failure):
                pass
            rows[name] = (case.row()["runtime_id"],
                          case.row()["execution_runtime"])
        finally:
            case.doCleanups()
    print("one boundary ->", rows)
    assert rows["refusal"] == rows["fault"], rows
    return True


if __name__ == "__main__":
    ok = [an_omission_cannot_erase_an_unresolved_provider(),
          a_fault_after_creation_attaches_the_exact_runtime(),
          a_fault_nothing_can_answer_is_still_uncertain(),
          both_kinds_of_failure_take_one_boundary()]
    print("OK" if all(ok) else "UNSAFE")
    raise SystemExit(0 if all(ok) else 1)
