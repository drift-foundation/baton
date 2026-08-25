"""THE AGENT SESSION: its axis, its adapter protocol, and its lifecycle.

W6627. `work/records/2026/08/finding-v12-manager-agent-session-protocols/`.
Ported from the frozen Node `agent_session_axis.mjs`, `agent_session.mjs` and
`agent_reconnect.mjs` by obligation, and extended where this Job's acceptance
names something the frozen host does not have.

THREE VOCABULARIES, NOT ONE, and this module is where they meet without
merging. The revalidation recorded in FINDING.md found the collapse this
Job's own title invites:

  the RUNTIME axis    is the container up (`attempts.py`, ten frozen axes);
  the SESSION state   is the agent inside it ready to be prompted (the nine
                      below, frozen §7.3);
  the POSTURE         is which of the two containers this is (`schema.py`).

Each answers a different question and none is derivable from another. An
`execution_runtime` of `running` says nothing about whether an agent is ready;
`agent-quiescent` says nothing about whether the container is gone; and the
posture is a label on evidence that authorizes nothing at all.

THE AXIS MOVES MONOTONICALLY AND NEVER REGRESSES -- frozen §7.3:

  not-started -> initializing -> ready -> prompting -> turn-ended -> closed
                                            |
                                            +-> cancel-requested
                                            |     -> agent-quiescent
                                            |     -> unknown
                                            +-> unknown

`unknown` IS TERMINAL AND STAYS THERE. §3.3 and §7.3 both say so, and the
reason is the whole point of the axis: `unknown` means no terminal fact was
observed. Promoting it to `closed` would record knowledge that was never
acquired -- a session record asserting that every turn the epoch started has a
terminal fact, when the honest answer is that nobody saw the ending.

AND A FINISHED CONVERSATION IS NOT AN ABSENT RUNTIME. §7.4 has one
implementation here and it always answers false: no agent-session state
satisfies the runtime-quiescence gate, because that gate is about whether the
runtime holding the generation is gone and every state on this axis is about
what an agent said.

WHAT AN AGENT ADAPTER MUST ANSWER is defined here for the first time. Nothing
in the Python distribution said it: `attempts.py` calls `agent.cancel(...)`
and types the answer, but no contract said what an adapter must carry or what
shape its answers take. `AGENT_ADAPTER` is that contract and
`SESSION_OBSERVATIONS` is the closed set of shapes an observation may be --
including POSITIVE SESSION ABSENCE, which the acceptance requires be
distinguishable from an absent runtime.

WHAT IS NOT HERE, and is named so its absence is deliberate: turns, their
deadlines and their outcomes; event normalization; agent-origin routing; and
the App Server's provider binding. This slice answers what a session IS, what
may be observed about it, and what a manager does when the answer is nothing.
"""

from types import MappingProxyType

from ..contracts import ContractRefusal, digest
from ..contracts.errors import name_value
from . import boundaries, documents, posture_slots, schema
from .handshake import certified_agent_session_profile
from .store import manager_signature

__all__ = ["SESSION_STATES", "SESSION_SUCCESSORS", "TERMINAL_SESSION_STATES",
           "AGENT_ADAPTER", "SESSION_OBSERVATIONS",
           "permits_session_transition", "satisfies_runtime_quiescence_gate",
           "open_agent_session", "adopt_provider_session",
           "observe_session_state", "close_agent_session",
           "handle_transport_loss", "reprompt_after_transport_loss",
           "transport_reachability_reidentifies", "reconcile_agent_session",
           "agent_sessions_of"]

SESSION_STATES = schema.SESSION_STATES

# WHICH STATE MAY FOLLOW WHICH. Transcribed from the frozen model rather than
# re-derived from the diagram above: the diagram shows the spine and the model
# carries the exact successor sets, including the edges the spine does not draw
# (`ready -> cancel-requested`, `turn-ended -> prompting` for a second
# supervised turn in one epoch, and the `-> closed` edges).
#
# Two rows are worth reading twice. `turn-ended -> prompting` is how one epoch
# runs a second supervised turn. And `unknown` and `closed` have EMPTY
# successor sets: both are terminal, and `unknown` is terminal in the direction
# that matters -- it never becomes `closed`, because that would be claiming an
# observation nobody made.
#
# Frozen all the way down, for the reason `attempts.TRANSITIONS` is: privacy is
# not an isolation boundary inside one process, and a table a caller could
# widen is not a table.
SESSION_SUCCESSORS = MappingProxyType({
    "not-started": ("initializing", "unknown"),
    "initializing": ("ready", "unknown", "closed"),
    "ready": ("prompting", "cancel-requested", "unknown", "closed"),
    "prompting": ("turn-ended", "cancel-requested", "unknown"),
    "turn-ended": ("prompting", "cancel-requested", "unknown", "closed"),
    "cancel-requested": ("agent-quiescent", "unknown"),
    "agent-quiescent": ("closed",),
    "unknown": (),
    "closed": (),
})

TERMINAL_SESSION_STATES = tuple(state for state in SESSION_STATES
                                if not SESSION_SUCCESSORS[state])

# WHAT AN AGENT ADAPTER MUST CARRY. Two operations, and the manager types both
# before it relies on either.
#
# `cancel` already existed as a call with no contract behind it --
# `attempts.request_cancellation` asks for it by name and nothing said an
# adapter had to have it. `observe_session` is new and is what makes positive
# session absence expressible at all: without an operation that LOOKS, absence
# could only ever be inferred from silence, which this whole design refuses.
AGENT_ADAPTER = ("cancel", "observe_session")

# WHAT `observe_session` MAY ANSWER. A closed set of SHAPES, not of names:
# knowing which alternative arrived tells you nothing if you do not then know
# what it must carry.
#
#   present  the adapter reached the provider session and reports what it
#            found. `state` is one of the nine and moves the axis through the
#            same boundary every other observation uses -- including its
#            regression refusal.
#   absent   the adapter LOOKED for the exact provider session and it is not
#            there. This is evidence, and it is evidence about an AGENT: it
#            recovers the posture and it satisfies no runtime gate, because a
#            provider process can die inside a container that is still running
#            somebody's code.
#
# There is deliberately no `unknown` or `unreachable` member. An adapter that
# could not tell reports nothing and the manager learns nothing, which is what
# `handle_transport_loss` is for -- and giving "I could not look" a place in
# this set is how it would come to be read as "there is nothing there".
SESSION_OBSERVATIONS = MappingProxyType({
    "present": (("state", "provider_session_id"), ()),
    "absent": (("provider_session_id",), ()),
})


def _state(state, what):
    """One of the nine, and the type is established with the membership.

    `x in mapping` on a list RAISES rather than answering, so a check that
    assumes the type it is checking is not owning the field -- the same defect
    `attempts.observe` was corrected for.
    """
    if type(state) is not str or state not in SESSION_SUCCESSORS:
        raise ContractRefusal(
            "integrity", "schema",
            f"{name_value(state)} is not one of the nine agent session states "
            f"({what}); the frozen §7.3 vocabulary is "
            f"{', '.join(SESSION_STATES)}")
    return state


def permits_session_transition(from_state, to_state):
    """Whether `to_state` may follow `from_state`. Pure, and the one place the
    table is read.

    AN OBSERVATION OF THE SAME STATE IS NOT A MOVE. The axis is what the relay
    has OBSERVED, and observing the same thing twice is ordinary -- so this
    permits it rather than refusing, because refusing would make a
    retransmitted frame look like a regression.
    """
    _state(from_state, "the state being moved from")
    _state(to_state, "the state being moved to")
    if from_state == to_state:
        return True
    return to_state in SESSION_SUCCESSORS[from_state]


def satisfies_runtime_quiescence_gate(state):
    """§7.4 -- the one function here that always answers false.

    A finished conversation says nothing about whether the runtime that held
    the generation is gone. The gate is satisfied only by worker-control §6.3
    runtime inspection reaching positive absence, or by W151's pinned
    certified-isolation clause. Neither is an agent-session fact, and
    `agent-quiescent` is the state most likely to be mistaken for one --
    §7.4's title is "agent quiescence is not runtime quiescence" for exactly
    that reason.

    It takes a state and PROVES it rather than ignoring its argument, because a
    caller passing a state this contract does not have is asking a malformed
    question, and answering `false` to a malformed question is how a caller
    concludes it asked a good one.
    """
    _state(state, "a state offered to the runtime-quiescence gate")
    return False


def _session_ref(session_ref):
    """The caller's §3.1 reference, PROVEN before it reaches any query.

    ALL FOUR COMPONENTS. §3.1 makes the provider session id the fourth part of
    the reference that labels evidence, and a boundary that binds three
    quarters of one moves the row held for provider session A on a report about
    B. `provider_session_id` is `None` before the provider names one and is a
    bounded opaque string afterwards; both are real answers and neither is
    absence of the member.
    """
    taken = boundaries.document(
        session_ref, "an agent session reference",
        required=("runtime_attempt_id", "posture", "session_epoch",
                  "provider_session_id"))
    boundaries.identity(taken["runtime_attempt_id"],
                        "an agent session reference's runtime attempt id")
    posture_slots._posture(taken["posture"])
    posture_slots._epoch(taken["session_epoch"])
    if taken["provider_session_id"] is not None:
        boundaries.identity(taken["provider_session_id"],
                            "an agent session reference's provider session id")
    return taken


def _session_row(connection, attempt_id, posture, session_epoch):
    """THE ONE CROSSING out of the agent_sessions table, and every column
    owned."""
    found = connection.execute(
        "SELECT * FROM agent_sessions WHERE runtime_attempt_id = ? "
        "AND posture = ? AND session_epoch = ?",
        (attempt_id, posture, session_epoch)).fetchone()
    if found is None:
        return None
    return boundaries.row(found, "a persisted agent session",
                          schema.AGENT_SESSION_COLUMNS)


def _require_session(connection, ref):
    row = _session_row(connection, ref["runtime_attempt_id"], ref["posture"],
                       ref["session_epoch"])
    if row is None:
        raise ContractRefusal(
            "refused", "precondition",
            f"no agent session {ref['posture']}/{ref['session_epoch']} for "
            f"attempt {name_value(ref['runtime_attempt_id'])}; an axis belongs "
            f"to a session")
    # THE LABEL IS BOUND BEFORE EITHER ANSWER. A no-op is still an observation:
    # affirming that provider session B's axis reads `prompting` is a claim
    # about B, and answering it from A's row is the same mistake as moving A's
    # row -- so the binding precedes every shortcut rather than sitting after
    # one.
    if row["provider_session_id"] != ref["provider_session_id"]:
        raise ContractRefusal(
            "runtime-observation", "identity-mismatch",
            f"this reference names provider session "
            f"{name_value(ref['provider_session_id'])} and epoch "
            f"{ref['posture']}/{ref['session_epoch']} durably names "
            f"{name_value(row['provider_session_id'])}; the reference labels "
            f"evidence and must be the one the session actually holds")
    return row


def _next_epoch(connection, attempt_id, posture):
    """ALWAYS THE NEXT ONE. The manager never resumes, forks or promotes a
    session, so there is no path that reuses an epoch -- and the derivation
    says so rather than a comment saying so. Consent and execution count
    separately, because they never share a connection either."""
    return connection.execute(
        "SELECT COALESCE(MAX(session_epoch), 0) + 1 AS next FROM "
        "agent_sessions WHERE runtime_attempt_id = ? AND posture = ?",
        (attempt_id, posture)).fetchone()["next"]


def _attempt(connection, attempt_id):
    found = connection.execute(
        "SELECT * FROM attempts WHERE runtime_attempt_id = ?",
        (attempt_id,)).fetchone()
    if found is None:
        raise ContractRefusal(
            "refused", "precondition",
            f"no runtime attempt {name_value(attempt_id)}")
    return boundaries.row(found, "a persisted attempt",
                          schema.ATTEMPT_COLUMNS)


def _open_operation_id(attempt_id, posture, intent):
    """The ONE fixed opening operation for this attempt, posture and intent.

    DERIVED, so a manager that restarts mid-open names the act it already
    performed instead of burning a second epoch on it. The frozen host had no
    identity here at all: a crash between the slot compare-and-set and the
    caller's answer left an epoch occupied by a session the caller never
    learned about, and the retry took the next epoch and found the posture
    taken.

    THE INTENT IS THE CALLER'S and it has to be, which is worth stating because
    an operand is a cost. Two sessions in one posture are a real thing -- the
    second begins after the first slot is recovered -- so an identity derived
    from the attempt and posture alone would replay the FIRST session's answer
    to a deliberate second opening. The caller is the only party that knows
    which of the two it means, exactly as it is for `claim_operation_id`.
    """
    return "session.open:" + digest({
        "attempt_id": attempt_id, "posture": posture, "intent": intent,
    })[len("sha256:"):]


def open_agent_session(store, port, *, attempt_id, posture, profile_digest,
                       intent):
    """Open one agent session in one posture, under one certified profile.

    The pinned acceptance:

        "It opens separate consent and execution sessions, each with a fresh
         per-posture epoch; it never resumes, forks, promotes or re-prompts
         after transport loss. Consent has no assignment/workspace/output,
         execution has the exact assignment and pinned workspace role, and
         neither receives Baton capability."

    THE THREE RULES, and where each is decided:

      1. a FRESH epoch per posture, every time -- decided here as the next one
         for this (attempt, posture), and never a reused one;
      2. the POSTURE BINDINGS -- consent has no assignment, no workspace and no
         declared output; execution has the exact fixed assignment, and its
         Work must be the session's Work, which the frozen schema's own
         description says JSON Schema cannot express;
      3. NO BATON CAPABILITY REACHES THE PROVIDER. The port is the manager's
         own participant-bound authority handle. It is READ -- once, to
         reproject the assignment an execution session claims to belong to --
         and it appears in nothing this function returns or writes.

    Rule 3 was once kept by giving this boundary no session at all, and that
    CONFLATED TWO ROLES: the trusted Worker Manager IS the one Baton authority
    client and must reproject the assignment immediately before an execution
    session exists; the untrusted agent endpoint and relay are what must never
    receive a capability. Removing the manager's handle did not prove provider
    isolation, it removed the liveness check the contract requires.
    """
    boundaries.identity(attempt_id, "a runtime attempt id")
    posture_slots._posture(posture)
    boundaries.text(profile_digest, "a certified profile digest")
    boundaries.identity(intent, "a session opening intent")
    operation_id = _open_operation_id(attempt_id, posture, intent)
    signature = manager_signature(
        "session.open", {"attempt_id": attempt_id, "posture": posture,
                         "profile_digest": profile_digest, "intent": intent})
    return store.transact(
        operation_id, "session.open", signature,
        lambda connection: _open(store, connection, port, attempt_id, posture,
                                 profile_digest))


def _open(store, connection, port, attempt_id, posture, profile_digest):
    attempt = _attempt(connection, attempt_id)
    # THE PROFILE MUST BE CERTIFIED, and read as the DOCUMENT it is. A session
    # pins a per-posture policy and a digest cannot be read for one. This is
    # W6592's public composition, consumed at its own boundary rather than
    # restated beside it -- which is what the dependency this Work waited on
    # exists to make possible.
    profile = certified_agent_session_profile(store, profile_digest)
    if profile is None:
        raise ContractRefusal(
            "policy", "profile-uncertified",
            f"nothing certifies agent-session profile "
            f"{name_value(profile_digest)} for this manager; a session pins a "
            f"policy, and one nothing has agreed to is not a policy")
    binding = profile["postures"][posture]
    if attempt["work_id"] is None or attempt["authority_uuid"] is None:
        raise ContractRefusal(
            "refused", "precondition",
            f"attempt {name_value(attempt_id)} names no Work; a session is "
            f"evidence about one and cannot be opened without it")
    assignment = None
    if posture == "execution":
        assignment = _live_assignment(port, attempt, attempt_id)
    pinned = digest(binding["policy"])
    epoch = _next_epoch(connection, attempt_id, posture)
    # ONE LIVE SESSION PER POSTURE, decided by the DATABASE, in the same
    # transaction that writes the session row. A read of MAX followed by a
    # separate insert is not an atomic allocator across two manager
    # connections.
    posture_slots._occupy_slot(connection, store._now(), attempt_id=attempt_id,
                              posture=posture, session_epoch=epoch)
    connection.execute(
        "INSERT INTO agent_sessions (runtime_attempt_id, posture, "
        "session_epoch, profile_digest, pinned_policy, work_id, "
        "authority_uuid, participant, generation, provider_session_id, "
        "state, opened_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, "
        "'not-started', ?)",
        (attempt_id, posture, epoch, profile_digest, pinned,
         attempt["work_id"], attempt["authority_uuid"],
         None if assignment is None else assignment["participant"],
         None if assignment is None else assignment["generation"],
         store._now()))
    return documents.session_opened(
        agent_session_ref=documents.session_ref(
            runtime_attempt_id=attempt_id, posture=posture,
            session_epoch=epoch, provider_session_id=None),
        profile_digest=profile_digest, pinned_policy=pinned,
        work_ref=documents.work_ref(authority_uuid=attempt["authority_uuid"],
                                    work_id=attempt["work_id"]),
        assignment=assignment, workspace=binding["workspace"],
        declared_output=binding["declared_output"], state="not-started")


def _live_assignment(port, attempt, attempt_id):
    """THE EXACT ASSIGNMENT, reprojected, and the cross-field rule the frozen
    schema's own description says JSON Schema cannot express: this assignment's
    Work is the session's Work.

    THE CACHED ROW IS NOT THE LIVE ASSIGNMENT. Consulting only the attempt's
    own copy opened an execution session cleanly against an assignment the
    authority had already fenced and ended. The manager is the authority
    client; it asks.

    AND THE HANDLE'S BINDING IS A SECOND RULE. `assignment_of` is WORK-SCOPED,
    so a session minted for another participant returns the same live
    assignment and the four-part comparison then proves the projection agrees
    with the attempt while proving nothing about who asked. The claim says
    which assignment this attempt won; the binding says who is asking.
    """
    if attempt["assignment_generation"] is None:
        raise ContractRefusal(
            "refused", "precondition",
            f"attempt {name_value(attempt_id)} is not activated; an execution "
            f"session has the exact assignment, and there is none")
    actor = port.participant
    if actor != attempt["assignment_participant"]:
        raise ContractRefusal(
            "refused", "capability",
            f"this authority session acts for {name_value(actor)} and attempt "
            f"{name_value(attempt_id)} is assigned to "
            f"{name_value(attempt['assignment_participant'])}")
    fixed = documents.assignment(
        work_ref=documents.work_ref(authority_uuid=attempt["authority_uuid"],
                                    work_id=attempt["work_id"]),
        participant=attempt["assignment_participant"],
        generation=attempt["assignment_generation"])
    live = port.assignment_of(attempt["work_id"], attempt["authority_uuid"])
    if live is None:
        raise ContractRefusal(
            "stale-assignment", "ended",
            f"{name_value(attempt['work_id'])} holds no live assignment; an "
            f"execution session belongs to one")
    if live != fixed:
        raise ContractRefusal(
            "stale-assignment", "generation",
            f"the live assignment is {name_value(live)} and this attempt is "
            f"fixed to {name_value(fixed)}")
    return fixed


def adopt_provider_session(store, *, attempt_id, posture, session_epoch,
                           provider_session_id):
    """Record the provider's own session id on an epoch that had none.

    ONCE, AND NEVER REWRITTEN. The fourth component of the §3.1 reference
    labels every piece of evidence this epoch produces; a boundary that let it
    be replaced would let a later report re-label evidence somebody already
    filed. A second adoption of the SAME id replays -- a retransmitted
    handshake is not a second session -- and a different one is an
    identity-mismatch rather than an update.
    """
    boundaries.identity(attempt_id, "a runtime attempt id")
    posture_slots._posture(posture)
    posture_slots._epoch(session_epoch)
    boundaries.identity(provider_session_id, "a provider session id")
    connection = store._connection
    connection.execute("BEGIN IMMEDIATE")
    try:
        row = _session_row(connection, attempt_id, posture, session_epoch)
        if row is None:
            raise ContractRefusal(
                "refused", "precondition",
                f"no agent session {posture}/{session_epoch} for attempt "
                f"{name_value(attempt_id)}")
        held = row["provider_session_id"]
        if held is not None:
            if held != provider_session_id:
                raise ContractRefusal(
                    "runtime-observation", "identity-mismatch",
                    f"{posture}/{session_epoch} already names provider "
                    f"session {name_value(held)} and this names "
                    f"{name_value(provider_session_id)}; the reference labels "
                    f"evidence already filed and is not re-pointed")
            adopted = False
        else:
            connection.execute(
                "UPDATE agent_sessions SET provider_session_id = ? WHERE "
                "runtime_attempt_id = ? AND posture = ? AND session_epoch = ?",
                (provider_session_id, attempt_id, posture, session_epoch))
            adopted = True
    except BaseException:
        try:
            connection.execute("ROLLBACK")
        except Exception:
            pass
        raise
    connection.execute("COMMIT")
    return documents.provider_session_adopted(
        agent_session_ref=documents.session_ref(
            runtime_attempt_id=attempt_id, posture=posture,
            session_epoch=session_epoch,
            provider_session_id=provider_session_id),
        adopted=adopted)


def observe_session_state(store, session_ref, state):
    """Move one durable session's axis, or refuse.

    DECIDED INSIDE THE WRITE TRANSACTION, for the reason the runtime
    observations already carry: a read of the current state followed by a
    separate write is not a monotone axis across two manager connections. Two
    managers both pass any read, and only the transaction decides.
    """
    connection = store._connection
    connection.execute("BEGIN IMMEDIATE")
    try:
        answer = _observe_session_state_in(connection, session_ref, state)
    except BaseException:
        try:
            connection.execute("ROLLBACK")
        except Exception:
            pass
        raise
    connection.execute("COMMIT")
    return answer


def _observe_session_state_in(connection, session_ref, state):
    """The same observation, INSIDE a caller's transaction.

    Exposed so an act that both observes and moves a posture slot is ONE
    transaction rather than two a crash can separate. The proof and the binding
    are identical; only who owns the transaction differs.
    """
    ref = _session_ref(session_ref)
    _state(state, "an observed session state")
    row = _require_session(connection, ref)
    if row["state"] == state:
        return documents.session_observed(
            agent_session_ref=ref, state=state, moved=False)
    if not permits_session_transition(row["state"], state):
        successors = SESSION_SUCCESSORS[row["state"]]
        raise ContractRefusal(
            "runtime-observation", "state-regression",
            f"agent session {ref['posture']}/{ref['session_epoch']} is "
            f"{row['state']} and cannot move to {state}; §7.3 permits "
            f"{', '.join(successors) if successors else 'no successor at all'}")
    connection.execute(
        "UPDATE agent_sessions SET state = ? WHERE runtime_attempt_id = ? "
        "AND posture = ? AND session_epoch = ?",
        (state, ref["runtime_attempt_id"], ref["posture"],
         ref["session_epoch"]))
    return documents.session_observed(agent_session_ref=ref, state=state,
                                     moved=True)


def _held_slot(connection, attempt_id, posture, session_epoch):
    """(this epoch holds the slot, the occupancy that actually holds).

    The observation is about THIS EPOCH and always lands; the slot movement is
    about the POSTURE, and a posture a later epoch has taken is not this
    report's to move. Refusing the whole act would be the other error -- epoch
    1's transport really did die, and that is true whatever the posture has
    done since.
    """
    row = posture_slots._slot_row(connection, attempt_id, posture)
    if row is None:
        return False, None
    return row["session_epoch"] == session_epoch, row["occupancy"]


def close_agent_session(store, session_ref,
                        reason="the provider session was observed closed"):
    """Observe one session CLOSED, and release the posture it held.

    SUPERSEDED BEHAVIOUR, W771: this used to write `closed` over any state that
    was not already `closed`, taking four edges §7.3 forbids -- including
    `unknown`, which §3.3 names as recording knowledge that was never acquired.
    It did that because `closed` was also the only thing that freed the
    posture, so recovering capacity required inventing an observation.

    The two facts are separate now. This is the NORMALLY OBSERVED end: the
    provider session was seen to close, the observation axis moves through its
    own boundary refusing every edge the table forbids, and the slot is
    released on that observation as positive evidence.

    A session that did NOT close normally is not this function's business.
    Transport loss goes to `handle_transport_loss`; a slot is then returned by
    `posture_slots.release_slot` with the evidence that actually established
    absence.
    """
    ref = _session_ref(session_ref)
    boundaries.text(reason, "a session close reason")
    connection = store._connection
    connection.execute("BEGIN IMMEDIATE")
    try:
        observed = _observe_session_state_in(connection, ref, "closed")
        mine, occupancy = _held_slot(connection, ref["runtime_attempt_id"],
                                     ref["posture"], ref["session_epoch"])
        if mine:
            moved = posture_slots._release_slot_in(
                connection, store._now(),
                attempt_id=ref["runtime_attempt_id"], posture=ref["posture"],
                session_epoch=ref["session_epoch"],
                evidence="provider-session-closed", reason=reason)
            occupancy = moved["occupancy"]
    except BaseException:
        try:
            connection.execute("ROLLBACK")
        except Exception:
            pass
        raise
    connection.execute("COMMIT")
    return documents.session_closed(
        agent_session_ref=ref, state=observed["state"],
        closed=observed["moved"], slot_occupancy=occupancy,
        released_slot=mine)


def handle_transport_loss(store, session_ref, *, turn_in_flight=False):
    """What a lost transport does to one epoch. §8.4.

        "A lost transport ENDS THE EPOCH. The relay never resumes and never
         re-prompts."

    AND THE REASONING IS SPECIFIC RATHER THAN GENERAL CAUTION. A turn that was
    in flight when the transport died may have completed, partially completed,
    or not started -- and it had a WRITABLE WORKSPACE. Re-prompting a fresh
    session with the same content would re-run side effects the manager cannot
    enumerate, against a workspace that already holds the first attempt's
    partial output.

    Durable: the axis moves to `unknown` through the axis boundary, so the full
    §3.1 reference is proved and bound exactly as every other observation is,
    and the slot moves to `recovery-required` in the SAME transaction -- a
    session recorded `unknown` whose posture still looked live is the state
    that composition exists to prevent. Idempotent by the axis's own rule: a
    transport does not die twice differently.

    IT REPORTS THE TURN OUTCOME AND DOES NOT RECORD IT. Recording a turn needs
    an allocated turn token, a prompt digest and the supervision window, and
    this boundary holds none of them -- inventing them here would be minting
    evidence about a turn it never saw.
    """
    ref = _session_ref(session_ref)
    if type(turn_in_flight) is not bool:
        raise ContractRefusal(
            "integrity", "schema",
            f"{name_value(turn_in_flight)} is not whether a turn was in "
            f"flight; this decides an outcome and is not inferred")
    connection = store._connection
    connection.execute("BEGIN IMMEDIATE")
    try:
        observed = _observe_session_state_in(connection, ref, "unknown")
        mine, occupancy = _held_slot(connection, ref["runtime_attempt_id"],
                                     ref["posture"], ref["session_epoch"])
        if mine and occupancy == "occupied":
            occupancy = posture_slots._require_slot_recovery_in(
                connection, store._now(),
                attempt_id=ref["runtime_attempt_id"], posture=ref["posture"],
                session_epoch=ref["session_epoch"],
                reason="the transport died and nothing observed the ending",
            )["occupancy"]
    except BaseException:
        try:
            connection.execute("ROLLBACK")
        except Exception:
            pass
        raise
    connection.execute("COMMIT")
    return documents.transport_lost(
        agent_session_ref=ref, session_state=observed["state"],
        slot_occupancy=occupancy, resume=False, reprompt=False,
        next_epoch_allowed_without_runtime_reidentification=False,
        turn_outcome="transport-lost" if turn_in_flight else None)


def reprompt_after_transport_loss(prompt):
    """§8.4 -- re-prompting after transport loss is refused, always.

    `ambiguous.operation` and not `refused.precondition`: the manager is not
    saying the request is malformed or out of order, it is saying it CANNOT
    KNOW what the first attempt did. That is the whole content of the refusal,
    and the closed pair carries it to a caller that never read §8.4.

    It takes the prompt and refuses it deliberately. A signature that accepted
    nothing would invite a caller to believe some other prompt might be
    acceptable; the refusal is about the epoch, not about what is being re-sent.
    """
    boundaries.text(prompt, "a prompt offered after transport loss")
    raise ContractRefusal(
        "ambiguous", "operation",
        f"a turn in flight when the transport died may have run side effects "
        f"the manager cannot enumerate, against a workspace that already "
        f"holds the first attempt's partial output; re-prompting is refused "
        f"and a new epoch waits for positive runtime re-identification")


def transport_reachability_reidentifies(evidence):
    """§8.4 -- transport reachability returning is not the runtime being the
    same runtime.

    The second function here that always answers false, for the same reason
    §7.4's quiescence gate does: a fact about a socket is not a fact about the
    process that held the generation. W151 §9's re-identification is what
    answers this, and it is not built in this slice -- so this says so rather
    than leaving a later caller to assume reachability was enough.
    """
    boundaries.text(evidence, "reachability evidence offered as "
                              "re-identification")
    return False


def reconcile_agent_session(store, agent, *, attempt_id, posture,
                            session_epoch):
    """ASK THE ADAPTER what it observes, and record what it answers.

    This is the session half of restart reconciliation. `reconcile_runtime`
    already answers "is the container the one this attempt owns"; nothing
    answered "is the agent inside it still there", so after a restart the
    manager's own row was the only evidence it had -- and its own row is what
    it wrote before it died.

    The two answers do different things, and keeping them apart is the point:

      PRESENT moves the axis through the ordinary observation boundary, which
      refuses a regression exactly as it would for any other report. It does
      not touch the slot: an agent that is there does not free a posture.

      ABSENT touches NO OBSERVATION at all. Absence is not one of the nine
      states -- there is no `gone` on this axis and adding one would let a
      failure to find something become a claim about what the provider did.
      What it does is RECOVER THE POSTURE, on `session-absent` evidence proved
      against the provider session id this epoch durably holds.

    AND ABSENCE OF A SESSION IS NOT ABSENCE OF A RUNTIME. The container may
    still be running somebody's code with no agent inside it; that is the whole
    reason this evidence kind exists separately, and it satisfies no runtime
    quiescence gate.
    """
    boundaries.identity(attempt_id, "a runtime attempt id")
    posture_slots._posture(posture)
    posture_slots._epoch(session_epoch)
    for operation in AGENT_ADAPTER:
        boundaries.capability(getattr(agent, operation, None),
                              f"the agent adapter's {operation}")
    row = _session_row(store._connection, attempt_id, posture, session_epoch)
    if row is None:
        raise ContractRefusal(
            "refused", "precondition",
            f"no agent session {posture}/{session_epoch} for attempt "
            f"{name_value(attempt_id)}")
    ref = documents.session_ref(
        runtime_attempt_id=attempt_id, posture=posture,
        session_epoch=session_epoch,
        provider_session_id=row["provider_session_id"])
    answer = boundaries.alternative(
        agent.observe_session(dict(ref)), "an agent session observation",
        SESSION_OBSERVATIONS)
    # THE ANSWER'S OWN MEMBERS, owned as the injected values they are. The
    # capability's callability was proved above; what it RETURNS is a separate
    # crossing, and a port that types the call and not the answer lets `None`
    # become a durable state.
    observed_id = answer["provider_session_id"]
    if observed_id is not None:
        boundaries.injected(observed_id,
                            "an observed provider session id")
    if observed_id != row["provider_session_id"]:
        raise ContractRefusal(
            "runtime-observation", "identity-mismatch",
            f"this observation is about provider session "
            f"{name_value(observed_id)} and {posture}/{session_epoch} durably "
            f"names {name_value(row['provider_session_id'])}; an adapter "
            f"reporting about another session reports about another session")
    if answer["kind"] == "present":
        state = boundaries.injected(answer["state"],
                                    "an observed session state")
        moved = observe_session_state(store, ref, state)
        return documents.session_reconciled(
            agent_session_ref=ref, found="present", state=moved["state"],
            moved=moved["moved"], slot=None)
    if observed_id is None:
        # ABSENCE OF A NAME IS NOT ABSENCE OF A SESSION. An epoch that never
        # learned a provider session id has no identity anybody can have
        # looked for, so "it is not there" is a statement about nothing. The
        # refusal names that rather than letting the release boundary answer
        # about a missing operand.
        raise ContractRefusal(
            "refused", "precondition",
            f"{posture}/{session_epoch} names no provider session, so nothing "
            f"can have been observed absent for it; an adapter reporting "
            f"absence names the session it looked for")
    slot = posture_slots.release_slot(
        store, attempt_id=attempt_id, posture=posture,
        session_epoch=session_epoch, evidence="session-absent",
        observed_identity=observed_id,
        reason="the adapter observed this provider session absent")
    return documents.session_reconciled(
        agent_session_ref=ref, found="absent", state=row["state"],
        moved=False, slot=slot["occupancy"])


def _live_session_of(connection, attempt_id, posture):
    """The session this posture's slot is CURRENTLY held by, or None.

    THE SLOT DECIDES, not the axis. Asking the sessions table for "the newest
    epoch" would name a session whose posture has already been recovered --
    which is a session nobody is talking to -- and asking the axis for "not
    terminal" would rebuild occupancy out of observations, which is the exact
    coupling W771 separated.
    """
    slot = posture_slots._slot_row(connection, attempt_id, posture)
    if slot is None or slot["occupancy"] != "occupied":
        return None
    return _session_row(connection, attempt_id, posture,
                        slot["session_epoch"])


def _request_session_quiescence(connection, attempt_id):
    """Announce `cancel-requested` on the live EXECUTION session's axis.

    ADDED WITHOUT REORDERING ANYTHING. `attempts.request_cancellation` fences
    at the authority, then orders the agent, then the runtime, and this changes
    none of it: it records the manager's intent on the session axis in the same
    place the runtime axis's own `cancel-requested` is recorded -- before the
    agent is asked -- so the durable state says what was intended if the
    process dies between the two boundaries.

    IT ANNOUNCES AND NEVER CONCLUDES. `agent-quiescent` is what the provider
    was OBSERVED to reach, and no announcement here may write it; the axis's
    own table is what refuses if this is asked from a state §7.3 does not
    permit it from.

    CONSENT IS NOT TOUCHED. A consent container is never cancelled mid-turn --
    that asymmetry is the M6617 topology written into the frozen runtime enums
    -- and a cancellation is about the assignment an execution session belongs
    to.
    """
    boundaries.identity(attempt_id, "a runtime attempt id")
    row = _live_session_of(connection, attempt_id, "execution")
    if row is None:
        return documents.session_quiescence_requested(
            agent_session_ref=None, requested=False, state=None,
            why=f"no execution session holds the posture of attempt "
                f"{name_value(attempt_id)}; there is no conversation to "
                f"interrupt")
    ref = documents.session_ref(
        runtime_attempt_id=attempt_id, posture="execution",
        session_epoch=row["session_epoch"],
        provider_session_id=row["provider_session_id"])
    if not permits_session_transition(row["state"], "cancel-requested"):
        # NOT A FAILURE. A session already `agent-quiescent`, `closed` or
        # `unknown` has nothing left to interrupt, and refusing the whole
        # cancellation because the conversation had already ended would leave a
        # fenced runtime running.
        return documents.session_quiescence_requested(
            agent_session_ref=ref, requested=False, state=row["state"],
            why=f"execution/{row['session_epoch']} is {row['state']}, from "
                f"which §7.3 does not permit cancel-requested")
    moved = _observe_session_state_in(connection, ref, "cancel-requested")
    return documents.session_quiescence_requested(
        agent_session_ref=ref, requested=True, state=moved["state"],
        why=None)


def agent_sessions_of(store, attempt_id):
    """Every session opened for this attempt, oldest first per posture."""
    boundaries.identity(attempt_id, "a runtime attempt id")
    return [boundaries.row(found, "a persisted agent session",
                           schema.AGENT_SESSION_COLUMNS)
            for found in store._connection.execute(
                "SELECT * FROM agent_sessions WHERE runtime_attempt_id = ? "
                "ORDER BY posture, session_epoch", (attempt_id,)).fetchall()]
