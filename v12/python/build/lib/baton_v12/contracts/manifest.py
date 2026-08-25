"""§12's semantic rules for a durable manifest, beyond what JSON Schema says.

W4, Cut D groundwork. The frozen schema decides SHAPE; these decide what the
shape has to MEAN. A consumer that trusted `entry_count` without checking it
against the entries would be trusting a claim about a tree it also holds, and a
Work id that does not carry its authority's prefix is a reference to a Work in
somebody else's store wearing this one's name.

WHAT IS NOT HERE, and is named rather than implied: §13's durable-secret rule.
Its two halves are a set of forbidden member NAMES and a check against the live
bearer VALUES this process is holding, and the second needs a reference-counted
secret registry this distribution does not have yet. Shipping the name half
under the whole rule's name would be the floor-versus-contract mistake this
dossier already carries twice, so the composite below is called what it is --
`check_manifest_structure` -- and becomes the manifest trust entry when the
secret rule lands beside it.

EVERY RULE IS ABOUT WHAT THE DOCUMENT CONTAINS, not about where a current schema
revision happens to put it. The artifact and content-manifest walks find every
nested object that IS one, at any depth, for that reason.
"""

import ipaddress
import re

from .canonical import digest
from .errors import ContractRefusal, label_of, name_value
from .validate import validate_fragment, verify_manifest_digest

__all__ = ["check_manifest_structure", "check_work_ref", "check_uri",
           "check_relative_path", "check_content_manifest",
           "ARTIFACT_REF_MEMBERS", "CONTENT_MANIFEST_MEMBERS"]

# EVERY EXPORTED RULE OWNS ITS OWN OPERAND.
#
# Review [P1]: `check_work_ref` and `check_content_manifest` are on the public
# surface and indexed their arguments as though the composite had already
# schema-owned them -- so a direct caller's malformed value escaped as a
# TypeError or a KeyError, and a dict SUBCLASS executed hostile `__getitem__`
# inside the trusted contracts layer.
#
# The shape is one public wrapper that validates the fragment, and one private
# body the composite calls with values it has already owned. That is the whole
# of the correction: a public entry owns its input, and an already-owned value
# is not owned twice.

# The member sets that identify a nested object as one of these, wherever it
# sits. Written out, because deciding it from a name would be the guessing the
# whole boundary layer exists to replace.
ARTIFACT_REF_MEMBERS = ("artifact_id", "media_type", "bytes", "content_digest",
                        "locator")
CONTENT_MANIFEST_MEMBERS = ("entries", "entry_count", "total_bytes",
                            "tree_digest")

# THE GRAMMAR, as literal patterns. `fixtures/uri-vectors.json` is the
# authority for what they must accept and refuse, and both runtimes read it.
_SCHEME = re.compile(r"\A[a-z][a-z0-9+.-]*\Z")

# One or more lower-case labels of letters and digits, hyphens allowed inside a
# label and never at either end, EACH BOUNDED TO 63 BYTES. IPv4 is the all-digit
# case of the same shape.
_DNS = re.compile(r"\A[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?"
                  r"(?:\.[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?)*\Z")

# The textual bound on a whole domain name. A label is 63 bytes and the name is
# 255 wire bytes, which is 253 characters written out.
_DNS_NAME = 253

# The bracketed literal's alphabet. `%` is absent, so a scope id never reaches
# the parser; `.` is absent too, and that is this grammar's own narrowing rather
# than the reviewer's prescription -- MEASURED, `ipaddress` returns
# `::ffff:1.2.3.4` unchanged while the frozen constructor normalizes it to
# `::ffff:102:304`, so admitting the dotted form is the one shape where the two
# runtimes would disagree about a canonical address.
_IPV6 = re.compile(r"\A[0-9a-f:]+\Z")

_PORT = re.compile(r"\A[1-9][0-9]{0,4}\Z")

_ESCAPE = re.compile(r"%[0-9A-F]{2}")

# RFC 3986's unreserved and sub-delims, plus the two characters a path segment
# uses. `%` is absent: it only appears as the head of an escape, checked apart.
_PATH_CHARACTERS = frozenset(
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    "-._~!$&'()*+,;=:@/")

_AUTHORITY_PREFIX = 8


def _refuse(message, code="schema"):
    raise ContractRefusal("integrity", code, message)


def check_work_ref(work_ref, what="a Work reference"):
    """PUBLIC: a Work reference this layer has not seen, owned then related."""
    what = label_of(what)
    return _relate_work_ref(
        validate_fragment(work_ref, "workRef", what=what), what)


def _relate_work_ref(work_ref, what):
    """A Work id carries its authority's prefix.

    §4: a reference names a Work IN AN AUTHORITY, and an id that does not carry
    that authority's prefix is a reference to somebody else's Work wearing this
    one's name. The schema can say both members are strings; only this can say
    they belong together.
    """
    authority = work_ref["authority_uuid"]
    work_id = work_ref["work_id"]
    if work_id.split("-", 1)[0] != authority[:_AUTHORITY_PREFIX]:
        _refuse(f"{what} names Work {name_value(work_id)}, which does not "
                f"carry the prefix of authority {name_value(authority)}")
    return work_ref


def check_relative_path(path, what="a path"):
    """A normalized POSIX-relative workspace path, and nothing else.

    Every clause is a way out of the workspace or a way to name one place
    twice: an absolute path leaves it, a backslash is a separator on the other
    family of systems, a NUL truncates in whatever consumes it, and an empty,
    `.` or `..` segment either denormalizes the path or climbs out of the tree
    the manifest is describing.
    """
    what = label_of(what)
    if type(path) is not str or path == "" or "\\" in path or "\0" in path \
            or path.startswith("/") \
            or any(segment in ("", ".", "..") for segment in path.split("/")):
        raise ContractRefusal(
            "integrity", "path",
            f"{what} {name_value(path)} is not a normalized POSIX-relative "
            f"workspace path")
    return path


def check_uri(uri, what="a uri"):
    """One durable locator, against the SHARED CANONICAL GRAMMAR.

    THE RULING (FINDING, "one smaller canonical URI grammar"): v12 does not
    reproduce the frozen constructor's WHATWG acceptance surface. It cannot be
    reproduced as a rule at all -- measured, that constructor NORMALIZES, and
    ten of nineteen forms it accepts come back as a different string. A durable
    locator whose meaning depends on a normalizing parser is one two conforming
    readers can disagree about, which is the failure §3.3 exists to prevent.

    So both runtimes enforce this smaller grammar over the ORIGINAL TEXT, and
    `fixtures/uri-vectors.json` is the authority for both -- not two
    implementations that agree today. Every clause below is literally checkable
    with no parse and no reconstruction:

        scheme      lower-case ASCII `[a-z][a-z0-9+.-]*`
        shape       `scheme://authority` then nothing or an absolute path;
                    `file:///absolute-path` with no remote authority
        authority   no userinfo; one non-empty lower-case DNS/IPv4 host or one
                    bracketed IPv6 literal; an optional port 1 to 65535
        everywhere  no query, no fragment, no backslash, no control or space
        path        percent escapes, when present, are `%` and two UPPER-CASE
                    hexadecimal digits

    DELIBERATELY EXCLUDED, and each is a versioned contract change rather than a
    parser exception if it is ever needed: special-scheme shorthand (`https:x`),
    opaque forms (`urn:x`, `mailto:x`), empty non-file authorities, empty port
    markers, and the rest of WHATWG normalization.
    """
    what = label_of(what)
    if type(uri) is not str or uri == "":
        _refuse(f"{what} is not a URI; this is {name_value(uri)}")
    # THE WHOLE STRING FIRST. These characters are refused wherever they sit,
    # so no later clause has to wonder whether its slice was the one carrying
    # them.
    if any(character <= " " or character == "\x7f" for character in uri):
        _refuse(f"{what} carries a control character or a space; a durable "
                f"locator is one exact line of text")
    if "\\" in uri:
        _refuse(f"{what} carries a backslash, which is a separator in one "
                f"runtime and an ordinary character in another")
    if "?" in uri:
        _refuse(f"{what} contains a query; durable source URIs forbid queries "
                f"because that is where signed credentials and unstable "
                f"selection parameters ride (§12 rule 4)")
    if "#" in uri:
        _refuse(f"{what} contains a fragment (§12 rule 4)")
    scheme, separator, rest = uri.partition("://")
    if not separator or _SCHEME.match(scheme) is None:
        _refuse(f"{what} {name_value(uri)} is not a canonical locator; the "
                f"grammar is a lower-case scheme followed by `://` and an "
                f"authority, with no shorthand and no opaque form")
    if scheme == "file":
        # `file:///absolute-path`, and NO REMOTE AUTHORITY. A file locator that
        # named a host would be a claim about somebody else's filesystem.
        if not rest.startswith("/") or rest == "/":
            _refuse(f"{what} {name_value(uri)} is a file locator; the grammar "
                    f"is `file:///` and an absolute path, with no host")
        _check_path(what, uri, rest)
        return uri
    authority, _, path = rest.partition("/")
    _check_authority(what, uri, authority)
    _check_path(what, uri, "/" + path if path or rest.endswith("/") else "")
    return uri


def _check_authority(what, uri, authority):
    """One host, optionally one port, and never a credential."""
    if not authority:
        _refuse(f"{what} {name_value(uri)} names no host; a locator this build "
                f"cannot resolve is never durable state (§3.3)")
    if "@" in authority:
        _refuse(f"{what} carries userinfo; a durable locator never carries a "
                f"credential (§12 rule 4)")
    if authority.startswith("["):
        host, bracket, port = authority.partition("]")
        if not bracket:
            _refuse(f"{what} {name_value(uri)} opens a bracketed host and does "
                    f"not close it")
        _check_ipv6(what, uri, host[1:])
    else:
        host, colon, port = authority.partition(":")
        if _DNS.match(host) is None or len(host) > _DNS_NAME:
            _refuse(f"{what} {name_value(uri)} names a host outside the "
                    f"grammar; it is lower-case ASCII labels of letters, "
                    f"digits and inner hyphens, each label at most 63 bytes "
                    f"and the whole name at most {_DNS_NAME}, or a bracketed "
                    f"IPv6 literal")
        port = colon + port
    if not port:
        return
    if not port.startswith(":"):
        _refuse(f"{what} {name_value(uri)} carries text after its host that is "
                f"not a port")
    _check_port(what, uri, port[1:])


def _check_port(what, uri, port):
    if _PORT.match(port) is None or int(port) > 65535:
        _refuse(f"{what} {name_value(uri)} names a port outside the grammar; "
                f"it is a decimal number from 1 to 65535 with no leading zero "
                f"and no empty marker")


def _check_ipv6(what, uri, literal):
    """The standard library's own IPv6 grammar, held to ONE CANONICAL TEXT.

    Hand-rolling an address parser is exactly what the ruling steers away from,
    and `ipaddress` is the standard library's. Two rules are this grammar's own
    and neither is redundant, because `ipaddress` is a READER and this boundary
    needs a WRITER's answer:

      * the alphabet, which keeps a scope id (`fe80::1%eth0`) and the dotted
        IPv4-mapped form away from the parser -- `ipaddress` accepts both and
        returns each unchanged, so the canonical-text rule below would not
        catch them, and the frozen constructor refuses the first and rewrites
        the second;
      * canonical text, which is the whole point: `2001:0db8::1` and
        `2001:db8:0:0:0:0:0:1` both PARSE, and both are a different way of
        writing an address this grammar already spells one way. A locator whose
        meaning survives only because a reader normalized it is one two
        conforming readers can disagree about.
    """
    # A separate lower-case clause stood here. MEASURED REDUNDANT and deleted:
    # the alphabet below admits no upper-case character at all, so no literal
    # can reach that clause other than lower case, and a boundary that can
    # never refuse anything is one more thing claiming to be checked.
    if _IPV6.match(literal) is None:
        _refuse(f"{what} {name_value(uri)} names an IPv6 host outside the "
                f"literal alphabet; it is hexadecimal digits and colons, with "
                f"no scope id and no embedded dotted address")
    try:
        parsed = ipaddress.IPv6Address(literal)
    except ValueError:
        _refuse(f"{what} {name_value(uri)} names no IPv6 address")
    if parsed.ipv4_mapped is not None:
        # THE ONE ADDRESS FAMILY WITH NO AGREED SPELLING, and it is measured
        # rather than assumed: for `::ffff:0:0/96` this library writes the
        # DOTTED form (`::ffff:1.2.3.4`) and the frozen constructor writes the
        # HEX form (`::ffff:102:304`), each rejecting the other's canonical
        # text. There is therefore no spelling of a mapped address both
        # runtimes accept, so the grammar excludes the family outright rather
        # than letting one runtime's locator be unreadable to the other.
        # Admitting it later is a versioned contract change, like the rest of
        # the exclusions.
        _refuse(f"{what} {name_value(uri)} names an IPv4-mapped IPv6 address; "
                f"the two runtimes spell that family differently and the "
                f"grammar admits no address it cannot spell one way")
    if str(parsed) != literal:
        _refuse(f"{what} {name_value(uri)} names an IPv6 address that is not "
                f"written canonically; {name_value(str(parsed))} is the one "
                f"spelling this grammar admits")


def _check_path(what, uri, path):
    """An absolute path, with UPPER-CASE percent escapes and nothing else."""
    if not path:
        return
    if not path.startswith("/"):
        _refuse(f"{what} {name_value(uri)} carries a path that is not absolute")
    at = 0
    while at < len(path):
        character = path[at]
        if character == "%":
            if _ESCAPE.match(path, at) is None:
                _refuse(f"{what} {name_value(uri)} carries a percent escape "
                        f"that is not `%` and two UPPER-CASE hexadecimal "
                        f"digits")
            at += 3
            continue
        if character not in _PATH_CHARACTERS:
            _refuse(f"{what} {name_value(uri)} carries {name_value(character)} "
                    f"in its path, which the grammar does not admit")
        at += 1


def check_content_manifest(content, what="a content manifest"):
    """PUBLIC: a content manifest this layer has not seen, owned then checked."""
    what = label_of(what)
    return _check_content_manifest(
        validate_fragment(content, "contentManifest", what=what), what)


def _check_content_manifest(content, what):
    """§12 rule 6: the entries, their order, and the aggregates over them.

    The aggregates are not decoration. A consumer that trusted `entry_count` or
    `total_bytes` without checking them against the entries would be trusting a
    claim about a tree it is also holding -- and the tree digest is what makes
    two manifests over the same tree the same manifest.
    """
    entries = content["entries"]
    paths = [entry["path"] for entry in entries]
    # NOT `check_relative_path` HERE. Every path member of a manifest is typed
    # `relativePath` in the frozen schema, and that pattern already refuses an
    # absolute path, a backslash, a NUL and an empty, `.` or `..` segment. I
    # called the rule here first and measured it: no document that reaches this
    # line can fail it. A second owner for one property is what 4bz forbids, and
    # this is the seventh unreachable boundary this campaign has made me remove.
    #
    # The dependency is not left implicit: a case pins that the schema's own
    # path type carries the rule, so if it ever stops the gate says so.
    for at in range(1, len(paths)):
        # Bytewise sorted AND unique in one pass: equality compares as not
        # less-than, so a duplicate is caught here too.
        if not paths[at - 1].encode("utf-8") < paths[at].encode("utf-8"):
            _refuse(f"{what} entries are not sorted bytewise and unique at "
                    f"{name_value(paths[at])}")
    if content["entry_count"] != len(entries):
        _refuse(f"{what} declares {content['entry_count']} entries and carries "
                f"{len(entries)}")
    total = sum(entry["bytes"] for entry in entries)
    if content["total_bytes"] != total:
        _refuse(f"{what} declares {content['total_bytes']} bytes and its "
                f"entries total {total}")
    if content["tree_digest"] != digest(entries):
        _refuse(f"{what} tree digest does not recompute over the canonical "
                f"ordered entry array (§3.3)", code="digest")
    return content


def _shaped(value, members):
    """Every nested object that IS one of these, at any depth."""
    if type(value) is list:
        for entry in value:
            yield from _shaped(entry, members)
        return
    if type(value) is not dict:
        return
    if all(member in value for member in members):
        yield value
    for child in value.values():
        yield from _shaped(child, members)


def _overlap(left, right):
    """One path inside the other, or the same path twice.

    OVERLAP, not equality. A declared output inside a source directory would
    have the worker writing into material the manifest also says was delivered
    -- and the seal over that tree would stop describing what is on disk.
    """
    return (left == right or left.startswith(right + "/")
            or right.startswith(left + "/"))


def _check_input_manifest(owned, what):
    """§12 rule 3 and rule 7, which are about an input manifest alone."""
    sources = owned["sources"]
    outputs = owned["outputs"]
    names = [item["name"] for item in sources] + [item["name"]
                                                  for item in outputs]
    if len(set(names)) != len(names):
        _refuse(f"{what} reuses an input/output name; names are unique across "
                f"both (§12 rule 3)")
    destinations = ([source["destination"] for source in sources]
                    + [output["path"] for output in outputs])
    # The schema owns each destination's SHAPE, as above. What it cannot see is
    # the relationship BETWEEN two of them, which is the rule below.
    for left in range(len(destinations)):
        for right in range(left + 1, len(destinations)):
            if _overlap(destinations[left], destinations[right]):
                raise ContractRefusal(
                    "integrity", "path",
                    f"{what} destinations {name_value(destinations[left])} "
                    f"and {name_value(destinations[right])} overlap "
                    f"(§12 rule 3)")
    for source in sources:
        check_uri(source["uri"], f"{what} source {source['name']} uri")
        # §12 rule 7: a sha1 base revision under a sha256 repository is not a
        # shorter digest, it is a different object namespace.
        if source["type"] == "git" \
                and source["object_format"] != source["base_revision"]["algorithm"]:
            _refuse(f"{what} source {source['name']} declares object format "
                    f"{name_value(source['object_format'])} and a "
                    f"{name_value(source['base_revision']['algorithm'])} base "
                    f"revision (§12 rule 7)")
    return owned


def check_manifest_structure(document, definition, *, what="a manifest"):
    """Schema first, then §12's semantics, over ONE owned copy.

    SCHEMA FIRST because every rule below reads members, and reading a member
    the schema has not established is how a document with the wrong shape gets
    to decide what happens next.

    Returns the owned document: a validated one a caller can still mutate is a
    time-of-check alias wearing the word "validated".

    NOT the whole §12 trust entry. §13's durable-secret rule is not here, and
    the module docstring says why; when it lands beside this, the composite
    becomes the entry.
    """
    what = label_of(what)
    owned = validate_fragment(document, definition, what=what)
    verify_manifest_digest(owned, what=what)
    # THE PRIVATE BODIES from here down. Every value below is a member of a
    # document the fragment validator has already owned, so validating it again
    # is the blanket revalidation 4bz forbids.
    if "work_ref" in owned:
        _relate_work_ref(owned["work_ref"], f"{what} Work reference")
    if owned.get("assignment_ref") is not None:
        assignment = owned["assignment_ref"]
        _relate_work_ref(assignment["work_ref"],
                         f"{what} assignment reference")
        # NOT the generation's RANGE. §12 rule 2 makes a generation positive and
        # `assignmentRef.generation` already carries `minimum: 1`, so a check
        # here is a second owner for one property and no document that reaches
        # this line can fail it -- the eighth unreachable boundary this campaign
        # has made me delete. A case pins the schema's own bound, so the
        # reliance is checked rather than assumed.
    # §12 rule 8's DECIDABLE HALF. Whether the bytes match is a collection-time
    # fact this layer cannot reach; that the REFERENCE is well formed and its
    # locator carries no credential is decidable here, and is the half that
    # keeps a secret out of the durable document.
    for artifact in _shaped(owned, ARTIFACT_REF_MEMBERS):
        check_uri(artifact["locator"],
                  f"{what} artifact {artifact['artifact_id']} locator")
    for content in _shaped(owned, CONTENT_MANIFEST_MEMBERS):
        _check_content_manifest(content, f"{what} content manifest")
    if owned.get("schema") == "baton.worker-manifest/input":
        _check_input_manifest(owned, what)
    return owned
