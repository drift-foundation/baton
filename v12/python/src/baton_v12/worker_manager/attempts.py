"""THE RUNTIME ATTEMPT: its axes, its observations, and its activation.

W4 cut D (PLAN item 4be), first slice. Ported from the frozen Node
`attempts.mjs` by obligation.

The offer slice ended with a recorded claim. This is what may happen next, and
the ordering is the content:

  1. an accepted offer's attempt is RECORDED, under an operation identity that
     signs every durable operand;
  2. `activate_assignment` binds the attempt to THIS attempt's own committed
     claim, through the participant-bound session, and fixes all four parts of
     the assignment before anything writable runs;
  3. observations move along PER-AXIS transitions, decided and written in one
     transaction against the expected current state, and journalled by source
     identity so an exact duplicate replays while a conflicting one refuses.

WHAT IS NOT HERE, and is the next slice's: runtime start, reconciliation and
cancellation ordering -- which introduce the injected runtime adapter and agent
boundaries -- and then output freeze, intake and cleanup. The frozen host slices
itself the same way and for the same reason: what a conforming adapter must BE
is a later item's to pin, and until then positive absence cannot be proven.

THE VOCABULARY AND THE TRANSITIONS ARE DIFFERENT THINGS. The schema's CHECK
constraints say what an axis may SAY; the map below says what may FOLLOW what.
Treating the vocabulary's order as a transition order is how
`worker_disposition=completed` once advanced to `unable` -- a different terminal
ANSWER, not a later stage of the same one.
"""

from types import MappingProxyType

from ..contracts import ContractRefusal, digest
from ..contracts.errors import name_value
from . import boundaries, documents, oci, schema, sessions, workspaces
from .store import manager_signature

# `_fixed_assignment` is PRIVATE until something outside this module needs it.
# It projects an attempt row this build has already adopted, and an exported
# projector over an unowned dict would be a boundary nobody owns.
# The three DERIVED identities are private for the same reason
# `_fixed_assignment` is: each projects an attempt row this build has already
# adopted, and an exported projector over an unowned dict is a boundary nobody
# owns. They become public when something outside this module needs to name the
# act -- which is what a restart will need, and is the next slice's to arrange.
__all__ = ["TRANSITIONS", "AXES", "record_attempt", "observe",
           "activate_assignment", "request_runtime_start",
           "reconcile_runtime", "request_cancellation"]


def _frozen(moves):
    return MappingProxyType({axis: MappingProxyType(
        {state: tuple(after) for state, after in states.items()})
        for axis, states in moves.items()})


# WHAT MAY FOLLOW WHAT, per axis. Frozen all the way down, for the reason the
# contracts layer's error pairing is: privacy is not an isolation boundary
# inside one process, and a transition map a caller could widen is not a map.
TRANSITIONS = _frozen({
    # `uncertain` is where the two runtime axes are deliberately asymmetric: it
    # may return to a positive observation, and it may NEVER become
    # `destroyed`. Destruction is a fact about the world, and inferring it from
    # a failure to look would report a cleaned-up runtime that is still
    # executing somebody's code.
    "consent_runtime": {
        "not-started": ["running", "uncertain", "destroyed"],
        "running": ["quiescent", "uncertain", "destroyed"],
        "quiescent": ["uncertain", "destroyed"],
        "uncertain": ["running", "quiescent"],
        "destroyed": [],
    },
    "execution_runtime": {
        # A COLD START CAN DISCOVER ANY OF THESE. At restart the local axis is
        # `not-started` while a runtime may already exist, so reconciliation
        # must be able to record what it finds -- including positive
        # destruction -- without inventing an intermediate state nobody
        # observed.
        #
        # CANCELLATION IS REACHABLE FROM EVERY NONTERMINAL STATE. One ambiguous
        # inspection must not disable the safety response to stronger later
        # evidence: mismatch and multiplicity can be discovered from any state
        # in which the manager is still looking.
        "not-started": ["start-requested", "running", "cancel-requested",
                        "uncertain", "destroyed"],
        "start-requested": ["running", "cancel-requested", "uncertain",
                            "destroyed"],
        "running": ["cancel-requested", "stopping", "quiescent", "uncertain",
                    "destroyed"],
        "cancel-requested": ["stopping", "quiescent", "uncertain", "destroyed"],
        "stopping": ["quiescent", "uncertain", "destroyed"],
        "quiescent": ["cancel-requested", "uncertain", "destroyed"],
        "uncertain": ["running", "cancel-requested", "stopping", "quiescent"],
        "destroyed": [],
    },
    "output": {
        "open": ["freeze-requested", "invalid", "discarded"],
        "freeze-requested": ["frozen", "invalid"],
        "frozen": ["sealed", "invalid", "discarded"],
        "invalid": ["discarded"],
        "sealed": ["discarded"],
        "discarded": [],
    },
    # EVERY disposition below is a terminal ALTERNATIVE. One answer is chosen,
    # and the others never follow it.
    "worker_disposition": {
        "none": ["completed", "unable", "plan-rejected", "cancelled"],
        "completed": [], "unable": [], "plan-rejected": [], "cancelled": [],
    },
    "proposal": {
        "none": ["publish-requested"],
        "publish-requested": ["published"],
        "published": ["superseded"],
        "superseded": [],
    },
    "verification": {
        "none": ["passed", "failed", "unable"],
        "passed": [], "failed": [], "unable": [],
    },
    "technical_review": {
        "none": ["accepted", "changes-requested", "rejected"],
        "accepted": [], "changes-requested": [], "rejected": [],
    },
    "approval": {"none": ["approved", "denied"], "approved": [], "denied": []},
    "integration": {"none": ["integrated", "failed"], "integrated": [],
                    "failed": []},
    "cleanup": {
        "pending": ["blocked-on-intake", "complete", "retained", "failed"],
        "blocked-on-intake": ["complete", "retained", "failed"],
        "complete": [], "retained": [], "failed": [],
    },
})

AXES = tuple(TRANSITIONS)

# The four parts of an assignment, as this table stores them.
ASSIGNMENT_COLUMNS = ("authority_uuid", "work_id", "assignment_participant",
                      "assignment_generation")


def _attempts(store, where, operands=()):
    """THE ONE CROSSING out of the attempts table, and every row owned.

    The same rule the offers table follows, for the same reason: a read site is
    a chance to forget, and there is one.
    """
    return [boundaries.row(record, "a persisted attempt",
                           schema.ATTEMPT_COLUMNS)
            for record in store._connection.execute(
                "SELECT * FROM attempts " + where, operands).fetchall()]


def _attempt_row(store, attempt_id):
    """The attempt, or ABSENCE -- and the two are different answers.

    A well-formed id naming nothing is an absence; an id that is not an id is a
    REFUSAL. Conflating them tells a caller "no such attempt" about a question
    that was never asked.
    """
    boundaries.identity(attempt_id, "a runtime attempt id")
    found = _attempts(store, "WHERE runtime_attempt_id = ?", (attempt_id,))
    return found[0] if found else None


def _require_attempt(store, attempt_id):
    attempt = _attempt_row(store, attempt_id)
    if attempt is None:
        raise ContractRefusal("refused", "precondition",
                              f"no runtime attempt {name_value(attempt_id)}")
    return attempt


def _fixed_assignment(attempt):
    """The four-part identity activation fixed, or None.

    Never three quarters of one: the schema's CHECK keeps the four columns
    together, and this reads them together so no caller can compare a subset.
    """
    if attempt["assignment_generation"] is None:
        return None
    return documents.assignment(
        work_ref=documents.work_ref(
            authority_uuid=attempt["authority_uuid"],
            work_id=attempt["work_id"]),
        participant=attempt["assignment_participant"],
        generation=attempt["assignment_generation"])


def record_attempt(store, *, attempt_id, adapter_name, adapter_digest,
                   profile_digest, input_digest=None, policy_digest=None,
                   image_digest=None, toolchain_digest=None):
    """Record the attempt an accepted offer named.

    EVERY DURABLE OPERAND RIDES THE SIGNATURE. The frozen host signed three of
    eight, so a changed adapter name or input digest replayed instead of
    colliding -- an operation identity that ignores operands is not an identity.
    """
    boundaries.identity(attempt_id, "a runtime attempt id")
    boundaries.text(adapter_name, "an adapter name")
    boundaries.text(adapter_digest, "an adapter digest")
    boundaries.text(profile_digest, "an attempt's profile digest")
    # THE OPTIONAL DIGESTS ARE OPERANDS TOO. An optional operand is exactly the
    # kind a sweep by imagination misses, and each of these reaches a TEXT
    # column and the signature.
    _optional(input_digest, "an attempt's input digest")
    _optional(policy_digest, "an attempt's policy digest")
    _optional(image_digest, "an image digest")
    _optional(toolchain_digest, "a toolchain digest")
    operands = {"attempt_id": attempt_id, "adapter_name": adapter_name,
                "adapter_digest": adapter_digest,
                "profile_digest": profile_digest, "input_digest": input_digest,
                "policy_digest": policy_digest, "image_digest": image_digest,
                "toolchain_digest": toolchain_digest}
    signature = manager_signature("attempt.record", operands)

    def act(connection):
        connection.execute(
            "INSERT INTO attempts (runtime_attempt_id, adapter_name, "
            "adapter_digest, profile_digest, input_digest, policy_digest, "
            "image_digest, toolchain_digest, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (attempt_id, adapter_name, adapter_digest, profile_digest,
             input_digest, policy_digest, image_digest, toolchain_digest,
             store._now()))
        return documents.attempt_recorded(attempt_id=attempt_id,
                                          adapter_name=adapter_name,
                                          profile_digest=profile_digest)

    return store.transact(f"attempt.record:{attempt_id}", "attempt.record",
                          signature, act)


def _optional(value, what):
    """An operand that may be absent -- and is owned when it is not.

    Absence and a value are different answers, so the rule is applied to the
    value rather than to whether the caller mentioned it.
    """
    # A LITERAL IN THE LABEL, even here. A shared owner whose label is entirely
    # the caller's noun is one the inventory cannot attribute and a probe cannot
    # assert -- the machinery caught this the moment the helper was written, for
    # the second time in this campaign.
    if value is not None:
        boundaries.text(value, f"{what}, when it is given,")
    return value


def _claim_of(store, attempt_id):
    """THIS attempt's own committed claim, or None.

    Review [P1] in the frozen host: activation accepted any free-standing
    attempt beside any currently live assignment. A live assignment somewhere in
    the authority is not evidence that this attempt's accepted offer claimed it
    -- and without that link a foreign session could activate somebody else's
    attempt onto its own Work.

    EXACTLY ONE, and the count is asked for rather than assumed. The unique
    index makes two impossible going forward; this fails closed against a store
    written before it, because "which of these two is this attempt's claim" has
    no answer a manager may guess at.
    """
    from .offers import claimed_offers_for
    found = claimed_offers_for(store, attempt_id)
    if len(found) > 1:
        raise ContractRefusal(
            "integrity", "schema",
            f"attempt {name_value(attempt_id)} has {len(found)} claimed "
            f"offers; one attempt belongs to one offer, and choosing between "
            f"them by row order would be inventing an answer")
    return found[0] if found else None


def activate_assignment(store, port, *, attempt_id, expect):
    """Step 1: bind the attempt to its OWN claim, through its own session.

    Three separate things must agree before anything writable runs: the
    session's binding, this attempt's committed claim, and the authority's live
    assignment. ANY TWO AGREEING IS NOT ENOUGH -- that is exactly how a foreign
    session or a replayed activation gets in.
    """
    attempt = _require_attempt(store, attempt_id)
    expected = boundaries.document(expect, "the expected assignment",
                                   required=documents.ASSIGNMENT)
    boundaries.document(expected["work_ref"],
                        "the expected assignment's Work reference",
                        required=documents.WORK_REF)
    boundaries.text(expected["work_ref"]["authority_uuid"],
                    "the expected assignment's authority")
    boundaries.identity(expected["work_ref"]["work_id"],
                        "the expected assignment's Work")
    boundaries.text(expected["participant"],
                    "the expected assignment's participant")
    boundaries.generation(expected["generation"],
                          "the expected assignment's generation")
    if expected["participant"] != port.participant:
        raise ContractRefusal(
            "refused", "precondition",
            f"this session acts for {name_value(port.participant)} and the "
            f"activation names {name_value(expected['participant'])}; an "
            f"assignment is activated by the identity that holds it")
    claim = _claim_of(store, attempt_id)
    if claim is None:
        raise ContractRefusal(
            "refused", "precondition",
            f"attempt {name_value(attempt_id)} has no committed claim; a live "
            f"assignment elsewhere in the authority is not evidence that this "
            f"attempt's offer claimed it")
    claimed = documents.assignment(
        work_ref=documents.work_ref(authority_uuid=claim["authority_uuid"],
                                    work_id=claim["work_id"]),
        participant=claim["participant"],
        generation=claim["claim_generation"])
    if claimed != expected:
        raise ContractRefusal(
            "stale-assignment", "generation",
            f"attempt {name_value(attempt_id)} claimed "
            f"{_differing(claimed, expected)}")
    signature = manager_signature("assignment.activate",
                                  {"attempt_id": attempt_id,
                                   "expect": expected})
    # THE JOURNAL ANSWERS FIRST, before anything is synthesized from current
    # state.
    #
    # Review [P1]: the already-fixed branch below returned an answer built from
    # the row, so the FIRST call committed `already_fixed=False` and a later
    # exact retry answered `already_fixed=True` -- while a contender that had
    # read before the commit replayed the journalled False. One act, two
    # answers, chosen by when the retry arrived. The manager's journal exists so
    # an exact retry reproduces the recorded bytes, and a branch that steps
    # around it is not a replay however reasonable its answer looks.
    #
    # A DIFFERENT `expect` still collides here rather than replaying, because
    # the signature carries it -- and it is reached only after the claim
    # comparison above, so a foreign activation is refused as a precondition
    # rather than as a collision.
    already = _fixed_assignment(attempt)
    # FIXED ONCE, and compared on ALL FOUR parts. Comparing Work and generation
    # alone let a later activation replay under another participant or
    # authority.
    #
    # DECIDED BEFORE THE JOURNAL IS ASKED, because this is a precondition about
    # the ATTEMPT rather than about this operation's identity: an activation
    # naming another assignment is refused with what actually differs, not with
    # an operation collision that says only that the operands changed.
    if already is not None and already != expected:
        raise ContractRefusal(
            "stale-assignment", "generation",
            f"attempt {name_value(attempt_id)} is fixed to a different "
            f"assignment: {_differing(already, expected)}")
    found, recorded = store.replay(f"assignment.activate:{attempt_id}",
                                   signature, kind="assignment.activate")
    if found:
        return recorded
    if already is not None:
        # NO JOURNAL ROW AND A FIXED ROW: this build did not write it, or it
        # was written under another identity. The assignment is reported as it
        # STANDS, which is the honest answer when there is no recorded act to
        # reproduce.
        return documents.assignment_activated(
            attempt_id=attempt_id, assignment=already, already_fixed=True)
    live = port.assignment_of(expected["work_ref"]["work_id"],
                              expected["work_ref"]["authority_uuid"])
    if live is None:
        raise ContractRefusal(
            "stale-assignment", "ended",
            f"{name_value(expected['work_ref']['work_id'])} holds no live "
            f"assignment; nothing writable may run against an assignment that "
            f"has ended")
    if live != expected:
        raise ContractRefusal(
            "stale-assignment", "generation",
            f"the live assignment carries {_differing(live, expected)}")
    def act(connection):
        changed = connection.execute(
            "UPDATE attempts SET work_id = ?, authority_uuid = ?, "
            "assignment_generation = ?, assignment_participant = ? "
            "WHERE runtime_attempt_id = ? AND assignment_generation IS NULL",
            (expected["work_ref"]["work_id"],
             expected["work_ref"]["authority_uuid"], expected["generation"],
             expected["participant"], attempt_id)).rowcount
        if changed != 1:
            raise ContractRefusal(
                "refused", "precondition",
                f"attempt {name_value(attempt_id)} was activated by another "
                f"act")
        return documents.assignment_activated(
            attempt_id=attempt_id, assignment=expected, already_fixed=False)

    return store.transact(f"assignment.activate:{attempt_id}",
                          "assignment.activate", signature, act)


def _differing(found, expected):
    """Which PART of two assignments disagrees.

    "a dict and a dict" is a true sentence about two identities and tells a
    reader nothing. §4 says an identity is four parts, so a mismatch is reported
    as the parts that differ -- and my own first case for this was what found
    the useless message.
    """
    parts = []
    for member in ("authority_uuid", "work_id"):
        if found["work_ref"][member] != expected["work_ref"][member]:
            parts.append(f"{member} {name_value(found['work_ref'][member])} "
                         f"where this activation names "
                         f"{name_value(expected['work_ref'][member])}")
    for member in ("participant", "generation"):
        if found[member] != expected[member]:
            parts.append(f"{member} {name_value(found[member])} where this "
                         f"activation names {name_value(expected[member])}")
    return "; ".join(parts) if parts else "matches on every part"


def observe(store, *, attempt_id, axis, value, source=None):
    """One observation, DECIDED AND WRITTEN atomically.

    Review [P1] in the frozen host: this read the current value, checked it in
    the host language, and wrote unconditionally outside any transaction -- so a
    stale observer could overwrite a newer value between the two. The transition
    is decided INSIDE the write, against the exact value the update compares.

    It is also journalled by SOURCE IDENTITY. An exact duplicate -- same
    incarnation, same source sequence, same observed digest -- replays; a
    conflicting one refuses, which is what makes "the same observation again"
    answerable at all.
    """
    # THE TYPE IS ESTABLISHED BEFORE THE MEMBERSHIP QUESTION, in the same
    # expression. Review [P1]: `x in mapping` on a list RAISES rather than
    # answering, so an exact-POD list escaped both of these closed sets as a raw
    # `TypeError` while the inventory declared them owned. This is the same
    # defect the sealed refusal's pairing was corrected for one round ago, and
    # the same remedy: a check that assumes the type it is checking is not
    # owning the field.
    if type(axis) is not str or axis not in TRANSITIONS:
        raise ContractRefusal(
            "integrity", "schema",
            f"{name_value(axis)} is not one of the frozen runtime-attempt "
            f"axes")
    moves = TRANSITIONS[axis]
    if type(value) is not str or value not in moves:
        raise ContractRefusal(
            "integrity", "schema",
            f"{name_value(value)} is not a value of {axis}; the axes are "
            f"frozen by the runtime-attempt manifest")
    incarnation, source_seq = _source_identity(store, source)
    # A SAVEPOINT rather than a transaction, because `observe` is also called
    # from inside a journalled action -- a later slice records
    # `start-requested` within the runtime-start operation's own transaction,
    # and a nested BEGIN would refuse. A savepoint is the same all-or-nothing
    # boundary at either depth, and the name is DERIVED rather than
    # interpolated from caller text, because a savepoint name cannot be bound
    # as a parameter.
    mark = f"observe_{abs(hash((attempt_id, axis))) % 10 ** 12}"
    connection = store._connection
    connection.execute(f"SAVEPOINT {mark}")
    try:
        answer = _decide(store, attempt_id, axis, value, moves, incarnation,
                         source_seq, source)
    except BaseException as failure:
        try:
            connection.execute(f"ROLLBACK TO {mark}")
        except Exception:
            pass
        try:
            connection.execute(f"RELEASE {mark}")
        except Exception:
            pass
        if _is_contention(failure):
            # A LOCKED DATABASE is a fact about the file, and at THIS boundary
            # it means exactly one thing: another writer is deciding this
            # attempt, so this observation did not land and the value it would
            # have overwritten is somebody else's newer one. The conditional
            # UPDATE's row count says the same thing when it gets to run; when
            # it cannot run at all, the caller is entitled to the same answer
            # rather than to SQLite's vocabulary.
            raise ContractRefusal(
                "runtime-observation", "state-regression",
                f"{axis} is being decided by another writer; this observation "
                f"did not land ({name_value(str(failure))})") from None
        raise
    connection.execute(f"RELEASE {mark}")
    return answer


def _is_contention(failure):
    """Whether a storage failure is CONTENTION and nothing else.

    ONLY SQLite's own result code decides. The frozen host matched a substring
    of the free-form message, and a trigger raising `busy provider invariant`
    was consequently handed a database lock's meaning and retry policy -- the
    message is APPLICATION-CONTROLLED prose. A constraint, a trigger's abort, a
    disk or schema fault keeps its own identity, because giving one a portable
    meaning it does not have hands a caller the wrong retry policy with full
    confidence.

    The low byte is the primary code and the high bits are the extended reason,
    so a trigger abort's 1811 is compared as SQLITE_CONSTRAINT rather than as
    itself.
    """
    code = getattr(failure, "sqlite_errorcode", None)
    if type(code) is not int:
        return False
    return code & 0xFF in (_SQLITE_BUSY, _SQLITE_LOCKED)


_SQLITE_BUSY = 5
_SQLITE_LOCKED = 6


def _source_identity(store, source):
    """WHO reported this, under WHICH sequence.

    A manager-internal observation mints a fresh sequence at every call: there
    is no identity for anyone else to reuse, so there is nothing to replay and
    nothing to conflict with.
    """
    if source is None:
        return (store.incarnation, None)
    taken = boundaries.document(source, "an observation source",
                                required=("incarnation", "seq"))
    boundaries.text(taken["incarnation"], "an observation source's incarnation")
    if type(taken["seq"]) is not int or taken["seq"] < 0:
        raise ContractRefusal(
            "integrity", "schema",
            f"an observation source's sequence counts from zero; this is "
            f"{name_value(taken['seq'])}")
    return (taken["incarnation"], taken["seq"])


def _next_source_seq(store, attempt_id, incarnation):
    # NOTHING TO OWN, and saying so beats owning it. `COALESCE(MAX(x), 0) + 1`
    # over a STRICT INTEGER column is a whole number by construction: the column
    # cannot hold anything else, and the empty case is the COALESCE. I wrote a
    # `boundaries.count_of` here first and could not drive it -- the fourth
    # unreachable boundary this campaign has made me delete rather than leave
    # standing as decoration.
    return store._connection.execute(
        "SELECT COALESCE(MAX(source_seq), 0) + 1 AS next FROM observations "
        "WHERE runtime_attempt_id = ? AND incarnation = ?",
        (attempt_id, incarnation)).fetchone()["next"]


def _decide(store, attempt_id, axis, value, moves, incarnation, source_seq,
            source):
    attempt = _require_attempt(store, attempt_id)
    # THE DIGEST IS COMPUTED AFTER THE ATTEMPT IS OWNED. Canonicalization
    # refuses an unstorable id with its own diagnostic, so composing it first
    # answered "this is not a digestible document" to a caller whose actual
    # mistake was naming an attempt that cannot exist.
    observed = digest({"attempt_id": attempt_id, "axis": axis, "value": value})
    # THE DURABLE IDENTITY IS RESOLVED FIRST, before today's axis is consulted
    # at all.
    #
    # Review [P1] in the frozen host: the current-value shortcut and the
    # transition check ran ahead of it, so an EXACT old observation was refused
    # once the axis had advanced, while a DIFFERENT observation reusing the same
    # source identity slipped through whenever its axis already held the
    # requested value. Both invert the pinned rule: what a source identity
    # already said is a fact about THAT IDENTITY, and today's axis has no
    # bearing on it.
    if source_seq is None:
        source_seq = _next_source_seq(store, attempt_id, incarnation)
    prior = store._connection.execute(
        "SELECT observation_digest FROM observations WHERE "
        "runtime_attempt_id = ? AND incarnation = ? AND source_seq = ?",
        (attempt_id, incarnation, source_seq)).fetchone()
    if prior is not None:
        if boundaries.text(prior["observation_digest"],
                           "a recorded observation digest") != observed:
            raise ContractRefusal(
                "runtime-observation", "state-regression",
                f"incarnation {name_value(incarnation)} already reported a "
                f"different observation at source sequence {source_seq}")
        # An exact replay returns the recorded answer and changes nothing --
        # never a regression of whatever came after it.
        return documents.observation(attempt_id=attempt_id, axis=axis,
                                     value=value, changed=False, replayed=True)
    current = attempt[axis]
    # AN ACCEPTED OBSERVATION CONSUMES ITS SOURCE IDENTITY, whether or not it
    # moved an axis. An inert sourced observation that wrote no row left its
    # identity reusable, and a DIFFERENT observation could then commit under it
    # -- which makes the identity's meaning depend on where the axis already
    # was, and the whole point of the identity is that it does not.
    if current == value and source is None:
        return documents.observation(attempt_id=attempt_id, axis=axis,
                                     value=value, changed=False)
    if current != value:
        if value not in moves[current]:
            raise ContractRefusal(
                "runtime-observation", "state-regression",
                f"{axis} is {name_value(current)}; {name_value(value)} does "
                f"not follow it")
        changed = store._connection.execute(
            f"UPDATE attempts SET {axis} = ?, "
            f"observation_seq = observation_seq + 1, observed_at = ? "
            f"WHERE runtime_attempt_id = ? AND {axis} = ?",
            (value, store._now(), attempt_id, current)).rowcount
        if changed != 1:
            raise ContractRefusal(
                "runtime-observation", "state-regression",
                f"{axis} moved while this observation was being decided")
    # The same STRICT INTEGER guarantee, for the same reason.
    manager_seq = store._connection.execute(
        "SELECT COALESCE(MAX(manager_seq), 0) + 1 AS next FROM "
        "observations WHERE runtime_attempt_id = ?",
        (attempt_id,)).fetchone()["next"]
    store._connection.execute(
        "INSERT INTO observations (runtime_attempt_id, incarnation, "
        "source_seq, runtime_id, observation_digest, manager_seq, observed_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (attempt_id, incarnation, source_seq, attempt["runtime_id"], observed,
         manager_seq, store._now()))
    return documents.observation(attempt_id=attempt_id, axis=axis, value=value,
                                 changed=current != value,
                                 manager_seq=manager_seq)


# -- step 2: the runtime -----------------------------------------------------


def _runtime_labels(attempt):
    """The labels every runtime this manager starts must carry.

    ALL FOUR PARTS OF THE ASSIGNMENT. The frozen host omitted the participant,
    so two participants' runtimes on one Work and generation were
    indistinguishable by label -- and the whole reconciliation below decides by
    comparing labels.

    AND THE POLICY THE DELIVERY IS MADE UNDER. W6632 review [P1]: the resolved
    identity is image, profile, policy and adapter, and reconciliation has to
    be able to prove all four of a runtime it adopts. The engine reports the
    image itself; the policy digest exists nowhere but here.

    A CONSEQUENCE WORTH NAMING: `policy_digest` is nullable on the attempt row,
    so an attempt recorded without one can no longer start a runtime. That is
    the right answer rather than an accident -- a delivery whose policy this
    manager cannot name exactly is one no later reconciliation can describe --
    but it is a lifecycle rule this Job reached rather than one it owns, and it
    is refused HERE with a message that says so instead of surfacing as a
    digest complaint about `None` from two layers down.
    """
    if attempt["policy_digest"] is None:
        raise ContractRefusal(
            "refused", "precondition",
            f"attempt {name_value(attempt['runtime_attempt_id'])} records no "
            f"policy digest; a runtime is labelled with the policy its "
            f"delivery is made under, and reconciliation after a restart has "
            f"no other way to learn what this worker was started to obey")
    return documents.runtime_labels(
        runtime_attempt_id=attempt["runtime_attempt_id"],
        authority_uuid=attempt["authority_uuid"],
        work_id=attempt["work_id"],
        participant=attempt["assignment_participant"],
        generation=attempt["assignment_generation"],
        profile_digest=attempt["profile_digest"],
        policy_digest=attempt["policy_digest"],
        adapter_digest=attempt["adapter_digest"])


def _start_operation_id(attempt):
    """The ONE fixed start operation for an attempt.

    DERIVED, so a restart and the adapter can both name the act this manager
    performed without having watched it.
    """
    return "runtime.start:" + digest({
        "attempt_id": attempt["runtime_attempt_id"],
        "assignment": _fixed_assignment(attempt),
        "profile_digest": attempt["profile_digest"],
    })[len("sha256:"):]


def _plan_agrees(adapter, attempt_id, inputs):
    """An adapter's DECLARED mount plan, held to the root this manager proved.

    A plan is read only where one is declared. `mounts` is an attribute of the
    OCI adapter's assignment-scoped construction rather than a method of the
    seam, so an adapter that has none is not a mount planner and there is
    nothing here to compare -- and requiring the attribute would make every
    narrow adapter declare a plan it does not have. That is why the adapter's
    own refusal is the boundary and this one is the earlier moment: this saves
    a journalled operation, and cannot be the thing that makes the manager
    safe.
    """
    plan = getattr(adapter, "mounts", None)
    if plan is None:
        return
    # THE ADAPTER'S OWN SPELLING RULES, CALLED rather than reimplemented.
    #
    # W19784 third review [P1]: this normalized the target and resolved the
    # source before comparing them, so `/else/../input` arrived here already
    # collapsed to `/input` and `<inputs>/../inputs` already collapsed to the
    # proved source. Both were accepted, the start was journalled, the adapter
    # was invoked -- and only then did the adapter refuse them, correctly,
    # leaving this manager an operation to settle for a plan that could never
    # have been mounted.
    #
    # A guard written as a paraphrase of another guard agrees with it until it
    # doesn't, and the difference shows up exactly where it costs most. These
    # are `oci.canonical_target` and `oci.canonical_source` themselves, so the
    # earlier moment and the boundary cannot drift apart.
    landing = []
    for mount in plan:
        one = boundaries.document(mount, "a declared runtime mount",
                                  required=("source", "target", "writable"))
        if oci.canonical_target(one["target"],
                                "a declared mount target") == oci.INPUT_TARGET:
            landing.append(one)
    if inputs is None:
        if landing:
            raise ContractRefusal(
                "policy", "denied",
                f"the adapter for attempt {name_value(attempt_id)} mounts "
                f"{name_value(oci.INPUT_TARGET)} and no input root was "
                f"authorized; a worker reads its assignment from that path")
        return
    proved = oci.canonical_source(inputs, "an authorized input root")
    if len(landing) != 1 \
            or oci.canonical_source(landing[0]["source"],
                                    "a declared mount source") != proved \
            or landing[0]["writable"] is not False:
        raise ContractRefusal(
            "policy", "denied",
            f"the adapter for attempt {name_value(attempt_id)} does not mount "
            f"the authorized input root {name_value(proved)} read-only at "
            f"{name_value(oci.INPUT_TARGET)}; the root that was proved is the "
            f"root that is mounted")


def authorize_input_root(store, *, attempt_id, inputs):
    """Prove the composed `/input/` root belongs to THIS attempt, before the
    runtime that will mount it is started.

    W19784 review [P0], 2026-08-27. `workspaces.compose_input_root` writes the
    root and now holds the pair to a manager-owned assignment and attempt --
    but nothing in the LAUNCH path proved that the root a runtime is about to
    mount is the one that was composed for it. A root composed correctly for
    attempt 1 and then started under attempt 2's labels would have been caught
    only at the freeze, after the agent had run.

    This reads the two documents back OFF DISK rather than trusting a value
    passed down from the composition, because what the runtime mounts is the
    disk. Three manager-owned facts decide it, and each is a different way to
    be wrong:

      the ASSIGNMENT this attempt activated -- all four parts, never a subset;
      the RUNTIME ATTEMPT, so one attempt's root cannot be started under
      another's labels; and
      the INPUT DIGEST the attempt was recorded with, which is the manager's
      own record of what this attempt was offered and claimed against.

    A root this manager cannot read is a refusal rather than a start: the
    alternative is exposing a directory whose contents nothing has established.
    """
    attempt = _require_attempt(store, attempt_id)
    expected = _fixed_assignment(attempt)
    if expected is None:
        raise ContractRefusal(
            "refused", "precondition",
            f"attempt {name_value(attempt_id)} is not activated; there is no "
            f"live assignment to hold an input root against")
    given, delivered = workspaces.read_input_root(inputs)
    if delivered["assignment_ref"] != expected:
        raise ContractRefusal(
            "stale-assignment", "generation",
            f"the input root at {name_value(inputs)} names "
            f"{name_value(delivered['assignment_ref'])} and attempt "
            f"{name_value(attempt_id)} activated {name_value(expected)}")
    if delivered["runtime_attempt_id"] != attempt["runtime_attempt_id"]:
        raise ContractRefusal(
            "runtime-observation", "identity-mismatch",
            f"the input root at {name_value(inputs)} was composed for runtime "
            f"attempt {name_value(delivered['runtime_attempt_id'])} and this "
            f"start is {name_value(attempt['runtime_attempt_id'])}")
    # THE ATTEMPT'S OWN RECORD OF WHAT IT WAS CLAIMED AGAINST. Nullable on the
    # row, and an attempt that records none cannot have this proved -- which is
    # refused here rather than skipped, because "no recorded input" and "the
    # recorded input agrees" are not the same answer.
    if attempt["input_digest"] is None:
        raise ContractRefusal(
            "refused", "precondition",
            f"attempt {name_value(attempt_id)} records no input digest; a "
            f"root this manager cannot tie to what the attempt was claimed "
            f"against is one it will not expose")
    if given["manifest_digest"] != attempt["input_digest"]:
        raise ContractRefusal(
            "integrity", "digest",
            f"the input root at {name_value(inputs)} carries an input "
            f"manifest this attempt was not claimed against")
    return given, delivered


def request_runtime_start(store, adapter, *, attempt_id, inputs=None):
    """Commit a signed start operation, THEN call the adapter with it.

    Review [P1] in the frozen host: an axis label is not an effectively-once
    act. A journalled operation is what a restart replays and what the adapter
    can be asked about; a state column records only that somebody once intended
    to start. The adapter receives the operation identity so both sides settle
    the same act rather than two acts that happen to be adjacent.
    """
    boundaries.capability(getattr(adapter, "start", None),
                          "the runtime adapter's start")
    attempt = _require_attempt(store, attempt_id)
    if attempt["assignment_generation"] is None:
        raise ContractRefusal(
            "refused", "precondition",
            f"attempt {name_value(attempt_id)} is not activated; the "
            f"assignment manifest is fixed before the first writable adapter "
            f"call")
    if attempt["execution_runtime"] != "not-started":
        raise ContractRefusal(
            "refused", "already-terminal",
            f"attempt {name_value(attempt_id)} execution is "
            f"{name_value(attempt['execution_runtime'])}")
    # AND THE ADAPTER'S OWN PLAN AGREES, BEFORE ANYTHING IS JOURNALLED.
    #
    # W19784 second review [P0]. Carrying the authenticated source across the
    # seam makes the adapter refuse a plan that does not name it -- but that
    # refusal arrives INSIDE the adapter, after this manager has already
    # committed a start operation it now has to settle. An adapter that
    # declares its mount plan is one this manager can hold to the root it just
    # proved, and refusing here means no operation was journalled and there is
    # nothing to reconcile.
    #
    # BOTH, rather than either. This check cannot be the only one: an adapter
    # reached by any other path, or one whose plan is not declarable, still has
    # to fail closed on its own. And the adapter's check cannot be the only one
    # either, for the journalling reason above. They answer at two different
    # moments and neither subsumes the other.
    _plan_agrees(adapter, attempt_id, inputs)

    # THE ROOT IS AUTHORIZED BEFORE THE OPERATION IS JOURNALLED.
    #
    # W19784 review [P0]: nothing in the launch path proved that the root a
    # runtime is about to mount is the one composed for this attempt.
    #
    # THE REQUIREMENT IS DERIVED, NOT OPTIONAL, and the distinction is the
    # whole design. `inputs=None` is not "skip the check": it is only
    # reachable when the attempt records NO input digest, which means this
    # manager has nothing an input root could be bound to and therefore no
    # root to expose. Every real delivery is offered and claimed against an
    # input manifest, so every real delivery records that digest -- and from
    # that moment a start without an authorized root is refused.
    #
    # An optional operand would have been the hole: a caller that could pass
    # nothing would start a runtime over a directory nothing established. A
    # derived one cannot be omitted by the callers that matter.
    if attempt["input_digest"] is not None or inputs is not None:
        if inputs is None:
            raise ContractRefusal(
                "refused", "precondition",
                f"attempt {name_value(attempt_id)} was claimed against an "
                f"input manifest and no input root was named; a runtime is "
                f"not started over a directory this manager has not held "
                f"against its own assignment")
        authorize_input_root(store, attempt_id=attempt_id, inputs=inputs)
    labels = _runtime_labels(attempt)
    operation_id = _start_operation_id(attempt)
    signature = manager_signature("runtime.start",
                                  {"attempt_id": attempt_id, "labels": labels,
                                   "operation_id": operation_id})

    def act(connection):
        observe(store, attempt_id=attempt_id, axis="execution_runtime",
                value="start-requested")
        return documents.runtime_start_requested(attempt_id=attempt_id,
                                                 operation_id=operation_id)

    store.transact(operation_id, "runtime.start", signature, act)
    # AND ONLY THEN THE ADAPTER. A crash between the two boundaries is
    # answerable because the journal row exists; a crash before it leaves
    # nothing to answer for.
    # THE AUTHENTICATED SOURCE CROSSES THE SEAM. W19784 second review [P0]:
    # this manager proved one directory and then called an adapter whose mount
    # plan is independent of it, so the authorization and the mount were two
    # operations. The adapter requires this exact source, read-only, at the
    # worker's fixed `/input` -- and refuses a `/input` bind at all when there
    # is none to require.
    started = _started(adapter.start({"labels": labels,
                                      "operation_id": operation_id,
                                      "input_root": inputs}))
    return reconcile_runtime(store, adapter, attempt_id=attempt_id,
                             minted=started["runtime_id"],
                             minted_labels=started["labels"])


def _started(answer):
    """What the adapter said it started, owned as far as this manager reads it.

    Absence is an answer here: an adapter that returns nothing has not told us
    it started anything, and that is different from telling us it started
    something unnamed. Both members are read -- the id to compare against the
    listing, the labels to catch a runtime this call mislabelled -- so both are
    owned when they are present.
    """
    if answer is None:
        return {"runtime_id": None, "labels": None}
    taken = boundaries.document(answer, "the adapter's start answer",
                                required=(), optional=("runtime_id", "labels"))
    runtime_id = taken.get("runtime_id")
    labels = taken.get("labels")
    if runtime_id is not None:
        boundaries.identity(runtime_id, "a started runtime id")
    if labels is not None:
        boundaries.document(labels, "a started runtime's labels",
                            required=documents.RUNTIME_LABELS)
    return {"runtime_id": runtime_id, "labels": labels}


def reconcile_runtime(store, adapter, *, attempt_id, minted=None,
                      minted_labels=None):
    """Decide what exists, by IDENTITY and by the FULL labels.

    ZERO WAITS. "The adapter reports nothing" and "nothing exists" are different
    facts, and starting a second runtime for one assignment is the failure this
    whole ordering exists to prevent.

    POSITIVE ABSENCE NEEDS CERTIFIED ADAPTER EVIDENCE, which is a later item's
    to define -- so until then THE RETRY PATH IS CLOSED and says so. A proof a
    caller can write is not a proof, which is why this takes no `absence_proven`
    operand.

    MISMATCH OR MULTIPLICITY CANCELS, including a runtime THIS CALL started
    whose labels are wrong: that is not an absence, it is a mismatch this call
    caused.
    """
    boundaries.capability(getattr(adapter, "list", None),
                          "the runtime adapter's list")
    # THE CALLER'S ACCOUNT OF WHAT IT STARTED is a receiver input like any
    # other. It is COMPARED against what the adapter lists, and a comparison
    # against a value nobody owns decides nothing.
    if minted is not None:
        boundaries.identity(minted, "a minted runtime id")
    if minted_labels is not None:
        boundaries.document(minted_labels, "a minted runtime's labels",
                            required=documents.RUNTIME_LABELS)
    attempt = _require_attempt(store, attempt_id)
    labels = _runtime_labels(attempt)
    listed = _listed(adapter.list({"labels": labels}))
    # THE MINTED RUNTIME IS CHECKED BEFORE THE FILTER. A runtime this call
    # started carrying labels for a different assignment was filtered out and
    # reported as uncertainty -- but it is not absent, it is WRONG, and dropping
    # it would leave a mislabelled runtime running with the manager waiting for
    # news.
    if minted is not None:
        own = [runtime for runtime in listed
               if runtime["runtime_id"] == minted]
        own_labels = minted_labels if minted_labels is not None else (
            own[0]["labels"] if own else None)
        if own_labels is not None and own_labels != labels:
            return _cancel(store, attempt_id,
                           f"the runtime this call started "
                           f"({name_value(minted)}) carries labels for a "
                           f"different assignment")
    found = [runtime for runtime in listed if runtime["labels"] == labels]
    if len(found) > 1:
        return _cancel(store, attempt_id,
                       f"{len(found)} runtimes carry this assignment's labels; "
                       f"starting another would compound it",
                       runtimes=[runtime["runtime_id"] for runtime in found])
    if len(found) == 1:
        runtime = found[0]
        if minted is not None and runtime["runtime_id"] != minted:
            return _cancel(store, attempt_id,
                           f"this call started {name_value(minted)} and the "
                           f"adapter holds "
                           f"{name_value(runtime['runtime_id'])} for these "
                           f"labels")
        return _attach(store, attempt, runtime["runtime_id"])
    if minted is not None:
        # This call started something the adapter now cannot see. That is not
        # absence either -- it is a runtime whose fate is unknown.
        observe(store, attempt_id=attempt_id, axis="execution_runtime",
                value="uncertain")
        return documents.runtime_uncertain(
            attempt_id=attempt_id, decision="uncertain",
            why=f"this call started {name_value(minted)} and the adapter does "
                f"not list it; a second start could leave two runtimes")
    observe(store, attempt_id=attempt_id, axis="execution_runtime",
            value="uncertain")
    return documents.runtime_uncertain(
        attempt_id=attempt_id, decision="uncertain",
        why="the adapter reports no runtime, and positive absence needs "
            "certified adapter evidence this slice does not yet have; a second "
            "start would risk two runtimes for one assignment")


def _listed(answer):
    """What the adapter says exists, each entry owned before it is compared."""
    if answer is None:
        return []
    if type(answer) is not list:
        raise ContractRefusal(
            "integrity", "schema",
            f"the adapter's listing is a list of runtimes; this is "
            f"{name_value(answer)}")
    found = []
    for runtime in answer:
        taken = boundaries.document(runtime, "a listed runtime",
                                    required=("runtime_id", "labels"))
        boundaries.identity(taken["runtime_id"], "a listed runtime's id")
        boundaries.document(taken["labels"], "a listed runtime's labels",
                            required=documents.RUNTIME_LABELS)
        found.append(taken)
    return found


# THE STATES IN WHICH A STOP IS ALREADY IN FLIGHT.
#
# `stopping` is deliberately not re-announced: moving the axis backwards to
# repeat an intent the runtime is already carrying out changes nothing about
# where the runtime is. `destroyed` is not here either -- it is terminal, and an
# adapter still listing runtimes for a destroyed attempt is a contradiction
# rather than a cancellation this manager can carry out.
CANCELLATION_IN_FLIGHT = ("cancel-requested", "stopping")


def _cancel(store, attempt_id, why, runtimes=None):
    attempt = _require_attempt(store, attempt_id)
    if attempt["execution_runtime"] not in CANCELLATION_IN_FLIGHT:
        observe(store, attempt_id=attempt_id, axis="execution_runtime",
                value="cancel-requested")
    if runtimes is None:
        return documents.runtime_cancel(attempt_id=attempt_id,
                                        decision="cancel", why=why)
    return documents.runtime_cancel(attempt_id=attempt_id, decision="cancel",
                                    why=why, runtimes=runtimes)


def _attach(store, attempt, runtime_id):
    """The FIRST positive attachment fixes the runtime identity.

    Review [P1] in the frozen host: this overwrote `runtime_id`
    unconditionally, so a later inspection silently replaced the fixed runtime.
    The compare-and-swap admits null or the identical id; a different one is a
    mismatch, and a mismatch CANCELS rather than rewriting what is recorded.
    """
    attempt_id = attempt["runtime_attempt_id"]
    # NO EARLY MISMATCH CHECK. I wrote one -- read the row, compare, cancel --
    # and a mutation deleting it measured zero: the compare-and-swap below
    # refuses exactly the same case and the lost path answers with the same
    # cancellation, from a FRESHER read. A duplicate of the write's own
    # condition is the sixth such this campaign has made me remove, and this one
    # was also the staler of the two.
    #
    # ONE OPERATION PER RUNTIME, not one per attempt. Review [P1]: keyed on the
    # attempt alone, a stale manager that lost the race reached the journal
    # under the SAME operation id with a DIFFERENT signature -- so it surfaced
    # an operation collision instead of the pinned mismatch cancellation.
    # Attaching runtime A and attaching runtime B are two acts.
    def act(connection):
        changed = connection.execute(
            "UPDATE attempts SET runtime_id = ? WHERE runtime_attempt_id = ? "
            "AND (runtime_id IS NULL OR runtime_id = ?)",
            (runtime_id, attempt_id, runtime_id)).rowcount
        if changed != 1:
            raise ContractRefusal(
                "refused", "precondition",
                f"attempt {name_value(attempt_id)} is attached to another "
                f"runtime")
        # THE OBSERVATION IS PART OF THE ATTACHMENT, not a step after it.
        #
        # Review [P1]: the axis move ran AFTER the transaction committed, so a
        # fault between them left a committed attachment whose exact retry
        # REPLAYED the recorded answer without running the action -- answering
        # `attached` forever while the durable axis still said
        # `start-requested`. Effectively-once means the retry reproduces the
        # first act's whole effect, and an effect outside the transaction is
        # not part of the act.
        #
        # The observation's savepoint exists for exactly this nested use: it is
        # the same all-or-nothing boundary at either depth, where a second
        # BEGIN would refuse.
        observe(store, attempt_id=attempt_id, axis="execution_runtime",
                value="running")
        return documents.runtime_attached(attempt_id=attempt_id,
                                          decision="attached",
                                          runtime_id=runtime_id)

    try:
        answer = store.transact(f"attempt.attach:{attempt_id}:{runtime_id}",
                                "attempt.attach",
                                manager_signature("attempt.attach",
                                                  {"attempt_id": attempt_id,
                                                   "runtime_id": runtime_id}),
                                act)
    except ContractRefusal as refusal:
        # ONLY THE COMPARE-AND-SWAP'S OWN REFUSAL IS A LOST RACE. A broad catch
        # here swallowed an operation COLLISION and answered it as a
        # cancellation -- so the identity keying below could have been wrong and
        # nothing would have said so. §4.2's collision is the caller's to see.
        if refusal.code != "precondition":
            raise
        # LOST. The fixed identity is re-read and PRESERVED -- whoever attached
        # first decided it -- and the runtime this call saw becomes a mismatch
        # to cancel rather than a second write.
        now = _require_attempt(store, attempt_id)
        if now["runtime_id"] == runtime_id:
            return documents.runtime_attached(attempt_id=attempt_id,
                                              decision="attached",
                                              runtime_id=runtime_id)
        return _cancel(store, attempt_id,
                       f"attempt {name_value(attempt_id)} is attached to "
                       f"{name_value(now['runtime_id'])} and this inspection "
                       f"found {name_value(runtime_id)}")
    return answer


# -- step 3: cancellation, in the ONE order that is safe ----------------------


def _cancel_operation_id(attempt):
    """The ONE fixed cancellation operation for an attempt's exact generation.

    Derived from the attempt and its assignment, so a manager that restarts
    mid-cancellation names the act it already performed instead of starting a
    second one.
    """
    return "attempt.cancel:" + digest({
        "attempt_id": attempt["runtime_attempt_id"],
        "assignment": _fixed_assignment(attempt),
    })[len("sha256:"):]


def _authority_cancel_operation_id(attempt):
    """The AUTHORITY's identity for the same cancellation.

    Derived from the same operands and DELIBERATELY DIFFERENT from the
    manager's. §4.2: success at one boundary does not imply success at the
    other, and reconciliation queries both exact records -- one shared string
    would invite reading either journal's row as evidence of the other's.
    """
    return "authority." + _cancel_operation_id(attempt)


def request_cancellation(store, port, agent, adapter, *, attempt_id,
                         reason=None):
    """Fence at the authority FIRST, and only afterwards order the quiescence.

    Until the generation is fenced the assignment is still live, so a runtime
    stopped first would be a worker torn out from under an assignment the
    authority still believes is executing. FENCE, THEN STOP.

    The manager's own intent is journalled BEFORE the authority is asked, for
    the same reason runtime start journals before the adapter call: a crash
    between the two boundaries must be answerable, and a state column records
    only that somebody once intended to cancel.

    WHAT THIS DOES NOT DO: it does not satisfy the quiescence gate the authority
    installs. That gate takes positive absence naming the exact runtime, which
    is the same certified-adapter evidence the retry path is closed for.
    Agent-side quiescence is not that evidence and never becomes it.
    """
    # THE PARAMETER ORDER IS THE ACT ORDER: fence, then the agent, then the
    # runtime. Two adjacent injected objects are easy to swap, so the shapes are
    # checked -- a swap refuses here instead of quietly cancelling the wrong
    # boundary first.
    boundaries.capability(getattr(agent, "cancel", None), "the agent's cancel")
    boundaries.capability(getattr(adapter, "stop", None),
                          "the runtime adapter's stop")
    attempt = _require_attempt(store, attempt_id)
    expected = _fixed_assignment(attempt)
    if expected is None:
        raise ContractRefusal(
            "refused", "precondition",
            f"attempt {name_value(attempt_id)} has no fixed assignment; "
            f"cancellation fences an exact generation and there is none to "
            f"fence")
    # The session is the BINDING. A session for somebody else could otherwise
    # end this participant's assignment through this manager, which is the
    # authorization the activation slice already refuses.
    if expected["participant"] != port.participant:
        raise ContractRefusal(
            "refused", "capability",
            f"this session acts for {name_value(port.participant)} and attempt "
            f"{name_value(attempt_id)} is assigned to "
            f"{name_value(expected['participant'])}")
    _optional(reason, "a cancellation reason")
    # NO LIVENESS PRE-CHECK. Whether this assignment is still the live one is
    # the AUTHORITY's decision, made inside its own transaction against its own
    # state; asking first and acting on the answer would be a read-then-write
    # race wearing a guard's clothes.
    manager_operation_id = _cancel_operation_id(attempt)
    authority_operation_id = _authority_cancel_operation_id(attempt)
    signature = manager_signature(
        "attempt.cancel", {"attempt_id": attempt_id, "expect": expected,
                           "authority_operation_id": authority_operation_id,
                           "reason": reason})
    intent = store.transact(
        manager_operation_id, "attempt.cancel", signature,
        lambda connection: documents.cancel_intent(
            attempt_id=attempt_id, assignment=expected,
            authority_operation_id=authority_operation_id, reason=reason))
    fenced = port.cancel(expected, authority_operation_id, reason,
                         expected["work_ref"]["work_id"],
                         expected["work_ref"]["authority_uuid"])
    # ONLY NOW. Everything below this line runs after the generation is fenced
    # and the assignment is ended.
    # W6627: the SESSION's own announcement, on the axis, before the agent is
    # asked -- the same place the runtime axis's `cancel-requested` is recorded
    # and in the same order. Nothing below moves.
    session_quiescence = sessions._request_session_quiescence(
        store._connection, attempt_id)
    return documents.attempt_cancelled(
        intent=intent, fenced=fenced,
        session_quiescence=session_quiescence,
        quiescence=_order_quiescence(store, agent, adapter, attempt_id,
                                     expected, manager_operation_id))


def _order_quiescence(store, agent, adapter, attempt_id, assignment,
                      operation_id):
    """Order the AGENT cancelled and then the runtime stopped -- and never claim
    either of them happened.

    Review [P1] in the frozen host: it discarded the adapter's answer and
    reported `stopped: true` whenever the call RETURNED. Reaching a boundary is
    not evidence of its effect, so the manager reports what it KNOWS -- that it
    ordered the acts -- and passes each settlement through uninterpreted.
    Positive quiescence arrives as an OBSERVATION or not at all.

    The axis is announced only where the transition map declares
    `cancel-requested` from where the runtime actually is. The stop ORDER is
    still re-issued in flight, under the same operation identity: an order that
    may have been lost must be repeatable, and the identity is what keeps the
    repeat one act rather than two.
    """
    attempt = _require_attempt(store, attempt_id)
    current = attempt["execution_runtime"]
    if "cancel-requested" in TRANSITIONS["execution_runtime"][current]:
        observe(store, attempt_id=attempt_id, axis="execution_runtime",
                value="cancel-requested")
    if attempt["runtime_id"] is None:
        return documents.quiescence_not_ordered(
            ordered=False,
            why=f"no runtime is attached to attempt {name_value(attempt_id)}, "
                f"so there is no agent inside one and nothing to stop")
    if current == "destroyed":
        return documents.quiescence_not_ordered(
            ordered=False,
            why=f"attempt {name_value(attempt_id)} observed "
                f"{name_value(attempt['runtime_id'])} destroyed; there is "
                f"nothing left to cancel or stop")
    # THE AGENT FIRST, then the runtime. An agent told to stop after its runtime
    # is already going away never hears the order, and the whole point of asking
    # it is the cooperative shutdown a kill does not give. Both receive the
    # MANAGER's operation identity, so each side settles the same act.
    #
    # A FAILED COOPERATIVE REQUEST DOES NOT VETO THE STOP. Review [P1]: a
    # throwing agent left the function before the stop was reached, and the
    # authority had ALREADY fenced and ended the assignment -- so an unreachable
    # provider left a fenced runtime running indefinitely. Persistent agent
    # unreachability is a REASON to stop the runtime, not a reason to leave it
    # alone.
    #
    # PRESENCE IS ITS OWN FACT: a sentinel list rather than `None`, because
    # `None` is a value a boundary can legitimately raise and a value that also
    # means absence cannot carry presence.
    agent_failure = []
    agent_settlement = None
    try:
        agent_settlement = agent.cancel({
            "attempt_id": attempt_id, "assignment": assignment,
            "runtime_id": attempt["runtime_id"], "operation_id": operation_id})
    except BaseException as failure:
        agent_failure.append(failure)
    try:
        runtime_settlement = adapter.stop({
            "runtime_id": attempt["runtime_id"], "operation_id": operation_id})
    except BaseException as failure:
        # Both boundaries failed. Neither is allowed to hide the other, and
        # choosing between them would be this boundary deciding which failure
        # the caller is entitled to see.
        if agent_failure:
            raise ExceptionGroup(
                f"neither the agent nor the runtime accepted cancellation for "
                f"attempt {attempt_id}",
                [agent_failure[0], failure]) from None
        raise
    if agent_failure:
        raise agent_failure[0]
    # ORDERED, not done. Each settlement is passed through as the boundary gave
    # it, un-summarized: the manager has no basis for turning either into a fact
    # about the world, and normalizing "returned nothing" into "returned null"
    # is a smaller version of the same mistake.
    return documents.quiescence_ordered(
        ordered=True, runtime_id=attempt["runtime_id"],
        agent_settlement=agent_settlement,
        runtime_settlement=runtime_settlement)
