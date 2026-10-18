"""The supported owner disposition surface: what is due, approve or deny the
exact reviewed candidate, record the HUMAN integration, and close on the
acceptance that was actually selected.

W321689, under the W321608 pilot, after W321688's record provider.

WHAT THE ASSESSMENT FOUND MISSING, and it is four separate absences rather than
one:

  NOTHING SAID WHAT WAS DUE. `Session.approve` and `Session.close` exist, and
  `stack_command.COMMANDS` exposed neither -- nor any read that answers "is
  there a candidate on this Work waiting for me". So the owner's disposition
  was reachable only by somebody who already knew the proposal identity, which
  means it was reachable only out of band.

  AN APPROVAL BOUND WHATEVER IT WAS HANDED. `approve` takes a proposal id and
  a policy generation; it does not ask which candidate bytes or which
  independent review the approver was LOOKING at. Those are operands of the
  human act, so this command requires them and compares them before the
  authority is asked to write anything.

  THE HUMAN INTEGRATION HAD NOWHERE TO GO. The selected closure is integrated
  documentation: a person imports the approved bytes and commits them. The
  commit is evidence of an act performed outside this system, so it is
  recorded as what it is -- a readable record cited in the dossier by digest,
  plus the authority's own immutable integration receipt naming the actor and
  the exact candidate.

  AND CLOSURE CHECKED A CAPABILITY, NOT AN ACCEPTANCE. `core.close` asks
  whether the actor may close -- correctly, because an approver closing Work
  somebody else executed is the ordinary case -- and it has no opinion about
  whether anything was accepted. `INTAKE_OUTCOMES` would therefore take
  `satisfying` on a Work whose only evidence was a passing verification: a
  green execution flag. The acceptance check for the SELECTED disposition
  lives here, in the command the owner runs, rather than being retrofitted
  into the generic transition.

WHAT THIS IS. A wrapper over the existing public faces. Every durable act goes
through a participant-bound `Session` minted for `--participant`, so the actor
on every receipt and the claimant on every check comes from the binding and
never from an operand -- there is no `--actor` here, and that absence is the
point. Reads go through the read-only authority handle, which takes no write
lock on a deployment somebody is serving from.

WHICH VERBS BIND A REQUEST, AND WHY NOT ALL OF THEM. `integrated` and `close`
are COMPOSITE: each performs more than one authority act, and each carries
operands no single transition takes -- a human's commit, the record that
attests it, the selected acceptance. So each binds its complete canonical
request under its own operation identity first, and the authority decides
whether a retry is the same act (`_bind`).

`approve` and `deny` need no such binding and deliberately do not have one.
Everything they RECORD -- the proposal, the receipt identity, the actor, the
disposition and the policy generation -- is already in the authority's own
approval signature, so a changed retry collides there. Their extra operands
(`--expect-candidate-digest`, `--expect-review`) are preconditions compared
against IMMUTABLE facts: a proposal's candidate digest and an accepted review's
receipt identity never change, so a retry naming different ones is refused by
the comparison rather than replayed. Adding a binding there would be ceremony
that checks nothing. `pending` writes nothing at all.

WHAT IT WILL NOT DO. It writes no repository file, moves no bytes into a
target, runs no Git command and performs no integration: it READS the human's
integration record, digests it, and records that the human said so. It grants
nothing -- an actor without the configured capability is refused by the
authority, and this command has no way to widen that. It infers no approval
from a worker's verdict or a finished Job, and it cannot: approval is an act
with its own identity, actor and policy generation.
"""
import argparse
import json
import os
import sys

from tools import dossier_command

__all__ = ["main"]

# The human integration record this command reads, and its CLOSED member set.
#
# IT IS A DOCUMENT A PERSON WROTE, which is why it is checked rather than
# generated: the integration happened outside this system, by a human with a
# checkout and Git ownership, and the only honest thing a program can do with
# that is read what they recorded, bind it to the exact candidate, and refuse
# when the two disagree. A command that MINTED this record would be attesting
# to an act it did not witness.
INTEGRATION_SCHEMA = "baton.v12.human-integration-record/1"
INTEGRATION_REQUIRED = ("schema", "authority_uuid", "work_id", "proposal_id",
                        "candidate_digest", "commit", "integrated_by",
                        "integrated_at")
# `notes` is the one place prose belongs: what was imported, what was checked,
# what the human wants the next reader to know.
INTEGRATION_OPTIONAL = ("notes", "paths")

# How much of a cited record this command will read into memory. An integration
# record names a commit and a candidate; anything approaching this is not one,
# and a bound is what stops a verb from being handed a file it will only partly
# see.
RECORD_LIMIT = 64 * 1024

# THE OWNER ACTION, as a CLOSED set of answers rather than a sentence a reader
# has to parse. Each one names the next act and who owes it, because "pending"
# that cannot distinguish "the reviewer has not finished" from "you have not
# approved" is not a pending action at all.
NO_CANDIDATE = "no-candidate"
AWAITING_VERIFICATION = "awaiting-verification"
AWAITING_REVIEW = "awaiting-review"
REVIEW_NOT_ACCEPTED = "review-not-accepted"
APPROVAL_DUE = "approval-due"
DENIED = "denied"
INTEGRATION_DUE = "integration-due"
CLOSURE_DUE = "closure-due"
CLOSED = "closed"

# What each answer MEANS, in the one sentence an operator needs. Kept beside the
# constants so an answer and its explanation cannot drift apart.
MEANING = {
    NO_CANDIDATE: "this Work has published no candidate, so no owner act is "
                  "due; nothing here is waiting on a human",
    AWAITING_VERIFICATION: "the latest candidate has no passed verification, "
                           "so execution has not produced a checkable result "
                           "yet",
    AWAITING_REVIEW: "the latest candidate passed verification and has no "
                     "independent review; the owner's act follows the "
                     "reviewer's, never the other way round",
    REVIEW_NOT_ACCEPTED: "independent review did not accept the latest "
                         "candidate, so there is nothing for the owner to "
                         "approve; a correction produces a new candidate",
    APPROVAL_DUE: "independent review accepted the latest candidate and no "
                  "approval receipt exists; the owner's approve or deny is "
                  "due on these exact bytes",
    DENIED: "the owner denied this candidate; the evidence is preserved and "
            "the remaining owner act is a non-satisfying closure or a new "
            "candidate",
    INTEGRATION_DUE: "the owner approved this candidate and no integration "
                     "receipt exists; a human imports the approved bytes, "
                     "commits them, and records that here",
    CLOSURE_DUE: "the candidate is approved and its human integration is "
                 "recorded; the owner's closure on the selected acceptance is "
                 "due",
    CLOSED: "this Work is terminal and its outcome is recorded; no further "
            "disposition is due",
}

# The outcomes a close may record, and the ONE of them this command treats as
# the selected acceptance. The others are ordinary endings and need no
# acceptance -- what they must not do is erase the evidence of why, which is
# why `close` reports every receipt and citation it found either way.
SATISFYING = "satisfying"

# THE SELECTED ACCEPTANCE, DURABLE, and where review 2026-10-18T16-39-10Z found
# it was not.
#
# The first cut COMPUTED the acceptance and printed it. So a closed Work could
# not say what it had been closed on: the four receipt identities, the exact
# candidate and the human's integration reference survived only in one
# command's standard output. Worse, an identical close retried after a lost
# response RE-DERIVED the acceptance from the filesystem, so a record edited in
# the meantime made the retry refuse while the canonical Work was already
# closed -- a recovery path that reports failure for work that committed.
#
# WHY THE RATIONALE CARRIES IT. §7's close takes a durable `rationale` and
# nothing else that an owner command may write, and the review explicitly does
# not prescribe a generic close redesign -- a new authority column for this
# would be exactly that. The rationale is also the right place on the merits:
# it is the durable text that says WHY this Work is satisfying, and "because
# candidate X, carrying these four receipts, was integrated by a human at
# commit C" is that why. Because it rides the rationale it rides the close
# OPERATION SIGNATURE too, so a retry naming a different candidate or
# acceptance COLLIDES rather than replaying somebody else's decision.
#
# ONE CANONICAL LINE, so a reader and this command parse the same thing. The
# operator's own prose comes first and is returned verbatim by `pending`.
ACCEPTANCE_SCHEMA = "baton.v12.owner-closure-acceptance/1"
ACCEPTANCE_MARKER = "owner-closure-acceptance: "
ACCEPTANCE_MEMBERS = ("schema", "proposal_id", "candidate_digest",
                      "verification", "review", "approval", "integration",
                      "evidence_reference", "evidence_digest", "commit")


def _acceptance_line(acceptance):
    """The one canonical line a closure's rationale carries.

    Compact and key-sorted, so the same acceptance renders identically twice --
    which is what makes it comparable on retry rather than merely readable.
    """
    return ACCEPTANCE_MARKER + json.dumps(
        {name: acceptance[name] for name in ACCEPTANCE_MEMBERS},
        sort_keys=True, separators=(",", ":"))


def _composed_rationale(operator_text, acceptance):
    return (operator_text if acceptance is None
            else operator_text + "\n\n" + _acceptance_line(acceptance))


def _rationale_parts(stored):
    """`(operator prose, acceptance document or None)` from a stored rationale.

    A rationale this command did not compose simply has no acceptance, which is
    an answer: every closure before this verb existed, and every non-satisfying
    ending, is prose and nothing else.
    """
    if type(stored) is not str:
        return stored, None
    place = stored.find("\n\n" + ACCEPTANCE_MARKER)
    if place < 0:
        return stored, None
    body = stored[place + 2 + len(ACCEPTANCE_MARKER):]
    try:
        held = json.loads(body)
    except ValueError:
        return stored, None
    if type(held) is not dict or held.get("schema") != ACCEPTANCE_SCHEMA:
        return stored, None
    return stored[:place], held


def _say(value):
    print(json.dumps(value, indent=2, sort_keys=True))


def _refused(message):
    print("refused: " + message, file=sys.stderr)
    return 2


def _authority(taken, *, writable):
    """Open the named authority; read-only unless this verb writes.

    `pending` only reads, and a read verb that opened the store writably would
    take a write lock on a deployment somebody is serving from -- the same rule
    `tools/dossier_command.py` follows for the same reason.
    """
    from baton_v12.authority import Authority

    if writable:
        return Authority.open(taken.authority_store,
                              expected_authority_uuid=taken.authority_uuid)
    return Authority.open_readonly(
        taken.authority_store, expected_authority_uuid=taken.authority_uuid)


def _receipts_of(authority, proposal_id):
    """The four receipt kinds for one proposal, every one of them named.

    ABSENT IS `None` AND IS REPORTED, rather than the key being missing: a
    consumer deciding what is due branches on four facts, and a reader of this
    JSON should see which of them has not happened yet.
    """
    return {kind: authority.receipt(proposal_id, kind)
            for kind in ("verification", "review", "approval", "integration")}


def _disposition(receipts, kind):
    held = receipts.get(kind)
    return None if held is None else held["disposition"]


def _owner_action(receipts):
    """Which act is due on ONE proposal, from its receipts alone.

    DERIVED FROM THE RECEIPTS AND NOTHING ELSE. No label, no phase and no Job
    status contributes: those say where execution got to, and the question here
    is what a human owes. The pilot's whole point is that a finished Job is not
    an acceptance.
    """
    if _disposition(receipts, "verification") != "passed":
        return AWAITING_VERIFICATION
    review = _disposition(receipts, "review")
    if review is None:
        return AWAITING_REVIEW
    if review != "accepted":
        return REVIEW_NOT_ACCEPTED
    approval = _disposition(receipts, "approval")
    if approval is None:
        return APPROVAL_DUE
    if approval != "approved":
        return DENIED
    if _disposition(receipts, "integration") is None:
        return INTEGRATION_DUE
    return CLOSURE_DUE


def _candidate(authority, work_id, proposal_id, expect_digest):
    """One proposal, PROVED to be this Work's and these bytes.

    TWO COMPARISONS THE AUTHORITY DOES NOT MAKE, and each is a way a human
    disposition could be bound to the wrong thing:

      THE WORK. `approve` and `integrate` take a proposal id and never ask
      which Work it belongs to, so an operator handed an identity from another
      Work would approve that one and the receipt would be perfectly valid.

      THE BYTES. The candidate digest is what the reviewer read and what the
      human is deciding about. A proposal id is stable while its digest is the
      fact that matters, so an approval that did not compare it would bind
      "whatever is at that identity" -- and the acceptance asks for a stale
      candidate to REFUSE.
    """
    proposal = authority.proposal(proposal_id)
    held = proposal["assignment_ref"]["work_ref"]["work_id"]
    if held != work_id:
        return None, (f"proposal {proposal_id!r} was published for Work "
                      f"{held!r} and this disposition names {work_id!r}; an "
                      f"owner act is bound to the Work's own candidate")
    if proposal["candidate_digest"] != expect_digest:
        return None, (f"proposal {proposal_id!r} holds candidate "
                      f"{proposal['candidate_digest']!r} and this disposition "
                      f"expects {expect_digest!r}; the bytes under review are "
                      f"what is being decided, so a changed candidate refuses "
                      f"rather than inheriting a decision made about other "
                      f"bytes")
    return proposal, None


def _read_record(root, reference):
    """The human integration record: contained, bounded, digested, parsed.

    ONE DESCRIPTOR FOR THE CHECK AND THE READ. `dossier_command._contained_open`
    is the containment rule W321688's review arrived at through a real
    interleaving -- every component opened relative to the one before it, so a
    parent replaced mid-resolution cannot redirect the read. Digesting the
    bytes and parsing them from the SAME descriptor is why this does not
    re-resolve the name: a record that passed the check and a record that was
    cited would otherwise be two different files.

    Returns `(digest, document, None)` or `(None, None, refusal_text)`.
    """
    state, descriptor = dossier_command._contained_open(root, reference)
    if state != dossier_command.EVIDENCE_PRESENT:
        return None, None, (
            f"{reference!r} resolves under {root!r} as {state!r}, so there is "
            f"no integration record to read; bytes reached through a symbolic "
            f"link are not under this root")
    try:
        # UNTIL EOF OR ONE BYTE PAST THE BOUND, because `os.read` answers "up
        # to" a count and a short read would digest a PREFIX of the record --
        # which the authority would then store as the digest of the whole file,
        # so `record verify` would report this dossier's own citation as
        # `changed` against bytes nobody changed.
        body = b""
        while len(body) <= RECORD_LIMIT:
            block = os.read(descriptor, RECORD_LIMIT + 1 - len(body))
            if not block:
                break
            body += block
    except OSError as failure:
        return None, None, f"{type(failure).__name__}: {failure}"
    finally:
        os.close(descriptor)
    if len(body) > RECORD_LIMIT:
        return None, None, (
            f"{reference!r} is larger than {RECORD_LIMIT} bytes; an "
            f"integration record names a commit and a candidate, and this is "
            f"not one")
    import hashlib

    digest = "sha256:" + hashlib.sha256(body).hexdigest()
    try:
        document = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, ValueError) as failure:
        return None, None, (
            f"{reference!r} did not read as an integration record: "
            f"{type(failure).__name__}: {failure}")
    if type(document) is not dict:
        return None, None, (
            f"{reference!r} holds {type(document).__name__}, and an "
            f"integration record is one document")
    return digest, document, None


def _record_fault(document, *, authority_uuid, work_id, proposal, commit):
    """Why this is not an integration record OF THIS INTEGRATION, or `None`.

    THE MEMBER SET IS CLOSED in both directions. A missing member is a record
    that cannot say what it integrated; an unknown one is an operator believing
    they recorded something this command reads, which is W321688's review
    finding one layer up -- a selection carried in a document nothing validates.

    AND EVERY IDENTITY IS COMPARED. A record naming another authority, Work,
    proposal or candidate is evidence of a DIFFERENT integration, and citing it
    here would bind this closure to somebody else's commit. The commit operand
    is compared too: a reference the record does not name is two claims about
    one integration.
    """
    # EVERY REQUIRED MEMBER IS NON-EMPTY TEXT, and the type is checked rather
    # than assumed: `{"commit": 433}` is not a commit reference, and a member
    # that reached the comparison below as a number would be reported back into
    # this command's own JSON as though it were one.
    absent = [name for name in INTEGRATION_REQUIRED
              if type(document.get(name)) is not str or not document[name]]
    if absent:
        return ("the integration record does not supply "
                + ", ".join(sorted(absent))
                + " as non-empty text")
    allowed = set(INTEGRATION_REQUIRED) | set(INTEGRATION_OPTIONAL)
    unknown = sorted(name for name in document if name not in allowed)
    if unknown:
        return ("the integration record names " + ", ".join(unknown)
                + ", which nothing here reads; a member this command would "
                  "ignore is one the operator believes they recorded")
    if document["schema"] != INTEGRATION_SCHEMA:
        return (f"the integration record is schema "
                f"{document['schema']!r} and this command reads "
                f"{INTEGRATION_SCHEMA!r}")
    for name, wanted in (("authority_uuid", authority_uuid),
                         ("work_id", work_id),
                         ("proposal_id", proposal["proposal_id"]),
                         ("candidate_digest", proposal["candidate_digest"])):
        if document[name] != wanted:
            return (f"the integration record names {name} "
                    f"{document[name]!r} and this integration is for "
                    f"{wanted!r}; that record is evidence of a different "
                    f"integration")
    if commit is not None and document["commit"] != commit:
        return (f"the integration record names commit "
                f"{document['commit']!r} and this operand names {commit!r}; "
                f"one integration has one commit")
    return None


def _cited_integration(authority, taken, proposal):
    """The dossier's own citation of THIS integration, resolved and intact.

    WHY CLOSURE RE-READS IT rather than trusting the integration receipt alone.
    The receipt proves the owner recorded an integration of these exact bytes.
    It does not prove the human's account of it still exists: a record deleted
    or rewritten between the integration and the closure would leave a
    satisfying closure whose only evidence of the human act was a receipt
    pointing at nothing.

    AND IT IS FOUND BY WHAT IT SAYS, not by where it sits. A reference operand
    at closure time could name any cited file; a naming convention would make
    a file name authoritative. So every citation is resolved and the one that
    IS an integration record for this Work, proposal and candidate is the
    evidence -- a record that cannot identify itself is not this integration's.
    """
    cited = authority.dossier_evidence(taken.work)
    looked = []
    for one in cited:
        digest, document, fault = _read_record(taken.root, one["reference"])
        if fault is not None:
            looked.append({"reference": one["reference"], "state": "unusable",
                           "detail": fault})
            continue
        if digest != one["digest"]:
            looked.append({"reference": one["reference"], "state": "changed",
                           "cited_digest": one["digest"], "actual": digest})
            continue
        why = _record_fault(document, authority_uuid=authority.authority_uuid,
                            work_id=taken.work, proposal=proposal, commit=None)
        if why is not None:
            looked.append({"reference": one["reference"],
                           "state": "not-this-integration", "detail": why})
            continue
        return {"reference": one["reference"], "digest": digest,
                "commit": document["commit"],
                "integrated_by": document["integrated_by"],
                "integrated_at": document["integrated_at"]}, looked
    return None, looked


def _evidence_now(root, reference, cited_digest):
    """What the cited record looks like RIGHT NOW, reported as its own fact.

    A committed integration is not undone by somebody editing the record
    afterwards, and a retry must not report failure for an act that happened.
    So drift is answered beside the committed outcome rather than instead of
    it -- which is the distinction review 2026-10-18T16-39-10Z asks for in both
    directions: replay the committed result, report the later drift separately.
    """
    digest, document, why = _read_record(root, reference)
    if why is not None:
        return {"reference": reference, "state": "unusable", "detail": why,
                "cited_digest": cited_digest}, None
    if digest != cited_digest:
        return {"reference": reference, "state": "changed",
                "cited_digest": cited_digest, "actual": digest}, None
    return {"reference": reference, "state": "intact",
            "cited_digest": cited_digest, "commit": document["commit"],
            "integrated_by": document["integrated_by"],
            "integrated_at": document["integrated_at"]}, document


def _derived(operation_id, suffix):
    """One authority act's operation identity, DERIVED from the command's.

    The command operation identity is the operator's one handle on the whole
    act, and the authority acts it performs each need their own. Deriving them
    means an exact retry derives the same ones -- so the authority replays each
    act -- while the request binding above decides, once, whether this is the
    same request at all.

    The frozen opaque grammar is 160 characters, so a command identity long
    enough to overflow it is refused HERE, naming the bound, rather than
    arriving at the journal as a malformed key.
    """
    from baton_v12.authority.errors import Refusal

    held = operation_id + ":" + suffix
    if len(held) > 160:
        raise Refusal(
            f"this command derives the operation identity {held!r} for its "
            f"{suffix} act, and a durable identity is at most 160 characters; "
            f"supply a shorter --operation-id")
    return held


def _bind(authority, taken, request):
    """THE ONE ARBITER of whether this invocation is the same act as before.

    W321689 review 2026-10-18T16-55-00Z. Two cuts of this command compared
    semantic operands BY HAND -- against the committed receipt, the citation
    row and, fatally, against the cited file's current bytes. Review broke both
    with the same move: change the record, then retry with a different commit.
    Mutable bytes are not a request identity, and a comparison that depends on
    them is a check that stops holding the moment somebody edits a file.

    So the complete canonical request is journalled under the command's own
    operation identity by `Authority.bind_request`, and the AUTHORITY decides:
    an exact retry replays the binding, and a request that differs in any
    member collides as "reused for different operands" before this command
    performs anything at all. Nothing here re-derives, re-compares or re-reads
    a file to make that decision.

    WHAT GOES IN IT: every operand that decides WHAT is being asked. Not
    `--root`, deliberately -- that is WHERE the evidence is resolved, not what
    is being decided, and the evidence itself is bound by digest at first
    execution and by the citation afterwards. A retry from a relocated checkout
    is the same request; a retry naming another commit is not.
    """
    from baton_v12.authority.errors import Refusal

    try:
        return authority.bind_request(taken.work, request,
                                      operation_id=taken.operation_id)
    except Refusal as refusal:
        # AND THE ANSWER SAYS WHAT THE IDENTITY ALREADY MEANS. A collision is
        # the one refusal an operator cannot diagnose from their own command
        # line: they have to see the request this identity already carries to
        # know whether to correct the call or to use a new identity. The
        # committed binding is a read, so showing it costs nothing.
        held = None
        try:
            held = authority.operation_result(taken.operation_id)
        except Refusal:
            pass
        _say({"work_id": taken.work, "verb": request["verb"],
              "operation_id": taken.operation_id, "replayed": False,
              "already_carries": held, "this_request": request,
              "performed": "nothing"})
        raise Refusal(
            f"this {request['verb']} request is not the one operation "
            f"{taken.operation_id!r} already carries: {refusal}. The answer "
            f"above shows both; a retry under one identity is the same request "
            f"or it is refused, and nothing was done") from None


# WHAT EACH ACT'S COMMITTED RESULT LOOKS LIKE, as a closed member set.
#
# Review 2026-10-18T17-12-52Z. The previous cut read the journal at the
# operator-supplied citation identity and treated ANY result there as proof
# that this command had already validated the human's record. So an ordinary
# `record cite` under that identity -- or any other act that happened to use
# it -- let a fresh request skip validation entirely and write an integration
# receipt for a commit nobody had read. A journal result is not a provenance:
# what is being asked is "is this MY act's committed outcome", and that is
# answered by the result's own shape and operands.
CITATION_RESULT = ("work_id", "reference", "digest", "act_id", "recorded_at")
INTEGRATION_RESULT = ("kind", "receipt_id", "proposal_id", "actor",
                      "disposition")
CLOSE_RESULT = ("outcome", "actor", "assignment", "decision")


def _citation_fault(held, taken, evidence_digest):
    """Why the result at the citation identity is not this act's citation.

    THE DIGEST IS PART OF THIS, and review 2026-10-18T17-21-14Z is why. The
    previous cut compared the Work, the reference and the recording act and
    stopped -- so a citation of OTHER BYTES at that identity passed, and on a
    second invocation the request binding (which survives a refused citation)
    made the command skip reading and re-offering and write a receipt on
    evidence it had never matched. A citation is this integration's only if it
    cites the bytes this request validated.
    """
    if sorted(held) != sorted(CITATION_RESULT):
        return (f"operation {taken.evidence_operation_id!r} already carries a "
                f"result with members {sorted(held)}, which is not a dossier "
                f"citation at all")
    if held["work_id"] != taken.work or held["reference"] != taken.reference:
        return (f"operation {taken.evidence_operation_id!r} already cited "
                f"{held['reference']!r} of Work {held['work_id']!r}, and this "
                f"integration cites {taken.reference!r} of {taken.work!r}")
    if held["act_id"] != taken.evidence_operation_id:
        return (f"the citation at {taken.evidence_operation_id!r} was recorded "
                f"by act {held['act_id']!r}")
    if held["digest"] != evidence_digest:
        return (f"operation {taken.evidence_operation_id!r} cites "
                f"{taken.reference!r} at {held['digest']!r} and this "
                f"integration validated {evidence_digest!r}; a citation is "
                f"this integration's evidence only if it cites the bytes this "
                f"request validated")
    return None


def _integration_fault(held, taken):
    """Why the result at the derived identity is not this act's receipt."""
    if sorted(held) != sorted(INTEGRATION_RESULT) \
            or held.get("kind") != "integration":
        return (f"the derived operation identity already carries a result with "
                f"members {sorted(held)}, which is not an integration receipt")
    if held["receipt_id"] != taken.integration_id \
            or held["proposal_id"] != taken.proposal \
            or held["actor"] != taken.participant:
        return (f"the derived operation identity already carries integration "
                f"receipt {held['receipt_id']!r} of proposal "
                f"{held['proposal_id']!r} by {held['actor']!r}, and this call "
                f"names {taken.integration_id!r} of {taken.proposal!r} by "
                f"{taken.participant!r}")
    return None


def _closure_fault(held, taken):
    """Why the result at the derived identity is not this act's close."""
    if sorted(held) != sorted(CLOSE_RESULT):
        return (f"the derived operation identity already carries a result with "
                f"members {sorted(held)}, which is not a close")
    if held["outcome"] != taken.outcome or held["actor"] != taken.participant:
        return (f"the derived operation identity already carries a "
                f"{held['outcome']!r} close by {held['actor']!r}, and this "
                f"call names {taken.outcome!r} by {taken.participant!r}")
    return None


def _integration_request(taken, evidence_digest):
    """The canonical `integrated` request: what the owner is asking, exactly.

    `evidence_digest` IS IN IT, which is the correction review
    2026-10-18T17-21-14Z asks for. The request is not "integrate citing that
    reference" -- it is "integrate citing those BYTES, which I read and
    validated". With the digest bound, a recovery takes it from the journal
    instead of from the file, so the citation step needs no filesystem at all
    and a citation of other bytes can never satisfy this request.
    """
    return {"verb": "integrated", "participant": taken.participant,
            "work": taken.work, "proposal": taken.proposal,
            "candidate_digest": taken.expect_candidate_digest,
            "reference": taken.reference, "commit": taken.commit,
            "evidence_digest": evidence_digest,
            "integration_id": taken.integration_id,
            "evidence_operation": taken.evidence_operation_id}


def _bound_evidence_digest(prior):
    """The digest a committed request binding says this act validated.

    `(digest, fault)`. A binding this command did not write -- or one whose
    document does not carry the member -- is not this request's provenance, and
    answering from it would be the same mistake one layer along.
    """
    held = prior.get("request") if type(prior) is dict else None
    if type(held) is not dict or held.get("verb") != "integrated":
        return None, ("that command identity already carries a binding that is "
                      "not an integration request")
    digest = held.get("evidence_digest")
    if type(digest) is not str or not digest:
        return None, ("the binding at that command identity records no "
                      "validated evidence digest, so it cannot be this "
                      "request's provenance")
    return digest, None


def _closure_request(taken, expect):
    """The canonical `close` request, including the assignment precondition.

    `expect` IS PART OF THE REQUEST, PRESENCE AND VALUE. Review
    2026-10-18T16-55-00Z: the previous cut parsed `--expect-assignment` and
    then its hand-rolled replay never looked at it, so a close performed
    WITHOUT an assignment precondition could be retried WITH one and be
    answered as a replay -- dropping the compare-and-swap the authority's own
    close signature distinguishes. `None` here means "no precondition was
    named", which is a different request from any identity at all.
    """
    return {"verb": "close", "participant": taken.participant,
            "work": taken.work, "outcome": taken.outcome,
            "rationale": taken.rationale, "proposal": taken.proposal,
            "candidate_digest": taken.expect_candidate_digest,
            "expect_assignment": expect}

# -- the verbs ---------------------------------------------------------------

def _pending(taken):
    """What is due on one Work, and who owes it. READ-ONLY.

    A deployment-wide inventory is deliberately NOT here. This authority's
    public reads answer about one Work or about labels, and inventing a
    "every Work waiting on a human" sweep would be a surface this Work did not
    select. The pilot's dossier binding is how an operator gets from a record
    to a Work id; `record read --locator` answers that direction already.
    """
    with _authority(taken, writable=False) as authority:
        work = authority.project_work(taken.work)
        dossier = authority.dossier_of(taken.work)
        proposals = []
        for one in authority.proposals_of(taken.work):
            receipts = _receipts_of(authority, one["proposal_id"])
            proposals.append(dict(one, receipts=receipts,
                                  owner_action=_owner_action(receipts)))
        # THE SELECTED ACCEPTANCE, READ BACK. Review 2026-10-18T16-39-10Z: a
        # closed Work could not say what it had been closed ON through any
        # supported read, and the attributable close decision was not reported
        # here either -- so the one surface an operator uses to ask about a
        # Work went quiet at exactly the point the record matters most.
        operator_text, accepted = _rationale_parts(work["rationale"])
        answer = {
            "authority_uuid": authority.authority_uuid,
            "work": {name: work[name] for name in
                     ("work_id", "route", "scope", "status", "phase",
                      "outcome", "handler", "assignment")},
            "rationale": operator_text,
            "closure_acceptance": accepted,
            "close_decision": work["close_decision"],
            "dossier": dossier,
            "evidence": (authority.dossier_evidence(taken.work)
                         if dossier is not None else []),
            "policy_generation": authority.policy_generation(),
            "canonical_target": authority.canonical_target(),
            "proposals": proposals,
        }
        # AND WHETHER THE ACCEPTED EVIDENCE IS STILL THERE, when a root is
        # named. Reported as its own fact: a closure that committed is not
        # undone by a later edit, and an operator auditing a closed Work wants
        # to know about the edit anyway.
        if accepted is not None and taken.root is not None:
            answer["evidence_now"] = _evidence_now(
                taken.root, accepted["evidence_reference"],
                accepted["evidence_digest"])[0]
        # THE WORK'S OWN STATUS WINS. A closed Work owes nothing, whatever its
        # last proposal's receipts say -- and reporting `approval-due` on a
        # terminal Work would send an operator to perform an act the authority
        # will refuse.
        if work["status"] != "open":
            action = CLOSED
        elif not proposals:
            action = NO_CANDIDATE
        else:
            action = proposals[-1]["owner_action"]
        answer["owner_action"] = action
        answer["due"] = MEANING[action]
        answer["latest_proposal"] = (proposals[-1]["proposal_id"]
                                     if proposals else None)
        if taken.participant is not None:
            # WHETHER THE ASKER CAN ACTUALLY DO IT, in the Work's own scope.
            # An operator told an act is due and not told they hold no grant
            # for it learns that from a refusal later; this is the same fact,
            # earlier, and it is a READ -- holding a capability is not using it.
            answer["participant"] = taken.participant
            answer["holds"] = {
                capability: authority.holds_capability(
                    taken.participant, capability, scope=work["scope"])
                for capability in ("approve", "integrate", "close")}
        _say(answer)
    return 0


def _decide(taken, disposition):
    """The owner's approve or deny, bound to the exact candidate and review.

    EVERY COMPARISON BEFORE THE WRITE. The authority refuses an approval
    without an accepted review and binds the policy generation into the
    operation identity, so a changed retry collides rather than replaying. What
    it cannot do is check the operands of the HUMAN act -- which candidate
    bytes, which independent review, and whether the generation named is the
    one in force now -- so those are checked here and the session is asked only
    once they hold.

    THE ACTOR IS THE SESSION. There is no `--actor`: `--participant` mints the
    session and the authority takes the receipt's actor from that binding, so a
    caller cannot name an identity the authority then treats as authenticated.
    """
    with _authority(taken, writable=True) as authority:
        proposal, fault = _candidate(authority, taken.work, taken.proposal,
                                     taken.expect_candidate_digest)
        if fault is not None:
            return _refused(fault)
        receipts = _receipts_of(authority, taken.proposal)
        if _disposition(receipts, "verification") != "passed":
            return _refused(
                f"proposal {taken.proposal!r} has no passed verification, so "
                f"there is nothing an owner can decide about it yet")
        review = receipts.get("review")
        if review is None or review["disposition"] != "accepted":
            return _refused(
                f"proposal {taken.proposal!r} has no accepted independent "
                f"review ({_disposition(receipts, 'review')!r}), and an owner "
                f"disposition follows independent review rather than "
                f"substituting for it")
        if review["receipt_id"] != taken.expect_review:
            return _refused(
                f"the accepted review of proposal {taken.proposal!r} is "
                f"{review['receipt_id']!r} and this disposition expects "
                f"{taken.expect_review!r}; the owner decides on the review "
                f"they actually read")
        # THE GENERATION IN FORCE, not merely a positive integer. The authority
        # binds whatever generation it is given into the operation signature,
        # which makes a retry under a different one collide -- it does not make
        # a decision taken under a stale configuration refuse, and the
        # acceptance asks for that.
        generation = authority.policy_generation()
        if taken.policy_generation != generation:
            return _refused(
                f"this authority's policy generation is {generation} and this "
                f"disposition names {taken.policy_generation}; an approval "
                f"binds the configuration it was granted under, so a stale "
                f"generation refuses rather than being recorded as current")
        session = authority.session(taken.participant)
        said = session.approve({"proposal_id": taken.proposal,
                                "approval_id": taken.approval_id,
                                "disposition": disposition,
                                "operation_id": taken.operation_id,
                                "policy_generation": taken.policy_generation})
        _say({"authority_uuid": authority.authority_uuid,
              "work_id": taken.work, "approval": said,
              "bound": {"candidate_digest": proposal["candidate_digest"],
                        "review_receipt": review["receipt_id"],
                        "policy_generation": taken.policy_generation,
                        "actor": session.participant},
              "integration_due": disposition == "approved",
              "evidence_preserved": True})
    return 0


def _integrated(taken):
    """Record the HUMAN integration: the request bound, the record cited, the
    receipt written.

    THREE DURABLE ACTS AND THEY ARE NOT ONE.

      THE REQUEST BINDING is what makes this command operation identity MEAN
      the act it performed -- see `_bind`. It is first, before any effect,
      because that is the only position from which it can refuse a changed
      retry without one.

      THE CITATION binds the human's own account of what they imported and
      committed, by digest, through W321688's record provider.

      THE RECEIPT is the authority's immutable, separately attributable
      statement that this actor integrated this exact candidate. Neither
      substitutes for the other: a citation has no actor, and a receipt has no
      commit.

    EACH AUTHORITY ACT HAS ITS OWN IDENTITY, derived from the command's, so an
    exact retry replays every one of them and a partially completed act --
    citation committed, receipt not -- continues from where it stopped. The
    command never decides a replay by comparing operands itself: two cuts of
    this file did, and review 2026-10-18T16-55-00Z broke both by editing the
    cited file, because a comparison that reads mutable bytes stops holding the
    moment somebody writes to them.

    AND THE ACTOR IS CHECKED BEFORE THE CITATION. The authority refuses the
    receipt to a participant holding no `integrate` grant, which is correct and
    is one act too late: the citation would already have been recorded for an
    actor who could not perform the integration it belongs to. So the grant is
    read first, in the Work's own scope, and a wrong actor writes nothing.

    AND NOTHING IS INTEGRATED HERE. No byte is moved, no file is written, no
    Git command runs. A human did that and owns it; this records it.
    """
    from baton_v12.authority.dossier import check_evidence_reference
    from baton_v12.authority.errors import Refusal

    # THE GRAMMAR BEFORE THE FILESYSTEM, which is W321688 review P1's finding
    # in its own `cite` verb: a malformed or escaping reference must not be
    # opened and read before the authority is asked whether it is citable.
    check_evidence_reference(taken.reference)
    citation_act = taken.evidence_operation_id
    receipt_act = _derived(taken.operation_id, "integrate")
    with _authority(taken, writable=True) as authority:
        proposal, fault = _candidate(authority, taken.work, taken.proposal,
                                     taken.expect_candidate_digest)
        if fault is not None:
            return _refused(fault)
        # WHAT MAY JUSTIFY SKIPPING VALIDATION, and it is exactly one thing:
        # THIS COMPLETE REQUEST HAVING BEEN VALIDATED AND BOUND BEFORE.
        #
        # Review 2026-10-18T17-12-52Z found the previous answer -- a committed
        # result at the operator-supplied citation identity -- was no such
        # proof: an ordinary `record cite` under that identity let a fresh
        # request skip validation and write a receipt for a commit nobody had
        # read. The binding is the only durable record of "this exact request
        # passed validation", because validation precedes it and the authority
        # refuses to bind a different request under that identity.
        #
        # AND THE BINDING CARRIES THE VALIDATED DIGEST, which is review
        # 2026-10-18T17-21-14Z: a binding alone does not say that the citation
        # SUCCEEDED, so a recovery reads the digest it validated out of the
        # journal and holds the citation to it. Nothing below reads a file to
        # decide whether this is the same act.
        prior = authority.operation_result(taken.operation_id)
        if prior is None:
            receipts = _receipts_of(authority, taken.proposal)
            approval = receipts.get("approval")
            if approval is None or approval["disposition"] != "approved":
                return _refused(
                    f"proposal {taken.proposal!r} is not approved "
                    f"({_disposition(receipts, 'approval')!r}), so there is no "
                    f"approved candidate for a human to have integrated; a "
                    f"passed verification or a finished Job is not an approval")
            evidence_digest, document, why = _read_record(taken.root,
                                                          taken.reference)
            if why is not None:
                return _refused(why)
            why = _record_fault(document,
                                authority_uuid=authority.authority_uuid,
                                work_id=taken.work, proposal=proposal,
                                commit=taken.commit)
            if why is not None:
                return _refused(why + ". Nothing was recorded")
            scope = authority.project_work(taken.work)["scope"]
            if not authority.holds_capability(taken.participant, "integrate",
                                              scope=scope):
                return _refused(
                    f"{taken.participant!r} does not hold the integrate "
                    f"capability in {scope!r}, so it cannot record this "
                    f"integration; nothing was cited and nothing was changed")
        else:
            evidence_digest, why = _bound_evidence_digest(prior)
            if why is not None:
                return _refused(why + ". Nothing was changed")
        cited = authority.operation_result(citation_act)
        said = authority.operation_result(receipt_act)
        # EVERY IDENTITY THIS ACT WOULD USE MUST BE ITS OWN, checked BEFORE the
        # binding so a conflict refuses without consuming the command identity
        # -- and refuses the SAME WAY every time it is retried, which is what
        # review 2026-10-18T17-21-14Z found this command had lost.
        for why in (_citation_fault(cited, taken, evidence_digest)
                    if cited is not None else None,
                    _integration_fault(said, taken)
                    if said is not None else None):
            if why is not None:
                _say({"work_id": taken.work, "reference": taken.reference,
                      "validated_digest": evidence_digest,
                      "citation_operation": citation_act,
                      "already_recorded": cited, "integration": said,
                      "performed": "nothing"})
                return _refused(
                    why + ". An integration records its own evidence under its "
                    "own identities; nothing was cited, nothing was changed, "
                    "and a fresh --operation-id with a fresh "
                    "--evidence-operation-id is how a different act is "
                    "performed")
        replayed = cited is not None and said is not None
        # THE ARBITER: an exact retry replays this binding, and a request
        # differing in any member collides here -- so nothing below runs for a
        # changed retry.
        bound = _bind(authority, taken,
                      _integration_request(taken, evidence_digest))
        if cited is None:
            # THE VALIDATED DIGEST, not one read from a file. A recovery that
            # has not cited yet completes from the journal, so a record edited
            # or deleted in the meantime cannot strand it -- and what gets
            # cited is still exactly what this request validated.
            cited = authority.record_dossier_evidence(
                taken.work, taken.reference, evidence_digest,
                operation_id=citation_act)
        session = authority.session(taken.participant)
        if said is None:
            try:
                said = session.integrate(
                    {"proposal_id": taken.proposal,
                     "integration_id": taken.integration_id,
                     "operation_id": receipt_act})
            except Refusal as refusal:
                # A DURABLE REFUSAL IS A COMMITTED OUTCOME of that operation
                # identity -- the stale-target integration journals its attempt
                # before refusing -- so a retry under the same identity replays
                # the REFUSAL rather than reattempting. Saying "just retry"
                # there would send an operator round a loop that cannot end.
                _say({"authority_uuid": authority.authority_uuid,
                      "work_id": taken.work, "request": bound,
                      "cited": cited, "integration": None,
                      "durable": refusal.durable, "detail": str(refusal)})
                if refusal.durable:
                    return _refused(
                        f"the integration record is cited and the integration "
                        f"receipt was durably refused: {refusal}. That refusal "
                        f"is the committed outcome of integration identity "
                        f"{taken.integration_id!r} and operation "
                        f"{receipt_act!r}, so resolve the cause and record the "
                        f"integration under NEW identities; the citation "
                        f"stands and is replayed as it is")
                return _refused(
                    f"the integration record is cited and the integration "
                    f"receipt was refused: {refusal}. Nothing durable was "
                    f"written for it, so retrying under the same command "
                    f"identity replays the citation and reattempts the receipt")
        _say({"authority_uuid": authority.authority_uuid,
              "work_id": taken.work, "request": bound, "cited": cited,
              "integration": said, "replayed": replayed,
              "bound": {"candidate_digest": proposal["candidate_digest"],
                        "commit": taken.commit,
                        "actor": taken.participant},
              # THE RECORD AS IT STANDS NOW, reported as its own fact rather
              # than as a verdict: the integration committed, and whether the
              # human's account of it still holds the cited bytes is a
              # different question an operator needs answered separately.
              "evidence_now": _evidence_now(taken.root, taken.reference,
                                            cited["digest"])[0],
              "closure_due": True})
    return 0


def _close(taken):
    """Close on the acceptance that was SELECTED, or refuse and change nothing.

    THE ASYMMETRY IS THE WHOLE VERB. A satisfying closure is the claim that
    this Work delivered what it was for, so it requires the selected
    acceptance: a passed verification, an accepted independent review, the
    owner's approval, the owner's integration receipt, and the human's
    integration record still intact where the dossier cites it. Any one of them
    missing refuses, and the refusal names which.

    EVERY OTHER OUTCOME IS AN ORDINARY ENDING and requires none of that --
    denied work, abandoned work and cancelled work all close honestly. What
    they must not do is lose the account of why, so the answer reports every
    receipt and citation that exists at closure either way. Nothing here
    deletes, rewrites or withdraws evidence; there is no code in this file that
    can.

    THE ACCEPTANCE IS DURABLE AND REPLAYABLE, which review
    2026-10-18T16-39-10Z found it was not. It is composed into the close's own
    `rationale`, so it survives in the canonical record, rides the authority's
    own close signature, and is read back by `pending` -- see
    `ACCEPTANCE_SCHEMA`.

    AND THE REPLAY IS THE AUTHORITY'S, NOT THIS COMMAND'S. The previous cut
    answered a committed close from the journal itself and compared the
    operands by hand -- and review 2026-10-18T16-55-00Z found it had dropped
    `--expect-assignment` from that comparison, so a close performed with no
    assignment precondition could be retried WITH one and be answered as a
    replay. Now the complete request is bound first (`_bind`), the acceptance
    clause on a retry is read from the Work's own stored rationale rather than
    re-derived from the filesystem, and `session.close` is called with exactly
    the operands the first execution used: the authority replays its committed
    result or refuses as "different operands". A record edited after a
    successful close therefore neither breaks the recovery nor goes unreported
    -- the drift is answered beside the committed outcome.
    """
    from baton_v12.authority.core import INTAKE_OUTCOMES

    if taken.outcome not in INTAKE_OUTCOMES:
        return _refused(
            f"{taken.outcome!r} is not a terminal outcome; this authority "
            f"records " + ", ".join(sorted(INTAKE_OUTCOMES)))
    if ACCEPTANCE_MARKER in taken.rationale:
        # THE MARKER IS THIS COMMAND'S, so an operator cannot hand-write a
        # clause and have a later readback report it as the acceptance this
        # closure actually checked.
        return _refused(
            f"a rationale may not contain {ACCEPTANCE_MARKER!r}: that line is "
            f"the selected acceptance, and this command composes it from the "
            f"receipts and evidence it verified")
    expect = None
    if taken.expect_assignment is not None:
        try:
            with open(taken.expect_assignment, "r", encoding="utf-8") as one:
                expect = json.load(one)
        except (OSError, ValueError) as failure:
            return _refused(f"{taken.expect_assignment!r} did not read as an "
                            f"assignment identity: "
                            f"{type(failure).__name__}: {failure}")
    # THE OPERAND SHAPE FIRST, before any state is read, because it is a rule
    # about the REQUEST rather than about the record -- and because the replay
    # path below must not be reachable by a call that omitted the operands its
    # comparison is made of.
    named = [name for name, value in
             (("--proposal", taken.proposal),
              ("--expect-candidate-digest", taken.expect_candidate_digest),
              ("--root", taken.root)) if value is not None]
    if taken.outcome == SATISFYING:
        if len(named) != 3:
            return _refused(
                "a satisfying closure names the candidate it accepts: "
                "--proposal, --expect-candidate-digest and --root are "
                "required, because the claim being recorded is that THOSE "
                "bytes were approved and integrated")
    elif named:
        # AN OPERAND SUPPLIED AND IGNORED IS ONE THE CALLER BELIEVES IT CHOSE.
        # These three bind the acceptance a SATISFYING closure records; on any
        # other outcome nothing reads them, and silently dropping them would
        # let an operator believe this ending was checked against that
        # candidate.
        return _refused(
            f"a {taken.outcome!r} closure does not take " + ", ".join(named)
            + "; those bind the acceptance a satisfying closure records, and "
              "an ending that is not one checks no candidate. Nothing was "
              "changed")
    close_act = _derived(taken.operation_id, "close")
    with _authority(taken, writable=True) as authority:
        work = authority.project_work(taken.work)
        # WHAT MAY JUSTIFY SKIPPING VALIDATION, and it is the same one thing
        # `integrated` relies on: this complete request having been validated
        # and bound before. A result at the derived close identity alone is not
        # that proof -- see review 2026-10-18T17-12-52Z -- and it must also BE
        # this act's own close rather than whatever else reused the identity.
        validated = authority.operation_result(taken.operation_id) is not None
        committed = authority.operation_result(close_act)
        if committed is not None:
            why = _closure_fault(committed, taken)
            if why is not None:
                return _refused(
                    why + ". A closure is performed under its own identity; "
                    "nothing was changed")
        if not validated:
            # Not a recovery of this request, whatever the journal holds at the
            # derived identity: validate from the beginning.
            committed = None
        acceptance = {"outcome": taken.outcome, "required": False}
        if committed is not None:
            # THE ACCEPTANCE THIS IDENTITY RECORDED, read from the Work's own
            # rationale. Nothing is compared here: the binding below is the one
            # arbiter of whether this is the same request, and the operator's
            # prose is one of the members it compares.
            _operator_text, accepted = _rationale_parts(work["rationale"])
            if accepted is not None:
                acceptance = dict(accepted, required=True,
                                  outcome=work["outcome"])
        elif taken.outcome == SATISFYING:
            proposal, fault = _candidate(authority, taken.work, taken.proposal,
                                         taken.expect_candidate_digest)
            if fault is not None:
                return _refused(fault)
            receipts = _receipts_of(authority, taken.proposal)
            action = _owner_action(receipts)
            if action != CLOSURE_DUE:
                return _refused(
                    f"a satisfying closure of {taken.work!r} is refused: the "
                    f"owner action due on proposal {taken.proposal!r} is "
                    f"{action!r} -- {MEANING[action]}. A capability to close "
                    f"is not an acceptance, and nothing was changed")
            found, looked = _cited_integration(authority, taken, proposal)
            if found is None:
                _say({"work_id": taken.work, "proposal": taken.proposal,
                      "citations_examined": looked})
                return _refused(
                    f"a satisfying closure of {taken.work!r} is refused: the "
                    f"dossier cites no intact human integration record for "
                    f"candidate {proposal['candidate_digest']!r} under "
                    f"{taken.root!r}; the states above say what was examined "
                    f"and why each was rejected. Nothing was changed")
            acceptance = {
                "schema": ACCEPTANCE_SCHEMA,
                "outcome": taken.outcome, "required": True,
                "proposal_id": taken.proposal,
                "candidate_digest": proposal["candidate_digest"],
                "verification": receipts["verification"]["receipt_id"],
                "review": receipts["review"]["receipt_id"],
                "approval": receipts["approval"]["receipt_id"],
                "integration": receipts["integration"]["receipt_id"],
                "evidence_reference": found["reference"],
                "evidence_digest": found["digest"],
                "commit": found["commit"],
                "human_integration": found}
        # THE EVIDENCE AS IT STANDS AT CLOSURE, reported whatever the outcome.
        # A non-satisfying ending is where an account of the work is most
        # likely to be wanted later, and it is exactly where a terse answer
        # would leave none.
        preserved = {"evidence": authority.dossier_evidence(taken.work),
                     "dossier": authority.dossier_of(taken.work),
                     "proposals": [
                         {"proposal_id": one["proposal_id"],
                          "candidate_digest": one["candidate_digest"],
                          "receipts": _receipts_of(authority,
                                                   one["proposal_id"])}
                         for one in authority.proposals_of(taken.work)]}
        if committed is None:
            # TWO PRECONDITIONS THE AUTHORITY WOULD REFUSE ANYWAY, checked here
            # so that a CORRECTABLE mistake does not consume the command
            # identity. The request is bound before any effect, which is what
            # makes a changed retry refuse -- and it would also mean an
            # operator who forgot `--expect-assignment` could not simply add it
            # and rerun. These two refusals come first, so they can.
            if not authority.holds_capability(taken.participant, "close",
                                              scope=work["scope"]):
                return _refused(
                    f"{taken.participant!r} does not hold the close "
                    f"capability in {work['scope']!r}; a closure is performed "
                    f"by the configured actor, and nothing was changed")
            if work["assignment"] is not None \
                    and taken.expect_assignment is None:
                return _refused(
                    f"{taken.work!r} has a live assignment, so a close that "
                    f"ends it must supply --expect-assignment naming that "
                    f"exact identity; `pending` reports it under "
                    f"work.assignment. Nothing was changed")
        # THE ARBITER, after validation and before the close: an exact retry
        # replays this binding, and a request differing in any member --
        # including the PRESENCE of an assignment precondition -- collides here.
        bound = _bind(authority, taken, _closure_request(taken, expect))
        session = authority.session(taken.participant)
        # THE ACCEPTANCE RIDES THE RATIONALE, so it is durable, it is in the
        # authority's own close signature, and it is reproduced here EXACTLY as
        # the first execution composed it -- from the stored clause on a retry,
        # from the verified receipts and evidence on a first execution.
        operands = {"work_id": taken.work, "operation_id": close_act,
                    "outcome": taken.outcome,
                    "rationale": _composed_rationale(
                        taken.rationale,
                        {name: acceptance[name] for name in ACCEPTANCE_MEMBERS}
                        if acceptance["required"] else None)}
        if expect is not None:
            operands["expect"] = expect
        said = session.close(operands)
        answer = {"authority_uuid": authority.authority_uuid,
                  "work_id": taken.work, "closed": said, "request": bound,
                  "replayed": committed is not None,
                  "acceptance": acceptance, "actor": session.participant,
                  "work_at_invocation": {
                      "status": work["status"], "phase": work["phase"],
                      "outcome": work["outcome"]},
                  "preserved": preserved}
        # LATER DRIFT, BESIDE THE COMMITTED OUTCOME AND NOT INSTEAD OF IT.
        if acceptance["required"] and taken.root is not None:
            answer["evidence_now"] = _evidence_now(
                taken.root, acceptance["evidence_reference"],
                acceptance["evidence_digest"])[0]
        _say(answer)
    return 0


VERBS = {"pending": _pending,
         "approve": lambda taken: _decide(taken, "approved"),
         "deny": lambda taken: _decide(taken, "denied"),
         "integrated": _integrated,
         "close": _close}


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    parser = argparse.ArgumentParser(
        prog="baton-v12-stack disposition",
        description="The owner's disposition: what is due, approve or deny the "
                    "exact reviewed candidate, record the human integration, "
                    "and close on the selected acceptance. Writes no "
                    "repository file and runs no Git command.")
    verbs = parser.add_subparsers(dest="verb", required=True)

    def store_operands(one):
        one.add_argument("--authority-store", required=True)
        one.add_argument("--authority-uuid", required=True)

    def acting(one):
        """The operands every durable act takes.

        `--participant` AND NO `--actor`. The session is minted for this
        participant and the authority takes the receipt's actor from that
        binding, so there is nothing for a caller to name. `--operation-id`
        makes the act replayable: the same identity with the same operands
        replays the committed answer, and with different operands it collides.
        """
        store_operands(one)
        one.add_argument("--participant", required=True)
        one.add_argument("--work", required=True)
        one.add_argument("--operation-id", required=True)

    pending = verbs.add_parser(
        "pending", help="what owner act is due on one Work")
    store_operands(pending)
    pending.add_argument("--work", required=True)
    pending.add_argument("--participant", default=None,
                         help="also report whether this participant holds the "
                              "capability each due act needs")
    pending.add_argument("--root", default=None,
                         help="also resolve the accepted integration record "
                              "under this root and report its state now")

    for name, what in (("approve", "approve the exact reviewed candidate"),
                       ("deny", "deny the exact reviewed candidate")):
        one = verbs.add_parser(name, help=what)
        acting(one)
        one.add_argument("--proposal", required=True)
        one.add_argument("--expect-candidate-digest", required=True)
        one.add_argument("--expect-review", required=True,
                         help="the accepted review receipt this decision was "
                              "taken on")
        one.add_argument("--policy-generation", required=True, type=int)
        one.add_argument("--approval-id", required=True)

    integrated = verbs.add_parser(
        "integrated", help="record the human integration of approved bytes")
    acting(integrated)
    integrated.add_argument("--proposal", required=True)
    integrated.add_argument("--expect-candidate-digest", required=True)
    integrated.add_argument("--root", required=True)
    integrated.add_argument("--reference", required=True,
                            help="the human integration record, relative to "
                                 "--root")
    integrated.add_argument("--commit", required=True,
                            help="the commit the record must name")
    integrated.add_argument("--integration-id", required=True)
    integrated.add_argument("--evidence-operation-id", required=True,
                            help="the citation is its own replayable act")

    closing = verbs.add_parser(
        "close", help="close on the selected acceptance")
    acting(closing)
    closing.add_argument("--outcome", required=True)
    closing.add_argument("--rationale", required=True)
    closing.add_argument("--proposal", default=None)
    closing.add_argument("--expect-candidate-digest", default=None)
    closing.add_argument("--root", default=None)
    closing.add_argument("--expect-assignment", default=None,
                         help="a JSON document holding the exact assignment "
                              "identity this close ends, when one is live")

    taken = parser.parse_args(argv)
    from baton_v12.authority.errors import Refusal

    try:
        return VERBS[taken.verb](taken)
    except Refusal as refusal:
        # THE AUTHORITY'S OWN SENTENCE, not a traceback. Every refusal this
        # command can reach is a contract answer an operator is meant to read.
        return _refused(str(refusal))
    except OSError as failure:
        return _refused(f"{type(failure).__name__}: {failure}")


if __name__ == "__main__":                                  # pragma: no cover
    raise SystemExit(main())
