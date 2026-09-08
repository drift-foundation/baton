"""The durable identity shapes of `SPEC.md` §4, and the canonical form every
operation signature is compared in.

Two rules from the contract are enforced HERE rather than at each call site,
because §4 says an identity is never a substitute for the operands and §7 says
every durable operand rides the replay signature:

 1. An `assignment_ref` is exactly (authority UUID, full Work id, participant,
    generation) -- never a participant alone, never a local selector.
    `assignment_key` refuses anything else, so a caller cannot accidentally
    compare three quarters of an identity.
 2. A signature is a CANONICAL serialization of every effective operand
    including the prose.  Sorting keys is what makes `{a, b}` and `{b, a}` one
    signature rather than two, and including reasons and rationales is what
    makes reusing one operation id with different durable text a refusal
    instead of a silent replay of somebody else's result.

THE SHAPES ARE SNAKE_CASE, NOT THE NODE HOST'S CAMEL CASE.  W2845's boundary
pins the frozen conceptual identities -- `work_ref {authority_uuid, work_id}`
and `assignment_ref {work_ref, participant, generation}` -- and the Node
implementation's member spelling is an implementation detail of that host, not
the contract.  This is a port by obligation, not a transliteration.
"""

import json
import re

from .errors import Refusal, label_of, name_of, type_name_of

__all__ = [
    "V11", "V12", "ABSENT",
    "GATE_QUIESCENCE", "GATE_CONTRACT_RUNTIME", "GATE_PLAN_REVISION",
    "MAX_DEPTH", "MAX_MEMBERS", "MAX_SAFE_INTEGER",
    "own", "signature_of", "claim_signature",
    "work_ref", "assignment_ref", "assignment_key", "normalize_assignment",
    "same_assignment", "is_v12_contract",
    "check_authority_uuid", "check_work_id", "check_participant",
    "check_generation", "check_text", "check_timestamp",
    "check_opaque_id", "opaque_id_fault",
    "gate_token", "parse_gate",
]

V11 = "v11"
V12 = "v12-assignment-1"


class _Absent:
    """The MISSING operand, which is not the null one.

    JSON has one hole and callers have two: "I did not pass a gate" and "I
    passed no gate" are different intentions and must not share a signature.
    The Node host spelled this with `undefined`; Python has no second hole, so
    the distinction is carried by this one module-private sentinel and tagged
    explicitly in the canonical form.
    """

    __slots__ = ()

    def __repr__(self):
        return "ABSENT"


ABSENT = _Absent()

# Bounds on what may cross the boundary as one operand.  Depth is the frozen
# host's; members is stated here because "excessive members" needs a number
# somebody can test rather than a word somebody can argue with.
MAX_DEPTH = 8
MAX_MEMBERS = 512

# JSON's interoperable integer range, and the range every consumer of these
# documents can read back without loss.  The frozen host expressed it as
# `Number.isSafeInteger`; Python's ints are unbounded, so the bound has to be
# applied deliberately or a durable operand becomes unreadable elsewhere.
MAX_SAFE_INTEGER = 2 ** 53 - 1

# §4's identity grammars, as the frozen contract states them.
_AUTHORITY_UUID = re.compile(r"\A[0-9a-f]{32}\Z")
_WORK_ID = re.compile(r"\A[0-9a-f]{8}-W[1-9][0-9]*\Z")
_PARTICIPANT = re.compile(r"\A[a-z][a-z0-9_-]*\.[a-z][a-z0-9_-]*\Z")
# The frozen `$defs.timestamp` grammar.  A durable instant is TEXT in exactly
# this shape; "UTC text" without the shape is just a string, and a clock that
# answered one would put it in every row it touched.
_TIMESTAMP = re.compile(
    r"\A[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]{3}Z\Z")


def _well_formed_text(value):
    """Whether this `str` is text that can survive a round trip.

    A Python `str` may hold lone surrogates, which are not encodable and are
    not JSON.  Detecting them by attempting the encode runs no caller code:
    `value` is already known to be an exact `str`.
    """
    try:
        value.encode("utf-8")
    except UnicodeEncodeError:
        return False
    return True


def own(value, *, what="operand", _depth=0):
    """Take ONE snapshot of a caller-owned operand and never look at the
    original again.

    This is the Python translation of the reviewed snapshot correction, ported
    by its OBLIGATION rather than by its mechanics.  The Node host's defect was
    that a session validated `operands.expect.participant` and then handed the
    SAME object to the core, which read it again -- a getter that answered one
    participant for the check and another for the execution passed the binding
    and then ended somebody else's live assignment.  Validating one view and
    executing another is the whole defect, and no amount of checking fixes it
    while the object can still change its answer.

    Python's version of that hazard is not `Proxy` and not getters.  It is
    `dict`/`list` SUBCLASSES, `__getitem__` overrides, arbitrary `Mapping`s and
    objects with `__eq__`/`__hash__`/`__iter__` of their own.  So the rule here
    is not "no proxies"; it is that a BEHAVIOUR-BEARING CONTAINER NEVER ENTERS
    THE AUTHORITY at all:

      * types are tested with `type(x) is T`, never `isinstance`, so a subclass
        is refused rather than admitted with its overrides intact;
      * only exact `dict`, `list`, `str`, `int`, `bool` and `None` are data;
      * every value is read exactly once, into a fresh built-in.

    The refusal names the value's TYPE, never its `repr` -- a refusal must not
    run the value it is refusing, and `__repr__` is the caller's code.
    """
    # The LABEL is caller text at every exported helper, so it is
    # bound by the rule here, once, where it is accepted.
    what = label_of(what)
    if _depth > MAX_DEPTH:
        raise Refusal(
            f"{what} is nested deeper than {MAX_DEPTH} levels; a durable "
            f"operand is a document, not a graph")
    kind = type(value)
    # `bool` before `int`, because `bool` IS an `int` in Python and the two are
    # different operands everywhere this contract cares.
    if value is None or kind is bool:
        return value
    if kind is int:
        if not -MAX_SAFE_INTEGER <= value <= MAX_SAFE_INTEGER:
            raise Refusal(
                f"{what} carries an integer outside the interoperable range; a "
                f"durable operand every consumer can read back is bounded by "
                f"±{MAX_SAFE_INTEGER}")
        return value
    if kind is str:
        if not _well_formed_text(value):
            raise Refusal(
                f"{what} carries text that is not encodable; a durable operand "
                f"round-trips or it is not one")
        return value
    if kind is list:
        if len(value) > MAX_MEMBERS:
            raise Refusal(
                f"{what} carries more than {MAX_MEMBERS} members")
        return [own(entry, what=what, _depth=_depth + 1) for entry in value]
    if kind is dict:
        if len(value) > MAX_MEMBERS:
            raise Refusal(
                f"{what} carries more than {MAX_MEMBERS} members")
        taken = {}
        # `dict.items` on an EXACT dict runs no caller code.  Keys are read as
        # they are; a non-string key is refused rather than coerced, because
        # coercing it would invent a member the caller did not send.
        for key, member in value.items():
            if type(key) is not str:
                raise Refusal(
                    f"{what} carries a {type_name_of(key)} key; a document's "
                    f"members are named by text")
            if not _well_formed_text(key):
                raise Refusal(f"{what} carries a member name that is not encodable")
            taken[key] = own(member, what=what, _depth=_depth + 1)
        return taken
    raise Refusal(
        f"{what} carries {name_of(value)}, which is not JSON data; the "
        f"authority takes exact built-in documents and nothing that carries "
        f"behaviour of its own")


def _canonical(value):
    if value is ABSENT:
        return {"$absent": True}
    if type(value) is dict:
        # NOT sorted here.  `signature_of` serializes with `sort_keys=True`,
        # which is the mechanism that actually decides the output, and a second
        # sort in front of it is a guard nothing can observe -- measured:
        # removing it failed no case.  One mechanism, and it is the one the
        # bytes come out of.
        return {key: _canonical(member) for key, member in value.items()}
    if type(value) is list:
        return [_canonical(entry) for entry in value]
    return value


def signature_of(kind, operands):
    """The stable text an operation's operands are compared as.

    Sorted keys, no insignificant whitespace, no NaN or Infinity, and the
    absent operand spelled out.  `ensure_ascii=False` keeps the text the
    caller's text rather than an escaped rendering of it; `own` has already
    proved it is encodable.
    """
    return json.dumps(
        _canonical({"kind": kind, "operands": operands}),
        sort_keys=True, separators=(",", ":"), ensure_ascii=False,
        allow_nan=False)


def claim_signature(work_id, participant):
    """THE authority-owned claim signature, exported for the Worker Manager.

    W4 persists this and must not recreate its encoding.  A manager that
    reimplemented the format would be a second authority on the question of
    whether two claims are the same claim, and the first time the two spellings
    disagreed only one of them would be authoritative -- and it would not be
    the one doing the comparing.
    """
    check_work_id(work_id)
    check_participant(participant)
    return signature_of("claim", {"work_id": work_id, "participant": participant})


def check_authority_uuid(value, *, what="authority_uuid"):
    # The LABEL is caller text at every exported helper, so it is
    # bound by the rule here, once, where it is accepted.
    what = label_of(what)
    if type(value) is not str or _AUTHORITY_UUID.match(value) is None:
        raise Refusal(
            f"{what} is {name_of(value)}; an authority UUID is 32 lowercase "
            f"hexadecimal characters")
    return value


def check_work_id(value, *, what="work_id"):
    # The LABEL is caller text at every exported helper, so it is
    # bound by the rule here, once, where it is accepted.
    what = label_of(what)
    if type(value) is not str or _WORK_ID.match(value) is None:
        raise Refusal(
            f"{what} is {name_of(value)}; a Work id is the full canonical "
            f"<8 hex>-W<positive> identity and a local selector is not one")
    return value


def check_participant(value, *, what="participant"):
    # The LABEL is caller text at every exported helper, so it is
    # bound by the rule here, once, where it is accepted.
    what = label_of(what)
    if type(value) is not str or _PARTICIPANT.match(value) is None:
        raise Refusal(
            f"{what} is {name_of(value)}; a participant is team.member")
    return value


def check_generation(value, *, what="generation", allow_null=True):
    # The LABEL is caller text at every exported helper, so it is
    # bound by the rule here, once, where it is accepted.
    what = label_of(what)
    if value is None:
        if allow_null:
            return None
        raise Refusal(f"{what} is none and this identity mints a generation")
    # `bool` first: `True` is an `int` and is not a generation.
    if type(value) is bool or type(value) is not int:
        raise Refusal(f"{what} is {name_of(value)}; a generation is a positive integer")
    if value < 1 or value > MAX_SAFE_INTEGER:
        # Review [P1]: this interpolated the rejected integer, and Python 3.13
        # refuses to render one above 4,300 digits -- so a 5,001-digit
        # generation left this boundary as a raw `ValueError` from the MESSAGE
        # rather than as the Refusal the check had already decided on.  The
        # value is named by the rule it violated, through the one helper that
        # knows how to name a value without rendering it.
        raise Refusal(
            f"{what} is {name_of(value)}; a generation is positive and within "
            f"the interoperable integer range (±{MAX_SAFE_INTEGER})")
    return value


# The frozen `opaqueId` grammar, reused for every opaque identity this authority
# takes.  Stated here rather than in each caller, so a second boundary cannot
# come to a different conclusion about the same string.
_OPAQUE_ID_LIMIT = 160
_OPAQUE_ID = re.compile(r"\A[A-Za-z0-9][A-Za-z0-9._:-]*\Z")


def check_opaque_id(value, what):
    """THE one opaque-identity check, for every path that takes one.

    Review [P1]: I put the rule in one place and then called it from ONE SITE.
    `Store.replay` enforced it; settlement and both journal reads used the
    weaker text check -- so a one-million-character id was still accepted as a
    durable primary key, and worse, settlement could RECORD an invalid identity
    as retired while a claim under the same id rejected its shape before ever
    seeing the retirement.  Two authority paths then disagreed about whether a
    durable identity existed, and the bound retirement reason was never
    replayed.

    Stating a rule in one place is not applying it in one place.  This function
    exists so the four paths cannot answer differently about the same string.
    """
    # The LABEL is caller text at every exported helper, so it is
    # bound by the rule here, once, where it is accepted.
    what = label_of(what)
    fault = opaque_id_fault(value)
    if fault is not None:
        raise Refusal(f"{what} {fault}")
    return value


def opaque_id_fault(value):
    """Why `value` is not a frozen opaque id, or `None`.

    Length BEFORE the pattern: cheaper, and it is the same
    shape-before-membership discipline used everywhere else here.
    """
    if type(value) is not str:
        return f"is {name_of(value)}"
    if value == "":
        return "is empty"
    if len(value) > _OPAQUE_ID_LIMIT:
        return (f"is longer than the frozen limit of {_OPAQUE_ID_LIMIT} "
                f"characters")
    if _OPAQUE_ID.match(value) is None:
        return f"is {name_of(value)}, which is not the frozen opaque grammar"
    return None


def check_text(value, what, *, optional=False):
    """ONE text rule for every durable scalar operand.

    Review [P1]: cut 2 had a local `_text` that required exact nonempty `str`
    and stopped there, so a LONE SURROGATE reached SQLite and escaped as
    `UnicodeEncodeError` -- from `create_work`'s route, from an ending's prose,
    from a plan digest, and out of `gate_token` as an invalid durable token.
    `own` already enforced this for documents; the scalars had their own,
    weaker rule beside it.

    A rule that exists twice is a rule that holds in one of the two places.  So
    there is one, here, next to the other identity grammars, and every cut-2
    text operand uses it -- optional prose included, because prose is durable
    too.
    """
    # The LABEL is caller text at every exported helper, so it is
    # bound by the rule here, once, where it is accepted.
    what = label_of(what)
    if optional and value is None:
        return None
    if type(value) is not str or value == "":
        raise Refusal(f"{what} is nonempty text; this is {name_of(value)}")
    if not _well_formed_text(value):
        raise Refusal(
            f"{what} carries text that is not encodable; a durable value "
            f"round-trips or it is not one")
    return value


def check_timestamp(value, *, what="a durable instant"):
    """The frozen `timestamp` grammar, enforced where the value enters.

    Found by probing my own cut 2: `_now` validated that the configured clock
    answered NONEMPTY TEXT, and a clock answering `banana` wrote `banana` into a
    durable `created_at`.  The boundary says timestamps cross as VALIDATED UTC
    text, and "validated" has to mean the shape or it means nothing.
    """
    # The LABEL is caller text at every exported helper, so it is
    # bound by the rule here, once, where it is accepted.
    what = label_of(what)
    if type(value) is not str or _TIMESTAMP.match(value) is None:
        raise Refusal(
            f"{what} is {name_of(value)}; a durable instant is UTC text in the "
            f"form 0000-00-00T00:00:00.000Z")
    return value


def work_ref(authority_uuid, work_id):
    """One Work's authoritative identity, as owned built-in data."""
    return {
        "authority_uuid": check_authority_uuid(authority_uuid),
        "work_id": check_work_id(work_id),
    }


def assignment_ref(authority_uuid, work_id, participant, generation):
    """The full four-part assignment identity, as owned built-in data.

    A v11 assignment carries no live generation, so `generation` may be `None`.
    A v12 worker-control assignment document always carries one and never
    serializes a null: that rule belongs to the document, and this shape is the
    in-process identity the document is built from.
    """
    return {
        "work_ref": work_ref(authority_uuid, work_id),
        "participant": check_participant(participant),
        "generation": check_generation(generation),
    }


def assignment_key(assignment, *, what="assignment"):
    """The comparable form of one assignment identity.

    A missing field is refused rather than defaulted.  §8 exists because
    participant equality is insufficient -- the same participant may release
    generation 7 and immediately claim generation 8 -- so an identity that
    silently completed itself from current state would defeat the one check the
    contract is built on.
    """
    # The LABEL is caller text at every exported helper, so it is
    # bound by the rule here, once, where it is accepted.
    what = label_of(what)
    if assignment is None:
        return None
    if type(assignment) is not dict:
        raise Refusal(
            f"{what} is {name_of(assignment)}; an assignment identity is a "
            f"document")
    if set(assignment) != {"work_ref", "participant", "generation"}:
        raise Refusal(
            f"{what} must be the full four-part identity (authority UUID, Work "
            f"id, participant, generation); a participant alone is not an "
            f"assignment")
    reference = assignment["work_ref"]
    if type(reference) is not dict or set(reference) != {"authority_uuid", "work_id"}:
        raise Refusal(
            f"{what} must carry the full work_ref (authority UUID and Work id)")
    check_authority_uuid(reference["authority_uuid"], what=f"{what}.authority_uuid")
    check_work_id(reference["work_id"], what=f"{what}.work_id")
    check_participant(assignment["participant"], what=f"{what}.participant")
    check_generation(assignment["generation"], what=f"{what}.generation")
    return json.dumps(
        [reference["authority_uuid"], reference["work_id"],
         assignment["participant"], assignment["generation"]],
        separators=(",", ":"), ensure_ascii=False)


def normalize_assignment(value, *, what="assignment"):
    """The owned snapshot of one assignment identity, validated as the full
    four-part shape.

    `None` passes through, so a caller that legitimately has no assignment -- an
    unclaimed close, an unclaimed gate arrival -- is not forced to invent one.
    The snapshot happens BEFORE the validation, which is the whole point: what
    is validated and what is later used are the same owned bytes.
    """
    # The LABEL is caller text at every exported helper, so it is
    # bound by the rule here, once, where it is accepted.
    what = label_of(what)
    if value is None:
        return None
    taken = own(value, what=what)
    assignment_key(taken, what=what)
    return taken


def same_assignment(left, right):
    """Whether these are the same assignment identity.

    Review [P1]: this short-circuited on `None` BEFORE validating anything, so
    an exported boundary helper answered a question about an operand it had
    never proved -- and with two non-null operands it compared caller data
    directly.  An exported helper is a boundary, and a boundary that only
    sometimes validates is one that sometimes does not.

    Both sides are taken as owned snapshots and proved as full four-part
    identities first.  `None` is still a legitimate answer -- an unclaimed close
    has no assignment -- but it is now the validated absence rather than an
    unexamined one.
    """
    left = normalize_assignment(left, what="left assignment")
    right = normalize_assignment(right, what="right assignment")
    if left is None or right is None:
        return left is right
    return assignment_key(left) == assignment_key(right)


def is_v12_contract(contract):
    """Whether this contract is a v12 one.

    Review [P1]: `contract != V11` invokes the CALLER'S `__ne__`, so an
    exported helper ran caller code and let an arbitrary exception escape as
    the answer.  Comparing is not inert when the thing being compared chose how
    comparison works.  The operand is proved to be exact text first, after
    which the comparison runs nothing.
    """
    if type(contract) is not str:
        raise Refusal(
            f"a contract is text; this is {name_of(contract)}")
    return contract != V11


# Gate tokens are TYPED (§4).  The type is what a satisfier checks, so it is
# parsed here once rather than by string-matching at three call sites.
GATE_QUIESCENCE = "runtime-quiescence"
GATE_CONTRACT_RUNTIME = "contract-runtime"
GATE_PLAN_REVISION = "plan-revision"


def gate_token(kind, detail):
    """Build one typed gate token.

    Review [P1]: the f-string invoked the caller's `__format__`, so an exported
    helper ran caller code while assembling a value that becomes DURABLE.  Both
    halves are proved to be exact text first; interpolating a `str` runs
    nothing and cannot fail.

    The kind may not contain the separator, because the token is parsed by its
    FIRST colon: a kind carrying one would parse back as a different kind with
    the rest of itself in the detail, and a token that does not round-trip is
    not an identity.
    """
    check_text(kind, "a gate kind")
    # Review [P1]: the detail was allowed to be any `str`, so a lone surrogate
    # produced a token that is not encodable -- and a gate token is DURABLE and
    # is compared for equality later.  Both halves go through the one text rule.
    check_text(detail, "a gate detail")
    if ":" in kind:
        raise Refusal(
            "a gate kind may not contain the separator; the token is parsed at "
            "its first colon and one that does not round-trip is not an "
            "identity")
    return f"{kind}:{detail}"


def parse_gate(gate):
    if type(gate) is not str:
        return None
    at = gate.find(":")
    if at < 1:
        return None
    return {"kind": gate[:at], "detail": gate[at + 1:]}
