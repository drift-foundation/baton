"""§3.2 canonical bytes and digests, closed over the value space this admits.

W4 cut A. Ported from the frozen Node canonicalizer WITH ITS CORRECTIONS, and
with the one place a faithful transliteration would have been silently wrong.

WHY THIS STAYS A LOCAL IMPLEMENTATION while the SCHEMA VALIDATOR does not, in
the reviewer's words and mine: RFC 8785's genuinely hard part is number
formatting, and this contract has no numbers to format. §3.2 forbids floating
point, NaN, infinity and negative zero in durable documents, so the admitted
space is non-negative safe integers, which have exactly one spelling. What
remains is member ordering and string escaping. A JSON Schema validator, by
contrast, has a large construct surface that would be re-derived rather than
implemented -- which is the mistake this repository has caught me making before.

THE ONE PLACE PYTHON IS NOT JAVASCRIPT, and it changes digests rather than
messages. RFC 8785 orders member names by their UTF-16 CODE UNITS.
`Array.prototype.sort` on JavaScript strings already is that ordering, so the
Node implementation gets it for free and says so. Python's `sorted()` orders by
CODE POINTS, and the two disagree for every document with an astral member name
beside one in U+E000..U+FFFF -- because UTF-16 encodes astral characters as
surrogate pairs in U+D800..U+DFFF, which sort BELOW U+E000. A faithful-looking
`sorted(document)` would therefore produce a different canonical form, a
different digest, and a manager that disagrees with the frozen reference about
what a document IS. So the ordering is done on the UTF-16 encoding, and a
regression pins a document that distinguishes the two.
"""

import hashlib
import json

from .errors import ContractRefusal, name_value, type_name_of

__all__ = ["canonical_bytes", "canonical_text", "digest", "digest_of_bytes",
           "MAX_SAFE_INTEGER", "MAX_DEPTH", "MAX_MEMBERS"]

# The JSON-safe integer ceiling, the same one the frozen contract uses: what a
# consumer can read back without loss.
MAX_SAFE_INTEGER = 2 ** 53 - 1

# The frozen structural bounds.
#
# Review [P2]: these lived in `pod.py` and `own` enforced them, but the CANONICAL
# surface is public too -- so a document `own` refuses as too deep or too wide
# could still acquire canonical bytes and a digest by going straight to it. One
# rule enforced at one of two public doors is the shape this repository has
# caught me in five times now, so the bounds live HERE, beside the recursion that
# has to respect them, and `pod` takes them from here.
#
# Depth is checked DURING the descent rather than before it, because a document
# deep enough to matter is one whose depth cannot be measured without descending
# -- and letting it escape as a raw `RecursionError` would be a fault leaving a
# boundary that had a refusal ready.
MAX_DEPTH = 8
MAX_MEMBERS = 512


def _refuse(message):
    # Every canonicalization refusal is the same closed pair: a document that
    # cannot be canonicalized is not a document this contract can carry.
    raise ContractRefusal("integrity", "schema", message)


def _utf16_order(name):
    """The RFC 8785 ordering key: the name's UTF-16 code units.

    Big-endian so that comparing the bytes compares the code units in order.
    This runs no caller code -- `str.encode` on an exact `str` is a built-in
    conversion -- and it raises for a lone surrogate, which is why the surrogate
    rule below runs first and this is never asked to encode one.
    """
    return name.encode("utf-16-be")


def _has_lone_surrogate(text):
    """True when the text carries a UTF-16 surrogate that is not part of a pair.

    Python strings are sequences of CODE POINTS, so a lone surrogate is simply a
    code point in U+D800..U+DFFF -- there are no pairs to check, because a valid
    astral character is one code point above U+FFFF and never a surrogate. That
    is a simpler test than the JavaScript one and it is the same rule: RFC 8785
    requires invalid Unicode to FAIL rather than be repaired into a digestible
    document.
    """
    return any(0xD800 <= ord(character) <= 0xDFFF for character in text)


def canonical_text(value):
    """The canonical string for one admitted value.

    Review [P1]: this took the traversal depth as a parameter. A leading
    underscore is a convention, not a boundary -- a caller could pass
    `_depth=-1000000` and canonicalize a document far past the frozen limit.

    THE BOUND WAS SHARED AND ITS ENFORCEMENT STATE WAS NOT. That is the same
    rule-versus-site defect one level lower than the one the last correction
    closed, and the answer is the same in kind: a public operation takes only
    its genuine operands, and the bookkeeping the rule depends on lives where a
    caller cannot reach it.
    """
    return _canonical_text(value, 0)


def _canonical_text(value, _depth):
    """The descent. Its depth is this module's, not a caller's.

    Exact built-in types only, tested with `type(x) is T` and never `isinstance`:
    a `dict` subclass, an `IntEnum`, a `bool` where an integer is meant or an
    object with a `__json__` hook would each serialize as something other than
    what the caller meant, and a digest over "something else" is the one failure
    this boundary exists to prevent.
    """
    if _depth > MAX_DEPTH:
        _refuse(
            f"the document nests deeper than the frozen limit of {MAX_DEPTH}; "
            f"a shape this boundary refuses to own may not acquire a digest "
            f"either")
    if value is None:
        return "null"
    kind = type(value)
    # `bool` BEFORE `int`, because `True` is an `int` in Python and `1` is not
    # `true`. Checking the other way round would canonicalize a boolean as a
    # number and give two different documents one digest.
    if kind is bool:
        return "true" if value else "false"
    if kind is int:
        if value < 0 or value > MAX_SAFE_INTEGER:
            _refuse(
                f"canonical JSON here admits only JSON-safe NON-NEGATIVE "
                f"integers; {name_value(value)} is not one (§3.2 forbids "
                f"floating point, NaN, infinity, negative zero and, in this "
                f"schema's value space, negative integers)")
        return str(value)
    if kind is float:
        # Python has no separate integer/float JSON space the way the frozen
        # host's `number` did, so the negative-zero and non-finite cases the
        # Node implementation names individually are all here: a float is not a
        # value this contract carries, whatever its magnitude.
        _refuse(
            "§3.2 forbids floating point in a durable document; a float is "
            "refused rather than rounded into a digestible integer")
    if kind is str:
        if _has_lone_surrogate(value):
            _refuse(
                "the string carries a lone UTF-16 surrogate; RFC 8785 requires "
                "invalid Unicode to fail rather than be repaired into a "
                "digestible document")
        # `ensure_ascii=False` keeps the text the caller's text rather than an
        # escaped rendering of it, and Python's escaping of the characters that
        # MUST be escaped is RFC 8785's: the short forms for backspace, tab,
        # newline, form feed and carriage return, `\uXXXX` for the other
        # controls, and nothing else. A vector regression proves that against
        # the frozen reference rather than trusting this paragraph.
        return json.dumps(value, ensure_ascii=False)
    if kind is list:
        if len(value) > MAX_MEMBERS:
            _refuse(
                f"the array carries more than the frozen limit of "
                f"{MAX_MEMBERS} entries")
        return "[" + ",".join(_canonical_text(entry, _depth + 1)
                              for entry in value) + "]"
    if kind is dict:
        if len(value) > MAX_MEMBERS:
            _refuse(
                f"the object carries more than the frozen limit of "
                f"{MAX_MEMBERS} members")
        names = []
        for name in value:
            if type(name) is not str:
                _refuse(
                    f"a member name is {name_value(name)}; canonical JSON "
                    f"names members with text and a coerced name would invent "
                    f"a member the caller did not send")
            if _has_lone_surrogate(name):
                # The frozen host was corrected for exactly this: its surrogate
                # check ran on string VALUES only, so moving the same malformed
                # Unicode into a member NAME made it digestible. RFC 8785's
                # invalid-Unicode failure is not side-dependent.
                _refuse(
                    "a member name carries a lone UTF-16 surrogate; RFC 8785 "
                    "requires invalid Unicode to fail wherever it sits")
            names.append(name)
        names.sort(key=_utf16_order)
        return "{" + ",".join(
            f"{json.dumps(name, ensure_ascii=False)}:"
            f"{_canonical_text(value[name], _depth + 1)}"
            for name in names) + "}"
    _refuse(
        f"canonical JSON has no representation for {type_name_of(value)}; this "
        f"contract admits exact built-in objects, arrays, strings, booleans, "
        f"null and non-negative safe integers")


def canonical_bytes(value):
    return canonical_text(value).encode("utf-8")


def digest(value):
    return "sha256:" + hashlib.sha256(canonical_bytes(value)).hexdigest()


def digest_of_bytes(payload):
    if type(payload) is not bytes:
        _refuse(
            f"a digest over bytes needs exact bytes; this is "
            f"{name_value(payload)}")
    return "sha256:" + hashlib.sha256(payload).hexdigest()
