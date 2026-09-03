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
an episode is opened, and the row is what every later reader asks. That is what
lets episode 1 keep the plain `offer:{stage_id}` spelling a schema-1 store
already wrote into the manager's journal while episode 2 gets a new one -- the
identity a restart reconciles against is the one that was actually used, not
one recomputed from a rule that has since gained a case.

WHAT DECIDES "AT MOST ONE REPLACEMENT". Not this module: the partial unique
index `episodes_one_live_per_stage`, plus the journalled operation identity
below, which is derived from the stage and the episode NUMBER. Two managers
that both see one abandoned episode 1 both compute `episode.open:...:2`, and
one of them replays the other's committed result instead of opening a third
row. A duplicate abandonment notice cannot mint a second offer for the same
reason, in whatever order it arrives.
"""

from ..contracts import ContractRefusal
from ..contracts.errors import name_value
from ..worker_manager import boundaries
from . import documents, schema
from .store import job_signature

__all__ = ["OPEN_KIND", "END_KIND", "attempting", "end_episode",
           "episode_by_offer", "episode_of", "episodes_of", "identities",
           "live_of", "open_next", "open_first"]

OPEN_KIND = "episode.open"
END_KIND = "episode.end"


def open_operation_id(stage_id, episode):
    return f"{OPEN_KIND}:{stage_id}:{episode}"


def end_operation_id(stage_id, episode):
    return f"{END_KIND}:{stage_id}:{episode}"


def identities(stage_id, episode):
    """The offer and attempt ids one new episode is opened with.

    EPISODE 1 KEEPS THE UNADORNED SPELLING. It is the identity a schema-1
    store already used, so a migrated store's `offer.issue:offer:job-a/…`
    journal row is still the row its receipt names. Suffixing every episode
    would have been tidier to read and would have orphaned every operation
    identity this package has already committed.
    """
    boundaries.identity(stage_id, "a stage id")
    if type(episode) is not int or episode < 1:
        raise ContractRefusal(
            "integrity", "schema",
            f"a stage episode is a whole number from 1; this is "
            f"{name_value(episode)}")
    suffix = "" if episode == 1 else f"#{episode}"
    return (f"offer:{stage_id}{suffix}", f"attempt:{stage_id}{suffix}")


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
    """
    offer_id, attempt_id = identities(stage_id, 1)
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
    offer_id, attempt_id = identities(stage_id, episode)
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
