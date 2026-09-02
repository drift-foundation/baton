"""The OFFER and the CLAIM: where a manager spends a bearer on somebody's behalf.

W4 cut C (PLAN item 4bd). Ported from the frozen Node `offers.mjs` by obligation.

Every step here is about ONE question: after a crash, can the next incarnation
tell what actually happened? The pinned cuts, in order, and each is a durable
fact rather than an inference:

  1. read the Work and the participant's capacity BEFORE spending entropy;
  2. one control-store transaction wins the per-Work offer CAS and stores the
     VERIFIER -- the bearer is emitted only after that commit;
  3. acceptance compares the binding and the verifier in constant time, and in
     ONE transaction consumes the verifier, freezes the intent digest, derives
     the fixed claim operation id and stores a SEPARATE settlement deadline;
  4. the claim is submitted through the participant-bound session and its result
     is recorded before anything else may run;
  5. a LOST result is settled through the authority's own settlement, which may
     only OBSERVE before the deadline;
  6. a commit the manager never saw is recorded late, on restart.

NO ADAPTER WRITE OCCURS WHILE THE CLAIM OUTCOME IS AMBIGUOUS. That is item 4bd's
own sentence and it is why step 5 answers `live` and writes nothing: a control
row written there would claim knowledge this manager does not have.

A DECLINE IS NOT STEP 3 WITH A DIFFERENT WORD (W33937, ruled 2026-08-28 and
reaffirmed 2026-09-02). It carries NO bearer, consumes the verifier in one
transaction so the offer is terminal for that secret, and mints no claim. The
two decisions prove themselves differently on purpose: an acceptance proves
POSSESSION because it is about to take authority, and a decline proves the
exact IDENTITY of the offer it is ending, which is all a terminal act on an
offer needs.

BEARER-FREE IS NOT ANONYMOUS, and step 3 proves the caller before it proves
anything else about the message: BOTH decisions compare the live session's
participant binding against the participant this offer froze at issue. An
offer's binding is public coordination data, so without that comparison the
decline path -- which carries no secret by ruling -- would have no
caller-specific proof at all.
"""

import hmac
import sqlite3

from ..contracts import ContractRefusal, digest, held_secret
from ..contracts.errors import name_value
from . import boundaries, documents, schema
from .store import manager_signature

__all__ = ["OFFER_TTL_SECONDS", "SETTLE_SECONDS", "claim_operation_id",
           "certify_profile", "expire_overdue", "issue_offer", "accept_offer",
           "submit_claim", "settle_claim", "recover_on_restart",
           "claimed_offers_for"]

# §10.2: capacity is advisory here and decided again inside the authority's own
# claim transaction. Checking it at issue is not a substitute -- it is what stops
# a manager minting a bearer it can already see it cannot spend.
OFFER_TTL_SECONDS = 120
SETTLE_SECONDS = 60

_LIVE = ("issued", "accepted")


class _NoBearer:
    """A decline's ABSENT bearer, which is not a bearer that is `None`.

    JSON has one hole and callers have two, and the authority carries the same
    distinction with its own `ABSENT`. Here the two intentions are "I am
    declining, and a decline carries no claim token" and "I sent you a claim
    token whose value is null" -- and they must not share a spelling, because
    a decline is refused for carrying ANY bearer value, the empty string and
    `None` included. An absence that a caller can also produce by accident is
    not an absence this boundary can prove.

    Module-private, and the operand simply DEFAULTS to it: a decline is
    written by omitting the bearer, so there is no second way to spell the
    absence and nothing new on the package's public surface.
    """

    __slots__ = ()

    def __repr__(self):
        return "NO_BEARER"


_NO_BEARER = _NoBearer()


def claim_operation_id(offer_id, intent_digest):
    """The ONE deterministic claim operation id for an accepted offer.

    DERIVED, never random. It is what makes a lost result settleable: the next
    incarnation must be able to name the exact operation this one submitted
    WITHOUT having seen it submitted.
    """
    return "claim:" + digest({"offer_id": offer_id,
                              "intent_digest": intent_digest})[len("sha256:"):]


def _offers(store, where, operands=()):
    """THE ONE CROSSING out of the offers table, and every row owned as it comes.

    Review [P1]: this module read the offers table from three places -- the
    lookup, the expiry sweep and restart recovery -- and each turned `SELECT *`
    into a dict that was then treated as trusted internal data. A persisted
    `settle_by` of `not-an-instant` was COMPARED against the current instant and
    the claim continued as though the deadline were valid.

    Three read sites is three chances to forget, which is the defect class this
    whole campaign is about. So there is ONE, and a caller cannot obtain an
    offer row without passing through it.
    """
    return [boundaries.row(record, "a persisted offer", schema.OFFER_COLUMNS)
            for record in store._connection.execute(
                "SELECT * FROM offers " + where, operands).fetchall()]


def claimed_offers_for(store, attempt_id):
    """Every CLAIMED offer naming this attempt, through the one crossing.

    Cut D's activation asks "which offer's claim is this attempt's", and the
    answer has to come out of the same owned read every other offer question
    does -- a second reader is a second chance to forget.
    """
    boundaries.identity(attempt_id, "a runtime attempt id")
    return _offers(store, "WHERE runtime_attempt_id = ? AND state = 'claimed'",
                   (attempt_id,))


def _offer_row(store, offer_id):
    # THE OWNING BOUNDARY. Review [P1]: `submit_claim` and `settle_claim` both
    # look an offer up by an unproved identity, and my correction proved the
    # identity at `accept_offer` -- the site I had probed. Proving it at each
    # caller is how a rule ends up applied at some of its sites; proving it
    # where the lookup happens is how it ends up applied at all of them.
    boundaries.identity(offer_id, "an offer id")
    found = _offers(store, "WHERE offer_id = ?", (offer_id,))
    return found[0] if found else None


# Review [P1]: this module had its own `_text`, and it accepted lone surrogates
# and any nonempty string as an instant -- so a surrogate offer id escaped as a
# raw `UnicodeEncodeError` from SQLite and "not-an-instant" silently expired a
# valid offer by lexicographic comparison.
#
# Cut B established both rules and I wrote a weaker copy one file over. SEVENTH
# TIME a rule has been applied at one of N sites in this campaign, and the first
# where the other site was mine and three days old. There is no local rule now:
# `_durable_text` and `_durable_instant` are imported, so there is one of each.


# -- certification -----------------------------------------------------------


def certify_profile(store, kind, name, profile_digest):
    """Record that this manager may act under one profile, BY DIGEST.

    A profile is certified by digest because "the runtime profile we agreed on"
    is a byte identity, not a name -- a later edit to a file would otherwise
    silently recertify itself.
    """
    # BOTH KEY PARTS, before the key is composed. Canonicalizability is not
    # durable text: an integer canonicalizes happily, is interpolated into the
    # metadata key, and commits.
    boundaries.text(kind, "a certified profile kind")
    boundaries.text(name, "a certified profile name")
    boundaries.text(profile_digest, "a certified profile digest")
    signature = manager_signature(
        "profile.certify",
        {"kind": kind, "name": name, "profile_digest": profile_digest})
    def act(connection):
        connection.execute(
            "INSERT INTO meta (key, value) VALUES (?, ?) "
            "ON CONFLICT (key) DO UPDATE SET value = excluded.value",
            (f"profile:{kind}:{name}", profile_digest))
        return documents.profile_certified(kind=kind, name=name,
                                          digest=profile_digest)

    return store.transact(f"profile.certify:{kind}:{name}", "profile.certify",
                          signature, act)


def _certified(store, kind, name):
    """The certification this store recorded, ADOPTED as it is read back.

    A metadata value is persisted text like any other, and a certification is
    compared against the offer's profile digest -- so an unreadable one would
    reach that comparison. Absence is answered separately from value, because
    "nothing certifies this profile" and "the certification says X" are
    different answers to the caller.
    """
    row = store._connection.execute(
        "SELECT value FROM meta WHERE key = ?",
        (f"profile:{kind}:{name}",)).fetchone()
    if row is None:
        return None
    return boundaries.text(row["value"], "a persisted profile certification")


# -- expiry ------------------------------------------------------------------


def expire_overdue(store, now, work_id=None):
    """Settle every offer this manager's own clock has ended.

    Review [P1] in the frozen host: expiry was reachable only from a LATE
    DECISION, so an offer whose worker never answered stayed `issued` with an
    unspent verifier and held the per-Work unique index forever. A bound that
    depends on the holder of an expired authorization sending one more message
    is not a bound.

    Reissue is manager-owned time processing, so it belongs here -- before
    entropy, like every other check.
    """
    boundaries.instant(now, "the current instant")
    where = "WHERE state IN ('issued', 'accepted') AND expires_at <= ?"
    operands = [now]
    if work_id is not None:
        # The optional filter is an operand too, and an optional one is exactly
        # the kind a sweep by probing misses.
        boundaries.identity(work_id, "a Work id")
        where += " AND work_id = ?"
        operands.append(work_id)
    expired = []
    for offer in _offers(store, where, operands):
        _settle_terminal(store, offer, "expired", "the offer's time elapsed",
                         now)
        expired.append(offer["offer_id"])
    return expired


def _settle_terminal(store, issued, state, reason, at):
    """An ISSUED-ONLY terminal transition: decline, expiry, abandonment.

    Review [P1]: the frozen host updated `issued` OR `accepted` rows, and both
    callers act from an earlier `issued` read. Another manager can accept in
    between -- and a stale decline or abandonment then destroyed the durable
    authorization and the fixed claim identity acceptance had just frozen.

    Each of these CASes only from `issued`, and losing reports the winner's
    state without rewriting it.

    W33937: the decline REPLAY reaches this with an already-`declined` row on
    purpose. The journal answers first -- an exact repeat returns the recorded
    result and a reworded one is an operation collision -- so the act below is
    not reached, and if it ever were, its CAS is what still refuses to rewrite
    the committed settlement.
    """
    offer_id = issued["offer_id"]
    signature = manager_signature(f"offer.{state}",
                                  {"offer_id": offer_id, "reason": reason})

    def act(connection):
        changed = connection.execute(
            "UPDATE offers SET state = ?, verifier_spent = 1, "
            "decision_reason = ?, decided_at = ? "
            "WHERE offer_id = ? AND state = 'issued'",
            (state, reason, at, offer_id)).rowcount
        if changed != 1:
            current = _offer_row(store, offer_id)
            return documents.offer_settled_by_another(
                offer_id=offer_id, state=current["state"],
                settled_by_another=True)
        return documents.offer_settled(offer_id=offer_id, state=state,
                                       reason=reason)

    return store.transact(f"offer.{state}:{offer_id}", f"offer.{state}",
                          signature, act)


# -- step 1 and 2: the offer -------------------------------------------------


def issue_offer(store, port, *, offer_id, work_id, runtime_attempt_id,
                input_digest, policy_digest, profile_digest, profile_name,
                mint_bearer, participant=None, ttl_seconds=OFFER_TTL_SECONDS):
    """Issue one offer, and return its bearer exactly once.

    THE PARTICIPANT IS THE SESSION'S BINDING, not an operand beside it. The
    frozen host took one independently and never compared it, so the offer, the
    verifier and the intent could name B while the claim was necessarily taken
    as A through the bound session -- an authorization recorded for one identity
    and spent by another.
    """
    # UNROLLED, so every label is a literal AT ITS CALL SITE. This was a loop
    # over a table of (value, label) pairs, which reads well and hides the labels
    # from an inventory derived by walking the code -- the same defect as a
    # boundary nobody applied, one level up: a rule that is applied and cannot be
    # SEEN to be applied is a rule the next reviewer has to take on trust.
    boundaries.text(offer_id, "an offer id")
    boundaries.text(work_id, "a Work id")
    boundaries.text(runtime_attempt_id, "a runtime attempt id")
    boundaries.text(input_digest, "an input digest")
    boundaries.text(policy_digest, "a policy digest")
    boundaries.text(profile_digest, "a profile digest")
    boundaries.text(profile_name, "a profile name")
    # THE MINT IS A CAPABILITY, typed before anything is spent. Review [P1]: an
    # untyped one performed the projection, the certification check, expiry
    # processing and the capacity read before escaping as a raw `TypeError` --
    # four authority interactions spent on a call that could never happen.
    boundaries.capability(mint_bearer, "the bearer mint")
    # Review [P1]: `ttl_seconds` went straight to `timedelta`, so a negative
    # duration minted a bearer and COMMITTED AN ALREADY-EXPIRED OFFER -- durable
    # authority nobody can use, holding the per-Work slot until something sweeps
    # it. A duration is an operand like any other and is proved before the reads
    # it precedes, let alone before entropy.
    # THE DURATION AND THE SUM are both the deadline boundary's business now, so
    # there is no local duration rule to drift from it.
    # AND THE DEADLINE IS COMPUTED HERE, before the authority is read at all.
    #
    # Review [P1]: representability was proved where the deadline was USED,
    # which is after `project_work` and `slot_holder` -- so an unrepresentable
    # duration still spent two authority reads before being refused. The clock
    # is this manager's own, so nothing about computing the deadline needs the
    # authority, and doing it first makes "before reads or entropy" true rather
    # than nearly true.
    issued_at = store._now()
    expires_at = boundaries.deadline(issued_at, ttl_seconds, "the offer's expiry")
    if participant is not None and participant != port.participant:
        raise ContractRefusal(
            "refused", "precondition",
            f"the offer names {name_value(participant)} and this session acts "
            f"for {name_value(port.participant)}; the claim would be taken by "
            f"the binding, not by the operand")
    participant = port.participant

    work = port.project_work(work_id)
    if work is None:
        raise ContractRefusal("refused", "precondition",
                              f"no Work {name_value(work_id)}")
    if (work.get("status") != "open" or work.get("phase") != "queued"
            or work.get("handler") is not None
            or work.get("gate") is not None):
        raise ContractRefusal(
            "refused", "precondition",
            f"{name_value(work_id)} is {name_value(work.get('status'))}/"
            f"{name_value(work.get('phase'))} with handler "
            f"{name_value(work.get('handler'))} and gate "
            f"{name_value(work.get('gate'))}; an offer is issued only against "
            f"open, queued, unclaimed, ungated Work")

    # CERTIFICATION IS UNAVOIDABLE.
    #
    # Review [P1]: the frozen host's comparison was conditional on the argument
    # being supplied, so OMITTING it issued an offer with no certification check
    # at all -- and the happy-path fixtures omitted it throughout. A check a
    # caller can skip by not mentioning it is not a boundary. There is no
    # operand here at all: the control store's own record is the only fact.
    certified = _certified(store, "runtime", profile_name)
    if certified is None:
        raise ContractRefusal(
            "policy", "profile-uncertified",
            f"nothing certifies profile {name_value(profile_name)} for this "
            f"manager; an offer promises an execution shape, and one nothing "
            f"has agreed to is not a shape")
    if certified != profile_digest:
        raise ContractRefusal(
            "policy", "profile-uncertified",
            f"the offer names profile {name_value(profile_digest)} and this "
            f"manager has certified {name_value(certified)}")

    # ELAPSED OFFERS ARE SETTLED FIRST, before entropy, like every other check.
    expire_overdue(store, issued_at, work_id=work_id)

    held = port.slot_holder(participant)
    if held is not None:
        raise ContractRefusal(
            "refused", "precondition",
            f"{name_value(participant)} already holds {name_value(held)}; "
            f"capacity is checked here so a bearer is not minted for a claim "
            f"that cannot be taken, and again inside the authority's own "
            f"transaction (§10.2)")

    # EVERY EFFECTIVE DURABLE OPERAND RIDES THE SIGNATURE, including the
    # AUTHORITY the Work belongs to. The frozen host carried the local Work id
    # alone, so reusing an issue identity against another authority read as an
    # exact replay rather than an operation collision -- and a changed policy
    # digest replayed the first offer as though it were the same request. An
    # operation identity that ignores operands is not an identity.
    # OWNED AT THE PORT, as part of the projection document. Owning it again
    # here is the blanket revalidation 4bz forbids -- and the inventory found it
    # by noticing the probe now lands on the port's label instead of this one.
    authority_uuid = work["authority_uuid"]
    # W16823: AND THE TWO FACTS THIS OFFER FREEZES ABOUT THE WORK. Owned at the
    # port with the rest of the projection, for the same reason the authority
    # is: owning them again here is the blanket revalidation 4bz forbids.
    work_scope = work["scope"]
    work_route = work["route"]
    signature = manager_signature("offer.issue", {
        "offer_id": offer_id, "authority_uuid": authority_uuid,
        "work_id": work_id, "participant": participant,
        "runtime_attempt_id": runtime_attempt_id, "input_digest": input_digest,
        "policy_digest": policy_digest, "profile_digest": profile_digest,
        # THE FROZEN PAIR RIDES THE SIGNATURE, because it is a durable operand
        # that changes what this offer MEANS: the same offer id issued against
        # a Work whose scope has moved is a different authorization promise,
        # and replaying the first would promise a scope nobody offered.
        "work_scope": work_scope, "work_route": work_route,
        "expires_at": expires_at})

    # AND THE REPLAY IS CHECKED BEFORE ENTROPY IS SPENT.
    #
    # Review [P1]: the bearer was minted first, so an exact replay returned the
    # FIRST offer's durable verifier beside a newly minted bearer that does not
    # derive it -- a secret the holder cannot use and cannot tell is unusable.
    # The bearer exists only in the process that minted it, so a replay cannot
    # reproduce one; refusing is the only honest answer, and it is given without
    # minting anything.
    found, _ = store.replay(f"offer.issue:{offer_id}", signature,
                            kind="offer.issue")
    if found:
        raise ContractRefusal(
            "refused", "precondition",
            f"offer {name_value(offer_id)} is already issued; its bearer "
            f"existed only in the process that minted it, so this call cannot "
            f"reproduce one and will not answer with a bearer that does not "
            f"derive the stored verifier")

    bearer = mint_bearer()
    boundaries.text(bearer, "a minted bearer")
    verifier = digest(bearer)

    # THE ACTION IS THE COMMIT MARKER.
    #
    # Re-review [P1]: provenance was inferred from bearer INEQUALITY, and
    # inequality proves a loss while equality proves nothing -- two exact
    # issuers can receive the same injected bearer, and the loser then replayed
    # the winner's record and reported success. Effectively-once is decided by
    # the journal, never by a probabilistic property of the secret source.
    #
    # `transact` runs the action only when it did NOT replay, so this flag IS
    # the transaction boundary reporting which of the two happened.
    committed = []

    def act(connection):
        committed.append("ours")
        # ONE LIVE OFFER PER WORK is enforced by a partial unique index, and an
        # index violation is a raw `sqlite3.IntegrityError`. Found by my own
        # fixture rather than by a review: a manager that loses this race is
        # having an ordinary precondition refused, and telling it so in SQLite's
        # vocabulary would make a caller learn our taxonomy from a driver.
        try:
            connection.execute(
                "INSERT INTO offers (offer_id, work_id, authority_uuid, "
                "participant, runtime_attempt_id, incarnation, input_digest, "
                "policy_digest, profile_digest, verifier, work_scope, "
                "work_route, issued_at, expires_at, state) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'issued')",
                (offer_id, work_id, authority_uuid, participant,
                 runtime_attempt_id, store.incarnation, input_digest,
                 policy_digest, profile_digest, verifier, work_scope,
                 work_route, issued_at, expires_at))
        except sqlite3.IntegrityError as failure:
            raise ContractRefusal(
                "refused", "precondition",
                f"Work {name_value(work_id)} already has a live offer; one "
                f"authorization at a time is what stops two workers being "
                f"promised the same Work") from None
        return documents.offer_issued(
            offer_id=offer_id, work_id=work_id, participant=participant,
            runtime_attempt_id=runtime_attempt_id, verifier=verifier,
            issued_at=issued_at, expires_at=expires_at)

    # §13 (W6630): THE BEARER IS LIVE FOR EXACTLY THIS ACT, so the journal's
    # own durable-surface walk has something to refuse. Registering it is what
    # turns the value half of §13 from a dormant rule into an enforced one --
    # a check against an empty registry reads as a leak boundary while being
    # nothing at all, which is the same failure a name-only check would be.
    #
    # SCOPED TO THE JOURNALLED ACT and no wider. The bearer rides back with
    # the RESULT deliberately (`offer_bearer` below), and holding it across
    # that return would make this manager refuse to answer with the one value
    # the caller is entitled to.
    with held_secret(bearer):
        record = store.transact(f"offer.issue:{offer_id}", "offer.issue",
                                signature, act)
    # AND THE DECIDING REPLAY IS THE ONE INSIDE THE TRANSACTION. The optimistic
    # check above answers the sequential case and two concurrent exact issuers
    # both pass it; the winner commits its verifier and `transact` hands the
    # LOSER that committed record. Returning it beside the loser's freshly
    # minted bearer is the original unusable pair, under exactly the concurrency
    # the journal exists to settle.
    if not committed:
        raise ContractRefusal(
            "refused", "precondition",
            f"offer {name_value(offer_id)} was issued concurrently by another "
            f"act; this call replayed that act's committed record rather than "
            f"performing one, and the bearer it would answer with existed only "
            f"in the process that minted it")
    if record["verifier"] != verifier:
        # A SEPARATE INVARIANT, not the provenance decision: if this call did
        # commit, the row it wrote must derive from the bearer it minted.
        raise ContractRefusal(
            "integrity", "digest",
            f"offer {name_value(offer_id)} committed a verifier this call's "
            f"bearer does not derive")
    # The bearer rides back with the RESULT and never through the store.
    return documents.offer_bearer(record, bearer)


# -- step 3: acceptance ------------------------------------------------------


def accept_offer(store, port, *, offer_id, decision, bearer=_NO_BEARER, now,
                 runtime_attempt_id, work_ref, reason=None):
    """Accept or decline one decision, in ONE transaction.

    What this owns is the BINDING: the caller's session must be bound to the
    participant this offer authorizes, and the decision must name this exact
    offer, attempt and Work. An ACCEPTANCE additionally carries possession of
    this exact bearer; a DECLINE carries no bearer at all and is refused if it
    carries one (W33937).
    """
    # `_offer_row` owns the identity as it crosses into SQL, so owning it here
    # too was the same value validated twice -- 4bz's blanket revalidation, and
    # the one my old inventory could not see because both sites shared a label.
    boundaries.instant(now, "the current instant")
    issued = _offer_row(store, offer_id)
    if issued is None:
        raise ContractRefusal("refused", "precondition",
                              f"no offer {name_value(offer_id)}")
    if decision not in ("accept", "decline"):
        raise ContractRefusal(
            "refused", "precondition",
            f"a decision is accept or decline; this is {name_value(decision)}")

    # THE BEARER IS ACCEPTANCE'S CAPABILITY, NOT THE OFFER'S PASSWORD. W33937,
    # ruled 2026-08-28 and reaffirmed 2026-09-02: an acceptance presents the one
    # deliberate secret because it is about to TAKE authority, and a decline is
    # authorized by the exact integrity-protected binding it names. Putting the
    # secret on the wire in order to REFUSE authority would widen that one
    # exposure and buy nothing.
    #
    # This boundary used to prove possession before it branched, so a decline
    # carrying the bearer settled the offer -- against the frozen worker-control
    # shape (`claim_token` is null for a decline), its portable case, and the
    # assignment state machine. That is the stale implementation the ruling
    # names, and this is the correction.
    #
    # THE SHAPE FIRST, ahead of the binding comparison below: whether a claim
    # token is present at all is what schema decides, and which offer the
    # decision names is what this manager decides afterwards. Nothing has been
    # compared or written when a carrying decline is refused here, so the offer
    # and the journal are exactly as they were.
    if decision == "decline" and bearer is not _NO_BEARER:
        raise ContractRefusal(
            "integrity", "schema",
            f"the decline for offer {name_value(offer_id)} carries a claim "
            f"token; a decline carries none and is authorized by the exact "
            f"binding it names")

    # AND THE CALLER'S OWN PARTICIPANT AUTHORITY, before either decision
    # settles OR replays.
    #
    # Review [P1] of 2026-09-02: the comparisons below prove which offer a
    # decision NAMES, and the verifier proves possession for an ACCEPTANCE --
    # so once the ruling took the bearer off the decline path, nothing left on
    # it was caller-specific at all. An offer's binding is not a secret: the
    # attempt id and the Work ref are ordinary coordination values, and any
    # differently bound session that knew them could terminate somebody else's
    # offer and consume its verifier. The ruling says a bearer-free decline is
    # authorized by the caller's participant authority AND the exact binding;
    # this is the first half, and it had no implementation.
    #
    # THE SESSION'S BINDING AGAINST THE OFFER'S FROZEN PARTICIPANT. Both sides
    # are already owned -- the port proves its binding when the session enters
    # this manager, and the row's column contract proves what was frozen at
    # issue -- so this is the relation rather than a second crossing.
    #
    # BEFORE THE REPLAYS below, not merely before the settlements: a committed
    # acceptance's answer carries the frozen claim identity and a committed
    # decline's carries the recorded settlement, and handing either to a
    # session that does not hold the authorization would answer a question it
    # was never entitled to ask.
    if port.participant != issued["participant"]:
        raise ContractRefusal(
            "refused", "capability",
            f"offer {name_value(offer_id)} authorizes "
            f"{name_value(issued['participant'])} and this session acts for "
            f"{name_value(port.participant)}; a decision on an offer is the "
            f"bound participant's, and no binding it names makes it anyone "
            f"else's")

    # THE BINDING BEFORE THE SECRET. A decision that names another attempt or
    # another Work is not this offer's decision whatever it possesses, and
    # comparing the secret first would spend the comparison on a message that
    # was never addressed here.
    if runtime_attempt_id != issued["runtime_attempt_id"]:
        raise ContractRefusal(
            "refused", "precondition",
            f"the decision names attempt {name_value(runtime_attempt_id)} and "
            f"offer {name_value(offer_id)} is for "
            f"{name_value(issued['runtime_attempt_id'])}")
    if (type(work_ref) is not dict
            or work_ref.get("work_id") != issued["work_id"]
            or work_ref.get("authority_uuid") != issued["authority_uuid"]):
        raise ContractRefusal(
            "refused", "precondition",
            f"the decision names another Work; an authorization is bound to "
            f"the Work it was issued against")

    # POSSESSION, IN CONSTANT TIME, AND ONLY FOR THE DECISION THAT TAKES
    # AUTHORITY. `compare_digest` is used rather than `!=` because a verifier
    # comparison that returns early tells the holder of a wrong bearer how much
    # of it was right.
    #
    # THE VERIFIER OUTLIVES ITS SPENDING, deliberately: `verifier_spent` records
    # that it was consumed and the digest stays, because an exact retry can only
    # be recognized AS exact if the bearer it carries can still be compared.
    if decision == "accept" and (type(bearer) is not str
                                 or not hmac.compare_digest(
                                     digest(bearer), issued["verifier"])):
        raise ContractRefusal(
            "refused", "capability",
            f"the decision for offer {name_value(offer_id)} does not carry the "
            f"bearer this offer was issued with")

    # AN EXACT REPEAT OF A COMMITTED DECISION REPLAYS IT (§10.2), and that is
    # decided BEFORE the single-use and terminal-state refusals below. What
    # reaches here has already named this exact offer, attempt and Work, and an
    # acceptance has already proved possession -- so it is this offer's own
    # decision arriving a second time, which is what a lost reply looks like.
    # Answering "the bearer is already spent" would fail a retry for doing
    # exactly what a retry is for. Consumption is what stops a SECOND, DIFFERENT
    # outcome; it is not a reason to lose the first one.
    if decision == "accept" and issued["accepted_at"] is not None:
        # THE FROZEN COLUMNS, which acceptance wrote once inside its own
        # transaction and which nothing rewrites -- the terminal transitions
        # compare-and-swap from `issued` precisely so they cannot. So this is
        # the committed answer rather than a newly decided one, member for
        # member, in the contract's own order.
        #
        # KEYED ON THE FREEZE RATHER THAN ON `state`, because submitting the
        # claim moves the state and does not unmake the acceptance this
        # operation committed. An acceptance is the only writer of these
        # columns, so their presence IS "this offer was accepted".
        return documents.offer_accepted(
            offer_id=offer_id, state="accepted",
            intent_digest=issued["intent_digest"],
            claim_operation_id=issued["claim_operation_id"],
            claim_signature=issued["claim_signature"],
            accepted_at=issued["accepted_at"], settle_by=issued["settle_by"])
    if decision == "decline" and issued["state"] == "declined":
        # THROUGH THE JOURNAL, not around it. Replaying a committed decline and
        # refusing a colliding one are the same question, and the store already
        # answers it: the settlement's operation identity is this offer's, and
        # its signature carries the reason. An exact repeat returns the recorded
        # bytes without running the act; a repeat that changes the reason is
        # `refused/operation-collision` and rewrites nothing.
        return _settle_terminal(store, issued, "declined",
                                reason or "declined by the worker", now)

    if issued["verifier_spent"] != 0:
        raise ContractRefusal(
            "refused", "already-terminal",
            f"offer {name_value(offer_id)}'s bearer is already spent; it is "
            f"single-use across acceptance, decline and expiry alike")
    if issued["state"] != "issued":
        raise ContractRefusal(
            "refused", "already-terminal",
            f"offer {name_value(offer_id)} is {name_value(issued['state'])}")

    if now >= issued["expires_at"]:
        # EXPIRY IS A SETTLEMENT, not only a refusal. The frozen host threw and
        # left the row `issued` with an unspent verifier holding the per-Work
        # slot -- so the Work could never receive another offer and the bearer
        # stayed replayable, against the single-use rule.
        _settle_terminal(store, issued, "expired", "the offer's time elapsed",
                         now)
        raise ContractRefusal(
            "refused", "precondition",
            f"offer {name_value(offer_id)} expired at "
            f"{name_value(issued['expires_at'])}")

    if decision == "decline":
        # A decline terminates without spending anything else. The verifier is
        # still consumed, atomically and in the same CAS -- single-use across
        # every outcome -- so no bearer validates against this offer afterwards
        # and a completed decline can never become an acceptance. No claim is
        # minted, no participant capacity is taken and nothing writable exists.
        #
        # §13 OPENS NO SCOPE HERE, and its absence is the correction rather
        # than a gap in it: this manager was never handed the secret on this
        # path, so there is nothing to register live while the settlement's
        # signature and durable reason are walked. A decline that carried the
        # bearer -- to quote it in a reason or for any other purpose -- is
        # refused above as the carrying decline it is.
        return _settle_terminal(store, issued, "declined",
                                reason or "declined by the worker", now)

    # The INTENT is frozen here and never rewritten: it is what the claim
    # operation id derives from, so a later incarnation deriving the same id
    # must be looking at the same intent.
    #
    # AND THE OBSERVATION CLOCK IS NOT ONE OF ITS OPERANDS. Review [P1] of
    # 2026-09-02: `accepted_at` was a member, so the digest -- and with it the
    # derived claim operation id and this act's operation SIGNATURE -- differed
    # between two exact retries that merely read the clock at different
    # instants. The sequential replay above hides that, because a retry which
    # reads an already-accepted row never reaches here; two CONCURRENT retries
    # both read the offer `issued`, and the one that then lost the write lock
    # met the winner's journal row under a signature of its own and was refused
    # `refused/operation-collision` -- failing a retry for being a retry, one
    # step along from the defect this Work already corrected.
    #
    # Every remaining member is frozen at ISSUE, so the intent is a fact about
    # the offer rather than about the moment somebody looked at it, and every
    # exact acceptance of one offer derives one identity however its caller
    # reads the clock. WHEN the offer was accepted is not lost: `accepted_at`
    # is a committed column and a member of the answer, and the loser replays
    # the winner's recorded bytes -- so both callers receive the FIRST accepted
    # instant beside the one fixed claim identity, which is what the retry was
    # asking for.
    intent_digest = digest({
        "offer_id": offer_id, "work_id": issued["work_id"],
        "participant": issued["participant"],
        "runtime_attempt_id": issued["runtime_attempt_id"],
        "input_digest": issued["input_digest"],
        "policy_digest": issued["policy_digest"],
        "profile_digest": issued["profile_digest"]})
    operation_id = claim_operation_id(offer_id, intent_digest)
    # THE AUTHORITY'S OWN FIXED SIGNATURE, frozen with the intent. The frozen
    # host stored NULL here, so settlement passed nothing -- an operation
    # collision against a real committed claim, and a value the authority's NOT
    # NULL column cannot hold when retiring. A settlement that cannot name its
    # operation's operands cannot settle anything.
    # THE ANSWER, not only the callability. The port proves the derivation can
    # be called; what it returns becomes a frozen TEXT identity, and `None`
    # reached the schema-v4 CHECK during acceptance and escaped as a raw
    # `sqlite3.IntegrityError`. An injected capability is trusted to be the
    # authority's; it is not trusted to be correct.
    # OWNED AT THE PORT, once. PLAN 4bz: validate exactly once where the value
    # enters the receiving domain, and do not blanket-revalidate a trusted
    # internal return afterwards. This used to prove it here as well.
    claim_signature = port.claim_signature(issued["work_id"],
                                           issued["participant"])
    settle_by = boundaries.deadline(now, SETTLE_SECONDS, "the settlement deadline")
    signature = manager_signature(
        "offer.accept", {"offer_id": offer_id, "intent_digest": intent_digest})

    def act(connection):
        changed = connection.execute(
            "UPDATE offers SET state = 'accepted', verifier_spent = 1, "
            "intent_digest = ?, accepted_at = ?, settle_by = ?, "
            "claim_operation_id = ?, claim_signature = ? "
            "WHERE offer_id = ? AND state = 'issued' AND verifier_spent = 0",
            (intent_digest, now, settle_by, operation_id, claim_signature,
             offer_id)).rowcount
        if changed != 1:
            # The CAS lost: another process settled this offer between the read
            # and this write, and the read's answer is not the one that counts.
            raise ContractRefusal(
                "refused", "precondition",
                f"offer {name_value(offer_id)} was settled by another act")
        return documents.offer_accepted(
            offer_id=offer_id, state="accepted", intent_digest=intent_digest,
            claim_operation_id=operation_id, claim_signature=claim_signature,
            accepted_at=now, settle_by=settle_by)

    # §13: the same scope, for the bearer a caller handed us. By here it has
    # been proved to derive the stored verifier, so it IS the one deliberate
    # secret and everything this act journals is walked against it.
    with held_secret(bearer):
        return store.transact(f"offer.accept:{offer_id}", "offer.accept",
                              signature, act)


# -- steps 4, 5 and 6: the claim ---------------------------------------------


def _require_accepted(store, offer_id):
    offer = _offer_row(store, offer_id)
    if offer is None or offer["state"] != "accepted":
        raise ContractRefusal(
            "refused", "precondition",
            f"offer {name_value(offer_id)} is "
            f"{name_value(offer['state']) if offer else 'absent'}, not accepted")
    return offer


def _record_claim(store, offer, state, detail, context=None):
    """Record one claim decision, and the context it was authorized under.

    THE CONTEXT IS A SEPARATE PARAMETER rather than a member of `detail`.
    `detail` is the answer document's members and goes out to the caller;
    the context goes to COLUMNS and to the SIGNATURE. Carrying it in `detail`
    would put a durable operand in a document contract that does not name it,
    which the emitter refuses -- correctly.
    """
    offer_id = offer["offer_id"]
    # W16823: THE AUTHORIZATION CONTEXT RIDES THE SIGNATURE.
    #
    # `{offer_id, state}` alone made this identity mean "this offer reached
    # `claimed`", so a settlement carrying a DIFFERENT principal, scope, grant
    # or policy generation replayed the first one instead of colliding -- and
    # the row would durably attribute the second claim's authorization to the
    # first claim's context. What a replay must reproduce is the act, and the
    # act is "claimed, authorized like THIS".
    #
    # `None` for every path that authorized nothing -- a refused or expired
    # settlement -- which is a stable operand rather than an absent one.
    signature = manager_signature("offer.settle",
                                  {"offer_id": offer_id, "state": state,
                                   "context": context})

    def act(connection):
        assignment = detail.get("assignment")
        generation = (assignment.get("generation")
                      if type(assignment) is dict else None)
        held = context or {}
        changed = connection.execute(
            "UPDATE offers SET state = ?, decision_reason = ?, decided_at = ?, "
            # The GENERATION the claim committed. An attempt's activation
            # compares against this: a live assignment somewhere in the
            # authority is not proof that THIS offer claimed it.
            "claim_generation = ?, "
            # AND THE CONTEXT IT COMMITTED UNDER, in the same UPDATE as the
            # state. The table's CHECK requires all six on a `claimed` row and
            # none on any other, so a second write to fill them in could not
            # exist: either this statement is the whole record of the act or
            # the row is refused.
            #
            # COMPOSED FROM `schema.CLAIM_CONTEXT` rather than written out. The
            # six names are the offer's own columns and the attempt's
            # activation reads the same tuple to copy them, so one list is
            # one place for them to be right -- and a seventh added to the
            # table without a writer would be a column nothing fills.
            + ", ".join(f"{column} = ?"
                        for column, _, _ in schema.CLAIM_CONTEXT)
            + " WHERE offer_id = ? AND state = 'accepted'",
            (state, detail.get("reason"), store._now(), generation)
            + tuple(held.get(member) for _, _, member in schema.CLAIM_CONTEXT)
            + (offer_id,)).rowcount
        if changed != 1:
            raise ContractRefusal(
                "refused", "already-terminal",
                f"offer {name_value(offer_id)} is no longer accepted")
        return documents.claim_recorded(offer_id=offer_id, state=state,
                                        **detail)

    return store.transact(f"offer.settle:{offer_id}", "offer.settle",
                          signature, act)


def _context_of(result):
    """The context this manager persists, out of the authority's own result.

    W16823. A FLAT DOCUMENT of exactly the members the offer's columns hold,
    composed in ONE place because both claim-recording paths -- the submitted
    claim and the commit this manager never saw -- reach the same columns and
    the same signature. The endpoint is deliberately absent: it is already the
    offer's participant, and the port has proved the decision's equals it.
    """
    held = dict(result["decision"],
                claim_event_seq=result["claim_event"])
    return {member: held[member]
            for _, _, member in schema.CLAIM_CONTEXT}


def submit_claim(store, port, *, offer_id):
    """Step 4: take the claim, and record what the authority returned.

    THE ASSIGNMENT IS WHAT THE AUTHORITY RETURNED, not a member of it. The
    frozen host read `result.assignment` while the session returns the
    assignment directly -- so the authority held a live generation while the
    manager durably recorded `assignment: null`. A record that disagrees with
    the authority is worse than no record: a restart trusts it.

    W16823: AND THE ANSWER IS NOW THREE FACTS. The authority answers a closed
    result, so `assignment` IS a member of it again -- and the reason the
    correction above is not being undone is that the member is the authority's
    own and is owned at the port, rather than a shape the manager hoped for.
    The other two are the exact claim event and the decision the claim was
    authorized under, and they are recorded in the SAME transaction as the
    state: a claimed offer that could not say which principal claimed it is
    the conflation this Work exists to correct.
    """
    offer = _require_accepted(store, offer_id)
    result = port.claim(offer["work_id"], offer["claim_operation_id"],
                        offer["authority_uuid"], offer["work_scope"],
                        offer["work_route"])
    return _record_claim(store, offer, "claimed",
                         {"assignment": result["assignment"],
                          "claim_event": result["claim_event"],
                          "decision": result["decision"]},
                         _context_of(result))


def settle_claim(store, port, *, offer_id, now, refused_evidence=None):
    """Step 5: settle a claim whose result this manager never saw.

    BEFORE THE DEADLINE IT MAY ONLY OBSERVE. A read saying "not committed"
    proves only its own instant, because a submitter may already have passed its
    preconditions and be about to commit -- so retiring early could close an
    identity the authority is still going to honour, and the manager would
    record a refusal for a claim that succeeded.

    At or after the deadline retirement is safe, because the submitter's own
    window is over. POSITIVE EVIDENCE that the claim refused permits immediate
    retirement: that is not a guess, it is the answer.

    Every path ADOPTS an existing retirement's bound disposition and reason.
    Whoever retired the identity first decided what it means, and a second
    manager inventing its own answer would give one operation two meanings.
    """
    offer = _require_accepted(store, offer_id)
    boundaries.instant(now, "the current instant")
    may_retire = now >= offer["settle_by"] or refused_evidence is not None
    answer = port.settle_operation(
        offer["claim_operation_id"],
        # The signature acceptance froze. Passing anything else -- including
        # nothing -- is an operation collision against a real committed claim.
        offer["claim_signature"],
        refused_evidence or "the manager lost this claim's result",
        "claim-refused" if refused_evidence is not None
        else "settlement-expired",
        may_retire,
        # WHICH WORK AND WHOSE AUTHORITY, so a committed result the manager
        # never saw is owned as THIS offer's assignment rather than as a
        # well-formed one belonging to somebody else.
        # ...AND IN WHICH SCOPE AND AS WHICH ROUTE this offer was issued, so a
        # late-recorded commit is held to exactly the relations a submitted
        # claim is. The path a result arrives by does not change what it has to
        # be to reach these columns.
        offer["work_id"], offer["authority_uuid"], offer["work_scope"],
        offer["work_route"])
    kind = answer.get("kind") if type(answer) is dict else None
    if kind == "committed":
        # STEP 6: the authority committed and this manager never saw it.
        # Recording it late is the whole reason the operation id is derived.
        result = answer["result"]
        return _record_claim(store, offer, "claimed",
                             {"assignment": result["assignment"],
                              "claim_event": result["claim_event"],
                              "decision": result["decision"], "late": True},
                             _context_of(result))
    if kind == "retired":
        bound = answer.get("record") or {}
        state = ("claim-refused" if bound.get("disposition") == "claim-refused"
                 else "settlement-expired")
        return _record_claim(store, offer, state,
                             {"reason": bound.get("reason"), "adopted": True})
    if kind == "refused":
        return _record_claim(store, offer, "claim-refused",
                             {"reason": answer.get("detail")})
    # `live`: the identity is still open and the deadline has not passed.
    # NOTHING CHANGES, and saying so is the honest answer -- a control row
    # written here would claim knowledge this manager does not have.
    return documents.settlement_observed(
        offer_id=offer_id, state="accepted", settled=False,
        why=f"before {offer['settle_by']}; a lost result may only be "
            f"observed, never retired")


def recover_on_restart(store, *, now):
    """The restart rules, and they are deliberately asymmetric.

    An ISSUED offer from a prior incarnation is not honoured after restart:
    nothing durable says the bearer was ever delivered, and a manager that
    honoured it would be trusting a secret it cannot account for.

    An ACCEPTED offer IS recoverable, because its authorization and its fixed
    claim operation are durable -- that is what acceptance froze.

    AND ONLY THIS INCARNATION'S offers are left alone. Several managers
    coordinate through the shared store, so abandoning an offer merely because
    this process did not mint its bearer would let one live manager destroy
    another's work.
    """
    boundaries.instant(now, "the current instant")
    # Elapsed offers are settled first, so recovery reports what is really live
    # rather than counting rows the clock has already ended.
    expire_overdue(store, now)
    abandoned = []
    recoverable = []
    for offer in _offers(store, "WHERE state IN ('issued', 'accepted') "
                                "ORDER BY issued_at"):
        if offer["state"] == "accepted":
            recoverable.append(documents.recoverable_offer(
                offer_id=offer["offer_id"],
                claim_operation_id=offer["claim_operation_id"],
                settle_by=offer["settle_by"]))
            continue
        if offer["incarnation"] == store.incarnation:
            continue
        _settle_terminal(store, offer, "abandoned-after-restart",
                         f"issued by incarnation {offer['incarnation']}", now)
        abandoned.append(offer["offer_id"])
    return documents.recovery_report(abandoned=abandoned,
                                     recoverable=recoverable)
