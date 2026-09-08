"""The principal, the scope and the one authorization decision.

W16821 corrects the incompatibility W16793 found: the authority made ONE
`team.member` string serve as route endpoint, session identity, authorization
principal, capability grantee, claim-capacity key, Handler and audit actor.
That is consistent for one flat deployment and cannot represent W9901's one
global principal acting through more than one organizational scope.

THREE SHAPES, AND THEY ARE DELIBERATELY NOT THE SAME TYPE AS A PARTICIPANT.

  * a PRINCIPAL is the canonical global identity an act is attributed to.  Its
    grammar is `principal:<opaque>`, which no `team.member` can match and which
    matches no `team.member` -- so a participant string handed to a boundary
    expecting a principal is REFUSED rather than silently accepted as one.
    That substitution is the whole defect, and a grammar is the only guard that
    catches it at every site at once.

  * a SCOPE is the organizational context an authorization is effective in.
    Its grammar is `scope:<opaque>`, for the same reason.  §2 of the correction
    boundary forbids deriving it from route, repository or participant
    spelling, so there is no constructor here that takes one of those.

  * an AUTHORIZATION DECISION is what the authority answers when it authorizes
    an act.  It names the endpoint AND the principal separately -- keeping them
    in one field is the incompatibility -- plus the effective scope, the role
    or capability the decision was about, the provenance of the grant that
    carried it, and the policy generation it was decided under.

WHAT IS DELIBERATELY ABSENT.  There is no hierarchy resolver, no group, no
inheritance walk and no mask evaluation: those are W9901/M6 provider work and
the correction boundary excludes them.  What is here is the SHAPE that admits
them.  `GRANTS` carries all three provenance kinds so a durable column can
already hold one, and `M2_GRANTS` is the strictly smaller set this cut is
allowed to produce -- two names rather than one, because "the shape admits it"
and "this cut may write it" are different claims and a single constant could
only make one of them.
"""

import re

from .errors import Refusal, label_of, name_of

__all__ = ["PRINCIPAL_PREFIX", "SCOPE_PREFIX", "DEPLOYMENT_SCOPE",
           "GRANTS", "M2_GRANTS", "DIRECT",
           "check_principal", "check_scope", "check_grant_provenance",
           "principal_for_endpoint", "AuthorizationDecision"]

PRINCIPAL_PREFIX = "principal:"
SCOPE_PREFIX = "scope:"

# The provenance vocabulary the DURABLE SHAPE admits.
DIRECT = "direct"
INHERITED = "inherited"
MASKED = "masked"
GRANTS = (DIRECT, INHERITED, MASKED)

# ...and the strictly smaller set THIS CUT may produce.  A decision claiming
# inheritance would be claiming a resolver that does not exist.
M2_GRANTS = (DIRECT,)


# The one authority-owned scope a deployment has before it configures any
# others.  A CONSTANT, not a derivation: the correction boundary forbids
# inferring the effective scope from route, repository or participant spelling,
# and a default computed from any of those would be exactly that inference
# wearing a default's name.
DEPLOYMENT_SCOPE = SCOPE_PREFIX + "deployment"

_OPAQUE = re.compile(r"\A[A-Za-z0-9][A-Za-z0-9._:-]*\Z")

# THERE IS NO LENGTH BOUND HERE, and the first cut of this module had one.
#
# It was 160 characters, borrowed from the frozen `opaqueId` wire grammar, and
# it made the authority REFUSE ITS OWN DERIVED VALUE: `check_participant`
# bounds no length, the store already keeps unbounded participant text in
# `work.handler` and `claim_slot.participant`, and the default principal for a
# 1,000-character endpoint is a 1,010-character principal.  A wide but
# perfectly valid participant became unclaimable, with a refusal naming a value
# the caller never supplied.  The authority's own boundary suite caught it.
#
# A principal is therefore bounded by exactly what bounds the endpoint it
# names, and nothing else.  Diagnostics stay bounded because `name_of` bounds
# every value it renders, which is where that rule belongs -- a grammar that
# refuses a legitimate identity to keep a message short is fixing the wrong
# thing at the wrong layer.


def _well_formed(value, prefix):
    """Whether VALUE is `<prefix><opaque identity>`.  Decides nothing else."""
    if type(value) is not str or not value.startswith(prefix):
        return False
    body = value[len(prefix):]
    return body != "" and _OPAQUE.match(body) is not None


def check_principal(value, *, what="a principal"):
    """The canonical global identity, and never a participant address.

    THE MESSAGE IS A LITERAL, and the near-duplicate in `check_scope` below is
    deliberate.  Passing the noun and the prefix into one shared builder made
    every refusal here interpolate two module constants, which the authority's
    diagnostic walker cannot prove bounded -- so the shared helper bought four
    lines of reuse and cost four entries in an exception registry that exists
    to stay small.  Two literals are cheaper than two excuses.
    """
    if not _well_formed(value, PRINCIPAL_PREFIX):
        raise Refusal(
            f"{label_of(what)} is {name_of(value)}; a principal is written "
            f"principal:<identity> and is not a participant address")
    return value


def check_scope(value, *, what="an effective scope"):
    """The organizational context an authorization is effective in."""
    if not _well_formed(value, SCOPE_PREFIX):
        raise Refusal(
            f"{label_of(what)} is {name_of(value)}; a scope is written "
            f"scope:<identity> and is not a route, a repository or a "
            f"participant address")
    return value


def check_grant_provenance(value, *, what="a grant provenance",
                           producible=M2_GRANTS):
    """WHICH KIND OF GRANT carried this decision.

    `producible` defaults to what this cut may write rather than to everything
    the column admits, so a caller has to say out loud that it is reading a
    wider vocabulary than it may produce.
    """
    # THE VOCABULARIES ARE SPELLED OUT IN THE MESSAGES, not interpolated.
    # A joined constant is a value this package's diagnostic walker cannot
    # prove bounded, and buying an exception-registry entry for a three-word
    # phrase is the wrong trade.  `test_principal_scope` holds both literals to
    # `GRANTS` and `M2_GRANTS`, so a widened vocabulary and a stale message
    # cannot coexist.
    what = label_of(what)
    if type(value) is not str or value not in GRANTS:
        raise Refusal(
            f"{what} is {name_of(value)}; a grant provenance is one of "
            f"direct, inherited, masked")
    if value not in producible:
        # NAMED BY THE CONSTANT rather than by `producible`: a caller that
        # widened the set is not the authority for what this cut may write, and
        # a message built from the caller's own argument would agree with
        # whatever it was handed.
        raise Refusal(
            f"{what} is {name_of(value)}; this cut resolves no grant hierarchy "
            f"and may only record direct provenance")
    return value


def principal_for_endpoint(participant):
    """The AUTHORITY'S OWN default principal for an endpoint it has not been
    told about.

    This is a deployment mapping, which the correction boundary permits to be
    minimal at M2 -- and it is the AUTHORITY's, not the caller's.  A caller
    cannot pass this function a value: every site that reaches it has already
    validated the participant, and no exported surface accepts a principal
    operand for the endpoint it is acting as.

    The default is one principal per endpoint, which is exactly the behaviour
    the deployment had before this correction.  What changes is that the
    mapping now EXISTS and is durable, so binding two endpoints to one
    principal is a configuration act rather than an impossibility.
    """
    return PRINCIPAL_PREFIX + participant


class AuthorizationDecision:
    """What the authority answers when it authorizes one act.

    IMMUTABLE and comparable by value.  A decision that a caller could edit
    after receiving it would be provenance the caller wrote, which is the same
    class of defect as an actor supplied on a receipt.
    """

    __slots__ = ("endpoint", "principal", "effective_scope", "role",
                 "grant", "policy_generation")

    def __init__(self, *, endpoint, principal, effective_scope, role, grant,
                 policy_generation):
        # EVERY MEMBER CHECKED HERE, at construction, because this object is
        # handed to callers and written to durable columns; a decision that was
        # validated by whoever happened to build it is a decision validated
        # nowhere in particular.
        from .identity import check_participant
        object.__setattr__(self, "endpoint",
                           check_participant(
                               endpoint, what="a decision's endpoint"))
        object.__setattr__(self, "principal",
                           check_principal(
                               principal, what="a decision's principal"))
        object.__setattr__(self, "effective_scope",
                           check_scope(effective_scope,
                                       what="a decision's effective scope"))
        if type(role) is not str or role == "":
            raise Refusal(
                f"a decision's role is {name_of(role)}; it names the route or "
                f"capability the decision was about")
        object.__setattr__(self, "role", role)
        object.__setattr__(self, "grant",
                           check_grant_provenance(
                               grant, what="a decision's grant provenance"))
        if type(policy_generation) is bool \
                or type(policy_generation) is not int or policy_generation < 1:
            raise Refusal(
                f"a decision's policy generation is "
                f"{name_of(policy_generation)}; it is the configuration "
                f"generation the decision was taken under")
        object.__setattr__(self, "policy_generation", policy_generation)

    def __setattr__(self, name, value):
        raise Refusal("an authorization decision is immutable")

    def __delattr__(self, name):
        raise Refusal("an authorization decision is immutable")

    def as_document(self):
        """A fresh owned built-in, never this object.

        The endpoint and the principal are SEPARATE MEMBERS.  A consumer that
        wants to know who acted reads `principal`; one that wants to know where
        to route or fence reads `endpoint`; and neither can be mistaken for the
        other, which is the whole correction.
        """
        return {"endpoint": self.endpoint, "principal": self.principal,
                "effective_scope": self.effective_scope, "role": self.role,
                "grant": self.grant,
                "policy_generation": self.policy_generation}

    def __eq__(self, other):
        return (isinstance(other, AuthorizationDecision)
                and self.as_document() == other.as_document())

    def __hash__(self):
        return hash(tuple(sorted(self.as_document().items())))

    def __repr__(self):
        return (f"<AuthorizationDecision {name_of(self.principal)} via "
                f"{name_of(self.endpoint)} in {name_of(self.effective_scope)}>")
