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


def token_of(control, domain, generation):
    """This generation as it now stands: terms, launch, container and return."""
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
    answer["expired"] = control._now() >= acquired["expires_at"]
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
                f"{name_value(held['expires_at'])}) and that token has not been "
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


def returned(control, token, *, cessation):
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
        _owning(control, token, "returning the token")
        return dict(document)

    return control.transact(_returned_id(token["domain"], token["generation"]),
                            RETURNED_KIND,
                            manager_signature(RETURNED_KIND, document), returning)


def _owning(control, token, what):
    """Re-read the acquisition and require this act to be its owner.

    The document the caller holds is one the caller is holding; what authorizes each
    step is the record this journal still has, with its signature recomputed.
    """
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
    if control._now() >= held["expires_at"]:
        raise ContractRefusal(
            "refused", "precondition",
            f"{what} for generation {token['generation']} of "
            f"{name_value(token['domain'])} is refused: that token expired at "
            f"{name_value(held['expires_at'])}. Expiry begins revocation, and a late "
            f"binding or return under an expired token is not an exception to it")
    return held
