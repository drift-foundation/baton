"""W383215 / DESIGN LIM-5: explicit Job cancellation and the admission fence.

WHAT THIS OWNS. One durable, replayable CANCELLATION REQUEST per Job, journalled
in this store before any external effect, and the FENCE every admission owner
of this store reads inside its own write transaction: a fenced Job reserves no
worker, claims no offer, launches no runtime, opens no replacement episode, no
correction round and no fresh attempt. The request names the Job, the reason
and the moment it was committed; that moment is the shutdown-attempt trigger
LIM-5 measures from, and nothing moves it afterwards.

WHAT IT DOES NOT OWN, deliberately. Cessation. A request is an intent and a
fence; it is not an ending, not a verdict, not a cleanup and not cessation
evidence. The serving sweep carries the request out through the EXISTING
owners -- `request_cancellation` for an attached runtime, the pre-attach
assignment fence for a claimed attempt that never started -- and those owners'
own axes and endings are the only account of whether anything ceased. A
`job.cancel.target` record proves that an ORDER was placed for one exact
target; reconciliation keeps looking at the target every tick afterwards.

TWO STORES, NO CROSS-STORE TRANSACTION. Everything here that runs inside a
transaction reads this database only. The control store's attempt axes are
read by the callers AFTER this store's boundary is released, and are handed in
as plain documents.
"""

import json
from datetime import datetime, timezone

from ..contracts import ContractRefusal, digest
from ..contracts.errors import name_value
from ..worker_manager import boundaries
from . import documents, episodes, submission
from .store import job_signature

__all__ = ["REQUEST_KIND", "TARGET_KIND", "EFFECTS", "TARGET_STATES",
           "SETTLED_STATES", "SHUTDOWN_STATES", "SHUTDOWN_BOUND_SECONDS",
           "TRIGGERS", "REASON_KIND",
           "request_operation_id", "target_operation_id", "request",
           "reason_operation_id", "order_reason", "over",
           "fence_of", "fenced", "fences_of", "refuse_fenced", "requests_of",
           "targets_of", "record_target", "effect_for", "target_state",
           "reported", "report", "observed_from"]

REQUEST_KIND = "job.cancel"
TARGET_KIND = "job.cancel.target"
# W383217 (review 2026-11-19T00-20-37Z P2): THE ONE REASON THE STOP OWNERS
# ARE GIVEN for a Job, journalled when the first order is placed. The
# owners' stop operation is one per attempt and signed over its reason, so
# a Job whose fence is rediscovered as an earlier deadline after an
# operator's request was already carried out must keep ordering with the
# wording it first used, or a retry collides on the owner's own journal.
REASON_KIND = "job.cancel.reason"

# W383217: WHAT CAN CLOSE A JOB. The operator's explicit request, or the
# first stage/Job deadline reached under the Job's admitted control
# (`job_control.expire`). Both are journalled fences this module reads; the
# EARLIEST TRIGGER INSTANT is the Job's fence, decided from the records --
# the request's committed instant, the expiry's deadline instant -- never
# from which one a sweep happened to observe first. A tie goes to the
# explicit request.
TRIGGERS = ("operator", "stage-deadline", "job-deadline")

# THE TWO EFFECTS THE SWEEP CAN ORDER, each through one existing owner.
ORDER_CESSATION = "order-cessation"
FENCE_UNSTARTED = "fence-unstarted"
EFFECTS = (ORDER_CESSATION, FENCE_UNSTARTED)

# What one target of a request is reported as. `ceased`,
# `retired-before-admission`, `fenced-unstarted` and `ended-before-request`
# are SETTLED for the shutdown attempt: nothing of that target can still be
# executing. Everything else is still being reconciled.
# `ended-before-request` is any ending this request did not order: the
# attempt ended on its own account, before or beside the request, and its
# outcome, verdict and output stand exactly as the owners recorded them.
# `order-failed` is the owner's own record that its stop did not cross for
# the attached runtime; the pass asks again on the next tick. `ending-in-
# progress` is a worker that answered, whose ending the ending owners drive.
TARGET_STATES = ("retired-before-admission", "awaiting-offer-lapse",
                 "pending", "fenced-unstarted", "ordered", "order-failed",
                 "ending-in-progress", "ceased", "ended-before-request",
                 "held-unknown")
SETTLED_STATES = frozenset(("retired-before-admission", "fenced-unstarted",
                            "ceased", "ended-before-request"))

# LIM-5: a bounded shutdown attempt after the trigger, reported separately.
SHUTDOWN_BOUND_SECONDS = 120
SHUTDOWN_STATES = ("complete", "within-bound", "unresolved", "unknown-time")

# The cancellation owner's outcomes that mean its stop did NOT cross.
_FAILED_OUTCOMES = frozenset(("stop-failed", "engine-unavailable",
                              "fenced-not-ordered"))
_CEASED_CLEANUP = frozenset(("complete", "retained"))


def _refuse(message, *, category="refused", code="precondition"):
    raise ContractRefusal(category, code, message)


def request_operation_id(job_id):
    """ONE request per Job, so a repeat replays and a changed one collides."""
    return f"{REQUEST_KIND}:{job_id}"


def reason_operation_id(job_id):
    return REASON_KIND + ":" + job_id


def target_operation_id(authority_uuid, job_id, stage_id, episode, attempt_id,
                        effect):
    """One order per exact target and effect.

    Bound to the Authority namespace, the Job, the stage, the EPISODE and the
    attempt, so a replacement episode of the same stage -- which this fence
    forbids, but which a store from before the fence may hold -- can never
    replay an order placed for its predecessor.
    """
    return TARGET_KIND + ":" + digest({
        "authority_uuid": authority_uuid, "job_id": job_id,
        "stage_id": stage_id, "episode": episode, "attempt_id": attempt_id,
        "effect": effect})[len("sha256:"):]


def request(store, *, job_id, reason):
    """Record the explicit cancellation of one Job, effectively once.

    REPLAY IS BY IDENTITY AND SIGNATURE. The same Job and reason answer the
    committed record; the same Job with another reason is an operation
    collision, because one Job has one cancellation and a second account of it
    would be the second ledger this Work refuses to invent.

    WHAT IS OBSERVED IS EVIDENCE, NOT THE TARGET SET. The stages and live
    episodes seen inside this commit are recorded so a reader can see what the
    request found; what the sweep acts on is derived afresh on every tick from
    the live rows, so an admission that won a race against this fence is still
    found and reconciled afterwards.
    """
    boundaries.identity(job_id, "a Job id")
    reason = boundaries.text(reason, "a cancellation reason")
    if not reason.strip():
        _refuse("a cancellation carries the operator's own reason; calling "
                "this operation IS the request, so a blank one is a request "
                "nobody made", category="integrity", code="schema")
    operands = {"job_id": job_id, "reason": reason}
    signature = job_signature(REQUEST_KIND, operands)
    operation_id = request_operation_id(job_id)

    def act(connection):
        if submission.job_of(store, job_id) is None:
            _refuse(f"Job {name_value(job_id)} is not held by this store; a "
                    f"cancellation names work this manager admitted")
        observed = []
        for stage in submission.stages_of(store, job_id):
            live = episodes.live_of(store, stage["stage_id"])
            observed.append({
                "stage_id": stage["stage_id"], "kind": stage["kind"],
                "episode": live["episode"] if live is not None else None,
                "attempt_id": (live["attempt_id"] if live is not None
                               else None),
                "episodes": len(episodes.episodes_of(store,
                                                     stage["stage_id"]))})
        return documents.job_cancellation(
            operation_id=operation_id, job_id=job_id, reason=reason,
            requested_at=store._now(), incarnation=store.incarnation,
            observed=observed, trigger="operator")

    return store.transact(operation_id, REQUEST_KIND, signature, act)


def _request_in(connection, job_id):
    row = connection.execute(
        "SELECT state, result FROM operations WHERE operation_id = ? AND "
        "kind = ?", (request_operation_id(job_id), REQUEST_KIND)).fetchone()
    if row is None or row["state"] != "committed" or row["result"] is None:
        return None
    return json.loads(row["result"])


def _earliest(request, expiry):
    """The Job's fence: the earliest trigger, the explicit request on a tie."""
    if request is None:
        return expiry
    if expiry is None or request["requested_at"] <= expiry["requested_at"]:
        return request
    return expiry


def fenced(connection, job_id):
    """The fence of one Job, read on THIS connection, or None.

    This is the read every admission owner makes inside its own write
    transaction. It is two rows of this database and nothing else: the
    explicit request and the deadline expiry (W383217), whichever triggered
    first. The answer carries `trigger`, `reason` and `requested_at` -- the
    LIM-5 trigger instant the shutdown bound runs from -- whichever record
    it is.
    """
    from . import job_control

    return _earliest(_request_in(connection, job_id),
                     job_control.expiry_in(connection, job_id))


def fence_of(store, job_id):
    boundaries.identity(job_id, "a Job id")
    return fenced(store._connection, job_id)


def refuse_fenced(connection, job_id, what):
    """Refuse `what` for a cancelled Job, ORDINARILY, inside the caller's act.

    Ordinary rather than durable: the fence is already the durable fact, and
    recording a second refused outcome under the admission's own identity
    would make a cancelled Job's stages `exceptional`, which is a stage that
    FAILED. A cancelled stage did not fail; it was retired.
    """
    held = fenced(connection, job_id)
    if held is not None:
        if held.get("trigger", "operator") == "operator":
            _refuse(f"Job {name_value(job_id)} was cancelled at "
                    f"{held['requested_at']} ({held['reason']}); {what} is "
                    f"not admitted after an explicit cancellation")
        _refuse(f"Job {name_value(job_id)} expired at "
                f"{held['requested_at']} ({held['reason']}); {what} is not "
                f"admitted after the deadline")
    return None


def requests_of(store):
    """Every committed cancellation this store holds, by Job."""
    held = {}
    for row in store._connection.execute(
            "SELECT result FROM operations WHERE kind = ? AND state = "
            "'committed' AND result IS NOT NULL", (REQUEST_KIND,)):
        record = json.loads(row["result"])
        held[record["job_id"]] = record
    return held


def fences_of(store):
    """Every Job's fence -- the earliest of its request and its expiry."""
    from . import job_control

    requests = requests_of(store)
    expiries = job_control.expiries_of(store)
    return {job_id: _earliest(requests.get(job_id), expiries.get(job_id))
            for job_id in set(requests) | set(expiries)}


def targets_of(store, job_id=None):
    """Every committed order record, by Job, oldest first."""
    held = {}
    for row in store._connection.execute(
            "SELECT result FROM operations WHERE kind = ? AND state = "
            "'committed' AND result IS NOT NULL ORDER BY settled_at",
            (TARGET_KIND,)):
        record = json.loads(row["result"])
        if job_id is None or record["job_id"] == job_id:
            held.setdefault(record["job_id"], []).append(record)
    return held if job_id is None else held.get(job_id, [])


def record_target(store, *, job_id, stage_id, episode, attempt_id, effect,
                  evidence):
    """Journal that ONE order was placed for one exact target.

    Written AFTER the owner's call returned, because the owner's own journal
    is where the act is replayable; this is this store's account of having
    asked. It carries the owner's returned identities so a reader can follow
    the order to the record that will eventually prove cessation.
    """
    if effect not in EFFECTS:
        _refuse(f"a cancellation order has one of {EFFECTS}; this is "
                f"{name_value(effect)}", category="integrity", code="schema")
    operands = {"authority_uuid": store.authority_uuid, "job_id": job_id,
                "stage_id": stage_id, "episode": episode,
                "attempt_id": attempt_id, "effect": effect}
    operation_id = target_operation_id(**operands)
    signature = job_signature(TARGET_KIND, operands)

    def act(connection):
        if fenced(connection, job_id) is None:
            _refuse(f"no cancellation of Job {name_value(job_id)} is "
                    f"committed; an order is placed for a request that exists",
                    category="integrity", code="schema")
        return documents.job_cancellation_target(
            operation_id=operation_id, job_id=job_id, stage_id=stage_id,
            episode=episode, attempt_id=attempt_id, effect=effect,
            recorded_at=store._now(), evidence=evidence)

    return store.transact(operation_id, TARGET_KIND, signature, act)


def order_reason(store, job_id, fence):
    """The reason every stop order of this Job carries, journalled ONCE.

    Signed over the Job alone, so the call that finds the record committed
    replays it whatever record is the fence by then: the first order's
    wording is the Job's wording. `fence` is the record in force when the
    FIRST order is placed, and its `operation_id` is kept beside the reason
    so a reader can follow which account the owners were told.
    """
    operation_id = reason_operation_id(job_id)
    signature = job_signature(REASON_KIND, {"job_id": job_id})

    def act(connection):
        if fenced(connection, job_id) is None:
            _refuse(f"no cancellation of Job {name_value(job_id)} is "
                    f"committed; an order's reason follows a fence that "
                    f"exists", category="integrity", code="schema")
        return documents.job_cancellation_reason(
            operation_id=operation_id, job_id=job_id,
            reason=fence["reason"], fence_operation_id=fence["operation_id"],
            recorded_at=store._now())

    return store.transact(operation_id, REASON_KIND, signature, act)["reason"]


# -- what the sweep decides, per target, from the owners' live facts ---------


def _order_of(targets, attempt_id, effect):
    for record in targets:
        if record["attempt_id"] == attempt_id and record["effect"] == effect:
            return record
    return None


def _ceased(axes):
    return (axes["execution_runtime"] == "destroyed"
            or axes["cleanup"] in _CEASED_CLEANUP)


def _owner_ordered(observed, axes):
    """Whether the cancellation OWNER recorded that both boundaries crossed
    for the runtime that is attached NOW.

    Review 2026-11-18T19-56-12Z P1: `_order_quiescence` moves the axis to
    `cancel-requested` before it asks the adapter to stop, so the axis is an
    intent. The owner's own `attempt.cessation-outcome` record is where the
    answer lives: `ordered` means the agent and the runtime both accepted;
    `stop-failed`, `engine-unavailable` and `fenced-not-ordered` mean they
    did not. A record for another runtime identity is another generation's
    account and says nothing about this one.
    """
    cessation = observed.get("cessation")
    if cessation is None or cessation.get("outcome") != "ordered":
        return False
    if axes["runtime_id"] is not None:
        return cessation.get("runtime_id") == axes["runtime_id"]
    # IN-FLIGHT START: nothing attached yet, and the owner resolved the
    # token-bound container itself and ordered it. Its record names that
    # identity; a later attachment of the same identity keeps this true, and
    # a different one is ordered afresh above.
    return cessation.get("runtime_id") is not None


def _never_started(axes):
    """POSITIVELY never started: no identity attached AND the axis still says
    so. `start-requested` with nothing attached is an in-flight start whose
    reply may have been lost -- review 2026-11-18T20-12-59Z -- and belongs to
    the exact-generation cancellation owner, which resolves the token-bound
    runtime. `intake._no_start_declared` refuses anything else, rightly.
    """
    return axes["runtime_id"] is None and axes["execution_runtime"] == "not-started"


def over(entry):
    """Whether this stage's WORK IS OVER by the owners' evidence alone.

    W383217 (review 2026-11-19T00-20-37Z P1): the deadline of a stage that
    is over closes nothing, and a Job whose every stage is over is never
    fenced by a deadline that passes later. OVER IS NOT A LABEL. The
    projection's `exceptional` covers an uncertain runtime, a durable
    refusal beside an attached runtime and a failed start -- none of which
    is cessation, and each of which the cancellation pass still has to order
    or fence. So this reads what `effect_for` reads: a live attempt is over
    when its runtime axes say ceased; a stage with no live episode is over
    when its last episode ended in a way nothing replaces.
    """
    if entry["episode"] is None:
        history = entry["history"]
        if not history or history[-1]["ended_at"] is None:
            return False
        return history[-1]["ended_state"] not in documents.REPLACEABLE_ENDINGS
    axes = (entry.get("observed") or {}).get("runtime")
    return axes is not None and _ceased(axes)


def effect_for(state, observed, targets=()):
    """Which effect one live target owes RIGHT NOW, or None.

    LEVEL-TRIGGERED ON THE OWNERS' FACTS, never on an earlier order. The
    runtime axes, the frozen output and the cancellation owner's recorded
    outcome are read on this tick; a stop the owner recorded as failed, or a
    runtime that attached after a fence for a not-yet-started attempt, is
    simply ordered again, and the owner replays what it already committed and
    performs what it has not. Nothing suppresses unfinished stop work: not
    the request record, not a stage's terminal label, not the intent axis.
    """
    axes = observed.get("runtime")
    attempt_id = observed.get("attempt_id")
    if axes is None:
        # No attempt row: nothing of this attempt was ever activated. A
        # CLAIMED stage holds a live assignment, which the composition that
        # would have launched it fences instead.
        return FENCE_UNSTARTED if state == "claimed" else None
    if _ceased(axes):
        return None
    fenced = _order_of(targets, axes["attempt_id"], FENCE_UNSTARTED)
    if fenced is not None and axes["runtime_id"] is None:
        # The Authority fence answered synchronously and this store recorded
        # it; nothing attached since. A runtime attaching later is handled
        # below like any attached runtime.
        return None
    if _never_started(axes):
        return FENCE_UNSTARTED
    if observed.get("output") is not None:
        # The worker ANSWERED. Its ending and cleanup are the ending owners'
        # own path; ordering a cancellation over an answered attempt would
        # be a second ending beside the ruled one.
        return None
    if _owner_ordered(observed, axes):
        return None
    del attempt_id
    return ORDER_CESSATION


def target_state(entry, observed, targets, requested_at):
    """One target's reported state, from persisted rows and live facts only.

    `entry` is a `projection.materialized` owned entry (episode, history,
    receipts, attempt); `observed` carries the control store's `runtime`
    axes, the frozen `output` and the cancellation `cessation` record for the
    live attempt; `targets` are this Job's order records.
    """
    live = entry["episode"]
    if live is None:
        last = entry["history"][-1] if entry["history"] else None
        if last is None or last["ended_at"] is None:
            return "retired-before-admission"
        return ("ended-before-request" if last["ended_at"] < requested_at
                else "ceased")
    attempt_id = live["attempt_id"]
    ordered = _order_of(targets, attempt_id, ORDER_CESSATION)
    fenced_unstarted = _order_of(targets, attempt_id, FENCE_UNSTARTED)
    axes = observed.get("runtime")
    if axes is None:
        receipts = entry["receipts"]
        if "admit" not in receipts:
            return "retired-before-admission"
        if "claim" not in receipts:
            return "awaiting-offer-lapse"
        return "fenced-unstarted" if fenced_unstarted is not None else "pending"
    if _ceased(axes):
        # OVER, AND WHOSE DOING IT WAS: an attempt this request ordered or
        # fenced is `ceased`; one that ended with no order from this request
        # ended on its own account, and its outcome is preserved untouched.
        return ("ceased" if ordered is not None
                or fenced_unstarted is not None else "ended-before-request")
    if fenced_unstarted is not None and axes["runtime_id"] is None:
        # The pre-attach fence moves the axis to `cancel-requested` with
        # nothing to stop; the fence record is what says the assignment was
        # ended.
        return "fenced-unstarted"
    if _never_started(axes):
        return "pending"
    if observed.get("output") is not None:
        return "ending-in-progress"
    if axes["execution_runtime"] == "uncertain":
        return "held-unknown"
    if _owner_ordered(observed, axes):
        return "ordered"
    cessation = observed.get("cessation")
    if cessation is not None and cessation.get("runtime_id") == axes["runtime_id"] \
            and cessation.get("outcome") in _FAILED_OUTCOMES:
        return "order-failed"
    return "pending"


def _instant(value):
    for grammar in ("%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%dT%H:%M:%SZ"):
        try:
            return datetime.strptime(value, grammar).replace(
                tzinfo=timezone.utc)
        except (TypeError, ValueError):
            continue
    return None


def reported(record, targets, entries, *, observed_of, now):
    """The additive `cancellation` member of one Job's status, or None.

    THE TRIGGER IS THE COMMITTED REQUEST INSTANT. Elapsed time is measured
    from `requested_at` as this store stamped it; a retry, a restart, a
    replay or a manager that was not running do not restart the bound, and an
    instant this reader cannot order against the request is reported as
    `unknown-time` rather than as time that has not passed.
    """
    if record is None:
        return None
    reported_targets = []
    settled = True
    for entry in entries:
        attempt = entry["attempt"]
        observed = observed_of(entry) if attempt is not None else {}
        observed = observed if observed is not None else {}
        axes = observed.get("runtime")
        cessation = observed.get("cessation")
        state = target_state(entry, observed, targets, record["requested_at"])
        settled = settled and state in SETTLED_STATES
        orders = [one for one in targets
                  if attempt is not None
                  and one["attempt_id"] == attempt["attempt_id"]]
        reported_targets.append(documents.job_cancellation_target_status(
            stage_id=entry["stage"]["stage_id"],
            episode=attempt["episode"] if attempt is not None else None,
            attempt_id=attempt["attempt_id"] if attempt is not None else None,
            state=state,
            runtime=(axes["execution_runtime"] if axes is not None else None),
            cleanup=(axes["cleanup"] if axes is not None else None),
            cessation=(None if cessation is None else {
                "outcome": cessation.get("outcome"),
                "runtime_id": cessation.get("runtime_id"),
                "effects": list(cessation.get("effects") or ())}),
            orders=[{"effect": one["effect"],
                     "operation_id": one["operation_id"],
                     "recorded_at": one["recorded_at"]} for one in orders]))
    started = _instant(record["requested_at"])
    observed = _instant(now)
    if settled:
        shutdown, elapsed = "complete", None
    elif started is None or observed is None or observed < started:
        shutdown, elapsed = "unknown-time", None
    else:
        elapsed = int((observed - started).total_seconds())
        shutdown = ("unresolved" if elapsed >= SHUTDOWN_BOUND_SECONDS
                    else "within-bound")
    return documents.job_cancellation_report(
        operation_id=record["operation_id"], job_id=record["job_id"],
        reason=record["reason"], requested_at=record["requested_at"],
        trigger_at=record["requested_at"],
        trigger=record.get("trigger", "operator"),
        shutdown_bound_seconds=SHUTDOWN_BOUND_SECONDS,
        elapsed_seconds=elapsed, shutdown=shutdown,
        targets=reported_targets,
        **({"observed_at": record["observed_at"]}
           if "observed_at" in record else {}))


def observed_from(control, attempt_id):
    """The three owner facts the report reads, from a control store handle.

    The same members the serving projection's observation carries; for a
    reader that has no deployment to observe through.
    """
    from ..worker_manager import attempt_runtime_of, frozen_output_of
    from ..worker_manager.failure_cause import attempt_cessation_outcome_of

    return {"runtime": attempt_runtime_of(control, attempt_id),
            "output": frozen_output_of(control, attempt_id),
            "cessation": attempt_cessation_outcome_of(control, attempt_id,
                                                      "cancellation")}


def report(jobs, job_id, *, observed_of, now):
    """One Job's cancellation report from a Job store handle, read-only.

    The Job rows are materialized under one read view and that view is
    released before `axes_of` is asked anything about another store.
    """
    from . import projection

    boundaries.identity(job_id, "a Job id")
    snapshot = projection.materialized(jobs)
    if job_id not in snapshot["stages_by_job"]:
        _refuse(f"Job {name_value(job_id)} is not held by this store")
    record = snapshot["cancellations"].get(job_id)
    entries = [snapshot["owned"][row["stage_id"]]
               for row in snapshot["stages_by_job"][job_id]]
    return reported(record, snapshot["cancellation_targets"].get(job_id, []),
                    entries, observed_of=observed_of, now=now)
