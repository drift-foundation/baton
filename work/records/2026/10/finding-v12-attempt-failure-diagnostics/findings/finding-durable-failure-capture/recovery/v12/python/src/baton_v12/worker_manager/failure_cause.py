"""W333486 -- WHO ORDERED THIS RUNTIME STOPPED, under which operation, and what happened.

THE GAP THIS CLOSES, and it is a composition gap rather than a missing fact.
Every half already has an owner: `tokens.token_of` answers the token axis,
`tokens` journals `resource-token.revoked` and `resource-token.returned` with
the store's own `settled_at`, the attempt row carries `execution_runtime`,
`cleanup`, `observed_at`, `activity_bytes` and `activity_at`, and
`attempts.attempt_start_failure_of` / `attempt_preparation_failure_of` answer
the two pre-execution endings. What NO record carried and no reader composed
is the causal/operation/outcome triple: WHICH component ordered THIS exact
runtime stopped, under WHICH operation identity, with WHAT engine outcome, and
whether cessation was ESTABLISHED.

THREE RULES THIS MODULE IS BUILT ON, each of them a correction somebody paid
for:

1. THE RUNTIME IDENTITY COMES FROM THE TOKEN, NOT THE ATTEMPT ROW.
   `intake.reclaim_expired_resource` takes `runtime_id = overdue["container"]`
   and substitutes it into the attempt row before deriving its correlation id,
   because a governed launch BINDS a container before the attempt attaches it
   -- so `attempt["runtime_id"]` can be `None` while a real writer exists.
   `_token_bound` resolves it the same way and every reader here re-proves it.

2. INTENT IS NOT OUTCOME, AND OUTCOME IS NOT CESSATION. Three separate things.
   The intent is durable BEFORE the engine is asked, so a crash between an
   effect and any later record cannot lose the fact that this manager ordered
   this exact container stopped. The outcome is its own record. And within the
   outcome, a KNOWN TYPED STOP FAILURE is carried beside an EXPLICITLY UNKNOWN
   cessation, because reducing both to "no termination evidence" throws away
   the half the manager actually knows.

3. A REPLAYED RECLAIM MAY ISSUE NO EFFECT AT ALL, and the record must say so.
   `intake` guards the stop with `before not in ("absent", "quiescent")` and
   the removal with `before != "absent"` -- two DIFFERENT tests. Only an exact
   absence skips both; a quiescent container still exists, still holds its
   mounts, and is still removed. So `effects` names what this pass actually
   ordered rather than what the act is for.

AND NOTHING HERE INFERS A CESSATION. `review-333812` fixes the semantics: an
exact correlated positive runtime observation can prove cessation; an intent
cannot, and neither can an uncorrelated absence. A historical attempt carrying
none of these records reaches `unknown` and the reader NAMES which records are
absent, because a cause is never manufactured retrospectively.
"""

from ..contracts import ContractRefusal, digest
from ..contracts.errors import name_value
from . import attempts as _attempts
from . import boundaries, documents, tokens
from .store import manager_signature

__all__ = ["COMPONENTS", "OUTCOMES", "CESSATION", "EFFECTS",
           "DIAGNOSTIC_SCHEMA", "OUTCOME_REVISIONS",
           "cessation_intent_operation_id", "cessation_outcome_operation_id",
           "ensure_cessation_intent",
           "record_and_raise_cessation_intent",
           "record_and_raise_cessation_outcome",
           "record_cessation_outcome",
           "attempt_cessation_intent_of", "attempt_cessation_outcome_of",
           "attempt_failure_cause_of", "token_bound_runtime",
           "DEGRADED", "recording_degraded"]

# W333486 review340349 item 2: THE ONE OWNED, VERSIONED DIAGNOSTIC SHAPE, and
# it is one shape on all THREE sides -- this producer, the ordinary versioned
# status document, and the shareable report. The rule is uniform and has no
# exceptions: EVERY LEAF FACT IN THE DIAGNOSTIC IS A WRAPPER, either
# `{"known": true, "value": ..., "source": ...}` or `{"known": false,
# "value": null, "why": ...}`. Nothing in it is a bare scalar.
#
# WHY A WRAPPER EVERYWHERE RATHER THAN SCALARS WITH PROVENANCE BESIDE THEM.
# Both were defensible and TWO DIFFERENT ANSWERS WAS NOT: the rejected
# candidate wrapped the execution and token facts and left the causal ones
# bare, so the report's scalar member list reported a recorded KNOWN value as
# UNKNOWN. One rule means the report decodes every member through one
# function, and the thing the wrapper is FOR survives: a known zero is not a
# missing count, and an unknown still names what is absent.
DIAGNOSTIC_SCHEMA = "baton.v12.attempt-failure-cause/1"

# How far a supersession chain is read before this manager refuses to walk
# further. Bounded because a reader must not become unbounded work; sixteen
# distinct typed observations of one component's one generation is already far
# past anything the acting paths can produce.
OUTCOME_REVISIONS = 16


# THE COMPONENTS THAT ORDER A CESSATION. Three, and cancellation is here for
# the reason `attempts._order_quiescence` exists at all: an Authority-fenced
# cancellation can stop a runtime, and a composed cause that only knew about
# expiry reclaim would report `unknown` for an attempt cancellation ended.
COMPONENTS = ("expiry-reclaim", "settlement", "cancellation")

# WHAT A PASS MAY ACTUALLY ORDER. Named rather than summarized -- see rule 3.
EFFECTS = ("revoke", "stop", "remove", "agent-cancel")

# THE TYPED OUTCOME VOCABULARY. Every member is a distinct fact and none of
# them is reducible to another.
OUTCOMES = {
    # Cessation POSITIVELY established by an exact correlated observation of
    # the runtime this record names. `absent` and `quiescent` are NOT the same
    # fact and do not share a member: a quiescent container still exists.
    "ceased-absent": "absent",
    "ceased-quiescent": "quiescent",
    # A KNOWN TYPED STOP OR ENGINE FAILURE -- refused, timed out, or could not
    # be asked. The manager knows what went wrong and does NOT know whether
    # the runtime ceased.
    "stop-failed": "unknown",
    "engine-unavailable": "unknown",
    "engine-timeout": "unknown",
    # The effect crossed and what exists now could not be established.
    "uncertain-observation": "unknown",
    # The token and the attempt name different runtimes -- what both the
    # reclaim and the cancellation path raise as `identity-mismatch`.
    "identity-mismatch": "unknown",
    # The act may or may not have crossed.
    "lost-reply": "unknown",
    # (c) The token-bound runtime ceased and the attempt's own attachment or
    # activation remains unresolved. TWO facts, carried without collapsing.
    "held-attachment-unresolved": "quiescent-or-absent",
    # (d) Cancellation holds the Authority fence and no identity resolved.
    "fenced-not-ordered": "unknown",
    # The entitlement was withdrawn and NO runtime identity resolved, so there
    # was nothing to order stopped. Distinct from `fenced-not-ordered`, which
    # is cancellation's fence; this one is expiry's, with no fence at all.
    # Unresolved is not absent: a launch may have crossed and its reply been
    # lost, so a container this manager cannot name may be running right now.
    "no-identity-resolved": "unknown",
    # The order crossed and the engine accepted it; nothing is yet observed.
    "ordered": "unknown",
}

# What a record may say about CESSATION, separately from its outcome.
CESSATION = ("absent", "quiescent", "quiescent-or-absent", "unknown")


def _component(component):
    if component not in COMPONENTS:
        raise ContractRefusal(
            "integrity", "schema",
            f"this build named cessation component {name_value(component)}; "
            f"the components that order a cessation are "
            f"{', '.join(COMPONENTS)}")
    return component


def _outcome(outcome):
    if outcome not in OUTCOMES:
        raise ContractRefusal(
            "integrity", "schema",
            f"this build named cessation outcome {name_value(outcome)}; "
            f"the typed outcomes are {', '.join(sorted(OUTCOMES))}")
    return outcome


def _effects(effects):
    named = tuple(effects)
    bad = [one for one in named if one not in EFFECTS]
    if bad:
        raise ContractRefusal(
            "integrity", "schema",
            f"this build named effects {', '.join(map(name_value, bad))}; "
            f"a cessation record names only {', '.join(EFFECTS)}")
    return list(named)


def token_bound_runtime(store, attempt):
    """The container THIS attempt's governed workspace token bound, or `None`.

    Resolved the way `intake.reclaim_expired_resource` and
    `attempts._order_quiescence` resolve it, and not from the attempt column:
    a governed launch binds a container BEFORE the attempt attaches it, so
    `attempt["runtime_id"]` can be `None` while a real writer exists. An
    identity derived from that column is wrong here, and an earlier revision
    of this Work proposed exactly that mistake and withdrew it.

    Answers `(runtime_id, domain, generation, token)`, every member `None`
    when this attempt has no governed workspace generation at all.
    """
    if attempt["workspace_device"] is None or attempt["workspace_inode"] is None:
        return None, None, None, None
    domain = tokens.domain_of("workspace", tokens.workspace_identity(attempt))
    generation = tokens.generation_of(
        store, domain, execution=attempt["runtime_attempt_id"],
        operation=_attempts._start_operation_id(attempt))
    if generation is None:
        return None, domain, None, None
    token = tokens.token_of(store, domain, generation)
    if token is None:
        return None, domain, generation, None
    return token["container"], domain, generation, token


def _identity(what, attempt, component, generation):
    """THE ONE IDENTITY a cessation record of this kind is journalled under.

    STABLE FOR THE ONE ACT -- the attempt, its fixed assignment, the start
    operation this followed, which component ordered it, and which generation.
    Nothing that can change.

    THE RUNTIME IS DELIBERATELY NOT IN THE IDENTITY, and
    `attempts.start_failure_operation_id` already paid for that lesson: the
    store can only compare a changed signature after the caller selects the
    SAME id, so folding a changeable fact into the id means a different value
    selects a different row and never reaches the collision guard at all. The
    token-bound runtime rides the SIGNATURE, where a difference is refused,
    and the readers below re-prove it against the token.
    """
    boundaries.identity(attempt["runtime_attempt_id"], "an attempt identity")
    return what + ":" + digest({
        "attempt_id": attempt["runtime_attempt_id"],
        "assignment": _attempts._fixed_assignment(attempt),
        "start_operation_id": _attempts._start_operation_id(attempt),
        "component": _component(component),
        "generation": generation,
    })[len("sha256:"):]


def cessation_intent_operation_id(attempt, component, generation):
    return _identity("attempt.cessation-intent", attempt, component, generation)


def cessation_outcome_operation_id(attempt, component, generation,
                                   revision=0):
    """The identity of ONE REVISION of this component's outcome for this generation.

    Revision 0 is the first account and its id is exactly what it was before
    the chain existed. A LATER, DIFFERENT observation does not rewrite it and
    does not collide with it: it is journalled at the next free revision with
    `supersedes` naming the one before, so both are kept and the tip is
    current. That is the correction review340349 item 3 asked for -- an
    uncertain first observation must not be an enduring substitute for a
    later positive one.
    """
    if not isinstance(revision, int) or isinstance(revision, bool) \
            or revision < 0 or revision >= OUTCOME_REVISIONS:
        raise ContractRefusal(
            "integrity", "schema",
            f"this build asked for cessation outcome revision "
            f"{name_value(revision)}; a revision is an integer in "
            f"0..{OUTCOME_REVISIONS - 1}")
    what = "attempt.cessation-outcome"
    base = _identity(what, attempt, component, generation)
    if revision == 0:
        return base
    return base + ":" + str(revision)


def record_and_raise_cessation_intent(store, attempt_id, *, component,
                                      generation, domain, launched,
                                      runtime_id, correlation_id):
    """The intent recording itself, with its refusals RAISED.

    Named apart from the reporting wrapper below so a case can drive the rule
    and see what it answers. Production never calls this directly: a recorder
    that raised into an acting path would substitute its own problem for the
    work it was describing.
    """
    attempt = _attempts._require_attempt(store, attempt_id)
    expect = _attempts._fixed_assignment(attempt)
    start_operation_id = _attempts._start_operation_id(attempt)
    operation_id = cessation_intent_operation_id(attempt, component, generation)
    document = documents.attempt_cessation_intent(
        attempt_id=attempt_id, expect=expect,
        start_operation_id=start_operation_id, component=_component(component),
        domain=domain, generation=generation, launched=bool(launched),
        runtime_id=runtime_id, correlation_id=correlation_id)
    signature = manager_signature("attempt.cessation-intent", dict(document))
    store.transact(operation_id, "attempt.cessation-intent", signature,
                   lambda connection: dict(document))
    return operation_id, document


def _same_account(held, document):
    """Whether a committed revision says exactly what is arriving now.

    Compared on the FACTS and not on the chain coordinates: `revision` and
    `supersedes` are where a record sits, not what it says, so a replay whose
    account matches revision 0 must recognise it even though the arriving
    document has not been given a revision yet.
    """
    mine = {name: value for name, value in document.items()
            if name not in ("revision", "supersedes")}
    theirs = {name: held.get(name) for name in mine}
    # `effects` crosses the journal as a list and arrives here as one; a
    # tuple-vs-list difference is not a different account.
    for name in ("effects",):
        if name in mine:
            mine[name] = list(mine[name] or ())
            theirs[name] = list(theirs[name] or ())
    return mine == theirs


def record_and_raise_cessation_outcome(store, attempt_id, *, component,
                                       generation, runtime_id, correlation_id,
                                       effects, outcome, category=None,
                                       code=None):
    """The outcome recording itself, with its refusals RAISED.

    `cessation` is DERIVED from the typed outcome rather than supplied, so no
    caller can file a stop failure as a cessation. That mapping is `OUTCOMES`
    and it is the single place the two axes meet.

    NO MESSAGE, NO ENGINE TEXT, NO EXCEPTION REPR. Only the typed pair travels
    here. A refusal's prose can quote adapter stderr, and a durable record is
    the last place a live secret should be able to reach -- so the record
    carries what is typed and the acting path keeps the prose.

    AND A LATER, DIFFERENT OBSERVATION SUPERSEDES RATHER THAN COLLIDING.
    review340349 item 3: outcome identity is fixed by facts that cannot
    change, so an UNCERTAIN observation followed by a POSITIVE one used to
    collide under one id and the uncertain account was retained forever. The
    rule now has three branches and each is a different fact:

    * AN EXACT REPLAY RETURNS THE ACCOUNT ALREADY HELD and writes nothing --
      including a replay of a revision that something later superseded, which
      is why the whole chain is compared rather than only its tip.
    * A DIFFERENT ACCOUNT IS APPENDED at the next free revision, carrying
      `supersedes` -- both are kept and the tip is current.
    * A CHAIN AT ITS BOUND REFUSES rather than silently dropping the newer
      evidence or walking forever.

    Nothing here rewrites a committed record, so the first account still
    stands as what the manager knew then; what changed is that it no longer
    stands as what the manager knows NOW.
    """
    attempt = _attempts._require_attempt(store, attempt_id)
    expect = _attempts._fixed_assignment(attempt)
    start_operation_id = _attempts._start_operation_id(attempt)
    document = documents.attempt_cessation_outcome(
        attempt_id=attempt_id, expect=expect,
        start_operation_id=start_operation_id, component=_component(component),
        generation=generation, runtime_id=runtime_id,
        correlation_id=correlation_id, effects=_effects(effects),
        outcome=_outcome(outcome), cessation=OUTCOMES[outcome],
        category=category, code=code, revision=0, supersedes=None)
    previous = None
    for revision in range(OUTCOME_REVISIONS):
        operation_id = cessation_outcome_operation_id(
            attempt, component, generation, revision)
        held = _committed(store, attempt_id, operation_id,
                          "attempt.cessation-outcome",
                          documents.ATTEMPT_CESSATION_OUTCOME)
        if held is None:
            placed = documents.attempt_cessation_outcome(
                **dict(document, revision=revision, supersedes=previous))
            signature = manager_signature("attempt.cessation-outcome",
                                          dict(placed))
            store.transact(operation_id, "attempt.cessation-outcome",
                           signature, lambda connection: dict(placed))
            return operation_id, placed
        if _same_account(held, document):
            # THE ACCOUNT ALREADY HELD, returned as it was written and in the
            # same shape the writing branch answers. Nothing is added to it:
            # a replay that answered a differently-shaped document would make
            # "was this written now" visible to a caller that must not care.
            return operation_id, held
        previous = operation_id
    raise ContractRefusal(
        "integrity", "operation-collision",
        f"attempt {name_value(attempt_id)} already holds "
        f"{OUTCOME_REVISIONS} distinct {name_value(component)} cessation "
        f"outcome records for generation {name_value(generation)}, and this "
        f"one says something different again; the chain is bounded so a "
        f"reader stays bounded, and the newer evidence is refused rather "
        f"than dropped")


# THE ONE PHRASE THAT MARKS A REPORTED RECORDING DEGRADATION, so a caller can
# tell a journalled record from one that was not written WITHOUT parsing prose
# it does not own. `_reported` is the only place that writes it and
# `recording_degraded` the only place that tests it; two spellings of this
# would be two answers to "did the record get written".
DEGRADED = "a cessation record could not be written"


def _reported(what, record, failed):
    """What a never-raising recorder answers, in the shape `attempts` uses.

    A COLLISION IS STILL AN ANSWER about a record that EXISTS, and it is
    marked degraded because the facts arriving now are not the ones on disk.
    After review340349 item 3 the outcome recorder supersedes rather than
    colliding, so the only collision left here is a chain at its bound -- and
    that is newer evidence this manager refused to drop quietly.
    """
    if failed is None:
        return f"; the {what} is journalled as {name_value(record)}"
    if isinstance(failed, ContractRefusal):
        return (f"; and {DEGRADED}: this act already holds a different {what} "
                f"record, which stands: {failed.message}")
    return (f"; and {DEGRADED}: the {what} failed with "
            f"{type(failed).__name__}")


def recording_degraded(reported):
    """Whether a reported sentence says a record was NOT written.

    A RECORDING FAILURE MUST BE OBSERVABLE and not silently stepped over.
    The acting paths carry the sentence into the answer they were already
    going to give; this is how they decide there is something to carry.
    """
    return isinstance(reported, str) and DEGRADED in reported


def ensure_cessation_intent(store, attempt_id, **facts):
    """THE INTENT IS DURABLE BEFORE THE EFFECT IS ORDERED, or no effect is ordered.

    review340349 item 3, and this is the correction. The rejected candidate's
    recorder was documented "NEVER RAISES", returned prose on failure, and
    every acting call site DISCARDED that prose -- two of them ordering an
    effect on the next line. So under a recording failure the effect happened
    with no durable intent, which is exactly the property the design promised
    and did not deliver. Promising durability and delivering best-effort is
    the defect; this answers it by refusing.

    THE RULE HAS EXACTLY TWO OUTCOMES and no silent third:

    * A DURABLE INTENT EXISTS -> the caller proceeds, and the sentence
      answered here is appended to what it reports. A COLLISION SATISFIES
      THIS: the journal refusing because this act already holds a different
      intent record means an intent for this act IS durable, the first
      account stands, and the effect may be ordered. Replay stays honest.
    * NOTHING WAS MADE DURABLE -> this RAISES, and the effect is not ordered.
      The failure is observable because it propagates; it is not stepped over.

    REFUSING BEFORE THE EFFECT WEAKENS NO FENCING AND NO CLEANUP. On the
    cancellation path the Authority fence is already taken and a fenced
    assignment whose runtime was never ordered stopped is an outcome this
    manager ALREADY has a typed answer for; on the settlement path the
    release simply has not happened and the generation stays held. Both are
    states the existing readers describe, and neither invents one.
    """
    # THE VOCABULARY IS PROVED BEFORE THE JOURNAL IS TOUCHED, so a build
    # defect is reported as one rather than as a collision. Conflating them
    # would tell an operator a record already exists when none does.
    _component(facts.get("component"))
    try:
        operation_id, _document = record_and_raise_cessation_intent(
            store, attempt_id, **facts)
    except ContractRefusal as failed:
        if failed.code == "operation-collision":
            return _reported("cessation intent", None, failed)
        raise
    return _reported("cessation intent", operation_id, None)


def record_cessation_outcome(store, attempt_id, **facts):
    """NEVER RAISES, for the reason above. See `record_cessation_intent`."""
    try:
        _component(facts.get("component"))
        _outcome(facts.get("outcome"))
        _effects(facts.get("effects") or ())
    except Exception as failed:                            # noqa: BLE001
        return f"; and the cessation outcome could not be recorded: {failed}"
    try:
        operation_id, _document = record_and_raise_cessation_outcome(
            store, attempt_id, **facts)
    except Exception as failed:                            # noqa: BLE001
        return _reported("cessation outcome", None, failed)
    return _reported("cessation outcome", operation_id, None)


def _read(store, attempt_id, component, what, members, builder):
    """One of this manager's own cessation records, read back and OWNED.

    Held to `attempts._committed_record`'s discipline, which it reuses rather
    than respells: the kind agrees, the answer is decoded through the
    journal's own `replay`, the document is owned against its closed member
    set, and a REFUSED row under this identity is a COLLISION rather than
    evidence -- reading one as a cessation would invent an account out of a
    conflict.

    AND EVERY FACT THE IDENTITY IS DERIVED FROM IS RE-PROVED, plus the
    token-bound runtime that rides the signature. Comparing them re-proves the
    digest's contents instead of trusting that a matching id could only have
    come from matching facts.
    """
    found = _attempts._attempt_row(store, attempt_id)
    if found is None:
        return None
    _component(component)
    bound, _domain, generation, _token = token_bound_runtime(store, found)
    operation_id = builder(found, component, generation)
    record = _committed(store, attempt_id, operation_id, what, members)
    if record is None:
        return None
    for member, mine in (("attempt_id", attempt_id),
                         ("expect", _attempts._fixed_assignment(found)),
                         ("start_operation_id",
                          _attempts._start_operation_id(found)),
                         ("component", component),
                         ("generation", generation)):
        if record[member] != mine:
            raise ContractRefusal(
                "integrity", "schema",
                f"the {what} record for attempt {name_value(attempt_id)} "
                f"names {member} {name_value(record[member])} and this "
                f"attempt now carries {name_value(mine)}; a record describing "
                f"another act cannot say what happened to this one")
    # THE TOKEN-BOUND RUNTIME IS RE-PROVED SEPARATELY, and only when the token
    # still answers one. A generation whose binding this manager can no longer
    # resolve is an absence of evidence rather than a disagreement, and
    # refusing on it would lose a record that is perfectly readable.
    if bound is not None and record["runtime_id"] is not None \
            and record["runtime_id"] != bound:
        raise ContractRefusal(
            "runtime-observation", "identity-mismatch",
            f"the {what} record for attempt {name_value(attempt_id)} names "
            f"runtime {name_value(record['runtime_id'])} and this attempt's "
            f"token now binds {name_value(bound)}; a record about another "
            f"execution cannot say what happened to this one")
    answer = dict(record)
    answer["operation_id"] = operation_id
    return answer


def _committed(store, attempt_id, operation_id, what, members):
    """`attempts._committed_record`'s rule for a kind outside `runtime.*`.

    The shared owner there composes its kind as `runtime.<what>`; these two
    records are `attempt.*`, so the kind is passed whole. Everything the rule
    IS -- the committed state, the kind agreement, the `replay` decode and the
    closed-member ownership -- is identical and is not respelled loosely.
    """
    held = store.operation_record(operation_id)
    if held is None or held["state"] != "committed":
        return None
    if held.get("kind") != what:
        raise ContractRefusal(
            "integrity", "schema",
            f"attempt {name_value(attempt_id)} names operation "
            f"{name_value(operation_id)}, which this manager committed as "
            f"{name_value(held.get('kind'))} rather than a {what} record")
    _found, committed = store.replay(operation_id, held["signature"], kind=what)
    if committed is None:
        raise ContractRefusal(
            "integrity", "schema",
            f"attempt {name_value(attempt_id)} names operation "
            f"{name_value(operation_id)}, which this manager committed with "
            f"no recorded answer for a {what} record")
    return boundaries.document(committed, "a committed cessation record",
                               required=members)


def attempt_cessation_intent_of(store, attempt_id, component):
    """This manager's OWN record that it was about to order a cessation.

    ABSENCE IS THE ORDINARY ANSWER, twice over: a well-formed id naming no
    attempt, and an attempt no component ever ordered stopped under this
    component, are both `None`. A malformed id is a refusal.

    AND AN INTENT IS NOT A STOP. It says this manager was about to ask; it
    says nothing at all about what the engine did, which is why the outcome
    is a separate record and a separate reader.
    """
    return _read(store, attempt_id, component, "attempt.cessation-intent",
                 documents.ATTEMPT_CESSATION_INTENT,
                 cessation_intent_operation_id)


def attempt_cessation_outcome_of(store, attempt_id, component):
    """This manager's OWN record of what the engine answered -- THE CURRENT ONE.

    Same discipline, same absences. `cessation` and `outcome` are read as the
    two separate facts they were written as.

    AND IT ANSWERS THE TIP OF THE SUPERSESSION CHAIN, with `superseded`
    carrying the accounts it replaced in the order they were written. So a
    reader SEES that an uncertain observation was later replaced by a positive
    one, and sees which of the two is current -- rather than being handed the
    uncertain one forever, which is what review340349 item 3 rejected. Every
    revision is held to the same ownership and identity re-proof as the tip:
    a chain is not a reason to trust a record less carefully.
    """
    current = None
    superseded = []
    for revision in range(OUTCOME_REVISIONS):
        found = _read(store, attempt_id, component,
                      "attempt.cessation-outcome",
                      documents.ATTEMPT_CESSATION_OUTCOME,
                      lambda row, which, generation, revision=revision:
                      cessation_outcome_operation_id(row, which, generation,
                                                     revision))
        if found is None:
            break
        if current is not None:
            superseded.append(current)
        current = found
    if current is None:
        return None
    current = dict(current)
    current["superseded"] = tuple(superseded)
    return current


def _known(value, source):
    return {"known": True, "value": value, "source": source}


def _unknown(why):
    """A member nobody established, with a BOUNDED reason.

    A MISSING COUNT IS NEVER A ZERO. An observed zero is `_known(0, ...)` and
    says the manager looked; this says nobody did, or that what was found
    could not be owned.
    """
    return {"known": False, "value": None, "why": why}


def _members_of(held, names, missing, zeroable=()):
    """A whole axis flattened into WRAPPED SCALARS, member by member.

    The owner's numbers are passed through exactly as the owner composed
    them -- this does no arithmetic and derives nothing -- and each one
    arrives with its own source. `zeroable` names the members for which a
    value of `0` or `False` is a REAL ANSWER rather than an absence: a token
    with `renewals=0` was renewed zero times, which is the pilot's exact
    shape, and reporting that as unknown would be the "missing count read as
    a zero" mistake run backwards.
    """
    if held is None:
        return {name: _unknown(missing) for name, _source in names}
    answer = {}
    for name, source in names:
        value = held.get(name)
        if value is None and name not in zeroable:
            answer[name] = _unknown(
                f"this attempt's governed generation records no {name}")
        else:
            answer[name] = _known(value, source)
    return answer


def _revocation(store, domain, generation):
    """The revocation as its OWN owner journalled it -- never inferred.

    `tokens` writes `resource-token.revoked:<domain>:<generation>` with the
    domain, generation, owner, bound container and the `expired_at` that was
    blown, and the store stamps its own `settled_at`. That is durable evidence
    and this reads it rather than deducing a revocation from a reclaim record.
    """
    if domain is None or generation is None:
        return None
    return tokens._document(store, tokens._revoked_id(domain, generation),
                            tokens.REVOKED_KIND)


def _returned(store, domain, generation):
    """The return, journalled on EITHER release path.

    `reclaim_expired_resource`'s own `govern.release` and
    `settle_revoked_resource`'s both journal `resource-token.returned`, which
    is what makes completion attributable regardless of which one ran -- and
    is why this module adds no third completion record of its own.
    """
    if domain is None or generation is None:
        return None
    return tokens._document(store, tokens._returned_id(domain, generation),
                            tokens.RETURNED_KIND)


def attempt_failure_cause_of(store, attempt_id):
    """THE COMPOSED TYPED CAUSE, and an explicit `unknown` that names what is absent.

    Composed from facts their OWNERS already hold and nothing this derives
    itself. Every member is either KNOWN WITH ITS SOURCE or UNKNOWN WITH A
    BOUNDED REASON -- there is no third shape, and a missing count is never
    reported as a zero.

    A HISTORICAL ATTEMPT PREDATING THESE RECORDS REACHES `unknown`, and that
    is correct rather than a shortfall. The answer NAMES which records are
    absent. A cause is never manufactured retrospectively, never recovered by
    reading raw SQL, a secret's contents or a private transcript, and never
    assembled from an exception repr or a guessed timestamp -- and the
    revocation the token journal DOES hold is still reported beside the
    unknown, because an unknown cause is not an unknown everything.

    SNAPSHOT STATE IS EVIDENCE, NEVER A REPLACEMENT FOR CURRENT AUTHORITY.
    What is reported is what was recorded; nothing here lets a stale record
    outrank a current axis read, and nothing here decides a stage.
    """
    found = _attempts._attempt_row(store, attempt_id)
    if found is None:
        return None
    bound, domain, generation, token = token_bound_runtime(store, found)
    absent = []
    cause = None
    for component in COMPONENTS:
        outcome = attempt_cessation_outcome_of(store, attempt_id, component)
        intent = attempt_cessation_intent_of(store, attempt_id, component)
        if outcome is None and intent is None:
            absent.append(f"attempt.cessation-*:{component}")
            continue
        composed = {"component": _known(component, "failure_cause"),
                    "operation_id": _known(
                        (outcome or intent)["operation_id"],
                        "failure_cause.cessation_" +
                        ("outcome" if outcome is not None else "intent") +
                        "_operation_id")}
        if outcome is None:
            # INTENT WITHOUT AN OUTCOME IS EXACTLY THE CRASH THE INTENT EXISTS
            # FOR, and it is reported as what it is. The manager ordered this
            # container stopped and no outcome was ever recorded; inferring a
            # stop from that would be inferring an effect from an intent.
            composed.update({
                "outcome": _known("ordered-without-outcome", "failure_cause"),
                "cessation": _known("unknown", "failure_cause"),
                "correlation_id": _known(intent["correlation_id"],
                                         "attempt.cessation-intent"),
                "runtime_id": (_known(intent["runtime_id"],
                                      "attempt.cessation-intent")
                               if intent["runtime_id"] is not None else
                               _unknown("this component resolved no runtime "
                                        "identity to order stopped")),
                "effects": _unknown("no outcome was recorded, so what this "
                                    "pass actually ordered is unknown"),
                "category": _unknown("no outcome was recorded"),
                "code": _unknown("no outcome was recorded"),
                "superseded": _known(0, "attempt.cessation-outcome")})
        else:
            composed.update({
                "outcome": _known(outcome["outcome"],
                                  "attempt.cessation-outcome"),
                "cessation": _known(outcome["cessation"],
                                    "attempt.cessation-outcome"),
                "correlation_id": _known(outcome["correlation_id"],
                                         "attempt.cessation-outcome"),
                "runtime_id": (_known(outcome["runtime_id"],
                                      "attempt.cessation-outcome")
                               if outcome["runtime_id"] is not None else
                               _unknown("this component resolved no runtime "
                                        "identity to order stopped")),
                # WHAT THIS PASS ACTUALLY ORDERED, and `()` is a KNOWN EMPTY
                # rather than an unknown: a replayed reclaim that observed an
                # exact absence ordered nothing, and the record says so.
                "effects": _known(tuple(outcome["effects"] or ()),
                                  "attempt.cessation-outcome"),
                "category": (_known(outcome["category"],
                                    "attempt.cessation-outcome")
                             if outcome["category"] is not None else
                             _unknown("this outcome carries no typed refusal "
                                      "category")),
                "code": (_known(outcome["code"], "attempt.cessation-outcome")
                         if outcome["code"] is not None else
                         _unknown("this outcome carries no typed refusal "
                                  "code")),
                # HOW MANY EARLIER ACCOUNTS THIS ONE REPLACED. A known zero
                # says the first account is still current; it is not a
                # missing count.
                "superseded": _known(len(outcome.get("superseded") or ()),
                                     "attempt.cessation-outcome")})
        # WHETHER AN INTENT WAS RECORDED AT ALL, beside the outcome and never
        # instead of it. An outcome with no intent is a record written by a
        # build that did not yet promise durability, which is a different
        # fact from a crash between the two.
        composed["intent_recorded"] = _known(intent is not None,
                                             "attempt.cessation-intent")
        # THE LAST COMPONENT TO ACT WINS ONLY WHEN IT ESTABLISHED SOMETHING.
        # Cancellation may fence and resolve nothing while expiry reclaim
        # already proved an absence, and a composition that preferred the
        # later record would lose the established fact.
        if cause is None or (cause["cessation"]["value"] == "unknown"
                             and composed["cessation"]["value"] != "unknown"):
            cause = composed
    revoked = _revocation(store, domain, generation)
    returned = _returned(store, domain, generation)
    if revoked is None:
        absent.append(f"{tokens.REVOKED_KIND}:{domain}:{generation}"
                      if domain is not None else tokens.REVOKED_KIND)
    start_failure = _attempts.attempt_start_failure_of(store, attempt_id)
    preparation = _attempts.attempt_preparation_failure_of(store, attempt_id)
    if start_failure is None:
        absent.append("runtime.start-failed")
    if preparation is None:
        absent.append("runtime.preparation-failed")
    unknown = None
    if cause is None and start_failure is None and preparation is None:
        # AND THE ABSENCE OF A START-FAILURE OR PREPARATION-FAILURE RECORD IS
        # EXPECTED for the components this composition is about -- it is not
        # proof of any proposed cause. The reason is bounded and names the
        # records rather than guessing why they are not there.
        unknown = {"why": "no component of this manager recorded ordering a "
                          "cessation for this attempt, and no start or "
                          "preparation failure is recorded either; which "
                          "component ended it, if any did, is unknown",
                   "absent": tuple(absent)}
    return {
        # THE OWNED, VERSIONED SHAPE. The same string travels into ordinary
        # status and is asserted by the report, so a newer producer does not
        # silently satisfy an older reader and an older document reads as
        # unknown rather than failing.
        "schema": DIAGNOSTIC_SCHEMA,
        "attempt_id": attempt_id,
        "cause": cause,
        "unknown": unknown,
        "absent_records": tuple(absent),
        # EVERY LEAF BELOW IS A WRAPPED SCALAR, which is what makes one shape
        # possible on all three sides. The owners' DOCUMENTS are deliberately
        # not forwarded: a status member that carried somebody else's whole
        # document would be this composition republishing a shape it does not
        # own, and the report would have to forward a nested object to show
        # it. What travels is the named facts, each with its source.
        "start_failure_recorded": _known(
            start_failure is not None, "attempts.attempt_start_failure_of"),
        "start_failure_runtime_id": (
            _known(start_failure.get("runtime_id"),
                   "attempts.attempt_start_failure_of")
            if start_failure is not None
            and start_failure.get("runtime_id") is not None else
            _unknown("this manager recorded no failed start naming a runtime "
                     "for this attempt")),
        "preparation_failure_recorded": _known(
            preparation is not None,
            "attempts.attempt_preparation_failure_of"),
        "preparation_failure_runtime_id": (
            _known(preparation.get("runtime_id"),
                   "attempts.attempt_preparation_failure_of")
            if preparation is not None
            and preparation.get("runtime_id") is not None else
            _unknown("this manager recorded no failed preparation naming a "
                     "runtime for this attempt")),
        # READ FROM THE TOKEN JOURNAL RATHER THAN INFERRED. A reclaim record
        # is not a revocation and must not be read as one. Reported beside an
        # unknown cause, because an unknown cause is not an unknown
        # everything.
        "revocation": _known(revoked is not None,
                             f"tokens:{tokens.REVOKED_KIND}")
        if revoked is not None else
        _unknown("no revocation is journalled for this attempt's governed "
                 "generation"),
        "revoked_expired_at": (
            _known(revoked.get("expired_at"), f"tokens:{tokens.REVOKED_KIND}")
            if revoked is not None else
            _unknown("no revocation is journalled for this attempt's "
                     "governed generation")),
        "revoked_container": (
            _known(revoked.get("container"), f"tokens:{tokens.REVOKED_KIND}")
            if revoked is not None and revoked.get("container") is not None
            else _unknown("no revocation naming a bound container is "
                          "journalled for this generation")),
        "revoked_owner": (
            _known(revoked.get("owner"), f"tokens:{tokens.REVOKED_KIND}")
            if revoked is not None and revoked.get("owner") is not None else
            _unknown("no revocation naming an owner is journalled for this "
                     "generation")),
        # COMPLETION ON EITHER RELEASE PATH, from the one record both write --
        # which is why a captured intent or outcome does not disappear because
        # completion happened on the other one.
        "completion": _known(returned is not None,
                             f"tokens:{tokens.RETURNED_KIND}")
        if returned is not None else
        _unknown("this generation's resource token has not been returned"),
        "domain": (_known(domain, "tokens.domain_of") if domain is not None
                   else _unknown("this attempt names no workspace object")),
        "generation": (_known(generation, "tokens.generation_of")
                       if generation is not None else
                       _unknown("no generation of this domain names this "
                                "execution")),
        # THE TOKEN AXIS, FACT BY FACT AND WITH NO ARITHMETIC. An expiry with
        # `renewals=0` against a Job that allowed a longer provider turn is
        # the pilot's exact shape, and it is legible here without the reader
        # computing anything: the count, the limit, the lifetime, both
        # deadlines and the judged instant are each passed through as their
        # owner composed them. A KNOWN ZERO renewals is not a missing count.
        "token": _members_of(token, (
            ("owner", "tokens.token_of"),
            ("container", "tokens.token_of"),
            ("expires_at", "tokens.token_of"),
            ("acquired_expires_at", "tokens.token_of"),
            ("renewed_at", "tokens.token_of"),
            ("renewals", "tokens.token_of"),
            ("renewals_remaining", "tokens.token_of"),
            ("expired", "tokens.token_of"),
            ("expiry_judged_at", "tokens.token_of"),
            ("returned", "tokens.token_of"),
            ("activating", "tokens.token_of"),
            ("launch", "tokens.token_of"),
        ), "this attempt has no governed workspace generation", zeroable=(
            "renewals", "renewals_remaining")),
        # AND THE CEILINGS THE TOKEN AXIS IS READ AGAINST, so `renewals=0`
        # against a limit of four is one read rather than two.
        "renewal_limit": _known(tokens.RENEWAL_LIMIT,
                                "tokens.RENEWAL_LIMIT"),
        "lifetime_seconds": _known(tokens.LIFETIME_SECONDS,
                                   "tokens.LIFETIME_SECONDS"),
        "execution": {
            "execution_runtime": _known(found["execution_runtime"], "attempts"),
            "cleanup": _known(found["cleanup"], "attempts"),
            "observed_at": (_known(found["observed_at"], "attempts")
                            if found["observed_at"] is not None else
                            _unknown("nobody has observed this attempt")),
            "runtime_id": (_known(found["runtime_id"], "attempts")
                           if found["runtime_id"] is not None else
                           _unknown("no runtime is attached to this attempt")),
            # THE TOKEN-BOUND CONTAINER IS REPORTED BESIDE THE ATTACHED ONE
            # and never instead of it. They differ exactly in the interval
            # this whole module exists to describe.
            "token_bound_runtime_id": (
                _known(bound, "tokens.token_of") if bound is not None else
                _unknown("this attempt's governed generation binds no "
                         "container")),
            # AN OBSERVED ZERO IS A KNOWN ZERO. `activity_bytes` is `None`
            # when nobody has observed the stream and `0` when somebody
            # observed it empty, and the two are not interchangeable.
            "activity_bytes": (_known(found["activity_bytes"], "attempts")
                               if found["activity_bytes"] is not None else
                               _unknown("no session stream has been observed")),
            "activity_at": (_known(found["activity_at"], "attempts")
                            if found["activity_at"] is not None else
                            _unknown("no session stream has been observed")),
        },
        # SAFE LOCATORS ONLY. Device and inode identify a workspace OBJECT and
        # are not a path and not a retained-output locator by themselves; the
        # supported read is the deployed `logs` subcommand over
        # `worker_manager.attempt_logs`, whose delivery root is an operand
        # only the operator can supply.
        "workspace_object": {
            "device": (_known(found["workspace_device"], "attempts")
                       if found["workspace_device"] is not None else
                       _unknown("no workspace object is recorded")),
            "inode": (_known(found["workspace_inode"], "attempts")
                      if found["workspace_inode"] is not None else
                      _unknown("no workspace object is recorded")),
            "is_a_locator": False,
            "why": "a device and inode identify a workspace object; they are "
                   "not a path and resolve no retained output on their own",
        },
    }
