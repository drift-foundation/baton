"""The composed ending's own obligation, journalled where the Job lives.

W119733, `work/records/2026/09/finding-v12-composed-ending-recovery/`.

WHAT WAS MISSING, AND IT IS NOT A STEP OF THE ENDING. Every act a composed
ending performs is already owned and already replays: the freeze, the terminal
correlation, the intake, the retention decision, the publication, the
checkpoint, the runtime cleanup, and W119548's gate discharge. What nothing
owned is the OBLIGATION to finish that sequence. `projection._ending_owed`
decides whether to ask again from the Worker Manager's cleanup axis, and that
axis becomes terminal the moment `authorize_cleanup` commits -- which is the
SECOND-TO-LAST thing a composed ending does rather than the last. A process
death between the cleanup and the acts after it therefore left a stage
projected `completed`, a Work blocked at a gate nobody was going to discharge,
and no tick that would ever ask again.

SO THE OBLIGATION IS RECORDED BEFORE IT CAN BE LOST, and it is recorded HERE
because the Job manager is what schedules the ask. The Worker Manager owns
whether a runtime is gone; this leaf owns whether a composed stage is finished,
and those are different facts held by different stores. An intent is committed
before the first step of the ending can reach cleanup, and a correlated
settlement is committed only after the ending's evidence, the required gate
discharge and the applicable routing have all succeeded.

WHAT THESE TWO RECORDS ARE NOT. They certify nothing. An intent does not say a
runtime is absent, a settlement does not authorize a discharge, and neither
promotes a worker's claim to proof: the terminal identity kept below is a
SELECTOR the frozen-result owner still checks. What they carry is exactly the
selectors needed to re-enter the same ending on a later incarnation, without a
process cache and without a live exchange to read.

A SIGNATURE IS NOT OWNERSHIP, and W120424 exists because these readers acted
as though it were. Review 2026-09-08T15-46-16Z [P1]: `intent_of` and
`settlement_of` proved that a record was well made -- its member set, its kind,
its committed state, and that its stored signature was the one this build
derives from the bytes it holds -- and every one of those is equally true of a
LEGITIMATE record belonging to another stage. A genuine review settlement,
copied through the public journal to the implementation stage's selected
identity, was therefore read as that stage's own: pending discovery emptied,
the implementation projected `completed`, and its dependent opened. So every
read now also proves WHOSE the record is -- that its own stage and episode
derive the identity it was selected by, that its selectors still bind to this
store's rows, that its assignment is this store's Authority and its stage's
Work, and that a settlement is paired with the obligation it claims to end.

NO SCHEMA CHANGE AND NO SECOND JOURNAL. Both records are ordinary operations in
the Job store's existing journal, taken through `transact` under deterministic
identities derived from the stage and its episode, so a second registration
replays rather than repeats and a different document under the same identity
refuses. The episode is IN the identity for `manager.receipt_operation_id`'s
reason: a correction round opens a fresh episode, and an obligation keyed by
the stage alone would let the new round replay the old round's record.
"""

from ..contracts import ContractRefusal
from ..contracts.errors import name_value
from ..worker_manager import boundaries
from . import episodes, schema, submission
from .store import job_signature

__all__ = ["ASSIGNMENT_MEMBERS", "EVIDENCE_MEMBERS", "EVIDENCE_OPTIONAL",
           "INTENT_KIND", "INTENT_MEMBERS", "SELECTORS", "SETTLED_KIND",
           "SETTLEMENT_MEMBERS", "WORK_REF_MEMBERS", "attempt_of",
           "ending_of", "intent_of", "intent_operation_id", "pending_endings",
           "register_ending", "settle_ending", "settlement_of",
           "settlement_operation_id"]

INTENT_KIND = "ending.intent"
SETTLED_KIND = "ending.settled"

# THE IMMUTABLE SELECTORS BOTH RECORDS CARRY. Every one of them is an identity
# this store already holds in a row, and they are written into the journal so a
# later incarnation can rebuild the same attempt from the record alone. They
# are also what makes a foreign record refusable: each is compared back against
# the stage and episode rows before anything is done with it.
SELECTORS = ("stage_id", "job_id", "kind", "episode", "offer_id",
             "attempt_id", "work_id")

# The four-part fixed assignment, spelled exactly as the Worker Manager's own
# `documents.assignment` spells it. A second spelling of one identity is how
# two components come to disagree about which generation they mean.
WORK_REF_MEMBERS = ("authority_uuid", "work_id")
ASSIGNMENT_MEMBERS = ("work_ref", "participant", "generation")

INTENT_MEMBERS = SELECTORS + ("assignment", "disposition",
                              "terminal_manifest_digest",
                              "retention_disposition",
                              "retention_policy_digest")

SETTLEMENT_MEMBERS = SELECTORS + ("assignment", "intent", "evidence")

# WHAT A SETTLEMENT RECORDS ABOUT THE ACTS THAT FINISHED THE ENDING, and it is
# a set of REFERENCES rather than a second account of them. Each owner already
# holds its own journalled record; what this adds is the correlation, so an
# operator reading the Job store can find them. The three required members are
# the ones every composed ending produces; the optional ones differ by stage
# kind, and a member absent from an implementation ending is not a review
# ending's missing evidence.
EVIDENCE_MEMBERS = ("result_id", "manifest_digest", "receipt_digest")
EVIDENCE_OPTIONAL = ("checkpoint_id", "gate_discharge", "outcome", "routed",
                     "verdict_id")


def _refuse(message, *, category="integrity", code="schema"):
    raise ContractRefusal(category, code, message)


def _operation_id(kind, stage_id, episode):
    """ONE derivation, used to store a record and to prove a stored one.

    Review [P1] is why it is one function rather than two spellings: the check
    that a document belongs at the identity it was selected by is only a check
    if it derives that identity exactly as the write did.
    """
    return f"{kind}:{stage_id}:{episode}"


def intent_operation_id(stage_id, episode):
    """The one identity a stage episode's ending obligation is journalled by."""
    return _operation_id(INTENT_KIND, stage_id, episode)


def settlement_operation_id(stage_id, episode):
    """And the one its settlement is journalled by."""
    return _operation_id(SETTLED_KIND, stage_id, episode)


def _selectors(held, what):
    """The seven selectors, owned before anything is derived from them."""
    if type(held) is not dict:
        _refuse(f"{what} is one exact document; this is {name_value(held)}")
    missing = [member for member in SELECTORS if member not in held]
    if missing:
        _refuse(f"{what} needs {', '.join(missing)}; a composed ending is "
                f"re-entered from these selectors and nothing else")
    taken = {member: held[member] for member in SELECTORS}
    boundaries.identity(taken["stage_id"], f"{what}'s stage id")
    boundaries.identity(taken["job_id"], f"{what}'s Job id")
    boundaries.text(taken["kind"], f"{what}'s stage kind")
    boundaries.text(taken["work_id"], f"{what}'s Work id")
    boundaries.identity(taken["offer_id"], f"{what}'s offer id")
    boundaries.identity(taken["attempt_id"], f"{what}'s runtime attempt id")
    if type(taken["episode"]) is not int or taken["episode"] < 1:
        _refuse(f"{what}'s episode is a whole number from 1; this is "
                f"{name_value(taken['episode'])}")
    return taken


def _stage_row(store, stage_id, rows=None):
    """The stage row THIS STORE holds, read rather than accepted.

    REVIEW 2026-09-08T16-00-28Z [P2]: this used to return a `stage` operand
    unchanged when one was supplied, so a caller handing over a dictionary
    that agreed with a stored record's wrong Work made the public reader
    answer it -- the bypass being that a document matching a document is not a
    proof that this store owns either. `rows` is not that operand: it is
    nothing a caller can supply, only the one read `pending_endings` performs
    for a pass that asks about many stages, and every row in it came out of
    this store inside that call.
    """
    if rows is not None:
        found = rows.get(stage_id)
        if found is not None:
            return found
    else:
        for row in submission.stage_rows(store):
            if row["stage_id"] == stage_id:
                return row
    _refuse(f"this Job store carries no stage {name_value(stage_id)}; a "
            f"composed ending belongs to a stage this scheduler holds",
            category="refused", code="precondition")


def _bound(store, taken, rows=None):
    """The selectors, PROVED against the rows this store actually holds.

    A RECORD IS NOT ITS OWN AUTHORITY. The journal is durable text this process
    did not write, so a record naming an episode whose offer or attempt has a
    different identity is a stranger's obligation or a hand edit -- and acting
    on one would drive an ending for an attempt this stage never made. Both
    rows are read and every selector is compared before the record is used for
    anything.
    """
    stage = _stage_row(store, taken["stage_id"], rows)
    if stage["job_id"] != taken["job_id"] or stage["kind"] != taken["kind"] \
            or stage["work_id"] != taken["work_id"]:
        _refuse(f"stage {name_value(taken['stage_id'])} is "
                f"{name_value(stage['kind'])} of Job "
                f"{name_value(stage['job_id'])} at Work "
                f"{name_value(stage['work_id'])}, and this composed ending "
                f"names {name_value(taken['kind'])} of "
                f"{name_value(taken['job_id'])} at "
                f"{name_value(taken['work_id'])}",
                category="refused", code="operation-collision")
    episode = episodes.episode_of(store, taken["stage_id"], taken["episode"])
    if episode is None:
        _refuse(f"stage {name_value(taken['stage_id'])} has no episode "
                f"{taken['episode']}; a composed ending is owed by an episode "
                f"this store opened", category="refused", code="precondition")
    if episode["offer_id"] != taken["offer_id"] \
            or episode["attempt_id"] != taken["attempt_id"]:
        _refuse(f"stage {name_value(taken['stage_id'])} episode "
                f"{taken['episode']} was attempted as "
                f"{name_value(episode['attempt_id'])} under offer "
                f"{name_value(episode['offer_id'])}, and this composed ending "
                f"names {name_value(taken['attempt_id'])} under "
                f"{name_value(taken['offer_id'])}", category="refused", code="operation-collision")
    return stage, episode


def _shaped_assignment(value, what):
    """The exact four-part assignment, as a DOCUMENT and nothing more.

    Split from the ownership comparison below because the two answer different
    questions and are needed in different places: the shape is part of the
    payload contract both a write and a read hold a record to, and whose
    Authority it names can only be asked where the store is.
    """
    held = boundaries.document(value, what, required=ASSIGNMENT_MEMBERS)
    ref = boundaries.document(held["work_ref"], f"{what}'s Work reference",
                              required=WORK_REF_MEMBERS)
    schema.check_authority(ref["authority_uuid"], what=f"{what}'s Authority")
    boundaries.text(ref["work_id"], f"{what}'s Work id")
    boundaries.text(held["participant"], f"{what}'s participant")
    boundaries.generation(held["generation"], f"{what}'s generation")
    return {"work_ref": {"authority_uuid": ref["authority_uuid"],
                         "work_id": ref["work_id"]},
            "participant": held["participant"],
            "generation": held["generation"]}


def _intent_document(value, what):
    """The WHOLE registered obligation, owned the same way on both sides.

    REVIEW 2026-09-08T16-00-28Z [P1]: the reader proved the outer member set,
    the signature, the selectors and the assignment and then returned -- so a
    correctly signed record sitting at its own identity carried a null
    terminal digest, a list where a disposition belongs and a dictionary where
    a policy digest belongs, straight past the closed contract this module
    says it holds. Validating on the way IN does not discharge that: the
    process that wrote a durable value is not the process that reads it, which
    is the whole reason this package owns its own store's rows.

    SO THERE IS ONE VALIDATOR AND BOTH SIDES USE IT, rather than two that
    agree today. A contract enforced in one direction is a contract for as
    long as nothing else ever writes the table.
    """
    taken = boundaries.document(value, what, required=INTENT_MEMBERS)
    held = _selectors(taken, what)
    boundaries.text(taken["disposition"], f"{what}'s worker disposition")
    boundaries.identity(taken["terminal_manifest_digest"],
                        f"{what}'s worker completion manifest digest")
    boundaries.text(taken["retention_disposition"],
                    f"{what}'s retention disposition")
    boundaries.text(taken["retention_policy_digest"],
                    f"{what}'s retention policy digest")
    return dict(held,
                assignment=_shaped_assignment(
                    taken["assignment"], f"{what}'s fixed assignment"),
                disposition=taken["disposition"],
                terminal_manifest_digest=taken["terminal_manifest_digest"],
                retention_disposition=taken["retention_disposition"],
                retention_policy_digest=taken["retention_policy_digest"])


def _settlement_document(value, what):
    """The WHOLE settlement, owned the same way on both sides.

    Its `evidence` is the member [P1] found unowned on readback: `_evidence`
    was reached only by the writer, so a stored settlement carrying a list, an
    unknown member or three null references read back clean and closed the
    obligation it claimed to end.
    """
    taken = boundaries.document(value, what, required=SETTLEMENT_MEMBERS)
    held = _selectors(taken, what)
    boundaries.identity(taken["intent"], f"{what}'s obligation identity")
    return dict(held,
                assignment=_shaped_assignment(
                    taken["assignment"], f"{what}'s fixed assignment"),
                intent=taken["intent"],
                evidence=_evidence(taken["evidence"]))


def _assignment(store, value, work_id, what):
    """The exact four-part assignment this obligation is fenced at, OWNED.

    REVIEW 2026-09-08T15-46-16Z [P1]: THE WORK ID WAS COMPARED AND THE
    AUTHORITY WAS NOT. A well-shaped assignment naming a foreign Authority and
    this stage's Work id was accepted and journalled, which is the W83781
    collision one layer up: `authority_uuid` and `work_id` are a PAIR, and
    half of a four-part identity is not three quarters of one. This store is
    bound to exactly one Authority -- the namespace every episode identity is
    derived in -- so the pair is compared against that binding rather than
    merely parsed.
    """
    held = _shaped_assignment(value, what)
    ref = held["work_ref"]
    if ref["authority_uuid"] != store.authority_uuid:
        _refuse(f"{what} names Authority {name_value(ref['authority_uuid'])} "
                f"and this Job store is bound to "
                f"{name_value(store.authority_uuid)}; one composed ending "
                f"belongs to the Authority whose namespace its episode "
                f"identities were derived in",
                category="refused", code="operation-collision")
    if ref["work_id"] != work_id:
        _refuse(f"{what} names Work {name_value(ref['work_id'])} and its "
                f"stage is at {name_value(work_id)}; one ending belongs to "
                f"one Work", category="refused", code="operation-collision")
    return held


def _evidence(value):
    """The settled ending's correlated owner references, closed and PRESENT.

    REVIEW 2026-09-08T15-46-16Z [P1]: NULL WAS ACCEPTED FOR ALL THREE REQUIRED
    REFERENCES, so an ordinary settlement carrying no reference to any owner's
    record closed the obligation and opened the dependent stage. A member that
    may be null is a member that is not required, and the point of these three
    is that an operator reading this store can find the acts that finished the
    ending. An optional member is OMITTED when there is nothing to name --
    which is what a pass with no gate to discharge does -- rather than present
    and empty.
    """
    held = boundaries.document(value, "a composed ending's settled evidence",
                               required=EVIDENCE_MEMBERS,
                               optional=EVIDENCE_OPTIONAL)
    for member in sorted(held):
        boundaries.text(held[member],
                        f"a composed ending's settled {member}")
    return {member: held[member] for member in
            EVIDENCE_MEMBERS + tuple(one for one in EVIDENCE_OPTIONAL
                                     if one in held)}


# WHICH VALIDATOR OWNS WHICH RECORD. One table, so "is this document held to
# its whole contract" has a written answer rather than a survey of call sites.
_PAYLOAD = {INTENT_KIND: _intent_document, SETTLED_KIND: _settlement_document}


def _committed(store, kind, stage_id, episode, what, rows=None):
    """One journalled record THIS STORE OWNS at that identity, or absence.

    ABSENCE AND A PRESENT INVALID RECORD ARE DIFFERENT ANSWERS, which is
    `intake.gate_discharge_of`'s rule and is here for the same reason: a
    consumer that read a malformed record as "nothing registered" would resume
    an ending it could not describe, or report one finished that never was.
    Only a genuinely missing row answers `None`.

    REVIEW 2026-09-08T15-46-16Z [P1]: A SIGNATURE IS NOT OWNERSHIP, AND THAT
    WAS THE WHOLE DEFECT. This used to prove the member set, the kind, the
    committed state and that the row's stored signature was the one this build
    derives from the bytes the row holds -- every one of which a LEGITIMATE
    record for another stage also satisfies. So a genuinely committed review
    settlement, copied through the public journal to the implementation
    stage's selected identity, was read here as that stage's own: pending
    discovery found nothing, the implementation projected `completed`, and its
    dependent opened. The record proved it was well made. Nothing asked whose
    it was.

    SO THREE MORE QUESTIONS ARE ASKED, IN THIS ORDER, AND EACH ONE IS ABOUT
    SOMETHING THE CALLER DID NOT SUPPLY:

      1. does the document's own stage and episode DERIVE the identity it was
         selected by? A record is stored at an identity built from two of its
         own members, so a document naming another pair is a document filed
         under somebody else's name;
      2. do its selectors still bind to this store's stage and episode rows --
         the same `_bound` proof a write makes, so a read is held to what a
         write was held to; and
      3. is its assignment this store's Authority and its stage's Work?

    NONE OF THEM IS OPTIONAL AND NONE IS DEFERRED TO A CALLER. A reader that
    returned the document and left the correlation to whoever asked would be
    the same defect wearing a different name, because the callers are a
    projection and a sweep and neither of them can know.
    """
    operation_id = _operation_id(kind, stage_id, episode)
    record = store.operation_record(operation_id)
    if record is None:
        return None
    if record["kind"] != kind:
        _refuse(f"{what} is journalled as {name_value(record['kind'])} and "
                f"this build records it as {name_value(kind)}",
                category="refused", code="operation-collision")
    if record["state"] != "committed":
        _refuse(f"{what} is recorded {name_value(record['state'])}; a "
                f"composed ending is read from a committed act and never from "
                f"one that did not settle", category="refused",
                code="precondition")
    # THE WHOLE PAYLOAD, NOT ITS OUTLINE. Review [P1]: this used to own the
    # member SET and then reach past the rest of the document for the members
    # it wanted, so every value outside the selectors and the assignment was
    # unowned on the way out. The validator below is the one the writer uses.
    document = _PAYLOAD[kind](boundaries.adopted(record["result"], what),
                              what)
    if record["signature"] != job_signature(kind, document):
        _refuse(f"{what} carries operands its own journalled signature does "
                f"not name; a durable identity is the exact canonical text "
                f"this build produces", category="refused", code="operation-collision")
    taken = {member: document[member] for member in SELECTORS}
    held = _operation_id(kind, taken["stage_id"], taken["episode"])
    if held != operation_id:
        _refuse(f"{what} was selected at {name_value(operation_id)} and its "
                f"own stage and episode derive {name_value(held)}; a record "
                f"is filed under an identity built from its own members, so "
                f"one filed under another stage's is that stage's record and "
                f"not this one's",
                category="refused", code="operation-collision")
    _bound(store, taken, rows)
    _assignment(store, document["assignment"],
                taken["work_id"], f"{what}'s fixed assignment")
    return document


def intent_of(store, stage_id, episode):
    """The registered composed-ending obligation for one episode, or absence.

    READ-ONLY, AND IT DECIDES NOTHING BEYOND OWNERSHIP. Whether the obligation
    is still owed is the settlement's question, one call over; this answers
    only whether one was registered here, by this store, for this stage's
    actual episode.
    """
    boundaries.identity(stage_id, "a stage id")
    return _intent_of(store, stage_id, episode)


def _intent_of(store, stage_id, episode, rows=None):
    return _committed(store, INTENT_KIND, stage_id, episode,
                      f"stage {name_value(stage_id)} episode {episode}'s "
                      f"registered composed ending", rows)


def settlement_of(store, stage_id, episode):
    """That obligation's settlement, PAIRED WITH IT, or absence.

    REVIEW 2026-09-08T15-46-16Z [P1]: AN ORPHAN IS NOT A SETTLEMENT AND A
    STRANGER IS NOT A PAIR. A settlement means one thing -- "the obligation
    recorded over there finished" -- so a record that names no intent, names
    another one, or disagrees with the intent this store actually holds is not
    evidence that anything finished. Reading one as though it were is how an
    unfinished ending stopped being discoverable.

    REVIEW 2026-09-08T16-00-28Z [P2]: AND THE OBLIGATION IS READ HERE RATHER
    THAN ACCEPTED. This took an `intent=` operand so a caller that already
    held one could avoid a second read, and a fabricated document that agreed
    with the settlement was therefore enough to answer a settlement whose
    obligation this store does not hold at all. The reasoning offered for it
    was wrong twice over: matching members are not ownership, and two ordinary
    reads on one connection are not a transactional snapshot, so the "one
    moment" the operand was supposed to buy never existed.
    """
    boundaries.identity(stage_id, "a stage id")
    return _settlement_of(store, stage_id, episode)


def _settlement_of(store, stage_id, episode, rows=None):
    what = (f"stage {name_value(stage_id)} episode {episode}'s settled "
            f"composed ending")
    settlement = _committed(store, SETTLED_KIND, stage_id, episode, what,
                            rows)
    if settlement is None:
        return None
    owed = _operation_id(INTENT_KIND, stage_id, episode)
    if settlement["intent"] != owed:
        _refuse(f"{what} settles {name_value(settlement['intent'])} and the "
                f"obligation at this identity is {name_value(owed)}",
                category="refused", code="operation-collision")
    held = _intent_of(store, stage_id, episode, rows)
    if held is None:
        _refuse(f"{what} settles an obligation this store never registered; a "
                f"settlement is the end of one and never the whole of one",
                category="refused", code="precondition")
    differing = [member for member in SELECTORS + ("assignment",)
                 if held[member] != settlement[member]]
    if differing:
        _refuse(f"{what} and the obligation it settles name a different "
                f"{', '.join(differing)}",
                category="refused", code="operation-collision")
    return settlement


def ending_of(store, stage_id, episode):
    """Both halves in one read, or absence when nothing was registered.

    THE PROJECTION ASKS THIS AND NOTHING ELSE, because "is an ending owed" is
    one question about two records and asking it as two would let a caller pair
    an intent with somebody else's settlement.

    AND A PRESENT INVALID HALF REFUSES OUT OF HERE, deliberately. `live_of`
    already refuses a stage with two live episodes rather than choosing
    between them, for the same reason: a control plane that cannot describe
    the store it holds must say so, and the alternatives here are worse than a
    visible refusal -- answering absence hides an unfinished ending, and
    answering "settled" opens a dependent stage on a stranger's record.

    THE SETTLEMENT IS SOUGHT EVEN WHEN THE OBLIGATION IS ABSENT, and that is
    not a wasted read. A settlement standing alone is a store this build
    cannot explain -- an obligation lost, or an ending recorded as finished
    that nobody ever registered -- and returning `None` for it would hand the
    stage back to the generic cleanup rules, which is precisely the state the
    obligation exists to stop being mistaken for a finished one.
    """
    boundaries.identity(stage_id, "a stage id")
    return _ending_of(store, stage_id, episode)


def _ending_of(store, stage_id, episode, rows=None):
    """Both halves, with `rows` the one read a many-stage pass already made.

    `rows` IS NOT AN OPERAND ANY CALLER CAN REACH. It is built inside
    `pending_endings` from this store's own stage rows and is used only to
    avoid re-reading them once per stage; the public entries above take
    nothing and read for themselves, which is [P2]'s requirement that a public
    reader establish the same owned result with and without it.
    """
    intent = _intent_of(store, stage_id, episode, rows)
    settlement = _settlement_of(store, stage_id, episode, rows)
    if intent is None:
        return None
    return {"intent": intent, "settlement": settlement}


def register_ending(store, attempt, *, assignment, disposition,
                    terminal_manifest_digest, retention_disposition,
                    retention_policy_digest):
    """Commit the obligation to finish this attempt's composed ending.

    BEFORE THE FIRST STEP THAT CAN REACH CLEANUP, which is the whole contract.
    An intent written afterwards would be an obligation recorded on the far
    side of the window it exists to cover.

    IT CERTIFIES NOTHING AND AUTHORIZES NOTHING. The disposition and the
    terminal digest are the WORKER's claims, kept because the driver needs them
    to re-enter the same ending; the frozen-result owner still proves the
    terminal against the envelope this manager measured, so persisting a claim
    never promotes it to evidence. The assignment and the retention operands
    are the deployment's own configured facts, kept for the same reason and
    with the same standing.

    A SECOND REGISTRATION REPLAYS. The identity is derived from the stage and
    its episode, so a tick that registered and then died re-enters here and
    adopts what it wrote; a DIFFERENT document under that identity refuses at
    the journal rather than rewriting an obligation somebody may already have
    acted on.
    """
    taken = _selectors(attempt, "a composed ending's attempt")
    _bound(store, taken)
    fixed = _assignment(store, assignment, taken["work_id"],
                        "a composed ending's fixed assignment")
    document = _intent_document(
        dict(taken, assignment=fixed, disposition=disposition,
             terminal_manifest_digest=terminal_manifest_digest,
             retention_disposition=retention_disposition,
             retention_policy_digest=retention_policy_digest),
        "a composed ending's obligation")
    operation_id = intent_operation_id(taken["stage_id"], taken["episode"])
    return store.transact(operation_id, INTENT_KIND,
                          job_signature(INTENT_KIND, document),
                          lambda connection: document)


def settle_ending(store, attempt, *, assignment, evidence):
    """Record that this attempt's composed ending actually finished.

    ONLY AFTER EVERY OWNER HAS ANSWERED, and this act is not one of them. The
    driver's evidence, W119548's gate discharge where the recorded fence owes
    one, and whatever routing the answer earned are each somebody else's
    journalled act; a settlement written before they succeed would end the
    retry that is the only thing left to complete them.

    AN OLD OBLIGATION CANNOT SETTLE A NEWER ONE. The assignment is compared
    against the registered intent's, so a caller holding a stale generation
    refuses here rather than closing an obligation that belongs to the round
    after it. And a settlement with no intent refuses outright: there is
    nothing for it to be the end of, and recording one would make an ending
    this store never registered look finished.
    """
    taken = _selectors(attempt, "a composed ending's attempt")
    _bound(store, taken)
    fixed = _assignment(store, assignment, taken["work_id"],
                        "a composed ending's fixed assignment")
    intent = intent_of(store, taken["stage_id"], taken["episode"])
    if intent is None:
        _refuse(f"stage {name_value(taken['stage_id'])} episode "
                f"{taken['episode']} registered no composed ending; a "
                f"settlement is the end of an obligation and never the whole "
                f"of one", category="refused", code="precondition")
    differing = [member for member in SELECTORS
                 if intent[member] != taken[member]]
    if differing:
        _refuse(f"the registered composed ending for stage "
                f"{name_value(taken['stage_id'])} episode {taken['episode']} "
                f"names a different {', '.join(differing)}",
                category="refused", code="operation-collision")
    if intent["assignment"] != fixed:
        _refuse(f"stage {name_value(taken['stage_id'])} episode "
                f"{taken['episode']} registered its composed ending at "
                f"generation {intent['assignment']['generation']} and this "
                f"settlement names {fixed['generation']}; an obligation is "
                f"settled at the assignment it was taken under",
                category="stale-assignment", code="generation")
    document = _settlement_document(
        dict(taken, assignment=fixed,
             intent=intent_operation_id(taken["stage_id"], taken["episode"]),
             evidence=evidence),
        "a composed ending's settlement")
    operation_id = settlement_operation_id(taken["stage_id"],
                                           taken["episode"])
    return store.transact(operation_id, SETTLED_KIND,
                          job_signature(SETTLED_KIND, document),
                          lambda connection: document)


def pending_endings(store):
    """Every registered ending with no settlement, oldest episode first.

    ENUMERATED FROM THE OWNED IDENTITIES, NOT FROM THE JOURNAL TABLE. The
    stages and their episodes are rows this store owns, and each one's record
    is found at an identity this build derives -- so nothing here reads raw
    journal SQL, and a deployment's other operations are invisible to it.

    PRIOR EPISODES ARE INCLUDED, and that is the case this function exists for.
    `advance_correction` ends both of a Job's episodes and opens their
    successors in one act, so an ending interrupted before its settlement is
    an obligation of an episode that is no longer live -- and a sweep that
    looked only at live episodes would walk past it forever.
    """
    rows = {one["stage_id"]: one for one in submission.stage_rows(store)}
    pending = []
    for stage_id in rows:
        for episode in episodes.episodes_of(store, stage_id):
            # ONE READ OF BOTH HALVES, so what this pass skips is an
            # obligation whose OWN settlement it has proved -- not merely a
            # record standing at the settlement's identity. Review
            # 2026-09-08T15-46-16Z [P1]: a stranger's document there was
            # enough to skip a stage forever.
            held = _ending_of(store, stage_id, episode["episode"], rows)
            if held is None or held["settlement"] is not None:
                continue
            pending.append(held["intent"])
    return pending


def attempt_of(store, intent):
    """The stage-and-episode view a recorded obligation still binds to.

    THE SAME VIEW A LIVE TICK WOULD HAVE PASSED, rebuilt from the rows rather
    than from the record: `episodes.attempting` merges the stage with the
    episode answering for it, and handing a deployment anything else would let
    a resumed ending be driven against selectors nobody proved.
    """
    taken = _selectors(intent, "a registered composed ending")
    stage, episode = _bound(store, taken)
    return episodes.attempting(stage, episode)
