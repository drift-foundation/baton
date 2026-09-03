"""What a stage IS, derived rather than stored.

W71875. THE ACCEPTANCE VOCABULARY IS A PROJECTION AND NOT A COLUMN. `queued`,
`offered`, `claimed`, `running`, `reviewing`, `changes-requested`,
`integrating`, `completed` and `exceptional` are computed here from two
sources -- this store's receipts of the acts it delegated, and the Worker
Manager's own public reads -- and written nowhere. A column saying "running"
would be a second account of the runtime axis the manager owns, and the moment
the two disagreed a restart would have to choose which to believe.

DEPENDENCIES GATE ON `completed` AND NOTHING ELSE. A predecessor that ended in
`changes-requested` or `exceptional` leaves its successors blocked, and this
leaf does not reopen it: the same-line correction cycle is W71918's and the
first slice's terminal policy is to report and contain. So a gate that will
never open is REPORTED as closed rather than quietly treated as satisfied.

WHAT THE RUNTIME PROJECTION CARRIES, and what it deliberately does not. The
manager's durable runtime facts are the runtime id, the execution runtime and
the fixed assignment, so those are what a status document names. W71830's
worker-pool ruling separates `worker_id`, `incarnation_id` and `assignment_id`
as three identities; the first two are W71877's to introduce, and inventing
placeholder values for them here would put a fact in an operator's hands that
nothing produced.
"""

import json

from ..worker_manager import boundaries
from . import delegation, documents, schema, submission

__all__ = ["ACT_OUTCOMES", "gates_of", "owed_acts", "receipt_rows",
           "receipts_of", "stage_states", "status"]

# What one sweep can answer about one owed act.
ACT_OUTCOMES = ("performed", "adopted", "deferred", "refused")

# How a frozen result's disposition -- the manager's own closed vocabulary --
# reaches the vocabulary an operator reads. `plan-rejected` is a REVIEW's
# verdict, so it means changes were requested; on any other stage the same
# disposition is an ending nobody planned for, which is exceptional and is
# reported as such rather than rounded to the nearest happy state.
_DISPOSITIONS = {"completed": "completed", "unable": "exceptional",
                 "cancelled": "exceptional"}

# Which state a claimed stage with a live runtime is IN, by what the stage is
# for. One vocabulary, three kinds, written down rather than inferred.
_RUNNING = {"implementation": "running", "review": "reviewing",
            "integration": "integrating"}


def receipt_rows(store):
    return [boundaries.row(record, "a persisted receipt",
                           schema.RECEIPT_COLUMNS)
            for record in store._connection.execute(
                "SELECT * FROM receipts ORDER BY stage_id, act").fetchall()]


def receipts_of(store, stage_id):
    """Every receipt for one stage, keyed by the act it records."""
    boundaries.identity(stage_id, "a stage id")
    return {record["act"]: record for record in
            [boundaries.row(entry, "a persisted receipt",
                            schema.RECEIPT_COLUMNS)
             for entry in store._connection.execute(
                 "SELECT * FROM receipts WHERE stage_id = ? ORDER BY act",
                 (stage_id,)).fetchall()]}


def _observed_state(stage, receipts, observed):
    """One stage's state from evidence, before dependencies are considered.

    Returns `None` when nothing has happened to this stage yet, which is the
    only case where the gates decide between `blocked` and `queued`.
    """
    # A DURABLY REFUSED ACT IS THE FIRST ANSWER. Whatever else is true of the
    # stage, an act this control plane delegated and the manager refused for
    # good is a condition an operator has to see rather than a state to keep
    # sweeping past.
    if any(record["state"] == "refused" for record in receipts.values()):
        return "exceptional"
    frozen = observed.get("output")
    if type(frozen) is dict:
        disposition = frozen.get("disposition")
        if disposition == "plan-rejected":
            return ("changes-requested" if stage["kind"] == "review"
                    else "exceptional")
        if disposition in _DISPOSITIONS:
            return _DISPOSITIONS[disposition]
        # A disposition this build does not recognise is not read as the least
        # alarming one. The manager's vocabulary is closed, so an unknown
        # member means this build and that store disagree about what a
        # disposition is.
        return "exceptional"
    if observed.get("claimed_by") is not None or "claim" in receipts:
        runtime = observed.get("runtime")
        if type(runtime) is dict and runtime.get("runtime_id") is not None:
            return _RUNNING[stage["kind"]]
        return "claimed"
    if "admit" in receipts:
        return "offered"
    return None


def stage_states(store, operations, stages=None):
    """Every stage's state and its canonical observation, in one pass.

    The observation is kept beside the state because the status document
    reports both and re-reading the manager a second time would be two
    moments -- a caller comparing one against the other would be comparing a
    stage with itself at two times.

    THE CANONICAL BINDING IS PROVED AS THE OBSERVATION IS ACQUIRED, and this
    is the one pass that makes that true everywhere: the sweep's adoption, the
    derivation of what is owed and the status document all come through here.
    So a control store holding somebody else's offer under this stage's derived
    identity refuses -- it is not adopted as a receipt, and it is not projected
    beside this store's Job either.

    IT IS ONE CALL, NOT TWO, and re-review [P1, 2026-09-03] is why. This pass
    used to prove the offer and then ask for the observation, which read the
    claim, the runtime and the frozen result under a derived ATTEMPT id the
    proof had said nothing about -- so another Job store's offer holding that
    attempt's claim was projected here as this Job's. `observation_of` acquires
    and binds in one operation, and there is no unqualified attempt read left
    for this pass to make.
    """
    rows = stages if stages is not None else submission.stage_rows(store)
    held = {}
    for stage in rows:
        observed = delegation.observation_of(
            operations, stage, submission.job_of(store, stage["job_id"]))
        receipts = receipts_of(store, stage["stage_id"])
        held[stage["stage_id"]] = {
            "stage": stage, "observed": observed, "receipts": receipts,
            "state": _observed_state(stage, receipts, observed)}
    for entry in held.values():
        if entry["state"] is not None:
            continue
        gates = gates_of(entry["stage"], held)
        entry["state"] = ("queued" if all(gate["open"] for gate in gates)
                          else "blocked")
    return held


def gates_of(stage, held):
    """This stage's dependency gates, each with the state that decides it."""
    gates = []
    for gate in json.loads(stage["depends_on"]):
        stage_id = documents.stage_id(gate["job_id"], gate["kind"])
        found = held.get(stage_id)
        # A gate naming a stage this store does not carry cannot be open. The
        # submission boundary refuses an unresolvable dependency, so reaching
        # here means the row set changed underneath us -- and answering `open`
        # would admit a stage whose predecessor nobody can find.
        state = found["state"] if found is not None else None
        gates.append(documents.dependency_gate(
            stage_id=stage_id, state=state, open=state == "completed"))
    return gates


def owed_acts(store, operations, held=None):
    """Every act this control plane owes right now, in a stable order.

    DERIVED FROM PERSISTED STATE, which is the whole point: a restarted
    process answers this from the two stores rather than from an operator's
    memory or a shell transcript.
    """
    held = held if held is not None else stage_states(store, operations)
    owed = []
    for stage_id in sorted(held):
        entry = held[stage_id]
        stage = entry["stage"]
        act = _owed(entry)
        if act is None:
            continue
        owed.append(documents.act(
            stage_id=stage_id, job_id=stage["job_id"], kind=stage["kind"],
            act=act,
            operation_id=operations.canonical_operation(act,
                                                        stage["offer_id"]),
            offer_id=stage["offer_id"], attempt_id=stage["attempt_id"],
            work_id=stage["work_id"]))
    return owed


def _owed(entry):
    if entry["state"] == "queued":
        return "admit"
    # `offered` is the only state a claim is owed from. A claimed, running or
    # terminal stage owes nothing here -- what happens after the claim is the
    # other leaves' work, and a sweep that kept acting would be this one
    # taking it over.
    if entry["state"] == "offered" and "claim" not in entry["receipts"]:
        return "claim"
    return None


def status(store, operations, *, observed_at):
    """The read-only status document, versioned and whole.

    ONE DOCUMENT FOR EVERY SUBMISSION IN THE STORE, because an operator asking
    "what is running" is not asking about one submission and would otherwise
    have to know what to ask for.
    """
    held = stage_states(store, operations)
    jobs = []
    for job in submission.job_rows(store):
        stages = []
        for row in submission.stages_of(store, job["job_id"]):
            entry = held[row["stage_id"]]
            stages.append(_stage_status(entry, held))
        jobs.append(documents.job_status(
            job_id=job["job_id"], submission_id=job["submission_id"],
            input_digest=job["input_digest"],
            policy_digest=job["policy_digest"],
            test_scope=json.loads(job["test_scope"]),
            terminal_policy=job["terminal_policy"], stages=stages))
    return documents.status(
        schema=documents.STATUS_SCHEMA, observed_at=observed_at,
        incarnation=store.incarnation,
        # WHETHER THE CANONICAL STORE WAS READ AT ALL. A status assembled
        # without the manager can still report what was submitted and what
        # this store received receipts for, and saying so is the difference
        # between "nothing is running" and "nobody looked".
        canonical=operations.canonical, jobs=jobs)


def _stage_status(entry, held):
    stage = entry["stage"]
    observed = entry["observed"]
    frozen = observed.get("output")
    runtime = observed.get("runtime")
    return documents.stage_status(
        stage_id=stage["stage_id"], job_id=stage["job_id"],
        kind=stage["kind"], state=entry["state"], work_id=stage["work_id"],
        profile_name=stage["profile_name"],
        profile_digest=stage["profile_digest"], offer_id=stage["offer_id"],
        attempt_id=stage["attempt_id"], gates=gates_of(stage, held),
        receipts=[documents.receipt(
            stage_id=record["stage_id"], act=record["act"],
            operation_id=record["operation_id"], state=record["state"],
            recorded_at=record["recorded_at"],
            detail=json.loads(record["detail"]))
            for _, record in sorted(entry["receipts"].items())],
        runtime={"runtime_id": runtime.get("runtime_id"),
                 "execution_runtime": runtime.get("execution_runtime"),
                 "assignment": runtime.get("assignment"),
                 # SAFE LOCATORS AND NOTHING ELSE. The activity projection is
                 # a count of observed bytes and the instant they were
                 # received; approver ruling M61707 makes it diagnostic, so
                 # nothing here branches on it.
                 "activity": observed.get("activity")}
        if type(runtime) is dict else None,
        # The frozen result's artifacts carry the manager's own locators. They
        # are reported as the manager recorded them and are not resolved,
        # opened or walked here.
        artifacts=frozen.get("artifacts") if type(frozen) is dict else None)
