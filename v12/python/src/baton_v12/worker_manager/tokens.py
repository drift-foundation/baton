"""The shared resource token — Baton's exclusive expiring permission to act.

W275617 / audit G1, under `v12/DESIGN.md`
7f504a5edbb46acae739cab0727173fc1c51098300ae8048d25b56bba274cee0. ONE owner for
every resource token, so that allocation, custody, removal, context and review all
ask the same authority rather than each carrying a lease of its own.

THE CONFLICT DOMAIN IS THE RESOURCE, NOT THE ATTEMPT, and review
2026-09-26T13:29:00Z is why that sentence is first. My dossier proposed a domain
"derived from an attempt", which would have given the same workspace a fresh domain
per attempt and quietly let two attempts hold one resource at once -- an escape
hatch dressed as an identity. So the domain names the governed resource and outlives
every attempt that competes for it; the attempt rides in the token's OWNERSHIP and
its launch binding, where it belongs (TOK-2).

WHAT THIS MODULE DOES NOT DO, deliberately. It performs no filesystem work, starts
no container and stops none: it decides permission and records evidence. The
governed effects belong behind a token-bound maintenance execution (TOK-7), which is
G2, and the removal consumer is G3. Both are excluded from this Work by owner 275617.
"""
from ..contracts import ContractRefusal
from ..contracts.errors import name_value
from . import boundaries

# THE PROFILE CHOICES, NAMED HERE RATHER THAN BURIED IN A CALL. Review
# 2026-09-26T13:29:00Z: these are author-proposed implementation profile values, not
# owner rulings, and their effective semantics are recorded with them.
#
#   LIFETIME  how long an acquisition owns the resource before it is overdue.
#   GRACE     how long after a stop request a cessation answer may still arrive
#             before the outcome counts as UNKNOWN -- and unknown is held, never
#             presumed stopped.
#   RENEWALS  the bound on extensions of one generation. Exhaustion does not free
#             the resource; it means the holder must finish or be revoked.
#   VERSION   the token record shape, so a later change is a migration rather than
#             a silent reinterpretation.
LIFETIME_SECONDS = 900
STOP_GRACE_SECONDS = 30
RENEWAL_LIMIT = 4
TOKEN_VERSION = 1

ACQUIRED_KIND = "resource-token.acquired"
LAUNCH_KIND = "resource-token.launch"
BOUND_KIND = "resource-token.bound"
RETURNED_KIND = "resource-token.returned"
# W275774 review 15:00:16Z: THE IN-FLIGHT ACTIVATION IS ITSELF A DURABLE FACT.
#
# An independent probe defeated the previous argument exactly: a permission was
# read, another host then settled the inert container and took generation 2, and
# the suspended starter activated generation 1's container afterwards -- two
# holders of one resource. "Expiry does not free the token" was true and did not
# help, because SETTLEMENT frees it, and settlement was allowed to happen under a
# live activation.
#
# So an activation is admitted before the engine is asked, and the admission is a
# record rather than a boolean somebody computed. While it is unresolved the
# resource cannot be handed on: `returned` refuses. The hold ends when the
# activation's outcome is settled, which is the conclusive external answer the
# review required rather than a timeout or an assumption.
ACTIVATING_KIND = "resource-token.activating"
ACTIVATION_SETTLED_KIND = "resource-token.activation-settled"
# W275774 review 16:37:09Z: EXPIRY IS NOT SELF-EXECUTING.
#
# An expired generation stops being ENTITLED to act, and that is all it does: TOK-5
# says the resource is revoked rather than replaced, because the container may still
# be running and the workspace may still be written. So reclaiming an overdue
# resource is four acts and not one -- REVOKE the entitlement durably, STOP the
# container, POSITIVELY CONFIRM it is gone, and only then SETTLE the return. The
# revocation is the first of them and it is journalled, so the old holder is refused
# at its next journal-guarded step instead of racing the reclaim.
REVOKED_KIND = "resource-token.revoked"
# W275775 (Child B), TOK-9: ONE RECORD PER REVISION OF ONE GENERATION'S DEADLINE.
#
# The identity carries the revision rather than only the generation, which is what makes a
# renewal both replayable and non-repeatable: asking again for revision 3 answers the
# committed revision 3, and asking for a revision that is not the next one cannot reach a
# write at all. A single `renewed:<domain>:<generation>` id would have had to choose between
# those two properties.
RENEWED_KIND = "resource-token.renewed"
# W275775 review 2026-09-27T02-43-54Z [P1]: THE EXPIRY DECISION, MADE DURABLE.
#
# A deadline compared against the wall clock is a decision that can be UNMADE: the probe
# advanced the host clock past a token's deadline, watched `renew` refuse it as expired, moved
# the same clock back, and renewed it. TOK-9 forbids exactly that -- "no heartbeat, late
# renewal request or clock adjustment revives the token" -- and also says ambiguous timing
# means hold, so a request arriving on a clock that has gone backwards is not a licence.
#
# So the first act that JUDGES a generation expired records that judgement, and from then on
# the fact is the record rather than the arithmetic. It is written by the act that made the
# decision, in its own short transaction, and it is read by every later act.
#
# WHAT IT DOES NOT DO, because the whole point of TOK-5 is that expiry is not permission:
# it frees nothing, returns nothing, and stops no container. It also does not block the
# SETTLEMENT paths -- a revocation, a manager return on confirmed cessation and a reclaim all
# still act on an expired generation, which is the only way a held resource is ever released.
# What it blocks is REVIVAL.
EXPIRED_KIND = "resource-token.expired"
# W275775 review 2026-09-27T03-12-19Z [C1]: AND THE THIRD ANSWER, WHICH TOK-9 NAMES.
#
# "Ambiguous timing means hold/reconcile." The reviewer's counterexample is exactly that
# ambiguity: a request observed its deadline had passed, and before the decision could be
# recorded the host clock moved BACKWARDS, so at the moment of writing the token was not
# expired -- and a conditional write that simply declined left the caller refused and the
# next attempt free to renew. Neither "expired" nor "live" is the truth there; the truth is
# that this manager's timing cannot be trusted for this generation, and the honest outcome is
# a durable HOLD rather than a guess in either direction.
#
# LIKE THE EXPIRY JUDGEMENT, IT IS A DECISION AND NOT A CONSEQUENCE: it frees nothing, returns
# nothing and stops nothing. What it does is refuse further RENEWAL until the ambiguity is
# reconciled, so a clock that went backwards cannot be used to buy time.
TIMING_AMBIGUOUS_KIND = "resource-token.timing-ambiguous"


def domain_of(resource_kind, identity):
    """The stable conflict domain for one governed resource.

    Two attempts, two aliases and two overlapping uses of one resource MUST resolve
    to the same string, because that string is what acquisition serializes on. It is
    deliberately independent of attempt, assignment and generation: a resource does
    not become free by being asked for under a new name.

    `resource_kind` is the family whose owner defines the identity -- `workspace`,
    `line`, `context`, `custody` -- and `identity` is that owner's canonical
    identity for the exact resource. Callers pass an identity their own owner
    already validated; composing one here would make this module a second authority
    on what a workspace or a line is.
    """
    kind = boundaries.text(resource_kind, "a governed resource kind")
    identity = boundaries.text(identity, "a governed resource identity")
    if ":" in kind:
        raise ContractRefusal(
            "integrity", "schema",
            f"a governed resource kind is a single family name; {name_value(kind)} "
            f"carries a separator and would make two different resources collide")
    return f"{kind}:{identity}"


def _acquired_id(domain, generation):
    return f"{ACQUIRED_KIND}:{domain}:{generation}"


def _launch_id(domain, generation):
    return f"{LAUNCH_KIND}:{domain}:{generation}"


def _bound_id(domain, generation):
    return f"{BOUND_KIND}:{domain}:{generation}"


def _activating_id(domain, generation):
    return f"{ACTIVATING_KIND}:{domain}:{generation}"


def _activation_settled_id(domain, generation):
    return f"{ACTIVATION_SETTLED_KIND}:{domain}:{generation}"


def _revoked_id(domain, generation):
    return f"{REVOKED_KIND}:{domain}:{generation}"


def _expired_id(domain, generation):
    return f"{EXPIRED_KIND}:{domain}:{generation}"


def _ambiguous_id(domain, generation):
    return f"{TIMING_AMBIGUOUS_KIND}:{domain}:{generation}"


def _renewed_id(domain, generation, revision):
    return f"{RENEWED_KIND}:{domain}:{generation}:{revision}"


def _returned_id(domain, generation):
    return f"{RETURNED_KIND}:{domain}:{generation}"


def _document(control, operation_id, kind):
    """A committed record's own document, read back through `replay`.

    Never the `result` column read raw: `replay` recomputes the signature, so a row
    edited in place to name another owner or container no longer answers.
    """
    found = control.operation_record(operation_id)
    if found is None:
        return None
    _, document = control.replay(operation_id, found["signature"], kind=kind)
    return document


def outstanding(control, domain):
    """Every generation of this domain that has been acquired and not returned.

    Read by derived identity rather than by scanning a table, which is this build's
    rule for operation records: another deployment's rows are invisible to it. An
    acquisition with no return is OUTSTANDING whatever became of its holder -- that
    is the held state an interrupted execution must leave behind, and nothing here
    guesses that a vanished holder finished.
    """
    held = []
    generation = 1
    while True:
        acquired = _document(control, _acquired_id(domain, generation), ACQUIRED_KIND)
        if acquired is None:
            return held
        if _document(control, _returned_id(domain, generation), RETURNED_KIND) is None:
            held.append(acquired)
        generation += 1


def _renewals_of(control, domain, generation):
    """Every committed renewal of this generation, in revision order.

    W275775. READ FROM THE JOURNAL BY DERIVED IDENTITY, like every other token fact:
    revision 1 is the first renewal, and the walk stops at the first absent one, so a
    record written under some other identity cannot lengthen a lifetime here.
    """
    found = []
    revision = 1
    while True:
        document = _document(control, _renewed_id(domain, generation, revision),
                             RENEWED_KIND)
        if document is None:
            return found
        found.append(document)
        revision += 1


def token_of(control, domain, generation):
    """This generation as it now stands: terms, launch, container and return.

    W275775: AND ITS CURRENT DEADLINE, which is the acquisition's only until a renewal
    moves it. This is the single place the effective deadline is composed, so `revoke`,
    `_owning`, `Governance.overdue` and the conflict message all arbitrate against the
    SAME current state rather than each against the acquisition -- which is what TOK-9
    means by renewal and expiry competing against that state. A reader that kept the
    acquisition's own `expires_at` would have made every renewal cosmetic.
    """
    acquired = _document(control, _acquired_id(domain, generation), ACQUIRED_KIND)
    if acquired is None:
        return None
    launch = _document(control, _launch_id(domain, generation), LAUNCH_KIND)
    bound = _document(control, _bound_id(domain, generation), BOUND_KIND)
    answer = dict(acquired)
    answer["launch"] = (launch or {}).get("launch")
    answer["container"] = (bound or {}).get("container")
    answer["returned"] = _document(control, _returned_id(domain, generation),
                                   RETURNED_KIND) is not None
    admitted = _document(control, _activating_id(domain, generation),
                         ACTIVATING_KIND)
    settled = _document(control, _activation_settled_id(domain, generation),
                        ACTIVATION_SETTLED_KIND)
    answer["activating"] = admitted is not None and settled is None
    answer["activation_started"] = None if settled is None else settled["started"]
    # W275775: THE RENEWED DEADLINE REPLACES THE ACQUIRED ONE, and the acquisition's is
    # kept beside it rather than overwritten: a restart reconciling a token needs to know
    # what it was granted originally as well as what it is owed now.
    renewals = _renewals_of(control, domain, generation)
    answer["acquired_expires_at"] = acquired["expires_at"]
    answer["renewals"] = len(renewals)
    answer["revision"] = len(renewals)
    if renewals:
        answer["expires_at"] = renewals[-1]["expires_at"]
        answer["renewed_at"] = renewals[-1]["renewed_at"]
    else:
        answer["renewed_at"] = None
    answer["renewals_remaining"] = max(0, RENEWAL_LIMIT - len(renewals))
    # W275775 [P1]: A JUDGED EXPIRY IS STICKY, and this reader says so. Without the record
    # this answered the arithmetic alone, so a clock that went backwards made a token that
    # had already been judged expired look live again -- and a reader that contradicts an
    # authoritative decision is how a caller talks itself into reviving one.
    judged = _document(control, _expired_id(domain, generation), EXPIRED_KIND)
    answer["expiry_judged_at"] = None if judged is None else judged["observed_at"]
    answer["expired"] = judged is not None or control._now() >= answer["expires_at"]
    # W275775 [C1]: AND WHETHER THIS MANAGER CAN SAY WHAT TIME IT IS for this generation. A
    # reader that hid an ambiguity hold would let a caller believe a live token is simply
    # live, when what actually stands is "held until somebody reconciles the timing".
    unsure = _document(control, _ambiguous_id(domain, generation),
                       TIMING_AMBIGUOUS_KIND)
    answer["timing_ambiguous"] = unsure is not None
    answer["timing_observed_at"] = None if unsure is None else unsure["observed_at"]
    answer["timing_decided_at"] = None if unsure is None else unsure["decided_at"]
    answer["revoked"] = _document(control, _revoked_id(domain, generation),
                                  REVOKED_KIND) is not None
    return answer


def acquire(control, domain, *, operation, execution, attempt=None,
            seconds=LIFETIME_SECONDS, eligible=None):
    """Take exclusive permission for this resource, atomically, in one short write.

    EVERYTHING HERE IS DATABASE WORK, which is DB-1 and DB-3: eligibility, the
    conflict read and the acquisition are one transaction, and the caller's external
    work happens after it commits. `eligible` is a PURE-SQL predicate the resource's
    own owner supplies -- it is called inside this transaction and must not touch a
    filesystem, an engine or another store. That restriction is stated because the
    tempting shape, passing a callback that checks a directory, is exactly the defect
    DB-2 names.

    ANOTHER GENERATION OUTSTANDING REFUSES, whether it is live, expired or
    uncertain: expiry is not permission to replace (TOK-6), and the revocation path
    that can end an expired generation is a later G1 step, not an implicit effect of
    asking again.
    """
    boundaries.text(domain, "a governed conflict domain")
    operation = boundaries.text(operation, "a token operation identity")
    execution = boundaries.text(execution, "a token execution identity")
    if attempt is not None:
        boundaries.identity(attempt, "an assignment identity")
    if eligible is not None:
        boundaries.capability(eligible, "a pure-database eligibility predicate")
    # NO `uuid` AT ALL, AND THAT IS THE BETTER ANSWER RATHER THAN A WORKAROUND.
    #
    # `test_dependencies`' ruled-import check flagged `uuid`, and the allowlist is a
    # CURATED standard-library set, not an oversight -- widening it would be weakening the
    # check the reviewer told me not to weaken. Moving the import inside the function did
    # not help either: the rule walks every `ast.Import`, function-local ones included.
    #
    # So the owner is DERIVED instead of drawn, over EXACTLY these inputs: the domain, the
    # operation, the execution, the acquiring instant and this manager's incarnation.
    #
    # THE GENERATION IS NOT AMONG THEM, and review 2026-09-26T14:01:00Z was right to make
    # me say so: my first comment listed it, but the generation is not known until the
    # walk below has run inside the transaction, and the owner is computed before the lock.
    # Prose that names an input the code does not use is the kind of claim this Work keeps
    # catching in my writing, so the list above is the code's list.
    #
    # Uniqueness therefore rests on the INSTANT distinguishing two acquisitions of one
    # domain by one operation and execution. That is sound here because a replay of the
    # same operation returns the original record rather than computing a second owner --
    # the walk below sees to it -- so two distinct owners for one (domain, operation,
    # execution) triple cannot both be recorded.
    #
    # An owner is an IDENTITY, not a secret: unpredictability was never the requirement,
    # which is why a digest replaces the entropy source rather than approximating it. The
    # marker below still reads "the randomness is prepared outside the transaction"; that
    # sentence is now about the DIGEST, and there is no randomness left in this path.
    import hashlib

    from .store import _recorded, manager_signature

    # (4) THE OWNER IS COMPUTED OUTSIDE THE TRANSACTION. Review
    # 2026-09-26T13:41:00Z found `uuid.uuid4()` running inside `BEGIN IMMEDIATE`, and OS
    # randomness is external to the database decision -- DB-1 does not carve out
    # "small" external reads. It is drawn here, before the lock, and only used inside.
    taken_at = control._now()
    proposed_owner = hashlib.sha256("\n".join((
        "baton-v12-resource-token", domain, operation, execution, taken_at,
        str(getattr(control, "incarnation", "")))).encode("utf-8")).hexdigest()
    connection = control._connection
    connection.execute("BEGIN IMMEDIATE")
    try:
        # (3) THE SAME OPERATION RESOLVES TO ITS OWN ACQUISITION, ACROSS RETIREMENT, and
        # with its complete canonical operands bound.
        #
        # Review 2026-09-26T13:50:00Z caught my first fix scanning only `outstanding`, so a
        # RETURNED operation acquired generation 2 -- a completed act taking fresh
        # permission, which is the opposite of replay. And it compared only the execution,
        # so a changed attempt or a changed lifetime replayed silently under one identity.
        # DB-7: "Same ID/same operands replays; changed operands refuse."
        #
        # So the walk covers every generation, returned or not, and the comparison is the
        # full operand set this acquisition was recorded under.
        offered = {"execution": execution, "attempt": attempt, "seconds": seconds}
        generation = 1
        while True:
            recorded = _document(control, _acquired_id(domain, generation), ACQUIRED_KIND)
            if recorded is None:
                break
            if recorded["operation"] == operation:
                against = {member: recorded.get(member) for member in offered}
                if against != offered:
                    raise ContractRefusal(
                        "refused", "operation-collision",
                        f"operation {name_value(operation)} already acquired generation "
                        f"{recorded['generation']} of {name_value(domain)} under "
                        f"{against!r} and is now offered {offered!r}; an operation whose "
                        f"operands changed is a different act wearing the first one's name")
                # THE ORIGINAL DURABLE OUTCOME, whatever became of it since. A returned
                # generation replays as itself and acquires nothing.
                connection.execute("COMMIT")
                return dict(recorded)
            generation += 1
        for held in outstanding(control, domain):
            raise ContractRefusal(
                "refused", "precondition",
                f"resource {name_value(domain)} is owned by token generation "
                f"{held['generation']} (operation {name_value(held['operation'])}, "
                f"execution {name_value(held['execution'])}, expires "
                f"{name_value(_deadline_of(control, domain, held['generation'], held))}) "
                f"and that token has not been "
                f"returned; an outstanding baton excludes every conflicting "
                f"acquisition, and an expired one is revoked rather than replaced")
        if eligible is not None:
            refusal = eligible(connection)
            if refusal is not None:
                raise ContractRefusal("refused", "precondition", refusal)
        taken = taken_at
        document = {"version": TOKEN_VERSION, "domain": domain,
                    "generation": generation, "operation": operation,
                    "execution": execution, "attempt": attempt,
                    # THE LIFETIME IS A RECORDED OPERAND, not only an input to the expiry,
                    # because replay has to compare what this acquisition was asked for.
                    "seconds": seconds,
                    "owner": proposed_owner, "renewals": 0,
                    "acquired_at": taken,
                    "expires_at": boundaries.deadline(taken, seconds,
                                                      "a resource token expiry")}
        control._record(_acquired_id(domain, generation), ACQUIRED_KIND,
                        manager_signature(ACQUIRED_KIND, document),
                        "committed", _recorded(document), None)
        connection.execute("COMMIT")
    except BaseException:
        try:
            connection.execute("ROLLBACK")
        except Exception:
            pass
        raise
    return document


def renew(control, token, *, execution, operation, expected_revision,
          seconds=LIFETIME_SECONDS):
    """Extend THIS generation's deadline, once, against the state it names.

    W275775, TOK-9: "The host MAY explicitly renew a still-unexpired, unrevoked token for
    the same resource, generation, operation and execution under the selected bounded
    policy. Renewal is an atomic conditional control-store decision with a durable
    operation ID, expected deadline revision and recorded new deadline."

    EXPLICIT, NOT IMPLICIT. There is no heartbeat here and no timer: a caller asks for an
    extension and either gets exactly one or is refused. TOK-9's first paragraph is the
    reason -- "Heartbeats report liveness; they do not implicitly extend a token" -- and the
    shape of this function is that sentence: nothing about observing a live worker reaches
    this code, and nothing here can be reached without asking.

    `expected_revision` IS THE CONDITION, AND IT IS THE REVISION THE PUBLIC READER RETURNS.
    W275775 review 2026-09-27T02-43-54Z: my first cut described the acquisition as revision 0
    and then required a positive input, so a caller that did the obvious thing --
    `renew(..., expected_revision=token_of(...)["revision"])` -- was refused on its very
    first call, and prose and code held opposite conventions. They now hold one:
    `expected_revision` IS `token_of(...)["revision"]`, the number of renewals this generation
    has committed. An unrenewed generation stands at 0 and its first renewal is asked for with
    0; the record that renewal writes is revision 1, which is what the reader then returns.

    A caller that believes the deadline is older than it is names a revision that is already
    committed, and `transact` answers THAT record rather than writing a new one -- so a retry
    after a lost reply returns the extension that already happened instead of extending a
    second time, which is TOK-9's "same-operation replay returns the recorded renewal without
    extending again" and "a lost renewal reply grants nothing beyond the committed authority
    state". A caller that names a revision further ahead than the state is refused: a renewal
    cannot skip the state it claims to have observed.

    WHAT IT CANNOT DO, and each is a refusal rather than a silent no-op:

      * revive an EXPIRED generation. Once the deadline has passed, expiry has won and
        TOK-9 is explicit that no late request revives it. THE REFUSAL ITSELF IS NOT
        JOURNALLED -- no refused operation row is written and the request stays retryable --
        but the EXPIRY it discovered is recorded, conditionally, by `_judge_expired`: see
        `_judging`. W275775 review 2026-09-27T03-02-01Z asked for this sentence to be
        corrected rather than left saying "non-durable" beside a judgement that commits. What
        the record changes is only that the timing fact can no longer be argued with; the
        resource stays exactly as held as it was, nothing is returned and nothing is
        replaced.
      * act on a REVOKED or RETURNED generation, for the same reason `_owning` refuses
        every other late act on one.
      * cross EXECUTION or OPERATION. Renewal is for "the same resource, generation,
        operation and execution"; a different execution asking is not a renewal, it is a
        second holder asking for somebody else's permission.
      * exceed the bounded policy. `RENEWAL_LIMIT` is that bound, and its recorded
        semantics are followed exactly: exhaustion does NOT free the resource, it means
        this holder must finish or be revoked, so the refusal leaves the token held.
      * create a writer or move a Job limit. This writes one record and touches nothing
        else -- no lane, no attempt row, no allocation -- which is TOK-9's "It does not
        create a new writer or reset Job execution limits".

    ONE SHORT WRITE, NO EXTERNAL I/O. DB-1: the whole decision is database work inside one
    `transact`, and the deadline is computed from the store's own clock rather than from
    anything a caller supplied.
    """
    from .store import manager_signature

    execution = boundaries.text(execution, "a token execution identity")
    operation = boundaries.text(operation, "a token operation identity")
    revision = _observed_revision(expected_revision)
    domain = boundaries.text(token["domain"], "a governed conflict domain")
    generation = token["generation"]
    what = (f"renewing generation {generation} of {name_value(domain)}")
    # THE OWNER, THE LIFECYCLE AND THE CURRENT DEADLINE, through the same gate every other
    # late act passes: `_owning` re-reads the acquisition, refuses a revoked, returned or
    # EXPIRED generation, and answers the committed record rather than the caller's copy.
    # ONE GATE AROUND THE WHOLE ATTEMPT, so expiry found in the preflight and expiry found
    # under the write lock have the SAME durable semantics -- see `_judging`.
    return _judging(control, domain, generation,
                    lambda: _extended(control, token, domain, generation, what,
                                      execution, operation, revision, seconds, held=None))


def _extended(control, token, domain, generation, what, execution, operation,
              revision, seconds, held=None):
    """The renewal attempt itself: every condition, then one conditional write.

    Split out of `renew` so the expiry judgement can wrap the WHOLE attempt rather than only
    its preflight -- W275775 review 2026-09-27T03-02-01Z asked for exactly that equivalence.
    """
    from .store import manager_signature

    held = _owning(control, token, what)
    if held["execution"] != execution or held["operation"] != operation:
        raise ContractRefusal(
            "runtime-observation", "identity-mismatch",
            f"{what} was asked for execution {name_value(execution)} under operation "
            f"{name_value(operation)}, and that generation was acquired by execution "
            f"{name_value(held['execution'])} under {name_value(held['operation'])}; a "
            f"renewal is for the same resource, generation, operation and execution, and "
            f"anything else is a second holder asking for somebody else's permission")
    standing = _renewals_of(control, domain, generation)
    if revision > len(standing):
        raise ContractRefusal(
            "refused", "precondition",
            f"{what} names expected revision {revision} and this generation stands at "
            f"{len(standing)}; a renewal cannot skip the state it claims to have observed")
    # W275775 review 2026-09-27T02-43-54Z [P2]: A REPLAY IS NOT A NEW EXTENSION, AND THE
    # BOUND APPLIES ONLY TO A NEW ONE.
    #
    # The probe found this exactly: revisions 1..4 committed, then the caller repeats its
    # fourth request because it never saw the reply -- and the bound refused it before
    # `transact` could answer the record that already exists. So the lost reply at the limit
    # was the one lost reply that could not be recovered, which inverts TOK-9's "a lost
    # renewal reply grants nothing beyond the committed authority state": it granted LESS
    # than the committed state, by hiding it.
    #
    # `revision < len(standing)` is a request whose record is already committed: it spends
    # no allowance, and `transact` answers it from the journal below. The bound is checked
    # for a NEW extension only -- and again inside the write, where it cannot be stale.
    renewing_anew = revision == len(standing)
    if renewing_anew and len(standing) >= RENEWAL_LIMIT:
        raise ContractRefusal(
            "policy", "denied",
            f"{what} is refused: this generation has been renewed {len(standing)} times and "
            f"the bounded policy allows {RENEWAL_LIMIT}. Exhaustion does not free the "
            f"resource -- the holder finishes or is revoked, and the resource stays held "
            f"either way")
    # THE NEW DEADLINE IS COMPOSED OUTSIDE THE LOCK, exactly where `acquire` composes its
    # own and for the same recorded reason: DB-1 keeps non-database work out of the
    # transaction, and this is arithmetic over the store's clock rather than a decision.
    # What the transaction decides is whether this extension is ALLOWED -- the owner, the
    # lifecycle, the current deadline and the revision are all re-proved under the write
    # lock below -- so reading the instant here costs the serialization nothing.
    taken = control._now()
    # THE SIGNATURE COVERS THE REQUEST, NOT THE CLOCK, and this is Child A's correction
    # applied rather than rediscovered: review 2026-09-26T13:41:00Z found `returned`
    # stamping a fresh clock value into its SIGNED operands, so an exact replay changed its
    # own signature and collided with itself. A renewal is the same shape -- the caller's
    # request is the resource, generation, revision, operation, execution, owner and
    # lifetime, and the instant is what this manager ANSWERS. So the clock-derived members
    # ride the recorded document and a retry after a lost reply replays instead of colliding.
    operands = {"version": TOKEN_VERSION, "domain": domain,
                "generation": generation, "revision": revision + 1,
                "operation": operation, "execution": execution,
                "owner": held["owner"], "seconds": seconds}
    document = dict(operands, renewed_at=taken,
                    expires_at=boundaries.deadline(
                        taken, seconds, "a renewed resource token expiry"))
    identity = _renewed_id(domain, generation, revision + 1)
    signature = manager_signature(RENEWED_KIND, operands)

    def extend(connection):
        """Reached ONLY when this identity has no committed record -- see `transact`."""
        # RE-PROVED INSIDE THE WRITE, because everything above is a read and a read proves
        # only its own instant. `transact` holds the write lock here, so a competing
        # revocation or return that committed in between is seen NOW -- which is the
        # serialization TOK-9's renewal-versus-expiry competition asks for, and the reason
        # this is one transaction rather than a check followed by a write.
        _owning(control, token, what)
        current = _renewals_of(control, domain, generation)
        if len(current) != revision:
            raise ContractRefusal(
                "refused", "operation-collision",
                f"{what} was asked against revision {revision} and another renewal "
                f"committed first; one revision has one renewal")
        # AND THE BOUND, RE-PROVED WHERE IT CANNOT BE STALE. The read above happened before
        # the write lock; this is the decision. A replay never reaches here at all.
        if len(current) >= RENEWAL_LIMIT:
            raise ContractRefusal(
                "policy", "denied",
                f"{what} is refused: this generation has been renewed {len(current)} times "
                f"and the bounded policy allows {RENEWAL_LIMIT}. Exhaustion does not free "
                f"the resource -- the holder finishes or is revoked, and the resource stays "
                f"held either way")
        return dict(document)

    return control.transact(identity, RENEWED_KIND, signature, extend)


def journal_launch(control, token, launch):
    """Record the launch this token authorizes, BEFORE any container exists.

    TOK-4: "Reserve before launch. A container ID may not yet exist." So the fixed
    launch operation is journalled first and correlated afterwards. Until a container
    is bound, `effects_permitted` answers False -- a launch whose reply is late or
    lost therefore cannot reach the governed resource, and it cannot be freed by a
    positive callback that names no container.
    """
    from .store import manager_signature

    launch = boundaries.text(launch, "a launch operation identity")
    document = {"domain": token["domain"], "generation": token["generation"],
                "owner": token["owner"], "launch": launch}

    def journalling(_connection):
        _owning(control, token, "journalling a launch")
        return dict(document)

    return control.transact(_launch_id(token["domain"], token["generation"]),
                            LAUNCH_KIND,
                            manager_signature(LAUNCH_KIND, document), journalling)


def bind_container(control, token, container, *, launch):
    """Correlate the eventual container with this exact token and launch.

    TYPED, AND ONLY FOR THE JOURNALLED LAUNCH. The binding names the launch operation
    it answers, so a container from some other start cannot be attached to this
    generation, and a stale owner cannot bind at all. One binding per generation: a
    second, differing one collides at this identity, which is the journal enforcing
    the same rule one layer earlier.
    """
    from .store import manager_signature

    container = boundaries.text(container, "a bound container identity")
    launch = boundaries.text(launch, "a launch operation identity")
    recorded = _document(control, _launch_id(token["domain"], token["generation"]),
                         LAUNCH_KIND)
    if recorded is None or recorded.get("launch") != launch:
        raise ContractRefusal(
            "refused", "precondition",
            f"binding container {name_value(container)} to token generation "
            f"{token['generation']} of {name_value(token['domain'])} names launch "
            f"{name_value(launch)}, which is not the launch this token journalled; a "
            f"container from another start is not this token's execution")
    document = {"domain": token["domain"], "generation": token["generation"],
                "owner": token["owner"], "launch": launch, "container": container}

    def binding(_connection):
        _owning(control, token, "binding a container")
        return dict(document)

    return control.transact(_bound_id(token["domain"], token["generation"]),
                            BOUND_KIND,
                            manager_signature(BOUND_KIND, document), binding)


def revoke(control, resource_identity, resource_kind, *, execution, operation):
    """Withdraw an OVERDUE generation's entitlement, durably and first.

    THE FIRST OF THE FOUR ACTS a reclaim performs. It changes no container and
    frees no resource: what it does is record that this generation may no longer
    act, so the old holder is refused at its next journal-guarded step rather than
    racing whatever the reclaim does next. TOK-5's "revoked rather than replaced"
    is exactly this ordering -- the resource stays held by the revoked generation
    until its cessation is confirmed.

    ONLY AN EXPIRED GENERATION MAY BE REVOKED. A live one is somebody's valid
    permission, and taking it away because a sweep happened to look would make the
    lifetime advisory. An already-revoked generation replays its own record.
    """
    from .store import _recorded, manager_signature

    domain = domain_of(resource_kind, resource_identity)
    connection = control._connection
    # W275774 review 2026-09-26T19-13-42Z: THE WHOLE DECISION IS ONE TRANSACTION,
    # and the reason is `admit_activation`'s reason applied where I had not applied
    # it. Every read here -- which generation this execution holds, whether it has
    # been returned, whether it is overdue -- used to happen BEFORE `BEGIN
    # IMMEDIATE`, and only the replay record was read under the lock. So the
    # unstable half was again an ABSENCE: a caller suspended after reading
    # `returned` as false resumed and wrote a revocation for a generation that had
    # since been returned and replaced, which is a withdrawal of an entitlement
    # generation 2 now holds nothing about.
    #
    # The lock decides now. The replay record is read first and the TERMINAL FACTS
    # LAST, for the ordering reason the admission states: `BEGIN IMMEDIATE` excludes
    # another connection's writer, and reading the terminal facts last additionally
    # excludes work that reaches the store from inside this very transaction.
    connection.execute("BEGIN IMMEDIATE")
    try:
        generation = generation_of(control, domain, execution=execution,
                                   operation=operation)
        if generation is None:
            connection.execute("COMMIT")
            return None
        existing = _document(control, _revoked_id(domain, generation),
                             REVOKED_KIND)
        # AND THE FRESHEST TERMINAL READS, taken after everything else.
        current = token_of(control, domain, generation)
        if current["returned"]:
            connection.execute("COMMIT")
            return None
        if not current["expired"]:
            raise ContractRefusal(
                "refused", "precondition",
                f"generation {generation} of {name_value(domain)} expires at "
                f"{name_value(current['expires_at'])} and is not overdue; a live "
                f"permission is not revoked because a sweep looked at it")
        if existing is not None:
            connection.execute("COMMIT")
            return dict(existing)
        document = {"domain": domain, "generation": generation,
                    "owner": current["owner"],
                    "container": current["container"],
                    "expired_at": current["expires_at"]}
        control._record(_revoked_id(domain, generation), REVOKED_KIND,
                        manager_signature(REVOKED_KIND, document), "committed",
                        _recorded(document), None)
        connection.execute("COMMIT")
    except BaseException:
        try:
            connection.execute("ROLLBACK")
        except Exception:
            pass
        raise
    return document


def admit_activation(control, token, *, container):
    """ADMIT ONE ACTIVATION, DURABLY, BEFORE THE ENGINE IS ASKED TO RUN ANYTHING.

    THE ANSWER IS A RECORD, NOT A BOOLEAN. Review 15:00:16Z showed a caller
    answering `True` from a read it had taken earlier, after the resource had been
    settled and handed to generation 2; a boolean cannot be told apart from a stale
    boolean. What this returns is the admission itself, naming the domain,
    generation and exact container, so a consumer can require the document.

    AND THE WHOLE DECISION IS ONE TRANSACTION. Review 15:19:45Z destroyed my
    previous argument in one sentence: monotone POSITIVE terminal facts do not
    stabilize an ABSENCE read. I was checking that no settlement and no return
    existed, outside the lock, and then letting `transact` replay -- so a
    settlement, a return and a generation-2 acquisition could all commit in between
    and the replay would still hand back an admission that authorized a start. The
    absence was the unstable half and I reasoned about the presence.

    So this takes `BEGIN IMMEDIATE` itself instead of delegating to `transact`, and
    under that lock it reads the terminal facts, decides the replay disposition, and
    writes. A RETRY OF AN ACTIVATION STILL IN FLIGHT replays its own record, which
    is what makes an interrupted starter safe to resume. Anything terminal --
    settled, or the generation returned -- refuses, because at that point what the
    caller holds is A HISTORICAL RESULT AND NOT A FRESH PERMISSION TO START. Those
    are different things and this is where they are told apart.
    """
    from .store import _recorded, manager_signature

    container = boundaries.text(container, "a bound container identity")
    document = {"domain": token["domain"], "generation": token["generation"],
                "owner": token["owner"], "container": container}
    signature = manager_signature(ACTIVATING_KIND, document)
    connection = control._connection
    connection.execute("BEGIN IMMEDIATE")
    try:
        bound = _document(control, _bound_id(token["domain"], token["generation"]),
                          BOUND_KIND)
        if bound is None:
            raise ContractRefusal(
                "refused", "precondition",
                f"token generation {token['generation']} of "
                f"{name_value(token['domain'])} has bound no container, so there "
                f"is nothing to admit an activation for")
        if bound["container"] != container:
            raise ContractRefusal(
                "runtime-observation", "identity-mismatch",
                f"this token governs container {name_value(bound['container'])} "
                f"and the activation names {name_value(container)}; an admission "
                f"for another container is not this token's execution")
        # THE REPLAY DISPOSITION, DECIDED HERE AND NOT BY THE JOURNAL. An admission
        # still in flight answers itself -- one executor resuming its own act. One
        # that names different operands is a different act wearing this one's name.
        admitted = _document(control, _activating_id(token["domain"],
                                                     token["generation"]),
                             ACTIVATING_KIND)
        # THE TERMINAL FACTS ARE THE LAST THING READ BEFORE THE DISPOSITION, and
        # that ordering is the correction rather than a detail.
        #
        # Review 15:19:45Z first: monotone POSITIVE facts do not stabilize an
        # ABSENCE read, and absence was the half I depended on. Moving the checks
        # under the lock was necessary and not sufficient -- with them read FIRST, a
        # settlement, a return and a generation-2 acquisition could still land
        # between them and the admission read, and the replay answered anyway. That
        # is what the independent probe drives, by interleaving exactly there.
        #
        # So the disposition is decided on the FRESHEST reads this transaction can
        # take: everything else is read first, and whether this generation may still
        # authorize an execution is asked last. `BEGIN IMMEDIATE` excludes another
        # connection's writer; this ordering additionally excludes work that reaches
        # the store from inside this very transaction, which is the case a lock
        # cannot help with.
        _owning(control, token, "admitting an activation")
        if _document(control, _activation_settled_id(token["domain"],
                                                     token["generation"]),
                     ACTIVATION_SETTLED_KIND) is not None:
            raise ContractRefusal(
                "refused", "already-terminal",
                f"the activation of generation {token['generation']} of "
                f"{name_value(token['domain'])} has already been settled; its record "
                f"is the history of what happened and not permission to start again")
        if admitted is not None:
            if admitted["container"] != container \
                    or admitted["owner"] != token["owner"]:
                raise ContractRefusal(
                    "refused", "operation-collision",
                    f"generation {token['generation']} of "
                    f"{name_value(token['domain'])} already admitted an activation of "
                    f"{name_value(admitted['container'])} for another owner; one "
                    f"executor holds an activation at a time")
            connection.execute("COMMIT")
            return dict(admitted)
        control._record(_activating_id(token["domain"], token["generation"]),
                        ACTIVATING_KIND, signature, "committed",
                        _recorded(document), None)
        connection.execute("COMMIT")
    except BaseException:
        try:
            connection.execute("ROLLBACK")
        except Exception:
            pass
        raise
    return document


def settle_activation(control, token, *, container, started):
    """Resolve the in-flight activation with its CONCLUSIVE outcome.

    AND ONLY A CONCLUSIVE ONE. Review 15:14:13Z corrects an instruction I had
    written: a caller must NOT settle `started=False` merely because
    `adapter.start` refused. A fault or a later check can follow a real
    activation, so a refusal is evidence about this manager's decision and not
    about the engine. An outcome nobody knows is left UNSETTLED on purpose -- the
    resource stays held, which is the honest state, rather than freed on a guess.

    Until this exists the resource is held: `returned` will not settle a
    generation whose activation nobody has answered for, because a container that
    may or may not have been started is the unknown the token exists to hold. The
    outcome is a real boolean -- a truthy string is not an answer, the same
    lesson the cessation evidence already carries.
    """
    from .store import manager_signature

    container = boundaries.text(container, "a bound container identity")
    if started is not True and started is not False:
        raise ContractRefusal(
            "runtime-observation", "quiescence-unknown",
            f"the activation outcome for container {name_value(container)} is "
            f"{name_value(started)} and not the boolean True or False; an "
            f"activation nobody positively resolved stays in flight")
    admitted = _document(control, _activating_id(token["domain"],
                                                 token["generation"]),
                         ACTIVATING_KIND)
    if admitted is None or admitted["container"] != container:
        raise ContractRefusal(
            "refused", "precondition",
            f"no activation of container {name_value(container)} was admitted "
            f"for token generation {token['generation']} of "
            f"{name_value(token['domain'])}; there is nothing to settle")
    # W275774 review 15:14:13Z [P1]: THE SETTLEMENT IS THE ADMITTED OWNER'S ACT.
    #
    # It accepted a forged owner, which made the one record that releases the
    # in-flight hold writable by anybody holding a copy of the token. The owner is
    # compared against THE ADMISSION'S OWN RECORD rather than through `_owning`,
    # deliberately: `_owning` refuses an expired generation, and settling the
    # outcome of an activation whose generation has since expired is exactly the
    # legitimate reconciliation this must still allow. Expiry is a reason to stop
    # ACTING, not a reason to refuse the answer about what already happened.
    if admitted["owner"] != token["owner"]:
        raise ContractRefusal(
            "runtime-observation", "identity-mismatch",
            f"settling the activation of container {name_value(container)} for "
            f"generation {token['generation']} of {name_value(token['domain'])} was "
            f"asked by an act that does not own the admission; only the owner that "
            f"was admitted may answer for its outcome")
    document = {"domain": token["domain"], "generation": token["generation"],
                "owner": token["owner"], "container": container,
                "started": started}

    def settling(_connection):
        return dict(document)

    return control.transact(
        _activation_settled_id(token["domain"], token["generation"]),
        ACTIVATION_SETTLED_KIND,
        manager_signature(ACTIVATION_SETTLED_KIND, document), settling)


def effects_permitted(control, token):
    """Whether the governed resource may be exposed to this token's effects YET.

    THE GATE REVIEW 2026-09-26T13:29:00Z ASKED FOR. Journalling before the start and
    binding after the reply is not sufficient on its own: between those two moments
    the container may already exist. So permission to expose the resource is a
    separate, positive question, and it answers True only when THIS generation is
    current, unreturned, unexpired and has a bound container. A caller that cannot
    get True here must not hand the resource to the execution -- the closed
    start/dispatch sequence at the production seam is what enforces that, and it is
    the next G1 step.
    """
    current = token_of(control, token["domain"], token["generation"])
    if current is None or current["returned"] or current["expired"]:
        return False
    if current["owner"] != token["owner"] or current["container"] is None:
        return False
    return True


def _reclaiming(value):
    """EXACTLY `True` OR `False`, and nothing that merely looks like one.

    W275774 review 2026-09-27T01-49-32Z reproduced the defect with two inputs:
    `returned(..., reclaiming='false')` and `release(..., reclaiming=1)`. Both are
    TRUTHY, so both selected the manager-reclaim path -- the one exception to the
    ordinary holder's expiry and revocation refusals -- and an expired generation was
    returned by a caller that had asked for the opposite, or for nothing in
    particular.

    THE SAME RULE `stopped` ALREADY HAS, one operand along. Review
    2026-09-26T13:41:00Z refused `stopped="false"` for exactly this reason: a
    two-valued switch that accepts any object accepts the wrong answer with the same
    silence as the right one. `reclaiming` selects a PRIVILEGE, so it is the last
    operand that should be read loosely.

    REFUSED BEFORE ANY EFFECT AND BEFORE ANY REPLAY, so a malformed request never
    reaches a journal read, a generation lookup or a settlement -- and a repeated
    malformed request is refused again rather than answering some earlier act's
    record.

    LOCAL AND TYPED, per that review: `boundaries` publishes no flag verb, and
    growing the shared API for one operand would be a wider change than the defect.
    `bool` is checked by identity rather than by `isinstance`, because `True` and
    `1` are equal and `isinstance(1, bool)` is False but `isinstance(True, int)` is
    True -- so the test that actually excludes `1` is the type itself.
    """
    if type(value) is not bool:
        raise ContractRefusal(
            "integrity", "schema",
            f"a manager-reclaim selector is exactly true or false; "
            f"{name_value(repr(value))} is {type(value).__name__} and a truthy "
            f"value of another type would silently select the manager settlement "
            f"that is the one exception to a holder's expiry and revocation "
            f"refusals")
    return value


def returned(control, token, *, cessation, reclaiming=False):
    """Return the token, conditional on this exact generation and proven cessation.

    TOK-5 as amended (DESIGN 7f504a5e): confirmed termination of the exact outgoing
    container is required before ownership passes to another execution, INCLUDING a
    normal handoff, and a naturally exited container qualifies only after the same
    positive checks. So `cessation` is typed evidence about the bound container --
    `stopped` and `helpers` -- and anything short of "that container is gone and no
    writable helper survives" refuses and leaves the resource held.

    NEVER A STALE RETURN. A holder whose generation or owner no longer matches cannot
    return, which is what stops a finished generation 1 from freeing a live
    generation 2.
    """
    from .store import manager_signature

    # (0) THE MODE SELECTOR, FIRST OF ALL, because it decides which refusals apply.
    reclaiming = _reclaiming(reclaiming)
    # (1) TYPED, EXACT AND NOT TRUTHY. Review 2026-09-26T13:41:00Z found three holes in
    # one line: the document carried no binding to this token, `stopped="false"` passed
    # the conditional because a non-empty string is true, and an UNBOUND return skipped
    # the check entirely even with a journalled launch of unknown outcome.
    #
    # So the evidence must NAME what it is evidence about -- domain, generation, launch
    # and container -- and `stopped` must be the boolean `True`, not something that looks
    # like it. TOK-11: "String truthiness, a caller's boolean assertion, or an old cleanup
    # receipt cannot substitute for the trusted adapter's correlated evidence."
    cessation = boundaries.document(
        cessation, "a container cessation answer",
        required=("domain", "generation", "launch", "container", "stopped", "helpers"))
    current = token_of(control, token["domain"], token["generation"])
    if current is None or current["owner"] != token["owner"]:
        raise ContractRefusal(
            "runtime-observation", "identity-mismatch",
            f"returning token generation {token['generation']} of "
            f"{name_value(token['domain'])} was asked by an act that does not own it; "
            f"a stale holder cannot release a later token")
    if cessation["domain"] != token["domain"] \
            or cessation["generation"] != token["generation"] \
            or cessation["launch"] != current["launch"] \
            or cessation["container"] != current["container"]:
        raise ContractRefusal(
            "runtime-observation", "identity-mismatch",
            f"the cessation evidence offered for generation {token['generation']} of "
            f"{name_value(token['domain'])} describes launch "
            f"{name_value(cessation['launch'])} and container "
            f"{name_value(cessation['container'])}, which is not what this token bound "
            f"(launch {name_value(current['launch'])}, container "
            f"{name_value(current['container'])}); evidence about another execution is "
            f"not evidence about this one")
    if cessation["stopped"] is not True:
        raise ContractRefusal(
            "runtime-observation", "quiescence-unknown",
            f"the cessation evidence for generation {token['generation']} of "
            f"{name_value(token['domain'])} reports stopped="
            f"{cessation['stopped']!r}, which is not the boolean True; a value that merely "
            f"looks true is not a confirmed termination")
    # W275774 review 15:00:16Z [P1]: AND AN ACTIVATION IN FLIGHT HOLDS THE RESOURCE.
    #
    # THIS IS THE HOLE THE PROBE FOUND, and it was not expiry. Settlement frees the
    # domain for a replacement, and it was being allowed to do so while a starter
    # sat between its admission and the engine call -- so generation 2 could be
    # acquired and generation 1's container started afterwards. Two holders of one
    # resource, reached without anything expiring.
    #
    # An admitted activation whose outcome nobody has resolved is exactly the
    # "unknown" this token exists to hold: the container may be about to run. So the
    # return refuses until the activation is settled either way, which makes the
    # hold last through the conclusive outcome rather than through a guess.
    if current["activating"]:
        raise ContractRefusal(
            "runtime-observation", "quiescence-unknown",
            f"generation {token['generation']} of {name_value(token['domain'])} has an "
            f"ADMITTED ACTIVATION of container {name_value(current['container'])} that "
            f"nobody has settled, so whether it is about to run is UNKNOWN; the resource "
            f"stays held until that activation is resolved, because a replacement taken "
            f"now could be joined by this one")
    if current["container"] is None and current["launch"] is not None:
        raise ContractRefusal(
            "runtime-observation", "quiescence-unknown",
            f"generation {token['generation']} of {name_value(token['domain'])} journalled "
            f"launch {name_value(current['launch'])} and never bound a container, so "
            f"whether that launch produced a running execution is UNKNOWN; the resource "
            f"stays held until the launch is conclusively settled rather than returned on "
            f"the strength of there being nothing recorded to stop")
    if current["container"] is not None:
        if cessation["helpers"]:
            raise ContractRefusal(
                "runtime-observation", "quiescence-unknown",
                f"token generation {token['generation']} of "
                f"{name_value(token['domain'])} cannot be returned: its container "
                f"{name_value(current['container'])} is not positively gone "
                f"(stopped={cessation['stopped']!r}, surviving helpers="
                f"{cessation['helpers']!r}). Confirmed termination precedes every "
                f"handoff, and a natural exit is not an exemption")
    # (3) NO FRESH CLOCK IN SIGNED OPERANDS. Review 13:41:00Z: `settled_at` was stamped
    # on every invocation, so an exact replay of this return computed a DIFFERENT
    # signature and collided with itself. The operands are now exactly the facts the
    # return is about; the instant is the journal's own, recorded by the store.
    document = {"domain": token["domain"], "generation": token["generation"],
                "owner": token["owner"], "container": current["container"],
                "launch": current["launch"], "stopped": True}

    def returning(_connection):
        # W275774: WHO IS SETTLING MATTERS, and this is the distinction my own expiry
        # case forced me to draw properly.
        #
        # A STALE HOLDER returning on its own authority after expiry is still
        # refused -- that is `test_an_expired_generation_cannot_bind_or_return`, and
        # it is right: a holder whose permission ran out does not get to declare the
        # resource free. A RECLAIM is the opposite situation: the entitlement was
        # withdrawn deliberately, the container was stopped and its absence
        # positively confirmed, and refusing that settlement would leave every
        # reclaimed resource held forever, because the only path that could free it
        # is the one expiry and revocation close.
        #
        # So `reclaiming` names which of those two this is. It relaxes NOTHING else:
        # the owner is still compared against the record, and the cessation evidence
        # is still checked member by member against what was bound.
        _owning(control, token, "returning the token", reclaiming=reclaiming)
        # W275774 review 15:14:13Z [P1]: RE-ASKED HERE, INSIDE THE COMMITTING
        # TRANSACTION, and the earlier check above is only the cheap early one.
        #
        # The probe was exact: an activation admitted between the preliminary read
        # and this transaction slipped past, because the decision was being made on
        # a value read before the lock was held. This is the same prepare-outside,
        # decide-in-DB discipline the correction paths already use -- the authority
        # is the read that happens under the write lock, and the two disagreeing is
        # only possible in the direction that refuses.
        admitted = _document(control, _activating_id(token["domain"],
                                                     token["generation"]),
                             ACTIVATING_KIND)
        settled = _document(control, _activation_settled_id(token["domain"],
                                                            token["generation"]),
                            ACTIVATION_SETTLED_KIND)
        if admitted is not None and settled is None:
            raise ContractRefusal(
                "runtime-observation", "quiescence-unknown",
                f"generation {token['generation']} of {name_value(token['domain'])} "
                f"has an ADMITTED ACTIVATION of container "
                f"{name_value(admitted['container'])} that nobody has settled, so "
                f"whether it is about to run is UNKNOWN; the resource stays held "
                f"until that activation is resolved")
        return dict(document)

    return control.transact(_returned_id(token["domain"], token["generation"]),
                            RETURNED_KIND,
                            manager_signature(RETURNED_KIND, document), returning)


def _owning(control, token, what, *, reclaiming=False):
    """Re-read the acquisition and require this act to be its owner.

    The document the caller holds is one the caller is holding; what authorizes each
    step is the record this journal still has, with its signature recomputed.
    """
    # W275774: A REVOCATION STOPS ACTING AND DOES NOT STOP SETTLING, which is the
    # same distinction expiry already draws. Withdrawing the entitlement is what
    # keeps a stale holder from launching, binding or admitting an activation; if it
    # also blocked the RETURN then the only path that can free a reclaimed resource
    # would be the one the revocation closes, and every revoked generation would
    # hold its resource forever. My own case found exactly that.
    if not reclaiming and _document(
            control, _revoked_id(token["domain"], token["generation"]),
            REVOKED_KIND) is not None:
        raise ContractRefusal(
            "refused", "already-terminal",
            f"{what} for generation {token['generation']} of "
            f"{name_value(token['domain'])} is refused: that generation has been "
            f"REVOKED, so its entitlement is withdrawn; only a manager settlement "
            f"holding positive cessation evidence may act on it now")
    held = _document(control, _acquired_id(token["domain"], token["generation"]),
                     ACQUIRED_KIND)
    if held is None or held.get("owner") != token["owner"]:
        raise ContractRefusal(
            "runtime-observation", "identity-mismatch",
            f"{what} for generation {token['generation']} of "
            f"{name_value(token['domain'])} was asked by an act that does not own it")
    # (2) THE LIFECYCLE, NOT ONLY THE OWNER. Review 2026-09-26T13:41:00Z: this checked
    # the original acquisition owner alone, so a RETURNED or EXPIRED generation could
    # still bind a container afterwards -- late binding by the rightful owner of a dead
    # token, which is exactly what TOK-11 forbids ("Revoked or superseded reservations
    # cannot acquire a late container binding").
    if _document(control, _returned_id(token["domain"], token["generation"]),
                 RETURNED_KIND) is not None:
        raise ContractRefusal(
            "refused", "precondition",
            f"{what} for generation {token['generation']} of "
            f"{name_value(token['domain'])} is refused: that token has been returned, and "
            f"a returned generation authorizes nothing further")
    # W275775: AGAINST THE CURRENT DEADLINE, WHICH A RENEWAL MAY HAVE MOVED.
    #
    # TOK-9: "Renewal and expiry compete against that same current state." This read the
    # ACQUISITION's own `expires_at`, so once renewal existed a holder that had legitimately
    # extended its deadline would still have been refused here at the original one -- the
    # renewal would have granted nothing, which is the failure the requirement names from
    # the other side. `_deadline_of` walks the committed renewals, so the fact this refuses
    # on is the same one `token_of`, `revoke` and the conflict message see.
    #
    # AND THE COMMITTED RECORD IS WHAT DECIDES, never the caller's copy: the token document
    # a caller holds carries the deadline it was given, and an extension it never learned
    # about is still an extension. Nothing here trusts `token["expires_at"]`.
    # W275775 review 2026-09-27T03-21-53Z [P1b]: ONE READ, NOT TWO. The deadline and the
    # revision it came from are derived from the SAME list of committed renewals, because a
    # pair read at two instants is a torn observation: the reviewer's probe renewed between
    # the two reads, so the refusal carried an OLD deadline beside the NEW revision, and a
    # correlation check comparing only the revision then accepted it and held a token whose
    # real deadline had never passed.
    standing = _renewals_of(control, token["domain"], token["generation"])
    deadline = standing[-1]["expires_at"] if standing else held["expires_at"]
    # W275775 [P1]: AND A JUDGEMENT ALREADY MADE OUTWEIGHS THE CLOCK. The record is
    # consulted first because it cannot be un-made: a generation judged expired stays
    # expired for every act this gate protects, whatever the clock says afterwards.
    judged = _judged_expired(control, token["domain"], token["generation"])
    # W275775 [C1]: AND A TIMING AMBIGUITY HOLDS TOO, for the same reason a judged expiry
    # does: this manager cannot say what time it is for this generation, so it does not get
    # to act on a guess. Settlement paths pass `reclaiming=True` and are unaffected.
    unsure = _judged_ambiguous(control, token["domain"], token["generation"])
    if not reclaiming and unsure is not None:
        raise ContractRefusal(
            "refused", "precondition",
            f"{what} for generation {token['generation']} of "
            f"{name_value(token['domain'])} is refused: this manager's timing for that "
            f"generation is AMBIGUOUS -- at {name_value(unsure['observed_at'])} it had "
            f"passed {name_value(unsure['expires_at'])}, and the clock then read "
            f"{name_value(unsure['decided_at'])}. Ambiguous timing is held and reconciled, "
            f"never resolved by asking again")
    now = control._now()
    if not reclaiming and (judged is not None or now >= deadline):
        refusal = ContractRefusal(
            "refused", "precondition",
            f"{what} for generation {token['generation']} of "
            f"{name_value(token['domain'])} is refused: that token expired at "
            f"{name_value(deadline)}"
            + ("" if judged is None else
               f" and was judged expired at {name_value(judged['observed_at'])}")
            + ". Expiry begins revocation, and a late "
            f"binding or return under an expired token is not an exception to it")
        # THE OBSERVATION THIS DECISION WAS MADE ON, carried to whoever records it.
        #
        # W275775 review 2026-09-27T03-12-19Z [C1]: the recorder used to take a FRESH reading
        # of the clock, so the window between deciding and recording was invisible to it --
        # a clock that moved backwards in that window simply made the record decline. The
        # deadline, the revision and the INSTANT this refusal rests on travel with it, so the
        # recorder can correlate them against what stands and tell an overtaken observation
        # (somebody renewed) from a moved clock (nobody did).
        refusal.timing = {"expires_at": deadline, "observed_at": now,
                          "revision": len(standing)}
        raise refusal
    return held


def _observed_revision(value):
    """The revision a caller says it OBSERVED: exactly a whole number, zero included.

    W275775 review 2026-09-27T02-43-54Z. `boundaries.generation` was the wrong owner here --
    it requires a positive integer, and the first renewal of a generation is asked for
    against the observed revision ZERO, which is what `token_of` answers for a token nobody
    has renewed. Validated locally and typed, like the two other closed-vocabulary operands
    this module owns, and witnessed in the boundary catalog rather than probed for a label.

    BOOLEANS ARE NOT NUMBERS HERE. `True` is an `int` in Python and would otherwise read as
    revision 1, which would let `renew(..., expected_revision=True)` replay somebody's first
    renewal; the type is checked exactly.
    """
    if type(value) is not int or value < 0:
        raise ContractRefusal(
            "integrity", "schema",
            f"an expected deadline revision is a whole number of committed renewals -- the "
            f"value `token_of` answers as `revision`, zero for a generation nobody has "
            f"renewed -- and {name_value(repr(value))} is not one")
    return value


def _judged_expired(control, domain, generation):
    """The durable expiry judgement for this generation, or `None`."""
    return _document(control, _expired_id(domain, generation), EXPIRED_KIND)


def _judged_ambiguous(control, domain, generation):
    """The durable timing-ambiguity hold for this generation, or `None`."""
    return _document(control, _ambiguous_id(domain, generation),
                     TIMING_AMBIGUOUS_KIND)


def _judging(control, domain, generation, act):
    """Run a renewal attempt, and record an expiry judgement if one is TRUE afterwards.

    W275775 [P1], and the two things the reviewer asked this to stop doing.

    NO MESSAGE MATCHING. My first cut inspected the refusal's text for "expired at" and only
    then judged, which made a durable authority fact depend on prose. The refusal now CARRIES
    the observation its decision rested on -- deadline, revision and instant -- and only an
    expiry refusal carries one, so the typed operand selects the path and the prose is
    irrelevant. W275775 review 2026-09-27T03-12-19Z asked for exactly that correlation.

    AND EXPIRY FIRST DISCOVERED INSIDE THE TRANSACTION GETS THE SAME SEMANTICS. `renew`
    re-proves ownership under the write lock, so expiry can be found there too -- and a write
    made inside that transaction would be rolled back with it. So the judgement is attempted
    around the WHOLE attempt, after any transaction has unwound, in its own short write.
    Never nested, and never a lock held across anything external.

    A RENEWAL THAT SUCCEEDS JUDGES NOTHING: it just moved the deadline, so the condition
    cannot hold. Only the refusal path asks.
    """
    try:
        return act()
    except ContractRefusal as refusal:
        observed = getattr(refusal, "timing", None)
        if observed is not None:
            _judge_expired(control, domain, generation, observed)
        raise


def _judge_expired(control, domain, generation, observed):
    """Classify this generation's timing ONCE, on ONE snapshot, and record the answer.

    W275775 review 2026-09-27T03-21-53Z [P1a]. My previous cut made two decisions in two
    transactions -- "is it expired?" then "did the clock move backwards?" -- each reading its
    own snapshot, and the reviewer scheduled a clock that made BOTH decline: no expiry record,
    no ambiguity record, and the next attempt renewed. Two conditional writes are not an
    exhaustive decision, however carefully each one is written.

    SO THERE IS ONE TRANSACTION AND IT ALWAYS DECIDES. It takes the write lock, reads the
    acquisition, the committed renewals, the deadline they imply and the instant ONCE, and
    classifies:

      * THE OBSERVATION DOES NOT CORRELATE -- a different revision or a different deadline
        than what stands. Then it was overtaken (somebody renewed) and it is not about this
        state at all: nothing is recorded, and the caller's own refusal remains its own
        business. This is the earlier stale-observation correction, kept exactly.
      * IT CORRELATES AND THE DEADLINE HAS PASSED -> EXPIRED is recorded. Authoritative.
      * IT CORRELATES AND THE DEADLINE HAS NOT PASSED -> the observation that refused and the
        state that stands disagree about the time, with no renewal in between. That is TOK-9's
        ambiguous timing, and AMBIGUOUS is recorded. It covers the clock moving backwards
        between the observation and this decision, and it covers any other disagreement of
        this manager's own clock with itself: the branch is the ELSE, so a correlated
        observation can never leave both records absent.

    ONE SHORT WRITE, ITS OWN LOCK, NOTHING NESTED AND NO EXTERNAL I/O -- the same shape
    `acquire` uses, for the same DB-1 reason. A record already committed under either identity
    is answered instead of written, so a second judgement replays the first.
    """
    from .store import _recorded, manager_signature

    operands = {"version": TOKEN_VERSION, "domain": domain, "generation": generation}
    expired_at_id = _expired_id(domain, generation)
    ambiguous_at_id = _ambiguous_id(domain, generation)
    connection = control._connection
    connection.execute("BEGIN IMMEDIATE")
    try:
        # A DECISION ALREADY MADE IS THE ANSWER. Read inside the lock, so a concurrent
        # judgement cannot be half-visible.
        for identity, kind in ((expired_at_id, EXPIRED_KIND),
                               (ambiguous_at_id, TIMING_AMBIGUOUS_KIND)):
            standing = _document(control, identity, kind)
            if standing is not None:
                connection.execute("COMMIT")
                return standing
        acquired = _document(control, _acquired_id(domain, generation), ACQUIRED_KIND)
        renewals = _renewals_of(control, domain, generation)
        deadline = (renewals[-1]["expires_at"] if renewals
                    else (acquired or {}).get("expires_at"))
        revision = len(renewals)
        now = control._now()
        if acquired is None or revision != observed["revision"] \
                or deadline != observed["expires_at"]:
            # OVERTAKEN, OR ABOUT NOTHING. No record: this observation is not about the state
            # that stands, and a durable claim from it would be exactly the defect the
            # previous correction closed.
            connection.execute("COMMIT")
            return None
        if now >= deadline:
            identity, kind = expired_at_id, EXPIRED_KIND
        else:
            identity, kind = ambiguous_at_id, TIMING_AMBIGUOUS_KIND
        document = {"version": TOKEN_VERSION, "domain": domain,
                    "generation": generation, "expires_at": deadline,
                    "revision": revision,
                    "observed_at": observed["observed_at"], "decided_at": now}
        control._record(identity, kind, manager_signature(kind, operands),
                        "committed", _recorded(document), None)
        connection.execute("COMMIT")
        return document
    except BaseException:
        try:
            connection.execute("ROLLBACK")
        except Exception:
            pass
        raise


def _deadline_of(control, domain, generation, acquired=None):
    """The deadline this generation is owed NOW: its last renewal's, or its own.

    W275775. ONE DERIVATION, used by every act that arbitrates against the deadline, so
    "renewal and expiry compete against that same current state" is a property of one
    function rather than an agreement between several readers.
    """
    if acquired is None:
        acquired = _document(control, _acquired_id(domain, generation), ACQUIRED_KIND)
        if acquired is None:
            return None
    renewals = _renewals_of(control, domain, generation)
    return renewals[-1]["expires_at"] if renewals else acquired["expires_at"]


# -- the consumer's side: one governed start, composed once -------------------
#
# W275774 review 15:28:31Z asked the CALLER to demonstrate that it reserves ONE
# external crossing and that retries reconcile onto it. That is a composition
# rather than a new rule, and it lives here rather than in `attempts.py` so the
# ordering -- reserve, journal the launch, bind, admit, settle -- is owned in one
# place by the module that owns the records.


class Reservation:
    """One attempt's reservation of one resource, and the acts it authorizes.

    Handed to `attempts.request_runtime_start`, which passes `bind` into the
    adapter and calls `settle` only on a conclusive outcome. It holds no engine
    handle and performs no I/O: every method here is a journal decision.
    """

    def __init__(self, control, token, launch):
        self.control = control
        self.token = token
        self.launch = launch

    def bind(self, container):
        """Bind the created container, and answer the ADMISSION for its start.

        Called between the engine's `create` and its `start`, which is the only
        moment at which the container's identity exists and no process has
        touched the resource. The returned callable is asked at the last moment
        before activation and answers the admission record itself -- never a
        boolean, which could not be told apart from a stale one.
        """
        bind_container(self.control, self.token, container, launch=self.launch)
        return lambda: admit_activation(self.control, self.token,
                                        container=container)

    def settle(self, container):
        """The activation positively happened: the engine answered."""
        return settle_activation(self.control, self.token, container=container,
                                 started=True)


def generation_of(control, domain, *, execution, operation):
    """The generation THIS execution and operation reserved, or `None`.

    W275774 review 15:55:27Z [P1]: a recovered return must name the generation its
    own act reserved, NOT whatever is outstanding now. The previous cut took "the
    one outstanding generation", so a stale recovery arriving after generation 2 had
    been acquired would have returned GENERATION 2 -- somebody else's live hold,
    released by a message about a dead one.

    So the generation is found by the pair that identifies the original act, and a
    recovery whose own generation is already returned finds it and stops.

    AND THE PAIR IS OWNED HERE, WHICH IT WAS NOT. W275774 inventory B/D, 2026-09-27:
    `acquire` validates `operation` and `execution` and this resolver did not, so the
    two acts that reach a generation THROUGH it -- `release` and `revoke` -- took the
    identifying pair unvalidated and merely COMPARED it against journal documents. A
    comparison is not ownership: a non-text operand matched nothing and left "no
    generation was reserved by ...", a refusal that reads like an absent record rather
    than a malformed request. Validated in the ONE resolver both callers use, so
    neither has its own spelling of the same rule.
    """
    boundaries.text(domain, "a governed conflict domain")
    execution = boundaries.text(execution, "a token execution identity")
    operation = boundaries.text(operation, "a token operation identity")
    generation = 1
    while True:
        acquired = _document(control, _acquired_id(domain, generation),
                             ACQUIRED_KIND)
        if acquired is None:
            return None
        if acquired["execution"] == execution \
                and acquired["operation"] == operation:
            return generation
        generation += 1


def release(control, resource_identity, resource_kind, *, execution, operation,
            cessation, reclaiming=False):
    """Return the resource on CONFIRMED cessation of the exact bound container.

    THE OTHER END OF THE LIFECYCLE, and the piece whose absence measurably made a
    governed start one-shot: nothing returned a token, so the first governed start
    held its domain for the life of the store.

    RESTART-SAFE, AND BOUND TO ITS OWN ACT. It takes the resource identity and the
    execution/operation pair rather than a token document -- the process that must
    return a resource is routinely not the one that reserved it -- and it resolves
    the generation THAT PAIR reserved. A generation already returned answers `None`,
    so a repeated ending is idempotent rather than fatal, and a later generation
    belonging to somebody else is never touched.

    `cessation` IS THE CALLER'S EVIDENCE AND IS NOT INVENTED HERE. Review 15:55:27Z
    caught the previous cut synthesizing `stopped=True` from a state column and
    defaulting `helpers` to empty -- which is asserting that no writer survived
    rather than observing it. This requires the document, `returned` re-checks it
    against what was bound, and nothing here supplies a default for either field.
    """
    reclaiming = _reclaiming(reclaiming)
    domain = domain_of(resource_kind, resource_identity)
    offered = boundaries.document(cessation, "a container cessation answer",
                                  required=("container", "stopped", "helpers"))
    generation = generation_of(control, domain, execution=execution,
                               operation=operation)
    if generation is None:
        raise ContractRefusal(
            "refused", "precondition",
            f"no generation of {name_value(domain)} was reserved by execution "
            f"{name_value(execution)} under operation {name_value(operation)}; "
            f"there is nothing this ending can return")
    current = token_of(control, domain, generation)
    if current["returned"]:
        return None
    token = {"domain": domain, "generation": generation,
             "owner": current["owner"]}
    return returned(control, token, reclaiming=reclaiming, cessation={
        "domain": domain, "generation": generation,
        "launch": current["launch"], "container": offered["container"],
        "stopped": offered["stopped"], "helpers": offered["helpers"]})


class Governance:
    """The authority one resource family's starts are serialized against."""

    def __init__(self, resource_kind, identity):
        self.resource_kind = boundaries.text(resource_kind,
                                             "a governed resource kind")
        self.identity = boundaries.capability(identity,
                                              "a governed resource identity")

    def release(self, control, attempt, *, operation, cessation,
                reclaiming=False):
        """This family's return: the resource identity is the governance's own."""
        reclaiming = _reclaiming(reclaiming)
        return release(control, self.identity(attempt), self.resource_kind,
                       execution=attempt["runtime_attempt_id"],
                       operation=operation, cessation=cessation,
                       reclaiming=reclaiming)

    def overdue(self, control, attempt, *, operation):
        """This attempt's generation if it is overdue and unreturned, else `None`."""
        domain = domain_of(self.resource_kind, self.identity(attempt))
        generation = generation_of(control, domain,
                                   execution=attempt["runtime_attempt_id"],
                                   operation=operation)
        if generation is None:
            return None
        current = token_of(control, domain, generation)
        if current["returned"] or not current["expired"]:
            return None
        return current

    def revoke(self, control, attempt, *, operation):
        """This family's revocation, on its own resource identity."""
        return revoke(control, self.identity(attempt), self.resource_kind,
                      execution=attempt["runtime_attempt_id"],
                      operation=operation)

    def reserve(self, control, attempt, *, operation):
        """Reserve the resource for this attempt BEFORE any launch is attempted.

        The launch is journalled under the START OPERATION'S OWN IDENTITY, so the
        launch the token names is the journalled start rather than a second act
        beside it -- and a retry of that operation replays this same reservation
        rather than allocating a second generation.
        """
        domain = domain_of(self.resource_kind, self.identity(attempt))
        token = acquire(control, domain, operation=operation,
                        execution=attempt["runtime_attempt_id"],
                        attempt=attempt["runtime_attempt_id"])
        journal_launch(control, token, operation)
        return Reservation(control, token, operation)


def governed_workspace_identity(control, attempt, mounted=None):
    """The workspace resource identity WITH ITS OVERLAP ARGUMENT, when a store is here.

    W275774 review 18:27:07Z directed the shared durable domain and overlap exclusion,
    and this is the half the token owner can hold: it delegates to the containment
    owner, which has the paths this module deliberately does not.

    `workspaces.governed_resource_identity` answers `device:inode` ONLY after checking
    that the root sits in the sibling position the configured storage arranges -- so
    two attempts naming one object share a domain, and two attempts naming different
    objects provably cannot be writing the same tree. A root reached by some other
    arrangement is refused rather than handed out as an identity that looks unique and
    is not.

    THE ROW-ONLY FORM BELOW REMAINS, and its limit is now explicit rather than
    implied: it names the same object and makes NO overlap argument, so it is the
    fallback for callers that hold no store and not the governed path.
    """
    from . import workspaces

    argued = workspaces.governed_resource_identity(
        control, attempt["runtime_attempt_id"], mounted=mounted)
    # AND IT MUST BE THE OBJECT THIS ATTEMPT PINNED, which is what keeps the domain
    # STABLE across the lifecycle. Review 18:33:48Z named the risk: if the live object
    # were allowed to differ from the pinned one, a start would reserve under one
    # domain and its ending would compute another and find no generation to return.
    # So the containment argument is required to agree with the pinned identity, and a
    # disagreement is a refusal rather than a silently different resource.
    pinned = workspace_identity(attempt)
    if argued != pinned:
        raise ContractRefusal(
            "runtime-observation", "identity-mismatch",
            f"attempt {name_value(attempt['runtime_attempt_id'])} pinned workspace "
            f"object {name_value(pinned)} and its governed root now resolves to "
            f"{name_value(argued)}; the resource a start reserved is not the resource "
            f"this act would name")
    return argued


def workspace_identity(attempt):
    """The attempt's workspace object, as the resource its starts contend for.

NAMES THE OBJECT AND MAKES NO OVERLAP ARGUMENT, which is now stated as the
    difference rather than as a caveat. Review 14:41:35Z ruled the device/inode
    selection an implementation proposal precisely because nested roots can differ by
    inode while sharing writable descendants, so naming the same object is not on its
    own an exclusion.

    `governed_workspace_identity` above is the form that carries the argument, by
    delegating to the containment owner. This one is for a caller holding no store,
    and a `Governance` composed on it excludes only same-object contention.
    """
    device, inode = attempt["workspace_device"], attempt["workspace_inode"]
    if device is None or inode is None:
        raise ContractRefusal(
            "refused", "precondition",
            f"attempt {name_value(attempt['runtime_attempt_id'])} has no pinned "
            f"workspace object, so the resource its start contends for cannot be "
            f"named; a governed start requires the boundary identity first")
    return f"{device}:{inode}"


def workspace_governance(*, control=None, mounted=None):
    """Starts serialized against the workspace object they mount.

    WITH a control store the identity carries its overlap argument, because the
    containment owner is asked. WITHOUT one it names the same object and excludes
    same-object contention only -- which is the honest difference, not a detail.

    W275774 review 2026-09-26T22-07-51Z: `mounted` IS THE ROOT THIS START ACTUALLY
    MOUNTS, and passing it is how a caller keeps the overlap argument in a deployment
    whose writable root is not `<storage>/<attempt>/workspace`. The containment owner
    proves the root sits in one of the two sibling arrangements this build supports; the
    equality against the PINNED object is unchanged, so the domain is still the durable
    one every ending resolves through. Supplying nothing leaves the ordinary derivation
    exactly as it was.
    """
    if control is None:
        return Governance("workspace", workspace_identity)
    return Governance("workspace",
                      lambda attempt: governed_workspace_identity(
                          control, attempt, mounted=mounted))


def _held_generation(control, domain):
    """The one outstanding generation of this domain, or `None`.

    Restart-safe by construction: it reads the journal rather than expecting the
    caller to still hold the token document it was handed before the restart.
    """
    held = outstanding(control, domain)
    if not held:
        return None
    if len(held) > 1:
        raise ContractRefusal(
            "runtime-observation", "identity-mismatch",
            f"resource {name_value(domain)} has {len(held)} outstanding token "
            f"generations, which is a state this owner never creates; nothing is "
            f"returned until that is reconciled")
    return held[0]["generation"]
