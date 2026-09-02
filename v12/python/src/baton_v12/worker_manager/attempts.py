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
from . import (boundaries, documents, lanes, oci, schema, sessions,
               workspaces)
from .store import manager_signature

# `_fixed_assignment` is PRIVATE until something outside this module needs it.
# It projects an attempt row this build has already adopted, and an exported
# projector over an unowned dict would be a boundary nobody owns.
# The three DERIVED identities are private for the same reason
# `_fixed_assignment` is: each projects an attempt row this build has already
# adopted, and an exported projector over an unowned dict is a boundary nobody
# owns. They become public when something outside this module needs to name the
# act -- which is what a restart will need, and is the next slice's to arrange.
__all__ = ["TRANSITIONS", "AXES", "CONTEXT_COLUMNS",
           "start_failure_operation_id", "record_attempt",
           "observe", "activate_assignment", "label_context",
           "attempt_activity_of", "observe_activity",
           "request_runtime_start",
           "reconcile_runtime", "request_cancellation",
           "finalize_quiescent_assignment"]


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
        # W26294 ADDS `quiescent` TO BOTH, and it is a discovery rather than
        # a new act. Reconciliation now ASKS the engine about the exact
        # runtime instead of reading `running` off a listing, so a container
        # that finished between the start and the reconciliation is something
        # this manager can now see -- and since W26291 delivered the launch
        # document that is the ORDINARY case, because the reference worker
        # starts, finds no frames on a closed stdin and exits cleanly.
        #
        # Without it the axis would refuse the truthful answer and the manager
        # would have to record `running` for a container it had just been told
        # is not, which is the defect this Work exists to remove.
        "not-started": ["start-requested", "running", "quiescent",
                        "cancel-requested", "uncertain", "destroyed"],
        "start-requested": ["running", "quiescent", "cancel-requested",
                            "uncertain", "destroyed"],
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

# W16823: THE AUTHORIZATION CONTEXT, as this table stores it and as the claimed
# offer row spells it. Two names for one fact is how the two drift, so the pair
# is written down once and both sides are read through it.
CONTEXT_COLUMNS = tuple((mine, theirs)
                        for theirs, mine, _ in schema.CLAIM_CONTEXT)


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


def attempt_runtime_of(store, attempt_id):
    """W55758: the durable runtime facts a RECOVERY may branch on.

    A READ AND NOTHING ELSE, and it exists because a public recovery command
    has to choose between two endings that are not interchangeable. An attempt
    whose runtime ATTACHED is ended by `abandon_attempt`, which refuses one
    that never did; an attempt interrupted after credential materialization
    and before attachment has no attempt ending to reach at all, and inventing
    a terminal one for it would be a second ending beside the ruled one.

    WITHOUT THIS the deployment could only learn which it was by CALLING the
    abandonment and reading the sentence in its refusal. A branch that turns
    on the wording of a message is a branch that changes when the message is
    improved, and this question is the manager's own durable state rather than
    an accident of prose.

    ABSENCE IS AN ANSWER. A well-formed id naming no attempt answers `None`,
    exactly as `_attempt_row` does, and a malformed one is a refusal.
    """
    found = _attempt_row(store, attempt_id)
    if found is None:
        return None
    return {"attempt_id": found["runtime_attempt_id"],
            "runtime_id": found["runtime_id"],
            "execution_runtime": found["execution_runtime"],
            "cleanup": found["cleanup"],
            # W55758, approver ruling APPROVE-EXTEND (M60437): THE FIXED
            # ASSIGNMENT TRAVELS WITH THE RUNTIME AXES, in ONE atomic read.
            #
            # A public recovery command is editable-grants-driven, and nothing
            # was holding those grants against what the manager fixed: a
            # grants file naming another generation ended the attempt anyway
            # and then wrote its own generation into the recovery record as
            # though it were the identity the ending used. The hold needs the
            # complete four-part identity, and it needs it from the SAME read
            # the branch turns on -- two reads are two moments, and a caller
            # comparing one against the other would be comparing an attempt
            # with itself at two times.
            #
            # `None` when activation never fixed one, which is its own
            # refusal at the caller: an attempt with no fixed assignment is
            # not one a grants file can be held against.
            "assignment": _fixed_assignment(found)}


def attempt_activity_of(store, attempt_id):
    """W61599: the DEFAULT LIVENESS PROJECTION, and nothing about content.

    Two numbers answer the question an operator actually asks of a running
    worker -- "is this thing moving?" -- without opening its container, naming
    a provider-private path or reading one byte the child produced: how much
    of its native session stream this manager has OBSERVED, and when the
    manager last received some of it.

    APPROVER RULING M61707 BOUNDS WHAT THIS IS. It is an observation and not
    proof of useful progress: repeated noise grows the count, a long quiet
    model call leaves it unchanged, and a provider may expose no measurable
    stream at all. It never renews a claim, clears a gate, extends a deadline
    or authorizes recovery, so nothing in this manager branches on it.

    ABSENCE IS TWO DIFFERENT ANSWERS, and they are not interchangeable. A
    well-formed id naming no attempt is `None` -- there is nothing to be live.
    A recorded attempt nobody has observed yet answers a projection whose
    members are `None`: it exists and has shown nothing, which is exactly what
    an operator watching a start needs to be told rather than a zero that
    would read as "observed, and empty".
    """
    found = _attempt_row(store, attempt_id)
    if found is None:
        return None
    return {"attempt_id": found["runtime_attempt_id"],
            "bytes_observed": found["activity_bytes"],
            "observed_at": found["activity_at"]}


def observe_activity(store, *, attempt_id, bytes_observed):
    """One liveness observation: MONOTONIC, manager-stamped, content-free.

    The operand is a CUMULATIVE TOTAL rather than a delta, and that is what
    makes a lost, duplicated or reordered report harmless: two observers
    reporting the same stream cannot double-count it, and a report that
    arrives late is simply behind. A delta would make this counter the sum of
    everything that happened to reach it.

    MONOTONIC IS DECIDED INSIDE THE WRITE, against the exact value the update
    compares, for the reason `observe` decides its transition there: a
    host-language check around an unconditional write is two moments, and the
    second one overwrites whatever landed in between.

    A REPEAT OF THE SAME TOTAL IS NOT ACTIVITY. It is accepted -- an observer
    that polls a quiet stream is behaving correctly -- and it deliberately
    does NOT move the instant, because the instant is the age of the latest
    OBSERVED ACTIVITY and advancing it would make a wedged worker look freshly
    alive. That is the exact misreading this projection exists to prevent, so
    the no-op is the whole point rather than an optimization.

    A DECREASE REFUSES. A total that went backwards is not this stream, and
    quietly accepting it would let a stale or confused observer make a
    progressing worker look stalled.

    THE INSTANT IS THE MANAGER'S. `store._now()` is the same clock the journal
    stamps rows from; a provider timestamp would be the observed child's own
    account of its liveness, which is the thing being questioned.
    """
    _require_attempt(store, attempt_id)
    if type(bytes_observed) is not int or bytes_observed < 0:
        raise ContractRefusal(
            "integrity", "schema",
            f"an observed activity total is a whole number of bytes this "
            f"manager has seen, which cannot be negative; this is "
            f"{name_value(bytes_observed)}")
    # A SAVEPOINT for the same reason `observe` takes one: the conditional
    # write and the read that explains its outcome are one answer at one
    # moment, and a caller must never be told "you went backwards" about a
    # value some other writer moved between the two statements.
    mark = f"activity_{abs(hash(attempt_id)) % 10 ** 12}"
    connection = store._connection
    connection.execute(f"SAVEPOINT {mark}")
    try:
        connection.execute(
            "UPDATE attempts SET activity_bytes = ?, activity_at = ? "
            "WHERE runtime_attempt_id = ? "
            "AND (activity_bytes IS NULL OR activity_bytes < ?)",
            (bytes_observed, store._now(), attempt_id, bytes_observed))
        held = _require_attempt(store, attempt_id)["activity_bytes"]
        if held is not None and held > bytes_observed:
            raise ContractRefusal(
                "runtime-observation", "state-regression",
                f"this manager has already observed {held} byte(s) of "
                f"{name_value(attempt_id)}'s session stream and this reports "
                f"{bytes_observed}; an observed total never goes backwards")
    except BaseException:
        try:
            connection.execute(f"ROLLBACK TO {mark}")
        except Exception:
            pass
        try:
            connection.execute(f"RELEASE {mark}")
        except Exception:
            pass
        raise
    connection.execute(f"RELEASE {mark}")
    return attempt_activity_of(store, attempt_id)


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
    # W16823: THE CONTEXT COMES FROM THE CLAIMED OFFER, AND FROM NOWHERE ELSE.
    #
    # There is no operand for it on this function and there is deliberately not
    # going to be one. `expect` is the four-part fence and stays exactly that;
    # the principal, scope, role, grant and policy generation are what the
    # AUTHORITY answered when this offer's claim committed, read back off the
    # row this manager wrote from that answer. A caller -- or a worker reaching
    # a caller -- has no way to choose or widen any of them, because the
    # nearest thing to a hole is the offer row, and the port is the only writer
    # of these columns.
    context = {stored: claim[held] for stored, held in CONTEXT_COLUMNS}
    if any(value is None for value in context.values()):
        raise ContractRefusal(
            "integrity", "schema",
            f"attempt {name_value(attempt_id)} was claimed by an offer that "
            f"retains no authorization context; the claim's principal and "
            f"effective scope are what this activation fixes beside the fence, "
            f"and an attempt that cannot say which principal it runs for is "
            f"the conflation this manager was corrected for")
    signature = manager_signature("assignment.activate",
                                  {"attempt_id": attempt_id,
                                   "expect": expected,
                                   # AND THE CONTEXT, because it changes the
                                   # AUTHORIZATION MEANING of the act.
                                   # Without it, activating the same attempt
                                   # against the same fence under a different
                                   # principal would REPLAY the first
                                   # activation -- one act, two authorizations,
                                   # and the row keeping whichever arrived
                                   # first.
                                   "context": context})
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
            "assignment_generation = ?, assignment_participant = ?, "
            # THE SAME UPDATE, because the table's CHECK is all-ten-or-none:
            # a fence fixed without its context could not be written at all.
            # Composed from `CONTEXT_COLUMNS`, which is `schema.CLAIM_CONTEXT`
            # read from this table's side -- so the offer's columns and this
            # table's cannot drift into two lists that agree until they do not.
            + ", ".join(f"{column} = ?" for column, _ in CONTEXT_COLUMNS)
            + " WHERE runtime_attempt_id = ? "
              "AND assignment_generation IS NULL",
            (expected["work_ref"]["work_id"],
             expected["work_ref"]["authority_uuid"], expected["generation"],
             expected["participant"])
            + tuple(context[column] for column, _ in CONTEXT_COLUMNS)
            + (attempt_id,)).rowcount
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

    AND THE PRINCIPAL AND EFFECTIVE SCOPE THE CLAIM WAS AUTHORIZED FOR.
    W16793's finding: the participant is an operational ENDPOINT and this
    manager was treating it as every identity below the authority, so two
    endpoint addresses the authority maps to one principal produced two
    unrelated label sets -- and anything reading runtimes back saw two
    independent identities where the authority holds one. The principal is
    here because nothing else in the label set can express that, and the
    endpoint stays because the fence is what it is for.

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
        # W16823: BESIDE the fence, never instead of it. These come off the
        # same activation that fixed the four parts, so a runtime cannot carry
        # a principal from one claim and a generation from another.
        principal=attempt["assignment_principal"],
        effective_scope=attempt["assignment_scope"],
        profile_digest=attempt["profile_digest"],
        policy_digest=attempt["policy_digest"],
        adapter_digest=attempt["adapter_digest"])


def label_context(store, attempt_id):
    """The two label members an adapter cannot derive from the fence.

    W16823. PUBLIC because the isolation boundary is where it is needed: an
    adapter selects an attempt's runtimes by their whole label set, the set now
    names the principal and the effective scope, and an adapter holds no
    control store to read them from -- by design, because a runtime adapter
    that could read this manager's rows would be exactly the capability the
    topology exists to withhold.

    READ FROM THE ACTIVATED ROW and refused when the attempt is not activated.
    Composing a selector out of nulls would list every runtime that also has
    none, which is the failure a manager cannot see: an empty answer reads as
    "nothing is running".
    """
    attempt = _require_attempt(store, attempt_id)
    if attempt["assignment_principal"] is None:
        raise ContractRefusal(
            "refused", "precondition",
            f"attempt {name_value(attempt_id)} is not activated, so it has no "
            f"principal or effective scope; a runtime selector composed out of "
            f"absent labels selects whatever else is missing them")
    return {"principal": attempt["assignment_principal"],
            "effective_scope": attempt["assignment_scope"]}


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


def start_failure_operation_id(attempt):
    """The ONE identity a failed start is journalled under.

    PUBLIC because W32648's cleanup crossing is authorized by that record and
    has to name the identity it was written under. Recomputing the derivation
    at the reader would be two spellings of one identity, and the first time
    they disagreed only one would be the row that exists.

    STABLE FOR THE ONE START ACT -- the attempt, its fixed assignment and the
    start operation this followed, and nothing that can change.

    RE-REVIEW [P0]: the first cut hashed the attached runtime and the typed
    failure into the id as well, and that inverted the guarantee it claimed.
    `store.transact` can compare a changed signature only after the caller
    selects the SAME id, so folding the changeable facts into the id meant a
    different runtime or a different failure chose a different row and never
    reached the collision guard at all.  Worse, the case I wrote asserted the
    two rows -- durable evidence of the opposite contract.

    The changeable facts live in the SIGNATURE instead, where a difference is
    what the journal is built to refuse.  So an exact repetition replays, and
    any changed fact arrives at this same id with another signature and fails
    closed with the first record intact.
    """
    return "runtime.start-failed:" + digest({
        "attempt_id": attempt["runtime_attempt_id"],
        "assignment": _fixed_assignment(attempt),
        "start_operation_id": _start_operation_id(attempt),
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
    # W32649: AND NO PREDECESSOR HOLDS THIS WORK'S LANE.
    #
    # ASKED HERE, BEFORE ANYTHING DURABLE HAPPENS. Authorizing an input root is
    # a journalled act, and a successor that cannot start must not perform one
    # -- "refuse a successor before reaching the engine" is the boundary, and
    # the honest reading of it is before writing anything at all.
    #
    # THIS READ IS NOT THE DECISION, which is why it is not the only check. It
    # proves only its own instant; a predecessor could settle, or another
    # successor could take the lane, between here and the transaction. The
    # authoritative answer is the `INSERT` inside `act` below, where the lane's
    # primary key decides the race with no window. This one exists so the
    # ordinary case refuses early and cheaply, and the two disagreeing is not
    # possible in a direction that matters: the transaction can only be
    # stricter.
    reference = lanes.lane_reference(attempt)
    lanes._no_predecessor_holds(store._connection, reference, attempt_id)
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
        # W32649: THE LANE IS TAKEN IN THE SAME WRITE THAT MAKES THE START
        # ELIGIBLE, and before the adapter is called at all.
        #
        # "Before the first writable runtime start, atomically with the manager
        # fact that makes the start eligible" is the boundary, and this
        # transaction IS that fact: it is what a restart reads to decide a
        # start was requested. Taking the lane anywhere else would leave a
        # window in which the journal says a start is under way and the lane
        # says nobody is executing, and a successor arriving in that window is
        # the overlap the lane exists to prevent.
        #
        # THE PREDECESSOR CHECK RIDES WITH IT, inside `occupy_lane`, so a
        # successor is refused HERE -- before the engine, before any delivery
        # -- rather than after something has been created.
        lanes._occupy_lane(connection, store._now(), attempt_id=attempt_id,
                          reference=reference,
                          reason=f"execution requested under "
                                 f"{operation_id}")
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
    # W26291: NO LAUNCH OPERAND HERE, and the absence is the design.
    #
    # W6636's composition found the adapter delivered nothing the reference
    # worker needed, so an adapter-started worker could not run at all. The
    # first correction added an `environment` operand to THIS function and
    # carried four `BATON_WORKER_*` values through it; the dossier superseded
    # that before acceptance, and the replacement is not the same value in a
    # different wrapper.
    #
    # The launch document is a materialized, §13-walked, frozen file and the
    # thing that travels is the CAPABILITY to mount it. That is not data, so it
    # does not belong in a start request -- `boundaries.document` takes exact
    # built-in documents and refuses anything carrying behaviour, and reducing
    # a delivery to something that fits would make it a path, which is the
    # caller-selected locator the fixed target exists to remove. It is held on
    # the adapter at construction, exactly as the credential delivery is and
    # for the same reason: an attempt-scoped, manager-owned, non-assignment
    # mount whose two acts are exposing it at a fixed path and tearing it down.
    try:
        started = _started(adapter.start({"labels": labels,
                                          "operation_id": operation_id,
                                          "input_root": inputs}))
    except ContractRefusal as refusal:
        raise _start_failed(store, adapter, attempt_id, refusal) from None
    except Exception as fault:                             # noqa: BLE001
        # RE-REVIEW [P0]: A FAULT IS A FAILED START TOO, and it takes THE SAME
        # SETTLEMENT BOUNDARY as a refusal.
        #
        # The first correction called `_settle_unknown_start` directly here,
        # which never asks the adapter anything -- so a driver that created a
        # runtime and then raised left that runtime unnamed and outside the
        # ordinary destroy crossing, even though `list` and `observe` would
        # have found and identified it immediately. A fault says LESS about
        # the start result than a typed refusal; it does not make exact
        # reconciliation less necessary, it makes it more.
        #
        # THE FAULT ITSELF IS RE-RAISED UNCHANGED. This manager has no account
        # of what it was, and wrapping it would replace the thing that went
        # wrong with this manager's guess about it.
        # RECORDED THROUGH THE SAME BOUNDARY, with the fault preserved as a
        # fault rather than dressed as a refusal it never was.
        _settled_and_recorded(store, adapter, attempt_id,
                              _fault_failure(fault))
        raise
    return reconcile_runtime(store, adapter, attempt_id=attempt_id,
                             minted=started["runtime_id"],
                             minted_labels=started["labels"])


def _refusal_failure(refusal):
    """A refused start, as the record's typed failure."""
    return {"kind": "refusal", "category": refusal.category,
            "code": refusal.code, "message": refusal.message}


def _fault_failure(fault):
    """A FAULTED start, as the record's typed failure.

    NO REFUSAL PAIR IS MANUFACTURED FOR IT.  The closed pairing has no
    `refused/start-failed`, and this module's own history says why: a wrapper
    that retyped every failed start as one was measured against the boundary
    inventory and broke three probes, because a malformed start ANSWER is
    `integrity/schema` and relabelling it made the manager's account disagree
    with the boundary that found it.  A fault has no pair at all, so the record
    says which KIND of failure it holds and preserves the exception's own class
    and text -- which is what "preserve the original typed adapter/transport
    fault" asks for, rather than a category this manager chose for it.
    """
    return {"kind": "fault", "fault": type(fault).__name__,
            "message": str(fault)}


def _record_and_raise_start_failure(store, attempt_id, failure):
    """The recording itself, with its refusals RAISED.

    Named apart from the reporting wrapper below so a case can drive the rule
    and see what it answers.  Production never calls this directly: a recorder
    that raised into a failure already on its way out would substitute its own
    problem for the one that actually happened.
    """
    attempt = _require_attempt(store, attempt_id)
    record = {"attempt_id": attempt_id, "expect": _fixed_assignment(attempt),
              "start_operation_id": _start_operation_id(attempt),
              "runtime_id": attempt["runtime_id"],
              "execution_runtime": attempt["execution_runtime"],
              "failure": failure}
    operation_id = start_failure_operation_id(attempt)
    signature = manager_signature("runtime.start-failed", record)
    store.transact(operation_id, "runtime.start-failed", signature,
                   lambda connection: documents.runtime_start_failed(**record))
    return operation_id


def _record_start_failure(store, attempt_id, failure):
    """The durable manager-owned record of a failed start.

    W32648, approver ruling M33800.  The start operation ALREADY COMMITTED --
    `request_runtime_start` journals its intent and only then calls the adapter
    -- so the failure cannot be carried as that operation's refusal.  It is its
    own journalled act, which is what makes it durable, replayable and
    collidable.

    THE JOURNAL IS THE RECORD, and no new table is.  `store.transact` stores
    the sealed document as the operation's result, so an operator reads the
    typed fault back through `operation_result` and a restarted manager finds
    the same row.

    THE IDENTITY IS THE ONE START ACT -- the attempt, its fixed assignment and
    the start operation this followed.  The runtime reconciliation attached,
    the settled axis and the typed failure ride the SIGNATURE, which is where
    a difference is refused.  Review [P0] corrected this: folding the
    changeable facts into the id meant a changed runtime or failure selected
    another row and never reached the collision guard at all.  An exact retry
    reproduces this result; any changed fact arrives at this same id with
    another signature and fails closed with the first record intact.

    NEVER RAISES.  It runs while another failure is on its way out, and a
    recorder that threw would replace the thing that went wrong with the
    attempt to write it down.
    """
    try:
        operation_id = _record_and_raise_start_failure(store, attempt_id,
                                                       failure)
    except ContractRefusal as collided:
        # A COLLISION IS AN ANSWER, not a failure to record.  This start act
        # already has a record and the facts arriving now differ from it, so
        # the journal refuses -- and the FIRST account, written when the
        # manager knew most, is the one that stands.
        return (f"; and this start act already holds a different failure "
                f"record, which stands: {collided.message}")
    except Exception as failed:                            # noqa: BLE001
        return (f"; and the start failure could not be recorded: "
                f"{type(failed).__name__}")
    return (f"; the start failure is journalled as "
            f"{name_value(operation_id)}")


def _settle_unknown_start(store, adapter, attempt_id):
    """Leave an ENDING when the exact state could not be established.

    RE-REVIEW [P0]: `_start_failed` caught a failed reconciliation only to
    extend the exception message, so an adapter whose listing was unavailable
    left the attempt at `start-requested` with no identity -- the exact
    stranded state this settlement was written to remove, reached through the
    one path where the manager knows least. An ending recorded only when the
    settlement itself goes well is not an invariant.

    `uncertain` IS THE HONEST ENDING and the axis reaches it from
    `start-requested`. Nothing was established, so nothing positive may be
    written: it is not `destroyed`, because destruction is a fact about the
    world, and it is not `not-started`, because the adapter was called.

    ONLY FROM `start-requested`. A reconciliation that recorded something
    truer before it failed is not overwritten -- this closes a hole, and
    replacing an observation with `uncertain` would open a different one.

    Answers a string so the caller can append what it did to the refusal an
    operator reads, and never raises: this runs while another failure is
    already being reported, and a settlement that threw would replace the
    thing that went wrong with the attempt to describe it.
    """
    try:
        row = _require_attempt(store, attempt_id)
        if row["execution_runtime"] != "start-requested":
            return ""
        observe(store, attempt_id=attempt_id, axis="execution_runtime",
                value="uncertain")
    except Exception as failure:                           # noqa: BLE001
        return (f"; and this attempt could not be settled either: "
                f"{type(failure).__name__}")
    return "; this attempt's execution runtime is recorded uncertain"


def _start_failed(store, adapter, attempt_id, refusal):
    """W6636 [P0]: a refused start is SETTLED before its refusal is raised.

    The operation is journalled above and `execution_runtime` says
    `start-requested`; then the adapter refuses and, until now, that refusal
    propagated untouched. The attempt was left claimed, activated, and stranded
    at `start-requested` with no runtime identity -- and `authorize_cleanup`
    refuses exactly that shape ("no runtime is attached; there is no identity
    to destroy and no absence to prove"), so nothing could clean it up either.
    A successful atomic claim could therefore end in an attempt no operation in
    this manager could move.

    WHAT THE ADAPTER ALREADY DID IS NOT WHAT THIS MANAGER KNOWS.
    `OciAdapter._refused_start` asks which runtimes carry these labels and
    settles both delivery roots on the answer -- but it says so in refusal
    PROSE, and prose is not a durable manager fact. So the manager asks the
    same question through the operation that owns the answer.

    RECONCILIATION IS THE OWNER, and it is called rather than reimplemented.
    W26294 settled what an exact observation means; if a runtime carries this
    attempt's labels it is attached here, which is what makes it nameable by
    the ordinary destroy crossing, and if the manager cannot establish what
    exists the axis records `uncertain`. Both preserve the invariant that
    matters most: NO REPLACEMENT IS STARTED on either path.

    THE ORIGINAL REFUSAL IS NOT LOST, AND NEITHER IS ITS CLOSED PAIR. The
    category and the code come through unchanged and only the message grows,
    because settling is not a different thing going wrong -- it is what this
    manager did about the thing that went wrong. A wrapper that retyped every
    refusal as `refused/start-failed` was measured against the boundary
    inventory and broke three probes: a malformed start ANSWER is
    `integrity/schema` at `_started`, and relabelling it would have made the
    manager's account of the failure disagree with the boundary that found it.

    THE DURABLE RECORD IS THE TYPED ENDING. What a caller acts on is the
    attempt row -- an attached identity the destroy crossing can name, or
    `uncertain` -- rather than a code carried on an exception, and that record
    survives the process this refusal is raised in.
    """
    return ContractRefusal(refusal.category, refusal.code,
                           refusal.message
                           + _settled_and_recorded(
                               store, adapter, attempt_id,
                               _refusal_failure(refusal)))


def _settle_failed_start(store, adapter, attempt_id):
    """RECONCILE FIRST, and fall back to `uncertain` only when that cannot
    answer. Shared by every failed start, however it failed.

    ONE BOUNDARY FOR BOTH KINDS OF FAILURE. A refusal and a fault differ in
    what they say about WHY the start did not complete and not at all in what
    the manager has to do about it: ask the adapter which runtime carries this
    attempt's labels, attach the one it finds -- which is what makes it
    nameable by the ordinary destroy crossing -- and record `uncertain` when
    nothing can be established. Splitting them was how the fault path lost the
    reconciliation.

    Answers a string the caller appends to whatever it is reporting, and never
    raises: this runs while another failure is already on its way out, and a
    settlement that threw would replace it.
    """
    try:
        settled = reconcile_runtime(store, adapter, attempt_id=attempt_id)
    except ContractRefusal as second:
        return (f"; and the exact runtime state could not be reconciled "
                f"afterwards: {second.message}"
                f"{_settle_unknown_start(store, adapter, attempt_id)}")
    except Exception as failure:                           # noqa: BLE001
        return (f"; and reconciling the exact runtime state afterwards "
                f"raised {type(failure).__name__}"
                f"{_settle_unknown_start(store, adapter, attempt_id)}")
    row = _require_attempt(store, attempt_id)
    return (f"; the start was settled as {name_value(settled['decision'])} "
            f"and this attempt's execution runtime is now "
            f"{name_value(row['execution_runtime'])}")


def _settled_and_recorded(store, adapter, attempt_id, failure):
    """Reconcile, then record -- in that order, and both for every failure.

    THE ORDER IS THE CONTENT.  The record names the runtime the reconciliation
    attached, so recording first would durably say `None` about a runtime that
    exists, and the ordinary destroy crossing would then have a record
    disagreeing with the attempt row it is meant to authorize.
    """
    return (_settle_failed_start(store, adapter, attempt_id)
            + _record_start_failure(store, attempt_id, failure))


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
    # W26294: BOTH CAPABILITIES AT THE PUBLIC BOUNDARY, beside each other and
    # before anything is asked of either -- the same shape
    # `request_runtime_start` uses for `start`. `list` answers WHICH
    # containers carry these labels and `observe` answers what one of them
    # IS; an adapter with one and not the other is a narrow adapter this seam
    # cannot use, and finding that out halfway through a reconciliation would
    # be finding it out after the listing already happened.
    boundaries.capability(getattr(adapter, "observe", None),
                          "the runtime adapter's observe")
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
        # W26294: THE EXACT RUNTIME IS OBSERVED BEFORE ANYTHING IS RECORDED.
        # Membership in `ps --all` proves this container carries this
        # assignment's labels and says nothing about whether it is alive.
        state, value, why = _observed(adapter, runtime["runtime_id"])
        return _settled(store, attempt, runtime["runtime_id"],
                        state, value, why)
    # W26294 review [P0]: AN EXACT IDENTITY IS STILL A QUESTION THIS SEAM CAN
    # ASK, and until now it did not.
    #
    # `_observed` ran only inside the one-candidate branch, so the ORDINARY
    # post-removal shape -- the container gone, `ps --all` therefore empty,
    # and the attempt still holding the exact immutable runtime id -- returned
    # `uncertain` without asking the adapter about the identity it already
    # had. Positive absence was unreachable in normal operation, which is the
    # opposite of what this Work's acceptance says it delivers.
    #
    # TWO SOURCES OF AN EXACT IDENTITY, and the durable one wins. A recorded
    # attachment is what this attempt IS bound to; `minted` is what this call
    # started and has not attached yet. Either is a runtime the adapter can be
    # asked about by name.
    known = attempt["runtime_id"] if attempt["runtime_id"] is not None \
        else minted
    if known is not None:
        state, value, why = _observed(adapter, known)
        if state == "uncertain":
            # ASKED AND STILL UNKNOWN. The identity is not erased -- an
            # attachment already made stands, and a lost `minted` stays the
            # caller's to reconcile again.
            observe(store, attempt_id=attempt_id, axis="execution_runtime",
                    value="uncertain")
            return documents.runtime_uncertain(
                attempt_id=attempt_id, decision="uncertain",
                why=f"the adapter lists no runtime for these labels and "
                    f"cannot say what {name_value(known)} is: {why}")
        # PROVED, BY NAME. `absent` here is the answer the acceptance asks for
        # and the listing alone can never give: this exact runtime is gone.
        # The attachment is what fixes WHICH runtime this attempt had, and it
        # is true whatever state that runtime is now in -- `observed` carries
        # the state, which is the whole of W26294's correction to this
        # document's meaning.
        return _settled(store, attempt, known, state, value, why)
    # NO EXACT IDENTITY AT ALL, which is the one reconciliation that still
    # cannot ask the question: nothing was started by this call and nothing is
    # recorded, so there is no runtime to name.
    observe(store, attempt_id=attempt_id, axis="execution_runtime",
            value="uncertain")
    return documents.runtime_uncertain(
        attempt_id=attempt_id, decision="uncertain",
        why="the adapter reports no runtime and this attempt names none; a "
            "second start would risk two runtimes for one assignment")


def _settled(store, attempt, runtime_id, state, value, why):
    """Attach the exact identity and RECORD the state just observed.

    ONE OWNER FOR BOTH WAYS AN EXACT RUNTIME IS FOUND. The listing names one
    candidate, or the listing is empty and the attempt names one; the identity
    arrives differently and everything after it is the same act. The re-review
    correction added the second caller, and writing this out twice would have
    been two copies of one rule -- which the mutation harness noticed as an
    anchor matching twice, before a reader would have.

    RECORDED ON EVERY PASS, outside the effectively-once attachment. See
    `_attach` for why this cannot live inside it.

    THE ANSWER CARRIES THE STATE JUST OBSERVED, not the one the attachment was
    first settled with. `_attach` is effectively-once, so a replay reproduces
    the FIRST document -- whose `observed` is as old as the attachment.
    Returning it unchanged would answer this reconciliation with a previous
    one's reading, which is a smaller version of the defect this Work removes.

    THE REASON RIDES ONLY WHEN THE OBSERVATION WAS INCONCLUSIVE. A conclusive
    one's prose is the adapter's ordinary description and adds nothing; an
    inconclusive one is the only case where the recorded state does not say
    what happened.

    RE-REVIEW [P1]: THE ANSWER IS REBUILT, NEVER MERGED. This returned
    `{**attached, "observed": value}`, which refreshes ONE member of a document
    the effectively-once attachment replayed from the first pass -- so `why`
    stayed whatever that first pass carried. Both directions were wrong and in
    opposite ways: a first `running` then a failed observation answered
    `observed=uncertain` with NO reason, and a first failed observation then a
    `running` one answered `observed=running` while still carrying the original
    failure's prose. A partial refresh is worse than none, because the members
    that moved and the members that did not are indistinguishable to a reader.

    So the outward document is COMPOSED from the two things that are true now:
    the STABLE attachment identity, which is what `_attach` exists to fix and
    is the one member a replay is authoritative about, and THIS pass's
    observation. Nothing is carried across from the replayed document.
    """
    attempt_id = attempt["runtime_attempt_id"]
    # ONE OWNER FOR "INCONCLUSIVE", read from the value that is actually
    # recorded and returned. `state` and `value` agree on it by construction
    # (`OBSERVED_RUNTIME` maps `uncertain` to itself and nothing else to it),
    # and deciding it from `observed` is what makes the document consistent
    # with ITSELF rather than with a variable a reader has to go and check.
    inconclusive = value == "uncertain"
    attached = _attach(store, attempt, runtime_id, value,
                       why if inconclusive else None)
    # A CANCELLATION IS A DIFFERENT DOCUMENT and passes straight through. It
    # answers a mismatch rather than an attachment, and there is no observation
    # of this attempt's runtime to state in it.
    if attached["decision"] != "attached":
        return attached
    observe(store, attempt_id=attempt_id, axis="execution_runtime",
            value=value)
    return documents.runtime_attached(
        **{"attempt_id": attempt_id, "decision": "attached",
           # FROM THE ATTACHMENT, not from this call's argument. They are equal
           # on every path that reaches here, and saying so from the attachment
           # is what makes "the identity is fixed by the first pass" a property
           # of the code rather than of the caller.
           "runtime_id": attached["runtime_id"], "observed": value},
        **({"why": why} if inconclusive else {}))


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


# W26294: what `adapter.observe` may answer about one exact runtime, and the
# axis value each answer means. Closed on purpose: an engine state this build
# does not recognise is not a state it will record, and `uncertain` is the
# honest reading of confusion rather than a default that happens to be safe.
#
# `absent` becomes `destroyed` because it is POSITIVE evidence about one exact
# identity -- the adapter answers it only when the engine says that container
# does not exist -- and the transition map's own note says a reconciliation
# must be able to record what it finds "including positive destruction".
# Inferring it from a failure to LOOK is the thing that stays forbidden, and
# that is `uncertain`, which the map still refuses to let become `destroyed`.
OBSERVED_RUNTIME = {"running": "running", "quiescent": "quiescent",
                    "absent": "destroyed", "uncertain": "uncertain"}


def _observed(adapter, runtime_id):
    """The exact runtime's state, asked of the ADAPTER rather than inferred.

    W6636's composition found reconciliation reading `running` off membership
    in `docker ps --all` -- a listing that includes exited containers -- so an
    execution attempt recorded a running worker for one that had already
    finished. `list` answers WHICH containers carry an assignment's labels;
    only `observe` answers what one of them IS.

    FAIL CLOSED ON EVERYTHING ELSE. A failed observation, an answer this build
    does not recognise, or an answer that is not a document are all reasons to
    say `uncertain` and none is a reason to say running: a manager that
    treated confusion as liveness would hold an assignment open for a worker
    that finished, and one that treated it as absence would release an
    assignment whose worker is still executing.
    """
    # EVERY FAILURE IS `uncertain`, and until the re-review this docstring
    # promised that while the code raised instead. A propagated exception left
    # the durable axis at whatever it said before -- including `running` -- so
    # an observation that FAILED was indistinguishable from one that answered
    # liveness. That is the same defect this Work exists to remove, one level
    # up: a state assumed rather than observed.
    #
    # THE ADAPTER'S OWN FAILURE IS ITS ANSWER. A refusal, a transport error, a
    # provider that raised -- none of them says what the runtime is, and all of
    # them are reasons to say so.
    try:
        answer = adapter.observe(runtime_id)
    except ContractRefusal as refusal:
        return "uncertain", "uncertain", _inconclusive(refusal.message)
    except Exception as failure:                           # noqa: BLE001
        return "uncertain", "uncertain", _inconclusive(
            f"{type(failure).__name__}")
    # OWNED MEMBER BY MEMBER, and only the two this manager reads.
    #
    # NOT `boundaries.document` over the whole answer, and the reason is a
    # boundary question rather than a convenience. That owner refuses any
    # member it was not told about, so it would have to be told about
    # `mounts` -- which this manager never consumes, and which the adapter
    # answers as its own structure. Owning a member in order to ignore it is
    # claiming a contract over something this seam has no opinion about, and
    # the POD walk then refuses the adapter's own shape for a reason that has
    # nothing to do with reconciliation.
    if type(answer) is not dict:
        return "uncertain", "uncertain", _inconclusive(
            f"a runtime observation is a document; this is "
            f"{name_value(answer)}")
    for member in ("state", "why"):
        if member not in answer:
            return "uncertain", "uncertain", _inconclusive(
                f"a runtime observation needs {name_value(member)}")
    try:
        why = boundaries.text(answer["why"], "a runtime observation's reason")
        state = boundaries.text(answer["state"],
                                "a runtime observation's state")
    except ContractRefusal as refusal:
        return "uncertain", "uncertain", _inconclusive(refusal.message)
    if state not in OBSERVED_RUNTIME:
        return "uncertain", "uncertain", _inconclusive(
            f"{name_value(state)} is not a runtime observation; the four this "
            f"build reads are {', '.join(sorted(OBSERVED_RUNTIME))}")
    return state, OBSERVED_RUNTIME[state], why


# How far an inconclusive observation's own words travel. The adapter's
# message is read to SAY WHY and then bounded: it can carry a URL, a daemon
# path or an engine's own diagnostic, and a reason is a short explanation
# rather than a log.
MAX_INCONCLUSIVE = 400


def _inconclusive(why):
    return f"the exact runtime could not be observed: {str(why)[:MAX_INCONCLUSIVE]}"


def _attach(store, attempt, runtime_id, value="running", why=None):
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
        # W26294: THE OBSERVED VALUE, not a constant. This recorded `running`
        # unconditionally, which is the whole defect: the identity was proved
        # by the listing and the STATE was assumed from it.
        observe(store, attempt_id=attempt_id, axis="execution_runtime",
                value=value)
        # `why` ONLY WHEN THERE IS SOMETHING TO EXPLAIN. A conclusive
        # observation's reason is the adapter's ordinary prose and adds
        # nothing; an INCONCLUSIVE one is the only case where the recorded
        # state does not say what happened.
        return documents.runtime_attached(
            **{"attempt_id": attempt_id, "decision": "attached",
               "runtime_id": runtime_id, "observed": value},
            **({"why": why} if why is not None else {}))

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
            # W26294 review [P2]: `observed` IS SUPPLIED HERE TOO. The
            # contract requires it and this branch omitted it, so a lost race
            # against a winner that attached the SAME runtime would have
            # assembled a document its own contract refuses. The value is this
            # call's own fresh reading, which is what the caller returns for
            # the ordinary path as well.
            return documents.runtime_attached(
                **{"attempt_id": attempt_id, "decision": "attached",
                   "runtime_id": runtime_id, "observed": value},
                **({"why": why} if why is not None else {}))
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


# -- step 4: finalizing an assignment that is ALREADY QUIESCENT ---------------
#
# W61984. THE INTERVAL NOTHING OWNED. A worker answers one of the four terminal
# dispositions, the exact execution runtime is positively observed `quiescent`,
# and the assignment is still LIVE at the authority -- so it holds the
# participant's global claim slot, and `intake.authorize_cleanup` correctly
# refuses to end a runtime whose assignment the authority still believes is
# executing. W52821 run5b sat in exactly that state.
#
# WHY `request_cancellation` IS NOT THAT OPERATION, and why it is unchanged.
# Its order -- fence, ask the agent, stop the runtime -- is right for a
# cancellation that INITIATES quiescence, and `test_attempts` pins it. Reused
# after the worker conversation has ended it would add two fallible external
# acts restating a fact this manager already holds durably, and either of them
# can fault AFTER the authority has fenced.
#
# WHAT THIS DOES, AND EXACTLY THIS. It journals one operator decision, derives
# the fixed assignment, the runtime identity and the recorded disposition from
# this manager's own row, and calls the SAME exact authority fence. It makes no
# agent call and no runtime call -- it takes neither capability, so it cannot
# -- and it decides nothing about output, intake, retention, verification,
# review, approval, integration or cleanup. Freeing the claim slot is not
# accepting the proposal, and the Work stays behind
# `runtime-quiescence:<generation>` until POSITIVE absence, which quiescence
# never is.

# How far an operator's own sentence travels onto a durable surface. Prose in a
# journalled signature is durable, and an unbounded operand is an unbounded
# durable write.
MAX_FINALIZATION_REASON = 2000


def _finalize_operation_id(attempt):
    """The ONE finalization identity for an attempt's exact generation.

    Derived from the attempt and its assignment -- and deliberately not from
    the reason, the runtime or the disposition. Those ride the SIGNATURE, so a
    second decision naming a different reason COLLIDES against this identity
    instead of committing a second finalization of one attempt.
    """
    return "attempt.finalize-quiescent:" + digest({
        "attempt_id": attempt["runtime_attempt_id"],
        "assignment": _fixed_assignment(attempt),
    })[len("sha256:"):]


def _authority_finalize_operation_id(attempt):
    """The AUTHORITY's own effectively-once identity for this fence.

    DISTINCT FROM ALL THREE of the decision above, `attempt.cancel:*` and
    `authority.abandon-fence:*`. §4.2: success at one boundary does not imply
    success at the other, and a finalization must not be able to replay a
    cancellation's or an abandonment's authority act -- four identities because
    they are four acts.
    """
    return "authority.finalize-quiescent:" + digest({
        "attempt_id": attempt["runtime_attempt_id"],
        "assignment": _fixed_assignment(attempt),
    })[len("sha256:"):]


def finalize_quiescent_assignment(store, port, *, attempt_id, reason):
    """End the exact live assignment of an already-quiescent attempt.

    CALLING THIS IS THE OPERATOR'S DECISION. There is no deadline, no timer and
    no clock: a terminal worker disposition is not by itself a decision to end
    the assignment, and the specification keeps an `unable` result waiting for
    an explicit pass, release or close. Nothing in this manager calls this on a
    worker's behalf.

    EVERY OPERAND BUT THE ATTEMPT AND THE REASON IS DERIVED. The four-part
    assignment, the exact runtime identity and the recorded terminal
    disposition come off this manager's own row, so a caller cannot name an
    assignment, a generation or a runtime the manager did not fix.

    THE ORDER, and each step is the next one's precondition:

      1. own the two operands and the participant binding, and refuse an
         attempt with no fixed assignment or no attached runtime -- before any
         durable write and long before the authority is asked;
      2. commit or replay the decision, with the two MUTABLE facts -- a
         terminal disposition and a positively quiescent exact runtime --
         decided INSIDE that write, because "check then commit" is two acts;
      3. read the committed record back as the authorization and fence the
         exact generation with ITS values, so a resumed call reissues the same
         authority act rather than a freshly recomposed one.

    AND NOTHING FOLLOWS. `request_cancellation` continues past its fence to the
    agent and the runtime; this returns. The retained output stays frozen and
    in custody, pending an explicit retention decision, and the runtime stays
    where it is for the existing exact cleanup to prove absent.
    """
    boundaries.identity(attempt_id, "a runtime attempt id")
    reason = boundaries.text(reason, "a finalization reason")
    # A BLANK SENTENCE IS A DECISION NOBODY MADE, on the rule `abandon_attempt`
    # states: calling this operation IS the operator's declaration, so the
    # account of it is not optional the way a cancellation's is.
    if not reason.strip():
        raise ContractRefusal(
            "integrity", "schema",
            "a finalization carries the operator's own reason; calling this "
            "operation IS the decision, so a blank one is a decision nobody "
            "made")
    if len(reason) > MAX_FINALIZATION_REASON:
        raise ContractRefusal(
            "integrity", "limit",
            f"a finalization reason is at most {MAX_FINALIZATION_REASON} "
            f"characters and this one is {len(reason)}; the sentence is "
            f"journalled, and an unbounded operand is an unbounded durable "
            f"write")
    attempt = _require_attempt(store, attempt_id)
    expected = _fixed_assignment(attempt)
    if expected is None:
        raise ContractRefusal(
            "refused", "precondition",
            f"attempt {name_value(attempt_id)} has no fixed assignment; "
            f"finalization ends an exact generation and there is none to end")
    # The session is the BINDING, exactly as it is for a cancellation. A
    # session for somebody else could otherwise end this participant's
    # assignment through this manager.
    if expected["participant"] != port.participant:
        raise ContractRefusal(
            "refused", "capability",
            f"this session acts for {name_value(port.participant)} and "
            f"attempt {name_value(attempt_id)} is assigned to "
            f"{name_value(expected['participant'])}")
    # THE RECORD NAMES THE RUNTIME WHOSE QUIESCENCE WAS ACTED ON, so an attempt
    # that never attached one has nothing for it to name. Such an attempt is
    # also one no runtime ever executed for, which is a different situation and
    # not this operation's.
    if attempt["runtime_id"] is None:
        raise ContractRefusal(
            "refused", "precondition",
            f"attempt {name_value(attempt_id)} has no attached runtime; this "
            f"operation finalizes an assignment whose exact runtime was "
            f"observed quiescent, and there is none to name")
    authority_operation_id = _authority_finalize_operation_id(attempt)
    record = _finalization_record(store, attempt, attempt_id, expected, reason,
                                  authority_operation_id)
    # FENCED WITH THE ADOPTED RECORD'S OWN VALUES, on the rule the abandonment
    # follows: a resumed call must reissue the SAME authority operation with
    # the SAME reason, and reading them off the committed decision is what
    # makes that true across a restart.
    #
    # NO LIVENESS PRE-CHECK. Whether this assignment is still the live one is
    # the AUTHORITY's decision, made inside its own transaction against its own
    # state; asking first and acting on the answer would be a read-then-write
    # race wearing a guard's clothes.
    fenced = port.cancel(dict(expected),
                         record["authority_operation_id"], record["reason"],
                         expected["work_ref"]["work_id"],
                         expected["work_ref"]["authority_uuid"])
    return documents.attempt_finalized(intent=dict(record),
                                       fenced=dict(fenced))


def _finalization_record(store, attempt, attempt_id, expect, reason,
                         authority_operation_id):
    """Commit or replay the decision, then adopt it as the authorization.

    COMMITTED BEFORE THE AUTHORITY IS ASKED, which is what makes the fence
    resumable: a crash between the two boundaries leaves a record that already
    names the one authority act to reissue, rather than an intent somebody
    remembers having formed.
    """
    operation_id = _finalize_operation_id(attempt)
    signature = manager_signature(
        "attempt.finalize-quiescent",
        {"attempt_id": attempt_id, "expect": expect,
         "runtime_id": attempt["runtime_id"],
         "worker_disposition": attempt["worker_disposition"],
         "authority_operation_id": authority_operation_id,
         "reason": reason})
    document = documents.finalize_intent(
        attempt_id=attempt_id, assignment=dict(expect),
        runtime_id=attempt["runtime_id"], decision="finalized",
        worker_disposition=attempt["worker_disposition"],
        authority_operation_id=authority_operation_id, reason=reason)
    # ONE CALL, NOT A PEEK AND A CALL. `transact` replays inside its own lock
    # and does not run the action when it does, so the fresh eligibility below
    # is decided exactly once -- on the call that actually commits -- and a
    # resumed call is not re-judged against axes that moved because this
    # decision already ran.
    committed = store.transact(
        operation_id, "attempt.finalize-quiescent", signature,
        lambda connection: _quiescent(store, attempt_id, document))
    held = adopt_finalization_record(committed)
    # EVERY MEMBER, not the ones that name the world. The RECORD is the
    # authorization, so a record written about another attempt, another
    # generation, another runtime, another disposition, another authority act
    # or another sentence does not authorize this fence.
    for member, mine in (("attempt_id", attempt_id),
                         ("assignment", expect),
                         ("runtime_id", attempt["runtime_id"]),
                         ("decision", "finalized"),
                         ("worker_disposition", attempt["worker_disposition"]),
                         ("authority_operation_id", authority_operation_id),
                         ("reason", reason)):
        if held[member] != mine:
            raise ContractRefusal(
                "integrity", "schema",
                f"the recorded finalization names {member} "
                f"{name_value(held[member])} and this ending is for "
                f"{name_value(mine)}; the record and the act it authorizes "
                f"must describe one attempt, one runtime and one decision")
    return held


def adopt_finalization_record(record):
    """THE ONE PLACE a committed finalization decision crosses back IN.

    PLAN 4bz names the store a RECEIVING trust domain, and this is the entry.
    On the call that commits, `transact` hands back this build's own document;
    on a replay after a retry, a crash or a restart it hands back whatever
    bytes SQLite kept under that operation identity. The caller cannot tell the
    two apart, so BOTH are proved here -- once, as the value enters -- against
    the closed `attempt.finalize-intent` contract. Nothing revalidates it
    afterwards: the member comparison above is a rule over an already-owned
    document rather than a second crossing.

    NAMED AND PUBLIC BECAUSE IT IS A CROSSING. A private helper's operands are
    internal values of whatever called it; this one's operand is the durable
    store's answer, and hiding a receiving entry behind a naming convention is
    how one ends up with no owner and no probe.

    Handed back as this call's own mapping, so the authorization the fence is
    issued from is a value this operation holds rather than an alias of what
    the journal returned.
    """
    held = boundaries.document(record, "a committed finalization record",
                               required=documents.FINALIZE_INTENT)
    return dict(held)


def _quiescent(store, attempt_id, document):
    """The two MUTABLE facts, read inside the write that records the decision.

    INSIDE THE TRANSACTION, because "check then commit" is two acts and an
    axis can move between them. Both refusals are ordinary and undurable, so
    the whole transaction goes back: nothing is journalled, the authority is
    never asked, and no output, custody, retention or cleanup axis is touched.
    """
    attempt = _require_attempt(store, attempt_id)
    # EVERY RECORDED TERMINAL ANSWER, and `none` is the only one refused.
    # Approver ruling 2026-09-01 item 3: a `completed` worker whose independent
    # verification failed reaches the same lifecycle state as an `unable` one,
    # and finalization is about the ASSIGNMENT rather than about which terminal
    # answer the worker gave. A worker that has not answered at all has an
    # ending of its own and is not this operation's.
    if attempt["worker_disposition"] not in schema.DISPOSITIONS:
        raise ContractRefusal(
            "refused", "precondition",
            f"attempt {name_value(attempt_id)} worker disposition is "
            f"{name_value(attempt['worker_disposition'])}; finalization ends "
            f"the assignment of a worker that has ALREADY answered, and this "
            f"one has not")
    # `quiescent` AND NOTHING ELSE. `running` and `start-requested` say a
    # worker may still be executing; `uncertain` says this manager could not
    # see; `destroyed` and `stopping` are other endings' business. Only a
    # positive observation of the exact runtime says the thing this operation
    # is named for, and it is deliberately not upgraded to absence -- a
    # quiescent runtime still exists and satisfies no authority gate.
    if attempt["execution_runtime"] != "quiescent":
        raise ContractRefusal(
            "refused", "precondition",
            f"attempt {name_value(attempt_id)} execution runtime is "
            f"{name_value(attempt['execution_runtime'])}; this operation "
            f"finalizes an ALREADY-QUIESCENT assignment and makes no runtime "
            f"call, so only a positively quiescent exact runtime reaches it")
    # AND IT IS STILL THE CONTAINER THE DECISION NAMES.
    if attempt["runtime_id"] != document["runtime_id"]:
        raise ContractRefusal(
            "integrity", "schema",
            f"this finalization names runtime_id "
            f"{name_value(document['runtime_id'])} and attempt "
            f"{name_value(attempt_id)} is now attached to "
            f"{name_value(attempt['runtime_id'])}; the record and the state "
            f"it was decided on must describe one runtime")
    return document
