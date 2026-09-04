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
from . import delegation, documents, episodes, schema, submission

__all__ = ["ACT_OUTCOMES", "EXCHANGE_OWED", "gates_of", "owed_acts",
           "owed_exchange", "receipt_rows", "receipts_of", "replaceable",
           "stage_states", "status"]

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
                "SELECT * FROM receipts ORDER BY stage_id, episode, act"
            ).fetchall()]


def receipts_of(store, stage_id, episode):
    """Every receipt for ONE EPISODE of one stage, keyed by the act.

    W73629 put the episode in the key. A replacement legitimately performs its
    own `admit`, and a reader that gathered a stage's receipts across every
    episode would see the abandoned attempt's `admit` and conclude the fresh
    episode had already been offered -- which is the wedge, one layer up.
    """
    boundaries.identity(stage_id, "a stage id")
    return {record["act"]: record for record in
            [boundaries.row(entry, "a persisted receipt",
                            schema.RECEIPT_COLUMNS)
             for entry in store._connection.execute(
                 "SELECT * FROM receipts WHERE stage_id = ? AND episode = ? "
                 "ORDER BY act", (stage_id, episode)).fetchall()]}


def replaceable(entry):
    """Whether this stage owes a FRESH episode because its last one ended.

    Only an ending in the closed replaceable set answers yes. An episode that
    ended any other way is a stage that stopped, and it is projected as such
    rather than re-offered on this leaf's own authority.
    """
    if entry["episode"] is not None or not entry["history"]:
        return False
    return (entry["history"][-1]["ended_state"]
            in documents.REPLACEABLE_ENDINGS)


def _observed_state(entry):
    """One stage's state from evidence, before dependencies are considered.

    Returns `None` when nothing has happened to this stage's CURRENT episode
    yet, which is the only case where the gates decide between `blocked` and
    `queued`.

    NO LIVE EPISODE IS TWO DIFFERENT ANSWERS, and W73629 exists because they
    were one. A stage whose episode ended in a replaceable way owes a fresh
    one and is back where an unstarted stage is -- `None` here, so the gates
    decide. A stage whose episode ended any other way is over: an operator has
    to see that, so it is `exceptional` rather than a stage that will quietly
    be offered again.
    """
    stage = entry["stage"]
    receipts = entry["receipts"]
    observed = entry["observed"]
    if entry["episode"] is None:
        return None if replaceable(entry) else "exceptional"
    # A DURABLY REFUSED ACT IS THE FIRST ANSWER. Whatever else is true of the
    # stage, an act this control plane delegated and the manager refused for
    # good is a condition an operator has to see rather than a state to keep
    # sweeping past.
    if any(record["state"] == "refused" for record in receipts.values()):
        return "exceptional"
    # AND SO IS A START THIS MANAGER RECORDED AS FAILED. W76207: the runtime
    # axis alone could not say this. A failed start is journalled as the
    # manager's own act and reconciliation may ATTACH a runtime id afterwards,
    # so a projection reading only `runtime` reported a stage as `running` on
    # the strength of an identity its start never earned. The owner's record
    # decides, and it is read before the runtime is looked at rather than
    # after, so the attached identity never gets to answer first.
    # ...AND SO IS A PREPARATION THIS MANAGER RECORDED AS FAILED. Re-review
    # [P1]: the two are one answer to this projection and two facts to the
    # manager, which is why they are asked as two members and joined here. A
    # preparation that refused never reached an adapter, so it carries no
    # runtime the axis could have reported either.
    if observed.get("start_failure") is not None \
            or observed.get("preparation_failure") is not None:
        return "exceptional"
    # W81857 review 2026-09-04T03-43-45Z [P1]: THE ENDING IS OWED UNTIL ITS
    # LAST SUBSTEP IS SETTLED, AND A FROZEN OUTPUT IS NOT THAT SUBSTEP.
    #
    # This used to give any frozen output precedence, and `EXCHANGE_OWED` asks
    # `conclude` only for `answering` -- so a process death after
    # `request_freeze` and before intake, retention, the Authority pass and
    # cleanup left durable frozen output that every later sweep read as
    # `completed`. The remaining owed acts were never replayed: the Work was
    # reported finished while its assignment was still live and its result had
    # never reached the review Route.
    #
    # The freeze is the THIRD of seven steps. What says the ending finished is
    # the manager's own cleanup axis, which `authorize_cleanup` is the last
    # step to move, so an answered exchange keeps owing `conclude` until that
    # axis is terminal however much of the middle already committed.
    if _ending_owed(entry):
        return "answering"
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
        if type(runtime) is dict \
                and runtime.get("execution_runtime") == "uncertain":
            return "exceptional"
        if type(runtime) is dict and runtime.get("runtime_id") is not None:
            return _conversing(entry)
        return "claimed"
    if "admit" in receipts:
        return "offered"
    return None


# W81857: WHAT AN ATTACHED RUNTIME ACTUALLY MEANS, keyed by the exchange this
# manager can read rather than by the identity it was handed.
#
# The left column is the file exchange's own closed vocabulary and the right is
# this leaf's. `working` becomes the stage-specific active word because the
# worker has published its pre-dispatch receipt, which is the first moment
# anything durable says a provider turn was begun. Everything before that is a
# container that is up.
_EXCHANGE_STATES = {"not-requested": "starting", "waiting": "waiting",
                    "working": None, "answered": "answering",
                    "faulted": "exceptional", "lost": "exceptional",
                    "unreadable": "exceptional"}

# W81857 review [P1]: AND THE RUNTIME AXIS DECIDES WHETHER THE EXCHANGE STATE
# IS STILL TRUE.
#
# `working` says the worker published its pre-dispatch receipt. It does not say
# the worker is still there, and it cannot: a receipt is durable and a process
# is not. A container that died mid-turn keeps a receipt and never publishes a
# terminal, so reading `working` alone recreated the exact defect this Work
# exists to remove -- silence interpreted as progress, one layer down.
#
# So the active word requires BOTH: a receipt, and a runtime this manager
# observes as actually running. Every other axis value with a receipt and no
# terminal is the pinned incomplete/lost outcome -- reported, contained, and
# authorizing no replay, because only a named recovery act with positive
# evidence may turn it into an ending.
_LIVE = "running"

# Which axis values still permit each pre-answer exchange state. An answered
# terminal is deliberately absent from this table: the ending quiesces the
# runtime on purpose, so `answering` is the one state whose correctness does
# not depend on the container still being up.
_REQUIRES_LIVE_RUNTIME = ("not-requested", "waiting", "working")


def _conversing(entry):
    """Which state a claimed stage with an ATTACHED RUNTIME is actually in.

    THE DEFECT THIS FUNCTION IS, spelled out because the one-line version it
    replaced looked correct for a month. `_observed_state` mapped an attached
    runtime identity straight onto the stage-specific running word, so a
    container that started, read no command, spawned no provider and idled at
    zero CPU was projected `running` -- and elapsed time and process health
    cannot tell that apart from useful execution. A projection whose most
    reassuring answer is also its default is not reporting anything.

    ABSENCE IS `starting`, NOT AN INFERRED FAILURE AND NOT AN INFERRED
    SUCCESS. A control plane holding no exchange read has not looked; a
    deployment that composes no exchange has nothing to look at. Both are
    honestly "the container is up and this control plane cannot see a turn in
    it", and neither is grounds for reporting work in progress or for reporting
    that something went wrong.

    AN UNKNOWN EXCHANGE STATE IS `exceptional` rather than the least alarming
    member of the set. The exchange's vocabulary is closed, so a value outside
    it means this build and that reader disagree about what a state is.

    AND THE TWO AXES ARE READ TOGETHER. Review [P1]: a quiescent or destroyed
    runtime with a receipt and no terminal was projected as the active word,
    because only `uncertain` was treated as exceptional and everything else was
    handed to the exchange mapping alone. A worker that died mid-turn is not
    working, whatever its durable receipt says.
    """
    found = entry["observed"].get("exchange")
    if type(found) is not dict:
        return "starting"
    state = found.get("state")
    held = _EXCHANGE_STATES.get(state, "exceptional")
    if state in _REQUIRES_LIVE_RUNTIME:
        runtime = entry["observed"].get("runtime")
        alive = (type(runtime) is dict
                 and runtime.get("execution_runtime") == _LIVE)
        if not alive:
            # INCOMPLETE, AND REPORTED AS SUCH. The turn may have been begun
            # and cannot still be running; nothing here decides whether it was
            # lost, because deciding that is a recovery act with its own
            # positive evidence and its own record.
            return "exceptional"
    return _RUNNING[entry["stage"]["kind"]] if held is None else held


# The cleanup axis values that mean the ending REACHED ITS LAST STEP. Anything
# else -- `pending`, `blocked-on-intake` -- is an ending that has not finished,
# whatever committed before it.
_CLEANUP_SETTLED = ("complete", "retained", "failed")


def _ending_owed(entry):
    """Whether a worker's ending still has owed steps, from CANONICAL state.

    LEVEL-TRIGGERED FROM THE LAST SUBSTEP'S OWN AXIS, which is what makes every
    crash boundary in the middle of the ending replayable. The ordered owners
    each journal their own act, so asking again after a partial ending replays
    what committed and performs what did not; what this decides is only whether
    to ask.

    IT TAKES PRECEDENCE OVER THE FROZEN OUTPUT because the freeze is the third
    of seven steps. A stage whose output is frozen and whose assignment has not
    been passed is not `completed`, and reporting it as such is how a result
    that never reached review looked finished.

    W81857 review 2026-09-04T07-00-54Z [P1]: AND IT NO LONGER DEPENDS ON THE
    EXCHANGE BEING READABLE. This used to require an exchange whose state was
    `answered`, which the read-only `job_manager status` surface never has --
    it is given no deployment factory and honestly reports `exchange: null`.
    So the very same durable state that a serving manager called `answering`
    read back as `completed` there, which is the freeze-window defect wearing
    the one disguise the pass-2 correction did not cover: a reader that cannot
    see the exchange was inventing the end of an ending it could not see.
    `exchange: null` says nobody looked; it does not make a false terminal
    state truthful, and a dependent gate must not open on one.

    THE FROZEN OUTPUT IS THE MANAGER'S OWN EVIDENCE THAT A WORKER ANSWERED,
    which is what makes the exchange unnecessary here. Nothing but the ending
    freezes an output, so a frozen result with an unsettled cleanup axis is an
    ending in progress however the reader learned about it -- and both facts
    are the Worker Manager's own, available to every reader that holds its
    control store.

    THE CLEANUP AXIS IS ASKED FIRST, so a settled ending is settled for every
    reader and the answer does not depend on which evidence happened to be
    available.
    """
    observed = entry["observed"]
    runtime = observed.get("runtime")
    cleanup = runtime.get("cleanup") if type(runtime) is dict else None
    if cleanup in _CLEANUP_SETTLED:
        return False
    found = observed.get("exchange")
    if type(found) is dict and found.get("state") == "answered":
        return True
    return type(observed.get("output")) is dict


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
        stage_id = stage["stage_id"]
        history = episodes.episodes_of(store, stage_id)
        live = episodes.live_of(store, stage_id)
        # NOTHING CANONICAL IS READ FOR A STAGE THAT HAS NO LIVE EPISODE, and
        # that is not an optimization. Its identities belong to an attempt that
        # is over; asking the manager about them would answer with the ended
        # offer's own facts and project a finished attempt as this stage's
        # current one.
        held[stage_id] = {
            "stage": stage, "episode": live,
            "attempt": (episodes.attempting(stage, live)
                        if live is not None else None),
            "history": history,
            "observed": (delegation.observation_of(
                operations, episodes.attempting(stage, live),
                submission.job_of(store, stage["job_id"]))
                if live is not None else delegation.unobserved()),
            "receipts": (receipts_of(store, stage_id, live["episode"])
                         if live is not None else {})}
        held[stage_id]["state"] = _observed_state(held[stage_id])
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
        act = _owed(entry)
        if act is None:
            continue
        # An act is owed BY AN EPISODE, so a stage with none owes nothing here
        # -- what it owes is a replacement, which the sweep opens before it
        # derives anything.
        attempt = entry["attempt"]
        owed.append(documents.act(
            stage_id=stage_id, job_id=attempt["job_id"],
            kind=attempt["kind"], episode=attempt["episode"], act=act,
            operation_id=operations.canonical_operation(
                act, attempt["offer_id"]),
            offer_id=attempt["offer_id"], attempt_id=attempt["attempt_id"],
            work_id=attempt["work_id"]))
    return owed


def _owed(entry):
    if entry["episode"] is None:
        return None
    if entry["state"] == "queued":
        return "admit"
    # `offered` is the only state a claim is owed from. A claimed, running or
    # terminal stage owes nothing here -- what happens after the claim is the
    # other leaves' work, and a sweep that kept acting would be this one
    # taking it over.
    if entry["state"] == "offered" and "claim" not in entry["receipts"]:
        return "claim"
    return None


# W81857: which stage state owes which exchange act. Both are derived from
# canonical state alone, so an ordinary tick and the first tick after a restart
# ask the same question and get the same answer -- which is what makes the
# crash window between an act and anything recording it cost latency instead of
# a lost turn.
EXCHANGE_OWED = {"starting": "dispatch", "answering": "conclude"}


def owed_exchange(held):
    """Every exchange act this control plane owes right now, in stable order.

    `waiting` AND THE ACTIVE WORD OWE NOTHING, deliberately. A published
    command that the worker has not accepted is the manager having done
    everything it owes, and a worker that has published its receipt is a
    provider turn nobody may interrupt -- asking again in either state would be
    this leaf deciding that silence means something.
    """
    owed = []
    for stage_id in sorted(held):
        entry = held[stage_id]
        act = EXCHANGE_OWED.get(entry["state"])
        if act is None or entry["attempt"] is None:
            continue
        owed.append((act, entry["attempt"]))
    return owed


def status(store, operations, *, observed_at):
    """The read-only status document, versioned and whole.

    ONE DOCUMENT FOR EVERY SUBMISSION IN THE STORE, because an operator asking
    "what is running" is not asking about one submission and would otherwise
    have to know what to ask for.

    IT READS AND RECORDS NOTHING, which bounds what it can say. Review [P2,
    2026-09-03]: applying a canonical ending is a durable act, so this pass
    does not attach to the publisher and does not apply one. What it reports is
    what this store has RECORDED, plus the canonical observation of each
    stage's current episode -- so an offer that ended since the last sweep is
    over canonically and still `offered` here until a serving reconciler
    applies it. One tick, in a serving deployment; in a store nobody is
    advancing, exactly as stale as that store is.
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
    live = entry["episode"]
    observed = entry["observed"]
    frozen = observed.get("output")
    runtime = observed.get("runtime")
    return documents.stage_status(
        stage_id=stage["stage_id"], job_id=stage["job_id"],
        kind=stage["kind"], state=entry["state"], work_id=stage["work_id"],
        profile_name=stage["profile_name"],
        profile_digest=stage["profile_digest"],
        # THE CURRENT ATTEMPT, AND NULL WHEN THERE IS NONE. A stage between an
        # ending and its replacement genuinely has no offer, and naming the
        # ended one here would report a finished attempt as the live one --
        # which is the projection half of the defect this Work corrects.
        episode=live["episode"] if live is not None else None,
        offer_id=live["offer_id"] if live is not None else None,
        attempt_id=live["attempt_id"] if live is not None else None,
        # AND THE WHOLE HISTORY BESIDE IT. The abandoned episode keeps its
        # identities and its ending here, so a recovered stage shows what
        # happened to it rather than only where it got to.
        episodes=[documents.stage_episode(**record)
                  for record in entry["history"]],
        gates=gates_of(stage, held),
        receipts=[documents.receipt(
            stage_id=record["stage_id"], episode=record["episode"],
            act=record["act"],
            operation_id=record["operation_id"], state=record["state"],
            recorded_at=record["recorded_at"],
            detail=json.loads(record["detail"]))
            for _, record in sorted(entry["receipts"].items())],
        # W81857: THE EXCHANGE, REPORTED AS THE DEPLOYMENT ANSWERED IT and
        # never resolved, opened or walked here. `null` says this control plane
        # holds no exchange read, which is a different answer from an exchange
        # that has been read and carries no command yet.
        exchange=(observed.get("exchange")
                  if type(observed.get("exchange")) is dict else None),
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
