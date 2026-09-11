"""One stage's successive attempts at being admitted, append-only.

W73629. WHY A STAGE NEEDED MORE THAN ONE. Schema 1 derived exactly one offer
and one attempt from the stage id, which was right for everything that could
happen to a stage while it stayed the same stage. Then a restart happened: the
Worker Manager abandons an `issued` offer minted by a previous incarnation --
correctly, because nothing durable proves its bearer was delivered -- and this
control plane went on holding that stage's `admit` receipt, projecting
`offered`, and owing a `claim` against an offer that had ended. One derived
identity per stage left nowhere to put the second try, so the stage stayed
wedged forever.

AN EPISODE IS THAT SECOND TRY, AND THE FIRST ONE IS ALSO AN EPISODE. Each one
carries its own offer id, its own attempt id and its own receipts, and it ends
exactly once, with the canonical state that ended it. Nothing is rewritten and
nothing is deleted: the abandoned episode keeps its identities and its `admit`
receipt, the replacement is a NEW row, and a status reader can see both. That
is the difference between recovering a stage and pretending the failure did
not happen.

IDENTITIES ARE STORED, NOT RE-DERIVED. The derivation below is used once, when
an episode is opened, and the row is what every later reader asks. A schema-1
migration therefore keeps the plain `offer:{stage_id}` identity already used
by that store, while a newly submitted stage starts with a bounded identity
the worker contract can carry. A restart reconciles the identity actually
stored on the episode, never one recomputed from a newer rule.

WHAT DECIDES "AT MOST ONE REPLACEMENT". Not this module: the partial unique
index `episodes_one_live_per_stage`, plus the journalled operation identity
below, which is derived from the stage and the episode NUMBER. Two managers
that both see one abandoned episode 1 both compute `episode.open:...:2`, and
one of them replays the other's committed result instead of opening a third
row. A duplicate abandonment notice cannot mint a second offer for the same
reason, in whatever order it arrives.
"""

from ..contracts import ContractRefusal, digest
from ..contracts.errors import name_value
from ..worker_manager import boundaries
from . import documents, schema
from .store import job_signature

__all__ = ["CORRECT_KIND", "CORRECTION_DISPOSITION", "EXCLUSION_ENDING",
           "OPEN_KIND", "END_KIND", "RESTART_KIND",
           "advance_correction", "attempting", "correction_operation_id",
           "end_episode", "episode_by_offer", "episode_of", "episodes_of",
           "identities", "live_of", "open_next", "open_first",
           "restart_abandoned_correction", "restart_operation_id"]

OPEN_KIND = "episode.open"
END_KIND = "episode.end"
# W103076. One Job's implementation and review stages leaving their current
# episodes together and receiving their successors together, as ONE act.
CORRECT_KIND = "episode.correct"
# W128698. One live implementation episode ending because an operator declared
# its attempt abandoned and the two accepted providers proved the exclusion.
RESTART_KIND = "episode.restart-abandoned"
EXCLUSION_ENDING = documents.EXCLUSION_ENDINGS[0]


def open_operation_id(stage_id, episode):
    return f"{OPEN_KIND}:{stage_id}:{episode}"


def end_operation_id(stage_id, episode):
    return f"{END_KIND}:{stage_id}:{episode}"


def identities(authority_uuid, stage_id, episode):
    """The offer and attempt ids one new episode is opened with.

    THE ROW PRESERVES OLD IDENTITIES; THIS DERIVATION DOES NOT REWRITE THEM.
    Schema-1 migration copies the offer and attempt names already stored on
    each stage into episode 1, so its journal references remain exact. New
    episodes need identities the worker contract can actually carry: stage ids
    contain `/`, while its bounded `opaqueId` grammar deliberately does not.
    A canonical digest keeps the derivation stable and bounded without
    interpreting any value as path or protocol syntax.

    W83781: AND THE DIGEST IS TAKEN IN AN AUTHORITY'S NAMESPACE, because
    without one it was not a namespace at all. `stage_id` and `episode` are
    both LOCAL to one Job store, so two independent authorities running a
    stage with the same local name derived the same offer and attempt -- and a
    fresh authority's first episode was measured deriving
    `attempt-1851504c...`, already held by a retained container belonging to a
    different Authority and a different Work. The adapter refused to adopt
    that container, correctly and fail-closed, and that refusal is not the
    defect: the defect is handing the adapter an identity that two strangers
    can both produce.

    THE NAMESPACE IS AN EXPLICIT STABLE IDENTITY AND NOTHING ELSE. Not the
    database path, the process incarnation, the hostname, the clock or a retry
    counter -- every one of those is either deployment-local (so two hosts
    collide again) or unstable (so a retry stops replaying). The Authority UUID
    is globally unique, is already the label an OCI runtime carries, and is
    persisted on the store precisely so both episode-opening paths derive from
    the same value.

    REPLAY IS UNCHANGED WITHIN ONE AUTHORITY. The same triple gives the same
    pair every time, so a restart still finds the identity it committed under.
    """
    schema.check_authority(authority_uuid, what="an episode's Authority")
    boundaries.identity(stage_id, "a stage id")
    if type(episode) is not int or episode < 1:
        raise ContractRefusal(
            "integrity", "schema",
            f"a stage episode is a whole number from 1; this is "
            f"{name_value(episode)}")
    identity = digest({"authority_uuid": authority_uuid,
                       "stage_id": stage_id, "episode": episode})[
        len("sha256:"):]
    return f"offer-{identity}", f"attempt-{identity}"


def attempting(stage, episode):
    """One stage row and the episode currently answering for it, as one view.

    THE SEAM READS `offer_id` AND `attempt_id` OFF A STAGE, and this is what
    it now reads them off. Merging here rather than passing two objects keeps
    the intent proof, the canonical observation and the delegated calls looking
    at ONE thing -- a stage as it is being attempted right now -- instead of
    letting a caller pair a stage with somebody else's episode.
    """
    held = dict(stage)
    held["episode"] = episode["episode"]
    held["offer_id"] = episode["offer_id"]
    held["attempt_id"] = episode["attempt_id"]
    return held


# -- the owned reads ---------------------------------------------------------


def episodes_of(store, stage_id):
    """Every episode of one stage, oldest first."""
    boundaries.identity(stage_id, "a stage id")
    return [boundaries.row(record, "a persisted stage episode",
                           schema.EPISODE_COLUMNS)
            for record in store._connection.execute(
                "SELECT * FROM episodes WHERE stage_id = ? ORDER BY episode",
                (stage_id,)).fetchall()]


def episode_of(store, stage_id, episode):
    boundaries.identity(stage_id, "a stage id")
    found = store._connection.execute(
        "SELECT * FROM episodes WHERE stage_id = ? AND episode = ?",
        (stage_id, episode)).fetchone()
    if found is None:
        return None
    return boundaries.row(found, "a persisted stage episode",
                          schema.EPISODE_COLUMNS)


def live_of(store, stage_id):
    """The one episode currently answering for this stage, or absence.

    Absence is an ordinary state and not a fault: it is exactly what a stage
    whose episode has just ended looks like, in the window before its
    replacement is opened, and it is how the sweep knows a replacement is owed.
    """
    boundaries.identity(stage_id, "a stage id")
    found = store._connection.execute(
        "SELECT * FROM episodes WHERE stage_id = ? AND ended_state IS NULL",
        (stage_id,)).fetchall()
    if not found:
        return None
    if len(found) > 1:
        # The partial unique index makes this impossible going forward; a
        # store written before it must fail closed, because "which of these is
        # the stage's current attempt" has no answer row order may invent.
        raise ContractRefusal(
            "integrity", "schema",
            f"stage {name_value(stage_id)} has {len(found)} live episodes; "
            f"one stage is attempted one way at a time, and choosing between "
            f"them by row order would be inventing which offer is its own")
    return boundaries.row(found[0], "a persisted stage episode",
                          schema.EPISODE_COLUMNS)


def episode_by_offer(store, offer_id):
    """The episode that asked for one offer, or absence.

    ABSENCE IS THE ORDINARY ANSWER for most offers a publisher asserts about:
    a control store may carry other Job stores' offers, and an assertion about
    one of those is simply not this store's business. Refusing it would make a
    consumer's resynchronization fail on somebody else's row.
    """
    boundaries.identity(offer_id, "an offer id")
    found = store._connection.execute(
        "SELECT * FROM episodes WHERE offer_id = ?", (offer_id,)).fetchone()
    if found is None:
        return None
    return boundaries.row(found, "a persisted stage episode",
                          schema.EPISODE_COLUMNS)


# -- the journalled acts -----------------------------------------------------


def open_first(connection, store, stage_id, recorded_at):
    """Episode 1, written INSIDE the submission's own transaction.

    Not journalled separately, because it is not a separate act: a stage and
    its first episode are recorded by one submission, and a store holding the
    stage without the episode would be a stage nothing could ever admit. It
    takes the caller's connection for exactly that reason.

    W83781: THE NAMESPACE COMES FROM THE ALREADY-OPEN STORE, and both
    episode-opening paths take it from the same place. This one runs inside
    `submit`, before any deployment operations factory exists, so a namespace
    threaded through the production factory would arrive too late for episode
    1 and the two paths would be deriving from different inputs -- which is a
    second way for one stage's identities to disagree with themselves.
    """
    offer_id, attempt_id = identities(store.authority_uuid, stage_id, 1)
    connection.execute(
        "INSERT INTO episodes (stage_id, episode, offer_id, attempt_id, "
        "opened_at, incarnation) VALUES (?, ?, ?, ?, ?, ?)",
        (stage_id, 1, offer_id, attempt_id, recorded_at, store.incarnation))
    return documents.stage_episode(
        stage_id=stage_id, episode=1, offer_id=offer_id,
        attempt_id=attempt_id, opened_at=recorded_at,
        incarnation=store.incarnation, ended_state=None, ended_revision=None,
        ended_at=None)


def open_next(store, stage_id, ended):
    """Open the replacement for one ENDED episode, effectively once.

    The operation identity is derived from the stage and the successor's
    NUMBER, so two managers reconciling one abandoned episode agree on what
    they are opening and the second replays the first's result. The partial
    unique index is the other half: if anything else has already opened a live
    episode for this stage, the insert refuses rather than making the stage
    ambiguous.
    """
    if ended["ended_state"] is None:
        raise ContractRefusal(
            "refused", "precondition",
            f"episode {ended['episode']} of stage "
            f"{name_value(ended['stage_id'])} has not ended; a replacement is "
            f"owed by an ending and never by a live attempt")
    episode = ended["episode"] + 1
    offer_id, attempt_id = identities(store.authority_uuid, stage_id, episode)
    operands = {"stage_id": stage_id, "episode": episode,
                "offer_id": offer_id, "attempt_id": attempt_id,
                "replaces": ended["ended_state"]}
    signature = job_signature(OPEN_KIND, operands)

    def act(connection):
        opened_at = store._now()
        connection.execute(
            "INSERT INTO episodes (stage_id, episode, offer_id, attempt_id, "
            "opened_at, incarnation) VALUES (?, ?, ?, ?, ?, ?)",
            (stage_id, episode, offer_id, attempt_id, opened_at,
             store.incarnation))
        return documents.stage_episode(
            stage_id=stage_id, episode=episode, offer_id=offer_id,
            attempt_id=attempt_id, opened_at=opened_at,
            incarnation=store.incarnation, ended_state=None,
            ended_revision=None, ended_at=None)

    return store.transact(open_operation_id(stage_id, episode), OPEN_KIND,
                          signature, act)


def end_episode(store, episode, state, revision):
    """Record the ONE canonical ending an episode was observed to reach.

    IDEMPOTENT BY IDENTITY, which is what makes republication free. The
    operation is named by the stage and the episode, and its signature carries
    the state and the revision -- so the same assertion delivered twice, or
    after a restart, or on a timer, replays the first outcome and writes
    nothing. A DIFFERENT ending for one episode would collide instead, which is
    the honest answer: an offer reaches one ending, so two would mean the
    publisher and this store disagree about which offer this is.

    The row is updated only while it is still live. That guard is not a second
    idempotence mechanism -- the journal already provides one -- it is what
    keeps an ending from overwriting an ending if the two ever did disagree.
    """
    stage_id = episode["stage_id"]
    number = episode["episode"]
    operands = {"stage_id": stage_id, "episode": number, "state": state,
                "revision": revision}
    signature = job_signature(END_KIND, operands)

    def act(connection):
        ended_at = store._now()
        changed = connection.execute(
            "UPDATE episodes SET ended_state = ?, ended_revision = ?, "
            "ended_at = ? WHERE stage_id = ? AND episode = ? "
            "AND ended_state IS NULL",
            (state, revision, ended_at, stage_id, number)).rowcount
        if changed != 1:
            raise ContractRefusal(
                "refused", "precondition",
                f"episode {number} of stage {name_value(stage_id)} has "
                f"already recorded an ending; an episode ends once and this "
                f"store does not rewrite what it observed",
                durable=True)
        return documents.stage_episode(
            stage_id=stage_id, episode=number, offer_id=episode["offer_id"],
            attempt_id=episode["attempt_id"], opened_at=episode["opened_at"],
            incarnation=episode["incarnation"], ended_state=state,
            ended_revision=revision, ended_at=ended_at)

    return store.transact(end_operation_id(stage_id, number), END_KIND,
                          signature, act)


# -- the correction cycle ----------------------------------------------------
#
# W103076. WHY THIS ACT HAD TO EXIST AT ALL. A review that asks for changes is
# the ordinary outcome of reviewing, and until now it was terminal here:
# `changes-requested` projects, nothing is owed, and the stage stops. The only
# path to a second episode was `REPLACEABLE_ENDINGS`, which has one member and
# means "an offer was abandoned before anybody decided anything". A completed
# round of work that a reviewer read and sent back is the opposite of that.
#
# So the correction is a NAMED ACT rather than a re-offer, and what it names is
# a pair. The implementation stage and the review stage of one Job advance
# together or not at all: ending only the implementation stage would leave a
# review episode holding a verdict about a checkpoint the next writer is about
# to supersede, and ending only the review stage would ask a reviewer to look
# again at work nobody was asked to redo.
#
# IT IS ONE TRANSACTION AND ONE JOURNAL ROW, WHICH IS WHY IT DOES NOT COMPOSE
# `end_episode` AND `open_next`. Those are four separately journalled
# operations, and every window between them is a durable state this control
# plane cannot describe: a stage with no live episode that no ending made
# replaceable, or one Job with its implementation on round two and its review
# still holding round one's verdict. A crash inside this act commits nothing;
# a crash after it finds four rows and one committed operation.
#
# AND IT COPIES NO CUSTODY STATE. The line, the checkpoint and the verdict are
# read through the Worker Manager's own accepted readers and journal, and are
# recorded in this act's SIGNATURE rather than in a table. The Job store learns
# that a correction round was authorized and by which evidence; what a
# checkpoint is, what fenced it and what a verdict binds stay in the store that
# owns them.
#
# WHAT THE FIRST ROUND OF REVIEW CHANGED, and all three were the same mistake
# in different places: the act BELIEVED ITS CALLER. It took a verdict identity
# and only checked its shape, it took stage documents and never re-read the
# rows they claimed to be, and it proved the allocation precondition outside
# the transaction that relied on it. Every operand it acts on is now either
# re-read from a store or proved against an owner's committed record.

CORRECTION_ENDING = documents.CORRECTION_ENDINGS[0]

# The allocation states that still hold a worker. `released` does not: a
# released allocation is history, exactly as an ended episode is.
_HOLDING = ("reserved", "recovery-required")

# The one verdict disposition that asks for another round. The other two are
# decisions this act must not act on, and the accepted provider owns the
# vocabulary they come from.
CORRECTION_DISPOSITION = "changes-requested"

def correction_operation_id(job_id, checkpoint_id):
    """The identity one correction round commits under.

    DERIVED FROM THE CHECKPOINT BEING CORRECTED, and the two spellings before
    this one are worth keeping because each was wrong in a different way.

    The first named the two episode NUMBERS the round was leaving. That is
    stable for exactly as long as the act has not committed: the moment it
    has, those stages are on their successors, so an exact retry computed a
    different name and opened a THIRD round. A retry that advances the
    pipeline is not a retry, and its own test caught it.

    The second named the VERDICT, which does not move -- but a caller
    presenting any other verdict identity got a different name and a second
    round on the same checkpoint, because a line stays `correction-ready`
    from the verdict until its next writer is granted. The act was not
    protecting the thing it was about.

    THE CHECKPOINT IS WHAT A ROUND IS ABOUT, and unlike the verdict it is
    PROVED here rather than merely carried: the line must be corrected from
    exactly this frozen checkpoint. One checkpoint earns one correction round,
    so an exact retry replays it and any other operand collides on the journal
    instead of advancing stages it was never authorized for.
    """
    return f"{CORRECT_KIND}:{job_id}:{checkpoint_id}"


def _stored_pair(store, job_id):
    """This Job's two stages, READ FROM THIS STORE rather than accepted.

    REVIEW [P0]: the act used to take two stage documents and read `stage_id`,
    `kind`, `job_id` and `work_id` off them without ever asking the store what
    those rows actually say. Mutating a real document's Job, Work or kind made
    the preflight treat two unrelated stored stages as one pair, and the
    transaction then ended and reopened exactly the stage ids it had been
    handed. A caller cannot cross-wire what it does not choose, so it names the
    JOB and this reads the pair.
    """
    from . import submission
    boundaries.identity(job_id, "a Job identity")
    found = {}
    for row in submission.stages_of(store, job_id):
        if row["kind"] in ("implementation", "review"):
            if row["kind"] in found:
                raise ContractRefusal(
                    "integrity", "schema",
                    f"Job {name_value(job_id)} carries two {row['kind']} "
                    f"stages; a correction round advances one of each")
            found[row["kind"]] = row
    missing = [kind for kind in ("implementation", "review")
               if kind not in found]
    if missing:
        raise ContractRefusal(
            "refused", "precondition",
            f"Job {name_value(job_id)} has no {' or '.join(missing)} stage; a "
            f"correction round is a pair and this Job is not one")
    # THE SAME WORK, AND THE LINE PROVIDER IS WHY. A line is one
    # `(authority_uuid, work_id)` pair, its writer and its reviewer are
    # assignments of that Work, and `attach_review` binds the reviewer to the
    # SAME Work as the writer. Two stages naming unrelated Works can be
    # submitted and scheduled and can never be attached, so this refuses before
    # an offer rather than after a launch.
    if found["implementation"]["work_id"] != found["review"]["work_id"]:
        raise ContractRefusal(
            "refused", "precondition",
            f"Job {name_value(job_id)} implements "
            f"{name_value(found['implementation']['work_id'])} and reviews "
            f"{name_value(found['review']['work_id'])}; one development line "
            f"carries one Work, so these stages could never have been attached")
    return found


def _live_episode(store, stage, what):
    live = live_of(store, stage["stage_id"])
    if live is None:
        raise ContractRefusal(
            "refused", "precondition",
            f"stage {name_value(stage['stage_id'])} has no live episode, so "
            f"there is no {what} round to correct; a correction advances the "
            f"attempt that is answering now")
    return live


def _unheld(store, episode, what):
    """Refuse while a worker is still allocated to the episode being ended.

    An allocation is capacity somebody is holding. Opening the successor while
    the predecessor's reservation is live would let one Job hold two workers in
    one lane on the strength of a round that is over -- and the release is the
    scheduler's act, not this one's, so the honest answer is to refuse until it
    has happened rather than to release on the scheduler's behalf.

    REVIEW [P0]: THIS IS ASKED TWICE, and the second time is the one that
    counts. The preflight ran before `transact` took its write lock, so a
    reservation committed in between survived while both successors opened.
    The transaction repeats it, so the precondition holds at the moment the
    rows are written rather than shortly before.
    """
    from . import scheduler
    held = scheduler.allocation_of(store, episode["attempt_id"])
    if held is not None and held["allocation_state"] in _HOLDING:
        raise ContractRefusal(
            "refused", "precondition",
            f"the {what} episode's allocation "
            f"{name_value(held['assignment_id'])} is still "
            f"{name_value(held['allocation_state'])}; a correction round opens "
            f"after the round it replaces has released its worker")


def _proved_verdict(custody, verdict_id, *, line_id, checkpoint_id,
                    authority_uuid, work_id):
    """The verdict that authorized this round, read from the OWNER'S READER.

    REVIEW [P0], TWICE. It first took an identity and checked only its shape,
    so the first correction of any checkpoint accepted `verdict-somebody-elses`
    and persisted it. It then compared a caller-supplied document against a
    generic journal row -- which proved the document had been committed, but
    did so by reconstructing this provider's operation identity and parsing its
    journal shape here. That is a second account of something only the provider
    gets to change.

    `review_cycles.verdict_of` is the provider's own typed read, and it
    cross-binds the materialized verdict row against the act that recorded it.
    What is left here is the only question this leaf is entitled to ask: is the
    verdict it resolved the one that asks THIS Job for another round.
    """
    from ..worker_manager import review_cycles
    boundaries.identity(verdict_id, "a checkpoint verdict identity")
    verdict = review_cycles.verdict_of(custody, verdict_id)
    if verdict["disposition"] != CORRECTION_DISPOSITION:
        raise ContractRefusal(
            "refused", "precondition",
            f"verdict {name_value(verdict_id)} is "
            f"{name_value(verdict['disposition'])}; only "
            f"{name_value(CORRECTION_DISPOSITION)} asks for another round")
    if verdict["line_id"] != line_id \
            or verdict["checkpoint_id"] != checkpoint_id \
            or verdict["authority_uuid"] != authority_uuid \
            or verdict["work_id"] != work_id:
        raise ContractRefusal(
            "refused", "precondition",
            f"verdict {name_value(verdict_id)} was recorded about another "
            f"line, checkpoint, Authority or Work than the one this correction "
            f"names")
    return verdict


def _corrected_line(custody, verdict, *, line_id, checkpoint_id,
                    authority_uuid, work_id):
    """The custody proof, read through the accepted line provider only.

    WHAT IS PROVED HERE. `line_of` answers `correction-ready` for exactly one
    reason: `record_verdict` recorded a `changes-requested` disposition against
    the line's current checkpoint and moved it there. So a line that is
    `correction-ready` and whose `current_checkpoint_id` is the named frozen
    checkpoint IS the statement that this checkpoint's review asked for
    changes -- read from the owner's rows, through the owner's readers, with no
    copy of the verdict table on this side.

    AND THE PROVED VERDICT IS TIED TO THAT SAME LINE AND CHECKPOINT, which is
    what makes the two proofs one proof rather than two coincidences.

    THE AUTHORITY AND WORK ARE PROVED TOO, because a line is keyed by
    `(authority_uuid, work_id)` and a Job store is bound to one Authority. A
    correction that advanced this Job's stages on the strength of another
    Work's line would be the same class of defect as adopting another store's
    offer.
    """
    from ..worker_manager import review_cycles
    line = review_cycles.line_of(custody, line_id)
    if line["authority_uuid"] != authority_uuid \
            or line["work_id"] != work_id:
        raise ContractRefusal(
            "refused", "precondition",
            f"development line {name_value(line_id)} belongs to "
            f"{name_value(line['work_id'])} under another Authority or Work; "
            f"this correction is for {name_value(work_id)}")
    if line["state"] != "correction-ready":
        raise ContractRefusal(
            "refused", "precondition",
            f"development line {name_value(line_id)} is "
            f"{name_value(line['state'])}; a correction round follows a "
            f"recorded changes-requested verdict and nothing else")
    if line["current_checkpoint_id"] != checkpoint_id:
        raise ContractRefusal(
            "refused", "precondition",
            f"development line {name_value(line_id)} is corrected from "
            f"{name_value(line['current_checkpoint_id'])} and not from "
            f"{name_value(checkpoint_id)}")
    checkpoint = review_cycles.checkpoint_of(custody, checkpoint_id)
    if checkpoint["line_id"] != line_id or checkpoint["state"] != "frozen":
        raise ContractRefusal(
            "integrity", "schema",
            f"checkpoint {name_value(checkpoint_id)} is not this line's frozen "
            f"checkpoint")
    return line, checkpoint


def advance_correction(store, custody, *, job_id, line_id, checkpoint_id,
                       verdict_id):
    """End one Job's implementation and review episodes and open both successors.

    `job_id` names the Job; the two stages and the episodes that advance are
    READ FROM THIS STORE, which is what keeps a caller from pairing stages that
    are not a pair. `custody` is the Worker Manager control store that owns the
    development line, and every fact about the line, the checkpoint and the
    verdict is read through that owner's own typed readers.

    WHAT THE SUCCESSORS ARE, AND WHAT THEY ARE NOT. Two fresh episodes with
    fresh offer and attempt identities, opened by the same derivation every
    other episode uses. No receipt, claim, runtime, checkpoint or verdict is
    carried across: the new implementation episode has never been offered, and
    that is precisely what lets the ordinary sweep offer it. The projection
    then does the rest on its own -- the implementation stage falls back to
    `queued`, and the review stage's gate closes again because its dependency
    is no longer `completed`.
    """
    boundaries.identity(line_id, "a development line identity")
    boundaries.identity(checkpoint_id, "a line checkpoint identity")
    stages = _stored_pair(store, job_id)
    work_id = stages["implementation"]["work_id"]

    # THE SIGNATURE IS THE AUTHORIZATION, NOT THE OUTCOME, and the first
    # spelling had that backwards. It carried the episode numbers the round
    # was leaving and the identities it was opening -- both of which have
    # MOVED by the time an exact retry asks, so the retry computed a different
    # signature under the same identity and collided with its own committed
    # work. What authorizes a round is which Job, which Work, which line,
    # which checkpoint and which verdict; what the round DID is the journalled
    # result, and replaying that is what returns the same successors.
    proved = _proved_verdict(custody, verdict_id, line_id=line_id,
                             checkpoint_id=checkpoint_id,
                             authority_uuid=store.authority_uuid,
                             work_id=work_id)
    operands = {"job_id": job_id, "work_id": work_id, "line_id": line_id,
                "checkpoint_id": checkpoint_id,
                "verdict_id": proved["verdict_id"],
                "attachment_id": proved["attachment_id"]}
    signature = job_signature(CORRECT_KIND, operands)
    operation_id = correction_operation_id(job_id, checkpoint_id)
    # ASKED BEFORE THE PRECONDITIONS, because every one of them is about the
    # round this act would OPEN. A committed round has already moved the
    # stages past them, so proving them first would refuse the retry for
    # having succeeded.
    found, recorded = store.replay(operation_id, signature, kind=CORRECT_KIND)
    if found:
        return recorded

    first = _live_episode(store, stages["implementation"], "implementation")
    second = _live_episode(store, stages["review"], "review")
    _corrected_line(custody, proved, line_id=line_id,
                    checkpoint_id=checkpoint_id,
                    authority_uuid=store.authority_uuid, work_id=work_id)
    _unheld(store, first, "implementation")
    _unheld(store, second, "review")

    rounds = {}
    for kind, episode in (("implementation", first), ("review", second)):
        number = episode["episode"] + 1
        offer_id, attempt_id = identities(store.authority_uuid,
                                          stages[kind]["stage_id"], number)
        rounds[kind] = {"stage_id": stages[kind]["stage_id"],
                        "ended_episode": episode["episode"],
                        "episode": number, "offer_id": offer_id,
                        "attempt_id": attempt_id}

    def act(connection):
        now = store._now()
        opened = {}
        # EVERY GUARD FOR THE WHOLE PAIR, BEFORE THE FIRST ROW MOVES. Review
        # [P0]: this used to guard and mutate one stage at a time, and the
        # guard raised a DURABLE refusal -- which `transact` commits without
        # rolling the act's savepoint back. A review episode that had ended at
        # the cutpoint therefore left the implementation stage superseded with
        # a live successor and the review stage untouched: half a correction,
        # recorded, from an act whose whole premise is both or neither.
        #
        # Two things fix it and both are kept. Nothing is written until every
        # stage has passed every check, and the refusals below are ORDINARY
        # rather than durable, so a guard that fires after a partial write
        # still unwinds the savepoint instead of sealing it.
        for kind in ("implementation", "review"):
            round = rounds[kind]
            live = episode_of(store, round["stage_id"],
                              round["ended_episode"])
            if live is None or live["ended_state"] is not None:
                raise ContractRefusal(
                    "refused", "precondition",
                    f"episode {round['ended_episode']} of stage "
                    f"{name_value(round['stage_id'])} is no longer the live "
                    f"one; a correction round advances the pair it observed")
            # THE ALLOCATION PROOF, REPEATED UNDER THE WRITE LOCK. The
            # preflight above answers the ordinary case cheaply, and this is
            # the one that decides -- a reservation committed between them
            # would otherwise survive while both successors opened.
            _unheld(store, live, kind)
        for kind in ("implementation", "review"):
            round = rounds[kind]
            # THE ENDING IS STILL GUARDED BY ITS OWN LIVENESS, in the same
            # statement that performs it. The checks above ran under this
            # transaction's lock, so this cannot fire -- and it stays because a
            # write whose precondition is only checked somewhere else is a
            # write nobody is guarding.
            changed = connection.execute(
                "UPDATE episodes SET ended_state = ?, ended_revision = ?, "
                "ended_at = ? WHERE stage_id = ? AND episode = ? "
                "AND ended_state IS NULL",
                (CORRECTION_ENDING, round["episode"], now, round["stage_id"],
                 round["ended_episode"])).rowcount
            if changed != 1:
                raise ContractRefusal(
                    "refused", "precondition",
                    f"episode {round['ended_episode']} of stage "
                    f"{name_value(round['stage_id'])} stopped being live "
                    f"inside this transaction; a correction round advances the "
                    f"pair it observed")
            connection.execute(
                "INSERT INTO episodes (stage_id, episode, offer_id, "
                "attempt_id, opened_at, incarnation) VALUES (?, ?, ?, ?, ?, ?)",
                (round["stage_id"], round["episode"], round["offer_id"],
                 round["attempt_id"], now, store.incarnation))
            opened[kind] = documents.stage_episode(
                stage_id=round["stage_id"], episode=round["episode"],
                offer_id=round["offer_id"], attempt_id=round["attempt_id"],
                opened_at=now, incarnation=store.incarnation,
                ended_state=None, ended_revision=None, ended_at=None)
        return documents.correction(
            job_id=job_id, work_id=work_id, line_id=line_id,
            checkpoint_id=checkpoint_id, verdict_id=proved["verdict_id"],
            corrected_at=now,
            ended={kind: rounds[kind]["ended_episode"]
                   for kind in ("implementation", "review")},
            implementation=opened["implementation"], review=opened["review"])

    return store.transact(operation_id, CORRECT_KIND, signature, act)


# -- the explicit abandonment recovery ---------------------------------------


def restart_operation_id(attempt_id, generation):
    """The identity one abandoned correction's recovery commits under.

    DERIVED FROM THE ATTEMPT AND ITS FENCED GENERATION, and neither moves.
    `correction_operation_id`'s two wrong spellings are the argument: naming
    the episode NUMBERS was stable only until the act committed, and naming a
    caller-chosen identity let any other one open a second round. The attempt
    and the generation are what an abandonment IS about, they are fixed before
    this act runs, and they are still the same values after the ordinary sweep
    has opened the successor -- which is exactly what an exact replay needs.
    """
    return f"{RESTART_KIND}:{attempt_id}:{generation}"


def _excluded_correction(custody, attempt_id, generation, what):
    """A's and B's accepted receipts, cross-bound to each other.

    THROUGH THEIR PUBLIC READERS AND NOTHING ELSE. Both providers validate
    their own records whole on their own side -- the declaration, the fence,
    the removal's positive absence, the gate discharge, the historical writer,
    the retained checkpoint and the changes-requested verdict. No private
    helper of theirs is called and no table of theirs is read here; what is
    left for this leaf is the crossing.
    """
    from ..worker_manager import intake, review_cycles

    prepared = review_cycles.abandoned_correction_of(
        custody, attempt_id=attempt_id, generation=generation)
    if prepared is None:
        raise ContractRefusal(
            "refused", "precondition",
            f"{what} has no completed abandoned-correction recovery; an "
            f"episode is replaced after the checkout has been restored and "
            f"the old writer excluded, and never before")
    discharge = intake.abandoned_gate_discharge_of(custody, attempt_id)
    if discharge is None:
        raise ContractRefusal(
            "refused", "precondition",
            f"{what}'s abandonment has not discharged its runtime-quiescence "
            f"gate; a successor cannot be assigned while the generation is "
            f"still held at the authority")
    # THE TWO RECEIPTS DESCRIBE ONE ACT, or they describe two and this leaf
    # has no tie-break. `cleanup_operation` carries the identity AND the
    # signature, and the signature is the half that names the runtime.
    if prepared["discharge_operation_id"] != discharge["operation_id"] \
            or prepared["assignment"] != discharge["assignment"] \
            or prepared["runtime_id"] != discharge["runtime_id"] \
            or prepared["cleanup_operation"] != discharge["cleanup_operation"]:
        raise ContractRefusal(
            "integrity", "schema",
            f"{what}'s restored correction and its committed gate discharge do "
            f"not describe one abandonment")
    if prepared["assignment"]["generation"] != generation:
        raise ContractRefusal(
            "stale-assignment", "generation",
            f"{what}'s recovery is for generation "
            f"{prepared['assignment']['generation']}; one replacement answers "
            f"for one fenced generation")
    return prepared


def _prepared_line(custody, prepared, *, authority_uuid, work_id, what):
    """The line is STILL prepared for this replacement, and still this Work's.

    WHAT `correction-ready` MEANS HERE is what `_corrected_line` says it means
    one operation over: `record_verdict` moves a line there for exactly one
    reason, a `changes-requested` disposition against its current checkpoint.
    So a line that is `correction-ready` at the checkpoint B restored IS the
    statement that this checkpoint's review asked for changes -- and B proved
    that verdict through its own owner before it restored anything.

    AND NOTHING HAS SUPERSEDED IT. An accepted verdict would have made the
    line `accepted` and recorded integration eligibility; a later round would
    have moved the current checkpoint. Both are read from the line provider's
    own rows through its own readers.
    """
    from ..worker_manager import review_cycles

    line = review_cycles.line_of(custody, prepared["line_id"])
    if line["authority_uuid"] != authority_uuid \
            or line["work_id"] != work_id:
        raise ContractRefusal(
            "refused", "precondition",
            f"development line {name_value(prepared['line_id'])} belongs to "
            f"another Authority or Work than the Job {what} names")
    if line["state"] != "correction-ready":
        raise ContractRefusal(
            "refused", "precondition",
            f"development line {name_value(prepared['line_id'])} is "
            f"{name_value(line['state'])}; a replacement follows a restored "
            f"correction that left it ready and nothing else")
    if line["current_checkpoint_id"] != prepared["checkpoint_id"]:
        raise ContractRefusal(
            "refused", "precondition",
            f"development line {name_value(prepared['line_id'])} is corrected "
            f"from {name_value(line['current_checkpoint_id'])} and this "
            f"recovery restored {name_value(prepared['checkpoint_id'])}; a "
            f"later round has superseded it")
    if review_cycles.integration_checkpoint(
            custody, prepared["line_id"]) is not None:
        raise ContractRefusal(
            "refused", "precondition",
            f"development line {name_value(prepared['line_id'])} already has "
            f"an accepted checkpoint eligible for integration; an accepted "
            f"review supersedes the correction this would replace")
    writer = review_cycles.writer_of(custody, prepared["writer_id"])
    if writer["state"] == "active":
        raise ContractRefusal(
            "refused", "precondition",
            f"the abandoned writer {name_value(prepared['writer_id'])} still "
            f"holds the line; a successor is not offered onto a checkout "
            f"somebody is still excluded from")
    return line


def _job_correction(store, custody, *, job_id, stage_id, attempt_id,
                    prepared, work_id, what):
    """THE JOB'S OWN COMMITTED CORRECTION, and it is what selects the
    checkpoint.

    Review 2026-09-09T17:07Z [P1], and the counterexample is exactly right. The
    first cut proved the selected attempt and the WORK'S CURRENT prepared line
    -- so a later custody round that recorded changes-requested against another
    checkpoint, without ever advancing this Job, let a recovery restored from
    THAT checkpoint end an episode whose committed correction named a different
    one. Same Work, same current line and a valid verdict somewhere in custody
    are not this Job's selected correction.

    SO THE RELATIONSHIP IS READ FROM THIS STORE'S OWN JOURNAL.
    `advance_correction` commits under an identity derived from the Job and the
    checkpoint it corrected, and its result names the episode it opened. Both
    halves are required here: the identity this recovery's checkpoint composes
    must be one this Job committed, AND the episode that correction opened must
    be the attempt this recovery is about. Either alone is a coincidence.

    AND THE VERDICT IT RESOLVED IS RE-READ through the custody provider's own
    typed reader, exactly as `_proved_verdict` does one operation over, so a
    correction is bound to the decision that asked for it rather than to the
    fact that some decision exists.
    """
    from ..worker_manager import review_cycles

    operation_id = correction_operation_id(job_id, prepared["checkpoint_id"])
    record = store.operation_record(operation_id)
    if record is None:
        raise ContractRefusal(
            "refused", "precondition",
            f"Job {name_value(job_id)} committed no correction from "
            f"checkpoint {name_value(prepared['checkpoint_id'])}; {what} "
            f"restored a checkpoint this Job's own handoff never selected")
    if record["kind"] != CORRECT_KIND:
        raise ContractRefusal(
            "integrity", "schema",
            f"Job {name_value(job_id)} names correction operation "
            f"{name_value(operation_id)}, which this store committed as "
            f"{name_value(record['kind'])}")
    _, committed = store.replay(operation_id, record["signature"],
                                kind=CORRECT_KIND)
    if committed is None:
        raise ContractRefusal(
            "integrity", "schema",
            f"Job {name_value(job_id)} names correction operation "
            f"{name_value(operation_id)}, which this store committed with no "
            f"recorded answer to replay")
    correction = boundaries.document(
        committed, f"Job {name_value(job_id)}'s committed correction",
        required=documents.CONTRACTS["stage.correction"][0])
    opened = boundaries.document(
        correction["implementation"],
        f"Job {name_value(job_id)}'s corrected implementation episode",
        required=documents.CONTRACTS["stage.episode"][0])
    if correction["job_id"] != job_id or correction["work_id"] != work_id \
            or correction["line_id"] != prepared["line_id"] \
            or correction["checkpoint_id"] != prepared["checkpoint_id"]:
        raise ContractRefusal(
            "integrity", "schema",
            f"Job {name_value(job_id)}'s committed correction names another "
            f"Job, Work, line or checkpoint than {what} recovered")
    if opened["stage_id"] != stage_id or opened["attempt_id"] != attempt_id:
        raise ContractRefusal(
            "refused", "precondition",
            f"Job {name_value(job_id)}'s correction from checkpoint "
            f"{name_value(prepared['checkpoint_id'])} opened attempt "
            f"{name_value(opened['attempt_id'])} and {what} is about "
            f"{name_value(attempt_id)}; a recovery ends the episode its own "
            f"Job handoff selected")
    verdict = review_cycles.verdict_of(custody, correction["verdict_id"])
    if verdict["disposition"] != CORRECTION_DISPOSITION:
        raise ContractRefusal(
            "refused", "precondition",
            f"verdict {name_value(correction['verdict_id'])} is "
            f"{name_value(verdict['disposition'])}; only "
            f"{name_value(CORRECTION_DISPOSITION)} asks for another round")
    if verdict["line_id"] != prepared["line_id"] \
            or verdict["checkpoint_id"] != prepared["checkpoint_id"] \
            or verdict["authority_uuid"] != store.authority_uuid \
            or verdict["work_id"] != work_id:
        raise ContractRefusal(
            "refused", "precondition",
            f"verdict {name_value(correction['verdict_id'])} was recorded "
            f"about another line, checkpoint, Authority or Work than {what}")
    return correction


def _adopted_restart(value, what, *, operation_id=None, attempt_id=None,
                     stage_id=None):
    """One completed replacement receipt, owned with its RELATIONSHIPS.

    Review 2026-09-09T17:07Z [P1]. The replay branch returned whatever
    `JobStore.replay` decoded: that owner verifies the operation kind and the
    SELECTOR signature and then hands back the stored result, so a journal row
    whose result carried a foreign schema, a null assignment and somebody
    else's checkpoint replayed as an ordinary success. Generic decoding
    establishes that bytes parse and nothing about whose recovery they
    describe.

    BOTH EXITS COME THROUGH HERE, so what is written is held to exactly the
    contract what is read is held to.
    """
    taken = boundaries.document(value, what,
                                required=documents.CONTRACTS[
                                    "stage.abandoned-restart"][0])
    if taken["schema"] != documents.ABANDONED_RESTART_SCHEMA:
        raise ContractRefusal(
            "integrity", "schema",
            f"{what} records schema {name_value(taken['schema'])} and this "
            f"store writes {name_value(documents.ABANDONED_RESTART_SCHEMA)}")
    if taken["ended_state"] != EXCLUSION_ENDING:
        raise ContractRefusal(
            "integrity", "schema",
            f"{what} records ending {name_value(taken['ended_state'])} and a "
            f"replacement this store committed records "
            f"{name_value(EXCLUSION_ENDING)}")
    for member in ("operation_id", "job_id", "stage_id", "attempt_id",
                   "line_id", "checkpoint_id", "preparation_operation_id",
                   "discharge_operation_id"):
        boundaries.identity(taken[member], f"{what}'s {member}")
    boundaries.generation(taken["episode"], f"{what}'s episode")
    assignment = boundaries.document(
        taken["assignment"], f"{what}'s assignment",
        required=("work_ref", "participant", "generation"))
    boundaries.document(assignment["work_ref"], f"{what}'s Work reference",
                        required=("authority_uuid", "work_id"))
    boundaries.generation(assignment["generation"], f"{what}'s generation")
    for member, expected in (("operation_id", operation_id),
                             ("attempt_id", attempt_id),
                             ("stage_id", stage_id)):
        if expected is not None and taken[member] != expected:
            raise ContractRefusal(
                "integrity", "schema",
                f"{what} records {member} {name_value(taken[member])} and this "
                f"read selected {name_value(expected)}")
    return taken


def restart_abandoned_correction(store, custody, *, job_id, attempt_id,
                                 generation):
    """End the one live episode an explicit abandonment left unfinishable.

    W128698, `work/records/2026/09/finding-v12-abandoned-episode-replacement/`.
    W119114 measured the whole defect: an operator declaration ends the
    ATTEMPT, and nothing ended the stage's live EPISODE -- so
    `projection.replaceable` saw a stage with a live episode, `manager._replace`
    never opened a successor, and the Job stopped with `implementation`
    `exceptional` and everything behind it blocked.

    IT IS AN EXPLICIT RECOVERY AND NOT A SCHEDULING RULE. There is no timer,
    no deadline, no retry count and no clock read anywhere in it: what
    authorizes it is that A and B have COMMITTED their own proofs -- the
    declaration, the fence, the positively absent runtime, the discharged
    gate, the restored checkout and the excluded writer -- and this leaf reads
    both through their public interfaces and crosses them against this Job.

    IT OPENS NOTHING. Ending the episode is the whole act; the ordinary sweep
    then opens exactly one successor through `open_next`, under the same
    journalled identity and the same one-live-episode index every other
    replacement uses. A leaf that opened its own successor here would be
    building a second scheduler beside the one that already works.

    THE ORDER, and each step is the next one's precondition:

      1. own the operands and read this Job's implementation stage;
      2. REPLAY, before any mutable stage state is read. A committed recovery
         must answer after the successor has already started, and checking
         today's live episode first would refuse the retry for having
         succeeded -- which is `advance_correction`'s own lesson;
      3. prove A's and B's receipts and cross-bind them to each other;
      4. prove the line is still prepared for THIS replacement and that no
         accepted review or later round has superseded it;
      5. prove the live episode is the abandoned attempt's OWN. A historical
         receipt never ends a different or later episode; and
      6. end exactly that episode, guarded by its own liveness in the same
         statement that performs it.
    """
    boundaries.identity(attempt_id, "a runtime attempt id")
    boundaries.generation(generation, "a fenced assignment generation")
    stages = _stored_pair(store, job_id)
    stage = stages["implementation"]
    work_id = stage["work_id"]
    what = (f"the abandoned correction for attempt {name_value(attempt_id)} "
            f"generation {generation}")

    operation_id = restart_operation_id(attempt_id, generation)
    operands = {"job_id": job_id, "work_id": work_id,
                "stage_id": stage["stage_id"], "attempt_id": attempt_id,
                "generation": generation}
    signature = job_signature(RESTART_KIND, operands)
    # STEP TWO, AND ITS POSITION IS THE CONTRACT.
    found, recorded = store.replay(operation_id, signature, kind=RESTART_KIND)
    if found:
        held = _adopted_restart(
            recorded, f"{what}'s committed replacement",
            operation_id=operation_id, attempt_id=attempt_id,
            stage_id=stage["stage_id"])
        # AND ITS HISTORICAL RELATIONSHIPS, re-read from the owners. The
        # receipt names two provider operations and a checkpoint; a stored
        # result that changed any of them consistently is well shaped and still
        # about somebody else's recovery.
        replayed = _excluded_correction(custody, attempt_id, generation, what)
        if held["line_id"] != replayed["line_id"] \
                or held["checkpoint_id"] != replayed["checkpoint_id"] \
                or held["assignment"] != replayed["assignment"] \
                or held["preparation_operation_id"] != replayed["operation_id"] \
                or held["discharge_operation_id"] \
                != replayed["discharge_operation_id"]:
            raise ContractRefusal(
                "integrity", "schema",
                f"{what}'s committed replacement names a line, checkpoint, "
                f"assignment or provider operation its own owners do not "
                f"describe")
        return held

    prepared = _excluded_correction(custody, attempt_id, generation, what)
    _prepared_line(custody, prepared, authority_uuid=store.authority_uuid,
                   work_id=work_id, what=f"Job {name_value(job_id)}")
    if prepared["assignment"]["work_ref"]["work_id"] != work_id \
            or prepared["assignment"]["work_ref"]["authority_uuid"] \
            != store.authority_uuid:
        raise ContractRefusal(
            "refused", "precondition",
            f"{what} was fixed to another Authority or Work than Job "
            f"{name_value(job_id)}'s implementation stage")
    live = _live_episode(store, stage, "implementation")
    if live["attempt_id"] != attempt_id:
        raise ContractRefusal(
            "refused", "precondition",
            f"stage {name_value(stage['stage_id'])} is live on attempt "
            f"{name_value(live['attempt_id'])} and {what} is about "
            f"{name_value(attempt_id)}; a historical recovery never ends a "
            f"different or later episode")
    _unheld(store, live, "implementation")
    _job_correction(store, custody, job_id=job_id, stage_id=stage["stage_id"],
                    attempt_id=attempt_id, prepared=prepared,
                    work_id=work_id, what=what)
    answer = {"schema": documents.ABANDONED_RESTART_SCHEMA,
              "operation_id": operation_id, "job_id": job_id,
              "stage_id": stage["stage_id"], "episode": live["episode"],
              "attempt_id": attempt_id,
              "assignment": dict(prepared["assignment"]),
              "line_id": prepared["line_id"],
              "checkpoint_id": prepared["checkpoint_id"],
              "preparation_operation_id": prepared["operation_id"],
              "discharge_operation_id": prepared["discharge_operation_id"],
              "ended_state": EXCLUSION_ENDING}

    def act(connection):
        # UNDER THE WRITE LOCK, because the preflight above answers the
        # ordinary case cheaply and this is the one that decides. The refusals
        # are ORDINARY rather than durable, so a guard that fires unwinds the
        # savepoint instead of sealing an outcome that never happened.
        current = episode_of(store, stage["stage_id"], live["episode"])
        if current is None or current["ended_state"] is not None \
                or current["attempt_id"] != attempt_id:
            raise ContractRefusal(
                "refused", "precondition",
                f"episode {live['episode']} of stage "
                f"{name_value(stage['stage_id'])} is no longer the live one "
                f"for {name_value(attempt_id)}; a replacement ends the episode "
                f"it observed")
        _unheld(store, current, "implementation")
        # THE CUSTODY RELATIONSHIP, REVALIDATED HERE TOO. Review [P1]: the
        # first cut proved the prepared line and the absence of a superseding
        # accepted review only in the preflight, and a public accepted round
        # landing between that and this transaction still ended the episode.
        #
        # THE JOB LOCK DOES NOT FREEZE CUSTODY, and that is the whole point:
        # they are two stores, `transact` holds a write lock on THIS one, and
        # nothing stops the control store moving underneath it. So the reads
        # that decide are repeated at the boundary that commits, and their
        # refusals are ORDINARY rather than durable -- a guard that fires
        # unwinds the savepoint and leaves the episode and the journal exactly
        # as they were.
        settled = _excluded_correction(custody, attempt_id, generation, what)
        _prepared_line(custody, settled, authority_uuid=store.authority_uuid,
                       work_id=work_id, what=f"Job {name_value(job_id)}")
        if settled["line_id"] != prepared["line_id"] \
                or settled["checkpoint_id"] != prepared["checkpoint_id"] \
                or settled["operation_id"] != prepared["operation_id"]:
            raise ContractRefusal(
                "refused", "precondition",
                f"{what}'s restored correction changed while this replacement "
                f"was being proved")
        _job_correction(store, custody, job_id=job_id,
                        stage_id=stage["stage_id"], attempt_id=attempt_id,
                        prepared=settled, work_id=work_id, what=what)
        # THE ENDING IS STILL GUARDED BY ITS OWN LIVENESS, in the same
        # statement that performs it: a write whose precondition is only
        # checked somewhere else is a write nobody is guarding.
        changed = connection.execute(
            "UPDATE episodes SET ended_state = ?, ended_revision = ?, "
            "ended_at = ? WHERE stage_id = ? AND episode = ? "
            "AND ended_state IS NULL",
            (EXCLUSION_ENDING, live["episode"] + 1, store._now(),
             stage["stage_id"], live["episode"])).rowcount
        if changed != 1:
            raise ContractRefusal(
                "refused", "precondition",
                f"episode {live['episode']} of stage "
                f"{name_value(stage['stage_id'])} stopped being live inside "
                f"this transaction; a replacement ends the episode it "
                f"observed")
        return _adopted_restart(documents.abandoned_restart(**answer),
                                f"{what}'s replacement receipt",
                                operation_id=operation_id,
                                attempt_id=attempt_id,
                                stage_id=stage["stage_id"])

    return store.transact(operation_id, RESTART_KIND, signature, act)
