"""The long-lived control loop: recover, derive, delegate, record.

W71875. WHAT MAKES THIS A MANAGER RATHER THAN A SCRIPT is that every tick
starts from persisted state. Nothing is carried in a variable across a
restart, no step is owed because the previous command said so, and an operator
supplies no per-transition instruction: a sweep reads the two stores, derives
which acts are owed, delegates each to its canonical operation, and records
what came back.

THE ORDER INSIDE ONE ACT IS THE RESTART CONTRACT, and it is deliberately not
the obvious one. The delegated operation is performed OUTSIDE this store's
transaction, and the receipt is written afterwards from the manager's own
journal row. That leaves exactly one window -- performed but unrecorded -- and
it is the window the reconciliation read closes: the next sweep finds the
manager's committed operation under the identity this build derives, adopts
it, and does not perform it again. The reverse order would be worse in a way
no read could fix: a receipt written first and a crash before the call would
durably assert an act that never happened.

WHY THE RECEIPT IS TAKEN FROM THE MANAGER'S ROW AND NOT FROM THE CALL'S
ANSWER. The two are the same bytes when the call performed the act and are not
comparable when it replayed one -- and `issue_offer` deliberately answers with
a bearer that must not be stored. Reading the row means a performed act and an
adopted act record the same thing, so a restart audit compares receipts rather
than provenance.
"""

import json

from ..contracts import ContractRefusal
from ..contracts.errors import name_value
from ..worker_manager import boundaries
from . import delegation, documents, projection, submission
from .store import job_signature

__all__ = ["TICK_SECONDS", "reconcile", "serve", "sweep"]

# The default distance between ticks of a serving loop, in seconds. It is a
# DEFAULT and not a policy: `serve` takes the interval as an operand, and a
# deployment that wants another cadence supplies one.
TICK_SECONDS = 5

_RECEIPT_KIND = "stage.receipt"


def receipt_operation_id(stage_id, act):
    return f"{_RECEIPT_KIND}:{stage_id}:{act}"


def reconcile(store, operations, *, now):
    """Resume: run the manager's own restart recovery, then sweep once.

    The recovery is the MANAGER's, not a second one written here. An offer a
    previous incarnation issued and never delivered a bearer for is abandoned
    by `recover_on_restart`; an accepted one stays recoverable. Re-deciding
    that would be a second opinion about somebody else's durable state, and
    the two opinions would differ exactly when it mattered.
    """
    recovered = operations.recover(now=now)
    return sweep(store, operations, now=now, recovered=recovered)


def sweep(store, operations, *, now, recovered=None):
    """One tick: adopt what already committed, then derive and delegate.

    THE ADOPTION PASS COMES FIRST AND COVERS EVERY ACT, not only the ones a
    stage still owes. A crash between a delegated call and its receipt leaves
    the manager holding a committed operation and this store holding no record
    of it -- and for the claim in particular the canonical state has already
    moved on, so the act is no longer owed and a pass that only looked at owed
    acts would leave the receipt missing forever. Reconciling by the identity
    rather than by the eligibility is what makes "records the returned
    identity/receipt" survive a restart.
    """
    boundaries.instant(now, "the sweep's instant")
    held = projection.stage_states(store, operations)
    acts = _adopt(store, operations, held)
    if acts:
        # The receipts changed underneath the derivation, so what is owed is
        # decided from the state AFTER adoption rather than before it.
        held = projection.stage_states(store, operations)
    for owed in projection.owed_acts(store, operations, held):
        stage = held[owed["stage_id"]]["stage"]
        acts.append(_delegate(store, operations, owed, stage,
                              submission.job_of(store, stage["job_id"])))
    return documents.sweep_report(observed_at=now, recovered=recovered,
                                  acts=acts)


def _adopt(store, operations, held):
    """Record a receipt for every canonical act this store never wrote one for.

    Nothing is performed here. The manager's journal is the authority on what
    happened, so an operation committed under the identity this build derives
    is adopted exactly as it stands -- and an act with no such row is left
    alone, because absence of a receipt is not evidence that an act ran.

    THAT THE ROW IS THIS STAGE'S ACT IS PROVED AT THE READ, and no longer
    inherited from the `stage_states` pass that built `held` immediately above.
    Review [P1, 2026-09-03]: a proof that has to stay true between two reads is
    not a proof of what the second one returned. A stage whose offer was absent
    when that pass looked is answered `None` there -- absence is the ordinary
    state of an unstarted stage -- so a foreign offer committing in between
    would be adopted here on the strength of a check that ran before it
    existed, and reported to an operator as this Job's `adopted` act.
    """
    adopted = []
    for stage_id in sorted(held):
        entry = held[stage_id]
        stage = entry["stage"]
        job = submission.job_of(store, stage["job_id"])
        for act in documents.ACTS:
            if act in entry["receipts"]:
                continue
            operation_id = operations.canonical_operation(act,
                                                          stage["offer_id"])
            record = _proved(operations, operation_id, stage, job)
            if record is None:
                continue
            state = "refused" if record["state"] == "refused" else "adopted"
            _record(store, {"stage_id": stage_id, "act": act}, record, state)
            adopted.append(documents.reconciliation(
                stage_id=stage_id, act=act, outcome=state,
                operation_id=operation_id))
    return adopted


def serve(store, operations, *, clock, sleep, should_continue,
          interval=TICK_SECONDS):
    """The long-lived process, with its waiting and its stopping INJECTED.

    A loop that reached for `time.sleep` and a module-level flag would be a
    loop no test can drive and no deployment can stop politely. So the caller
    supplies the instant source, the wait and the predicate that ends the run,
    and this function owns only the order: recover once, then sweep until the
    predicate says to stop.

    Answers the LAST report rather than every one of them. A process that ran
    for a week would otherwise answer with a week of reports, and the useful
    fact at the end of a run is what was true at the end of it.
    """
    boundaries.capability(clock, "the Job manager's instant source")
    boundaries.capability(sleep, "the loop's wait")
    boundaries.capability(should_continue, "the loop's stop condition")
    if type(interval) is not int or interval <= 0:
        raise ContractRefusal(
            "integrity", "schema",
            f"a serving loop ticks a positive whole number of seconds apart; "
            f"this is {name_value(interval)}")
    report = reconcile(store, operations, now=clock())
    while should_continue():
        sleep(interval)
        report = sweep(store, operations, now=clock())
    return report


def _proved(operations, canonical_id, stage, job):
    """One canonical row under a derived identity, or absence -- never a row
    this stage has not been shown to own.

    OBTAINING AND PROVING ARE ONE ACT HERE, and that is the whole of review
    [P1, 2026-09-03]. They used to be two steps a caller could take the first
    of: `_delegate` proved the row its FIRST read returned and then read the
    journal again after the delegated call, and `_adopt` rested on a check the
    projection pass had run a moment earlier. Both of those reads can return a
    row that did not exist when the proof ran -- a second Job store commits the
    same derived `offer.issue` identity, this store's call refuses the
    collision, and the foreign row is picked up as the answer. Routing every
    read through one function leaves no read that can skip the proof.

    Absence is answered as absence: an unissued offer is the ordinary state of
    a stage nothing has admitted, and there is nothing there to prove.
    """
    record = operations.receipt_of(canonical_id)
    if record is not None:
        delegation.check_binding(operations, stage, job)
    return record


def _delegate(store, operations, owed, stage, job):
    """Perform one owed act at most once, and record its canonical receipt.

    ONE ACQUISITION AFTER THE CALL, WHICHEVER WAY THE CALL ANSWERED. A returned
    call and a durable refusal are two answers about the same journal, and
    reading it at two sites was what let one of them go unproved. So the
    delegated call decides only whether a missing row is `deferred` or a
    derived-identity fault, and the row itself is obtained and proved once.
    """
    canonical_id = owed["operation_id"]
    record = _proved(operations, canonical_id, stage, job)
    performed = False
    if record is None:
        try:
            _perform(operations, owed["act"], stage, job)
        except ContractRefusal as refusal:
            # AN ORDINARY REFUSAL IS AN ANSWER, NOT A FAILURE. `submit_claim`
            # refuses an offer the worker has not accepted yet, and that is
            # the honest state of the world rather than something to record.
            # A DURABLE one did commit a journal row, so the act is settled
            # and the row below is what settles it here too.
            deferred = {"category": refusal.category, "code": refusal.code,
                        "message": refusal.message}
        else:
            deferred = None
        record = _proved(operations, canonical_id, stage, job)
        if record is None:
            if deferred is not None:
                return documents.reconciliation(
                    stage_id=owed["stage_id"], act=owed["act"],
                    outcome="deferred", operation_id=canonical_id,
                    detail=deferred)
            # THE DERIVED IDENTITY IS WRONG, and this is where that shows.
            # The operation happened and the journal holds nothing under
            # the name this build asked for, so every later reconciliation
            # would repeat it. Refusing here is the only answer that does
            # not silently start re-issuing offers.
            raise ContractRefusal(
                "integrity", "schema",
                f"the {owed['act']} of stage "
                f"{name_value(owed['stage_id'])} was performed and the "
                f"Worker Manager journalled no operation "
                f"{name_value(canonical_id)}; this build derives that "
                f"identity to decide what a restart already did, and one "
                f"that names nothing would make every sweep repeat the "
                f"act")
        performed = True
    state = ("refused" if record["state"] == "refused"
             else ("performed" if performed else "adopted"))
    _record(store, owed, record, state)
    return documents.reconciliation(
        stage_id=owed["stage_id"], act=owed["act"], outcome=state,
        operation_id=canonical_id)


def _perform(operations, act, stage, job):
    if act == "admit":
        return operations.admit(stage, job)
    return operations.claim(stage)


def _record(store, owed, record, state):
    """Write the receipt for one settled canonical act.

    THE SIGNATURE NAMES THE FACT AND NOT HOW WE LEARNED IT. `performed` and
    `adopted` are the same act observed by two paths -- one incarnation that
    called it and one that found it committed -- so putting the path in the
    durable identity would make two sweeps of one act collide instead of
    replaying.
    """
    stage_id = owed["stage_id"]
    act = owed["act"]
    operation_id = record["operation_id"]
    signature = job_signature(_RECEIPT_KIND,
                              {"stage_id": stage_id, "act": act,
                               "operation_id": operation_id})
    detail = {"canonical_state": record["state"],
              "settled_at": record["settled_at"],
              "result": json.loads(record["result"])
              if record["result"] is not None else None,
              "refusal": json.loads(record["refusal"])
              if record["refusal"] is not None else None}

    def perform(connection):
        recorded_at = store._now()
        connection.execute(
            "INSERT INTO receipts (stage_id, act, operation_id, state, "
            "detail, recorded_at, incarnation) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (stage_id, act, operation_id, state,
             json.dumps(detail, sort_keys=True, ensure_ascii=False),
             recorded_at, store.incarnation))
        return documents.receipt(
            stage_id=stage_id, act=act, operation_id=operation_id,
            state=state, recorded_at=recorded_at, detail=detail)

    return store.transact(receipt_operation_id(stage_id, act), _RECEIPT_KIND,
                          signature, perform)
