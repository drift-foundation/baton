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
           "negotiate_acp", "settle_unsupported_version",
           "unsupported_version_operation_id"]

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
# W32576: the states a session is in while its handshake is still
# happening. `ready` is reached only after negotiation succeeds, so
# every later state is a session whose handshake is over.
_HANDSHAKE_STATES = ("not-started", "initializing")

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
    what = "an agent-session profile"
    # §13 (W6630) BEFORE THE OWNER ITSELF. Fifth review [P1]: the walk was
    # after `boundaries.document`, and that owner NAMES the value it rejects --
    # so a raw operand that IS the live bearer was rendered into a public
    # `integrity.schema` diagnostic and §13 was never reached.
    #
    # SAFE ON THE RAW OPERAND, which is what the fourth correction got wrong
    # here: `_walk` traverses only exact built-in `dict`, `list`, `tuple` and
    # `str`, and returns without reading anything else. A behaviour-bearing
    # value is refused by the owner below, unexamined by this rule.
    check_no_durable_secret(profile, what=what)
    # 1. SHAPE. Owned first, so nothing the validator or any later rule reads
    # can be a live reference back into the caller's object -- and owned by the
    # layer with a LITERAL label, so the inventory can attribute it.
    owned = boundaries.document(profile, "an agent-session profile")
    # THE OWNED COPY IS WALKED TOO, and the second walk is not redundant. An
    # agent-session document does NOT go through the manifest composite -- it
    # is a different frozen family with its own validator -- so this is the
    # walk that establishes §13 for the bytes actually filed, over the inert
    # copy rather than over an object the caller still holds a reference to.
    #
    # First among the content rules, which fourth review [P1] established for
    # the row boundary and which applies verbatim here: the schema and the seal
    # both NAME the value they reject, so a secret in a malformed member would
    # be quoted into a diagnostic before the walk could answer instead. A
    # document carrying a secret is refused AS SUCH rather than as whatever
    # structural fault is also in it, and the two answers send a caller to
    # different places.
    check_no_durable_secret(owned, what=what)
    validate_agent_session_fragment(owned, "sessionProfile", what=what)
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
    # §13 BEFORE THE SCHEMA AND THE DIGEST, for the reason fourth review [P1]
    # gave about `boundaries.row`: both of the checks below NAME the value they
    # reject, so a hand-edited profile carrying a live bearer would have it
    # interpolated into a public diagnostic before this walk could answer with
    # the bounded refusal instead. `adopted` has already decoded the bytes into
    # exact built-in data, so the walk traverses plain values and runs nothing.
    check_no_durable_secret(owned, what=what)
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
    return owned


def unsupported_version_operation_id(session_ref):
    """The one identity a session's refusal is filed under.

    NAMED RATHER THAN INLINE because a SECOND operation reads the record back:
    W32576's cleanup has to find the row this act wrote, on a later run and
    possibly in a later process, and a derivation spelled twice is two
    derivations that agree until one is edited.

    IT IS THE SESSION ACT AND NOTHING ELSE -- attempt, posture, epoch and
    provider session. The profile, the versions and the refusal's own text
    ride the SIGNATURE, where a change is an operation collision rather than a
    second incompatible account of what one session refused.
    """
    from .sessions import _session_ref
    taken = _session_ref(session_ref)
    return "session.unsupported-version:" + digest({
        "runtime_attempt_id": taken["runtime_attempt_id"],
        "posture": taken["posture"],
        "session_epoch": taken["session_epoch"],
        "provider_session_id": taken["provider_session_id"],
    })[len("sha256:"):]


def settle_unsupported_version(store, port, agent, adapter, *, session_ref,
                               agent_protocol_version,
                               agent_session_capabilities=None):
    """W32576: carry a genuine `unsupported-version` negotiation refusal into
    the ordinary runtime ending.

    THE REFUSAL IS PRODUCED HERE, NOT ACCEPTED FROM A CALLER. Review [P1]: the
    first version took a `ContractRefusal` as an operand and checked its
    category/code, which proves its TYPE and not its PROVENANCE -- so any
    holder of the manager capabilities could manufacture the closed pair,
    name an unrelated profile, and fence a live attempt. It now runs
    `negotiate_acp` itself against the PERSISTED session's own certified
    profile, so the refusal that reaches the ending is one this manager
    derived from evidence rather than one it was handed.

    AND THE SESSION IS THE EXACT PERSISTED FOUR-PART REFERENCE. Attempt,
    posture, epoch and provider session id are proved together by
    `sessions._require_session`, which also refuses a reference naming a
    provider session the row does not hold. The profile compared is the row's,
    never a caller's, and the attempt the ending fences is the row's attempt
    rather than a free operand.

    IT IS NOT A WORKER DISPOSITION AND NEVER BECOMES ONE. The frozen axis
    answers what a WORKER did; a wire version this manager never certified is
    a fact about the session. The axis this act moves is the runtime's.

    ONE FIXED IDENTITY FOR ONE SESSION'S REFUSAL, and changed facts COLLIDE.
    Review [P1] again: hashing the profile and version INTO the identity made
    a second version a second record, so one attempt could carry two
    incompatible accounts of what it refused. The identity is now the session
    act -- attempt, posture, epoch, provider session -- and the profile, the
    pinned and answered versions and the refusal's own text ride in the
    SIGNATURE, where a change is an operation collision rather than a second
    truth.
    """
    from .attempts import request_cancellation, _fixed_assignment, \
        _require_attempt
    from .posture_slots import _slot_row
    from .sessions import _require_session, _session_ref
    from .store import manager_signature

    reference = _session_ref(session_ref)
    if type(agent_protocol_version) is not int \
            or type(agent_protocol_version) is bool:
        raise ContractRefusal(
            "integrity", "schema",
            f"an agent wire version is an integer; this is "
            f"{name_value(agent_protocol_version)}")
    # THE IDENTITY AND THE SIGNATURE ARE MADE OF CALLER OPERANDS ONLY, so an
    # exact call can replay BEFORE any mutable precondition is consulted.
    #
    # Review [P1]: they used to carry the profile, the pinned version and the
    # refusal text, all read from state -- so a committed refusal stopped
    # replaying the moment its session advanced or its profile was withdrawn,
    # which is the opposite of what effectively-once means. Replay is a fact
    # about an act that already happened. What a caller can CHANGE is the
    # reference and the answered version, and changing either still collides.
    operation_id = unsupported_version_operation_id(reference)
    signature = manager_signature(
        "session.unsupported-version",
        {"runtime_attempt_id": reference["runtime_attempt_id"],
         "posture": reference["posture"],
         "session_epoch": reference["session_epoch"],
         "provider_session_id": reference["provider_session_id"],
         "agent_protocol_version": agent_protocol_version})
    found, already = store.replay(operation_id, signature,
                                  kind="session.unsupported-version")
    if found:
        # THE ENDING IS RE-ORDERED, NOT RE-DECIDED. `request_cancellation`
        # has its own effectively-once identity and deliberately re-issues in
        # flight, so a retry after a crash between the two boundaries still
        # reaches the authority.
        return {**already,
                "ending": request_cancellation(
                    store, port, agent, adapter,
                    attempt_id=already["attempt_id"],
                    reason=f"handshake refused: {already['why']}")}

    row = _require_session(store._connection, reference)
    if row["posture"] != "execution":
        raise ContractRefusal(
            "refused", "precondition",
            f"an unsupported-version ending belongs to an execution session; "
            f"this reference names {name_value(row['posture'])}")
    attempt_id = row["runtime_attempt_id"]
    attempt = _require_attempt(store, attempt_id)
    profile_digest = row["profile_digest"]
    profile = certified_agent_session_profile(store, profile_digest)
    if profile is None:
        raise ContractRefusal(
            "policy", "profile-uncertified",
            f"{name_value(profile_digest)} names no currently certified "
            f"agent-session profile; this session's own profile must be "
            f"certified for its refusal to mean anything")
    try:
        _negotiated_against(
            profile, profile_digest,
            agent_protocol_version=agent_protocol_version,
            agent_session_capabilities=list(
                agent_session_capabilities
                if agent_session_capabilities is not None
                else sorted(SESSION_CAPABILITIES)))
    except ContractRefusal as derived:
        if (derived.category, derived.code) != ("refused",
                                                "unsupported-version"):
            raise
        # BOUND OUT OF THE HANDLER, because Python deletes the `except` name
        # when the block ends and this refusal is the whole evidence below.
        refusal = derived
    else:
        raise ContractRefusal(
            "refused", "precondition",
            f"this session negotiated wire version "
            f"{name_value(agent_protocol_version)} successfully; there is no "
            f"unsupported-version refusal to settle")
    pinned = profile["pinned_wire_version"]

    def act(connection):
        # EVERY MUTABLE PRECONDITION RE-PROVED UNDER THE WRITE LOCK, which is
        # the boundary that fixes this record. The reads above answer an
        # optimistic question; these decide.
        held = _require_session(connection, reference)
        if held["state"] not in _HANDSHAKE_STATES \
                or held["profile_digest"] != profile_digest:
            raise ContractRefusal(
                "refused", "precondition",
                f"agent session {held['posture']}/{held['session_epoch']} "
                f"moved to {name_value(held['state'])} under "
                f"{name_value(held['profile_digest'])} while this refusal was "
                f"being settled; the evidence and the record must name one "
                f"session state")
        # AND THE SLOT, which is a SEPARATE AXIS. Review [P1]: runtime-absence
        # evidence releases the posture slot WITHOUT rewriting the session
        # state, so a historical `not-started`/`initializing` row survives the
        # state check while its posture belongs to nobody -- or to a newer
        # epoch. A refusal is evidence from the session that currently HOLDS
        # the execution posture, not from one that used to.
        slot = _slot_row(connection, attempt_id, "execution")
        if slot is None or slot["occupancy"] != "occupied" \
                or slot["session_epoch"] != held["session_epoch"]:
            raise ContractRefusal(
                "refused", "precondition",
                f"the execution posture slot for attempt "
                f"{name_value(attempt_id)} is "
                f"{name_value(None if slot is None else slot['occupancy'])} "
                f"held by epoch "
                f"{name_value(None if slot is None else slot['session_epoch'])}"
                f" and this refusal names epoch {held['session_epoch']}; the "
                f"evidence must come from the session that holds the posture")
        # THE RUNTIME THIS REFUSAL IS ABOUT, RECORDED WITH IT.
        #
        # W32648 review [P0] taught this on the other ending, and the lesson
        # transfers exactly: a manager-owned record that authorizes destroying
        # a container must NAME the container, or the authorization and the
        # command are two independently read facts that combine into one act.
        # The attempt row is re-read under this write lock, so the identity
        # recorded is the one attached when the refusal was fixed.
        held_attempt = _require_attempt(store, attempt_id)
        if held_attempt["runtime_id"] is None:
            raise ContractRefusal(
                "refused", "precondition",
                f"attempt {name_value(attempt_id)} has no attached runtime; a "
                f"handshake refusal is an ending for a session that was "
                f"speaking to a container, and there is none to name")
        return documents.session_unsupported_version(
            attempt_id=attempt_id, assignment=_fixed_assignment(attempt),
            decision="unsupported-version",
            category=refusal.category, code=refusal.code,
            why=refusal.message,
            posture=held["posture"],
            session_epoch=held["session_epoch"],
            provider_session_id=reference["provider_session_id"],
            profile_digest=profile_digest,
            pinned_wire_version=pinned,
            agent_protocol_version=agent_protocol_version,
            runtime_id=held_attempt["runtime_id"])

    recorded = store.transact(operation_id, "session.unsupported-version",
                              signature, act)
    ended = request_cancellation(store, port, agent, adapter,
                                 attempt_id=attempt_id,
                                 reason=f"handshake refused: "
                                        f"{refusal.message}")
    return {**recorded, "ending": ended}


def negotiate_acp(store, profile_digest, *, agent_protocol_version,
                  agent_session_capabilities=()):
    """§2.1-§2.4 for ACP: an EXACT wire-version match, or a refusal.

    NO DOWNGRADE. A version the agent answers with is not a negotiation, it is
    an announcement, and the profile is what pinned the one this manager
    certified against.
    """
    # W32576 review [P0]: THE PUBLIC DOOR READS THE CERTIFIED PROFILE, always.
    # An earlier correction gave this an optional `profile=` operand so one
    # snapshot could serve a verdict and a signature -- and since this function
    # is on the public surface, that let any caller pair an uncertified digest
    # with arbitrary bytes and receive a verdict from them. A single-snapshot
    # requirement is not a licence to widen a trust boundary. The snapshot is
    # shared through `_negotiated_against` below, which is private.
    profile = certified_agent_session_profile(store, profile_digest)
    if profile is None:
        raise ContractRefusal(
            "policy", "profile-uncertified",
            f"{name_value(profile_digest)} names no currently "
            f"certified agent-session profile; a handshake is conducted under "
            f"one or not at all")
    return _negotiated_against(
        profile, profile_digest,
        agent_protocol_version=agent_protocol_version,
        agent_session_capabilities=agent_session_capabilities)


def _negotiated_against(profile, profile_digest, *, agent_protocol_version,
                        agent_session_capabilities):
    """The negotiation RULE, over a profile its caller already owns.

    PRIVATE, and that is the whole point. `negotiate_acp` reads the certified
    profile and hands it here; `settle_unsupported_version` reads it once and
    hands the SAME snapshot here, so a verdict and the evidence signed beside
    it name one observation. Neither door lets a caller supply the bytes.
    """
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
