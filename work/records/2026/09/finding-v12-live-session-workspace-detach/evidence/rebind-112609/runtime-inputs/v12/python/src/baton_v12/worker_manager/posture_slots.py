"""POSTURE OCCUPANCY -- may this posture be used, and by which epoch.

W6627, ported from the frozen Node `posture_slots.mjs` by obligation. The
confirmed ruling it carries (W771, 2026-08-23):

    "Preserve the provider-observation axis exactly as evidence. `unknown`
     remains terminal and is never promoted to `closed` merely because the
     manager ordered a close, lost transport, reached a deadline, or wants to
     reuse the posture. Posture occupancy is a separate manager-owned axis:

         available -> occupied -> recovery-required -> available"

WHY THE TWO WERE TANGLED, since that is what the ruling untangles. Making
occupancy a projection of the session's observed state meant the only way to
get a posture back was to write `closed` -- and `closed` asserts that a
terminal turn fact was observed for every turn the epoch started. A session
that died before it initialized had no such facts, so recovering capacity
meant inventing knowledge.

SILENCE AND ELAPSED TIME NEVER RECOVER A SLOT. Leaving `recovery-required`
takes positive evidence that the old provider session CANNOT STILL ACT, and
this module's whole content is which observations count as that.

AND THREE KINDS OF ABSENCE ARE THREE FACTS. W6627's acceptance requires
positive absence of a SESSION to be distinguishable from an absent RUNTIME,
and the frozen host had only the second:

  provider-session-closed  the provider session was observed to END. The axis
                           is where that is established, and this reads it.
  session-absent           the adapter looked for the exact provider session
                           and it is NOT THERE. An agent process can die while
                           its container keeps running, and before this the
                           only way to recover that posture was to destroy a
                           container that was doing nothing wrong.
  runtime-absent           the adapter observed the exact runtime identity
                           stopped or no longer present.

NONE OF THEM SATISFIES THE RUNTIME-QUIESCENCE GATE, and `session-absent` is
the one most likely to be mistaken for a fact that does. It says an AGENT is
gone. The gate asks whether the RUNTIME holding the generation is gone, and
`sessions.satisfies_runtime_quiescence_gate` answers that question -- always
false -- for every state on the session axis.

AND RECOVERY DOES NOT REWRITE HISTORY. A durable result of

    observation: unknown   runtime: running   slot: available

is coherent and is the normal shape after an agent died inside a live
container. Recovering the posture does not discard a filesystem, accept an
output, or choose salvage; those stay independent disposition decisions this
module has no opinion about.
"""

from ..contracts import ContractRefusal
from ..contracts.errors import name_value
from . import boundaries, documents, schema

# The `_in` composition helpers and the occupancy compare-and-set are PRIVATE.
# Each must run inside a transaction its caller owns -- taking a posture and
# failing to become a session, or recording an observation whose slot movement
# did not land, are the strandings this axis exists to remove -- so none of them
# is a thing a caller outside this package may reach on its own.
__all__ = ["RECOVERY_EVIDENCE", "posture_slot", "release_slot",
           "require_slot_recovery"]

# A CLOSED SET, because "the manager believes it is gone" is not a member.
# A stop REQUEST, a dead socket and an elapsed deadline are deliberately none
# of these: each is a thing the manager did or failed to hear, and none of
# them is something anybody observed about the provider.
RECOVERY_EVIDENCE = ("provider-session-closed", "session-absent",
                     "runtime-absent")

# Which evidence names WHICH identity it observed absent. A name without the
# identity it is about is a claim about nothing -- "the container is gone"
# does not say which container -- so the kind decides which one is required
# and the proof below compares it with what the store durably holds.
_NAMES_IDENTITY = {"session-absent": "provider_session_id",
                   "runtime-absent": "runtime_id"}


def _posture(posture):
    """One of the two. A third vocabulary from the session state and from the
    runtime axis, and the refusal says so rather than listing the members of
    whichever one the caller meant.

    ONE LITERAL LABEL, and no `what` parameter to carry a caller's noun. Every
    crossing this owns is the same subject -- a posture -- so a per-caller noun
    would be prose rather than a distinction, and a label with no literal part
    is one the inventory cannot attribute and a probe cannot assert.
    """
    boundaries.text(posture, "a posture")
    if posture not in schema.POSTURES:
        raise ContractRefusal(
            "integrity", "schema",
            f"{name_value(posture)} is not a posture; a session is "
            f"{' or '.join(schema.POSTURES)}, and they never share an epoch "
            f"or a connection")
    return posture


def _epoch(session_epoch):
    """A positive session epoch, refused HERE rather than by the layer.

    NOT `boundaries.generation`, which is the rule for an ASSIGNMENT generation
    and counts from zero. Epoch zero is a session that was never allocated, and
    a query for one answers absence in a way a caller reads as "no such
    session" rather than "you asked a malformed question" -- so the frozen
    `positiveInt` this member is typed as is the rule, and it is one membership
    question with its type established in the same expression.

    I reached for `generation` first and measured it: every value it would have
    refused is one this test refuses above it, so the call was a second owner
    for a property already owned and unreachable besides. It is gone rather
    than left standing as decoration -- the fifth time this campaign has made
    me delete an owner instead of keeping one nothing can drive.

    `bool` is excluded because `True == 1`, and epoch `True` would compare equal
    to the first epoch any posture ever allocated.
    """
    if type(session_epoch) is not int or type(session_epoch) is bool \
            or session_epoch < 1:
        raise ContractRefusal(
            "integrity", "schema",
            f"{name_value(session_epoch)} is not a positive session epoch; "
            f"postures count from one and never reuse")
    return session_epoch


def _slot_row(connection, attempt_id, posture):
    """THE ONE CROSSING out of the posture_slots table, and every column owned.

    One reader, for the reason the offers and attempts tables have one: a read
    site is a chance to forget, and there is exactly one here.
    """
    found = connection.execute(
        "SELECT * FROM posture_slots WHERE runtime_attempt_id = ? "
        "AND posture = ?", (attempt_id, posture)).fetchone()
    if found is None:
        return None
    return boundaries.row(found, "a persisted posture slot",
                          schema.POSTURE_SLOT_COLUMNS)


def posture_slot(store, attempt_id, posture):
    """The slot as it stands, or None when the posture has never been used."""
    boundaries.identity(attempt_id, "a runtime attempt id")
    _posture(posture)
    row = _slot_row(store._connection, attempt_id, posture)
    if row is None:
        return None
    return documents.posture_slot(
        attempt_id=attempt_id, posture=posture, occupancy=row["occupancy"],
        session_epoch=row["session_epoch"], reason=row["reason"],
        changed_at=row["changed_at"])


def _occupy_slot(connection, at, *, attempt_id, posture, session_epoch):
    """TAKE the slot for one epoch, or refuse. Atomic, and inside the caller's
    write transaction.

    A never-used posture is created `available` and taken in the same statement
    pair, so the first open and a concurrent second are decided by the database
    rather than by a read. Freshness and concurrency are two rules and
    allocating the next epoch answers only the first.

    It takes a CONNECTION rather than a store because the slot and the session
    row are ONE act: a posture occupied by an epoch that never became a session
    would be exactly the stranding this axis exists to remove.
    """
    boundaries.identity(attempt_id, "a runtime attempt id")
    _posture(posture)
    _epoch(session_epoch)
    boundaries.instant(at, "a slot movement instant")
    # INSERT-OR-NOTHING first, so a posture nobody has used becomes an
    # `available` row without a read deciding anything.
    connection.execute(
        "INSERT OR IGNORE INTO posture_slots (runtime_attempt_id, posture, "
        "occupancy, session_epoch, reason, changed_at) "
        "VALUES (?, ?, 'available', NULL, NULL, ?)",
        (attempt_id, posture, at))
    taken = connection.execute(
        "UPDATE posture_slots SET occupancy = 'occupied', session_epoch = ?, "
        "reason = NULL, changed_at = ? WHERE runtime_attempt_id = ? "
        "AND posture = ? AND occupancy = 'available'",
        (session_epoch, at, attempt_id, posture)).rowcount
    if taken != 1:
        row = _slot_row(connection, attempt_id, posture)
        raise ContractRefusal(
            "runtime-observation", "duplicate-runtime",
            f"the {posture} posture of {name_value(attempt_id)} is "
            f"{row['occupancy']} (epoch {row['session_epoch']}"
            f"{': ' + row['reason'] if row['reason'] else ''}); a posture "
            f"holds one session, and a later epoch begins only after this "
            f"slot is recovered")
    return documents.slot_moved(attempt_id=attempt_id, posture=posture,
                               occupancy="occupied",
                               session_epoch=session_epoch, moved=True)


def _bound(connection, attempt_id, posture, session_epoch):
    """The slot as the write transaction sees it, WITH THE EPOCH BOUND.

    Evidence is about the epoch that produced it. Applied to a later occupant
    it is not stale evidence, it is evidence about something else -- so the
    comparison runs in the idempotent branches too. "Already released" is only
    an answer to a retry if the release being retried is the one that happened.
    """
    row = _slot_row(connection, attempt_id, posture)
    if row is None:
        raise ContractRefusal(
            "refused", "precondition",
            f"the {posture} posture of {name_value(attempt_id)} has never "
            f"been occupied; there is nothing to recover")
    if row["session_epoch"] != session_epoch:
        raise ContractRefusal(
            "runtime-observation", "identity-mismatch",
            f"this evidence is about {posture}/{session_epoch} and the slot "
            f"holds {posture}/{row['session_epoch']}; evidence about one "
            f"epoch says nothing about the one that replaced it")
    return row


def _prove(connection, *, attempt_id, posture, session_epoch, evidence,
           observed_identity):
    """Prove the durable fact an evidence NAME claims, or refuse.

    A closed vocabulary of labels is not evidence; it is a closed vocabulary
    of CLAIMS. Each kind is therefore checked against what the store already
    holds rather than against the caller's account of it:

      `provider-session-closed` requires THIS epoch's own observation to
      durably be `closed`. The axis is where that fact is established.

      `session-absent` requires the exact `provider_session_id` this epoch
      durably holds. An epoch that never learned a provider session id has no
      identity anybody can have observed absent, and refusing there is the
      point: absence of a name is not absence of a session.

      `runtime-absent` requires the exact `attempts.runtime_id`. A missing,
      foreign or stale identity recovers nothing, because "some container is
      gone" is not "the container that held this assignment is gone".

    Neither absence kind REWRITES the observation. Recovering capacity says
    nothing about what the provider was seen to do, which is the whole content
    of keeping the two axes apart.
    """
    session = connection.execute(
        "SELECT * FROM agent_sessions WHERE runtime_attempt_id = ? "
        "AND posture = ? AND session_epoch = ?",
        (attempt_id, posture, session_epoch)).fetchone()
    if session is None:
        raise ContractRefusal(
            "refused", "precondition",
            f"no agent session {posture}/{session_epoch} for attempt "
            f"{name_value(attempt_id)}")
    owned = boundaries.row(session, "a persisted agent session",
                           schema.AGENT_SESSION_COLUMNS)
    if evidence == "provider-session-closed":
        if owned["state"] != "closed":
            raise ContractRefusal(
                "refused", "precondition",
                f"{posture}/{session_epoch} is observed {owned['state']}, not "
                f"closed; a provider-close release reads the observation "
                f"rather than trusting a caller that one happened")
        return
    if evidence == "session-absent":
        held = owned["provider_session_id"]
        if held is None:
            raise ContractRefusal(
                "refused", "precondition",
                f"{posture}/{session_epoch} durably holds no provider session "
                f"id, so no provider session can have been observed absent "
                f"for it; an epoch that never named one has no identity to "
                f"look for")
        if observed_identity != held:
            raise ContractRefusal(
                "runtime-observation", "identity-mismatch",
                f"{name_value(observed_identity)} was observed absent and "
                f"{posture}/{session_epoch} holds {name_value(held)}; some "
                f"provider session being gone is not this one being gone")
        return
    attempt = connection.execute(
        "SELECT runtime_id FROM attempts WHERE runtime_attempt_id = ?",
        (attempt_id,)).fetchone()
    attached = None if attempt is None else attempt["runtime_id"]
    if attached is None:
        raise ContractRefusal(
            "refused", "precondition",
            f"attempt {name_value(attempt_id)} is attached to no runtime, so "
            f"no runtime identity can have been observed absent for it")
    boundaries.identity(attached, "a persisted attached runtime id")
    if observed_identity != attached:
        raise ContractRefusal(
            "runtime-observation", "identity-mismatch",
            f"{name_value(observed_identity)} was observed absent and attempt "
            f"{name_value(attempt_id)} is attached to {name_value(attached)}; "
            f"some container being gone is not the one that held this "
            f"assignment being gone")


def _evidence(evidence):
    """ONE LITERAL LABEL, for the reason `_posture` carries one: every crossing
    this owns is the same subject, and a label with no literal part is one the
    inventory cannot attribute."""
    boundaries.text(evidence, "slot recovery evidence")
    if evidence not in RECOVERY_EVIDENCE:
        raise ContractRefusal(
            "integrity", "schema",
            f"{name_value(evidence)} is not positive absence evidence; a slot "
            f"is recovered by {', '.join(RECOVERY_EVIDENCE)}, and silence, an "
            f"elapsed deadline or a stop REQUEST is none of them")
    return evidence


def require_slot_recovery(store, *, attempt_id, posture, session_epoch,
                          reason):
    """Move the slot to `recovery-required`, or refuse.

    This is what an AMBIGUOUS ending does. It is not a failure state and it is
    not terminal -- it says the epoch that held the slot may still be able to
    act and nobody has established otherwise, which is the honest reading of a
    dead transport, an elapsed deadline or a close nobody saw complete.

    It changes no observation. The session's own axis stays wherever the
    provider was actually seen to be, and that is the point of the separation.
    """
    connection = store._connection
    connection.execute("BEGIN IMMEDIATE")
    try:
        answer = _require_slot_recovery_in(
            connection, store._now(), attempt_id=attempt_id, posture=posture,
            session_epoch=session_epoch, reason=reason)
    except BaseException:
        try:
            connection.execute("ROLLBACK")
        except Exception:
            pass
        raise
    connection.execute("COMMIT")
    return answer


def _require_slot_recovery_in(connection, at, *, attempt_id, posture,
                             session_epoch, reason):
    """The same act, INSIDE a caller's transaction.

    Exposed because an act that both records an observation and moves the slot
    must be ONE transaction: composing them through two would leave a crash
    window in which the observation had landed and the slot had not -- a
    session recorded `unknown` whose posture still looked live.
    """
    boundaries.identity(attempt_id, "a runtime attempt id")
    _posture(posture)
    _epoch(session_epoch)
    boundaries.text(reason, "a slot movement reason")
    boundaries.instant(at, "a slot movement instant")
    row = _bound(connection, attempt_id, posture, session_epoch)
    if row["occupancy"] == "recovery-required":
        # Reporting the same ambiguity twice is ordinary, and the FIRST reason
        # is kept: the later report observed nothing new.
        return documents.slot_moved(
            attempt_id=attempt_id, posture=posture,
            occupancy="recovery-required", session_epoch=row["session_epoch"],
            moved=False)
    if row["occupancy"] != "occupied":
        raise ContractRefusal(
            "refused", "precondition",
            f"the {posture} posture of {name_value(attempt_id)} is "
            f"{row['occupancy']}; only an occupied slot can become ambiguous")
    connection.execute(
        "UPDATE posture_slots SET occupancy = 'recovery-required', "
        "reason = ?, changed_at = ? WHERE runtime_attempt_id = ? "
        "AND posture = ?", (reason, at, attempt_id, posture))
    return documents.slot_moved(
        attempt_id=attempt_id, posture=posture, occupancy="recovery-required",
        session_epoch=row["session_epoch"], moved=True)


def release_slot(store, *, attempt_id, posture, session_epoch, evidence,
                 observed_identity=None, reason):
    """RELEASE the slot on positive evidence, or refuse.

    The whole ruling lives here. A slot returns to `available` only when
    something was OBSERVED that establishes the old provider session cannot
    still act -- one of the three kinds named at the top of this module, each
    proved against what the store already holds.
    """
    connection = store._connection
    connection.execute("BEGIN IMMEDIATE")
    try:
        answer = _release_slot_in(
            connection, store._now(), attempt_id=attempt_id, posture=posture,
            session_epoch=session_epoch, evidence=evidence,
            observed_identity=observed_identity, reason=reason)
    except BaseException:
        try:
            connection.execute("ROLLBACK")
        except Exception:
            pass
        raise
    connection.execute("COMMIT")
    return answer


def _release_slot_in(connection, at, *, attempt_id, posture, session_epoch,
                    evidence, observed_identity=None, reason):
    """The same act, INSIDE a caller's transaction -- so an operation that both
    establishes an observation and releases on it is one act rather than two a
    crash can separate."""
    boundaries.identity(attempt_id, "a runtime attempt id")
    _posture(posture)
    _epoch(session_epoch)
    boundaries.text(reason, "a slot movement reason")
    boundaries.instant(at, "a slot movement instant")
    _evidence(evidence)
    if evidence in _NAMES_IDENTITY:
        # ONE LITERAL LABEL. An f-string naming which identity kind was
        # expected would leave the inventory a label with a hole in the middle
        # of it, and the message below already says which kind this evidence
        # is about.
        boundaries.identity(observed_identity, "the identity observed absent")
    elif observed_identity is not None:
        raise ContractRefusal(
            "integrity", "schema",
            f"{name_value(evidence)} names no identity and this release "
            f"carries {name_value(observed_identity)}; evidence that does not "
            f"observe an identity cannot be about one")
    row = _bound(connection, attempt_id, posture, session_epoch)
    # THE NAMED FACT, PROVED, before the slot's own state is consulted: a
    # caller whose evidence is not real must not learn whether a retry would
    # have answered.
    _prove(connection, attempt_id=attempt_id, posture=posture,
           session_epoch=session_epoch, evidence=evidence,
           observed_identity=observed_identity)
    if row["occupancy"] == "available":
        # Already recovered, FOR THIS EPOCH -- `_bound` established that. A
        # retried recovery answers rather than refusing: the evidence has not
        # changed and neither has the slot.
        return documents.slot_moved(
            attempt_id=attempt_id, posture=posture, occupancy="available",
            session_epoch=row["session_epoch"], moved=False)
    connection.execute(
        "UPDATE posture_slots SET occupancy = 'available', reason = ?, "
        "changed_at = ? WHERE runtime_attempt_id = ? AND posture = ?",
        (reason, at, attempt_id, posture))
    return documents.slot_moved(
        attempt_id=attempt_id, posture=posture, occupancy="available",
        session_epoch=row["session_epoch"], moved=True)
