"""The RUNTIME face: one participant-bound session, and nothing else.

There are two public faces and this is the narrow one.  The frozen Node host
carried both on one object and was corrected for it: through that single
advertised boundary a consumer claimed as `publisher`, granted `publisher` the
close capability, closed the live Work as that actor, and moved the canonical
target with zero proposals and zero receipts.  A second reproduction simply
passed a configured closer's NAME, because the capability check compared a
string the same caller supplied.

A capability nobody can take away from you is not a capability, and an actor
identity the caller chooses is not an identity.  So:

  Authority   TRUSTED BOOTSTRAP.  It configures and it reads, and it MINTS
              sessions.  A deployment holds exactly one, at start-up.
  Session     the runtime boundary, bound at construction to ONE participant.
              It performs transitions and reads projections.  It cannot
              configure anything, cannot reach the authority that made it, and
              cannot name a participant other than its own -- the actor on
              every receipt and the claimant on every claim come from the
              BINDING, never from an operand.

THE TRUST BOUNDARY IS THE FILESYSTEM, exactly as v11 states for its own
authority: whoever can open the store file is the deployment.  A session
therefore carries no path, no store and no authority handle.  What holding one
guarantees is that it grants no configuration authority and no identity but its
own.

AND THE PYTHON CLAIM IS THE NARROW ONE.  Private attributes are not a sandbox:
a determined trusted in-process module can read `_core` or import
`baton_v12.authority.core`, and no amount of underscores changes that.  What is
enforced is the SUPPORTED, EXPORTED surface and the deployment wiring; untrusted
workers are isolated by process and container, which is a mechanism that
enforces something.
"""

from .errors import Refusal, name_of
from .identity import ABSENT, check_participant, own

__all__ = ["Session", "SESSION_TRANSITIONS", "SESSION_READS"]

# How many unexpected operand names a refusal SHOWS.  The rest are counted.
#
# Review [P1]: this module joined the WHOLE rejected key set into the message and
# interpolated the supplied participant directly, so a one-million-character
# operand name produced a 1,000,089-character refusal.  `errors.py` states the
# rule two files away -- caller-controlled text in a refusal is bounded by the
# RULE and never by the operand -- and cut 5's own evidence asserted the bound
# held here.  Stating a rule and then writing the sites that break it is cut 4's
# projection defect, one cut later.
#
# So every caller-controlled rendering goes through `name_of`, and several
# rejected names become a bounded SAMPLE plus a count.  The whole message is then
# bounded by construction: the rule text is fixed, the transition name comes from
# the table, and nothing else is interpolated.
_SHOWN_EXTRAS = 3

# Sessions are MINTED, never constructed.  This object is module-private and
# exported nowhere, so a consumer that reaches the class through its own
# instance's `__class__` still cannot make a second one for another participant.
_MINT = object()


# What a session may do, WRITTEN OUT rather than derived.
#
# Deriving it from `Core` would mean that adding a method there silently widened
# the runtime boundary.  A new transition is unreachable from a session until
# somebody puts it in this table deliberately -- and the table also records, per
# transition, exactly which operands it takes, because an operand a caller
# supplies and has ignored is an operand the caller believes it chose.
#
# `required` and `optional` are the WHOLE key set.  Anything else refuses.
_TRANSITIONS = {
    "claim": {"required": ("work_id", "operation_id"), "optional": ()},
    "activity": {"required": ("expect", "key"), "optional": ()},
    "advance_contract": {
        "required": ("expect", "operation_id", "expect_contract",
                     "target_contract", "rationale"), "optional": ()},
    "approve": {"required": ("proposal_id", "approval_id", "disposition",
                             "operation_id", "policy_generation"),
                "optional": (), "actor": True},
    "cancel": {"required": ("expect", "operation_id"), "optional": ("reason",)},
    "close": {"required": ("work_id", "operation_id", "outcome", "rationale"),
              "optional": ("expect",), "actor": True},
    "end": {"required": ("expect", "operation_id"),
            "optional": ("disposition", "reason")},
    "install_gate": {"required": ("work_id", "operation_id", "gate"),
                     "optional": ("reason", "expect")},
    "integrate": {"required": ("proposal_id", "integration_id",
                               "operation_id"), "optional": (),
                  "actor": True},
    "pass_work": {"required": ("expect", "operation_id", "to_route"),
                  "optional": ("comment",)},
    "publish": {"required": ("expect", "operation_id", "proposal_id",
                             "result_id", "result_digest", "candidate_digest",
                             "input_digest", "policy_digest"),
                "optional": ("target",)},
    "reject_plan": {"required": ("expect", "operation_id", "plan_digest"),
                    "optional": ("reason",)},
    "review": {"required": ("proposal_id", "review_id", "disposition",
                            "operation_id"), "optional": (), "actor": True},
    "satisfy_gate": {"required": ("work_id", "operation_id", "gate",
                                  "evidence"), "optional": ()},
    "settle_operation": {"required": ("operation_id", "signature"),
                         "optional": ("reason", "disposition", "may_retire")},
    "verify": {"required": ("proposal_id", "verification_id", "observation",
                            "operation_id"), "optional": (), "actor": True},
}

SESSION_TRANSITIONS = tuple(sorted(_TRANSITIONS))

# The reads, and the operands each takes positionally.
_READS = {
    "activities": ("work_id",),
    "assert_invariants": ("work_id",),
    "assignment_events": ("work_id",),
    "assignment_of": ("work_id",),
    "canonical_target": (),
    "contract_events": ("work_id",),
    "fenced_generations": ("work_id",),
    "gate_evidence": ("work_id",),
    "integration_attempts": ("proposal_id",),
    "operation_record": ("operation_id",),
    "operation_result": ("operation_id",),
    "project_work": ("work_id",),
    "proposal": ("proposal_id",),
    "receipt": ("proposal_id", "kind"),
    "receipts": ("proposal_id",),
    "slot_holder": ("participant",),
}

SESSION_READS = tuple(sorted(_READS))

# The transitions that WRITE an attributable actor.  Only these receive one; the
# rest are authorized by the exact assignment they compare-and-swap, and handing
# them an operand they do not use would be noise that looks like authorization.
_ACTOR_TRANSITIONS = frozenset(
    name for name, shape in _TRANSITIONS.items() if shape.get("actor"))

# The transitions whose FIRST argument to the core is the assignment.
_ASSIGNMENT_FIRST = frozenset({
    "activity", "advance_contract", "cancel", "end", "pass_work", "publish",
    "reject_plan"})


def _sample_of(keys):
    """Name a bounded SAMPLE of rejected operand names, and count the rest.

    Deliberately NOT sorted.  Sorting a rejected set is work done for prose, and
    insertion order is the more useful answer anyway: it names the first
    unexpected operands in the order the caller wrote them.
    """
    shown = ", ".join(name_of(key) for key in keys[:_SHOWN_EXTRAS])
    if len(keys) <= _SHOWN_EXTRAS:
        return shown
    return f"{shown} and {len(keys) - _SHOWN_EXTRAS} more"


class Session:
    """One participant's runtime handle.  Minted by the trusted authority."""

    def __init__(self, mint, core, participant):
        if mint is not _MINT:
            raise Refusal(
                "a session is minted by the trusted authority, not "
                "constructed; holding one grants no way to make another")
        self._core = core
        self._participant = participant

    @property
    def participant(self):
        return self._participant

    def __repr__(self):
        # Bounded for the same reason the refusals are: a participant has a
        # grammar but no length, and a repr is a diagnostic that gets logged.
        # Found by sweeping this module rather than by being told about it.
        return f"<Session for {name_of(self._participant)}>"

    # -- the one operand rule -------------------------------------------------

    def _operands(self, name, documents):
        """EXACTLY one exact built-in operand document, taken ONCE.

        SNAPSHOT FIRST, and never read the caller's object again.  The frozen
        host read `operands.expect.participant` for the binding check and then
        handed the SAME object to the core, which read it again -- a getter
        answering one participant twice and another afterwards passed the check
        and then ended somebody else's live assignment.  Validating one view and
        executing another is the defect, and taking one owned copy is the only
        thing that removes it.

        Review [P2]: EXACTLY one, and the arity is checked HERE rather than by
        Python.  This took `given=None`, so an omitted document and an explicitly
        supplied `None` became the same empty dict and the caller was told which
        members were missing -- in the wrapper whose stated purpose is to refuse
        an operand supplied and then ignored.  A second document left as a raw
        `TypeError`, which is a fault escaping a boundary that had a refusal
        ready for it.  Zero, null and several are all the one-document rule now,
        and each of them says so.
        """
        if len(documents) != 1:
            raise Refusal(
                f"{name} takes exactly one operand document; this call supplies "
                f"{len(documents)}")
        given = documents[0]
        operands = own(given, what=f"the {name} operands")
        if type(operands) is not dict:
            raise Refusal(
                f"{name} takes one operand document; this is "
                f"{name_of(given)}")
        shape = _TRANSITIONS[name]
        # AN OPERAND THAT LOOKS AUTHORITATIVE AND IS NOT is worse than no
        # operand, so supplying one is REFUSED rather than ignored.  The frozen
        # host silently dropped a supplied `participant` on `claim`, so a caller
        # could believe it had been honoured.
        for forbidden in ("actor", "participant"):
            if forbidden in operands:
                raise Refusal(
                    f"{name} takes its identity from the session it is called "
                    f"on; supplying {forbidden} would let a caller choose an "
                    f"identity the authority then treated as authenticated")
        allowed = set(shape["required"]) | set(shape["optional"])
        extra = [key for key in operands if key not in allowed]
        if extra:
            raise Refusal(
                f"{name} does not take {_sample_of(extra)}; an operand supplied "
                f"and ignored is one the caller believes it chose")
        missing = sorted(set(shape["required"]) - set(operands))
        if missing:
            raise Refusal(f"{name} needs {', '.join(missing)}")
        return operands

    def _check_binding(self, name, operands):
        """A session acts only on its OWN assignments -- for the
        ASSIGNMENT-OWNED acts.

        The assignment identity authorizes those and is not a secret, so a
        session that could act on somebody else's would make the binding
        decorative.

        `close` is deliberately NOT one of them.  §7 authorizes it by the close
        CAPABILITY, and its `expect` is a compare-and-swap operand rather than
        proof of authorship: an approver closing a Work somebody else is
        executing is the ordinary case, and the identity is what stops them
        closing blindly.
        """
        if name in _ACTOR_TRANSITIONS:
            return
        expect = operands.get("expect")
        if type(expect) is not dict:
            return
        named = expect.get("participant")
        if named is not None and named != self._participant:
            # BOTH renderings bounded: the named participant is the caller's
            # text, and a session's own participant has a grammar but no length.
            raise Refusal(
                f"this session acts for {name_of(self._participant)}; the "
                f"assignment names {name_of(named)}")

    # -- transitions ----------------------------------------------------------

    def _call(self, name, documents):
        operands = self._operands(name, documents)
        self._check_binding(name, operands)
        method = getattr(self._core, name)
        if name == "claim":
            # THE CLAIMANT IS THE BINDING, not an operand.  A session for one
            # participant cannot claim for anybody else, so there is no
            # identity to choose.
            return method(operands["work_id"], self._participant,
                          operation_id=operands["operation_id"])
        keywords = dict(operands)
        if name in _ACTOR_TRANSITIONS:
            keywords["actor"] = self._participant
        if name in _ASSIGNMENT_FIRST:
            expect = keywords.pop("expect")
            return method(expect, **keywords)
        if name in ("install_gate", "satisfy_gate"):
            work_id = keywords.pop("work_id")
            return method(work_id, **keywords)
        if name == "close":
            work_id = keywords.pop("work_id")
            if "expect" not in keywords:
                keywords["expect"] = ABSENT
            return method(work_id, **keywords)
        if name == "settle_operation":
            operation_id = keywords.pop("operation_id")
            return method(operation_id, **keywords)
        return method(**keywords)


def _install():
    """Install the enumerated surface from inside this module.

    The delegating methods are built here because this is the only place `_MINT`
    and the tables live.  A method added elsewhere would not be in the table, so
    it would not exist -- which is the point of writing the surface out.
    """

    def transition(name):
        def call(self, *documents):
            # `*documents` rather than one defaulted parameter, so zero, null and
            # several are all THIS boundary's refusal instead of Python's
            # TypeError or a silent substitution.
            return self._call(name, documents)

        call.__name__ = name
        call.__qualname__ = f"Session.{name}"
        return call

    def read(name, parameters):
        def call(self, *arguments):
            if len(arguments) != len(parameters):
                raise Refusal(
                    f"{name} takes {', '.join(parameters) or 'no operands'}")
            return getattr(self._core, name)(*arguments)

        call.__name__ = name
        call.__qualname__ = f"Session.{name}"
        return call

    for name in _TRANSITIONS:
        setattr(Session, name, transition(name))
    for name, parameters in _READS.items():
        setattr(Session, name, read(name, parameters))


_install()


def _mint_session(core, participant):
    """The ONE route to a transition at all.

    Named private because it IS private: `Authority.session` is the only caller,
    and the mint object it passes is exported nowhere.  A module whose `__all__`
    says one thing while its public names say another is a surface claim that
    does not check, which is the defect this whole package keeps correcting.
    """
    check_participant(participant, what="a session is bound to one participant")
    return Session(_MINT, core, participant)
