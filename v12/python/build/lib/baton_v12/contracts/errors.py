"""The manager's CLOSED refusal, and the rules for describing a rejected value.

W4 cut A. Ported from the frozen Node `ContractError` by obligation.

WHY THIS IS NOT `baton_v12.authority.Refusal`. A caller has to be able to tell
WHICH boundary refused. The authority's refusal is an ordinary outcome of an
assignment transition; this one is §9's wire-shaped `category`/`code` pair, and
a manager that raised the authority's type would be telling a caller its own
precondition failure came from the authority. They ship in one distribution and
they are two boundaries.

WHY THE DIAGNOSTIC HELPERS ARE ALSO NOT SHARED, said plainly because a reviewer
should not have to guess. `baton_v12.authority.errors.name_of` implements the
same idea, and a rule that exists twice is a rule that holds in one of the two
places -- I have been shown that four times in this campaign. But `name_of` is
not on the authority package's exported surface, and reaching past that surface
is exactly what the authority's own boundary cases refuse. So the manager owns
its rule, and PROMOTING A SHARED PRIMITIVE IS RAISED RATHER THAN TAKEN: it would
change the authority's exported promise, which is closed Work and not mine.

The properties are carried forward whole, because they were each bought with a
review round:

  a refusal never RUNS the value it refuses -- no `str`, `repr`, iteration,
  attribute access or mapping method on an untrusted object;
  a bounded OUTPUT is not a bounded OPERATION, so nothing renders first and
  truncates after;
  caller text in a message is bounded by the RULE, never by the operand;
  and an integer is named by its SIZE when it is too wide to render, because
  `str()` of one raises above 4,300 digits.
"""

from types import MappingProxyType

__all__ = ["ContractRefusal", "ERROR_CODES", "is_closed_pair", "name_value",
           "label_of", "sample_of", "counted_sample_of", "type_name_of",
           "MESSAGE_LIMIT"]

# The bound on any caller-controlled text this module puts into a message.
_NAME_LIMIT = 60

# The bound on a whole refusal message. Large enough for this package's own
# composed prose plus several bounded operands, and small enough that a durable
# row's size is this contract's decision rather than a raising site's.
MESSAGE_LIMIT = 4096

# The bound on a caller-supplied diagnostic LABEL. Larger, because a label is
# this package's own prose naming the operand a rule is about, and a bound below
# what we legitimately write breaks us rather than a caller.
_LABEL_LIMIT = 160

# Integers wider than this are named by their bit length rather than rendered:
# `str()` of an integer above 4,300 digits RAISES, so the one helper whose job
# is to describe a rejected value safely would otherwise be a way for a rejected
# value to escape the refusal taxonomy.
_SHOWN_INTEGER_BITS = 64

# How many rejected names a message SHOWS. The rest are counted.
_SHOWN_NAMES = 3

# §9's closed category/code PAIRING.
#
# The frozen schema carries the two vocabularies as flat enums and does not pair
# them, which is why §12 makes the pairing a semantic rule. It is written out
# here and a regression asserts the union of these pairs is EXACTLY the schema's
# `category` and `code` enums -- so a code added to the frozen schema without a
# category fails loudly instead of quietly becoming unmappable.
# §9's closed category/code PAIRING, in TWO values on purpose.
#
# Review [P1]: there was one PUBLIC MUTABLE dict and `ContractRefusal` consulted
# that same object at every raising site -- so a caller could append its own code
# to the `policy` tuple and immediately construct a supposedly closed
# `policy/caller-invented` refusal. A closed set a caller can open is not closed.
#
# `_PAIRING` is what the check reads: private, and frozen all the way down, so
# widening it is not a thing a caller can reach. `ERROR_CODES` remains the
# ordinary readable vocabulary a consumer maps onto the wire.
#
# THE RESIDUAL RISK OF THIS SHAPE, named rather than left: two values can drift,
# and a caller reading the public one would believe something the boundary does
# not enforce. So a case asserts they agree, which is the same discipline as the
# pairing-versus-schema agreement one file over.
# Review [P1]: this comment used to say "frozen all the way down" while the
# OUTER container was an ordinary mutable dict -- so a caller reaching the module
# could replace one category's set and build an invented pair. Privacy is not an
# isolation boundary inside one process, which is the same thing the session face
# says about underscores. Frozen means frozen: a read-only mapping over frozen
# sets.
_PAIRING = MappingProxyType({
    "refused": frozenset({"precondition", "unsupported-version", "capability",
                          "extension", "operation-collision",
                          "already-terminal"}),
    "ambiguous": frozenset({"operation", "runtime-start", "collection"}),
    "unavailable": frozenset({"transport", "authority", "artifact-store",
                              "source-provider"}),
    "policy": frozenset({"denied", "profile-uncertified",
                         "credential-lifetime", "retention"}),
    "integrity": frozenset({"schema", "digest", "path", "file-type", "limit",
                            "secret-leak"}),
    "stale-assignment": frozenset({"ended", "generation", "contract",
                                   "target"}),
    "runtime-observation": frozenset({"identity-mismatch", "duplicate-runtime",
                                      "quiescence-unknown",
                                      "state-regression"}),
})

ERROR_CODES = {
    "refused": ("precondition", "unsupported-version", "capability",
                "extension", "operation-collision", "already-terminal"),
    "ambiguous": ("operation", "runtime-start", "collection"),
    "unavailable": ("transport", "authority", "artifact-store",
                    "source-provider"),
    "policy": ("denied", "profile-uncertified", "credential-lifetime",
               "retention"),
    "integrity": ("schema", "digest", "path", "file-type", "limit",
                  "secret-leak"),
    "stale-assignment": ("ended", "generation", "contract", "target"),
    "runtime-observation": ("identity-mismatch", "duplicate-runtime",
                            "quiescence-unknown", "state-regression"),
}


def is_closed_pair(category, code):
    """THE authoritative answer to "is this one of §9's pairs", for reuse.

    Review [P1]: the worker manager owned an adopted refusal's pair against
    `ERROR_CODES`, which is the READABLE vocabulary and an ordinary mutable dict
    -- a consumer maps it onto the wire, and this module's own case proves a
    caller can append to it without opening the frozen pairing. So the boundary
    that adopted persisted refusals was closed against a value callers can
    widen, while the constructor a line later stayed closed and turned the
    disagreement into an AssertionError.

    One authority, read by both. `_PAIRING` stays private because privacy is
    where the frozen data lives; this is the shared QUESTION, which carries no
    mutable state and hands nothing back that could be widened.

    THE TYPES ARE ESTABLISHED HERE, before anything hashes them. `x in mapping`
    on a list raises `TypeError: unhashable type`, so a caller-supplied category
    of the wrong shape escaped the boundary meant to own it -- a check that
    assumes the type it is checking is not owning the field.
    """
    return (type(category) is str and type(code) is str
            and category in _PAIRING and code in _PAIRING[category])


class ContractRefusal(Exception):
    """An ordinary manager refusal, carrying its closed wire pair.

    The pair is validated HERE rather than where it is mapped onto the wire.
    The frozen Node host carried `category` and `code` as free strings and
    trusted every raising site to spell them consistently; a pair checked at the
    edge is a pair that can already have been recorded wrong.
    """

    def __init__(self, category, code, message, *, durable=False):
        super().__init__(message)
        if category not in _PAIRING:
            raise AssertionError(
                f"{category!r} is not one of the frozen error categories")
        if code not in _PAIRING[category]:
            raise AssertionError(
                f"{code!r} is not a {category} code; the pairing is closed")
        self.category = category
        self.code = code
        # W7079: THE MESSAGE IS DURABLE TEXT AND IS OWNED AS SUCH. W6782's
        # inventory found this entry with no owner at all: a lone surrogate
        # reached `message` and was accepted, although a refusal is the value
        # most likely to be stored, journalled and logged -- and the store
        # would then fail to write the very refusal explaining why something
        # was refused, at the moment it is least able to report anything.
        #
        # An ASSERTION rather than a refusal, and for the same reason the
        # pairing above is: a message this build cannot encode is this build's
        # own defect at the raising site, not something a caller sent. Raising
        # a ContractRefusal here would also be a refusal whose own message is
        # the thing under suspicion.
        if type(message) is not str:
            raise AssertionError(
                f"a refusal message is text; this is {type(message).__name__}")
        try:
            message.encode("utf-8")
        except UnicodeEncodeError:
            raise AssertionError(
                "a refusal message must be encodable; a refusal that cannot "
                "be stored is one nobody can read back") from None
        # AND IT IS BOUNDED. Encodable was not enough: a refusal is journalled,
        # logged and carried onto a wire, and an unbounded one is a durable row
        # whose size a raising site decides by accident -- the same rule W1593
        # established for every other diagnostic, applied to the value that
        # carries them all. SCALARS rather than bytes, because that is the
        # length a reader and a `maxLength` both count in.
        if len(message) > MESSAGE_LIMIT:
            raise AssertionError(
                f"a refusal message is at most {MESSAGE_LIMIT} characters; "
                f"this is {len(message)}")
        self.message = message
        # `durable` is a property of the RAISING SITE, not of the calling
        # transition: only the site knows whether it had already written
        # something it must keep.
        #
        # W7079: EXACTLY A BOOLEAN. It took any object, and the truth value of
        # an arbitrary object is decided by running `__bool__` -- inside the
        # refusal handling of a transaction, which is where this build is
        # already failing and least able to survive a caller's code. `is not
        # True and is not False` rather than `isinstance(bool)`, because that
        # admits nothing else at all.
        if durable is not True and durable is not False:
            raise AssertionError(
                f"a refusal's durability is a Boolean; this is "
                f"{type(durable).__name__}")
        self.durable = durable

    def __str__(self):
        return self.message


def _shown(text, limit=_NAME_LIMIT):
    """Bound one already-inert string by the RULE.

    The single place a limit is applied, so a second caller cannot apply a
    different one.
    """
    if len(text) <= limit:
        return text
    return text[:limit] + "…"


def _rendered(text, limit=_NAME_LIMIT):
    """Bound the ESCAPED form, not just the input to the escaper.

    Review [P2]: this bounded the string to sixty CODE POINTS and then called
    `ascii()`, which expands an astral character to ten. Four rejected astral
    member names therefore produced a 1,933-character message under a rule that
    promises under five hundred, and 160 lone surrogates produced 1,004.

    A bounded OPERATION and a bounded OUTPUT are two different properties and
    this had only the first. Both now: the input is cut first, so the escaper
    never walks an unbounded string, and the RESULT is cut again, so the message
    is bounded in the unit it promises.
    """
    return _shown(ascii(_shown(text, limit)), limit)


# The built-in `__name__` getset descriptor, taken once from `type`'s own
# dictionary. Bound to a class directly, it cannot reach that class's metaclass.
_TYPE_NAME = type.__dict__["__name__"]


def type_name_of(value):
    """The bounded TYPE name, read WITHOUT metaclass dispatch.

    Review [P1]: this read `type(value).__name__` through ordinary attribute
    lookup. A class is an instance of its METACLASS, so a caller-controlled
    metaclass can run or raise from `__getattribute__` -- and the helper whose
    entire job is to describe a rejected value without running it was doing
    exactly that, letting the caller's `AssertionError` escape in place of the
    closed refusal the boundary had already decided on.

    `type.__getattribute__` is the default implementation, so calling it
    directly skips a metaclass override. A metaclass could still define
    `__name__` as a descriptor that runs on access, which is why the call is
    guarded and a type that will not name itself is described by that fact
    rather than by whatever it raised.
    """
    kind = type(value)
    try:
        # Review [P1], the SECOND correction of this one line. Attribute lookup
        # ran a metaclass `__getattribute__`; `type.__getattribute__` skipped
        # that override but still RESOLVED AND INVOKED a data descriptor the
        # metaclass installed as `__name__`. Both are the same defect: any
        # lookup that consults the metaclass consults the caller.
        #
        # This binds the built-in slot on `type` itself, so the metaclass is not
        # consulted at all -- the only description of a class this package will
        # accept is the one `type` keeps about it.
        name = _TYPE_NAME.__get__(kind)
    except BaseException:
        return "a value whose type will not name itself"
    if type(name) is not str:
        return "a value whose type will not name itself"
    return _shown(name)


def name_value(value):
    """Name a REJECTED value from inert facts only.

    `repr()` and `str()` call methods the caller chose, and a caller that wants
    to can make either raise -- which would replace this refusal with an
    exception of the caller's choosing at the moment the boundary had already
    decided to refuse. So: the type name, which is this package's own fact about
    the value, plus the value itself only for the built-in constants that carry
    no caller behaviour at all.
    """
    if value is None:
        return "none"
    if value is True:
        return "true"
    if value is False:
        return "false"
    kind = type(value)
    if kind is str:
        # `ascii()` on a `str` runs nothing, cannot fail, and renders a lone
        # surrogate readably instead of raising on the way out.
        return _rendered(value)
    if kind is int:
        if value.bit_length() <= _SHOWN_INTEGER_BITS:
            return str(value)
        return f"an integer of {value.bit_length()} bits"
    return f"a {type_name_of(value)}"


def label_of(what):
    """Bound a caller-supplied diagnostic LABEL by the rule.

    A label is prose naming the operand a rule is about, so it is not quoted the
    way a rejected value is. The LENGTH rule is the same rule, and so is the
    encodability rule: an exact `str` is inert but not necessarily text, and a
    lone surrogate in a label would replace an ordinary refusal with a
    `UnicodeEncodeError` the moment anything logged it.
    """
    if type(what) is not str:
        return name_value(what)
    shown = _shown(what, _LABEL_LIMIT)
    try:
        shown.encode("utf-8")
    except UnicodeEncodeError:
        # The escaped form is bounded too, for the reason `_rendered` gives:
        # 160 lone surrogates escape to 1,004 characters.
        return _rendered(shown, _LABEL_LIMIT)
    return shown


def sample_of(names):
    """Name a bounded SAMPLE of rejected names, and count the rest."""
    return counted_sample_of(names)[0]


def counted_sample_of(names):
    """The bounded sample AND how many names there were, in ONE PASS.

    Deliberately NOT sorted. Sorting a rejected set is work done for prose, and
    insertion order names the first offenders in the order the caller wrote
    them. The count is what makes the sample honest: "does not take three
    things" would understate a four-hundred-name mistake.

    W1593: this took `list(names)` and sliced it. A BOUNDED OUTPUT IS NOT A
    BOUNDED OPERATION -- the copy was proportional to the rejected value, which
    is the property that Work exists to hold, and a caller that also had to
    DECIDE on the count either walked the same names twice or built the same
    list itself. One walk answers both, keeps at most the shown names, and
    copies nothing else. `names` may therefore be a generator, and the one
    place that matters is a wide record whose extra names are never
    materialized at all.
    """
    shown = []
    total = 0
    for name in names:
        total += 1
        if len(shown) < _SHOWN_NAMES:
            shown.append(name)
    text = ", ".join(name_value(name) for name in shown)
    if total > _SHOWN_NAMES:
        text = f"{text} and {total - _SHOWN_NAMES} more"
    return text, total
