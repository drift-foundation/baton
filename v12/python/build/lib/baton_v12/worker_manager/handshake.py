"""CERTIFYING ONE AGENT-SESSION PROFILE, and the capability it advertises.

W6592 cut A, the Python manager's first public composition. Ported from the
frozen Node `agent_profile.mjs` and `agent_handshake.mjs` by obligation.

THE PINNED ACCEPTANCE IS ONE SENTENCE AND THE ORDER INSIDE IT IS THE CONTENT:

    the core certifies one exact profile by composing shape, document seal and
    policy checks IN THAT ORDER

SHAPE FIRST, because every later rule reads members, and reading a member the
schema has not established is how the worker-control entry's round-2 bypass
happened. SEAL SECOND, because a policy decision about a document whose bytes do
not match its own digest is a decision about something nobody agreed to. POLICY
LAST, and only the rules the schema CANNOT state.

WHY THE CAPABILITY CONSUMER LIVES HERE rather than beside the certification as
its own exported thing. Before this cut, `certify_profile` recorded that a
DIGEST was certified and nothing in Python ever saw the document that digest
named -- so there was no boundary at which `client_capabilities` could arrive,
which is why the consumer was missing rather than merely unexported. A rule
reached only by a test is a rule about the test.

§2.2 IS ENFORCED AT EMISSION, in `negotiate_acp`, and NOT on the certification
path. Measured: for a profile-carried document the frozen schema states §2.2
exactly, so a second check after the schema has spoken would be the second live
source of truth the schema's own prose warns about. The schema constrains what
may be STORED; §2.2 constrains what is SENT. (This paragraph replaced an
earlier one saying the check was reached from certification -- review [P2]: two
contradictory placements in one contract is worse than either.)

W641'S RULING IS PRESERVED RATHER THAN RECONSIDERED. Agent-session 1.0 keeps ONE
representation of a client capability and it is ACP's: `{"fs": {}, "terminal":
false}` on the wire, and the same structural document persisted. ACP's names and
OMISSION semantics are authoritative -- an absent `readTextFile` or
`writeTextFile` means that capability was not advertised, and Baton does not
synthesize an explicit `false` to restate it. A provider-neutral capability model
is separately justified Work with its own versioned contract if it is ever
needed, and not a translation invented at this boundary.

WHAT IS NOT HERE, and is named so its absence is deliberate: opening sessions,
turns, event normalization, agent-origin routing and the App Server's
provider binding. This cut answers whether a profile may be certified at all,
and what one may advertise.
"""

from ..contracts import (AGENT_SESSION, ContractRefusal, canonical_bytes,
                         check_no_durable_secret, digest, own, own_record,
                         validate_agent_session_fragment)
from types import MappingProxyType

from ..contracts.errors import name_value
from . import boundaries, documents

__all__ = ["ACP_CLIENT_CAPABILITIES", "ACP_CLIENT_CAPABILITY_MEMBERS",
           "SESSION_CAPABILITIES", "certify_agent_session_profile",
           "certified_agent_session_profile", "check_client_capabilities",
           "negotiate_acp"]

# The client-capability members ACP 1.3.0's own declaration names. `session` is
# STABLE and is nonetheless not advertised, because §2.2 withholds EVERYTHING
# rather than everything unsafe. Kept as a named set so a reader can see the
# omission is deliberate rather than an oversight somebody has to re-derive.
ACP_CLIENT_CAPABILITY_MEMBERS = ("fs", "terminal", "session", "plan", "auth",
                                 "elicitation", "nes", "positionEncodings")

# Exactly the six mandatory capabilities of agent-session 1.0, TAKEN FROM THE
# FROZEN SCHEMA rather than retyped. A list written twice is a list that holds
# in one of the two places, and the schema already states this one as a `const`
# on the profile's own member -- so a version that changed the set would change
# this module with it instead of leaving it to disagree quietly.
SESSION_CAPABILITIES = tuple(
    AGENT_SESSION["$defs"]["sessionProfile"]["properties"]
    ["session_capabilities"]["const"])


# §2.2 verbatim, and the ONE canonical representation W641 ruled for: ACP's
# own wire document, `{"fs": {}, "terminal": false}`, persisted structurally as
# it is sent.
#
# READ-ONLY rather than a plain dict. A module-level document would be a single
# object every caller could edit -- including the caller whose edit this
# boundary exists to refuse -- and a FUNCTION returning a fresh copy would put
# a constant on the package's callable surface, where every sweep over the
# exported operations would have to explain why one of them is not an
# operation. What goes on the wire is built from this, so the constant is the
# statement of the rule and never the object that travels.
ACP_CLIENT_CAPABILITIES = MappingProxyType(
    {"fs": MappingProxyType({}), "terminal": False})


def _wire_document():
    """A FRESH plain document, built from the constant rather than shared."""
    return {"fs": dict(ACP_CLIENT_CAPABILITIES["fs"]),
            "terminal": ACP_CLIENT_CAPABILITIES["terminal"]}


def check_client_capabilities(advertised):
    """§2.2 -- the relay may advertise no filesystem, terminal or other client
    capability, and THE COMPARISON IS EXACT.

    Exact rather than "no dangerous member set", because a subset check answers
    the wrong question: it asks whether what is here is safe, when the rule is
    that NOTHING MAY BE HERE. A member ACP adds next version would pass a subset
    check on the day it appeared.

    STRUCTURAL, NOT SERIALIZED. The frozen host's review [P1]: comparing
    `json.dumps` output would make member ORDER part of the rule, and JSON
    member order carries no meaning -- the same document written in a different
    insertion order is the same document, while a different member or value is a
    different one. That is the comparison this is for.

    THE WHOLE ENVELOPE FIRST, and only then its members. Proving the record
    before reading `terminal` or `fs` is what makes those reads inert: a data
    member on an exact built-in record runs nothing, and until the record is
    proved neither of those things is known.
    """
    envelope = _denies("the advertised client capabilities", advertised,
                       ("fs", "terminal"))
    if envelope is not None:
        _deny(envelope)
    if advertised["terminal"] is not False:
        _deny(f"terminal is {name_value(advertised['terminal'])} and §2.2 "
              f"sends false")
    # ABSENCE is how the wire withholds. A filesystem member present at all --
    # EVEN SET FALSE -- is a member ACP's optional type did not have to carry,
    # and this boundary is the one place that difference is still visible.
    inner = _denies("the advertised fs capability", advertised["fs"], ())
    if inner is not None:
        _deny(f"{inner}; §2.2 sends {{}} and the wire withholds by absence")
    return _wire_document()


def _denies(what, value, required):
    """The exact-record verdict as a REASON rather than a raised refusal.

    W1593's bounded diagnostic is the one that describes the fault, and this is
    the caller that needs its words without its taxonomy: §2.2's refusal is
    `policy.denied` because the manager is declining to advertise, not
    `integrity.schema` because a document was malformed. So the primitive is
    asked for its verdict and this boundary supplies the pair -- which is what
    "caller-local taxonomy" means, and why the primitive does not raise the
    caller's code itself.
    """
    try:
        own_record(value, required, what=what)
    except ContractRefusal as refusal:
        return refusal.message
    return None


def _deny(why):
    raise ContractRefusal(
        "policy", "denied",
        f"the relay may advertise no filesystem, terminal or other client "
        f"capability; {why}")


def certify_agent_session_profile(store, profile):
    """SHAPE, then the DOCUMENT SEAL, then POLICY. In that order.

    Returns the certified document with its digest, and files the exact
    canonical BYTES -- not just the digest. A session must pin the per-posture
    policy this profile carries, and a digest cannot be read for it.
    """
    # 1. SHAPE. Owned first, so nothing the validator or any later rule reads
    # can be a live reference back into the caller's object -- and owned by the
    # layer with a LITERAL label, so the inventory can attribute it.
    owned = boundaries.document(profile, "an agent-session profile")
    what = "an agent-session profile"
    validate_agent_session_fragment(owned, "sessionProfile", what=what)
    # §13 (W6630), between the shape and the seal. An agent-session document
    # does NOT go through the manifest composite -- it is a different frozen
    # family with its own validator -- so the durable-secret walk has to be
    # here or this build would file profile bytes nothing had ever walked.
    #
    # Before the seal rather than after: a document carrying a secret is
    # refused as such rather than as whatever digest disagreement is also in
    # it, and the two answers send a caller to different places.
    check_no_durable_secret(owned, what=what)
    # 2. THE DOCUMENT SEAL, over the document with `document_digest` OMITTED --
    # not nulled and not emptied, which are different documents with different
    # canonical bytes.
    declared = owned["document_digest"]
    rest = {name: member for name, member in owned.items()
            if name != "document_digest"}
    sealed = digest(rest)
    if declared != sealed:
        raise ContractRefusal(
            "integrity", "digest",
            f"{what} declares document digest "
            f"{name_value(declared)} and its canonical bytes with "
            f"that member omitted recompute to {name_value(sealed)}")
    # 3. POLICY -- only what the schema cannot state.
    #
    # THE TWO POSTURES CARRY DIFFERENT PINNED POLICIES, and a profile in which
    # they are equal is refused AT CERTIFICATION rather than at run time. The
    # schema pins consent to no workspace and no declared output, which it can
    # say because those are constants; it cannot compare two of its own members,
    # and a consent posture whose policy equals the execution one is a consent
    # session with execution's permissions -- the separation the two postures
    # exist for, removed by a document that otherwise validates.
    if digest(owned["postures"]["consent"]["policy"]) \
            == digest(owned["postures"]["execution"]["policy"]):
        raise ContractRefusal(
            "policy", "profile-uncertified",
            f"{what} pins the same policy for both postures; consent and "
            f"execution differ or there is no separation to enforce")
    # NO SEPARATE CAPABILITY RULE HERE, and that is measured rather than
    # assumed. For a PROFILE-CARRIED document the frozen schema states §2.2
    # exactly -- `clientCapabilities` requires `fs` and `terminal`, admits no
    # other member, makes `fs` an empty closed object and pins `terminal` to
    # the constant false -- and the ACP conditional makes it non-null. Checked
    # against every document `check_client_capabilities` refuses: the schema
    # refuses all of them. A rule repeated after the schema has already spoken
    # is the second live source of truth this schema's own prose warns about,
    # which is how a certified profile comes to disagree with the policy
    # actually enforced. §2.2 is enforced where it is NOT implied: at
    # emission, in `negotiate_acp`.
    body = canonical_bytes(owned).decode("utf-8")
    # NOT JOURNALLED-WITH-REPLAY, and this is the correction review [P1]
    # names. Certification SETS A REPLACEABLE STATE: `(kind, name)` is the
    # identity and recertifying one profile id under new bytes changes the one
    # current profile, which the store's schema says in as many words. The
    # journal's effectively-once contract answers a different question -- "did
    # this operation already happen" -- and an old row answering yes is not
    # proof that its effect is STILL CURRENT.
    #
    # The failing sequence was: certify A, certify B under the same id,
    # certify A again. The third call replayed A's journalled success and
    # skipped the upsert, so it ANSWERED that A was certified while the row
    # still held B -- and `certified_agent_session_profile` correctly reported
    # A absent. The operation contradicted itself.
    #
    # So the effect is performed every time, and it is safe to: the upsert is
    # IDEMPOTENT ON STATE. Running it twice with the same bytes leaves exactly
    # what running it once leaves, which is what effectively-once has to mean
    # for a state-setting operation -- the same answer and the same state, not
    # a cached answer and no state. The frozen host's own certification path
    # is unjournalled for this reason.
    with store._connection:
        store._connection.execute(
            "INSERT INTO profiles (kind, name, digest, body, certified_at) "
            "VALUES ('agent-session', ?, ?, ?, ?) "
            "ON CONFLICT (kind, name) DO UPDATE SET digest = excluded.digest, "
            "body = excluded.body, certified_at = excluded.certified_at, "
            "withdrawn_at = NULL",
            (owned["profile_id"], sealed, body, store._now()))
    return documents.agent_session_certified(
        profile_id=owned["profile_id"], digest=sealed)


def certified_agent_session_profile(store, profile_digest):
    """The certified profile DOCUMENT for a digest, or None.

    Re-validated and RE-BOUND TO THE KEY IT IS FILED UNDER. A row at the named
    key is not proof of what is in it, and a guard on the way IN cannot see an
    edit made afterwards.

    ONE EQUALITY AMONG ALL THREE WITNESSES: what the document DECLARES, what its
    canonical bytes RECOMPUTE to, and the KEY it is filed under. The frozen
    host's review [P1] found the declared member destructured away and never
    compared, so a retained profile whose every other byte matched its key could
    carry somebody else's well-formed seal and still open a session. TWO OF
    THREE AGREEING IS NOT AGREEMENT.
    """
    boundaries.text(profile_digest, "a certified profile digest")
    row = store._connection.execute(
        "SELECT body FROM profiles WHERE kind = 'agent-session' "
        "AND digest = ? AND withdrawn_at IS NULL",
        (profile_digest,)).fetchone()
    if row is None:
        return None
    # A LITERAL LABEL at the owner. The inventory attributes an owned entry by
    # the label written at the site, so a computed one is a boundary it cannot
    # place -- and the digest belongs in the refusals below, where it names
    # which profile disagreed, rather than in the name of the rule.
    # ONE LITERAL LABEL for every rule on this row, and the digest goes in the
    # message rather than in the name of the rule. The inventory attributes an
    # owned entry by the label written at the site, and a probe that spoils a
    # member has to be able to see the same label come back.
    what = "a retained agent-session profile"
    owned = boundaries.adopted(row["body"], "a retained agent-session profile")
    validate_agent_session_fragment(owned, "sessionProfile", what=what)
    declared = owned["document_digest"]
    rest = {name: member for name, member in owned.items()
            if name != "document_digest"}
    recomputed = digest(rest)
    if not (declared == recomputed == profile_digest):
        raise ContractRefusal(
            "integrity", "digest",
            f"{what} declares {name_value(declared)}, recomputes to "
            f"{name_value(recomputed)} and is filed under "
            f"{name_value(profile_digest)}; a profile is the one document all "
            f"three name or it is not certified")
    # §13 ON THE READ SIDE, for the reason the shape and the digest are already
    # re-checked here. Re-review [P1]: the inventory called this prose-only
    # because `certify_agent_session_profile` walks on the way in -- but this
    # function exists precisely because a write-side guard cannot see a later
    # store edit, and a §13 rule left out of that argument is the one rule this
    # read-side trust boundary was not applying. A hand-edited row carrying a
    # live bearer was revalidated, found well-formed, and returned.
    check_no_durable_secret(owned, what=what)
    return owned


def negotiate_acp(store, profile_digest, *, agent_protocol_version,
                  agent_session_capabilities=()):
    """§2.1-§2.4 for ACP: an EXACT wire-version match, or a refusal.

    NO DOWNGRADE. A version the agent answers with is not a negotiation, it is
    an announcement, and the profile is what pinned the one this manager
    certified against.
    """
    profile = certified_agent_session_profile(store, profile_digest)
    if profile is None:
        raise ContractRefusal(
            "policy", "profile-uncertified",
            f"{name_value(profile_digest)} names no currently "
            f"certified agent-session profile; a handshake is conducted under "
            f"one or not at all")
    if profile["wire_protocol"] != "acp":
        raise ContractRefusal(
            "refused", "unsupported-version",
            f"wire-version negotiation belongs to ACP; "
            f"{name_value(profile['wire_protocol'])} is certified "
            f"through its provider binding instead")
    # THE TYPE BEFORE THE VALUE. Review [P1]: this compared with `!=`
    # alone, and Python's equality relation says `True == 1` -- so an agent
    # answering the Boolean `true` was accepted as ACP wire version 1. The
    # frozen reference compares with JavaScript's type-strict `!==`, which
    # never had that reading, so this was a PORT DEFECT rather than a
    # permitted difference: Python's `==` is wider than the contract, and a
    # wire version is an integer or it is not a wire version.
    if type(agent_protocol_version) is not int \
            or type(agent_protocol_version) is bool \
            or agent_protocol_version != profile["pinned_wire_version"]:
        raise ContractRefusal(
            "refused", "unsupported-version",
            f"the agent answered wire version "
            f"{name_value(agent_protocol_version)} and the profile "
            f"pins {profile['pinned_wire_version']}; there is no downgrade")
    absent = [capability for capability in SESSION_CAPABILITIES
              if capability not in _offered(agent_session_capabilities)]
    if absent:
        raise ContractRefusal(
            "refused", "capability",
            f"this agent session cannot provide {', '.join(absent)}; all six "
            f"are mandatory in 1.0")
    return documents.acp_negotiated(
        wire_version=agent_protocol_version,
        # THE WIRE DOCUMENT, DERIVED FROM THE PROFILE AND CHECKED AS IT IS
        # SENT -- not read off a module constant.
        #
        # This is §2.2's real boundary and the reason the rule is not on the
        # certification path. The schema constrains what may be STORED; this
        # constrains what is SENT, and W641's correction was about exactly that
        # difference: the host had one constant standing for two documents and
        # emitted the durable summary onto the transport, sending field names
        # ACP does not have. Answering with a constant here would restore the
        # same seam -- the profile could say one thing and the wire carry
        # another, and nothing would be comparing them.
        client_capabilities=check_client_capabilities(
            profile["client_capabilities"]),
        session_capabilities=list(SESSION_CAPABILITIES))


def _offered(capabilities):
    """ONE EXACT BUILT-IN LIST OF TEXT, and nothing else.

    An operand this manager iterates is an operand it can be handed a
    behaviour-bearing version of -- a generator that yields the six mandatory
    capabilities the first time and nothing the second would otherwise pass a
    handshake and then fail every one of them.

    Review [P1]: `own` alone was not that contract. It owns any exact built-in
    JSON value, so a RECORD whose six keys were the capability names passed as
    though it were the list -- `name for name in {...}` walks a dict's keys.
    And a real list carrying the six plus `1`, `true` or `null` passed too,
    because this projected out the members it could not use. Owning a broader
    value and projecting a subset is not the same contract as establishing the
    one this boundary reads: what a caller sent that this cannot read is a
    REFUSAL, not something to drop quietly, because dropping it means the
    manager and the agent disagree about what was advertised and neither
    finds out.
    """
    taken = own(capabilities, what="the agent's session capabilities")
    if type(taken) is not list:
        _refuse_capabilities(
            f"the agent's session capabilities are one list; this is "
            f"{name_value(capabilities)}")
    for name in taken:
        if type(name) is not str:
            _refuse_capabilities(
                f"the agent's session capabilities name "
                f"{name_value(name)}, which is not a capability name; a "
                f"member this manager cannot read is refused rather than "
                f"dropped")
    return frozenset(taken)


def _refuse_capabilities(message):
    """The caller-local pair. A malformed capability answer is the agent
    failing to present what 1.0 requires, which is `refused.capability` --
    not `integrity.schema`, which would say this manager received a
    malformed document from somebody whose contract it owns."""
    raise ContractRefusal("refused", "capability", message)
