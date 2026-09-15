"""Manager-owned runtime deadlines (W32577, owner M33822).

The start boundary pins trusted configuration, not worker input. Reaching the
deadline is an observation; advancing a cancel policy is a separate act. All
identities and times survive restart in the existing manager journal.
"""

from types import SimpleNamespace

from ..contracts import ContractRefusal, check_no_durable_secret, digest
from . import attempts, boundaries, documents, intake
from .store import manager_signature

__all__ = ["deadline_of", "observe_deadline", "advance_deadline",
           "deadline_cleanup_of", "discharge_deadline_quiescence_gate"]

POLICY = ("policy_digest", "policy_generation", "duration_seconds", "action")
PIN = ("attempt_id", "assignment", "policy", "started_at", "deadline_at")
REACHED = ("attempt_id", "assignment", "pin_digest", "observed_at")
DESTROY = ("runtime_attempt_id", "assignment_ref", "runtime_id",
           "deadline_operation_id", "deadline_digest", "cancel_operation_id",
           "authority_operation_id", "retention_policy_digest")
PROOF = ("command", "fence", "observed", "cleanup")
DISCHARGE = ("attempt_id", "assignment", "runtime_id", "cleanup_operation",
             "operation_id", "gate", "evidence", "authority_receipt")


class _NotReached(Exception):
    """Roll back the observation transaction without journalling an early read."""


def _refuse(message, code="precondition"):
    raise ContractRefusal("refused", code, message)


def _identity(store, attempt_id):
    row = attempts._require_attempt(store, attempt_id)
    assignment = attempts._fixed_assignment(row)
    if assignment is None:
        _refuse("a runtime deadline requires an activated fixed assignment")
    return row, assignment


def _id(kind, attempt_id, assignment):
    return kind + ":" + digest({"attempt_id": attempt_id,
                                "assignment": assignment})[len("sha256:"):]


def _policy(value, row):
    if value is None:
        return None
    held = boundaries.document(value, "a runtime deadline policy", required=POLICY)
    boundaries.text(held["policy_digest"], "a runtime deadline policy digest")
    if held["policy_digest"] != row["policy_digest"]:
        _refuse("runtime deadline policy differs from the recorded attempt policy")
    if type(held["policy_generation"]) is not int or held["policy_generation"] < 1:
        _refuse("runtime deadline policy generation is a positive whole number")
    if type(held["duration_seconds"]) is not int or held["duration_seconds"] <= 0:
        _refuse("runtime deadline duration is a positive whole number of seconds")
    if held["action"] not in ("report-only", "cancel"):
        _refuse("runtime deadline action is report-only or cancel")
    return held


def _record(store, operation_id, kind, operands, members):
    record = store.operation_record(operation_id)
    if record is None:
        return None
    signature = manager_signature(kind, operands)
    found, answer = store.replay(operation_id, signature, kind=kind)
    if record["state"] != "committed" or not found:
        _refuse("runtime deadline evidence is not a committed operation")
    return boundaries.document(answer, "a committed runtime deadline document",
                               required=members)


def _pin_of(store, row, assignment):
    attempt_id = row["runtime_attempt_id"]
    operation_id = _id("runtime.deadline-pin", attempt_id, assignment)
    record = store.operation_record(operation_id)
    if record is None:
        return None
    # Decode via the journal, then compare its own signed policy with the row.
    _, value = store.replay(operation_id, record["signature"], kind="runtime.deadline-pin")
    held = boundaries.document(value, "a pinned runtime deadline", required=PIN)
    policy = _policy(held["policy"], row)
    expected = {"attempt_id": attempt_id, "assignment": assignment, "policy": policy}
    held = _record(store, operation_id, "runtime.deadline-pin", expected, PIN)
    if held["attempt_id"] != attempt_id or held["assignment"] != assignment:
        _refuse("runtime deadline pin names another attempt or assignment")
    started = boundaries.instant(held["started_at"], "a pinned runtime start instant")
    deadline = None if policy is None else boundaries.deadline(
        started, policy["duration_seconds"], "a pinned runtime deadline")
    if held["deadline_at"] != deadline:
        _refuse("runtime deadline differs from its pinned start and duration")
    return held


def deadline_of(store, *, attempt_id):
    """Read the immutable pin, or None for a legacy/unstarted unpinned attempt."""
    with store.snapshot():
        row, assignment = _identity(store, attempt_id)
        return _pin_of(store, row, assignment)


def _selection(store, row, policy):
    assignment = attempts._fixed_assignment(row)
    held = _policy(policy, row)
    pin = _pin_of(store, row, assignment)
    if pin is not None and pin["policy"] != held:
        _refuse("runtime deadline selection changed on retry", "operation-collision")
    if pin is None and store.operation_record(attempts._start_operation_id(row)) is not None:
        if held is not None:
            _refuse("a committed legacy start cannot acquire a runtime deadline")
    return held


def _pin_start(store, row, policy):
    assignment = attempts._fixed_assignment(row)
    held = _selection(store, row, policy)
    attempt_id = row["runtime_attempt_id"]
    if store.operation_record(attempts._start_operation_id(row)) is not None:
        return
    operands = {"attempt_id": attempt_id, "assignment": assignment, "policy": held}

    def act(connection):
        current, fixed = _identity(store, attempt_id)
        if fixed != assignment or current["execution_runtime"] != "not-started":
            _refuse("runtime deadline pin requires the same unstarted assignment; execution is " + current["execution_runtime"])
        now = store._now()
        until = None if held is None else boundaries.deadline(
            now, held["duration_seconds"], "a runtime attempt deadline")
        return documents.deadline_pin(**operands, started_at=now, deadline_at=until)

    store.transact(_id("runtime.deadline-pin", attempt_id, assignment),
                   "runtime.deadline-pin", manager_signature("runtime.deadline-pin", operands), act)


def _start_allowed(store, row, policy):
    held = _selection(store, row, policy)
    pin = _pin_of(store, row, attempts._fixed_assignment(row))
    if pin is None:
        _refuse("a new runtime start requires its explicit deadline selection")
    if held is not None and held["action"] == "cancel" and store._now() >= pin["deadline_at"]:
        _refuse("the pinned cancellation deadline has already been reached")


def _eligible(row):
    if row["cleanup"] not in ("pending", "blocked-on-intake") or row["execution_runtime"] == "destroyed":
        _refuse("a terminal attempt cannot acquire a new deadline observation", "already-terminal")
    if row["worker_disposition"] != "none":
        _refuse("an answered attempt cannot acquire a new deadline observation", "already-terminal")


def _reached(store, pin):
    operands = {"attempt_id": pin["attempt_id"], "assignment": pin["assignment"],
                "pin_digest": digest(pin)}
    operation_id = _id("runtime.deadline-reached", pin["attempt_id"], pin["assignment"])
    answer = _record(store, operation_id, "runtime.deadline-reached", operands, REACHED)
    if answer is not None:
        if any(answer[key] != value for key, value in operands.items()):
            _refuse("runtime deadline observation differs from its pin")
        at = boundaries.instant(answer["observed_at"], "a reached runtime deadline instant")
        if pin["deadline_at"] is None or at < pin["deadline_at"]:
            _refuse("runtime deadline observation precedes its deadline")
    return operation_id, operands, answer


def observe_deadline(store, port, *, attempt_id):
    """Record only the first reached instant; an early observation writes nothing."""
    row, assignment = _identity(store, attempt_id)
    pin = _pin_of(store, row, assignment)
    if pin is None or pin["policy"] is None:
        _refuse("this attempt has no configured runtime deadline")
    operation_id, operands, already = _reached(store, pin)
    if already is not None:
        return already
    intake._require_participant(port, assignment, attempt_id)
    if port.assignment_of(assignment["work_ref"]["work_id"], assignment["work_ref"]["authority_uuid"]) != assignment:
        _refuse("runtime deadline observation names a stale assignment")

    def act(connection):
        current, fixed = _identity(store, attempt_id)
        if fixed != assignment:
            _refuse("runtime deadline observation names a changed assignment")
        _eligible(current)
        now = store._now()
        if now < pin["deadline_at"]:
            raise _NotReached()
        return documents.deadline_reached(**operands, observed_at=now)

    try:
        return store.transact(operation_id, "runtime.deadline-reached",
                              manager_signature("runtime.deadline-reached", operands), act)
    except _NotReached:
        return None


def _ending(store, attempt_id, retention_policy_digest):
    boundaries.text(retention_policy_digest, "a deadline retention policy digest")
    row, assignment = _identity(store, attempt_id)
    pin = _pin_of(store, row, assignment)
    if pin is None or pin["policy"] is None:
        _refuse("this attempt has no configured runtime deadline")
    operation_id, _, reached = _reached(store, pin)
    if reached is None:
        _refuse("runtime deadline has no committed reached observation")
    return row, pin, operation_id, reached


def _command(row, pin, reached_id, reached, retention):
    return documents.deadline_destroy_command(
        runtime_attempt_id=row["runtime_attempt_id"], assignment_ref=pin["assignment"],
        runtime_id=row["runtime_id"], deadline_operation_id=reached_id,
        deadline_digest=digest(reached), cancel_operation_id=attempts._cancel_operation_id(row),
        authority_operation_id=attempts._authority_cancel_operation_id(row),
        retention_policy_digest=retention)


def _operation(command):
    kind = "runtime.destroy-deadline"
    operation_id = kind + ":" + digest(command)[len("sha256:"):]
    return documents.operation(operation_id=operation_id,
        signature_digest=digest({"kind": kind, "operands": {**command, "operation_id": operation_id}}))


def _cancel_intent(store, row, reached_id):
    reason = "runtime deadline reached: " + reached_id
    expected = documents.cancel_intent(attempt_id=row["runtime_attempt_id"],
        assignment=attempts._fixed_assignment(row),
        authority_operation_id=attempts._authority_cancel_operation_id(row), reason=reason)
    record = _record(store, attempts._cancel_operation_id(row), "attempt.cancel",
        {"attempt_id": row["runtime_attempt_id"], "expect": expected["assignment"],
         "authority_operation_id": expected["authority_operation_id"], "reason": reason},
        documents.CONTRACTS["attempt.cancel-intent"][0])
    if record is not None and record != expected:
        _refuse("deadline cancellation intent differs from its fixed observation")
    return record, reason


def _proof(store, command):
    operation = _operation(command)
    proof = _record(store, operation["operation_id"], "runtime.destroy-deadline", command, PROOF)
    if proof is None:
        return None
    if proof["command"] != command:
        _refuse("deadline cleanup command differs from its owner records")
    authorization_id = "runtime.deadline-cleanup-authorized:" + digest(command)[len("sha256:"):]
    authorization = _record(store, authorization_id, "runtime.deadline-cleanup-authorized", command, DESTROY)
    if authorization != command:
        _refuse("deadline cleanup lacks its exact committed authorization")
    intake._abandoned_fence(proof["fence"], command["assignment_ref"], "deadline cleanup")
    observed = _destroy_observation(proof["observed"], command["runtime_id"])
    if observed["state"] != "absent" or intake._unsettled_providers(observed):
        _refuse("deadline cleanup has no positive absence and settled providers")
    intake._abandoned_absence(store, proof["cleanup"], command["runtime_attempt_id"], operation, "deadline cleanup")
    return proof


def _destroy_observation(value, runtime_id):
    held = boundaries.document(value, "a deadline destroy observation",
                               required=intake._DESTROY_MEMBERS[0], optional=intake._DESTROY_MEMBERS[1])
    boundaries.identity(held["runtime_id"], "a deadline observed runtime identity")
    boundaries.text(held["why"], "a deadline destroy observation reason")
    if held["runtime_id"] != runtime_id or held["state"] not in intake._DESTROY_STATES:
        _refuse("deadline destroy observation names another runtime or unknown state")
    for provider in ("credentials", "launch"):
        intake._provider_ending(held[provider], provider)
    return held


def deadline_cleanup_of(store, *, attempt_id, retention_policy_digest):
    """Read a deadline family's positive cleanup proof; never infer it from axes."""
    with store.snapshot():
        row, pin, reached_id, reached = _ending(store, attempt_id, retention_policy_digest)
        if pin["policy"]["action"] != "cancel":
            return None
        intent, _ = _cancel_intent(store, row, reached_id)
        if intent is None or row["runtime_id"] is None:
            return None
        return _proof(store, _command(row, pin, reached_id, reached, retention_policy_digest))


def _cooperative_failure(store, row, reached_id, stage, failure):
    # Retain the original typed fault without allowing provider exception prose
    # to leak a held credential. Unrecordable diagnostics retain a fixed account.
    try:
        fault = attempts._refusal_failure(failure) if isinstance(failure, ContractRefusal) else attempts._fault_failure(failure)
        check_no_durable_secret(fault, "a deadline cooperative failure")
        fault["message"] = fault["message"][:2000]
        digest(fault)
    except Exception:
        fault = {"kind": "fault", "fault": "unrecordable-diagnostic",
                 "message": "cooperative call raised; diagnostic withheld"}
    operands = {"attempt_id": row["runtime_attempt_id"], "assignment": attempts._fixed_assignment(row),
                "runtime_id": row["runtime_id"], "deadline_operation_id": reached_id,
                "cancel_operation_id": attempts._cancel_operation_id(row), "stage": stage, "failure": fault}
    kind = "runtime.deadline-cooperative-failure"
    operation_id = kind + ":" + digest(operands)[len("sha256:"):]
    store.transact(operation_id, kind, manager_signature(kind, operands),
                   lambda connection: {**operands, "observed_at": store._now()})


def _cancel_for_deadline(store, port, agent, adapter, row, pin, reached_id, reason):
    """Recover only cooperative faults, then obtain the exact fence again.

    The ordinary owner keeps its exception behavior. Capturing the actual
    exception objects at the two advisory boundaries distinguishes them from
    Authority, journal and manager failures without guessing from error text.
    """
    failures = []

    def cooperative(stage, performing, command):
        try:
            return performing(command)
        except Exception as failure:
            failures.append((stage, failure))
            raise

    cooperative_agent = SimpleNamespace(cancel=lambda command: cooperative("agent.cancel", agent.cancel, command))
    cooperative_runtime = SimpleNamespace(stop=lambda command: cooperative("adapter.stop", adapter.stop, command))
    try:
        cancelled = attempts.request_cancellation(store, port, cooperative_agent, cooperative_runtime,
            attempt_id=row["runtime_attempt_id"], reason=reason)
        return intake._abandoned_fence(cancelled["fenced"], pin["assignment"], "deadline cancellation")
    except Exception as failure:
        captured = [one for _, one in failures]
        same = len(captured) == 1 and failure is captured[0]
        grouped = (len(captured) == 2 and type(failure) is ExceptionGroup
                   and len(failure.exceptions) == 2
                   and all(actual is expected for actual, expected in zip(failure.exceptions, captured)))
        if not (same or grouped):
            raise
        for stage, advisory in failures:
            _cooperative_failure(store, row, reached_id, stage, advisory)
        current, assignment = _identity(store, row["runtime_attempt_id"])
        if assignment != pin["assignment"] or current["runtime_id"] != row["runtime_id"]:
            _refuse("deadline cooperative failure recovery names a changed assignment or runtime")
        intent, _ = _cancel_intent(store, current, reached_id)
        if intent is None:
            _refuse("deadline cooperative failure recovery has no committed cancellation intent")
        # This exact Authority operation is a retry of the already-issued fence,
        # not an inference from an axis, local intent, or the advisory exception.
        fence = port.cancel(assignment, intent["authority_operation_id"], reason,
                            assignment["work_ref"]["work_id"], assignment["work_ref"]["authority_uuid"])
        return intake._abandoned_fence(fence, assignment, "deadline cancellation recovery")


def advance_deadline(store, port, agent, adapter, *, attempt_id, retention_policy_digest):
    """Apply only the persisted policy, preserving output and retryable cleanup."""
    row, pin, reached_id, reached = _ending(store, attempt_id, retention_policy_digest)
    if pin["policy"]["action"] == "report-only":
        return documents.deadline_advanced(observation=reached, action="report-only", cleanup=None, discharge=None)
    intake._require_participant(port, pin["assignment"], attempt_id)
    intent, reason = _cancel_intent(store, row, reached_id)
    command = _command(row, pin, reached_id, reached, retention_policy_digest)
    proof = _proof(store, command) if intent is not None and row["runtime_id"] is not None else None
    if proof is not None:
        discharged = discharge_deadline_quiescence_gate(store, port,
            attempt_id=attempt_id, retention_policy_digest=retention_policy_digest)
        return documents.deadline_advanced(observation=reached, action="cancel", cleanup=proof, discharge=discharged)
    for capability, what in ((getattr(agent, "cancel", None), "a deadline agent cancel"),
            (getattr(adapter, "stop", None), "a deadline runtime stop"),
            (getattr(adapter, "destroy_deadline", None), "a deadline runtime destroy"),
            (getattr(port, "satisfy_gate", None), "a deadline Authority gate discharge")):
        boundaries.capability(capability, what)
    intake._custody_capable(adapter)
    if row["cleanup"] not in ("pending", "blocked-on-intake"):
        # Ordinary receipt cleanup can already have committed before discharge.
        if intake.intake_receipt_of(store, attempt_id) is not None:
            cleanup = intake.authorize_cleanup(store, port, adapter, attempt_id=attempt_id,
                                               retention_policy_digest=retention_policy_digest)
            discharge = intake.discharge_quiescence_gate(store, port, attempt_id=attempt_id,
                                                         retention_policy_digest=retention_policy_digest)
            return documents.deadline_advanced(observation=reached, action="cancel", cleanup=cleanup, discharge=discharge)
        _refuse("a terminal cleanup cannot acquire a new deadline ending", "already-terminal")
    if intent is None and row["worker_disposition"] != "none":
        _refuse("worker answered before deadline cancellation; use its ordinary ending")
    fence = _cancel_for_deadline(store, port, agent, adapter, row, pin, reached_id, reason)
    intent, _ = _cancel_intent(store, row, reached_id)
    if intent is None:
        _refuse("deadline cancellation has no committed intent")
    current, fixed = _identity(store, attempt_id)
    if fixed != pin["assignment"] or current["runtime_id"] != row["runtime_id"]:
        _refuse("deadline cancellation assignment or runtime changed")
    if current["runtime_id"] is None:
        if store.operation_record(attempts._start_operation_id(current)) is not None:
            attempts.reconcile_runtime(store, adapter, attempt_id=attempt_id)
            current, _ = _identity(store, attempt_id)
        if current["runtime_id"] is None:
            proof = attempts.unstarted_cancellation_of(store, port, attempt_id)
            return documents.deadline_advanced(observation=reached, action="cancel", cleanup=proof, discharge=None)
    if intake.intake_receipt_of(store, attempt_id) is not None:
        cleanup = intake.authorize_cleanup(store, port, adapter, attempt_id=attempt_id,
                                           retention_policy_digest=retention_policy_digest)
        discharge = None
        if cleanup.get("cleanup") in ("complete", "retained"):
            discharge = intake.discharge_quiescence_gate(store, port, attempt_id=attempt_id,
                                                         retention_policy_digest=retention_policy_digest)
        return documents.deadline_advanced(observation=reached, action="cancel", cleanup=cleanup, discharge=discharge)
    command = _command(current, pin, reached_id, reached, retention_policy_digest)
    cleanup = intake._authorize_deadline_cleanup(store, adapter, command=command, fence=fence)
    discharge = None
    if cleanup.get("cleanup", {}).get("cleanup") == "retained":
        discharge = discharge_deadline_quiescence_gate(store, port, attempt_id=attempt_id,
                                                       retention_policy_digest=retention_policy_digest)
    return documents.deadline_advanced(observation=reached, action="cancel", cleanup=cleanup, discharge=discharge)


def discharge_deadline_quiescence_gate(store, port, *, attempt_id, retention_policy_digest):
    """Carry only a validated committed deadline cleanup to its exact remote gate."""
    proof = deadline_cleanup_of(store, attempt_id=attempt_id, retention_policy_digest=retention_policy_digest)
    if proof is None:
        _refuse("no committed deadline cleanup can discharge this gate")
    command = proof["command"]
    assignment = command["assignment_ref"]
    intake._require_participant(port, assignment, attempt_id)
    operation = _operation(command)
    kind = "authority.discharge-quiescence-deadline"
    operation_id = kind + ":" + digest(command)[len("sha256:"):]
    gate = intake._quiescence_gate_token(assignment)
    evidence = {"kind": intake.RUNTIME_ABSENT, "runtime": command["runtime_id"]}
    operands = {"attempt_id": attempt_id, "assignment": assignment,
                "runtime_id": command["runtime_id"], "cleanup_operation": operation,
                "operation_id": operation_id, "gate": gate, "evidence": evidence}
    already = _record(store, operation_id, kind, operands, DISCHARGE)
    if already is not None:
        if any(already[key] != value for key, value in operands.items()) or already["authority_receipt"] != {
                "gate": gate, "kind": intake.RUNTIME_ABSENT, "phase": "queued"}:
            _refuse("deadline discharge receipt differs from its exact cleanup")
        return already
    intake._same_authority(port, assignment, attempt_id)
    answer = port.satisfy_gate(assignment["work_ref"]["work_id"], operation_id, gate, evidence)
    if answer != {"gate": gate, "kind": intake.RUNTIME_ABSENT, "phase": "queued"}:
        _refuse("deadline Authority discharge returned another gate or outcome")
    return store.transact(operation_id, kind, manager_signature(kind, operands),
        lambda connection: documents.deadline_discharge(**operands, authority_receipt=answer))
