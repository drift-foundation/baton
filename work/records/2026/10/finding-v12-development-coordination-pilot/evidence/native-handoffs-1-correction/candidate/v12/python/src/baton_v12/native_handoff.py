"""THE NATIVE HANDOFF DOCUMENT: one closed, bounded, versioned contract.

W385331, first vertical native communication slice. The reviewer planning
disposition is `work/records/2026/11/
finding-v12-native-agent-handoffs-discovery/FIRST-NATIVE-SLICE.md`.

WHAT THIS IS. The bounded document a worker returns on its own declared output
to say which of four things its invocation was: a FINAL SUBMISSION, a
CLARIFICATION REQUEST, a within-scope FINDING REQUEST, or a RESPONSE to one of
the two requests. It is pure data with a canonical digest, and this module is
the only reader of its shape.

WHAT IT IS NOT, and every boundary here is load-bearing rather than decorative:

  * NOT AN AUTHORITY. Nothing here decides whether a request may be sent, who
    may answer it, whether a checkpoint exists or whether a continuation is
    allowed. A worker fills this in about itself; `authority.messages` binds
    the durable record to the assignment, and `job_manager.native_handoffs`
    decides what the host does about it. A worker-supplied author identity
    cannot substitute for assignment attribution, so there is no author member
    to supply.
  * NOT AN APPROVAL. A `response` carries an interpretation of accepted scope
    or a classification of a finding. It is NOT an `accepted` technical review,
    it mints no verification/review/approval/integration receipt, and the
    vocabulary below has no word for one.
  * NOT A FRAMEWORK. Every object is CLOSED, every list is bounded, and the
    version is in the schema name -- a second disposition, another evidence
    shape or a wider body is a NEW revision rather than a member somebody
    fills in.
  * NOT A STORE OR A PROVIDER. No import from `worker_manager`, `job_manager`,
    `authority` or `v12/worker` is reachable from here, and nothing opens a
    file, a connection or a socket.

THE FOUR KINDS ARE DISCRIMINATED AND THEIR MEMBER SETS DO NOT OVERLAP BY
ACCIDENT. `own` takes one snapshot, `_exactly` closes each object, and the
member set is selected BY KIND -- so a document that carries a final
submission's members and a request's escalation is refused as the mixture it
is rather than read for whichever half a consumer looked at first. The slice's
rule is that undeclared, mixed, missing or foreign output HOLDS; this module is
where mixed and foreign are decided.
"""

import json

from .contracts import ContractRefusal, canonical_bytes, digest, own
from .contracts.errors import name_value

__all__ = ["HANDOFF_SCHEMA", "HANDOFF_KINDS", "REQUEST_KINDS", "FINAL_KIND",
           "CLARIFICATION_KIND", "FINDING_KIND", "RESPONSE_KIND",
           "DISPOSITIONS", "ANSWER_DISPOSITION", "ESCALATE_DISPOSITION",
           "COMMON_MEMBERS", "FINAL_MEMBERS", "REQUEST_MEMBERS",
           "RESPONSE_MEMBERS", "REFERENCE_MEMBERS", "EVIDENCE_MEMBERS",
           "ESCALATION_MEMBERS", "MAX_HANDOFF_BYTES", "MAX_BODY",
           "MAX_EVIDENCE", "MAX_OPTIONS", "MAX_REFERENCE", "MAX_RATIONALE",
           "check_handoff", "handoff_digest", "handoff_of_bytes",
           "is_request", "is_response", "is_final"]

# -- the closed vocabulary ----------------------------------------------------

HANDOFF_SCHEMA = "baton.native-handoff/1"

# THE FOUR THINGS ONE INVOCATION CAN HAVE BEEN. `final-submission` is the
# ordinary ending every existing consumer already handles; the other three are
# this slice's.
FINAL_KIND = "final-submission"
CLARIFICATION_KIND = "clarification-request"
FINDING_KIND = "finding-request"
RESPONSE_KIND = "response"
HANDOFF_KINDS = (FINAL_KIND, CLARIFICATION_KIND, FINDING_KIND, RESPONSE_KIND)
# The two that YIELD, named as a set because every host branch asks exactly
# this question and a membership test spelled twice is two tests that can
# disagree.
REQUEST_KINDS = (CLARIFICATION_KIND, FINDING_KIND)

# WHAT A RESPONSE CAN DO, and there are two answers rather than three. A
# reviewer either resolves the question inside accepted scope or records ONE
# explicit escalation; "reject", "approve" and "accept" are deliberately absent
# because a text message never transfers ownership or approves code.
ANSWER_DISPOSITION = "answer"
ESCALATE_DISPOSITION = "escalate"
DISPOSITIONS = (ANSWER_DISPOSITION, ESCALATE_DISPOSITION)

# -- the bounds ---------------------------------------------------------------
#
# EVERY ONE IS AN EXACT CEILING AND NOT A SUGGESTION, for `role_contract`'s
# reason: a document wider than this is one no supported carrier will hold, and
# a limit that is decidable here and not decided here is a limit nobody
# enforces. The DEPTH bound is `contracts.canonical.MAX_DEPTH` and is enforced
# by `own` rather than restated as a second number.
MAX_HANDOFF_BYTES = 16384
MAX_BODY = 4096
MAX_RATIONALE = 2048
MAX_REFERENCE = 512
MAX_EVIDENCE = 16
MAX_OPTIONS = 8
MAX_PARTICIPANT = 160

# -- the member sets ----------------------------------------------------------
#
# CLOSED PER KIND. `COMMON_MEMBERS` is what every kind carries; the rest is
# selected by the kind and nothing else, so a request's members on a final
# submission are UNEXPECTED rather than ignored.
COMMON_MEMBERS = ("schema", "kind")

# A FINAL SUBMISSION SAYS ONLY THAT IT IS ONE. The candidate, its transport and
# its recap are the existing `baton.git-proposal/1` claim's and are not
# restated here: two accounts of one candidate are two things that can
# disagree, and the publication boundary already owns the first.
FINAL_MEMBERS = COMMON_MEMBERS

# A REQUEST carries exactly what the planning disposition names: kind, body,
# accepted-scope question/finding evidence, exact continuation, checkpoint
# reference and permitted recipient.
REQUEST_MEMBERS = COMMON_MEMBERS + ("body", "evidence", "continuation",
                                    "checkpoint", "recipient")

# A RESPONSE carries the request identity/digest, the answer-or-escalate
# disposition, rationale/evidence and, for an escalation only, the
# ambiguity/options/recommendation.
RESPONSE_MEMBERS = COMMON_MEMBERS + ("request", "disposition", "body",
                                     "rationale", "evidence", "checkpoint",
                                     "escalation")

# ONE SHAPE FOR EVERY DIGESTED REFERENCE, used by `checkpoint`, `continuation`
# and `request` alike. A reference without a digest can only establish that
# something has that name, which is the gap `work_dossier_evidence` names one
# package over.
REFERENCE_MEMBERS = ("reference", "digest")
EVIDENCE_MEMBERS = ("reference", "digest", "note")
ESCALATION_MEMBERS = ("ambiguity", "options", "recommendation")

_MEMBERS = {FINAL_KIND: FINAL_MEMBERS,
            CLARIFICATION_KIND: REQUEST_MEMBERS,
            FINDING_KIND: REQUEST_MEMBERS,
            RESPONSE_KIND: RESPONSE_MEMBERS}

_DIGEST_PREFIX = "sha256:"
_DIGEST_LENGTH = len(_DIGEST_PREFIX) + 64


def _refuse(message):
    raise ContractRefusal("integrity", "schema", message)


def _denied(message):
    raise ContractRefusal("policy", "denied", message)


def _exactly(value, members, what):
    """One closed object: these members, in this document, and nothing else.

    BOTH HALVES ARE NAMED, which is `templates._exactly`'s rule and
    `role_contract._exactly`'s after it: a MISSING member is a declaration
    whose rule nobody stated, and an EXTRA one is a rule somebody believes
    applies.
    """
    if type(value) is not dict:
        _refuse(f"{what} is one closed object; this is {name_value(value)}")
    missing = [one for one in members if one not in value]
    extra = sorted(one for one in value if one not in members)
    if missing or extra:
        _refuse(f"{what} is exactly {', '.join(members)}"
                + (f"; missing {', '.join(missing)}" if missing else "")
                + (f"; unexpected {', '.join(extra)}" if extra else ""))
    return value


def _bounded(value, limit, what, *, empty=False):
    if type(value) is not str:
        _refuse(f"{what} is text; this is {name_value(value)}")
    if not empty and not value:
        _refuse(f"{what} is not empty")
    if len(value) > limit:
        _refuse(f"{what} is at most {limit} characters and this is "
                f"{len(value)}")
    return value


def _digest(value, what):
    """One canonical SHA-256 digest in this distribution's own spelling."""
    _bounded(value, _DIGEST_LENGTH, what)
    if not value.startswith(_DIGEST_PREFIX) or len(value) != _DIGEST_LENGTH \
            or any(one not in "0123456789abcdef"
                   for one in value[len(_DIGEST_PREFIX):]):
        _refuse(f"{what} is a {_DIGEST_PREFIX} digest of 64 lowercase hex "
                f"characters; this is {name_value(value)}")
    return value


def _reference(value, what, *, members=REFERENCE_MEMBERS):
    taken = _exactly(value, members, what)
    _bounded(taken["reference"], MAX_REFERENCE, f"{what}'s reference")
    _digest(taken["digest"], f"{what}'s digest")
    if "note" in members:
        _bounded(taken["note"], MAX_BODY, f"{what}'s note", empty=True)
    return taken


def _evidence(value, what):
    """The accepted-scope evidence a request or a response cites.

    BOUNDED AND ORDERED AS GIVEN. A list rather than a set, because the order a
    worker cited its evidence in is part of the document the digest is over --
    and DUPLICATE references refuse, because two citations of one reference are
    not two pieces of evidence.
    """
    if type(value) is not list:
        _refuse(f"{what} is a list of cited evidence; this is "
                f"{name_value(value)}")
    if len(value) > MAX_EVIDENCE:
        _refuse(f"{what} cites at most {MAX_EVIDENCE} references and this "
                f"cites {len(value)}")
    seen = []
    for index, one in enumerate(value):
        taken = _reference(one, f"{what}'s evidence {index}",
                           members=EVIDENCE_MEMBERS)
        if taken["reference"] in seen:
            _refuse(f"{what} cites {name_value(taken['reference'])} twice; two "
                    f"citations of one reference are not two pieces of "
                    f"evidence")
        seen.append(taken["reference"])
    return value


def _participant(value, what):
    """One endpoint address, by its grammar and nothing else.

    WHETHER THAT ADDRESS MAY RECEIVE THIS REQUEST IS NOT DECIDED HERE and
    cannot be: the configured allowed destinations are the deployment's and the
    authority's. What this refuses is a recipient that is not an address at
    all.
    """
    _bounded(value, MAX_PARTICIPANT, what)
    if value.strip() != value or any(one.isspace() for one in value):
        _refuse(f"{what} is one endpoint address with no whitespace; this is "
                f"{name_value(value)}")
    return value


def _escalation(value, what):
    taken = _exactly(value, ESCALATION_MEMBERS, what)
    _bounded(taken["ambiguity"], MAX_BODY, f"{what}'s ambiguity")
    _bounded(taken["recommendation"], MAX_BODY, f"{what}'s recommendation")
    options = taken["options"]
    if type(options) is not list or not options:
        _refuse(f"{what} states a non-empty list of options; this is "
                f"{name_value(options)}")
    if len(options) > MAX_OPTIONS:
        _refuse(f"{what} states at most {MAX_OPTIONS} options and this states "
                f"{len(options)}")
    for index, one in enumerate(options):
        _bounded(one, MAX_BODY, f"{what}'s option {index}")
    if len(set(options)) != len(options):
        _refuse(f"{what} states one option twice; a duplicate option is not a "
                f"choice")
    return taken


def check_handoff(document, *, what="a native handoff"):
    """The pure closed validator. Answers the owned document or refuses.

    `own` FIRST, because every later comparison depends on the value space: it
    takes a fresh snapshot, refuses floats, non-built-in objects and anything
    nesting past the frozen depth, and keeps booleans and integers from
    becoming each other.

    THE SCHEMA IS ASKED FIRST OF THE MEMBERS and the KIND SECOND, in that
    order, because a document from another generation is not one to read the
    recognised parts out of -- and a kind this build does not carry is a kind
    rather than whichever member happened to differ.
    """
    taken = own(document, what=what)
    if type(taken) is not dict:
        _refuse(f"{what} is one closed object; this is {name_value(document)}")
    if taken.get("schema") != HANDOFF_SCHEMA:
        _denied(f"{what} says it is {name_value(taken.get('schema'))} and this "
                f"build reads exactly {name_value(HANDOFF_SCHEMA)}; a handoff "
                f"from another revision is not one to read the recognised "
                f"parts out of")
    kind = taken.get("kind")
    if kind not in HANDOFF_KINDS:
        _denied(f"{what} declares kind {name_value(kind)} and the four this "
                f"build carries are {', '.join(HANDOFF_KINDS)}; an unknown "
                f"kind is held rather than read as the least alarming one")
    _exactly(taken, _MEMBERS[kind], f"{what} of kind {kind}")
    if kind == FINAL_KIND:
        # A FINAL SUBMISSION IS THE ABSENCE OF A REQUEST, and saying so is the
        # whole of its contract. Everything a final submission is ABOUT is the
        # existing candidate claim's, whose owner is the publication boundary.
        return taken
    if kind in REQUEST_KINDS:
        _bounded(taken["body"], MAX_BODY, f"{what}'s body")
        _evidence(taken["evidence"], f"{what}")
        _reference(taken["continuation"], f"{what}'s continuation")
        _reference(taken["checkpoint"], f"{what}'s checkpoint")
        _participant(taken["recipient"], f"{what}'s permitted recipient")
        return taken
    _reference(taken["request"], f"{what}'s request")
    if taken["disposition"] not in DISPOSITIONS:
        _denied(f"{what} declares disposition "
                f"{name_value(taken['disposition'])}; a response either "
                f"{ANSWER_DISPOSITION}s within accepted scope or "
                f"{ESCALATE_DISPOSITION}s once, and there is no word here for "
                f"approving code")
    _bounded(taken["body"], MAX_BODY, f"{what}'s body")
    _bounded(taken["rationale"], MAX_RATIONALE, f"{what}'s rationale")
    _evidence(taken["evidence"], f"{what}")
    _reference(taken["checkpoint"], f"{what}'s checkpoint")
    if taken["disposition"] == ESCALATE_DISPOSITION:
        if taken["escalation"] is None:
            _refuse(f"{what} escalates and states no ambiguity, options or "
                    f"recommendation; an escalation that carries none is a "
                    f"refusal to answer wearing a disposition")
        _escalation(taken["escalation"], f"{what}'s escalation")
    elif taken["escalation"] is not None:
        _refuse(f"{what} answers within accepted scope and also carries an "
                f"escalation; one response decides once")
    return taken


def handoff_digest(document):
    """The canonical identity of one handoff, over the WHOLE object.

    NO EMBEDDED DIGEST MEMBER, which is `role_contract.contract_digest`'s rule
    and for its reason: whitespace in a file is not identity, and a document
    cannot carry a digest that disagrees with it because there is nowhere to
    put one.
    """
    return digest(own(document, what="a native handoff"))


def handoff_of_bytes(payload, *, what="a native handoff"):
    """One handoff read from BYTES, bounded, with duplicate keys refused.

    BOUNDED AT THE READ on the ENCODED size, and DUPLICATE KEYS REFUSED BEFORE
    CANONICALIZATION. `json.loads` keeps the last of two equal keys silently,
    so a document carrying `kind` twice has two readings -- the one a careless
    reader sees and the one the digest is taken over -- and two parties could
    then agree on a digest and disagree on the handoff.
    """
    if type(payload) is not bytes:
        _refuse(f"{what} is read from bytes; this is {name_value(payload)}")
    if len(payload) > MAX_HANDOFF_BYTES:
        _refuse(f"{what} is {len(payload)} encoded bytes and this contract "
                f"admits {MAX_HANDOFF_BYTES}")

    def _pairs(pairs):
        seen = {}
        for name, value in pairs:
            if name in seen:
                _refuse(f"{what} carries the member {name_value(name)} twice; "
                        f"a document with two readings has no identity, and "
                        f"the one a digest is taken over need not be the one a "
                        f"reader sees")
            seen[name] = value
        return seen

    try:
        document = json.loads(payload.decode("utf-8"), object_pairs_hook=_pairs)
    except UnicodeDecodeError:
        _refuse(f"{what} is UTF-8 text")
    except ValueError:
        _refuse(f"{what} is one readable JSON document")
    return check_handoff(document, what=what)


def is_request(document):
    """Whether this handoff YIELDS, asked of an already-validated document."""
    return document["kind"] in REQUEST_KINDS


def is_response(document):
    return document["kind"] == RESPONSE_KIND


def is_final(document):
    return document["kind"] == FINAL_KIND


# -- what this module is held to at import ------------------------------------
#
# ASSERTED RATHER THAN DESCRIBED, because each of these is a place where the
# member tables and the validator could drift apart silently and a comment
# would still read true.

assert set(_MEMBERS) == set(HANDOFF_KINDS)
assert set(REQUEST_KINDS) <= set(HANDOFF_KINDS)
assert FINAL_KIND not in REQUEST_KINDS and RESPONSE_KIND not in REQUEST_KINDS
# The three kinds that are not a final submission each carry MORE than it, so
# a final submission can never be read as one of them by member set alone.
assert all(set(FINAL_MEMBERS) < set(_MEMBERS[kind])
           for kind in HANDOFF_KINDS if kind != FINAL_KIND)
# A request and a response do not share a member set, which is what makes the
# discrimination by kind decidable rather than conventional.
assert set(REQUEST_MEMBERS) != set(RESPONSE_MEMBERS)
# And the smallest document this contract admits fits the ceiling it declares.
assert len(canonical_bytes({"schema": HANDOFF_SCHEMA, "kind": FINAL_KIND})) \
    <= MAX_HANDOFF_BYTES
