"""ONE owner for every operand rule this manager has.

W4, replacing three rounds of named-site patching. PLAN items 4bx and 4by: the
correction loop stopped because the same class kept surviving outside whatever
inventory I claimed, so the answer is not another site -- it is a layer that
NAMES ITS BOUNDARIES so an inventory can be derived from the code instead of
from my recollection.

NINE KINDS, and they are different properties rather than degrees of one:

  text        exact, non-empty, encodable. Keeps a value out of SQLite's way.
  identity    the same, for a value a durable ROW IS NAMED BY. Separate because
              a lookup by an identity that cannot exist is a different mistake
              from storing text that cannot be stored, and because naming the
              two apart is what makes the inventory legible.
  instant     text, the frozen grammar, AND A REAL CALENDAR INSTANT. Keeps a
              value out of a COMPARISON's way.
  deadline    an instant plus a duration, with both the duration and the SUM
              inside the domain this manager can express.
  injected    the answer of a capability trusted deployment supplied. Trusted to
              be the authority's; not trusted to be correct.
  document    an exact fresh dict with EXACTLY these members -- none missing and
              none extra, because a contract that names a subset of what it
              accepts is a floor rather than a contract.
  alternative one of a closed set of SHAPES. Closing the vocabulary alone tells
              you which alternative arrived and nothing about what it carries,
              so each variant brings its own member contract.
  adopted     persisted text decoded back into a value, refusing rather than
              faulting when this build cannot read what was written.
  row         one persisted SQL row, with its column SET and every column's
              value owned. The store is a receiving trust domain: this process
              did not write the bytes it is reading.

EVERY REFUSAL NAMES ITS BOUNDARY. `what` is not decoration here: it is how a
probe proves it reached the boundary it claims to test rather than being refused
earlier by something else. That is the vacuity the review found in my last
sweep, and the label is the mechanism that closes it.

WHY THE CALENDAR IS PART OF `instant` AND NOT OF `deadline`. Fixed-width digits
do not establish a calendar: `2026-99-99T99:99:99.999Z` matches the grammar,
escaped `strptime` as a raw `ValueError` on the arithmetic path, and on the
comparison-only path was never parsed at all -- it simply sorted after every real
deadline and silently expired a live offer. Comparison paths need the calendar
just as much as arithmetic ones, so the owner of the instant establishes it and
no caller has to remember which kind of path it is on.
"""

from datetime import datetime, timedelta, timezone
import json
import re

from ..contracts import ContractRefusal, check_no_durable_secret, own
from ..contracts.errors import is_closed_pair, name_value

__all__ = ["text", "identity", "instant", "deadline", "injected", "document",
           "alternative", "adopted", "row", "capability", "generation",
           "sealed",
           "Column", "KINDS", "GRAMMAR", "DOMAINS", "COLUMN_KINDS",
           "MAX_SAFE_INTEGER"]

KINDS = ("text", "identity", "instant", "deadline", "injected", "document",
         "alternative", "adopted", "row", "capability", "generation", "sealed")

# WHERE A VALUE CAME FROM, which is a different question from what shape it must
# have. PLAN 4bz names three receiving trust domains, and an entry is owned once
# as it crosses into this one.
#
#   caller    an operand a caller handed us
#   adopted   persistent data coming back out of our own store. Ours once; a
#             receiver input again the moment it is read, because the process
#             that wrote it is not this one and the bytes may not be either.
#   injected  the answer of a capability trusted deployment supplied.
DOMAINS = ("caller", "adopted", "injected")

# The frozen durable-instant grammar.
GRAMMAR = re.compile(r"\A[0-9]{4}-[0-9]{2}-[0-9]{2}"
                     r"T[0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]{3}Z\Z")

_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"


def _refuse(message):
    raise ContractRefusal("integrity", "schema", message)


def text(value, what):
    """Exact, non-empty, encodable text.

    Nothing here RUNS the value: `type(x) is str` and `len` touch no caller
    code, and encoding an exact `str` is a built-in conversion.
    """
    if type(value) is not str or value == "":
        _refuse(f"{what} is durable text; this is {name_value(value)}")
    try:
        value.encode("utf-8")
    except UnicodeEncodeError:
        _refuse(f"{what} carries text that is not encodable; a durable value "
                f"round-trips or it is not one")
    return value


def identity(value, what):
    """Text that a durable row is NAMED BY, on the way to or from SQL.

    The same rule as `text` today. It is a separate name because the inventory
    distinguishes what a row STORES from what a row is FOUND BY, and because a
    lookup for an identity that cannot exist should refuse rather than fault --
    which is a statement about reads, and `text` says nothing about reads.
    """
    return text(value, what)


def instant(value, what):
    """Text, the frozen grammar, and a REAL CALENDAR INSTANT.

    All three, because all three are needed by every path. The grammar makes
    lexicographic comparison correct; the calendar makes the value an instant at
    all. `2026-99-99T99:99:99.999Z` has the shape and is not a date, and on a
    comparison-only path it sorts after every real deadline.
    """
    _calendar(value, what)
    # THE TEXT BACK, not the parse. Everything downstream compares instants
    # lexicographically, and handing back a `datetime` would quietly make some
    # caller compare two different kinds of thing. The parse is how the calendar
    # is established, not what the caller asked for.
    return value


def _calendar(value, what):
    """Text, grammar and calendar. The parse, for the owner's own use."""
    text(value, what)
    if GRAMMAR.match(value) is None:
        _refuse(f"{what} is a durable instant in the frozen "
                f"0000-00-00T00:00:00.000Z grammar; this is {name_value(value)}")
    try:
        return datetime.strptime(value, _FORMAT).replace(tzinfo=timezone.utc)
    except ValueError:
        _refuse(f"{what} has the shape of an instant and is not one; "
                f"{name_value(value)} names no moment on any calendar")


def deadline(from_instant, seconds, what):
    """An instant plus a duration, with the DURATION and the SUM in the domain.

    Representability is a third property after "is an integer" and "is
    positive", and it belongs to the SUM: a small duration added to a late
    instant leaves the domain just as surely as a huge one added to an early
    one. The answer is returned as TEXT, because everything downstream compares
    it lexicographically.
    """
    # THE INSTANT IS ALREADY OWNED. PLAN 4bz: a value is owned as it crosses
    # into the receiving domain and is not revalidated afterwards -- every
    # caller here passes an instant this layer has already proved, so proving it
    # again was blanket revalidation of a trusted internal value. It was also
    # what made two "unreachable" entries in the old inventory: a boundary no
    # caller can drive is usually a boundary that should not be there.
    #
    # A parse that fails here would therefore be a DEFECT in the caller's
    # ownership rather than a refusal, and it is left to fault as one.
    parsed = datetime.strptime(from_instant, _FORMAT).replace(
        tzinfo=timezone.utc)
    if type(seconds) is not int or seconds <= 0:
        _refuse(f"{what} is a positive whole number of seconds after an "
                f"instant; the duration is {name_value(seconds)}")
    try:
        moved = parsed + timedelta(seconds=seconds)
    except (OverflowError, ValueError, OSError):
        _refuse(f"{what} would fall {name_value(seconds)} seconds after "
                f"{name_value(from_instant)}, which is outside the instants "
                f"this manager can express")
    answer = (moved.strftime("%Y-%m-%dT%H:%M:%S.")
              + f"{moved.microsecond // 1000:03d}Z")
    # The SUM is this layer's OWN output, and 4bz says an outbound value is the
    # next receiver's business rather than something to re-own here. `datetime`
    # cannot reach a year the grammar rejects, so the overflow refusal above is
    # what bounds it; re-proving the answer was the third of the double
    # validations the ruling names.
    return answer


def _members(taken, what, required, optional):
    """EXACTLY these members: none missing, and NONE EXTRA.

    Review [P1]: this checked only for missing members, so "exactly these
    members" was false of the function that said it -- a projection carrying an
    unexpected member was accepted and reached offer issuance. A contract that
    describes a subset of what it accepts is not a contract; it is a floor.

    An extra member is refused rather than ignored because the two readings of
    one are opposite. Either the sender is a build this one was not written
    against -- in which case the members we DO recognise may not mean what they
    did -- or the document is not the one we think it is. Ignoring it picks the
    happier reading silently, and the whole point of adopting a document is to
    stop doing that.
    """
    missing = [member for member in required if member not in taken]
    if missing:
        _refuse(f"{what} needs {', '.join(missing)}")
    allowed = frozenset(required) | frozenset(optional)
    extra = sorted(member for member in taken if member not in allowed)
    if extra:
        _refuse(f"{what} also carries {', '.join(extra)}, which this build's "
                f"contract for it does not name; an unrecognised member is "
                f"refused rather than ignored, because ignoring one silently "
                f"assumes the members we do recognise still mean what they did")


def document(value, what, required=(), optional=()):
    """An exact built-in document, owned, with EXACTLY these members.

    Review [P1]: `injected` was `text`, which can describe a signature string
    and nothing else -- so an integer `project_work` answer faulted at `.get`,
    an integer `claim` answer was PERSISTED as the assignment, and an integer
    `settle_operation` answer was silently treated as `live`. A capability's
    answer is a document, and a domain that cannot say "document" cannot own
    one.

    `own` is what makes it exact and fresh; the member contract is what makes it
    THIS document rather than any dict. `required` must be present; `optional`
    names the members this build knows about and does not read, which is how a
    contract stays closed without pretending the sender emits nothing else.
    """
    taken = own(value, what=what)
    if type(taken) is not dict:
        _refuse(f"{what} is one exact document; this is {name_value(value)}")
    if required or optional:
        _members(taken, what, required, optional)
    return taken


def alternative(value, what, variants, discriminator="kind"):
    """A document that must be ONE OF a closed set of shapes -- SHAPES, not
    names.

    A settlement answers `live`, `committed`, `retired` or `refused`, and the
    manager BRANCHES on which. An answer outside the set was silently treated as
    `live` -- the branch that writes nothing -- so an unrecognised answer became
    "the identity is still open", which is a claim about the authority nobody
    made.

    Review [P1]: closing only the VOCABULARY left every variant's shape open, so
    `{"kind": "committed"}` was a complete settlement -- and the offer durably
    advanced to `claimed` carrying a null assignment, which is the exact defect
    the `committed` branch exists to prevent. Knowing WHICH alternative arrived
    tells you nothing if you do not then know what it must carry.

    `variants` maps each kind to its own `(required, optional)` contract.
    """
    taken = own(value, what=what)
    if type(taken) is not dict:
        _refuse(f"{what} is one exact document; this is {name_value(value)}")
    if discriminator not in taken:
        _refuse(f"{what} needs {discriminator}")
    named = taken[discriminator]
    if named not in variants:
        _refuse(f"{what} answers {name_value(named)}, which is not one of "
                f"{', '.join(variants)}; an unrecognised answer is refused "
                f"rather than read as the least alarming one")
    required, optional = variants[named]
    _members(taken, f"{what}'s {named} answer",
             (discriminator,) + tuple(required), tuple(optional))
    return taken


class Column:
    """One persisted column's contract: its kind, and whether it may be absent.

    `allowed`, when given, is the closed vocabulary the column's own CHECK
    constraint states. It is repeated here rather than trusted because the CHECK
    binds what THIS build writes, and an adopted row is by definition one some
    other process wrote.
    """

    __slots__ = ("kind", "nullable", "allowed", "members")

    def __init__(self, kind, *, nullable=False, allowed=None, members=None):
        if kind not in COLUMN_KINDS:
            raise ContractRefusal(
                "integrity", "schema",
                f"a column contract names kind {name_value(kind)}, which is "
                f"not one of {', '.join(COLUMN_KINDS)}")
        self.kind = kind
        self.nullable = nullable
        self.allowed = allowed
        # A `json` column may name the members it must decode TO. The decode and
        # the member set are two properties of one crossing, and proving them
        # together at the read is what lets the consumer treat the value as
        # owned instead of adopting it a second time.
        self.members = members


def _flag(value, what):
    """SQLite has no boolean, so a flag column is 0 or 1 and nothing else."""
    if type(value) is not int or value not in (0, 1):
        _refuse(f"{what} is a persisted flag, which is 0 or 1; this is "
                f"{name_value(value)}")
    return value


def _count(value, what):
    if type(value) is not int:
        _refuse(f"{what} is a persisted whole number; this is "
                f"{name_value(value)}")
    return value



def _persisted_json(value, what):
    """Persisted text that DECODES, returned as the text it was.

    The same shape as `instant`: three properties are proved and the caller gets
    back what it stored. A column holding a journalled result is text on the way
    through SQLite and a value to whoever replays it, and proving the decode
    where the row is read is what stops a malformed one reaching the replay --
    the one function whose whole job is handing a retry the first answer.

    The TEXT comes back rather than the value because replay is BYTE-STABLE:
    the stored bytes are what an exact retry reproduces, not a re-encoding of
    something this build parsed and re-emitted.
    """
    text(value, what)
    try:
        json.loads(value)
    except ValueError:
        _refuse(f"{what} is persisted text this build cannot decode; a durable "
                f"value round-trips or it is not one")
    return value


def sealed(value, what):
    """ONE semantic owner for a sealed refusal, whichever domain it came from.

    Review [P1], twice over. The member set was checked and the members' meaning
    was not, so a persisted refusal whose category was the integer 7 passed --
    and `ContractRefusal`, whose closed-pairing check is an ASSERTION about this
    build's own raising sites, turned the disagreement into an AssertionError
    for a caller replaying its first answer.

    And when the adopted half was corrected the PUBLIC half was not: the same
    document arriving from a caller still had only its four names checked. Two
    doors into one document, and I fitted a lock to one of them. So there is one
    owner and both call it.

    What makes a seal a seal is the CLOSED PAIRING. §9 says a category and a
    code mean something together: `refused.precondition` and `policy.retention`
    carry different portable meanings and different retry policies, so a pair
    this build cannot place is not one of its refusals however well-formed its
    parts. The pairing is answered by the contracts layer's own authority rather
    than by the readable vocabulary a consumer maps onto the wire -- that
    vocabulary is mutable, and a boundary closed against a value callers can
    widen is not closed.
    """
    record = document(value, what,
                      required=("category", "code", "message", "durable"))
    # TYPED BEFORE ANYTHING IS PLACED. `is_closed_pair` establishes both types
    # before it hashes either, because `x in mapping` on a list raises rather
    # than answering -- and a check that assumes the type it is checking is not
    # owning the field.
    if not is_closed_pair(record["category"], record["code"]):
        _refuse(f"{what} pairs {name_value(record['category'])} with "
                f"{name_value(record['code'])}; §9's pairing is closed, and a "
                f"pair this build cannot place is not one of its refusals")
    text(record["message"], f"{what}'s message")
    if record["durable"] is not True:
        _refuse(f"{what} is marked durable {name_value(record['durable'])}; a "
                f"sealed refusal is the outcome of a decision that already "
                f"wrote something, and only a durable one is ever sealed")
    return record


def _sealed_refusal(value, what):
    """A persisted column holding one. The TEXT comes back: replay is
    byte-stable."""
    _persisted_json(value, what)
    sealed(json.loads(value), what)
    return value


COLUMN_KINDS = ("text", "identity", "instant", "flag", "count", "json",
                "refusal")

_COLUMN_RULE = {"text": text, "identity": identity, "instant": instant,
                "flag": _flag, "count": _count, "json": _persisted_json,
                "refusal": _sealed_refusal}


def row(record, what, columns):
    """ONE persisted SQL row, adopted as a fresh document with every column
    owned.

    Review [P1]: this domain did not exist. A row was read with `SELECT *`,
    turned into a dict and handed on as trusted internal data -- so a persisted
    `settle_by` of `not-an-instant` was COMPARED against the current instant and
    the claim continued as though the deadline were valid. The store is a
    receiving trust domain like any other: this process did not write the bytes
    it is reading, and a durable value that no longer round-trips is exactly the
    case a control store exists to survive.

    The column set is checked as well as the values. A row with columns this
    build does not name is a store written under a shape this build cannot
    reason about, and adopting its familiar-looking columns would be reading a
    stranger's row as our own.
    """
    taken = {key: record[key] for key in record.keys()}
    _members(taken, what, tuple(columns), ())
    for name in columns:
        contract = columns[name]
        value = taken[name]
        if value is None:
            if not contract.nullable:
                _refuse(f"{what} carries no {name}, and a persisted "
                        f"{name} is not optional in a row this build owns")
            continue
        _COLUMN_RULE[contract.kind](value, f"{what}'s {name}")
        if contract.members is not None:
            # The parse is this layer's own, on a value it has just proved
            # decodes -- the same rule `deadline` follows with an already-owned
            # instant. A failure here would be a defect in the line above.
            document(json.loads(value), f"{what}'s {name}",
                     required=contract.members)
        if contract.allowed is not None and value not in contract.allowed:
            _refuse(f"{what} records {name} {name_value(value)}, which is not "
                    f"one of {', '.join(contract.allowed)}")
    # §13 AT THE ONE CROSSING OUT OF THE STORE. Third review [P1]: the column
    # contract proves the SET and the SHAPES and says nothing about content, so
    # a hand edit could put a currently live bearer into a persisted value and
    # every public read that returns the row would hand it out. A write-side
    # walk cannot establish §13 for bytes read after a later edit -- which is
    # the reasoning `certified_agent_session_profile` was corrected on, and
    # this docstring already calls the store a receiving trust domain.
    #
    # HERE rather than in each reader, because "each reader" is a list somebody
    # maintains: every adopted row in this manager comes through this one
    # function, so a projection added tomorrow is covered tomorrow.
    #
    # THE DYNAMIC RULE, NOT A SECOND SHAPE ADOPTION. It refuses a value this
    # process is holding LIVE; a genuinely forgotten secret is absent from the
    # registry and its row stays readable and replayable, which is what keeps
    # an exact durable replay from failing on the retry.
    check_no_durable_secret(taken, what=what)
    return taken


def adopted(payload, what):
    """Persistent bytes coming back out of our own store, decoded and owned.

    Ours once; a receiver input again the moment they are read, because the
    process that wrote them is not this one and the bytes may not be either.
    Malformed persisted JSON escaped `replay` as a raw `JSONDecodeError` -- from
    the one function whose whole job is handing a retry the first answer.

    The decode is where the domain is crossed, so the decode is where the owner
    lives.
    """
    text(payload, what)
    try:
        return json.loads(payload)
    except ValueError:
        _refuse(f"{what} is persisted text this build cannot decode; a durable "
                f"value round-trips or it is not one")


# §10.1: the frozen assignment-generation range. A counter is never decremented
# or reused, so the space is finite -- and a generation outside it is one no
# consumer of these documents can read back.
MAX_SAFE_INTEGER = 2 ** 53 - 1


def capability(value, what):
    """Something this manager will CALL, typed before it is relied on.

    Review [P1]: the bearer mint was accepted untyped, so a non-callable one
    performed a Work projection, a certification check, expiry processing and a
    capacity read before escaping as a raw `TypeError` -- authority reads spent
    on a call that could never have happened. Typing a capability is cheap and
    happens before anything is spent; discovering it is missing halfway through
    is neither.

    `callable` inspects the object and runs nothing.
    """
    if not callable(value):
        _refuse(f"{what} is a capability this manager calls; this is "
                f"{name_value(value)}")
    return value


def generation(value, what):
    """An assignment generation: a whole number inside the frozen range.

    NOT `count`, and not a flag. §4 makes a generation part of an assignment
    IDENTITY, and identities are compared -- so text that looks like a number
    compares wrong everywhere and reaches an INTEGER column as a raw
    `sqlite3.IntegrityError`. Review [P1]: it did exactly that, AFTER the
    authority had already answered the claim, which is the worst moment to find
    out -- the authority holds a live assignment and the manager has no record.

    `bool` is excluded because `True == 1`, and a generation of `True` would
    compare equal to the first one ever minted.

    THE UPPER BOUND IS NOT HERE. §10.1 makes the generation space finite, and
    the contracts layer already refuses an integer outside the frozen range as
    part of owning the document this member arrived in -- so a bound repeated
    here would be a second owner for one property, and unreachable besides. I
    wrote one, measured it as an equivalence, and took it out rather than
    leaving a rule nothing can drive.
    """
    if type(value) is not int or value < 0:
        _refuse(f"{what} is a whole assignment generation, counting from zero; "
                f"this is {name_value(value)}")
    return value


def injected(value, what):
    """The answer of a capability trusted deployment supplied.

    Its callability is proved when the capability is accepted; this proves what
    it RETURNS. A port that types the call and not the answer lets `None` become
    a frozen durable identity, which is how an injected signature reached a NOT
    NULL column during acceptance.
    """
    return text(value, what)
