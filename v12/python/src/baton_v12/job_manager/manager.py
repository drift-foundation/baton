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
from ..worker_manager import events
from . import delegation, documents, episodes, projection, submission
from .store import job_signature

__all__ = ["TICK_SECONDS", "reconcile", "serve", "sweep"]

# The default distance between ticks of a serving loop, in seconds. It is a
# DEFAULT and not a policy: `serve` takes the interval as an operand, and a
# deployment that wants another cadence supplies one.
TICK_SECONDS = 5

# WHERE THE TWO ENDING VOCABULARIES MEET, so the relationship between them is a
# fact this build cannot start without rather than one a test happens to check.
# `documents.py` asserts the half it can see -- every replaceable ending is an
# ending -- and this is the half that needs both packages in scope: every
# ending this store acts on is a terminal offer state, and the one terminal
# offer state it must NOT act on is the successful one. Review [P1,
# 2026-09-03] is what a build that got this wrong did to a running stage.
assert frozenset(documents.EPISODE_ENDINGS) < frozenset(
    events.TERMINAL_OFFER_STATES)
assert (frozenset(events.TERMINAL_OFFER_STATES)
        - frozenset(documents.EPISODE_ENDINGS)) == {"claimed"}

_RECEIPT_KIND = "stage.receipt"


def receipt_operation_id(stage_id, episode, act):
    """One receipt's durable identity, WITH THE EPISODE IN IT.

    W73629: without the episode a replacement's `admit` would replay the
    abandoned episode's receipt instead of recording its own, so the fresh
    offer would be issued and then reported as an act that had already
    happened -- which is the wedge again, one layer down.
    """
    return f"{_RECEIPT_KIND}:{stage_id}:{episode}:{act}"


def reconcile(store, operations, *, now):
    """Resume: recover, RESYNCHRONIZE, then sweep once.

    The recovery is the MANAGER's, not a second one written here. An offer a
    previous incarnation issued and never delivered a bearer for is abandoned
    by `recover_on_restart`; an accepted one stays recoverable. Re-deciding
    that would be a second opinion about somebody else's durable state, and
    the two opinions would differ exactly when it mattered.

    W73629 ADDED THE MIDDLE STEP, and it is the correction at this level.
    Recovery used to end a stage's offer and tell nobody, so this store went
    on projecting `offered` and owing a `claim` against an offer that had
    ended -- one restart wedged the stage permanently. Now the seam is asked to
    REPUBLISH the current canonical state of every offer this store's live
    episodes name, and the sweep applies what comes back before it derives
    anything.

    THE ASK IS LEVEL-TRIGGERED, so nothing depends on having been listening at
    the right moment. An assertion missed while this process was down, or
    dropped with the transient transport, costs one tick of latency and
    nothing else: resynchronizing is exactly what attaching does, and it
    happens on every resume rather than once at a moment nobody can name.
    """
    recovered = operations.recover(now=now)
    return sweep(store, operations, now=now, recovered=recovered,
                 attach=True)


def sweep(store, operations, *, now, recovered=None, attach=False):
    """One tick: observe, replace, adopt, then derive and delegate.

    THE ADOPTION PASS COMES BEFORE DERIVATION AND COVERS EVERY ACT, not only
    the ones a stage still owes. A crash between a delegated call and its
    receipt leaves the manager holding a committed operation and this store
    holding no record of it -- and for the claim in particular the canonical
    state has already moved on, so the act is no longer owed and a pass that
    only looked at owed acts would leave the receipt missing forever.
    Reconciling by the identity rather than by the eligibility is what makes
    "records the returned identity/receipt" survive a restart.

    W73629 PUT TWO PASSES IN FRONT OF IT, in this order and for this reason:

    1. `_observe` drains whatever canonical state assertions are waiting, so
       an episode whose offer has ended is RECORDED as ended before anything
       reads what the stage owes. Draining afterwards would derive from state
       this same tick already knew was stale.
    2. `_replace` opens a fresh episode for every stage whose last one ended
       in a way that took nothing back. Doing it before adoption is what makes
       the replacement's `admit` an act THIS tick performs rather than one the
       operator waits another tick for.

    Both are no-ops on an ordinary tick, which is what a level-triggered
    design buys: the recovery path and the running path are one piece of code
    rather than two that have to agree.
    """
    boundaries.instant(now, "the sweep's instant")
    observed = _observe(store, operations, attach=attach)
    replaced = _replace(store, operations)
    # W85500: AND THE ENGINE IS ASKED BEFORE ANYTHING IS PROJECTED.
    #
    # THE THIRD PASS IN FRONT OF DERIVATION, for the same reason the two above
    # it are there: the runtime axis is state this tick can already know is
    # stale. A start attaches a runtime and records it, and nothing asked the
    # engine about that runtime again -- the successful ending is the only
    # other caller of the reconciliation, and an exceptional stage never
    # reaches it because it owes no act. So a worker that faulted and exited
    # was projected `running` for as long as anybody looked.
    #
    # BEFORE `stage_states`, NOT AFTER. What a stage owes and what a status
    # says are both derived from that projection, so refreshing afterwards
    # would report this tick's decisions from last tick's runtime truth.
    refreshed = _refresh(store, operations)
    held = projection.stage_states(store, operations)
    acts = _adopt(store, operations, held)
    if acts:
        # The receipts changed underneath the derivation, so what is owed is
        # decided from the state AFTER adoption rather than before it.
        held = projection.stage_states(store, operations)
    for owed in projection.owed_acts(store, operations, held):
        entry = held[owed["stage_id"]]
        acts.append(_delegate(store, operations, owed, entry["attempt"],
                              submission.job_of(store,
                                                entry["stage"]["job_id"])))
    # THE LAUNCH PASS IS LAST, AND IT REACQUIRES STATE FIRST. W76207: what a
    # stage is owed here depends on receipts this same tick may have written,
    # so deriving it from the `held` above would be deciding from state the
    # tick has already moved past.
    started = _launch(store, operations, projection.stage_states(store,
                                                                 operations))
    # W81857: AND THE EXCHANGE PASS IS AFTER THE LAUNCH, REACQUIRING AGAIN.
    # A stage this tick just started is a stage that now owes a command, and
    # deriving that from state read before the launch would make every fresh
    # container wait a whole tick for a sequence this tick could already have
    # published. The same reacquisition is what lets one tick command a stage
    # and the next one end it without either being edge-triggered on the other.
    spoken = _converse(store, operations, projection.stage_states(store,
                                                                  operations))
    return documents.sweep_report(observed_at=now, recovered=recovered,
                                  observed=observed, replaced=replaced,
                                  acts=acts, started=started, spoken=spoken,
                                  refreshed=refreshed)


def _converse(store, operations, held):
    """Publish the command a started stage owes, and end one that answered.

    LEVEL-TRIGGERED, WHICH IS THE WHOLE POINT, exactly as `_launch` is. Both
    acts are derived from canonical state -- a started runtime with no command,
    and a worker terminal that answered with no frozen output -- so an ordinary
    tick and the first tick after a restart ask the same question and get the
    same answer. Nothing here depends on having been the process that started
    the container, held a pipe, or saw an event.

    NOTHING IS WRITTEN TO THE JOB STORE, and that is the ruling rather than an
    omission. The command is a durable file whose name this build derives, and
    every substep of the ending is journalled by its own owner under an
    identity that owner derives, so replay is those owners' question. A receipt
    here would be a second account of a fact somebody else already holds -- and
    the one this leaf could not keep true, because the crash window it exists
    for is between the act and the receipt.

    A FAILURE IS CONTAINED TO ITS STAGE. A container that answered nonsense, a
    provider that faulted, an ending whose freeze refused: none of those may
    stop this sweep from observing every other stage. What makes a stage stop
    is a fact its own owner recorded, which the next projection reads.

    AN UNEXPECTED FAULT IS NOT CONTAINED. `_launch` contains an adapter fault
    only when the Worker Manager proved it recorded one; there is no equivalent
    proof for a programming error in a deployment's ending composition, and
    turning one into a per-stage outcome would bury it as a transient
    condition.
    """
    spoken = []
    for act, attempt in projection.owed_exchange(held):
        stage_id = attempt["stage_id"]
        job = submission.job_of(store, attempt["job_id"])
        try:
            performed = (operations.dispatch(attempt, job)
                         if act == "dispatch"
                         else operations.conclude(attempt, job))
        except ContractRefusal as refusal:
            # EVERY REFUSAL HERE IS A CONDITION AND NOT AN ENDING, DURABLE OR
            # NOT, and the difference from `_launch` is a fact about who owns
            # the record. A durable launch refusal that nobody journalled would
            # leave a stage claimed and retried forever, which is why that pass
            # raises; here the DURABLE endings are the Worker Manager's own
            # failed freeze, refused intake and abandonment records, and the
            # next projection reads them through the observation this leaf
            # already takes. There is no state this pass could leave that the
            # exchange and the canonical readers do not already describe.
            spoken.append(documents.stage_exchange(
                stage_id=stage_id, episode=attempt["episode"],
                attempt_id=attempt["attempt_id"], act=act, outcome="deferred",
                detail={"category": refusal.category, "code": refusal.code,
                        "message": refusal.message}))
            continue
        spoken.append(documents.stage_exchange(
            stage_id=stage_id, episode=attempt["episode"],
            attempt_id=attempt["attempt_id"], act=act, outcome="performed",
            detail=performed if type(performed) is dict else None))
    return spoken


def _launch(store, operations, held):
    """Ask the deployment to drive every CLAIMED stage into a live worker.

    LEVEL-TRIGGERED, WHICH IS THE WHOLE POINT. The eligibility is a fact about
    canonical state -- claimed, with no runtime and no recorded start failure --
    so an ordinary tick and the first tick after a restart ask exactly the same
    question and get the same answer. Folding this into `claim()` would have
    made it edge-triggered on an act a resumed manager deliberately does not
    repeat: a crash after the Authority commits the claim leaves the next
    incarnation adopting the canonical settlement without calling `claim`, and
    a launch hidden in there would be skipped once, permanently, on the one
    path nobody is watching.

    A FAILURE IS CONTAINED TO ITS STAGE. Unlike a delegated act, this pass does
    not raise: the acceptance says a failed start must contain that stage and
    still leave every other stage observable, so each launch is reported as its
    own outcome and the loop continues. A DURABLE refusal is the Worker
    Manager's recorded start failure, which the next projection reads as
    `exceptional` through `attempt_start_failure_of` or its preparation
    sibling; an ordinary one is a condition this tick could not satisfy and
    the next tick asks again.

    Nothing is written to the Job store here. `admit` and `claim` remain the
    only receipt acts this leaf owns; the runtime start is journalled by its
    owner under an identity that owner derives, so replay is that manager's
    question rather than a second account kept here.
    """
    started = []
    for stage_id in sorted(held):
        entry = held[stage_id]
        # `claimed` is exactly "the claim is taken and no runtime is attached".
        # `running` already has one, and a recorded start failure has already
        # made the stage `exceptional`, so neither is asked again.
        if entry["state"] != "claimed":
            continue
        attempt = entry["attempt"]
        job = submission.job_of(store, attempt["job_id"])
        try:
            answer = operations.launch(attempt, job)
        except ContractRefusal as refusal:
            detail = {"category": refusal.category, "code": refusal.code,
                      "message": refusal.message}
            if _recorded_failure(operations, attempt, job):
                # THE CANONICAL ENDING EXISTS, so this stage is over and the
                # next projection reads it as `exceptional`. Containing it here
                # is what keeps one failed stage from ending the sweep.
                started.append(documents.stage_launch(
                    stage_id=stage_id, episode=attempt["episode"],
                    attempt_id=attempt["attempt_id"], outcome="refused",
                    detail=detail))
                continue
            if refusal.durable:
                # A DURABLE ENDING NOBODY RECORDED IS NOT A STAGE OUTCOME.
                # Review [P1]: reporting it as `refused` left the stage
                # `claimed` with no canonical failure, so the next tick asked
                # again and the one after that, forever. The deployment's
                # composition owns recording its own durable endings through
                # the Worker Manager; one that refuses durably and journals
                # nothing has left this control plane no fact to project and
                # no reason to stop, and saying so loudly is the only answer
                # that is not a silent retry loop.
                raise ContractRefusal(
                    "integrity", "schema",
                    f"the launch of stage {name_value(stage_id)} refused "
                    f"durably as {name_value(refusal.code)} and the Worker "
                    f"Manager holds no failed-start record for attempt "
                    f"{name_value(attempt['attempt_id'])}; a durable ending "
                    f"this control plane cannot observe would leave the stage "
                    f"claimed and retried on every tick") from refusal
            # AN ORDINARY REFUSAL IS A CONDITION, not an ending: the workspace
            # is not ready, the worker has not accepted. The next tick asks
            # again, which is what level-triggered means.
            started.append(documents.stage_launch(
                stage_id=stage_id, episode=attempt["episode"],
                attempt_id=attempt["attempt_id"], outcome="deferred",
                detail=detail))
            continue
        except Exception as fault:
            # THE ADAPTER FAULT PATH, and review [P1] is why it is here.
            # `request_runtime_start` journals the failed start and then
            # RE-RAISES the adapter's own typed fault, so a real engine error
            # is not a `ContractRefusal` at all -- it escaped this loop,
            # skipped every stage sorted after it, and ended `serve` even
            # though the canonical failure record now existed.
            #
            # ONLY A FAULT THE MANAGER PROVED IT RECORDED IS CONTAINED. A
            # programming error has no such record, and turning one into a
            # per-stage outcome would bury it as a transient condition.
            if not _recorded_failure(operations, attempt, job):
                raise
            started.append(documents.stage_launch(
                stage_id=stage_id, episode=attempt["episode"],
                attempt_id=attempt["attempt_id"], outcome="refused",
                detail={"category": "runtime-observation", "code": "fault",
                        "message": f"{type(fault).__name__}: {fault}"}))
            continue
        # THE RUNTIME IDENTITY IS THE MANAGER'S ANSWER, not a row this leaf
        # went looking for. An answer that names none is not a failure -- an
        # uncertain reconciliation carries no identity -- so it is reported as
        # what it is and the next tick observes rather than starting again.
        runtime_id = (answer.get("runtime_id") if type(answer) is dict
                      else None)
        started.append(documents.stage_launch(
            stage_id=stage_id, episode=attempt["episode"],
            attempt_id=attempt["attempt_id"], outcome="started",
            runtime_id=runtime_id))
    return started


def _observe(store, operations, *, attach):
    """Apply every canonical state assertion waiting for this store.

    NOTHING IS READ OUT OF THE WORKER MANAGER HERE. This asks its seam to
    republish what that manager already holds, then drains the transport; the
    assertions arrive as documents and `apply_offer_state` is the one thing in
    this package that ends an episode.

    ATTACHING NAMES WHAT IS RELEVANT. A control store may carry other Job
    stores' offers, so what this store asks about is the offers its own LIVE
    episodes name: an ended episode needs no further assertion, and asking
    about somebody else's offer would be taking an interest in a row that is
    not this store's business.

    Answers how many assertions were applied, so a tick that resynchronized
    can say so rather than leaving it to be inferred from what followed.
    """
    if attach:
        operations.attach([episode["offer_id"]
                           for episode in _live_episodes(store)])
    return operations.drain(
        {events.OFFER_STATE_KIND: lambda event: apply_offer_state(store,
                                                                  event)},
        quiescent=(lambda: store._connection.in_transaction,))


def _refresh(store, operations):
    """Ask the engine about every live attempt, one stage at a time.

    ONE STAGE'S FAILURE IS ONE STAGE'S. The acceptance says plainly that a
    faulted stage must not stop another from being observed or progressed, so
    a typed refusal is contained here and reported against the stage that
    raised it. An escaping refusal would make one damaged attempt stop the
    whole sweep from projecting anything -- which is the shape of the defect
    this Work exists to correct, arriving by a different road.

    TWO CONDITIONS AND NO MORE, which is re-review 2026-09-04T19:08:40Z [P1].
    Containment is for MALFORMED EVIDENCE a deployment answered with, and for
    the operational failure a deployment itself names as "the engine could not
    be reached". A defect in somebody's code is neither, and it must not be
    converted into report data: `serve` keeps only the last tick's report, so
    a defect contained on an earlier tick is raised nowhere, recorded nowhere,
    and gone as soon as one tick succeeds. It escapes to whoever is running
    the loop instead, where it can be seen and fixed.

    ONLY A LIVE EPISODE. A stage whose episode is over has identities that
    belong to a finished attempt; asking the engine about them would refresh
    somebody else's runtime into this stage's row.

    NOTHING IS WRITTEN HERE. The reconciliation the deployment performs writes
    its own answer under its own identity, exactly as `launch` and `dispatch`
    do, so a second Job-store receipt would be a second account of a fact its
    owner already holds.
    """
    refreshed = []
    for stage in submission.stage_rows(store):
        live = episodes.live_of(store, stage["stage_id"])
        if live is None:
            continue
        attempt = episodes.attempting(stage, live)
        members = {"stage_id": stage["stage_id"], "episode": live["episode"],
                   "attempt_id": live["attempt_id"]}
        try:
            answer = operations.refresh_runtime(attempt)
        except ContractRefusal as refusal:
            # THE CATEGORY AND THE CODE AND NOTHING ELSE. A refusal's prose is
            # composed from values this deployment read, and some of those come
            # from a worker; a sweep report is read by whoever watches the
            # service and is not a place to publish them.
            refreshed.append(documents.stage_refresh(
                **members, state=None,
                detail={"category": refusal.category, "code": refusal.code}))
            continue
        except delegation.RefreshUnavailable as unreachable:
            # AN ENGINE THAT COULD NOT BE ASKED IS NOT A RUNTIME THAT IS GONE.
            # Review 2026-09-04T14-27-54Z [P1]: only typed refusals were
            # contained, so a socket, a pipe or a missing binary aborted the
            # whole sweep before the first projection -- suppressing an
            # exchange terminal that was readable on disk the whole time.
            #
            # THE DEPLOYMENT DECIDES WHAT COUNTS, which is re-review
            # 2026-09-04T19:08:40Z [P1]. This used to catch `OSError` here and
            # then catch `Exception` after it, so every unexpected defect
            # became report data that `serve` overwrote on the next tick. Only
            # the deployment knows which of ITS failures mean the engine could
            # not be reached -- a missing binary and a runner that timed out
            # are the same operational fact and are not the same Python type --
            # so it names them, and this pass contains exactly what it named.
            #
            # NOTHING IS RECORDED FROM THIS. The runtime axis keeps whatever it
            # last knew; what this reports is that the question could not be
            # put, which is the honest difference between "gone" and "unasked".
            refreshed.append(documents.stage_refresh(
                **members, state=None,
                detail={"category": "uncertain", "code": "engine-unreachable",
                        "error": unreachable.engine_error}))
            continue
        refreshed.append(documents.stage_refresh(
            **members,
            state=("not-asked" if answer is None
                   else answer["execution_runtime"])))
    return refreshed


def _live_episodes(store):
    return [live for stage in submission.stage_rows(store)
            for live in [episodes.live_of(store, stage["stage_id"])]
            if live is not None]


def _replace(store, operations):
    """Open a fresh episode for every stage whose last one ended recoverably.

    THE ENDING IS WHAT AUTHORIZES THIS, and only an ending in the closed
    replaceable set. An abandoned offer decided nothing about the stage -- the
    manager ended it because it could not account for a bearer, not because
    anybody looked at the work -- so re-admitting it takes nothing back. An
    episode that ended any other way is a stage that stopped, and this pass
    leaves it stopped for the projection to report.

    ONE REPLACEMENT PER ENDING, decided by the store rather than by this loop.
    The successor's operation identity is derived from the ended episode's
    number, so two managers reconciling one abandonment open the same episode
    and the second replays the first's committed result; the partial unique
    index refuses a second live episode however else the race arrives.
    """
    opened = []
    held = projection.stage_states(store, operations)
    for stage_id in sorted(held):
        entry = held[stage_id]
        if not projection.replaceable(entry):
            continue
        opened.append(episodes.open_next(store, stage_id,
                                         entry["history"][-1]))
    return opened


def _recorded_failure(operations, attempt, job):
    """Did the Worker Manager durably record that THIS attempt will not run?

    The one question that decides whether a launch failure is this stage's
    ending or this control plane's problem. It is asked through the same bound
    observation everything else here goes through, so a foreign attempt under
    a derived id cannot answer it -- and it is asked AFTER the failure, because
    the record is written by the act that just failed.

    A refusal while asking is not an answer and is not swallowed: an
    unreadable or colliding failure record is an integrity problem in its own
    right, and `observation_of` raises it rather than letting this pass
    conclude that nothing was recorded.
    """
    observed = delegation.observation_of(operations, attempt, job)
    return (observed["start_failure"] is not None
            or observed["preparation_failure"] is not None)


def apply_offer_state(store, event):
    """Record what one canonical `offer.state` assertion means for this store.

    THE ONLY EFFECT AN ASSERTION CAN HAVE IS ENDING AN EPISODE, and it is
    worth being exact about why that is enough. A live offer -- `issued` or
    `accepted` -- tells this store nothing it does not already derive from its
    own receipts and the canonical observation it takes at projection time. An
    offer that will never produce a claim is the one fact it cannot derive,
    because the thing it would have derived it from is the offer that is now
    over.

    A TERMINAL OFFER IS NOT A TERMINAL STAGE. `claimed` is terminal for the
    offer and is the ending that means the stage is RUNNING, so it ends no
    episode here: the attempt that offer froze is the one the projection goes
    on observing. Review [P1, 2026-09-03] measured what treating the offer's
    whole terminal set as episode endings did -- a claimed stage came back
    `exceptional` with its identities cleared at the next restart. The set that
    ends an execution is `documents.EPISODE_ENDINGS`, and it is not
    `events.TERMINAL_OFFER_STATES`.

    IDEMPOTENT THREE TIMES OVER, because at-least-once delivery means the same
    assertion arrives again after a restart, after a reconnect, and on any
    republication. An assertion about an offer this store never asked for is
    silence; an assertion that the offer is still live has no effect; and an
    episode that has already recorded an ending keeps the one it recorded. The
    journalled `episode.end` identity is the fourth: two callers applying one
    assertion concurrently commit one row and replay it.

    A STALE ASSERTION CANNOT REGRESS ANYTHING. Revisions are monotone over the
    canonical lifecycle, so an older one is by construction either about a live
    state -- no effect -- or not greater than the ending already recorded, and
    an already-ended episode is never re-ended. The replacement episode is a
    different row with a different offer id, so no assertion about the ended
    offer can reach it at all.

    Answers the episode it ended, or `None` when the assertion changed nothing.
    """
    taken = boundaries.document(event, "an offer state assertion",
                                required=events.OFFER_STATE_MEMBERS)
    offer_id = boundaries.identity(taken["offer_id"], "an offer id")
    state = boundaries.text(taken["state"], "a canonical offer state")
    revision = events.offer_state_revision(state)
    if taken["revision"] != revision:
        raise ContractRefusal(
            "integrity", "schema",
            f"the assertion about {name_value(offer_id)} carries revision "
            f"{name_value(taken['revision'])} and this build ranks "
            f"{name_value(state)} at {revision}; a revision that does not "
            f"follow from the state it travels with cannot order anything")
    episode = episodes.episode_by_offer(store, offer_id)
    if episode is None:
        return None
    if episode["attempt_id"] != taken["attempt_id"]:
        raise ContractRefusal(
            "refused", "operation-collision",
            f"the assertion about {name_value(offer_id)} names attempt "
            f"{name_value(taken['attempt_id'])} and episode "
            f"{episode['episode']} of stage "
            f"{name_value(episode['stage_id'])} asked for "
            f"{name_value(episode['attempt_id'])}; one offer froze one "
            f"attempt, and applying this would record an ending for an "
            f"execution this store never asked for")
    if state not in documents.EPISODE_ENDINGS:
        return None
    if episode["ended_state"] is not None:
        # THE SAME ENDING AGAIN IS THE ORDINARY CASE and answers "nothing
        # changed". A DIFFERENT one is not ignorable: one offer reaches one
        # ending, so two would mean this store and the publisher disagree
        # about which offer this episode asked for, and quietly keeping the
        # first would be deciding that disagreement by arrival order.
        if episode["ended_state"] != state:
            raise ContractRefusal(
                "refused", "operation-collision",
                f"episode {episode['episode']} of stage "
                f"{name_value(episode['stage_id'])} recorded "
                f"{name_value(episode['ended_state'])} and this assertion "
                f"about {name_value(offer_id)} says {name_value(state)}; one "
                f"offer reaches one ending, so keeping the first by arrival "
                f"order would be deciding a disagreement rather than "
                f"reporting it")
        return None
    return episodes.end_episode(store, episode, state, revision)


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
        attempt = entry["attempt"]
        # A stage between an ending and its replacement has no identities to
        # reconcile against. Its ended episode's acts were adopted while it
        # was live, and asking the journal about them again would be adopting
        # a finished attempt's receipts onto a stage that has moved on.
        if attempt is None:
            continue
        job = submission.job_of(store, attempt["job_id"])
        for act in documents.ACTS:
            if act in entry["receipts"]:
                continue
            operation_id = operations.canonical_operation(
                act, attempt["offer_id"])
            record = _proved(operations, operation_id, attempt, job)
            if record is None:
                continue
            state = "refused" if record["state"] == "refused" else "adopted"
            _record(store, {"stage_id": stage_id, "act": act,
                            "episode": attempt["episode"]}, record, state)
            adopted.append(documents.reconciliation(
                stage_id=stage_id, episode=attempt["episode"], act=act,
                outcome=state, operation_id=operation_id))
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
                    stage_id=owed["stage_id"], episode=owed["episode"],
                    act=owed["act"], outcome="deferred",
                    operation_id=canonical_id, detail=deferred)
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
        stage_id=owed["stage_id"], episode=owed["episode"], act=owed["act"],
        outcome=state, operation_id=canonical_id)


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
    episode = owed["episode"]
    operation_id = record["operation_id"]
    signature = job_signature(_RECEIPT_KIND,
                              {"stage_id": stage_id, "episode": episode,
                               "act": act, "operation_id": operation_id})
    detail = {"canonical_state": record["state"],
              "settled_at": record["settled_at"],
              "result": json.loads(record["result"])
              if record["result"] is not None else None,
              "refusal": json.loads(record["refusal"])
              if record["refusal"] is not None else None}

    def perform(connection):
        recorded_at = store._now()
        connection.execute(
            "INSERT INTO receipts (stage_id, episode, act, operation_id, "
            "state, detail, recorded_at, incarnation) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (stage_id, episode, act, operation_id, state,
             json.dumps(detail, sort_keys=True, ensure_ascii=False),
             recorded_at, store.incarnation))
        return documents.receipt(
            stage_id=stage_id, episode=episode, act=act,
            operation_id=operation_id, state=state, recorded_at=recorded_at,
            detail=detail)

    return store.transact(receipt_operation_id(stage_id, episode, act),
                          _RECEIPT_KIND, signature, perform)
