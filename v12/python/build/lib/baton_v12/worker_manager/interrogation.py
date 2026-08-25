"""OPERATOR INTERROGATION: `probe` and `inquire`, which are two operations.

W6627's confirmed split, 2026-08-25.
`work/records/2026/08/finding-v12-manager-agent-session-protocols/`.

THE V11 `poke` CONFLATED TWO FACTS and this module exists to separate them:
whether the adapter and the session can be OBSERVED right now, and whether a
model has accepted and answered a new conversational request. One operation
answering both means an operator who asked "is it alive" spends a model turn,
and an operator who asked "please consider this" cannot tell a delivery from an
answer.

  `probe`    is an immediate control-plane observation. It requires and
             consumes NO model turn. It reports the exact runtime, session and
             assignment identity, the current session state, last activity and
             whatever provider diagnostics the adapter carries -- through a
             closed typed answer.
  `inquire`  is a conversational request. The adapter first ACKNOWLEDGES
             whether the request is queued or delivered; the eventual model
             answer is a SEPARATE correlated result at a safe turn boundary.

BOTH BIND FOUR THINGS AND NONE OF THEM IS THE CALLER'S ACCOUNT OF ITSELF: the
exact assignment generation, the posture-specific session identity, an
effectively-once operation identity, and a manager-observed deadline.

A TIMEOUT IS AN OBSERVATION, NOT A CANCELLATION and not authority to discard
work. It says this manager stopped waiting; it says nothing about whether the
turn is still running or whether an answer is still coming. So `timed-out` is
NOT terminal on either axis: a model that answers afterwards is answering, and
the axis has to be able to record that. An axis that made it terminal would
turn the manager's patience into a decision about somebody else's turn.

THE WORKER RECEIVES NO BATON AND NO SQLITE CAPABILITY. The Worker Manager
journals the interrogation and publishes any conversational answer into Baton
itself, with its own participant and operation provenance. That ordering is
load-bearing in the other direction too: a committed Baton request is never
represented as proof that the adapter or the model saw it, which is why
publication is a separate act from the answer and has its own column.

WHAT IS NOT HERE: general turn supervision, event normalization and the App
Server's provider binding. The ruling supersedes the earlier exclusion only to
the extent `inquire` requires, and this module goes no further.
"""

import json

from ..contracts import (ContractRefusal, canonical_text,
                         check_no_durable_secret)
from ..contracts.errors import name_value
from . import boundaries, documents, posture_slots, schema
from .sessions import _session_row, _state
from .store import manager_signature

__all__ = ["INTERROGATION_KINDS", "probe", "inquire", "settle_interrogation",
           "record_inquiry_answer", "publish_inquiry_answer",
           "interrogation_of", "interrogations_of"]

INTERROGATION_KINDS = schema.INTERROGATION_KINDS

# WHAT `probe` MAY ANSWER. A closed set of SHAPES, like every other adapter
# answer in this package: knowing which alternative arrived tells you nothing
# unless you then know what it must carry.
#
# `unreachable` and `runtime-absent` are DIFFERENT and neither implies the
# other. An adapter this manager could not reach says nothing about the
# runtime; a runtime observed absent says nothing about whether the adapter is
# up. Collapsing them is how "I could not ask" becomes "there is nothing
# there", which is the conflation this whole design refuses.
PROBE_ANSWERS = {
    "observed": (("state", "provider_session_id", "last_activity_at",
                  "diagnostics"), ()),
    "unreachable": (("why",), ()),
    "runtime-absent": (("provider_session_id",), ()),
}

# WHAT `inquire` MAY ACKNOWLEDGE. The acknowledgement is not the answer, which
# is the whole point of the split -- so `answered` is deliberately NOT a member
# of this set. An adapter that could answer synchronously would be an adapter
# reporting a model turn it has not had.
INQUIRY_ACKNOWLEDGEMENTS = {
    "queued": ((), ()),
    "delivered": ((), ()),
    "unreachable": (("why",), ()),
    "runtime-absent": (("provider_session_id",), ()),
}

# How an adapter's acknowledgement or probe answer maps onto the durable
# outcome axis. Written as a table rather than as branches, so the two
# vocabularies stay two and the translation is one thing a reader can check.
_PROBE_OUTCOME = {"observed": "observed", "unreachable": "adapter-unreachable",
                  "runtime-absent": "runtime-absent"}
_INQUIRY_OUTCOME = {"queued": "queued", "delivered": "delivered",
                    "unreachable": "adapter-unreachable",
                    "runtime-absent": "runtime-absent"}

# The bounded prose an inquiry carries and the bounded answer it may receive.
# The provider's own report is free-form and bounded. Entries and characters
# both, because "bounded" has to mean bounded in the dimension a hostile or
# merely careless adapter would grow.
MAX_DIAGNOSTICS = 32
MAX_DIAGNOSTIC = 2_000
MAX_QUESTION = 16_000
MAX_ANSWER = 64_000


def _row(connection, operation_id):
    """THE ONE CROSSING out of the interrogations table, and every column
    owned."""
    found = connection.execute(
        "SELECT * FROM interrogations WHERE operation_id = ?",
        (operation_id,)).fetchone()
    if found is None:
        return None
    return boundaries.row(found, "a persisted interrogation",
                          schema.INTERROGATION_COLUMNS)


def _require(connection, operation_id):
    row = _row(connection, operation_id)
    if row is None:
        raise ContractRefusal(
            "refused", "precondition",
            f"no interrogation {name_value(operation_id)}; an outcome belongs "
            f"to a request this manager journalled")
    return row


def _bound_session(store, attempt_id, posture, session_epoch, port):
    """The bindings that come from DURABLE state, and nothing mutable.

    Not one of them is a claim the caller supplied about itself: the session
    row carries the posture, the epoch and the provider identity, and the
    attempt carries the fixed four-part assignment. The port's own participant
    is compared here too, because that is this process's identity rather than
    an answer the authority may change under it.

    WHETHER THAT GENERATION IS STILL LIVE is `_still_live`'s question and is
    asked inside the fresh action -- see fourth review [P1]. What this returns
    is stable, which is what lets the operation signature be built before the
    journal decides replay.
    """
    row = _session_row(store._connection, attempt_id, posture, session_epoch)
    if row is None:
        raise ContractRefusal(
            "refused", "precondition",
            f"no agent session {posture}/{session_epoch} for attempt "
            f"{name_value(attempt_id)}; an interrogation is addressed to a "
            f"session")
    if row["participant"] is None or row["generation"] is None:
        raise ContractRefusal(
            "refused", "precondition",
            f"{posture}/{session_epoch} carries no assignment; an "
            f"interrogation binds the exact generation it is about, and a "
            f"consent session has none")
    fixed = documents.assignment(
        work_ref=documents.work_ref(authority_uuid=row["authority_uuid"],
                                    work_id=row["work_id"]),
        participant=row["participant"], generation=row["generation"])
    if port.participant != fixed["participant"]:
        raise ContractRefusal(
            "refused", "capability",
            f"this session acts for {name_value(port.participant)} and "
            f"{posture}/{session_epoch} is assigned to "
            f"{name_value(fixed['participant'])}")
    return row, fixed


def _still_live(port, row, fixed, posture, session_epoch):
    """The AUTHORITY's current answer about this generation.

    Fourth review [P1]: this ran beside the durable binding, before
    `store.transact` could decide replay -- so an exact retry of an operation
    that had already committed was refused once the assignment ended, and the
    second authority observation decided a historical operation exactly as the
    second clock used to. It is called from inside the fresh action now, so a
    replay neither asks Baton to re-decide what was allowed when the request
    committed nor reaches the adapter.

    A FRESH interrogation still requires the live exact generation, because
    the fresh action is where this runs.
    """
    live = port.assignment_of(row["work_id"], row["authority_uuid"])
    if live is None:
        raise ContractRefusal(
            "stale-assignment", "ended",
            f"{name_value(row['work_id'])} holds no live assignment; an "
            f"interrogation is about work somebody is executing")
    if live != fixed:
        raise ContractRefusal(
            "stale-assignment", "generation",
            f"the live assignment is {name_value(live)} and "
            f"{posture}/{session_epoch} is bound to {name_value(fixed)}")


def _ask(store, port, agent, *, kind, attempt_id, posture, session_epoch,
         operation_id, deadline_seconds, question=None):
    """The shared half of both operations: bind, journal, then ask.

    JOURNALLED BEFORE THE ADAPTER IS CALLED, for the reason every other act in
    this manager is: a crash between the two boundaries must be answerable, and
    an outcome column that only ever recorded settled requests could not say
    that one was made.
    """
    boundaries.identity(attempt_id, "a runtime attempt id")
    posture_slots._posture(posture)
    posture_slots._epoch(session_epoch)
    boundaries.identity(operation_id, "an interrogation operation id")
    for operation in ("probe", "inquire"):
        boundaries.capability(getattr(agent, operation, None),
                              f"the agent adapter's {operation}")
    if question is not None:
        boundaries.text(question, "an inquiry question")
        if len(question) > MAX_QUESTION:
            raise ContractRefusal(
                "integrity", "limit",
                f"an inquiry question is at most {MAX_QUESTION} characters")
    row, fixed = _bound_session(store, attempt_id, posture, session_epoch,
                                port)
    # THE DURATION, NOT THE INSTANT. Re-review [P1]: the derived absolute
    # deadline was in the signature, so calling the same operation with the
    # same identity and the same operands at a LATER instant produced a
    # different signature and collided with its own journalled request. Wall
    # time is not a caller operand, and effectively-once identity that depends
    # on it cannot survive the ordinary restart the durable journal exists for.
    #
    # The absolute deadline is still the operation's committed RESULT: `act`
    # writes the first manager-observed one into the row and into the answered
    # document, and a replay returns that document rather than recomputing it.
    # So the manager's first observation is what everybody sees, and the second
    # caller's clock decides nothing.
    signature = manager_signature(
        f"interrogation.{kind}",
        {"attempt_id": attempt_id, "posture": posture,
         "session_epoch": session_epoch, "assignment": fixed,
         "deadline_seconds": deadline_seconds, "question": question})

    # THE ACTION IS THE COMMIT MARKER, which is the offers slice's idiom and
    # is here for the same reason: `transact` runs the action only when it did
    # NOT replay, so this list IS the transaction boundary reporting which of
    # the two happened. Reading the returned document instead would not work —
    # a fresh commit and a replay answer with the same `requested` outcome,
    # because that is what the row said both times.
    committed = []

    def act(connection):
        # THE CLOCK IS READ HERE AND NOWHERE EARLIER. Third review [P1]:
        # `requested_at` and the derived deadline were computed before
        # `transact` could decide replay, so an exact retry at a valid but
        # late instant refused in the deadline arithmetic -- a request whose
        # durable answer already existed, rejected because a NEW deadline
        # would not fit. `transact` runs this only when it did not replay, so
        # the manager's first observation is the only one ever taken and the
        # second caller's clock decides nothing, which is what the previous
        # correction claimed and this makes true.
        committed.append("ours")
        # THE MUTABLE EXTERNAL READ, HERE AND NOWHERE EARLIER, for the same
        # reason the clock is: `transact` runs this only when it did not
        # replay, so what Baton says today decides today's requests and not
        # yesterday's answered one.
        _still_live(port, row, fixed, posture, session_epoch)
        requested_at = store._now()
        deadline_at = boundaries.deadline(requested_at, deadline_seconds,
                                          "an interrogation deadline")
        connection.execute(
            "INSERT INTO interrogations (operation_id, kind, "
            "runtime_attempt_id, posture, session_epoch, authority_uuid, "
            "work_id, assignment_participant, assignment_generation, "
            "requested_at, deadline_at, outcome) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'requested')",
            (operation_id, kind, attempt_id, posture, session_epoch,
             row["authority_uuid"], row["work_id"], fixed["participant"],
             fixed["generation"], requested_at, deadline_at))
        return documents.interrogation_requested(
            operation_id=operation_id, kind=kind,
            agent_session_ref=documents.session_ref(
                runtime_attempt_id=attempt_id, posture=posture,
                session_epoch=session_epoch,
                provider_session_id=row["provider_session_id"]),
            assignment=fixed, requested_at=requested_at,
            deadline_at=deadline_at, outcome="requested")

    answered = store.transact(operation_id, f"interrogation.{kind}",
                              signature, act)
    return answered, bool(committed), row, fixed


def probe(store, port, agent, *, attempt_id, posture, session_epoch,
          operation_id, deadline_seconds):
    """An IMMEDIATE control-plane observation, consuming no model turn.

    What it reports is what the adapter can see now: the exact session and
    assignment identity, the current session state, the last activity it
    observed and whatever provider diagnostics it carries. What it never does
    is ask the model anything -- which is the half of v11's `poke` an operator
    asking "is this alive" should never have been charged for.
    """
    answered, committed, row, fixed = _ask(
        store, port, agent, kind="probe", attempt_id=attempt_id,
        posture=posture, session_epoch=session_epoch,
        operation_id=operation_id, deadline_seconds=deadline_seconds)
    if not committed:
        # AN EXACT RETRY ASKS THE ADAPTER NOTHING. The request was made once,
        # and asking again under one operation identity would make the
        # effectively-once contract a statement about the journal alone while
        # the adapter saw two.
        return interrogation_of(store, operation_id)
    seen = boundaries.alternative(
        agent.probe({**answered["agent_session_ref"],
                     "operation_id": operation_id}),
        "an agent probe answer", PROBE_ANSWERS)
    _same_session(seen, row, posture, session_epoch)
    return _settle(
        store, operation_id, _PROBE_OUTCOME[seen["kind"]],
        _observation(seen) if seen["kind"] == "observed" else None)


def _observation(seen):
    """The `observed` variant's MEMBERS, owned as the injected values they are.

    Re-review [P1]: `alternative` closes the member NAMES and deliberately does
    not own their values, and the probe path did nothing afterwards -- so a
    runtime-axis `running` crossed as an agent-session state and collapsed two
    vocabularies this Work exists to keep apart. `reconcile_agent_session`
    already owns its observation's state through `observe_session_state`; this
    is the same rule on the path that had none.

    It matters more here than it did there, because this value is now DURABLE:
    an unowned reading would be written into the row and read back by every
    later lookup as though the manager had established it.
    """
    # §13 AT THE COMMON RECEIVING OWNER. Fourth review [P1]: `_diagnostics`
    # owned shape, count, key and value types and lengths -- and ownership is
    # not the secret walk, so a diagnostic named `claim_token` was accepted and
    # written to the durable `observation` column. Walked HERE because this is
    # the one owner both the fresh adapter path and the exported settlement
    # reach, so neither can persist a reading this manager has not walked.
    #
    # THE RAW ANSWER, before the members are composed: the walk's named half is
    # about MEMBER NAMES, and a member named for a secret is an ordinary
    # substring once it has been folded into a document somebody built.
    check_no_durable_secret(seen, what="a probe observation")
    return {
        "kind": "observed",
        # The frozen §7.3 nine, and nothing from the runtime axis. Injected
        # FIRST and then the vocabulary, which is exactly the pair
        # `reconcile_agent_session` applies to its own observation: the type is
        # what makes the membership question answerable rather than raising.
        "state": _state(
            boundaries.injected(seen["state"], "an observed session state"),
            "an observed session state"),
        "provider_session_id": seen["provider_session_id"],
        "last_activity_at": boundaries.instant(
            seen["last_activity_at"], "an observed last activity instant"),
        "diagnostics": _diagnostics(seen["diagnostics"]),
    }


def _diagnostics(given):
    """The provider's own bounded key/value report.

    Free-form BY DESIGN -- an adapter knows things this contract does not name
    -- and bounded anyway, because it is persisted and handed back: a nested
    structure or an unbounded blob would make a durable column a place to put
    whatever an adapter felt like, and a value with behaviour would run inside
    a walk somebody later performs over it.
    """
    document = boundaries.document(given, "probe diagnostics")
    if len(document) > MAX_DIAGNOSTICS:
        raise ContractRefusal(
            "integrity", "limit",
            f"probe diagnostics carry at most {MAX_DIAGNOSTICS} entries; this "
            f"carries {len(document)}")
    for name, value in document.items():
        boundaries.text(name, "a probe diagnostic name")
        # THE KEY, NOT ONLY THE VALUE. Third review [P1]: the per-entry bound
        # was applied to values alone, so one 2001-character NAME passed and
        # took the durable document past the bound this function states. A
        # bound on half of an entry is not a bound on the entry.
        if len(name) > MAX_DIAGNOSTIC:
            raise ContractRefusal(
                "integrity", "limit",
                f"a probe diagnostic name is at most {MAX_DIAGNOSTIC} "
                f"characters; this one is {len(name)}")
        if type(value) is bool or value is None or type(value) is int:
            continue
        if type(value) is str and len(value) <= MAX_DIAGNOSTIC:
            continue
        raise ContractRefusal(
            "integrity", "schema",
            f"probe diagnostic {name_value(name)} is text of at most "
            f"{MAX_DIAGNOSTIC} characters, a whole number, a flag or absent; "
            f"this is {name_value(value)}")
    return document


def inquire(store, port, agent, *, attempt_id, posture, session_epoch,
            operation_id, deadline_seconds, question):
    """A CONVERSATIONAL request, acknowledged now and answered later.

    The acknowledgement is not the answer. `queued` and `delivered` are two
    facts about where the request got to, and neither of them is a model
    saying anything -- so `answered` is not a member of the acknowledgement
    set at all, and an adapter that offered one would be reporting a turn it
    has not had.
    """
    answered, committed, row, fixed = _ask(
        store, port, agent, kind="inquire", attempt_id=attempt_id,
        posture=posture, session_epoch=session_epoch,
        operation_id=operation_id, deadline_seconds=deadline_seconds,
        question=question)
    if not committed:
        # The same rule, and it matters more here: asking a model twice for
        # one operation identity is two conversational turns spent on one
        # request.
        return interrogation_of(store, operation_id)
    seen = boundaries.alternative(
        agent.inquire({**answered["agent_session_ref"],
                       "operation_id": operation_id,
                       "question": question,
                       "deadline_at": answered["deadline_at"]}),
        "an agent inquiry acknowledgement", INQUIRY_ACKNOWLEDGEMENTS)
    _same_session(seen, row, posture, session_epoch)
    return _settle(store, operation_id, _INQUIRY_OUTCOME[seen["kind"]], None)


def _bound_row(connection, interrogation):
    """The agent session an interrogation is addressed to, or a refusal.

    `settle_interrogation` compares an observation's provider identity against
    DURABLE state, exactly as the fresh probe path does -- so a caller cannot
    settle one session's interrogation with another session's reading.
    """
    row = _session_row(connection, interrogation["runtime_attempt_id"],
                       interrogation["posture"],
                       interrogation["session_epoch"])
    if row is None:
        raise ContractRefusal(
            "refused", "precondition",
            f"agent session {interrogation['posture']}/"
            f"{interrogation['session_epoch']} is gone; an observation is "
            f"about a session this manager can still name")
    return row


def _same_session(seen, row, posture, session_epoch):
    """An adapter reporting about another session reports about another
    session."""
    if "provider_session_id" not in seen:
        return
    observed = seen["provider_session_id"]
    if observed is not None:
        boundaries.injected(observed, "an observed provider session id")
    if observed != row["provider_session_id"]:
        raise ContractRefusal(
            "runtime-observation", "identity-mismatch",
            f"this answer is about provider session {name_value(observed)} "
            f"and {posture}/{session_epoch} durably names "
            f"{name_value(row['provider_session_id'])}")


def settle_interrogation(store, *, operation_id, outcome, observation=None):
    """Move one interrogation's outcome, or refuse.

    DECIDED INSIDE THE WRITE, against the exact value the update compares --
    the same rule every axis in this manager follows, and for the same reason:
    a read of the current outcome followed by a separate write is not a
    monotone axis across two manager connections.

    A TIMEOUT IS AN OBSERVATION. Moving to `timed-out` records that this
    manager stopped waiting and nothing else; the table permits an answer
    afterwards precisely because the turn may still be running.
    """
    boundaries.identity(operation_id, "an interrogation operation id")
    boundaries.text(outcome, "an interrogation outcome")
    connection = store._connection
    if observation is not None:
        # THE PUBLIC DOOR OWNS ITS OWN OPERAND. Third review [P1]: `probe`
        # owned the adapter's reading and this exported operation took one
        # straight from its caller, so a direct call could persist a
        # runtime-axis `running` as an agent-session state -- the exact
        # vocabulary collapse the previous review found, surviving at the door
        # nobody had checked.
        observation = _observation(boundaries.document(
            observation, "an interrogation observation",
            required=("kind", "state", "provider_session_id",
                      "last_activity_at", "diagnostics")))
        _same_session(observation,
                      _bound_row(connection, _require(connection,
                                                      operation_id)),
                      *_addressed(connection, operation_id))
    return _settle(store, operation_id, outcome, observation)


def _addressed(connection, operation_id):
    row = _require(connection, operation_id)
    return row["posture"], row["session_epoch"]


def _settle(store, operation_id, outcome, observation):
    """The move itself, over an observation somebody has ALREADY owned.

    PLAN 4bz splits the two doors rather than removing one of the checks, the
    same way `revive_refusal` and `_revived` are split: a caller holding a raw
    reading gets the public boundary above, and `probe` -- which has just
    applied that owner to the adapter's answer and compared its provider
    session -- gets this. Owning it twice would be the blanket revalidation
    4bz forbids.
    """
    connection = store._connection
    connection.execute("BEGIN IMMEDIATE")
    try:
        row = _require(connection, operation_id)
        # THE PAIRING, REFUSED HERE RATHER THAN BY THE DRIVER. The column's
        # two CHECKs are the last word and stay; this is the same rule said in
        # this build's own vocabulary, so a caller learns what is wrong instead
        # of receiving an `IntegrityError` from SQLite.
        if row["kind"] == "probe" and outcome == "observed":
            if observation is None:
                raise ContractRefusal(
                    "refused", "precondition",
                    f"interrogation {name_value(operation_id)} cannot be "
                    f"observed with nothing observed; the reading is what a "
                    f"probe produces, and an outcome without it is a row "
                    f"saying somebody looked and declining to say at what")
        elif observation is not None:
            raise ContractRefusal(
                "refused", "precondition",
                f"a {row['kind']} settling {name_value(outcome)} carries no "
                f"observation; only an observed probe has one")
        moves = schema.INTERROGATION_OUTCOMES[row["kind"]]
        if outcome not in moves:
            raise ContractRefusal(
                "integrity", "schema",
                f"{name_value(outcome)} is not an outcome of a {row['kind']}; "
                f"its axis is {', '.join(sorted(moves))}")
        if row["outcome"] == outcome:
            # IDEMPOTENT ON THE SAME READING, AND ONLY THAT. Third review [P1]
            # asked for this re-audit: a second settlement carrying a
            # DIFFERENT reading used to be answered with the first one, which
            # is a manager telling a caller its observation was recorded when
            # it was discarded.
            recorded = (None if row["observation"] is None
                        else json.loads(row["observation"]))
            if observation is not None and recorded != observation:
                raise ContractRefusal(
                    "refused", "already-terminal",
                    f"interrogation {name_value(operation_id)} already "
                    f"recorded a different observation; one look answers "
                    f"once, and returning the first reading for the second "
                    f"call would say this one was kept")
            answer = _view(row)
        elif outcome not in moves[row["outcome"]]:
            successors = moves[row["outcome"]]
            raise ContractRefusal(
                "runtime-observation", "state-regression",
                f"interrogation {name_value(operation_id)} is "
                f"{row['outcome']} and cannot move to {outcome}; the axis "
                f"permits "
                f"{', '.join(successors) if successors else 'no successor'}")
        else:
            # ATOMIC WITH THE TRANSITION. Re-review [P1]: the reading was an
            # argument that reached the answer and never the row, so an
            # `observed` outcome survived a restart with nothing observed in
            # it. Written in the SAME statement as the move, because a probe
            # that recorded `observed` and then failed to record what it saw
            # would leave exactly the row the schema now refuses.
            connection.execute(
                "UPDATE interrogations SET outcome = ?, settled_at = ?, "
                "observation = ? WHERE operation_id = ? AND outcome = ?",
                (outcome, store._now(),
                 None if observation is None else canonical_text(observation),
                 operation_id, row["outcome"]))
            answer = _view(_require(connection, operation_id))
    except BaseException:
        try:
            connection.execute("ROLLBACK")
        except Exception:
            pass
        raise
    connection.execute("COMMIT")
    return answer


def record_inquiry_answer(store, *, operation_id, answer):
    """The model's eventual answer, journalled at a safe turn boundary.

    SEPARATE FROM THE ACKNOWLEDGEMENT, which is the split's whole content: an
    adapter saying `delivered` said where the request got to, and this is a
    model having said something.

    It is permitted from `timed-out` as well as from `queued` and `delivered`,
    because a timeout was this manager's observation about its own waiting and
    never a statement that the turn ended.
    """
    boundaries.identity(operation_id, "an interrogation operation id")
    boundaries.document(answer, "an inquiry answer",
                        required=("body",), optional=("diagnostics",))
    boundaries.text(answer["body"], "an inquiry answer body")
    if len(answer["body"]) > MAX_ANSWER:
        raise ContractRefusal(
            "integrity", "limit",
            f"an inquiry answer body is at most {MAX_ANSWER} characters")
    # §13 BEFORE THE ROW, because this act does NOT go through `transact`.
    # Found re-auditing the prose-only classifications re-review [P1] asked
    # for: the sweep entry excused this writer on the grounds that the answer
    # rides the same journalled signature `_ask` walks, and it does not — an
    # answer arrives at its own boundary long after the request, and the
    # UPDATE below is a direct one. So an answer body carrying a live bearer
    # reached durable storage with no walk at all, which is the plain §13
    # durable rule and not a subtle case of it.
    check_no_durable_secret(answer, what="an inquiry answer")
    connection = store._connection
    connection.execute("BEGIN IMMEDIATE")
    try:
        row = _require(connection, operation_id)
        if row["kind"] != "inquire":
            raise ContractRefusal(
                "refused", "precondition",
                f"interrogation {name_value(operation_id)} is a probe; a "
                f"probe consumes no model turn and has no answer to record")
        if row["answer"] is not None:
            if json.loads(row["answer"]) != answer:
                raise ContractRefusal(
                    "refused", "already-terminal",
                    f"interrogation {name_value(operation_id)} already "
                    f"recorded a different answer; one turn answers once")
        else:
            if "answered" not in schema.INTERROGATION_OUTCOMES["inquire"][
                    row["outcome"]] and row["outcome"] != "answered":
                raise ContractRefusal(
                    "runtime-observation", "state-regression",
                    f"interrogation {name_value(operation_id)} is "
                    f"{row['outcome']}; an answer follows a request that "
                    f"reached the agent")
            connection.execute(
                "UPDATE interrogations SET answer = ?, outcome = 'answered', "
                "settled_at = ? WHERE operation_id = ? AND outcome = ?",
                (canonical_text(answer), store._now(), operation_id,
                 row["outcome"]))
        settled = _view(_require(connection, operation_id))
    except BaseException:
        try:
            connection.execute("ROLLBACK")
        except Exception:
            pass
        raise
    connection.execute("COMMIT")
    return settled


def publish_inquiry_answer(store, port, *, operation_id):
    """Publish a recorded answer into Baton, with the manager's provenance.

    A SEPARATE ACT FROM RECORDING IT, and the ordering is the ruling: a
    committed Baton request is never represented as proof that the adapter or
    the model saw anything, so nothing is published until an answer exists to
    publish. The worker holds no Baton and no SQLite capability at any point --
    the manager is the one authority client, and this is the boundary where
    that is true rather than asserted.

    Idempotent by the row: an answer published twice is one publication, and
    the second call answers with the instant the first one recorded.

    The port is NOT re-interrogated for the member it is about to be asked for.
    `AuthorityPort.__init__` types the whole session surface once, which is why
    `publish_answer` joining SESSION_OPERATIONS was a construction-time change;
    checking it again here would be the blanket revalidation 4bz forbids, and
    the inventory says so by refusing an entry owned twice.
    """
    boundaries.identity(operation_id, "an interrogation operation id")
    row = _require(store._connection, operation_id)
    if row["answer"] is None:
        raise ContractRefusal(
            "refused", "precondition",
            f"interrogation {name_value(operation_id)} has no recorded "
            f"answer; publishing what nobody answered would put this "
            f"manager's own sentence into Baton wearing a model's provenance")
    if row["published_at"] is not None:
        return _view(row)
    published = port.publish_answer(
        documents.work_ref(authority_uuid=row["authority_uuid"],
                           work_id=row["work_id"]),
        operation_id, json.loads(row["answer"])["body"])
    boundaries.injected(published, "a published answer reference")
    connection = store._connection
    connection.execute("BEGIN IMMEDIATE")
    try:
        connection.execute(
            "UPDATE interrogations SET published_at = ? "
            "WHERE operation_id = ? AND published_at IS NULL",
            (store._now(), operation_id))
        settled = _view(_require(connection, operation_id))
    except BaseException:
        try:
            connection.execute("ROLLBACK")
        except Exception:
            pass
        raise
    connection.execute("COMMIT")
    return settled


def _view(row):
    """The durable row as the outbound document, observation included.

    Re-review [P1]: this took the observation as an ARGUMENT, so only the
    caller of a fresh probe ever saw one — a replay, a lookup, a list and a
    restart all reconstructed the same row and silently omitted the reading
    that is the whole content of the operation. There is no argument now:
    what a view says is what the row holds.
    """
    observation = (None if row["observation"] is None
                   else json.loads(row["observation"]))
    return documents.interrogation(
        operation_id=row["operation_id"], kind=row["kind"],
        agent_session_ref=documents.session_ref(
            runtime_attempt_id=row["runtime_attempt_id"],
            posture=row["posture"], session_epoch=row["session_epoch"],
            provider_session_id=None),
        assignment=documents.assignment(
            work_ref=documents.work_ref(
                authority_uuid=row["authority_uuid"],
                work_id=row["work_id"]),
            participant=row["assignment_participant"],
            generation=row["assignment_generation"]),
        requested_at=row["requested_at"], deadline_at=row["deadline_at"],
        outcome=row["outcome"], settled_at=row["settled_at"],
        answered=row["answer"] is not None,
        published_at=row["published_at"],
        observation=observation)


def interrogation_of(store, operation_id):
    """One journalled interrogation, or None."""
    boundaries.identity(operation_id, "an interrogation operation id")
    row = _row(store._connection, operation_id)
    return None if row is None else _view(row)


def interrogations_of(store, attempt_id, posture, session_epoch):
    """Every interrogation addressed to one posture session, oldest first."""
    boundaries.identity(attempt_id, "a runtime attempt id")
    posture_slots._posture(posture)
    posture_slots._epoch(session_epoch)
    return [_view(boundaries.row(found, "a persisted interrogation",
                                 schema.INTERROGATION_COLUMNS))
            for found in store._connection.execute(
                "SELECT * FROM interrogations WHERE runtime_attempt_id = ? "
                "AND posture = ? AND session_epoch = ? ORDER BY requested_at, "
                "operation_id", (attempt_id, posture, session_epoch)
            ).fetchall()]
