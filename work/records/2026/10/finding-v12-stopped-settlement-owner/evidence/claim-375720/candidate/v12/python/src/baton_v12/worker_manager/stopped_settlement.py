"""Retain-only settlement of a failed, exactly stopped primary execution.

The installed composition owns instance exclusion and Job/episode selection.
This owner binds the attempt, original assignment, exchange failure and exact
resource generation. It never calls an Authority mutation or an engine effect.
Intent and token fence commit together; observation happens after that commit;
outcome, return and receipt are separate recoverable cuts.
"""
from ..contracts import ContractRefusal
from ..contracts.canonical import digest
from . import attempts, boundaries, exchange, intake, tokens, workspaces
from .store import _recorded, manager_signature

INTENT = "stopped-settlement.intent"
SELECTED = "stopped-settlement.selected"
OUTCOME = "stopped-settlement.outcome"
RECEIPT = "stopped-settlement.receipt"
SCHEMA = "baton.v12.stopped-settlement-request/1"


def _id(kind, identity):
    return kind + ":" + digest(identity)[len("sha256:"):]


def _read(store, operation, kind):
    record = store.operation_record(operation)
    if record is None:
        return None
    return store.replay(operation, record["signature"], kind=kind)[1]


def _request(given):
    request = boundaries.document(given, "a stopped settlement request", required=("schema", "operation_id", "attempt_id", "runtime_id", "start_operation_id", "assignment", "token", "failure_digest"))
    if request["schema"] != SCHEMA:
        raise ContractRefusal("integrity", "schema", "unsupported stopped settlement request schema")
    for field in ("operation_id", "attempt_id", "runtime_id", "start_operation_id"):
        boundaries.identity(request[field], "a stopped settlement identity")
        if len(request[field].encode("utf-8")) > 512:
            raise ContractRefusal("integrity", "schema", "settlement identity exceeds 512 bytes")
    from . import documents
    assignment = boundaries.document(request["assignment"], "settlement assignment", required=("work_ref", "participant", "generation"))
    assignment["work_ref"] = boundaries.document(assignment["work_ref"], "settlement work reference", required=("authority_uuid", "work_id"))
    for key in ("authority_uuid", "work_id"):
        boundaries.identity(assignment["work_ref"][key], "a stopped settlement Work identity")
    boundaries.text(assignment["participant"], "settlement participant")
    boundaries.generation(assignment["generation"], "settlement assignment generation")
    request["assignment"] = documents.assignment(**assignment)
    token = boundaries.document(request["token"], "settlement token", required=("domain", "generation", "owner", "launch"))
    boundaries.generation(token["generation"], "settlement token generation")
    if token["generation"] == 0:
        raise ContractRefusal("integrity", "schema", "a resource token generation starts at one")
    for key in ("domain", "owner", "launch"):
        boundaries.text(token[key], "a stopped settlement token identity")
    request["token"] = token
    value = request["failure_digest"]
    if type(value) is not str or len(value) != 71 or not value.startswith("sha256:") or any(c not in "0123456789abcdef" for c in value[7:]):
        raise ContractRefusal("integrity", "schema", "settlement failure digest must be sha256")
    return request


def failure_digest(delivery):
    """Bind the exchange owner's validated fault history, never an output scan."""
    view = exchange.observation(delivery)
    if view["state"] != "faulted" or view["foreign"] or view["unreadable"] is not None:
        raise ContractRefusal("refused", "precondition", "settlement requires an exact validated faulted file exchange")
    return digest(view)


def _selection(request):
    return _id(SELECTED, request["attempt_id"])


def _state(store, request):
    attempt = attempts._require_attempt(store, request["attempt_id"])
    if attempts._fixed_assignment(attempt) != request["assignment"] or attempt["runtime_id"] != request["runtime_id"] or attempts._start_operation_id(attempt) != request["start_operation_id"]:
        raise ContractRefusal("runtime-observation", "identity-mismatch", "settlement no longer matches the exact fixed attempt")
    current = tokens.token_of(store, request["token"]["domain"], request["token"]["generation"])
    if current is None or any(current[key] != request["token"][key] for key in ("owner", "launch")) or current["container"] != request["runtime_id"] or current["execution"] != request["attempt_id"] or current["operation"] != request["start_operation_id"]:
        raise ContractRefusal("runtime-observation", "identity-mismatch", "settlement token does not belong to this exact execution and start")
    if current["activating"] or current["activation_started"] is None:
        raise ContractRefusal("runtime-observation", "quiescence-unknown", "unsettled activation keeps stopped execution held")
    prepared = workspaces.settlement_preparation(store, request["attempt_id"])
    if request["token"]["domain"] != tokens.domain_of("workspace", prepared["workspace"]):
        raise ContractRefusal("runtime-observation", "identity-mismatch", "settlement token does not govern the prepared workspace")
    if not attempts.start_submission_returned(store, attempt):
        raise ContractRefusal("runtime-observation", "quiescence-unknown", "start submission remains unresolved")
    return attempt, current, prepared


def _observe(store, adapter, request):
    if store._connection.in_transaction:
        raise RuntimeError("runtime observation inside a transaction")
    state, _, _ = attempts._observed(adapter, request["runtime_id"])
    if state not in ("quiescent", "absent"):
        return None, "runtime-" + state
    # No capability is required on the primary path. If the deployment supplies
    # one, its positive or uncertain evidence must not be discarded.
    if getattr(adapter, "surviving_helpers", None) is not None:
        try:
            surviving, unknown = intake._surviving_writers(adapter, store, request["attempt_id"])
        except Exception:
            return None, "writer-observation-unknown"
        if unknown is not None or surviving:
            return None, "writers-unsettled"
    return {"state": state, "runtime_id": request["runtime_id"], "observed_at": store._now(), "source": "trusted-runtime-adapter"}, None


def _governed_domain(govern, attempt):
    boundaries.capability(getattr(govern, "identity", None), "settlement resource governance")
    boundaries.capability(getattr(govern, "release", None), "settlement resource return")
    return tokens.domain_of(govern.resource_kind, govern.identity(attempt))


def status(store, request):
    """Read only; no runtime observation, permission decision or return."""
    request = _request(request)
    found, intent = store.replay(request["operation_id"], manager_signature(INTENT, request), kind=INTENT)
    if not found:
        return {"state": "not-selected", "operation_id": request["operation_id"]}
    outcome = _read(store, _id(OUTCOME, request["operation_id"]), OUTCOME)
    receipt = _read(store, _id(RECEIPT, request["operation_id"]), RECEIPT)
    current = tokens.token_of(store, request["token"]["domain"], request["token"]["generation"])
    state = "settled" if receipt else "returned-receipt-pending" if outcome and current and current["returned"] else "release-pending" if outcome else "held"
    return {"state": state, "operation_id": request["operation_id"], "intent": intent, "outcome": outcome, "receipt": receipt}


def settle_stopped(store, port, adapter, govern, *, request, delivery):
    """Select or resume one failed execution, preserving storage and Authority.

    `port` is the existing Authority read port; `delivery` is the exchange
    owner's typed delivery. Neither is consulted on replay after intent. The
    installed caller must hold its instance and per-attempt invocation guard.
    Core transactions still serialize competing selections and token acting.
    """
    request = _request(request)
    signature = manager_signature(INTENT, request)
    found, intent = store.replay(request["operation_id"], signature, kind=INTENT)
    if not found:
        selected = _read(store, _selection(request), SELECTED)
        if selected is not None:
            if selected == {"operation_id": request["operation_id"], "request_digest": digest(request)}:
                return settle_stopped(store, port, adapter, govern, request=request, delivery=delivery)
            raise ContractRefusal("refused", "operation-collision", "this attempt already selected settlement " + selected["operation_id"])
        attempt, current, prepared = _state(store, request)
        if current["returned"]:
            raise ContractRefusal("refused", "already-terminal", "a new settlement cannot select an already returned execution")
        domain = _governed_domain(govern, attempt)
        if domain != request["token"]["domain"]:
            raise ContractRefusal("runtime-observation", "identity-mismatch", "settlement governance names another resource")
        if type(delivery) is not exchange.ExchangeDelivery or delivery.attempt_id != request["attempt_id"] or failure_digest(delivery) != request["failure_digest"]:
            raise ContractRefusal("runtime-observation", "identity-mismatch", "settlement failure evidence does not match this attempt")
        assignment = request["assignment"]
        if port.assignment_of(assignment["work_ref"]["work_id"], assignment["work_ref"]["authority_uuid"]) != assignment:
            raise ContractRefusal("stale-assignment", "generation", "a new settlement requires the current expected assignment")
        observation, why = _observe(store, adapter, request)
        if why is not None:
            return {"state": "held", "why": why, "operation_id": request["operation_id"], "selected": False}
        selected_at = store._now()

        def begin(_connection):
            _, standing, preparation = _state(store, request)
            if standing["returned"]:
                raise ContractRefusal("refused", "already-terminal", "execution returned before settlement selection")
            if _read(store, _selection(request), SELECTED) is not None:
                raise ContractRefusal("refused", "operation-collision", "another settlement already selected this attempt")
            if preparation != prepared:
                raise ContractRefusal("refused", "precondition", "preparation changed before settlement selection")
            selection = {"operation_id": request["operation_id"], "request_digest": digest(request)}
            tokens._fence_settlement(store, request["token"], selection)
            store._record(_selection(request), SELECTED, manager_signature(SELECTED, selection), "committed", _recorded(selection), None)
            return {"request": request, "selected_at": selected_at, "preparation_digest": digest(preparation)}

        intent = store.transact(request["operation_id"], INTENT, signature, begin)
    report = status(store, request)
    if report["receipt"] is not None:
        return report
    outcome_id = _id(OUTCOME, request["operation_id"])
    outcome = report["outcome"]
    if outcome is None:
        _state(store, request)
        observation, why = _observe(store, adapter, request)
        if why is not None:
            return {**report, "why": why}

        def record_outcome(_connection):
            _, _, preparation = _state(store, request)
            fence = tokens.settlement_fence_of(store, request["token"]["domain"], request["token"]["generation"])
            if fence is None or fence["selection"] != {"operation_id": request["operation_id"], "request_digest": digest(request)} or digest(preparation) != intent["preparation_digest"]:
                raise ContractRefusal("refused", "precondition", "settlement provenance changed after its fence")
            cessation = {"container": request["runtime_id"], "stopped": True, "helpers": []}
            return {"execution_outcome": "failed-stopped", "request_digest": digest(request), "observation": observation, "cessation": cessation, "resources": "preserved", "result_consumption": "unresolved"}

        outcome = store.transact(outcome_id, OUTCOME, manager_signature(OUTCOME, request), record_outcome)
    current = tokens.token_of(store, request["token"]["domain"], request["token"]["generation"])
    if current is None:
        raise ContractRefusal("refused", "precondition", "settlement generation is unavailable")
    if not current["returned"]:
        attempt, current, _ = _state(store, request)
        # This record is post-fence cessation, not an exit acknowledgement. All
        # acting admissions are now fenced; unknown existing effects still hold.
        domain = _governed_domain(govern, attempt)
        if domain != request["token"]["domain"]:
            raise ContractRefusal("runtime-observation", "identity-mismatch", "return governance names another resource")
        govern.release(store, attempt, operation=request["start_operation_id"], cessation=outcome["cessation"], reclaiming=True)

    def receipt(_connection):
        current = tokens.token_of(store, request["token"]["domain"], request["token"]["generation"])
        if current is None or not current["returned"]:
            raise ContractRefusal("refused", "precondition", "settlement return has not committed")
        return {"operation_id": request["operation_id"], "request_digest": digest(request), "execution_outcome": "failed-stopped", "token": request["token"], "resources": "preserved", "result_consumption": "unresolved"}

    store.transact(_id(RECEIPT, request["operation_id"]), RECEIPT, manager_signature(RECEIPT, request), receipt)
    return status(store, request)
