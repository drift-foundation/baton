"""W52821 — THE USER-SCOPED CREDENTIAL SOURCE, and nothing else.

WHAT THIS REPLACES, and why the thing it replaces was a bypass. The supported
ordinary command took `--credential-file PATH` and returned that one file's
bytes for EVERY provider and EVERY reference the trusted profile resolved. So
the two operands `CredentialHome.materialize` asks a provider with -- the
provider identity and its opaque reference -- were discarded at the seam
(`del provider, reference`), and an attempt authorized for two slots delivered
one file twice. The profile decided what a credential IS and the command then
ignored the decision, which makes the profile's opacity a claim rather than a
property.

WHAT THIS IS INSTEAD. A CLOSED REGISTRY the user owns, privately, naming which
of their own files backs which exact (provider, reference) pair:

    {"schema": "baton.user-credential-sources/1",
     "sources": [{"provider": "...", "reference": "...", "path": "/abs/..."}]}

    python3 tools/dogfood_operator.py --grants G.json --evidence O.json \
        --credential-sources /home/<user>/.baton/credential-sources.json

FOUR PROPERTIES, and each is a rule below rather than a convention:

  EXACT SELECTION. The provider and the reference are matched TOGETHER and
  EXACTLY. There is no fallback of any shape -- not "the only entry", not a
  provider-only match, not a default source -- because every fallback is this
  module deciding a credential the profile did not name. And they are held to
  THE MANAGER'S OWN SHAPE and nothing narrower -- exact non-empty encodable
  text, the same thing `credentials.resolved_delivery` proves about the two
  values it reads out of the trusted profile. A grammar invented at this end
  would refuse a pair that end legitimately granted.
  AMBIGUITY REFUSES. Two entries for one (provider, reference) is a registry
  that does not say which file backs the pair, and picking either would be
  choosing a credential nobody chose. The whole registry is refused, whether
  or not the duplicated pair is the one being selected.
  PRIVATE, PROVED AT THE DESCRIPTOR. The registry and the selected source are
  each opened WITHOUT following a final symlink, proved to be an ordinary file
  owned by the effective uid carrying no group or other permission, and then
  read THROUGH THAT PROVED DESCRIPTOR. A name resolved a second time is a name
  something else can have replaced.
  NOTHING LEAVES BUT THE BEARER. `resolve` answers the credential text and
  nothing else. No content and no host source path reaches a grants file, an
  evidence record, a lifecycle record or any worker-visible document -- and
  because a refusal is prose that can be carried, NO REFUSAL IN THIS MODULE
  NAMES A PATH, A PROVIDER OR A REFERENCE EITHER. What a refusal names is ONE
  FIXED LABEL for the selection, the two values' encoded-byte WIDTHS, and the
  rule that failed; `_selection` below argues why a bounded prefix of an
  opaque value is not a safer quotation than the whole of it.

STANDARD LIBRARY ONLY, and it is deliberate rather than incidental. This is the
one piece a user reads before trusting the command with a path to their own
credential, so it stays small enough to read and imports nothing from the
manager. THE ONE THING IT DOES NOT SPELL is the bearer bound: `max_bearer` is a
required operand, so the manager's own `credentials.MAX_BEARER` governs the
read and there is no second copy of it here to drift.

IT READS NOTHING AT CONSTRUCTION. The approved lazy window -- no source read
and no attempt slot before activation -- is preserved by holding only the
operand's shape in `__init__`; the registry and the source are opened when the
delivery is materialized and never before.

AND IT HOLDS NOTHING BETWEEN CALLS. No cache, no lock, no module-level state:
two resolvers running concurrently over two registries are two independent
readers of two files, which is what lets one deployment supervise more than one
attempt without either of them learning about the other.
"""

import argparse
import json
import os
import stat

__all__ = ["ENDING_MODES", "MAX_PATH", "MAX_REGISTRY_BYTES",
           "MAX_SOURCES", "OPERAND", "SCHEMA", "SourceRefusal",
           "UserCredentialSources", "add_operand", "held_registry",
           "named_operand", "refused_in_ending"]

# THE REGISTRY'S OWN CONTRACT, held by equality at both ends like every other
# closed document this deployment reads. A registry from another generation is
# refused on the way in rather than interpreted as this one.
SCHEMA = "baton.user-credential-sources/1"

# THE OPERAND, spelled once. The command's parser, the launcher's own reader
# and every refusal below take the name from here, so there is no second
# spelling for `--help` and the code to disagree about.
OPERAND = "--credential-sources"

# THE MODES THAT MUST NOT CARRY ONE. An abandonment ends an attempt whose
# material is proved gone, a handoff retry finishes one whose delivery is
# ADOPTED, and W61984's already-quiescent finalization touches the authority
# and nothing else -- it opens no engine, no home and no source at all. None of
# the three reads a registry, and an operand that asks one of them to is a
# contradiction rather than a spare word.
ENDING_MODES = ("--abandon", "--retry-handoff", "--finalize-quiescent")

# HOW MANY SOURCES ONE REGISTRY MAY NAME. The same bound the manager puts on
# one assignment's slots, for the same reason: a registry is read once per
# resolved slot and an unbounded list is an unbounded read.
MAX_SOURCES = 16

# HOW WIDE THE REGISTRY DOCUMENT ITSELF MAY BE, bounded AT THE READ rather than
# after it. Reading a file of unknown size into memory and then measuring it is
# a ceiling that admits the thing it exists to refuse.
MAX_REGISTRY_BYTES = 64 * 1024

# A SOURCE PATH'S WIDTH, and this one is the reader's own rather than the
# manager's, because it bounds a name THIS module passes to `os.open`.
MAX_PATH = 4096

_REGISTRY_MEMBERS = ("schema", "sources")
_SOURCE_MEMBERS = ("path", "provider", "reference")

# NO GROUP AND NO OTHER PERMISSION. `credentials.VOLATILE_FILE` is 0640 because
# the manager's slot is delivered to a runtime that already holds the
# configured workspace group. A USER'S OWN SOURCE is delivered to nobody: it is
# read by this command running as that user, so any bit outside the owner's is
# a grant the user did not have to make.
_PRIVATE = 0o077


class SourceRefusal(Exception):
    """A user credential source this reader will not use.

    Deliberately its own type rather than the operator's or the manager's.
    `OperatorRefusal` is a deployment saying it was asked for something it does
    not do and `ContractRefusal` is the manager judging its own contracts; this
    is a reader saying the user's own registry or source does not meet the
    private-file rules it is read under. The command translates it at its own
    boundary rather than this module reaching for a type it cannot import.
    """


def _refuse(message):
    raise SourceRefusal(message)


# WHAT A REFUSAL SAYS ABOUT A SELECTION, and it is a LABEL rather than either
# value.
#
# Review 2026-09-01T13-57-01Z [P1]. Every refusal about a selection here
# interpolated `{provider!r}` and `{reference!r}`, and that was survivable only
# while this reader was inventing a 64-character grammar for a provider and a
# 512-character one for a reference. Holding both to THE MANAGER'S OWN SHAPE --
# exact non-empty encodable text, with no width of its own -- is the correction
# that removed those ceilings, and it removed with them the accident that had
# been bounding this prose: a deployment whose profile legitimately maps a slot
# to a 60 KiB opaque reference would have put 60 KiB of it into a refusal that
# an operator's terminal, a report, and anything that ever carried either, then
# holds.
#
# AND A PREFIX IS NOT A SAFER COPY. A reference is opaque precisely because
# neither end reads a meaning out of it, so neither end can say which of its
# bytes are the harmless ones -- and the FIRST bytes of an opaque value are
# exactly the ones a naming scheme makes identifying. A bounded quotation of a
# value nobody may interpret is still a quotation.
#
# SO THE LABEL IS FIXED AND ONLY A WIDTH VARIES. Two encoded byte counts, which
# are integers THIS reader measured rather than text the profile chose, so a
# refusal is the same length whatever the pair is. Nothing is lost that the
# deployment does not already hold: the two values are in the trusted profile
# it wrote and in the registry the user wrote, and the widths are what tell an
# operator which of those two columns disagree.
_SELECTION = "a provider identity and opaque reference"


def _selection(provider, reference):
    """The one fixed label, plus the two widths and nothing else.

    Both operands are `_held_text`-proved at every site that calls this, so
    `encode` answers a length here rather than raising. BYTES rather than
    characters because `MAX_REGISTRY_BYTES` is the bound stated over the same
    document, and two numbers an operator compares should be in one unit.
    """
    return (f"{_SELECTION} of {len(provider.encode('utf-8'))} and "
            f"{len(reference.encode('utf-8'))} encoded bytes")


# -- the operand ---------------------------------------------------------------


def add_operand(parser):
    """Declare `--credential-sources` on the ONE public parser.

    Review 2026-08-30T14:36:46Z [P1], applied to the operand that replaced the
    one it was written about: a private pre-parser that stripped an operand
    before the public parser saw it left `--help` listing two operands while
    the launcher refused without a third. So the declaration lives here, one
    function, and everything that reads the operand -- the command and the
    launcher below -- reads it through this same declaration.
    """
    parser.add_argument(
        OPERAND, dest="credential_sources", metavar="PATH",
        help=f"path to this user's own private {SCHEMA} registry, which names "
             f"which of their files backs each exact provider and reference "
             f"the trusted profile resolves. Never a grants member and never "
             f"an environment variable: both are durable surfaces. Read once, "
             f"when the delivery is materialized, and never written back")
    return parser


class _Quiet(argparse.ArgumentParser):
    """A parser whose refusal RAISES rather than printing and exiting.

    `named_operand` is not the command's parser and must not answer like one:
    a malformed operand is reported by the public parser, in the public
    parser's own words, with the public parser's usage line.
    """

    def error(self, message):
        raise SourceRefusal(message)


def named_operand(argv):
    """The operand's value, read from argv THROUGH THE SAME DECLARATION.

    The launcher constructs the resolver before the command parses its own
    operands, because the resolver is one of the capabilities the command is
    given. That is not the stripped pre-parser the review forbade: the operand
    is still declared on the public parser by `add_operand`, so `--help` names
    it and the command still holds it -- this reads the same declaration a
    second time rather than hiding it.

    IT NEVER SPEAKS FOR THE PUBLIC PARSER. Anything it cannot read answers
    `None`, and the public parser then reports the operand in its own words.
    """
    parser = _Quiet(add_help=False)
    add_operand(parser)
    try:
        known, _rest = parser.parse_known_args(list(argv))
    except SourceRefusal:
        return None
    return known.credential_sources


def refused_in_ending(value, *, mode):
    """An ending mode carrying this operand is a CONTRADICTION, not a spare word.

    Every ending mode runs without a registry by construction: an abandonment
    proves material gone without ever opening it, a handoff retry ADOPTS the
    delivery the ordinary attempt already materialized, and a quiescent
    finalization performs no engine, home or source act of any kind. An operand
    naming a source is therefore asking a mode that opens nothing to open
    something, and ignoring it would let an operator believe a credential was
    delivered by a command that delivers none.
    """
    if mode not in ENDING_MODES:
        _refuse(f"a credential source operand is held for exactly "
                f"{', '.join(ENDING_MODES)}; this asks about {mode!r}")
    if value is not None:
        _refuse(f"{mode} reads no credential source registry and opens no "
                f"source: it ends or finishes an attempt whose credential is "
                f"adopted or already proved gone. {OPERAND} names material "
                f"this mode must not open, so it is refused rather than "
                f"ignored")
    return None


# -- the registry document ------------------------------------------------------


def _held_text(value, what):
    """THE MANAGER'S OWN SHAPE, and deliberately not one character more.

    Review 2026-09-01T13-04-03Z [P1]. This reader used to hold a provider
    identity to a 64-character alphanumeric-dot-dash-underscore grammar with an
    alphanumeric first character, and an opaque reference to 512 characters
    with no control characters in it. NOTHING SAYS EITHER OF THOSE. What the
    manager proves about the same two values, one file over in
    `credentials.resolved_delivery`, is `boundaries.identity` and
    `boundaries.text` -- exact non-empty encodable text -- and this end
    inventing a NARROWER grammar is this module deciding what a credential may
    be named, which is the exact property the profile's opacity exists to give.
    A deployment whose profile legitimately maps `vault/team` to a reference
    wider than 512 characters would have had its registry refused here for a
    rule nobody wrote.

    SO THE HOLD IS THE SHAPE AND NOTHING ELSE: exactly `str`, not empty, and
    encodable. Encodability is not a length or a character class -- it is the
    one thing "text" has to mean at both ends of a value read out of a UTF-8
    document and MEASURED into a refusal by `_selection`, and a lone surrogate
    is text neither end can write down or count the bytes of.

    AND THE WIDTH IS STILL BOUNDED, by the document rather than by a second
    rule: `MAX_REGISTRY_BYTES` is enforced AT THE READ, so no provider and no
    reference this function ever sees is wider than the registry it came out
    of. A bound stated twice is a bound that holds in one of the two places.
    """
    if type(value) is not str:
        _refuse(f"{what} is text; this is a {type(value).__name__}")
    if not value:
        _refuse(f"{what} is not empty")
    # THE ANSWER IS A FLAG AND THE REFUSAL IS RAISED OUTSIDE THE HANDLER, on
    # purpose. `UnicodeEncodeError` puts THE WHOLE OFFENDING VALUE in its own
    # text, and this same function holds a source path -- so a refusal raised
    # inside the handler would chain a `__context__` naming one, which is the
    # single thing no refusal in this module may carry.
    try:
        value.encode("utf-8")
        encodable = True
    except UnicodeEncodeError:
        encodable = False
    if not encodable:
        _refuse(f"{what} is text this reader can encode; a value neither end "
                f"of one reference can write down is not one it will match on")
    return value


def _document(value, what, members):
    if type(value) is not dict:
        _refuse(f"{what} is one JSON object; this is a "
                f"{type(value).__name__}")
    missing = sorted(one for one in members if one not in value)
    extra = sorted(one for one in value if one not in members)
    if missing or extra:
        _refuse(f"{what} is exactly {', '.join(members)}"
                + (f"; missing {', '.join(missing)}" if missing else "")
                + (f"; unexpected {', '.join(extra)}" if extra else ""))
    return value


def _held_path(value, what):
    """A source path, held to a shape -- and NEVER echoed into a refusal.

    Absolute because a relative one means whatever directory the command
    happened to be started from, and `..` refused because a canonical path is
    what this reader opens. Both are shape rules and neither is custody: the
    custody proof is `_proved_read`, at the descriptor, where it cannot be
    raced by a name resolved twice.

    THE WIDTH AND THE CONTROL CHARACTERS ARE THIS RULE'S OWN, and they stay
    here rather than in `_held_text` because they are true of a NAME THIS
    MODULE OPENS rather than of a value the manager also holds. `os.open`
    rejects an embedded NUL with a `ValueError` that is not a `SourceRefusal`,
    and a path is the one value in this file no refusal may echo -- so a name
    this reader cannot state is refused before it is opened.
    """
    _held_text(value, what)
    if len(value) > MAX_PATH:
        _refuse(f"{what} is wider than the {MAX_PATH} characters this reader "
                f"holds")
    for one in value:
        if ord(one) < 0x20 or ord(one) == 0x7F:
            _refuse(f"{what} carries a control character; a name this reader "
                    f"cannot state is not one it will open")
    if not value.startswith("/"):
        _refuse(f"{what} is an absolute path; a relative one names whatever "
                f"directory this command was started from")
    if ".." in value.split("/"):
        _refuse(f"{what} traverses with `..`; a canonical path is what this "
                f"reader opens")
    return value


def held_registry(document):
    """The closed `baton.user-credential-sources/1` registry, proved as a whole.

    A PURE FUNCTION OVER A DOCUMENT, so the same hold is applied wherever a
    registry is believed and there is no chance of two answers. What it returns
    is a tuple of built-in triples rather than the caller's own objects: the
    selection below matches on values this function proved, never on members it
    reaches back into a caller's document for.
    """
    _document(document, "a user credential source registry",
              _REGISTRY_MEMBERS)
    if document["schema"] != SCHEMA:
        _refuse(f"a user credential source registry says it is "
                f"{document['schema']!r} and this reader reads {SCHEMA!r}")
    sources = document["sources"]
    if type(sources) is not list:
        _refuse(f"a user credential source registry's sources are a list; "
                f"this is a {type(sources).__name__}")
    if not sources:
        # A REGISTRY NAMING NOTHING IS NOT A REGISTRY. Every selection over it
        # would refuse for the wrong reason -- "unknown" rather than "you
        # granted none" -- and an operator would read the answer as a mismatch
        # between their profile and their file.
        _refuse("a user credential source registry names at least one source; "
                "a registry naming none grants nothing and would refuse every "
                "selection as unknown")
    if len(sources) > MAX_SOURCES:
        _refuse(f"a user credential source registry names at most "
                f"{MAX_SOURCES} sources; this one names {len(sources)}")
    held = []
    seen = []
    for entry in sources:
        _document(entry, "a user credential source", _SOURCE_MEMBERS)
        # BOTH HELD THE SAME WAY THE MANAGER HOLDS THEM, and neither
        # interpreted. `credentials.resolved_delivery` proves the provider and
        # the reference of one slot's mapping as exact non-empty encodable
        # text, and the two ends of one pair must be held the same way or the
        # agreement holds at one of them: a registry refused here for a
        # grammar the profile never had is a credential this deployment
        # granted and this reader would not deliver.
        provider = _held_text(entry["provider"],
                              "a credential provider identity")
        reference = _held_text(entry["reference"],
                               "a credential provider reference")
        path = _held_path(entry["path"], "a credential source path")
        key = (provider, reference)
        if key in seen:
            _refuse(f"a user credential source registry names "
                    f"{_selection(provider, reference)} twice; a pair with "
                    f"two sources does not say which file backs it, and "
                    f"picking either would be choosing a credential nobody "
                    f"chose")
        seen.append(key)
        held.append({"provider": provider, "reference": reference,
                     "path": path})
    return tuple(held)


# -- the private read -----------------------------------------------------------


def _whole(handle, count):
    """Up to `count` bytes from one descriptor. `os.read` may answer fewer."""
    chunks = []
    read = 0
    while read < count:
        step = os.read(handle, count - read)
        if not step:
            break
        chunks.append(step)
        read += len(step)
    return b"".join(chunks)


def _proved_read(place, *, limit, what):
    """One private file, PROVED AT THE DESCRIPTOR and read through it.

    `O_NOFOLLOW` so a symbolic link standing where the file should be is
    refused as itself rather than resolved into whatever it points at -- the
    same rule the manager applies with `lstat` to its own volatile slots, in
    the form that leaves no window between the proof and the read.

    THEN `fstat` ON THAT DESCRIPTOR, and the read from the same one. Proving a
    path and then opening it again is a check-then-open race: what the second
    resolution finds is not necessarily what the first one proved.

    THREE FACTS, and each is a way somebody else could be governing the bytes:
    an ordinary file (a fifo would block this command and a directory is not a
    credential), owned by the effective uid, and carrying no group or other
    permission. A source another identity owns is one they may replace; a
    source another identity may read is one this reader should not treat as
    the user's own private material.

    `O_NONBLOCK` FOR ONE REASON ONLY: it is ignored for the ordinary file this
    is going to accept, and it is what keeps the REFUSAL of a named pipe from
    being a hang. Opening a fifo for reading blocks until somebody writes, so
    without it a registry naming one would stop this command inside the open
    rather than at the type check below.

    NO PATH IN ANY REFUSAL. A refusal is prose, and prose travels: into an
    operator's terminal, into a report, and -- if anything ever carried it --
    into a durable record. What failed is nameable without a host path.

    AND EVERY DESCRIPTOR FAILURE IS ONE OF THIS READER'S OWN OUTCOMES. Review
    2026-09-01T13-04-03Z [P1]: the open was translated and the two acts AFTER
    it were not, so an `fstat` that failed on the proved descriptor, and an
    `os.read` that failed part way through the registry or the source, left a
    bare `OSError` escaping a door that answers `SourceRefusal`. The command
    translates a `SourceRefusal` at its own boundary and lets nothing else
    through, so what an operator saw for an I/O error on their own file was a
    traceback rather than a refusal -- and an `OSError`'s own text carries
    `strerror` AND THE FILENAME, which is the one thing no refusal in this
    module may name. Both are bounded here, into the same path-free prose,
    and NEITHER SUBSUMES THE FOUR RULES AROUND IT: the open refusal, and the
    type, owner and mode refusals below, are raised as themselves and are not
    `OSError`s, so they pass through these translations untouched.
    """
    try:
        handle = os.open(place, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC
                         | os.O_NONBLOCK)
    except OSError as failure:
        raise SourceRefusal(
            f"{what} could not be opened as an ordinary private file "
            f"({type(failure).__name__}); a final symbolic link, an absent "
            f"file and an unreadable one are all refused here, and no host "
            f"source path is named in saying so") from None
    try:
        try:
            found = os.fstat(handle)
        except OSError as failure:
            raise SourceRefusal(
                f"{what} could not be interrogated at the descriptor this "
                f"reader opened ({type(failure).__name__}); a file this "
                f"reader cannot ask about is not one it proves private, and "
                f"no host source path is named in saying so") from None
        if not stat.S_ISREG(found.st_mode):
            _refuse(f"{what} is not an ordinary file; a credential is read "
                    f"from a file this user wrote, never from a device, a "
                    f"directory or a pipe something else is feeding")
        if found.st_uid != os.geteuid():
            _refuse(f"{what} is owned by uid {found.st_uid} and this command "
                    f"runs as {os.geteuid()}; a source this user does not own "
                    f"is one somebody else may replace between two reads")
        mode = stat.S_IMODE(found.st_mode)
        if mode & _PRIVATE:
            _refuse(f"{what} is mode {oct(mode)}; a user-scoped credential "
                    f"source carries no group and no other permission, "
                    f"because it is read by this user and delivered to nobody")
        # ONE MORE THAN THE BOUND, so a file that is too wide is DETECTED
        # rather than silently truncated into a different value.
        try:
            raw = _whole(handle, limit + 1)
        except OSError as failure:
            # AND A PARTIAL READ IS NOT A VALUE. `_whole` may already hold some
            # bytes when the descriptor fails; they are dropped with the
            # failure rather than answered, for the same reason a file wider
            # than the bound is refused whole -- a prefix of a credential is a
            # value nobody can use and everybody would believe.
            raise SourceRefusal(
                f"{what} could not be read through the descriptor this "
                f"reader proved ({type(failure).__name__}); a file this "
                f"reader cannot hold whole is not one it will deliver a part "
                f"of, and no host source path is named in saying so") from None
    finally:
        os.close(handle)
    if len(raw) > limit:
        _refuse(f"{what} is wider than the {limit} bytes this reader holds; a "
                f"value this command cannot hold whole is not one it will "
                f"deliver a prefix of")
    return raw


# -- the resolver ----------------------------------------------------------------


class UserCredentialSources:
    """ONE ordinary command's resolver, over ONE user's own registry.

    CONSTRUCTED PER COMMAND and holding nothing but two operands. It is not a
    singleton, it takes no lock and it caches nothing: the registry is read
    when a slot is resolved, so a resolver built for an attempt that never
    reaches activation has opened nothing at all, and two of these running
    concurrently share no state to disagree about.

    RE-READ PER SLOT, deliberately. A memo across calls would be a cache whose
    contents nothing re-proves, and the registry is bounded precisely so that
    reading it once per resolved slot is an ordinary act. Every read carries
    its own private-file proof, which is the property a cached document would
    quietly drop.

    IT IS CALLABLE because `CredentialHome.materialize` asks its injected
    provider `provider(identity, reference)`. Being the callable itself rather
    than something a lambda closes over is what keeps the two operands from
    being discarded at the seam, which is the whole of the defect this module
    replaces.
    """

    __slots__ = ("place", "max_bearer")

    def __init__(self, place, *, max_bearer):
        # THE MANAGER'S OWN BOUND, AS AN OPERAND. There is no default: a second
        # spelling of `credentials.MAX_BEARER` here would be a second bound
        # with nothing comparing the two, and the one that governs the bytes
        # must be the one the manager will hold the value to.
        if type(max_bearer) is not int or type(max_bearer) is bool \
                or max_bearer < 1:
            _refuse(f"a credential source reader is given the manager's own "
                    f"bearer bound as a positive whole number; this is "
                    f"{type(max_bearer).__name__} {max_bearer!r}")
        # `None` IS AN ORDINARY STATE AND NOT A CONSTRUCTION FAULT. A command
        # invoked with no operand still builds its resolver -- the refusal
        # belongs where the credential is asked for, so an attempt that never
        # reaches activation never learns that it would have had none.
        if place is not None:
            _held_path(place, "a credential source registry path")
        self.place = place
        self.max_bearer = max_bearer

    def __call__(self, provider, reference):
        return self.resolve(provider, reference)

    def resolve(self, provider, reference):
        """The bearer for EXACTLY this provider and this reference.

        THE TWO OPERANDS ARE THE SELECTION. They arrive from
        `credentials.resolved_delivery`, which read them out of the trusted
        profile, and they are matched together and exactly against the user's
        own registry. Nothing here falls back: an unknown pair is refused, and
        so is a registry that names one pair twice.

        AND THE MATCH IS THE ONLY PLACE EITHER VALUE IS USED WHOLE. Every
        refusal below names them through `_selection`, which is a fixed label
        and two widths -- selection stays exact while the prose stays opaque.
        """
        provider = _held_text(provider, "a credential provider identity")
        reference = _held_text(reference, "a credential provider reference")
        named = _selection(provider, reference)
        if self.place is None:
            _refuse(f"this attempt delivers a credential for {named} and no "
                    f"{OPERAND} was named; a user's own credential source is "
                    f"granted explicitly or not at all")
        raw = _proved_read(self.place, limit=MAX_REGISTRY_BYTES,
                           what="the credential source registry")
        try:
            document = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, ValueError) as broken:
            raise SourceRefusal(
                f"the credential source registry is one JSON document and "
                f"this one is not ({type(broken).__name__})") from None
        chosen = [one for one in held_registry(document)
                  if one["provider"] == provider
                  and one["reference"] == reference]
        if not chosen:
            _refuse(f"the credential source registry names no source for "
                    f"{named}; an unknown selection is refused and there is "
                    f"no fallback -- not the only entry, not a provider-only "
                    f"match and not a default source, because every one of "
                    f"those is this reader choosing a credential the trusted "
                    f"profile did not name")
        # EXACTLY ONE, because `held_registry` refuses a duplicated pair.
        raw = _proved_read(chosen[0]["path"], limit=self.max_bearer,
                           what=f"the credential source for {named}")
        try:
            # STRIPPED OF THE SURROUNDING WHITESPACE AN EDITOR ADDS, which is
            # what the operand this replaces did and is not part of a secret.
            bearer = raw.decode("utf-8").strip()
        except UnicodeDecodeError:
            raise SourceRefusal(
                f"the credential source for {named} is not text; a "
                f"materialized credential is text and the manager holds it "
                f"to that") from None
        if not bearer:
            _refuse(f"the credential source for {named} is empty; an empty "
                    f"file is not a credential, and delivering one would fail "
                    f"three layers away from its cause")
        return bearer
