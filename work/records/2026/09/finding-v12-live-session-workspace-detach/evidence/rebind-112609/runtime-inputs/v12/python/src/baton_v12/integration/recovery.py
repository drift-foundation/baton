"""W101493: preserve interrupted integration for an operator.

This is the deliberately small leaf behind ``execution``.  A restart may turn
one still-live integration grant into a durable target block and may project
the evidence needed to inspect it.  It never decides that retained bytes are
good, repairs them, starts a runtime, settles the entry, reopens the target or
discards anything.

The only ending offered here is explicitly named ``abandon_held_lease``.  Its
caller has already chosen to end the obsolete grant, and the function first
reads the attempt from the Worker Manager.  Only ``quiescent`` or ``destroyed``
is positive evidence that the old writer cannot resume; silence, absence,
``not-started`` and ``uncertain`` all refuse.  Abandonment still leaves the
target blocked and the entry held, so inspection and any later repair remain
separate operator decisions.
"""

import os

from ..contracts import ContractRefusal, digest
from ..contracts.errors import name_value
from ..worker_manager import attempts, boundaries
from . import runtime
from .queue import abandon_lease, block_target, entries_of, lease_of, target_of

__all__ = ["HOLD_STATUS_SCHEMA", "abandon_held_lease", "held_status",
           "hold_interrupted"]

HOLD_STATUS_SCHEMA = "baton.v12.integration-operator-hold/1"

# Routine status says only which class THIS leaf knows.  The coordinator
# deliberately accepts arbitrary operator/runtime reason text, which stays in
# the retained blocked account and is represented here by its digest.
STATUS_REASONS = runtime.HOLD_REASONS + ("integration-held",)


def _denied(message):
    raise ContractRefusal("policy", "denied", message)


def _stores(store, manager):
    boundaries.capability(getattr(store, "_connection", None),
                          "the integration coordinator store")
    boundaries.capability(getattr(manager, "_connection", None),
                          "the Worker Manager store")


def _runtime(manager, attempt_id):
    """The inspectable subset of the manager row, including true absence."""
    found = attempts.attempt_runtime_of(manager, attempt_id)
    if found is None:
        return {"attempt_id": attempt_id, "runtime_id": None,
                "execution_runtime": "unknown", "cleanup": "unknown"}
    return {name: found[name] for name in
            ("attempt_id", "runtime_id", "execution_runtime", "cleanup")}


def _delivery(delivery, assignment):
    """One safe locator set and one bounded observation, without payloads."""
    if delivery is None:
        return ({"integration_delivery": None, "assignment_document": None,
                 "result_document": None},
                {"state": "not-assigned", "result": None, "hold": None})
    if type(delivery) is not runtime.IntegrationDelivery:
        _denied("an interrupted integration is inspected through the runtime "
                "boundary's own typed delivery")
    if delivery.attempt_id != assignment["attempt_id"]:
        _denied(f"delivery attempt {name_value(delivery.attempt_id)} does not "
                f"belong to held attempt {name_value(assignment['attempt_id'])}")
    locators = {
        "integration_delivery": delivery.root,
        "assignment_document": os.path.join(
            delivery.assignment_root, runtime.ASSIGNMENT_DOCUMENT),
        "result_document": os.path.join(
            delivery.result_root, runtime.RESULT_DOCUMENT)}
    return locators, runtime.observed_delivery(delivery, assignment)


def _blocked(store, assignment):
    target = target_of(store, assignment["canonical_target_id"])
    if target is None or target["state"] != "blocked":
        return None
    account = target["blocked_account"]
    expected = (assignment["entry_id"], assignment["lease_id"],
                assignment["fence"], assignment["attempt_id"],
                assignment["integrator_participant"])
    actual = (account["entry_id"], account["lease_id"], account["fence"],
              account["attempt_id"], account["integrator_participant"])
    if actual != expected:
        _denied(f"target {name_value(assignment['canonical_target_id'])} is "
                "blocked for another integration account")
    return account


def held_status(store, manager, delivery, assignment):
    """Project one blocked integration without copying untrusted payloads.

    The result and blocked-account payloads remain at their retained locators.
    Status exposes their digests, state and exact coordinator/runtime identities
    instead, so a credential-like string in model-authored detail is not copied
    into routine diagnostics.
    """
    _stores(store, manager)
    composed = runtime._owned_assignment(assignment)
    account = _blocked(store, composed)
    if account is None:
        return None
    runtime_status = _runtime(manager, composed["attempt_id"])
    locators, observed = _delivery(delivery, composed)
    return _status(store, composed, account, runtime_status, locators,
                   observed)


def _status(store, composed, account, runtime_status, locators, observed):
    """Author one projection from snapshots already owned by its caller."""
    entry = entries_of(store, composed["canonical_target_id"], state="held")
    if len(entry) != 1 or entry[0]["entry_id"] != composed["entry_id"]:
        _denied(f"target {name_value(composed['canonical_target_id'])} does "
                "not expose its one held entry")
    held_lease = lease_of(store, composed["lease_id"])
    if held_lease is None:
        _denied(f"held integration lease {name_value(composed['lease_id'])} "
                "is absent")
    # The Worker Manager owns no log bytes here.  Its durable runtime identity
    # is the safe selector a deployment uses to find the retained runtime log;
    # absence stays visible rather than becoming a guessed path.
    locators["runtime_log_selector"] = runtime_status["runtime_id"]
    outcome = (None if observed["result"] is None
               else observed["result"]["outcome"])
    return {
        "schema": HOLD_STATUS_SCHEMA,
        "state": "operator-held",
        "canonical_target_id": composed["canonical_target_id"],
        "target_state": "blocked",
        "entry_id": composed["entry_id"],
        "entry_state": entry[0]["state"],
        "lease_id": composed["lease_id"],
        "lease_state": held_lease["state"],
        "fence": composed["fence"],
        "integrator_participant": composed["integrator_participant"],
        "attempt_id": composed["attempt_id"],
        "reason": (account["reason"] if account["reason"] in STATUS_REASONS
                   else "integration-held"),
        "runtime": runtime_status,
        "locators": locators,
        "evidence": {
            "assignment_digest": runtime.assignment_digest(composed),
            "blocked_account_digest": digest(account),
            "entry_settlement_digest": digest(entry[0]["settlement"]),
            "delivery_state": observed["state"],
            "result_outcome": outcome}}


def hold_interrupted(store, manager, delivery, assignment):
    """Classify a restart observation and durably exclude its target.

    This is intentionally a hold even when a retained result looks complete:
    interruption means the cross-store sequence did not reach its ordinary
    settlement under one uninterrupted execution.  The result stays where the
    runtime wrote it for an operator to inspect.
    """
    _stores(store, manager)
    composed = runtime._owned_assignment(assignment)
    if _blocked(store, composed) is not None:
        return held_status(store, manager, delivery, composed)
    locators, observed = _delivery(delivery, composed)
    runtime_status = _runtime(manager, composed["attempt_id"])
    if observed["state"] == "held":
        reason = observed["hold"]["reason"]
        observation = observed["hold"]["observed"]
    elif runtime_status["execution_runtime"] in runtime.QUIESCENT_STATES:
        reason = "runtime-interrupted"
        observation = "the integration sequence ended before settlement"
    else:
        reason = "runtime-ambiguous"
        observation = "the prior integration runtime is not proved quiescent"
    detail = {
        "attempt_id": composed["attempt_id"],
        "assignment_digest": runtime.assignment_digest(composed),
        "execution_runtime": runtime_status["execution_runtime"],
        "runtime_id": runtime_status["runtime_id"],
        "delivery_state": observed["state"],
        "result_outcome": (None if observed["result"] is None
                           else observed["result"]["outcome"]),
        "observation": observation,
        # The paths are manager-derived from a typed delivery.  They point to
        # retained evidence and are never opened, removed or rewritten here.
        "locators": locators}
    block_target(store,
                 canonical_target_id=composed["canonical_target_id"],
                 entry_id=composed["entry_id"],
                 lease_id=composed["lease_id"], fence=composed["fence"],
                 reason=reason, detail=detail)
    return held_status(store, manager, delivery, composed)


def abandon_held_lease(store, manager, delivery, assignment):
    """Explicitly end the held grant after positive runtime quiescence.

    No caller-authored witness is accepted.  The manager row is read inside
    this operation, and only its terminal runtime states authorize the
    coordinator's existing abandonment verb.  The target remains blocked.
    """
    _stores(store, manager)
    composed = runtime._owned_assignment(assignment)
    account = _blocked(store, composed)
    if account is None:
        _denied(f"target {name_value(composed['canonical_target_id'])} is not "
                "held for operator recovery")
    # OWN EVERY CALLER OPERAND AND THE ANSWER BEFORE THE IRREVERSIBLE VERB.
    # In particular, a foreign delivery must not become a refusal reported
    # after the lease has already ended.
    locators, observed = _delivery(delivery, composed)
    # Construct every fallible coordinator/delivery part first.  The runtime
    # member is replaced in memory from the authoritative read below; this
    # placeholder authorizes nothing.
    placeholder = {"attempt_id": composed["attempt_id"], "runtime_id": None,
                   "execution_runtime": "unknown", "cleanup": "unknown"}
    answer = _status(store, composed, account, placeholder, locators, observed)
    if answer["lease_state"] == "abandoned":
        runtime_status = _runtime(manager, composed["attempt_id"])
        answer["runtime"] = runtime_status
        answer["locators"]["runtime_log_selector"] = \
            runtime_status["runtime_id"]
        return answer
    # THE LAST FALLIBLE PRE-MUTATION READ IS THE CUTPOINT. Delivery adoption,
    # coordinator relationships and every digest in the returned answer were
    # completed above.  From this manager-owned row to `abandon_lease` there
    # are only local comparisons and inert dictionary/string construction.
    runtime_status = _runtime(manager, composed["attempt_id"])
    if runtime_status["execution_runtime"] not in runtime.QUIESCENT_STATES:
        _denied(f"attempt {name_value(composed['attempt_id'])} is "
                f"{name_value(runtime_status['execution_runtime'])}; a held "
                "lease is "
                "abandoned only after the manager positively observes its "
                "runtime quiescent or destroyed at the last "
                "pre-mutation cutpoint")
    answer["runtime"] = runtime_status
    answer["locators"]["runtime_log_selector"] = runtime_status["runtime_id"]
    runtime_id = runtime_status["runtime_id"] or "not-attached"
    evidence = (f"worker-manager attempt {composed['attempt_id']} runtime "
                f"{runtime_id} observed "
                f"{runtime_status['execution_runtime']}")
    abandon_lease(store, lease_id=account["lease_id"],
                  fence=account["fence"],
                  recovery={"attempt_id": account["attempt_id"],
                            "evidence": evidence})
    # The coordinator transition changes only this one projected member: the
    # target stays blocked, the entry stays held and every locator/digest is
    # the preflighted answer above.  Do not perform a new fallible read after
    # the irreversible transition merely to rediscover that fact.
    return dict(answer, lease_state="abandoned")
